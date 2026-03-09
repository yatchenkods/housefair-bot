from telegram import Update
from telegram.ext import CallbackQueryHandler, CommandHandler, ContextTypes

from loguru import logger

from src.bot.keyboards import settings_keyboard, timezone_keyboard, assign_mode_keyboard, webapp_keyboard


async def get_user_context(update: Update, context: ContextTypes.DEFAULT_TYPE):
    db = context.bot_data["db"]
    user = update.effective_user
    chat_id = update.effective_chat.id

    family = await db.get_family_by_chat(chat_id)
    if not family:
        return None, None

    member = await db.get_member_by_user_id(user.id)
    if not member:
        members = await db.get_family_members(family["id"])
        for m in members:
            if m["username"] == (user.username or ""):
                await db.bind_member_user_id(m["id"], user.id)
                member = await db.get_member_by_user_id(user.id)
                break

    return family, member


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    text = (
        "Привет! Я бот для управления домашними делами.\n\n"
        "Для начала создайте семью командой /addfamily <название>\n"
        "Затем добавьте участников: /addmember @username\n\n"
        "Используйте /help для списка команд."
    )
    bot_settings = context.bot_data.get("settings")
    webapp_url = getattr(bot_settings, "webapp_url", "") if bot_settings else ""
    if webapp_url:
        await update.message.reply_text(text, reply_markup=webapp_keyboard(webapp_url))
    else:
        await update.message.reply_text(text)


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    text = (
        "Команды бота:\n\n"
        "Администрирование:\n"
        "/addfamily <название> — создать семью\n"
        "/addmember <@username> — добавить участника\n"
        "/removemember <@username> — удалить участника\n"
        "/familylist — список семьи\n"
        "/settings — настройки\n\n"
        "Домашние дела:\n"
        "/addchore — добавить задачу\n"
        "/mytasks — мои задачи\n"
        "/alltasks — все задачи семьи\n"
        "/done — отметить выполнение\n"
        "/pending — невыполненные задачи\n"
        "/history — история\n\n"
        "Кулинария:\n"
        "/addproduct — добавить продукт\n"
        "/myproducts — список продуктов\n"
        "/removeproduct — удалить продукт\n"
        "/recipe — сгенерировать рецепт\n"
        "/suggest — быстрый рецепт\n"
        "/cooked — отметить приготовление\n"
        "/shopping — список покупок\n\n"
        "Отчеты:\n"
        "/stats — моя статистика\n"
        "/familystats — статистика семьи\n"
        "/weekreport — отчет за неделю\n"
        "/monthreport — отчет за месяц\n"
        "/leaderboard — таблица лидеров\n\n"
        "AI-помощник:\n"
        "/ai <вопрос> — задать вопрос\n"
        "/improve <задача> — совет по задаче"
    )
    await update.message.reply_text(text)


async def addfamily_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    db = context.bot_data["db"]
    chat_id = update.effective_chat.id
    user = update.effective_user

    existing = await db.get_family_by_chat(chat_id)
    if existing:
        await update.message.reply_text("Семья уже создана для этого чата.")
        return

    if not context.args:
        await update.message.reply_text("Укажите название: /addfamily <название>")
        return

    name = " ".join(context.args)
    family_id = await db.create_family(name, chat_id)
    display_name = user.full_name or user.username or str(user.id)
    await db.add_member(
        family_id, user.username or str(user.id), display_name, role="admin", user_id=user.id
    )
    logger.info("Family '{}' created by {}", name, user.username)
    await update.message.reply_text(
        f"Семья \"{name}\" создана! Вы — администратор.\n"
        f"Добавьте участников: /addmember @username"
    )


async def addmember_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    db = context.bot_data["db"]
    family, member = await get_user_context(update, context)

    if not family:
        await update.message.reply_text("Сначала создайте семью: /addfamily")
        return
    if not member or member["role"] != "admin":
        await update.message.reply_text("Только администратор может добавлять участников.")
        return
    if not context.args:
        await update.message.reply_text("Укажите username: /addmember @username")
        return

    username = context.args[0].lstrip("@")
    existing = await db.get_member_by_username(family["id"], username)
    if existing:
        await update.message.reply_text(f"@{username} уже в семье.")
        return

    await db.add_member(family["id"], username, username, role="member")
    await update.message.reply_text(
        f"@{username} добавлен(а) в семью. "
        f"При первом сообщении в чат аккаунт привяжется автоматически."
    )


async def removemember_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    db = context.bot_data["db"]
    family, member = await get_user_context(update, context)

    if not family:
        await update.message.reply_text("Семья не найдена.")
        return
    if not member or member["role"] != "admin":
        await update.message.reply_text("Только администратор может удалять участников.")
        return
    if not context.args:
        await update.message.reply_text("Укажите username: /removemember @username")
        return

    username = context.args[0].lstrip("@")
    target = await db.get_member_by_username(family["id"], username)
    if not target:
        await update.message.reply_text(f"@{username} не найден(а) в семье.")
        return
    if target["role"] == "admin":
        await update.message.reply_text("Нельзя удалить администратора.")
        return

    await db.remove_member(target["id"])
    await update.message.reply_text(f"@{username} удален(а) из семьи.")


async def familylist_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    db = context.bot_data["db"]
    family, member = await get_user_context(update, context)

    if not family:
        await update.message.reply_text("Семья не найдена. Создайте: /addfamily")
        return

    members = await db.get_family_members(family["id"])
    lines = [f"Семья \"{family['name']}\":\n"]
    for m in members:
        role_icon = "[admin]" if m["role"] == "admin" else ""
        lines.append(f"  @{m['username']} {m['display_name']} {role_icon}")
    await update.message.reply_text("\n".join(lines))


async def settings_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    family, member = await get_user_context(update, context)
    if not family:
        await update.message.reply_text("Семья не найдена.")
        return
    await update.message.reply_text("Настройки:", reply_markup=settings_keyboard())


async def settings_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    data = query.data

    if data == "settings:timezone":
        await query.edit_message_text("Выберите часовой пояс:", reply_markup=timezone_keyboard())
    elif data == "settings:assign_mode":
        await query.edit_message_text("Режим назначения задач по умолчанию:", reply_markup=assign_mode_keyboard())


async def timezone_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    tz = query.data.split(":", 1)[1]
    db = context.bot_data["db"]
    family, _ = await get_user_context(update, context)
    if family:
        await db.update_family_timezone(family["id"], tz)
        await query.edit_message_text(f"Часовой пояс обновлен: {tz}")


async def assign_mode_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    mode = query.data.split(":", 1)[1]
    db = context.bot_data["db"]
    family, _ = await get_user_context(update, context)
    if family:
        import json
        settings = json.loads(family.get("settings", "{}"))
        settings["default_assign_mode"] = mode
        await db.update_family_settings(family["id"], settings)
        mode_names = {"manual": "Ручной", "random": "Случайный", "rotation": "Ротация", "free": "Свободный"}
        await query.edit_message_text(f"Режим назначения: {mode_names.get(mode, mode)}")


def register_admin_handlers(app):
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("addfamily", addfamily_command))
    app.add_handler(CommandHandler("addmember", addmember_command))
    app.add_handler(CommandHandler("removemember", removemember_command))
    app.add_handler(CommandHandler("familylist", familylist_command))
    app.add_handler(CommandHandler("settings", settings_command))
    app.add_handler(CallbackQueryHandler(settings_callback, pattern=r"^settings:"))
    app.add_handler(CallbackQueryHandler(timezone_callback, pattern=r"^tz:"))
    app.add_handler(CallbackQueryHandler(assign_mode_callback, pattern=r"^assign:(manual|random|rotation|free)$"))
