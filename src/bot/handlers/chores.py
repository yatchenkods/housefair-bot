from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ContextTypes,
    ConversationHandler,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    filters,
)

from ..client import api

TITLE, TYPE, CATEGORY, PHOTO, ASSIGN = range(5)

CHORE_TYPES = ["one_time", "daily", "weekly", "monthly"]
CATEGORIES = ["посуда", "уборка", "готовка", "другое"]
ASSIGN_MODES = ["manual", "random", "rotation", "free"]


async def addchore_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    await update.message.reply_text("Введите название задачи:")
    return TITLE


async def got_title(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["title"] = update.message.text
    keyboard = [[InlineKeyboardButton(t, callback_data=f"type:{t}")] for t in CHORE_TYPES]
    await update.message.reply_text("Выберите тип:", reply_markup=InlineKeyboardMarkup(keyboard))
    return TYPE


async def got_type(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    context.user_data["chore_type"] = query.data.split(":")[1]
    keyboard = [[InlineKeyboardButton(c, callback_data=f"cat:{c}")] for c in CATEGORIES]
    await query.edit_message_text("Выберите категорию:", reply_markup=InlineKeyboardMarkup(keyboard))
    return CATEGORY


async def got_category(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    context.user_data["category"] = query.data.split(":")[1]
    keyboard = [[InlineKeyboardButton("Пропустить", callback_data="photo:skip")]]
    await query.edit_message_text("Отправьте фото (или нажмите Пропустить):", reply_markup=InlineKeyboardMarkup(keyboard))
    return PHOTO


async def got_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message and update.message.photo:
        context.user_data["photo_url"] = update.message.photo[-1].file_id
    keyboard = [[InlineKeyboardButton(m, callback_data=f"assign:{m}")] for m in ASSIGN_MODES]
    msg = update.message or update.callback_query.message
    if update.callback_query:
        await update.callback_query.answer()
        await update.callback_query.edit_message_text("Назначение:", reply_markup=InlineKeyboardMarkup(keyboard))
    else:
        await msg.reply_text("Назначение:", reply_markup=InlineKeyboardMarkup(keyboard))
    return ASSIGN


async def got_assign(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    mode = query.data.split(":")[1]

    chat_id = update.effective_chat.id
    user = update.effective_user

    family = await api.get_family_by_chat(chat_id)
    if not family:
        await query.edit_message_text("Сначала используйте /start")
        return ConversationHandler.END

    member = await api.get_member_by_user(user.id, family["id"])
    if not member:
        await query.edit_message_text("Вы не зарегистрированы. Используйте /start")
        return ConversationHandler.END

    chore_payload = {
        "family_id": family["id"],
        "title": context.user_data["title"],
        "chore_type": context.user_data.get("chore_type", "one_time"),
        "category": context.user_data.get("category"),
        "created_by": member["id"],
    }
    chore = await api.create_chore(chore_payload)
    await api.assign_chore(chore["id"], mode)

    await query.edit_message_text(
        f"✅ Задача создана!\n"
        f"*{chore['title']}* (#{chore['id']})\n"
        f"Тип: {chore['chore_type']}\n"
        f"Назначение: {mode}",
        parse_mode="Markdown",
    )
    return ConversationHandler.END


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Отменено.")
    return ConversationHandler.END


def get_chore_conversation():
    return ConversationHandler(
        entry_points=[
            CommandHandler("addchore", addchore_start),
            CommandHandler("task", addchore_start),
        ],
        states={
            TITLE: [MessageHandler(filters.TEXT & ~filters.COMMAND, got_title)],
            TYPE: [CallbackQueryHandler(got_type, pattern="^type:")],
            CATEGORY: [CallbackQueryHandler(got_category, pattern="^cat:")],
            PHOTO: [
                MessageHandler(filters.PHOTO, got_photo),
                CallbackQueryHandler(got_photo, pattern="^photo:skip"),
            ],
            ASSIGN: [CallbackQueryHandler(got_assign, pattern="^assign:")],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )
