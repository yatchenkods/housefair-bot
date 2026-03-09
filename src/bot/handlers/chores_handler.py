from telegram import Update
from telegram.ext import (
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    ConversationHandler,
    MessageHandler,
    filters,
)

from src.bot.handlers.admin_handler import get_user_context
from src.bot.keyboards import (
    assign_mode_keyboard,
    chore_done_keyboard,
    chore_presets_keyboard,
    chore_type_keyboard,
    members_keyboard,
)
from src.services.chores_service import ChoresService
from src.utils.helpers import format_datetime

CHOOSE_PRESET, ENTER_CUSTOM, CHOOSE_TYPE, CHOOSE_ASSIGN, CHOOSE_MEMBER = range(5)


async def addchore_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    family, member = await get_user_context(update, context)
    if not family:
        await update.message.reply_text("Сначала создайте семью: /addfamily")
        return ConversationHandler.END
    context.user_data["chore_family"] = family
    context.user_data["chore_member"] = member
    await update.message.reply_text(
        "Выберите задачу из списка или создайте свою:",
        reply_markup=chore_presets_keyboard(),
    )
    return CHOOSE_PRESET


async def preset_chosen(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    preset = query.data.split(":", 1)[1]

    if preset == "custom":
        await query.edit_message_text("Введите название задачи:")
        return ENTER_CUSTOM

    context.user_data["chore_title"] = preset
    await query.edit_message_text(
        f"Задача: {preset}\nВыберите тип повторения:",
        reply_markup=chore_type_keyboard(),
    )
    return CHOOSE_TYPE


async def custom_title_entered(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data["chore_title"] = update.message.text
    await update.message.reply_text(
        f"Задача: {update.message.text}\nВыберите тип повторения:",
        reply_markup=chore_type_keyboard(),
    )
    return CHOOSE_TYPE


async def type_chosen(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    chore_type = query.data.split(":", 1)[1]
    context.user_data["chore_type"] = chore_type
    type_names = {"one_time": "Разовая", "daily": "Ежедневная", "weekly": "Еженедельная", "monthly": "Ежемесячная"}
    await query.edit_message_text(
        f"Тип: {type_names.get(chore_type, chore_type)}\nКому назначить?",
        reply_markup=assign_mode_keyboard(),
    )
    return CHOOSE_ASSIGN


async def assign_chosen(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    mode = query.data.split(":", 1)[1]
    context.user_data["assign_mode"] = mode

    db = context.bot_data["db"]
    family = context.user_data["chore_family"]
    member = context.user_data["chore_member"]
    service = ChoresService(db)

    chore_id = await service.create_chore(
        family_id=family["id"],
        title=context.user_data["chore_title"],
        created_by=member["id"],
        chore_type=context.user_data["chore_type"],
    )

    if mode == "manual":
        members = await db.get_family_members(family["id"])
        context.user_data["chore_id"] = chore_id
        await query.edit_message_text(
            "Выберите участника:", reply_markup=members_keyboard(members)
        )
        return CHOOSE_MEMBER

    chore = await service.assign_chore(chore_id, family["id"], mode=mode)

    if chore and chore["assigned_to"]:
        members = await db.get_family_members(family["id"])
        assigned = next((m for m in members if m["id"] == chore["assigned_to"]), None)
        name = assigned["display_name"] if assigned else "?"
        await query.edit_message_text(
            f"Задача \"{context.user_data['chore_title']}\" (#{chore_id}) назначена: {name}"
        )
    else:
        await query.edit_message_text(
            f"Задача \"{context.user_data['chore_title']}\" (#{chore_id}) создана как свободная."
        )

    return ConversationHandler.END


async def member_chosen(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    member_id = int(query.data.split(":", 1)[1])

    db = context.bot_data["db"]
    family = context.user_data["chore_family"]
    service = ChoresService(db)

    chore = await service.assign_chore(
        context.user_data["chore_id"], family["id"], mode="manual", member_id=member_id
    )
    members = await db.get_family_members(family["id"])
    assigned = next((m for m in members if m["id"] == member_id), None)
    name = assigned["display_name"] if assigned else "?"

    await query.edit_message_text(
        f"Задача \"{context.user_data['chore_title']}\" (#{chore['id']}) назначена: {name}"
    )
    return ConversationHandler.END


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text("Отменено.")
    return ConversationHandler.END


async def done_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    db = context.bot_data["db"]
    family, member = await get_user_context(update, context)
    if not family or not member:
        await update.message.reply_text("Семья не найдена.")
        return

    if context.args:
        try:
            chore_id = int(context.args[0])
            service = ChoresService(db)
            chore = await service.complete_chore(chore_id)
            if chore:
                await update.message.reply_text(f"Задача \"{chore['title']}\" (#{chore_id}) выполнена!")
            else:
                await update.message.reply_text("Задача не найдена.")
            return
        except ValueError:
            pass

    chores = await db.get_chores_by_member(member["id"], status="pending")
    overdue = await db.get_chores_by_member(member["id"], status="overdue")
    all_chores = chores + overdue

    if not all_chores:
        await update.message.reply_text("У вас нет активных задач.")
        return

    await update.message.reply_text(
        "Выберите выполненную задачу:", reply_markup=chore_done_keyboard(all_chores)
    )


async def done_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    chore_id = int(query.data.split(":", 1)[1])

    db = context.bot_data["db"]
    service = ChoresService(db)
    chore = await service.complete_chore(chore_id)
    if chore:
        await query.edit_message_text(f"Задача \"{chore['title']}\" (#{chore_id}) выполнена!")
    else:
        await query.edit_message_text("Задача не найдена.")


async def mytasks_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    db = context.bot_data["db"]
    family, member = await get_user_context(update, context)
    if not family or not member:
        await update.message.reply_text("Семья не найдена.")
        return

    chores = await db.get_chores_by_member(member["id"], status="pending")
    overdue = await db.get_chores_by_member(member["id"], status="overdue")
    all_chores = chores + overdue

    if not all_chores:
        await update.message.reply_text("У вас нет активных задач.")
        return

    tz = family.get("timezone", "Europe/Moscow")
    lines = ["Ваши задачи:\n"]
    for c in all_chores:
        status_icon = "!" if c["status"] == "overdue" else " "
        created = format_datetime(c["created_at"], tz) if c.get("created_at") else ""
        lines.append(f"{status_icon} #{c['id']} {c['title']} ({c['chore_type']}) - {created}")
    await update.message.reply_text("\n".join(lines))


async def alltasks_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    db = context.bot_data["db"]
    family, member = await get_user_context(update, context)
    if not family:
        await update.message.reply_text("Семья не найдена.")
        return

    chores = await db.get_chores_by_family(family["id"])
    if not chores:
        await update.message.reply_text("Задач пока нет.")
        return

    members = await db.get_family_members(family["id"])
    member_map = {m["id"]: m["display_name"] for m in members}
    tz = family.get("timezone", "Europe/Moscow")

    lines = ["Все задачи семьи:\n"]
    for c in chores[:20]:
        assignee = member_map.get(c["assigned_to"], "не назначена")
        status_icons = {"pending": "[ ]", "completed": "[+]", "overdue": "[!]"}
        icon = status_icons.get(c["status"], "[ ]")
        lines.append(f"{icon} #{c['id']} {c['title']} -> {assignee}")
    await update.message.reply_text("\n".join(lines))


async def pending_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    db = context.bot_data["db"]
    family, member = await get_user_context(update, context)
    if not family:
        await update.message.reply_text("Семья не найдена.")
        return

    service = ChoresService(db)
    chores = await service.get_pending(family["id"])
    if not chores:
        await update.message.reply_text("Нет невыполненных задач!")
        return

    members = await db.get_family_members(family["id"])
    member_map = {m["id"]: m["display_name"] for m in members}

    lines = ["Невыполненные задачи:\n"]
    for c in chores[:20]:
        assignee = member_map.get(c["assigned_to"], "свободная")
        lines.append(f"  #{c['id']} {c['title']} -> {assignee}")
    await update.message.reply_text("\n".join(lines))


async def history_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    db = context.bot_data["db"]
    family, member = await get_user_context(update, context)
    if not family:
        await update.message.reply_text("Семья не найдена.")
        return

    service = ChoresService(db)
    chores = await service.get_history(family["id"])
    if not chores:
        await update.message.reply_text("История пуста.")
        return

    members = await db.get_family_members(family["id"])
    member_map = {m["id"]: m["display_name"] for m in members}
    tz = family.get("timezone", "Europe/Moscow")

    lines = ["История выполненных задач:\n"]
    for c in chores[:20]:
        assignee = member_map.get(c["assigned_to"], "?")
        completed = format_datetime(c["completed_at"], tz) if c.get("completed_at") else ""
        lines.append(f"  #{c['id']} {c['title']} - {assignee} ({completed})")
    await update.message.reply_text("\n".join(lines))


def register_chores_handlers(app):
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("addchore", addchore_command)],
        states={
            CHOOSE_PRESET: [CallbackQueryHandler(preset_chosen, pattern=r"^preset:")],
            ENTER_CUSTOM: [MessageHandler(filters.TEXT & ~filters.COMMAND, custom_title_entered)],
            CHOOSE_TYPE: [CallbackQueryHandler(type_chosen, pattern=r"^type:")],
            CHOOSE_ASSIGN: [CallbackQueryHandler(assign_chosen, pattern=r"^assign:")],
            CHOOSE_MEMBER: [CallbackQueryHandler(member_chosen, pattern=r"^member:")],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
        name="addchore_conv",
        per_chat=True,
    )
    app.add_handler(conv_handler)
    app.add_handler(CommandHandler("done", done_command))
    app.add_handler(CallbackQueryHandler(done_callback, pattern=r"^done:"))
    app.add_handler(CommandHandler("mytasks", mytasks_command))
    app.add_handler(CommandHandler("alltasks", alltasks_command))
    app.add_handler(CommandHandler("pending", pending_command))
    app.add_handler(CommandHandler("history", history_command))
