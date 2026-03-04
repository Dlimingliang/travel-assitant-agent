"""
全局Agent管理器
用于在应用启动时初始化Agent，并在任何地方访问
"""
from typing import Optional
from ..agents.react_agent import ReActAgent


class AgentManager:
    """Agent管理器 - 单例模式"""
    _instance: Optional["AgentManager"] = None
    _agent: Optional[ReActAgent] = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def set_agent(self, agent: ReActAgent) -> None:
        """设置全局Agent实例"""
        self._agent = agent

    def get_agent(self) -> Optional[ReActAgent]:
        """获取全局Agent实例"""
        return self._agent

    @property
    def agent(self) -> ReActAgent:
        """获取Agent实例，如果未初始化则抛出异常"""
        if self._agent is None:
            raise RuntimeError("Agent尚未初始化，请确保应用已正确启动")
        return self._agent


# 全局Agent管理器实例
_agent_manager = AgentManager()


def get_agent_manager() -> AgentManager:
    """获取Agent管理器实例"""
    return _agent_manager


def get_agent() -> ReActAgent:
    """
    获取全局Agent实例的便捷方法
    
    Returns:
        ReActAgent: 全局Agent实例
        
    Raises:
        RuntimeError: 如果Agent尚未初始化
    """
    return _agent_manager.agent
