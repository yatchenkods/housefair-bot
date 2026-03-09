import os
import random

from loguru import logger
from telegram.ext import ContextTypes

from src.services.chores_service import ChoresService
from src.utils.helpers import get_local_now


REMINDER_MORNING_TEXTS = [
    "Доброе утро! Вот ваши задачи на сегодня:",
    "Новый день - новые дела! Проверьте свои задачи:",
    "Утренняя сводка дел готова:",
]

REMINDER_EVENING_TEXTS = [
    "Добрый вечер! Не забудьте про невыполненные задачи:",
    "Вечерняя проверка: есть незакрытые дела:",
    "Напоминаем о задачах, которые ждут выполнения:",
]

ESCALATION_TEXTS = [
    "Задача \"{title}\" не выполнена уже более 3 дней. Нужна помощь?",
    "Внимание! \"{title}\" ожидает выполнения уже давно.",
]


async def reminder_job(context: ContextTypes.DEFAULT_TYPE) -> None:
    db = context.bot_data["db"]
    families = await db.get_all_families()

    for family in families:
        tz = family.get("timezone", "Europe/Moscow")
        now = get_local_now(tz)
        hour = now.hour

        is_morning = 10 <= hour < 11
        is_evening = 18 <= hour < 19

        if not is_morning and not is_evening:
            continue

        members = await db.get_family_members(family["id"])
        for member in members:
            if not member.get("user_id"):
                continue

            chores = await db.get_chores_by_member(member["id"], status="pending")
            overdue = await db.get_chores_by_member(member["id"], status="overdue")
            all_chores = chores + overdue

            if not all_chores:
                continue

            texts = REMINDER_MORNING_TEXTS if is_morning else REMINDER_EVENING_TEXTS
            header = random.choice(texts)
            lines = [header]
            for c in all_chores[:5]:
                icon = "!" if c["status"] == "overdue" else "-"
                lines.append(f"  {icon} #{c['id']} {c['title']}")

            try:
                await context.bot.send_message(family["chat_id"], "\n".join(lines))
            except Exception as e:
                logger.error("Failed to send reminder to chat {}: {}", family["chat_id"], e)
            break  # one reminder per family per interval


async def escalation_job(context: ContextTypes.DEFAULT_TYPE) -> None:
    db = context.bot_data["db"]
    old_chores = await db.get_pending_chores_older_than(3)

    family_chores = {}
    for c in old_chores:
        family_chores.setdefault(c["family_id"], []).append(c)

    for family_id, chores in family_chores.items():
        family = await db.get_family(family_id)
        if not family:
            continue
        lines = ["Эскалация: следующие задачи не выполнены более 3 дней:\n"]
        for c in chores[:5]:
            lines.append(f"  #{c['id']} {c['title']}")
        try:
            await context.bot.send_message(family["chat_id"], "\n".join(lines))
        except Exception as e:
            logger.error("Escalation failed for chat {}: {}", family["chat_id"], e)


async def recurring_job(context: ContextTypes.DEFAULT_TYPE) -> None:
    db = context.bot_data["db"]
    service = ChoresService(db)
    count = await service.recreate_recurring()
    if count > 0:
        logger.info("Recreated {} recurring chores", count)


async def overdue_job(context: ContextTypes.DEFAULT_TYPE) -> None:
    db = context.bot_data["db"]
    service = ChoresService(db)
    count = await service.mark_overdue()
    if count > 0:
        logger.info("Marked {} chores as overdue", count)


async def backup_job(context: ContextTypes.DEFAULT_TYPE) -> None:
    db = context.bot_data["db"]
    settings = context.bot_data["settings"]
    backup_dir = os.path.join(os.path.dirname(settings.database_path), "backups")
    result = await db.backup(backup_dir, settings.backup_retention_days)
    if result:
        logger.info("Backup completed: {}", result)


def setup_scheduler(app, settings) -> None:
    job_queue = app.job_queue

    job_queue.run_repeating(reminder_job, interval=1800, first=10)
    job_queue.run_daily(overdue_job, time=__import__("datetime").time(0, 1))
    job_queue.run_daily(recurring_job, time=__import__("datetime").time(0, 5))

    if settings.backup_enabled:
        job_queue.run_daily(
            backup_job,
            time=__import__("datetime").time(settings.backup_hour, 0),
        )

    logger.info("Scheduler configured")
