from telegram import Update
from telegram.ext import CommandHandler, ContextTypes

from src.bot.handlers.admin_handler import get_user_context
from src.services.perplexity_service import PerplexityService
from src.services.reports_service import ReportsService


def _get_reports_service(context):
    db = context.bot_data["db"]
    perplexity = context.bot_data.get("perplexity")
    if not perplexity:
        settings = context.bot_data["settings"]
        perplexity = PerplexityService(settings.perplexity_api_key)
        context.bot_data["perplexity"] = perplexity
    return ReportsService(db, perplexity)


async def stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    family, member = await get_user_context(update, context)
    if not family or not member:
        await update.message.reply_text("Семья не найдена.")
        return

    service = _get_reports_service(context)
    text = await service.format_personal_stats(family["id"], member["id"], member["display_name"])
    await update.message.reply_text(text)


async def familystats_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    family, member = await get_user_context(update, context)
    if not family:
        await update.message.reply_text("Семья не найдена.")
        return

    service = _get_reports_service(context)
    text = await service.format_weekly_report(family["id"])
    await update.message.reply_text(text)


async def weekreport_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    family, member = await get_user_context(update, context)
    if not family:
        await update.message.reply_text("Семья не найдена.")
        return

    service = _get_reports_service(context)
    text = await service.format_weekly_report(family["id"])
    await update.message.reply_text(text)


async def monthreport_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    family, member = await get_user_context(update, context)
    if not family:
        await update.message.reply_text("Семья не найдена.")
        return

    service = _get_reports_service(context)
    text = await service.format_monthly_report(family["id"])
    await update.message.reply_text(text)


async def leaderboard_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    family, member = await get_user_context(update, context)
    if not family:
        await update.message.reply_text("Семья не найдена.")
        return

    service = _get_reports_service(context)
    text = await service.build_leaderboard(family["id"])
    await update.message.reply_text(text)


async def ai_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not context.args:
        await update.message.reply_text("Задайте вопрос: /ai <вопрос>")
        return

    question = " ".join(context.args)
    perplexity = context.bot_data.get("perplexity")
    if not perplexity:
        settings = context.bot_data["settings"]
        perplexity = PerplexityService(settings.perplexity_api_key)
        context.bot_data["perplexity"] = perplexity

    await update.message.reply_text("Думаю...")
    answer = await perplexity.ask_question(question)
    await update.message.reply_text(answer)


async def improve_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not context.args:
        await update.message.reply_text("Укажите задачу: /improve <задача>")
        return

    task = " ".join(context.args)
    perplexity = context.bot_data.get("perplexity")
    if not perplexity:
        settings = context.bot_data["settings"]
        perplexity = PerplexityService(settings.perplexity_api_key)
        context.bot_data["perplexity"] = perplexity

    await update.message.reply_text("Подбираю советы...")
    tips = await perplexity.get_improvement_tips(task)
    await update.message.reply_text(tips)


async def scheduled_weekly_report(context: ContextTypes.DEFAULT_TYPE) -> None:
    from loguru import logger
    from src.utils.helpers import get_local_now

    db = context.bot_data["db"]
    families = await db.get_all_families()

    for family in families:
        tz = family.get("timezone", "Europe/Moscow")
        now = get_local_now(tz)
        if now.weekday() != 6:
            continue

        perplexity = context.bot_data.get("perplexity")
        if not perplexity:
            settings = context.bot_data["settings"]
            perplexity = PerplexityService(settings.perplexity_api_key)
            context.bot_data["perplexity"] = perplexity

        service = ReportsService(db, perplexity)
        try:
            text = await service.format_weekly_report(family["id"])
            await context.bot.send_message(family["chat_id"], text)
        except Exception as e:
            logger.error("Failed to send weekly report to {}: {}", family["chat_id"], e)


async def scheduled_monthly_report(context: ContextTypes.DEFAULT_TYPE) -> None:
    from loguru import logger
    from src.utils.helpers import get_local_now

    db = context.bot_data["db"]
    families = await db.get_all_families()

    for family in families:
        tz = family.get("timezone", "Europe/Moscow")
        now = get_local_now(tz)
        if now.day != 1:
            continue

        perplexity = context.bot_data.get("perplexity")
        if not perplexity:
            settings = context.bot_data["settings"]
            perplexity = PerplexityService(settings.perplexity_api_key)
            context.bot_data["perplexity"] = perplexity

        service = ReportsService(db, perplexity)
        try:
            text = await service.format_monthly_report(family["id"])
            await context.bot.send_message(family["chat_id"], text)
        except Exception as e:
            logger.error("Failed to send monthly report to {}: {}", family["chat_id"], e)


def register_reports_handlers(app):
    app.add_handler(CommandHandler("stats", stats_command))
    app.add_handler(CommandHandler("familystats", familystats_command))
    app.add_handler(CommandHandler("weekreport", weekreport_command))
    app.add_handler(CommandHandler("monthreport", monthreport_command))
    app.add_handler(CommandHandler("leaderboard", leaderboard_command))
    app.add_handler(CommandHandler("ai", ai_command))
    app.add_handler(CommandHandler("improve", improve_command))

    import datetime as dt
    app.job_queue.run_daily(scheduled_weekly_report, time=dt.time(20, 0))
    app.job_queue.run_daily(scheduled_monthly_report, time=dt.time(20, 0))
