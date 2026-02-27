from typing import Any
from pydantic import BaseModel, Field
from backend.app.core.llm_message import LlmMessage

class Memory(BaseModel):
    short_memory: dict[str,list[LlmMessage]] = Field(default_factory=dict,description="短期记忆")
    work_memory: dict[str,dict[str,Any]] = Field(default_factory=dict, description="工作记忆")

    def add_short_memory(self, session_id:str, memory: LlmMessage):
        self.short_memory[session_id].append(memory)
        if len(self.short_memory[session_id]) > 20:
            self.short_memory[session_id].pop(0)

    def add_work_memory(self, session_id:str, key: str, value: Any):
        self.work_memory[session_id][key] = value
