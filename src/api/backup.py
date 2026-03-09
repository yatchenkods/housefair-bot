import os
import shutil
import logging
from datetime import datetime, timezone
from apscheduler.schedulers.background import BackgroundScheduler

logger = logging.getLogger(__name__)

DB_PATH = os.getenv("DATABASE_URL", "sqlite:///./data/database.db").replace("sqlite:///", "")
BACKUP_DIR = os.path.join(os.path.dirname(DB_PATH), "backups")
MAX_BACKUPS = 30


def _do_backup():
    try:
        os.makedirs(BACKUP_DIR, exist_ok=True)
        date_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        dest = os.path.join(BACKUP_DIR, f"database_{date_str}.db")
        if os.path.exists(DB_PATH):
            shutil.copy2(DB_PATH, dest)
            logger.info(f"Backup created: {dest}")
        _cleanup_old_backups()
    except Exception as e:
        logger.error(f"Backup failed: {e}")


def _cleanup_old_backups():
    backups = sorted(
        [f for f in os.listdir(BACKUP_DIR) if f.startswith("database_")],
    )
    while len(backups) > MAX_BACKUPS:
        oldest = backups.pop(0)
        os.remove(os.path.join(BACKUP_DIR, oldest))
        logger.info(f"Removed old backup: {oldest}")


def start_backup_scheduler():
    scheduler = BackgroundScheduler()
    scheduler.add_job(_do_backup, "cron", hour=3, minute=0)
    scheduler.start()
    return scheduler
