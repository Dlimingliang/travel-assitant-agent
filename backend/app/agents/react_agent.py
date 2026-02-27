from enum import Enum
from typing import Any

from pydantic import BaseModel, Field
from ..core.memory import Memory
from ..core.llm_client import get_llm

class AgentState(Enum):
    """agent状态枚举"""
    IDLE = "idle"
    PERCEIVING = "perceiving"
    PLANNING = "planning"
    CLARIFY = "clarify" # 需要追问
    ACTING = "acting"
    TOOL_CALL = "tool_call"
    ERROR = "error"

class ReActAgent(BaseModel):
    name: str = Field(..., description="名称")
    role: str = Field(..., description="助手")
    memory: Memory = Field(description="记忆")
    tools: dict[str, Any] = Field(description="工具", default={})
    prompt: str = Field(description="提示词",default="")

    def call_llm(self,messages: list[dict[str, str]], temperature: int = 0):
        response = get_llm().chat(messages = messages, temperature = temperature)
        return response

