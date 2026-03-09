from fastapi import APIRouter, HTTPException

from backend.app.models.schemas import AgentResponse
from ...core.agent_manager import get_agent
from ...models.schemas import (
    TripRequest,
    TripPlanResponse,
)

router: APIRouter = APIRouter(prefix="/trip", tags=["旅行规划"])

@router.post(
    "/plan",
    response_model=TripPlanResponse,
    summary="生成旅行计划",
    description="根据用户输入的旅行需求，生成详细的旅行计划"
)
async def plan_trip(request: TripRequest):
    """
       生成旅行计划

       Args:
           request: 旅行请求参数

       Returns:
           旅行计划响应
       """
    try:
        print(f"\n{'=' * 60}")
        print(f"📥 收到旅行规划请求:")
        print("🚀 开始生成旅行计划...")
        
        # 获取全局Agent实例
        agent = get_agent()
        # 使用agent处理请求（根据你的实际需求调整参数）
        result: AgentResponse = agent.process(session_id=request.session_id, user_input=request.input)
        
        return TripPlanResponse(success=True, type=result.type, message=result.message)
    except Exception as e:
        print(f"❌ 生成旅行计划失败: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=500,
            detail=f"生成旅行计划失败: {str(e)}"
        )

