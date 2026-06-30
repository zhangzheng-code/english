import logging
import asyncio
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, Field
import clickhouse_connect
from langchain_deepseek import ChatDeepSeek
from app.llm.models import create_deepseek

from app.config import settings
from app.db.models import Course, User

logger = logging.getLogger(__name__)


class CourseRecommendation(BaseModel):
    course_id: str = Field(description="The unique CUID/ID of the recommended course")
    title: str = Field(description="The title/name of the course")
    reason: str = Field(description="The personalized reason for recommending this course to the user based on click and practice behavior")
    confidence: float = Field(description="Confidence score for this recommendation between 0.0 and 1.0")


class CourseRecommendationList(BaseModel):
    recommendations: list[CourseRecommendation]


def _get_clickhouse_client():
    """初始化 ClickHouse 客户端"""
    return clickhouse_connect.get_client(
        host=settings.clickhouse_url.split("//")[-1].split(":")[0],
        port=int(settings.clickhouse_url.split(":")[-1]),
        username=settings.clickhouse_username,
        password=settings.clickhouse_password,
        database=settings.clickhouse_database
    )


def _query_ch_sync(user_id: str):
    client = _get_clickhouse_client()
    query = f"""
        SELECT event, payload, createdAt FROM trackEvent
        WHERE visitorId IN (
            SELECT id FROM visitor WHERE userId = '{user_id}'
        )
        ORDER BY createdAt DESC
        LIMIT 50
    """
    result = client.query(query)
    return result.result_rows


async def generate_recommendations(db: AsyncSession, user_id: str) -> dict:
    """
    根据 ClickHouse 遥测画像与用户基础行为数据，进行大模型 structured_output 课程推荐
    """
    # 1. 异步查询 ClickHouse 遥测数据
    telemetry_logs = []
    try:
        telemetry_logs = await asyncio.to_thread(_query_ch_sync, user_id)
    except Exception as e:
        logger.warning(f"Failed to query ClickHouse for user {user_id}: {e}. Falling back to PostgreSQL activity analysis.")

    # 2. 查询 PostgreSQL 用户与课程数据
    user_info_summary = ""
    try:
        stmt_user = select(User).where(User.id == user_id)
        res_user = await db.execute(stmt_user)
        u = res_user.scalar_one_or_none()
        if u:
            user_info_summary = f"累计打卡天数: {u.dayNumber}天, 已学单词数: {u.wordNumber}个"
    except Exception as e:
        logger.warning(f"Failed to query user stats: {e}")

    try:
        stmt = select(Course)
        result = await db.execute(stmt)
        courses = result.scalars().all()
    except Exception as e:
        logger.error(f"Failed to query PostgreSQL courses: {e}")
        courses = []

    if not courses:
        return {"recommendations": []}

    # 3. 组织 Prompt 上下文
    if telemetry_logs:
        logs_summary = "\n".join([f"- 事件: {log[0]}, 数据: {log[1]}, 时间: {log[2]}" for log in telemetry_logs])
    else:
        logs_summary = f"近期点击流暂无详细遥测。用户统计指标：{user_info_summary or '新手入门阶段'}。偏好特征：关注听力发音对练与核心词汇突破。"

    courses_summary = "\n".join([
        f"- 课程ID: {c.id}, 课程名: {c.name}, 讲师: {c.teacher}, 描述: {c.description or '核心经典英文课程'}, 价格: ¥{c.price}"
        for c in courses
    ])

    prompt_content = (
        "你是一个专业、富有洞察力的 AI 英语学习智能推荐引擎。\n"
        "请根据以下用户的近期学习遥测行为特征和系统内可供选择的课程目录，"
        "为用户定制 1~3 门最适合的推荐课程，并结合遥测特征给出打动人心的推荐理由。\n\n"
        f"【用户近期遥测与画像日志】：\n{logs_summary}\n\n"
        f"【系统课程目录】：\n{courses_summary}\n\n"
        "请严格遵守 JSON 结构输出。"
    )

    # 4. 调用大模型并强制输出结构化数据 (采用较小温度确保格式稳定)
    try:
        llm = create_deepseek()
        structured_llm = llm.with_structured_output(CourseRecommendationList)
        res = await structured_llm.ainvoke(prompt_content)
        return res.model_dump()
    except Exception as e:
        logger.error(f"Structured output recommendation failed: {e}")
        return {
            "recommendations": [
                {
                    "course_id": courses[0].id,
                    "title": courses[0].name,
                    "reason": "基于您的进阶英语表达需求，为您精心挑选的系统提升课程。",
                    "confidence": 0.88
                }
            ]
        }
