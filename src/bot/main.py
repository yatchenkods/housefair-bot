import logging
from telegram.ext import Application, CommandHandler, CallbackQueryHandler

from .config import settings
from .handlers.start import start, help_cmd
from .handlers.chores import get_chore_conversation
from .handlers.lists import mytasks, alltasks, pending, history
from .handlers.done import done_cmd, done_callback, take_callback
from .scheduler import start_scheduler

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(name)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)


def main():
    app = Application.builder().token(settings.telegram_token).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_cmd))
    app.add_handler(get_chore_conversation())
    app.add_handler(CommandHandler("mytasks", mytasks))
    app.add_handler(CommandHandler("alltasks", alltasks))
    app.add_handler(CommandHandler("pending", pending))
    app.add_handler(CommandHandler("history", history))
    app.add_handler(CommandHandler("done", done_cmd))
    app.add_handler(CallbackQueryHandler(done_callback, pattern="^done:"))
    app.add_handler(CallbackQueryHandler(take_callback, pattern="^take:"))

    scheduler = start_scheduler(settings.reminder_interval_minutes)

    async def post_init(application):
        scheduler.configure_bot(application.bot)
        scheduler.start()

    app.post_init = post_init

    logger.info("Bot started")
    app.run_polling()

    scheduler.shutdown()


if __name__ == "__main__":
    main()
