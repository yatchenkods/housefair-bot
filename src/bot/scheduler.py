import logging
from datetime import datetime, timezone

from apscheduler.schedulers.asyncio import AsyncIOScheduler

from .client import api

logger = logging.getLogger(__name__)


async def _check_overdue(bot):
    try:
        families = await api.list_families()
        now = datetime.now(timezone.utc)
        for family in families:
            chores = await api.list_chores(family_id=family["id"], status="pending")
            for chore in chores:
                if chore.get("due_date"):
                    due = datetime.fromisoformat(chore["due_date"].replace("Z", "+00:00"))
                    if due < now:
                        await api.patch_chore(chore["id"], {"status": "overdue"})
                        await bot.send_message(
                            chat_id=family["chat_id"],
                            text=f"🔴 Задача #{chore['id']} *{chore['title']}* просрочена!",
                            parse_mode="Markdown",
                        )
    except Exception as e:
        logger.error(f"Scheduler error: {e}")


def start_scheduler(bot, interval_minutes: int = 30):
    scheduler = AsyncIOScheduler()
    scheduler.add_job(_check_overdue, "interval", minutes=interval_minutes, args=[bot])
    scheduler.start()
    return scheduler
