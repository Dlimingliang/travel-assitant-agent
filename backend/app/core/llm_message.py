from datetime import datetime
from enum import Enum
from typing import Any
from pydantic import BaseModel, Field, ConfigDict

class MessageRole(str, Enum):
    """消息类型枚举"""
    user = "user"
    assistant = "assistant"
    system = "system"
    tools = "tools"
    tool_calls = "tool_calls"

class LlmMessage(BaseModel):
    """和大模型交互消息类"""
    model_config = ConfigDict(use_enum_values=True)
    
    role: MessageRole = Field(..., description="消息类型")
    content: str = Field(..., description="内容")
    timestamp: datetime = Field(default_factory=datetime.now)

    def to_dict(self) -> dict[str, Any]:
        """转换为字典格式(OpenAI API格式)"""
        return {
            "role": self.role if isinstance(self.role, str) else self.role.value,
            "content": self.content,
            "timestamp": self.timestamp.isoformat(),
        }

