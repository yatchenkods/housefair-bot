import os
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    telegram_token: str
    api_base_url: str = "http://localhost:8000"
    reminder_interval_minutes: int = 30

    model_config = {"env_file": ".env", "extra": "ignore"}


settings = Settings()
