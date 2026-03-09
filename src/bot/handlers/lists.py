from datetime import datetime, timezone
from telegram import Update
from telegram.ext import ContextTypes

from ..client import api


def _fmt_chore(c: dict) -> str:
    status_icon = {"pending": "⏳", "completed": "✅", "overdue": "🔴"}.get(c["status"], "❓")
    due = f"\n  📅 до {c['due_date'][:10]}" if c.get("due_date") else ""
    assigned = f"\n  👤 #{c['assigned_to']}" if c.get("assigned_to") else ""
    return f"{status_icon} #{c['id']} *{c['title']}*{due}{assigned}"


async def _get_family_and_member(update: Update):
    chat_id = update.effective_chat.id
    user = update.effective_user
    family = await api.get_family_by_chat(chat_id)
    if not family:
        return None, None
    member = await api.get_member_by_user(user.id, family["id"])
    return family, member


async def mytasks(update: Update, context: ContextTypes.DEFAULT_TYPE):
    family, member = await _get_family_and_member(update)
    if not family or not member:
        await update.message.reply_text("Сначала используйте /start")
        return
    chores = await api.list_chores(family_id=family["id"], assigned_to=member["id"], status="pending")
    if not chores:
        await update.message.reply_text("У вас нет активных задач 🎉")
        return
    lines = [_fmt_chore(c) for c in chores]
    await update.message.reply_text("Ваши задачи:\n" + "\n".join(lines), parse_mode="Markdown")


async def alltasks(update: Update, context: ContextTypes.DEFAULT_TYPE):
    family, _ = await _get_family_and_member(update)
    if not family:
        await update.message.reply_text("Сначала используйте /start")
        return
    chores = await api.list_chores(family_id=family["id"])
    if not chores:
        await update.message.reply_text("Нет задач")
        return
    lines = [_fmt_chore(c) for c in chores]
    await update.message.reply_text("Все задачи:\n" + "\n".join(lines), parse_mode="Markdown")


async def pending(update: Update, context: ContextTypes.DEFAULT_TYPE):
    family, _ = await _get_family_and_member(update)
    if not family:
        await update.message.reply_text("Сначала используйте /start")
        return
    chores = await api.list_chores(family_id=family["id"], status="pending")
    if not chores:
        await update.message.reply_text("Нет невыполненных задач 🎉")
        return
    lines = [_fmt_chore(c) for c in chores]
    await update.message.reply_text("Невыполненные:\n" + "\n".join(lines), parse_mode="Markdown")


async def history(update: Update, context: ContextTypes.DEFAULT_TYPE):
    family, _ = await _get_family_and_member(update)
    if not family:
        await update.message.reply_text("Сначала используйте /start")
        return
    chores = await api.get_history(family["id"])
    if not chores:
        await update.message.reply_text("История пуста")
        return
    lines = [_fmt_chore(c) for c in chores]
    await update.message.reply_text("История:\n" + "\n".join(lines), parse_mode="Markdown")
