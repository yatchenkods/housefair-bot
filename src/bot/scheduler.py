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


class BotScheduler:
    def __init__(self, interval_minutes: int):
        self._interval_minutes = interval_minutes
        self._scheduler = AsyncIOScheduler()
        self._bot = None

    def configure_bot(self, bot):
        self._bot = bot
        self._scheduler.add_job(
            _check_overdue, "interval", minutes=self._interval_minutes, args=[bot]
        )

    def start(self):
        self._scheduler.start()

    def shutdown(self):
        if self._scheduler.running:
            self._scheduler.shutdown()


def start_scheduler(interval_minutes: int = 30) -> BotScheduler:
    return BotScheduler(interval_minutes)
