from fastapi import APIRouter
from app.deps import CurrentUser, SessionDep
from app.services.recommend import generate_recommendations

router = APIRouter(prefix="/recommend", tags=["recommend"])


@router.get("")
async def get_recommendations(db: SessionDep, current_user: CurrentUser):
    """
    获取个性化推荐课程：
    基于用户的 ClickHousePV/生词点击/语音时长数据，调用大模型 Structured Output 推荐课程。
    """
    return await generate_recommendations(db, current_user["userId"])
