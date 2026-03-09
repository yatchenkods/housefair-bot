from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from ..client import api


async def done_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Использование: /done <id>")
        return
    try:
        chore_id = int(context.args[0])
    except ValueError:
        await update.message.reply_text("ID должен быть числом")
        return

    user = update.effective_user
    chat_id = update.effective_chat.id

    family = await api.get_family_by_chat(chat_id)
    if not family:
        await update.message.reply_text("Сначала используйте /start")
        return

    member = await api.get_member_by_user(user.id, family["id"])
    if not member:
        await update.message.reply_text("Вы не зарегистрированы. Используйте /start")
        return

    try:
        chore = await api.complete_chore(chore_id, member["id"])
        await update.message.reply_text(f"✅ Задача #{chore_id} *{chore['title']}* выполнена!", parse_mode="Markdown")
    except Exception as e:
        await update.message.reply_text(f"Ошибка: {e}")


async def done_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    chore_id = int(query.data.split(":")[1])

    user = update.effective_user
    chat_id = update.effective_chat.id

    family = await api.get_family_by_chat(chat_id)
    if not family:
        await query.edit_message_text("Сначала используйте /start")
        return

    member = await api.get_member_by_user(user.id, family["id"])
    if not member:
        await query.edit_message_text("Вы не зарегистрированы. Используйте /start")
        return

    try:
        chore = await api.complete_chore(chore_id, member["id"])
        await query.edit_message_text(f"✅ Задача #{chore_id} *{chore['title']}* выполнена!", parse_mode="Markdown")
    except Exception as e:
        await query.edit_message_text(f"Ошибка: {e}")
