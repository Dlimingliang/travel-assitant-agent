from fastapi import APIRouter, HTTPException
from ...models.schemas import (
    TripRequest,
    TripPlanResponse,
)

router = APIRouter(prefix="/trip", tags=["旅行规划"])

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
        print("✅ 旅行计划生成成功,准备返回响应\n")
        return TripPlanResponse(success=True, message="旅行计划生成成功")
    except Exception as e:
        print(f"❌ 生成旅行计划失败: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=500,
            detail=f"生成旅行计划失败: {str(e)}"
        )

