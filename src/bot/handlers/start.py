from telegram import Update
from telegram.ext import ContextTypes

from ..client import api


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    user = update.effective_user

    family = await api.get_family_by_chat(chat_id)
    if not family:
        family = await api.create_family(f"Family {chat_id}", chat_id)
        role = "admin"
    else:
        members_list = await _get_members(family["id"])
        role = "admin" if len(members_list) == 0 else "member"

    display_name = user.full_name or user.username or str(user.id)
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
        "Команды:\n"
        "/addchore — добавить задачу\n"
        "/mytasks — мои задачи\n"
        "/alltasks — все задачи\n"
        "/pending — невыполненные\n"
        "/history — история\n"
        "/done <id> — отметить выполненной",
        parse_mode="Markdown",
    )


async def _get_members(family_id: int) -> list:
    import httpx
    from ..config import settings
    async with httpx.AsyncClient(base_url=settings.api_base_url) as c:
        r = await c.get("/api/members", params={"family_id": family_id})
        if r.is_success:
            return r.json()
    return []


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
        "/done <id> — отметить задачу выполненной"
    )
