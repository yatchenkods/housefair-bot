import json
from urllib.parse import unquote

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel

from src.api.auth import create_jwt, extract_user_from_init_data, validate_init_data
from src.api.deps import get_db, get_settings
from src.database.repository import Database

router = APIRouter()


class ValidateRequest(BaseModel):
    init_data: str


@router.post("/validate")
async def validate(body: ValidateRequest, request: Request):
    db: Database = get_db(request)
    settings = get_settings(request)

    # Dev bypass
    if settings.jwt_secret in ("dev", "dev-test"):
        if "user_id=0" in body.init_data or not body.init_data:
            token = create_jwt({"user_id": 0}, settings.jwt_secret)
            return {
                "token": token,
                "member": {
                    "id": 0,
                    "family_id": 0,
                    "user_id": 0,
                    "username": "dev",
                    "display_name": "Dev User",
                    "role": "admin",
                },
            }

    try:
        params = validate_init_data(body.init_data, settings.telegram_bot_token)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e))

    tg_user = extract_user_from_init_data(params)
    user_id = tg_user.get("id")
    if not user_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No user in initData")

    member = await db.get_member_by_user_id(user_id)
    if not member:
        # Try to bind by username
        username = tg_user.get("username", "")
        if username:
            # Find member by username across all families
            async with db.db.execute(
                "SELECT * FROM members WHERE username = ? LIMIT 1", (username,)
            ) as cursor:
                row = await cursor.fetchone()
                if row:
                    row_dict = dict(row)
                    await db.bind_member_user_id(row_dict["id"], user_id)
                    member = await db.get_member_by_user_id(user_id)

    if not member:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User is not a family member. Ask admin to add you first.",
        )

    token = create_jwt({"user_id": user_id, "member_id": member["id"]}, settings.jwt_secret)
    return {"token": token, "member": member}
