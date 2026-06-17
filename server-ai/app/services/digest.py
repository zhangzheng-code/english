from __future__ import annotations

import logging
from datetime import datetime, timedelta

import markdown
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.config import settings
from app.db.engine import async_session
from app.db.models import User, WordBook, WordBookRecord

logger = logging.getLogger(__name__)


async def get_qualifying_users(session: AsyncSession) -> list[dict]:
    """
    筛选符合条件的用户：
    - 开启了定时任务 (isTimingTask=True)
    - 定时任务时间不为空
    - 邮箱不为空
    - 今天学过单词
    """
    today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    tomorrow_start = today_start + timedelta(days=1)

    # 先查所有开启了定时任务且有邮箱的用户
    stmt = (
        select(User)
        .where(User.is_timing_task == True)  # noqa: E712
        .where(User.timing_task_time != "")
        .where(User.email.isnot(None))
    )
    result = await session.execute(stmt)
    users = result.scalars().all()

    qualifying = []
    for user in users:
        # 关联查询今天学过的单词（join WordBook 获取单词详情）
        records_stmt = (
            select(WordBookRecord)
            .options(selectinload(WordBookRecord.word))
            .where(WordBookRecord.user_id == user.id)
            .where(WordBookRecord.created_at >= today_start)
            .where(WordBookRecord.created_at < tomorrow_start)
        )
        records_result = await session.execute(records_stmt)
        records = records_result.scalars().all()

        if records:
            words = []
            for r in records:
                word_text = r.word.word if r.word else r.word_id
                translation = r.word.translation if r.word else ""
                words.append({"word": word_text, "translation": translation, "is_master": r.is_master})

            qualifying.append({
                "id": user.id,
                "name": user.name,
                "email": user.email,
                "timing_task_time": user.timing_task_time,
                "word_number": user.word_number,
                "today_words": words,
                "today_count": len(words),
                "mastered_count": sum(1 for w in words if w["is_master"]),
            })

    return qualifying


def build_report_html(user: dict) -> str:
    """根据用户学习数据构建 HTML 邮件内容"""
    today = datetime.utcnow().strftime("%Y-%m-%d")

    word_rows = ""
    for w in user["today_words"]:
        status = "✅" if w["is_master"] else "📖"
        word_rows += f"<tr><td>{status}</td><td>{w['word']}</td><td>{w['translation']}</td></tr>"

    return f"""
    <html>
    <body style="font-family: 'Microsoft YaHei', sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
        <h2 style="color: #4a90d9;">📚 每日单词记忆报告</h2>
        <p>Hi {user['name']}，以下是你的 <strong>{today}</strong> 学习总结：</p>

        <div style="background: #f5f7fa; padding: 15px; border-radius: 8px; margin: 15px 0;">
            <p>📊 今日学习：<strong>{user['today_count']}</strong> 个单词</p>
            <p>✅ 已掌握：<strong>{user['mastered_count']}</strong> 个</p>
            <p>📈 累计词汇：<strong>{user['word_number']}</strong> 个</p>
        </div>

        <h3>今日单词列表</h3>
        <table style="width: 100%; border-collapse: collapse;">
            <tr style="background: #4a90d9; color: white;">
                <th style="padding: 8px; text-align: left;">状态</th>
                <th style="padding: 8px; text-align: left;">单词</th>
                <th style="padding: 8px; text-align: left;">释义</th>
            </tr>
            {word_rows}
        </table>

        <p style="color: #999; margin-top: 20px; font-size: 12px;">
            坚持每天学习，积少成多！—— English App
        </p>
    </body>
    </html>
    """


async def send_email(to: str, subject: str, html: str) -> bool:
    """异步发送邮件"""
    import aiosmtplib
    from email.mime.text import MIMEText

    msg = MIMEText(html, "html", "utf-8")
    msg["Subject"] = subject
    msg["From"] = settings.email_from
    msg["To"] = to

    try:
        await aiosmtplib.send(
            msg,
            hostname=settings.email_host,
            port=settings.email_port,
            use_tls=settings.email_use_ssl,
            username=settings.email_user,
            password=settings.email_password,
        )
        return True
    except Exception as e:
        logger.error(f"邮件发送失败 [{to}]: {e}")
        return False


async def handle_daily_digest():
    """每日定时任务：查询符合条件的用户，生成报告并发送邮件"""
    logger.info("每日摘要任务开始执行")

    try:
        async with async_session() as session:
            users = await get_qualifying_users(session)
    except Exception as e:
        logger.error(f"查询用户失败: {e}")
        return

    if not users:
        logger.info("今日无符合条件的用户")
        return

    logger.info(f"找到 {len(users)} 个符合条件的用户")

    sent_count = 0
    for user in users:
        try:
            html = build_report_html(user)
            success = await send_email(
                to=user["email"],
                subject=f"📚 {user['name']}的每日单词报告",
                html=html,
            )
            if success:
                sent_count += 1
                logger.info(f"邮件已发送给 {user['email']}")
        except Exception as e:
            logger.error(f"用户 {user['id']} 处理失败: {e}")

    logger.info(f"摘要任务完成，成功发送 {sent_count}/{len(users)} 封邮件")
