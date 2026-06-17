from __future__ import annotations

from datetime import datetime, timedelta

from langchain_core.tools import tool
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import User, WordBookRecord


def create_query_tool(session: AsyncSession):
    @tool
    async def query_tool(userId: str) -> dict:
        """根据用户id查询用户学习的单词记录"""
        stmt = select(User).where(User.id == userId)
        result = await session.execute(stmt)
        user = result.scalar_one_or_none()
        if not user:
            return {"error": "用户不存在"}

        today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        tomorrow_start = today_start + timedelta(days=1)

        records_stmt = (
            select(WordBookRecord)
            .where(WordBookRecord.user_id == userId)
            .where(WordBookRecord.created_at >= today_start)
            .where(WordBookRecord.created_at < tomorrow_start)
        )
        records_result = await session.execute(records_stmt)
        records = records_result.scalars().all()

        return {
            "email": user.email,
            "name": user.name,
            "word_number": user.word_number,
            "today_words_count": len(records),
        }

    return query_tool
