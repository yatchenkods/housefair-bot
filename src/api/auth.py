import hashlib
import hmac
import json
from datetime import datetime, timedelta
from urllib.parse import parse_qsl, unquote

from jose import JWTError, jwt

ALGORITHM = "HS256"
TOKEN_EXPIRE_HOURS = 24


def validate_init_data(init_data: str, bot_token: str) -> dict:
    """Validate Telegram WebApp initData using HMAC-SHA256."""
    params = dict(parse_qsl(init_data, keep_blank_values=True))
    received_hash = params.pop("hash", "")

    data_check_string = "\n".join(
        f"{k}={v}" for k, v in sorted(params.items())
    )

    secret_key = hmac.new(b"WebAppData", bot_token.encode(), hashlib.sha256).digest()
    expected_hash = hmac.new(secret_key, data_check_string.encode(), hashlib.sha256).hexdigest()

    if not hmac.compare_digest(received_hash, expected_hash):
        raise ValueError("Invalid initData hash")

    return params


def extract_user_from_init_data(params: dict) -> dict:
    """Extract user dict from initData params."""
    user_str = params.get("user", "{}")
    return json.loads(unquote(user_str))


def create_jwt(payload: dict, secret: str) -> str:
    expire = datetime.utcnow() + timedelta(hours=TOKEN_EXPIRE_HOURS)
    data = {**payload, "exp": expire}
    return jwt.encode(data, secret, algorithm=ALGORITHM)


def decode_jwt(token: str, secret: str) -> dict:
    try:
        return jwt.decode(token, secret, algorithms=[ALGORITHM])
    except JWTError as e:
        raise ValueError(f"Invalid token: {e}")
