import json
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field
from ..core.memory import Memory
from ..core.llm_client import get_llm
from ..models.schemas import UserTripPlan

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

    # 收集用户信息，不足的时候要进行返回进行追问
    def perceiving(self, session_id: str,user_input: str) -> UserTripPlan:
        """感知用户输入，确认是否追问，如果需要，则进行追问，如果不需要则进行后面的阶段"""
        current_info: dict[str, Any] | None = self.memory.work_memory.get(session_id)
        current_info_str = json.dumps(current_info, ensure_ascii=False) if current_info else "暂无"
        print(f"用户输入: {user_input}")
        prompt = f"""
你是一个旅行助手，需要从用户的对话中提取旅行信息。

当前已经收集到的信息:
{current_info_str}

用户的最新消息:
{user_input}

请提取信息，并按以下规则处理：
1. 必要信息包括（必须提取以下所有字段）：
   - city（目的地城市，例如"北京"）
   - start_date（开始日期，格式YYYY-MM-DD，例如"2025-06-01"）
   - end_date（结束日期，格式YYYY-MM-DD，例如"2025-06-03"）
   - travel_days（旅行天数，整数，例如3）
   - accommodation（住宿偏好，例如"经济型酒店"）
2. 额外信息：free_text_input（额外要求，例如"希望多安排一些博物馆"）
3. 如果用户消息中提供了新信息，更新对应字段
4. 如果用户消息中没有提到某个字段，但当前信息中已有，则保留
5. 如果新消息与旧信息冲突，以新消息为准
6. complete 字段表示是否所有必要信息都已收集（布尔值）
7. missing_fields 列出所有尚未收集的必要信息，用中文列出，例如["开始日期", "结束日期", "旅行天数", "住宿偏好"]
8. 请返回完整的 UserTripPlan，包含所有字段，即使某些字段没有值也设置为 null
9. 请严格按照 JSON Schema 格式返回，确保字段名与 schema 一致
10. 必须返回以下所有字段：complete, city, start_date, end_date, travel_days, accommodation, free_text_input, missing_fields
11. 每个字段都必须出现在JSON中，即使值为null

示例JSON格式：
{{
  "complete": false,
  "city": "北京",
  "start_date": null,
  "end_date": null,
  "travel_days": null,
  "accommodation": null,
  "free_text_input": null,
  "missing_fields": ["开始日期", "结束日期", "旅行天数", "住宿偏好"]
}}
"""
        llm = get_llm()
        print(f"🧠 正在调用 {llm.model} 模型...")
        print(f"使用的JSON Schema字段: {list(UserTripPlan.model_json_schema().get('properties', {}).keys())}")
        response = llm.client.chat.completions.create(
            model = llm.model,
            messages = [{"role":"user","content":prompt}],
            response_format={
                "type": "json_schema",
                "json_schema": {
                    "name": "user_trip_plan",
                    "schema": UserTripPlan.model_json_schema()
                }
            },
            temperature=0
        )
        print(f"assistant response: {response}")
        content = response.choices[0].message.content
        print(f"LLM返回的content: {content}")
        if content is None:
            # 处理空内容的情况
            raise Exception("llm返回为空")
        try:
            user_trip_plan = UserTripPlan(**json.loads(content))
        except Exception as e:
            print(f"解析LLM返回的JSON失败: {e}, content: {content}")
            raise
        print(f"解析后的UserTripPlan: {user_trip_plan}")
        return user_trip_plan


    # 收集到了必要信息，开始进行规划、规划完成进行行动阶段

    # 行动之后添加返回结果继续执行

    # 最后返回结果, 返回结果需要进行规范格式

