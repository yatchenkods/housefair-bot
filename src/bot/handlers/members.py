from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from ..client import api
from ..utils import get_family_and_member


async def members_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    family, current = await get_family_and_member(update)
    if not family or not current:
        await update.message.reply_text("Семья не найдена. Введите /start.")
        return

    members = await api.list_members(family["id"])
    if not members:
        await update.message.reply_text("В семье нет участников.")
        return

    is_admin = current["role"] == "admin"

    lines = []
    for m in members:
        icon = "👑" if m["role"] == "admin" else "👤"
        lines.append(f"{icon} {m['display_name']}")
    text = f"Участники семьи *{family['name']}*:\n\n" + "\n".join(lines)

    keyboard = []
    if is_admin:
        for m in members:
            if m["role"] != "admin":
                keyboard.append([InlineKeyboardButton(
                    f"Назначить админом: {m['display_name']}",
                    callback_data=f"promote:{m['id']}"
                )])

    reply_markup = InlineKeyboardMarkup(keyboard) if keyboard else None
    await update.message.reply_text(text, parse_mode="Markdown", reply_markup=reply_markup)


async def addmember_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    family, current = await get_family_and_member(update)
    if not family or not current:
        await update.message.reply_text("Семья не найдена. Введите /start.")
        return

    if current["role"] != "admin":
        await update.message.reply_text("Эта команда доступна только администраторам.")
        return

    bot_username = context.bot.username
    invite_link = f"https://t.me/{bot_username}?start=join_{family['chat_id']}"
    await update.message.reply_text(
        f"Ссылка для вступления в семью <b>{family['name']}</b>:\n\n{invite_link}",
        parse_mode="HTML",
    )


async def promote_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    family, current = await get_family_and_member(update)
    if not family or not current:
        await query.edit_message_text("Семья не найдена.")
        return

    if current["role"] != "admin":
        await query.edit_message_text("Недостаточно прав.")
        return

    member_id = int(query.data.split(":")[1])
    updated = await api.update_member_role(member_id, "admin")
    await query.edit_message_text(f"✅ {updated['display_name']} теперь администратор.")
