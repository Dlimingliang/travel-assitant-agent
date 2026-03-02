import json
from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, Field
from ..core.memory import Memory
from ..core.llm_client import get_llm
from ..core.mcp_client import  MCPTool
from ..models.schemas import UserTripPlan, AgentResponse,TripPlanType

class AgentState(Enum):
    """agent状态枚举"""
    IDLE = "idle"
    PERCEIVING = "perceiving"
    PLANNING = "planning"
    CLARIFY = "clarify" # 需要追问
    EXECUTING = "executing"
    TOOL_CALL = "tool_call"
    ERROR = "error"

class ReActAgent(BaseModel):
    model_config = {"arbitrary_types_allowed": True}

    name: str = Field(..., description="名称")
    role: str = Field(..., description="助手")
    state: AgentState = AgentState.IDLE
    memory: Memory = Field(description="记忆")
    tools: dict[str, MCPTool] = Field(description="工具", default={})
    prompt: str = Field(description="提示词",default="")

    def process(self, session_id:str, user_input:str) -> AgentResponse:

        # 感知阶段
        perceive_response = self.perceiving(session_id, user_input)
        if perceive_response != "":
            return AgentResponse(
                type = TripPlanType.clarify,
                message = perceive_response,
            )
        # 感知结束，拿到了必要的信息，开始执行规划和tool调用
        # react开始 进入规划、行动、观察

        return AgentResponse(
        )


    def perceiving(self, session_id: str,user_input: str) -> str:
        """感知用户输入，确认是否追问，如果需要，则进行追问，如果不需要则进行后面的阶段"""
        self.state = AgentState.PERCEIVING
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
           - travel_days（旅行天数，整数，例如3）
           - accommodation（住宿偏好，例如"经济型酒店"）
        2. 额外信息：free_text_input（额外要求，例如"希望多安排一些博物馆"）
        3. 如果用户消息中提供了新信息，更新对应字段
        4. 如果用户消息中没有提到某个字段，但当前信息中已有，则保留
        5. 如果新消息与旧信息冲突，以新消息为准
        6. complete 字段表示是否所有必要信息都已收集（布尔值）
        7. missing_fields 列出所有尚未收集的必要信息，用中文列出，并总结为一句话,例如:请告诉我关于此次旅行的更多信息,包括目的地城市,旅行天数
        8. 请严格按照 JSON Schema 格式返回，确保字段名与 schema 一致
        9. 必须返回以下所有字段：complete, city, start_date, travel_days, accommodation, free_text_input, missing_fields
        10. 每个字段都必须出现在JSON中，即使值为null
        
        示例JSON格式：
        {{
          "complete": false,
          "city": "北京",
          "start_date": null,
          "travel_days": null,
          "accommodation": null,
          "free_text_input": null,
          "missing_fields": "请告诉我关于此次旅行的更多信息,包括目的地城市,旅行天数"
        }}
        """
        llm = get_llm()
        print(f"🧠 正在调用 {llm.model} 模型...")
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
        if content is None:
            # 处理空内容的情况
            raise Exception("llm返回为空")
        user_trip_plan = UserTripPlan(**json.loads(content))
        # 把现在这个当做工作记忆
        self.memory.work_memory[session_id] = content
        print(f"解析后的UserTripPlan: {user_trip_plan}")
        if not user_trip_plan.complete:
            return user_trip_plan.missing_fields
        return ""

    def planning(self, session_id: str, user_input: str) -> str:
        """有了用户的意图，开始规划行动"""
        self.state = AgentState.PLANNING
        
        # 示例：如果有工具，可以调用MCP工具
        if self.tools:
            print(f"🔧 Agent有 {len(self.tools)} 个可用工具")
            
            # 示例：查找地理编码工具（高德地图可能提供）
            geocode_tools = [name for name in self.tools.keys() if "geocode" in name.lower()]
            if geocode_tools:
                tool_name = geocode_tools[0]
                print(f"尝试调用工具: {tool_name}")
                
                # 示例调用（需要实际参数）
                # try:
                #     result = self.call_tool(tool_name, address="北京市")
                #     print(f"工具调用结果: {result}")
                # except Exception as e:
                #     print(f"工具调用失败: {e}")
        
        # TODO: Implement planning logic
        return ""
    
    def call_tool(self, tool_name: str, **kwargs) -> Any:
        """
        调用指定的MCP工具
        
        Args:
            tool_name: 工具名称（可以是原始名称或带服务器前缀的名称）
            **kwargs: 工具参数
            
        Returns:
            工具调用结果
            
        Raises:
            KeyError: 如果工具不存在
            Exception: 工具调用失败
        """
        if tool_name not in self.tools:
            # 尝试查找不带前缀的工具名
            available = list(self.tools.keys())
            # 如果工具名包含点，可能是server.tool格式
            if "." in tool_name:
                # 已经尝试过完整名称，直接报错
                raise KeyError(f"工具 '{tool_name}' 不存在。可用工具: {available}")
            else:
                # 尝试查找带前缀的版本
                prefixed = [name for name in available if name.endswith(f".{tool_name}")]
                if prefixed:
                    tool_name = prefixed[0]
                else:
                    raise KeyError(f"工具 '{tool_name}' 不存在。可用工具: {available}")
        
        tool = self.tools[tool_name]
        print(f"🔧 调用工具: {tool_name} with args: {kwargs}")
        
        try:
            result = tool.call(**kwargs)
            print(f"✅ 工具调用成功: {tool_name}")
            return result
        except Exception as e:
            print(f"❌ 工具调用失败: {tool_name}, error: {e}")
            raise
