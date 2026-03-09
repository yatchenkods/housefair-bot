from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from src.api.auth import decode_jwt
from src.database.repository import Database

bearer = HTTPBearer(auto_error=False)


def get_db(request: Request) -> Database:
    return request.app.state.db


def get_settings(request: Request):
    return request.app.state.settings


async def get_current_member(
    request: Request,
    credentials: HTTPAuthorizationCredentials = Depends(bearer),
) -> dict:
    db: Database = get_db(request)
    settings = get_settings(request)

    if credentials is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")

    try:
        payload = decode_jwt(credentials.credentials, settings.jwt_secret)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

    user_id = payload.get("user_id")
    if user_id is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token payload")

    # Dev bypass: mock member for user_id=0
    if settings.jwt_secret in ("dev", "dev-test") and user_id == 0:
        return {
            "id": 0,
            "family_id": 0,
            "user_id": 0,
            "username": "dev",
            "display_name": "Dev User",
            "role": "admin",
        }

    member = await db.get_member_by_user_id(user_id)
    if not member:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Member not found")

    return member
