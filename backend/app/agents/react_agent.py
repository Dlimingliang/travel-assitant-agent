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
        prompt = f"""你是一个温柔友好的旅行助手，负责从用户对话中提取旅行计划信息。

        ## 当前已收集的信息
        {current_info_str}
        
        ## 用户最新消息
        {user_input}
        
        ## 任务说明
        从用户消息中提取旅行信息，并与已收集的信息合并。
        
        ### 必要字段（4个）
        | 字段 | 说明 | 示例 |
        |------|------|------|
        | city | 目的地城市 | "北京" |
        | start_date | 开始日期(YYYY-MM-DD) | "2025-03-20" |
        | travel_days | 旅行天数(整数) | 3 |
        | accommodation | 住宿偏好 | "经济型酒店" |
        
        ### 可选字段
        - free_text_input: 额外要求，如"希望多安排一些博物馆"
        
        ## 处理规则
        1. 新消息中的信息 → 更新对应字段
        2. 新消息未提及但已有的信息 → 保留原值
        3. 新旧信息冲突 → 以新消息为准
        
        ## complete 判断逻辑（重要！）
        请逐一检查以下4个必要字段的最终值：
        - city 是否有值？
        - start_date 是否有值？
        - travel_days 是否有值？
        - accommodation 是否有值？
        
        **只有当以上4个字段全部有值（非null）时，complete = true，否则 complete = false**
        
        ## missing_fields 生成规则
        - 如果 complete = true → missing_fields = null
        - 如果 complete = false → missing_fields = 用温柔的语气列出缺失的字段，例如："请告诉我您的出发日期和旅行天数哦~"
        
        ## 输出格式
        严格按以下JSON格式输出，所有字段必须存在：
        ```json
        {{
          "complete": true或false,
          "city": "城市名"或null,
          "start_date": "YYYY-MM-DD"或null,
          "travel_days": 整数或null,
          "accommodation": "住宿偏好"或null,
          "free_text_input": "额外要求"或null,
          "missing_fields": "缺失提示"或null
        }}
        ```
        ```
        
        现在请处理用户的消息，输出JSON结果："""
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
        while current_step < 20:
            current_step += 1

            historyStr = json.dumps([msg.to_dict() for msg in self.memory.short_memory.get(session_id, [])], ensure_ascii=False)
            work_info = self.memory.work_memory.get(session_id, {})
            
            prompt = f"""你是一个专业的旅游规划助手，帮助用户制定完整的旅行计划。

## 当前信息

**用户需求：** {work_info}
**用户输入：** {user_input}

## 对话历史
{historyStr}

---

## 你的任务

为用户规划旅行，需要完成以下3项信息收集：

| # | 任务 | 工具 | 如何判断已完成 |
|---|------|------|----------------|
| 1 | 酒店 | `amap--maps_text_search` | 历史中有酒店搜索结果 |
| 2 | 景点 | `amap--maps_text_search` | 历史中有景点搜索结果 |
| 3 | 天气 | `amap--maps_weather` | 历史中有天气查询结果 |

---

## 【核心】执行前必须完成的检查

**请先逐一检查对话历史，回答以下问题：**

1. 历史中是否已有酒店搜索的调用和结果？
2. 历史中是否已有景点搜索的调用和结果？
3. 历史中是否已有天气查询的调用和结果？

**然后根据检查结果决定：**

- **如果3项都已完成** → 立即输出JSON旅行计划，不调用任何工具
- **如果有未完成项** → 只调用1个缺失任务的工具

---

## 输出规则

### 未完成时：调用工具
正常调用对应工具

### 全部完成时：输出JSON（重要！）

直接输出以下格式的纯JSON，**不要**有：
- 任何开场白或解释
- markdown代码块 ``` 标记  
- "这是您的旅行计划"等文字

JSON格式：
{res_simple_json}

---

## 绝对禁止
❌ 重复调用历史中已成功的工具
❌ 在JSON外添加任何文字

开始执行："""

            print(f"🧠 正在调用 {llm.model} 模型...")
            response = llm.client.chat.completions.create(
                model=llm.model,
                messages=[{"role": "user", "content": prompt}],
                tools=openai_tools if openai_tools else None,  # 传入工具定义
                tool_choice="auto",  # 让模型自动决定是否调用工具
                temperature=0,
                timeout=10000000
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
