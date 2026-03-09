from datetime import datetime

import pytz


def get_local_now(timezone: str = "Europe/Moscow") -> datetime:
    tz = pytz.timezone(timezone)
    return datetime.now(pytz.utc).astimezone(tz)


def format_datetime(dt: datetime, timezone: str = "Europe/Moscow") -> str:
    tz = pytz.timezone(timezone)
    local_dt = dt.astimezone(tz) if dt.tzinfo else pytz.utc.localize(dt).astimezone(tz)
    return local_dt.strftime("%d.%m.%Y %H:%M")


def escape_md(text: str) -> str:
    special_chars = r"_*[]()~`>#+-=|{}.!"
    result = ""
    for char in text:
        if char in special_chars:
            result += f"\\{char}"
        else:
            result += char
    return result
