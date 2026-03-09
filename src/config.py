from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    telegram_bot_token: str
    perplexity_api_key: str = ""
    database_path: str = "data/database.db"
    log_level: str = "INFO"
    backup_enabled: bool = True
    backup_hour: int = 3
    backup_retention_days: int = 30
    tz: str = "Europe/Moscow"

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}
