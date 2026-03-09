from telegram import Update

from .client import api


async def get_family_and_member(update: Update) -> tuple[dict | None, dict | None]:
    """
    Найти семью и участника для текущего пользователя.
    Сначала ищет семью по chat_id текущего чата.
    Если не найдена (например, личный чат после вступления по ссылке) —
    использует членство пользователя в любой семье.
    """
    chat_id = update.effective_chat.id
    user = update.effective_user

    family = await api.get_family_by_chat(chat_id)
    if family:
        member = await api.get_member_by_user(user.id, family["id"])
        return family, member

    # Fallback: пользователь вступил через invite-ссылку, открывает бота в личке
    memberships = await api.get_user_memberships(user.id)
    if not memberships:
        return None, None

    membership = memberships[0]
    family = await api.get_family_by_id(membership["family_id"])
    return family, membership
