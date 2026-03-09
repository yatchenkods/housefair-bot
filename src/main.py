import asyncio
import warnings

from loguru import logger
from telegram.warnings import PTBUserWarning

# chores_handler и product_conv используют смешанные состояния (MessageHandler + CallbackQueryHandler),
# поэтому per_message=False — намеренный выбор. Предупреждения PTB подавляем явно.
warnings.filterwarnings("ignore", category=PTBUserWarning, message=".*per_message.*")
from telegram.ext import ApplicationBuilder

from src.config import Settings
from src.database.repository import Database
from src.bot.handlers.admin_handler import register_admin_handlers
from src.bot.handlers.chores_handler import register_chores_handlers
from src.bot.handlers.cooking_handler import register_cooking_handlers
from src.bot.handlers.reports_handler import register_reports_handlers
from src.services.perplexity_service import PerplexityService
from src.services.scheduler import setup_scheduler
from src.utils.logger import setup_logger


async def post_init(app) -> None:
    db = app.bot_data["db"]
    await db.connect()
    await db.init_tables()
    ok = await db.check_integrity()
    if not ok:
        logger.error("Database integrity check failed!")
    logger.info("Bot initialized")


async def post_shutdown(app) -> None:
    db = app.bot_data["db"]
    await db.close()
    logger.info("Bot shutdown")


def main() -> None:
    # Python 3.12+ no longer auto-creates event loop in get_event_loop()
    asyncio.set_event_loop(asyncio.new_event_loop())

    settings = Settings()
    setup_logger(settings.log_level)

    db = Database(settings.database_path)
    perplexity = PerplexityService(settings.perplexity_api_key)

    app = (
        ApplicationBuilder()
        .token(settings.telegram_bot_token)
        .post_init(post_init)
        .post_shutdown(post_shutdown)
        .build()
    )

    app.bot_data["db"] = db
    app.bot_data["settings"] = settings
    app.bot_data["perplexity"] = perplexity

    register_admin_handlers(app)
    register_chores_handlers(app)
    register_cooking_handlers(app)
    register_reports_handlers(app)
    setup_scheduler(app, settings)

    logger.info("Starting bot...")
    app.run_polling()


if __name__ == "__main__":
    main()
