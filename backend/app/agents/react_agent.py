import json
from enum import Enum
from typing import Any, Optional, List, Dict

from pydantic import BaseModel, Field

from ..core import LlmMessage, MessageRole
from ..core.memory import Memory
from ..core.llm_client import get_llm
from ..core.mcp_client import  MCPTool
from ..models.schemas import UserTripPlan, AgentResponse,TripPlanType

res_json = """
```json
{
  "city": "城市名称",
  "start_date": "YYYY-MM-DD",
  "end_date": "YYYY-MM-DD",
  "days": [
    {
      "date": "YYYY-MM-DD",
      "day_index": 0,
      "description": "第1天行程概述",
      "transportation": "交通方式",
      "accommodation": "住宿类型",
      "hotel": {
        "name": "酒店名称",
        "address": "酒店地址",
        "location": {"longitude": 116.397128, "latitude": 39.916527},
        "price_range": "300-500元",
        "rating": "4.5",
        "distance": "距离景点2公里",
        "type": "经济型酒店",
        "estimated_cost": 400
      },
      "attractions": [
        {
          "name": "景点名称",
          "address": "详细地址",
          "location": {"longitude": 116.397128, "latitude": 39.916527},
          "visit_duration": 120,
          "description": "景点详细描述",
          "category": "景点类别",
          "ticket_price": 60
        }
      ],
      "meals": [
        {"type": "breakfast", "name": "早餐推荐", "description": "早餐描述", "estimated_cost": 30},
        {"type": "lunch", "name": "午餐推荐", "description": "午餐描述", "estimated_cost": 50},
        {"type": "dinner", "name": "晚餐推荐", "description": "晚餐描述", "estimated_cost": 80}
      ]
    }
  ],
  "weather_info": [
    {
      "date": "YYYY-MM-DD",
      "day_weather": "晴",
      "night_weather": "多云",
      "day_temp": 25,
      "night_temp": 15,
      "wind_direction": "南风",
      "wind_power": "1-3级"
    }
  ],
  "overall_suggestions": "总体建议",
  "budget": {
    "total_attractions": 180,
    "total_hotels": 1200,
    "total_meals": 480,
    "total_transportation": 200,
    "total": 2060
  }
}
```
"""

res_simple_json = """
{
  "city": "城市名称",
  "start_date": "YYYY-MM-DD",
  "end_date": "YYYY-MM-DD",
  "days": [
    {
      "date": "YYYY-MM-DD",
      "day_index": 0,
      "description": "第1天行程概述",
      "hotel": {
        "name": "酒店名称",
        "address": "酒店地址",
      },
      "attractions": [
        {
          "name": "景点名称",
          "address": "详细地址",
        }
      ]
    }
  ],
  "weather_info": [
    {
      "date": "YYYY-MM-DD",
      "day_weather": "晴",
      "night_weather": "多云",
      "day_temp": 25,
      "night_temp": 15,
      "wind_direction": "南风",
      "wind_power": "1-3级"
    }
  ],
  "overall_suggestions": "总体建议"
}
"""

class AgentState(Enum):
    """agent状态枚举"""
    IDLE = "idle"
    PERCEIVING = "perceiving"
    PLANNING = "planning"
    CLARIFY = "clarify" # 需要追问
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

    def get_tools_for_openai(self) -> List[Dict[str, Any]]:
        """
        获取所有工具的 OpenAI Function Calling 格式
        用于直接传递给 OpenAI API 的 tools 参数
        
        Returns:
            工具列表，每个工具都是 OpenAI function calling 格式
        """
        return [tool.to_openai_function_schema() for tool in self.tools.values()]
    
    def process(self, session_id:str, user_input:str) -> AgentResponse:

        # 感知阶段
        perceive_response = self.perceiving(session_id, user_input)
        if perceive_response != "":
            return AgentResponse(
                type = TripPlanType.clarify,
                message = perceive_response,
            )
        # 感知结束，拿到了必要的信息，开始执行规划和tool调用
        # react开始 进入thought、action、observation

        plan_response = self.planning(session_id, user_input)

        return AgentResponse(
            type = TripPlanType.stop,
            message = plan_response,
        )


    def perceiving(self, session_id: str,user_input: str) -> str:
        """感知用户输入，确认是否追问，如果需要，则进行追问，如果不需要则进行后面的阶段"""
        self.state = AgentState.PERCEIVING
        current_info: dict[str, Any] | None = self.memory.work_memory.get(session_id)
        current_info_str = json.dumps(current_info, ensure_ascii=False) if current_info else "暂无"
        print(f"👤 用户输入: {user_input}")
        prompt = f"""
        你是一个旅行助手，需要从用户的对话中提取旅行信息。
        如果用户的输入中不包含旅行信息，你要友好的提醒它，你能做什么，然后需要他补充什么信息。
        你的语言要温柔、友好，禁止强硬的预期
        
        
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
            response_format={"type": "json_object"},
            temperature=0
        )
        content = response.choices[0].message.content
        if content is None:
            # 处理空内容的情况
            raise Exception("llm返回为空")
        user_trip_plan = UserTripPlan(**json.loads(content))
        # 把现在这个当做工作记忆
        self.memory.add_work_memory(session_id=session_id, value=content)
        if not user_trip_plan.complete and user_trip_plan.missing_fields is not None:
            print(f"❌感知结束，用户提供信息不足,需要补充信息")
            return user_trip_plan.missing_fields
        print(f"✅ 感知结束，用户提供信息充足,可以进入规划阶段")
        return ""

    def planning(self, session_id: str, user_input: str) -> str | None | Any:
        """有了用户的意图，开始规划行动"""
        self.state = AgentState.PLANNING
        self.memory.add_short_memory(session_id=session_id, memory=LlmMessage(
            role= MessageRole.user,
            content=user_input,
        ))

        llm = get_llm()

        # 获取 OpenAI Function Calling 格式的工具列表
        openai_tools = self.get_tools_for_openai()

        current_step = 0
        while current_step < 10:
            current_step += 1

            historyStr = json.dumps([msg.to_dict() for msg in self.memory.short_memory.get(session_id, [])], ensure_ascii=False)
            work_info = self.memory.work_memory.get(session_id, {})
            # amap_maps_text_search 搜索景点 keywords 历史文化  city 北京
            # maps_weather 查询天气 city 北京
            prompt = f"""你是一个旅游助手, 你可以帮助用户完成旅游规划, 你可以使用工具来帮助用户完成任务。
                   
                
                    ## 用户的最新输入:
                    {user_input}
                    
                    # 必要的信息
                    {work_info}
                    
                    # 历史消息
                    History: {historyStr}
                    
                    ## 这里面有3项工作你是必须要完成的
                    1. 帮助用户搜索景点
                    2. 帮助用户搜索酒店
                    3. 帮助用户查询天气
                    4. 当你搜集到了足够的信息，请严格按照以下JSON格式返回旅行计划
                    {res_simple_json}
                    
        
                    ## 工作流程:
                    1. 思考（Thought）: 分析用户需求，思考需要什么信息或采取什么行动
                    2. 行动（Action）: 如果需要调用工具，请明确指出要调用哪个工具以及需要的参数
                    3. 观察（Observation）: 根据工具返回的结果进行分析

                    请开始你的思考，如果需要调用工具,则返回工具调用
                    如果不需要调用工具，可以直接回答用户。
                    注意：当信息足够返回，不需要调用工具的时候，只返回JSON格式的旅行计划，也不用遵循Thought、Action、Observation
                    重点：只要json，只要json
                    """

            print(f"🧠 正在调用 {llm.model} 模型...")
            response = llm.client.chat.completions.create(
                model=llm.model,
                messages=[{"role": "user", "content": prompt}],
                tools=openai_tools if openai_tools else None,  # 传入工具定义
                tool_choice="auto",  # 让模型自动决定是否调用工具
                temperature=0
            )

           # print(f"🤖 Assistant response: {response}")
            # 处理响应
            message = response.choices[0].message
            # 检查是否有工具调用
            if message.tool_calls:
                for tool_call in message.tool_calls:
                    too_id = tool_call.id
                    tool_name = tool_call.function.name
                    tool_args = json.loads(tool_call.function.arguments)
                    print(f"🔧 模型请求调用工具: {tool_name}")
                    self.memory.add_short_memory(session_id=session_id, memory=LlmMessage(
                        role=MessageRole.tool_calls,
                        content=json.dumps({"tool_name": tool_name, "tool_args": tool_args}, ensure_ascii=False),
                    ))
                    #这里可以实际调用工具
                    result = self.call_tool(tool_name, **tool_args)
                    self.memory.add_short_memory(session_id=session_id, memory=LlmMessage(
                        role=MessageRole.tool_calls,
                        content=json.dumps(result, ensure_ascii=False),
                    ))
            else:
                print(f"💬 最终回复: {message.content}")
                self.memory.add_short_memory(session_id=session_id, memory=LlmMessage(
                    role=MessageRole.assistant,
                    content=json.dumps(message.content, ensure_ascii=False),
                ))
                return message.content or ""
        return None

    def call_tool(self, tool_name: str, **kwargs) -> Any:
        """调用指定的MCP工具"""
        if tool_name not in self.tools:
            raise KeyError(f"工具 '{tool_name}' 不存在。可用工具: {list(self.tools.keys())}")
        
        print(f"🔧 调用工具: {tool_name} with args: {kwargs}")
        result = self.tools[tool_name].call(**kwargs)
        print(f"✅ 工具调用成功: {tool_name}")
        return result
