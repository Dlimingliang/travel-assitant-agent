import json
import uuid
from datetime import datetime
from enum import Enum
from typing import Any, Optional
from pydantic import BaseModel, Field
from .llm_message import LlmMessage, MessageRole

class StepType(Enum):
    """ReAct步骤类型"""
    THOUGHT = "thought"
    ACTION = "action"
    OBSERVATION = "observation"

class ReactStep(BaseModel):
    """单个React步骤"""
    step_type: StepType
    content: str
    timestamp: datetime = Field(default_factory=datetime.now)
    metadata: dict[str, Any] = Field(default_factory=dict)

class TaskContext(BaseModel):
    """当前任务上下文"""
    user_goal: str
    current_plan: list[str] = Field(default_factory=list)

class WorkMemory:
    """
    工作记忆：存储当前任务执行的临时状态
    - 当前任务上下文 task_context
    - ReAct循环步骤记录 react_steps
    - 最大循环次数 max_react_steps
    """
    def __init__(self, max_react_steps: int = 10):
        self.max_react_steps = max_react_steps
        self.react_steps: list[ReactStep] = []
        self.task_context: Optional[TaskContext] = None

    def init_task(self, user_goal: str):
        """每次新任务来了初始化任务"""
        self.task_context = TaskContext(user_goal=user_goal)
        self.react_steps = []

    def add_react_step(self, step_type: StepType, content: str, timestamp: datetime, metadata: dict[str, Any]):
        """添加react step"""
        self.react_steps.append(ReactStep(step_type=step_type, content=content, timestamp=timestamp, metadata=metadata))

    def get_react_trace(self) -> str:
        """合并trace轨迹，构建prompt"""
        trace: list[Any] = []
        for step in self.react_steps:
            prefix = step.step_type.value.capitalize()
            trace.append(f"{prefix}: {step.content}")
        return "\n".join(trace)

    def set_task_plan(self, plans: list[str]):
        """设置执行计划"""
        if self.task_context:
            self.task_context.current_plan = plans

    def clear(self):
        """清空工作记忆"""
        self.task_context = None
        self.react_steps = []

class ShortMemory:
    """
    短期记忆: 存储当前会话的对话历史
    - 完整对话历史
    """
    def __init__(self, max_message: int = 20):
        self.messages: list[LlmMessage] = []
        self.max_message = max_message

    def add_message(self, role: MessageRole, content:str):
        """添加消息"""
        self.messages.append(LlmMessage(role=role, content=content, timestamp=datetime.now()))
        if len(self.messages) > self.max_message:
            self._compress_history()

    def _compress_history(self):
        """压缩历史消息，避免膨胀"""
        # 保留第一条系统消息和最近的消息 暂时这样
        if self.messages and self.messages[0].role == MessageRole.system:
            system_msg = self.messages[0]
            recent_msgs = self.messages[-(self.max_message // 2):]
            self.messages = [system_msg] + recent_msgs
        else:
            self.messages = self.messages[-(self.max_message // 2):]

    def get_messages_for_llm(self) -> list[dict[str, str]]:
        """获取用于LLM的消息格式"""
        return [{"role": m.role, "content": m.content} for m in self.messages]

    def clear(self) -> None:
        """清空短期记忆"""
        self.messages = []



class MemorySystem:
    """
    统一记忆系统: 整合工作记忆和短期记忆
    """

    def __init__(self, max_message: int = 20, max_react_steps: int = 10):
        self.working_memory = WorkMemory(max_react_steps=max_react_steps)
        self.short_memory = ShortMemory(max_message=max_message)

    def build_prompt_context(self) -> str:
        """提取当前上下文信息"""
        parts: list[str] = []

        # 历史上下文
        if self.short_memory:
            current_info = self.short_memory.get_messages_for_llm()
            current_info_str = json.dumps(current_info, ensure_ascii=False) if current_info else "暂无"
            parts.append(f"[历史上下文]\n{current_info_str}")

        # 从工作任务中提取当前任务信息
        if self.working_memory.task_context:
            parts.append(f"[当前目标]\n{self.working_memory.task_context.user_goal}")

            if self.working_memory.task_context.current_plan:
                plan_str = "\n".join(f"{i + 1}. {s}" for i, s in enumerate(self.working_memory.task_context.current_plan))
                parts.append(f"[执行计划]\n{plan_str}")

        # 添加React任务轨迹
        react_trace = self.working_memory.get_react_trace()
        if react_trace:
            parts.append(f"[推理过程]\n{react_trace}")

        return "\n\n".join(parts)

    def reset_memory(self) -> None:
        """重置整个记忆"""
        self.working_memory.clear()
        self.short_memory.clear()

# 全局LLM实例
_session_memory_manager = None

class SessionMemoryManager:
    """
    会话记忆管理器：按session——id管理多个独立的记忆系统
    """
    def __init__(self, max_react_steps: int = 10, max_messages: int = 20):
        self._sessions: dict[str, MemorySystem] = {}
        self._max_react_steps = max_react_steps
        self._max_messages = max_messages

    def create_session_memory(self, session_id: Optional[str] = None) -> str:
        """
        创建新会话
        Args:
            session_id: 可选的会话ID，如果不提供则自动生成
        Returns:
            会话ID
        """
        if session_id is None:
            session_id = str(uuid.uuid4())

        if session_id not in self._sessions:
            self._sessions[session_id] = MemorySystem(
                max_react_steps=self._max_react_steps,
                max_message=self._max_messages
            )
        return session_id


    def get_or_create_session_memory(self, session_id: str) -> MemorySystem:
        """
        获取或创建会话的记忆系统
        Args:
            session_id: 会话ID
        Returns:
            对应的MemorySystem
        """
        if session_id not in self._sessions:
            self.create_session_memory(session_id)
        return self._sessions[session_id]

def get_session_memory_manager() -> SessionMemoryManager:
    """
    获取session记忆
    """
    global _session_memory_manager

    if _session_memory_manager is None:
        _session_memory_manager = SessionMemoryManager()

    return _session_memory_manager

def get_memory(session_id: str) -> MemorySystem:
    return get_session_memory_manager().get_or_create_session_memory(session_id)
