from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from ..client import api
from ..utils import get_family_and_member


async def done_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Использование: /done <id>")
        return
    try:
        chore_id = int(context.args[0])
    except ValueError:
        await update.message.reply_text("ID должен быть числом")
        return

    family, member = await get_family_and_member(update)
    if not family or not member:
        await update.message.reply_text("Сначала используйте /start")
        return

    try:
        chore = await api.complete_chore(chore_id, member["id"])
        await update.message.reply_text(f"✅ Задача *{chore['title']}* выполнена!", parse_mode="Markdown")
    except Exception as e:
        await update.message.reply_text(f"Ошибка: {e}")


async def done_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    chore_id = int(query.data.split(":")[1])

    family, member = await get_family_and_member(update)
    if not family or not member:
        await query.edit_message_text("Сначала используйте /start")
        return

    try:
        chore = await api.complete_chore(chore_id, member["id"])
        await query.edit_message_text(f"✅ Задача *{chore['title']}* выполнена!", parse_mode="Markdown")
    except Exception as e:
        await query.edit_message_text(f"Ошибка: {e}")


async def take_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    chore_id = int(query.data.split(":")[1])

    family, member = await get_family_and_member(update)
    if not family or not member:
        await query.answer("Сначала используйте /start", show_alert=True)
        return

    try:
        chore = await api.assign_chore(chore_id, mode="manual", assigned_to=member["id"])
        name = member.get("display_name") or member.get("username") or "вы"
        await query.edit_message_text(
            f"✅ Задача *{chore['title']}* назначена на {name}.",
            parse_mode="Markdown",
        )
    except Exception as e:
        await query.answer(f"Ошибка: {e}", show_alert=True)
