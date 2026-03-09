from telegram import Update
from telegram.ext import ContextTypes

from ..client import api


_COMMANDS_TEXT = (
    "/addchore — добавить задачу\n"
    "/mytasks — мои задачи\n"
    "/alltasks — все задачи\n"
    "/pending — невыполненные\n"
    "/history — история\n"
    "/done <id> — отметить выполненной\n"
    "/members — участники семьи\n"
    "/addmember — пригласить участника"
)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if context.args and context.args[0].startswith("join_"):
        await _handle_join(update, context, context.args[0])
        return

    user = update.effective_user
    display_name = user.full_name or user.username or str(user.id)

    # Если пользователь уже состоит в семье — не создавать новую
    memberships = await api.get_user_memberships(user.id)
    if memberships:
        family = await api.get_family_by_id(memberships[0]["family_id"])
        await update.message.reply_text(
            f"👋 Привет, {display_name}!\n\n"
            f"Семья: *{family['name']}*\n\n"
            f"Команды:\n{_COMMANDS_TEXT}",
            parse_mode="Markdown",
        )
        return

    chat_id = update.effective_chat.id
    chat_type = update.effective_chat.type

    # В личном чате без членства предлагаем вступить по ссылке
    if chat_type == "private":
        await update.message.reply_text(
            "Вы ещё не состоите ни в одной семье.\n\n"
            "Попросите администратора семьи прислать ссылку-приглашение (/addmember) "
            "или добавьте бота в групповой чат и используйте /start там."
        )
        return

    # Групповой чат — создать семью если нет
    family = await api.get_family_by_chat(chat_id)
    if not family:
        family = await api.create_family(f"Family {chat_id}", chat_id)
        role = "admin"
    else:
        members_list = await api.list_members(family["id"])
        role = "admin" if len(members_list) == 0 else "member"

    await api.get_or_create_member(
        family_id=family["id"],
        user_id=user.id,
        username=user.username,
        display_name=display_name,
        role=role,
    )

    await update.message.reply_text(
        f"👋 Привет, {display_name}!\n\n"
        f"Семья: *{family['name']}*\n\n"
        f"Команды:\n{_COMMANDS_TEXT}",
        parse_mode="Markdown",
    )


async def _handle_join(update: Update, context: ContextTypes.DEFAULT_TYPE, arg: str):
    target_chat_id = int(arg.split("_", 1)[1])
    family = await api.get_family_by_chat(target_chat_id)
    if not family:
        await update.message.reply_text("Семья не найдена.")
        return
    user = update.effective_user
    existing = await api.get_member_by_user(user.id, family["id"])
    if existing:
        await update.message.reply_text(f"Вы уже в семье *{family['name']}*.", parse_mode="Markdown")
        return
    display_name = user.full_name or user.username or str(user.id)
    await api.create_member(family["id"], user.id, user.username, display_name, role="member")
    await update.message.reply_text(f"✅ Вы вступили в семью *{family['name']}*!", parse_mode="Markdown")


async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Команды бота:\n"
        "/start — начало работы\n"
        "/addchore — добавить задачу\n"
        "/task — добавить задачу\n"
        "/mytasks — мои задачи\n"
        "/alltasks — все задачи семьи\n"
        "/pending — невыполненные задачи\n"
        "/history — история выполненных\n"
        "/done <id> — отметить задачу выполненной\n"
        "/members — участники семьи\n"
        "/addmember — пригласить участника"
    )
