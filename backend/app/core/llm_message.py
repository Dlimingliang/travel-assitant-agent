from enum import Enum
from typing import Literal, Any
from pydantic import BaseModel, Field

class MessageRole(Enum):
    """消息类型枚举"""
    user = "user"
    assistant = "assistant"
    system = "system"
    tools = "tools"

class LlmMessage(BaseModel):
    """和大模型交互消息类"""
    role: MessageRole = Field(..., description="消息类型")
    content: str = Field(..., description="内容")

    def to_dict(self) -> dict[str, Any]:
        """转换为字典格式(OpenAI API格式)"""
        return {
            "role": self.role.value,
            "content": self.content,
        }

