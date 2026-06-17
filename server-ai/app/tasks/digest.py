from __future__ import annotations

import logging

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from app.services.digest import handle_daily_digest

logger = logging.getLogger(__name__)

scheduler = AsyncIOScheduler()


def setup_scheduler():
    """注册定时任务（每日 0 点执行）"""
    scheduler.add_job(
        handle_daily_digest,
        trigger=CronTrigger(hour=0, minute=0, second=0),
        id="daily_digest",
        name="每日单词摘要邮件",
        replace_existing=True,
    )
    scheduler.start()
    logger.info("定时任务调度器已启动（每日 00:00 执行）")


def shutdown_scheduler():
    """关闭调度器"""
    if scheduler.running:
        scheduler.shutdown(wait=False)
        logger.info("定时任务调度器已关闭")
