from datetime import datetime, timedelta, timezone
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from ..client import api
from ..utils import get_family_and_member


def _fmt_chore(c: dict) -> str:
    status_icon = {"pending": "⏳", "completed": "✅", "overdue": "🔴"}.get(c["status"], "❓")
    due = f"\n  📅 до {c['due_date'][:10]}" if c.get("due_date") else ""
    assigned = f"\n  👤 #{c['assigned_to']}" if c.get("assigned_to") else ""
    return f"{status_icon} #{c['id']} *{c['title']}*{due}{assigned}"


async def mytasks(update: Update, context: ContextTypes.DEFAULT_TYPE):
    family, member = await get_family_and_member(update)
    if not family or not member:
        await update.message.reply_text("Сначала используйте /start")
        return
    chores = await api.list_chores(family_id=family["id"], assigned_to=member["id"], status="pending")
    if not chores:
        await update.message.reply_text("У вас нет активных задач 🎉")
        return
    keyboard = [
        [InlineKeyboardButton(
            f"✅ Выполнить: {c['title'][:30]} (#{c['id']})",
            callback_data=f"done:{c['id']}"
        )]
        for c in chores
    ]
    await update.message.reply_text(
        "Ваши задачи:",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )


async def alltasks(update: Update, context: ContextTypes.DEFAULT_TYPE):
    family, _ = await get_family_and_member(update)
    if not family:
        await update.message.reply_text("Сначала используйте /start")
        return
    chores = await api.list_chores(family_id=family["id"])
    cutoff = datetime.now(timezone.utc) - timedelta(days=3)
    visible = []
    for c in chores:
        if c["status"] != "completed":
            visible.append(c)
        elif c.get("completed_at") and datetime.fromisoformat(c["completed_at"]).replace(tzinfo=timezone.utc) >= cutoff:
            visible.append(c)
    if not visible:
        await update.message.reply_text("Нет задач")
        return
    lines = [_fmt_chore(c) for c in visible]
    await update.message.reply_text("Все задачи:\n" + "\n".join(lines), parse_mode="Markdown")


async def pending(update: Update, context: ContextTypes.DEFAULT_TYPE):
    family, _ = await get_family_and_member(update)
    if not family:
        await update.message.reply_text("Сначала используйте /start")
        return
    chores = await api.list_chores(family_id=family["id"], status="pending")
    unassigned = [c for c in chores if c.get("assigned_to") is None]
    if not unassigned:
        await update.message.reply_text("Нет свободных задач 🎉")
        return
    keyboard = [
        [InlineKeyboardButton(
            f"⚡ Взять: {c['title'][:30]} (#{c['id']})",
            callback_data=f"take:{c['id']}"
        )]
        for c in unassigned
    ]
    await update.message.reply_text(
        "Свободные задачи:",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )


async def history(update: Update, context: ContextTypes.DEFAULT_TYPE):
    family, _ = await get_family_and_member(update)
    if not family:
        await update.message.reply_text("Сначала используйте /start")
        return
    chores = await api.get_history(family["id"])
    if not chores:
        await update.message.reply_text("История пуста")
        return
    lines = [_fmt_chore(c) for c in chores]
    await update.message.reply_text("История:\n" + "\n".join(lines), parse_mode="Markdown")
