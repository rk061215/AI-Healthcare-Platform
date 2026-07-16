from loguru import logger
from apscheduler.schedulers.background import BackgroundScheduler

from app.core.config import settings


class ReminderScheduler:
    def __init__(self):
        self.scheduler = BackgroundScheduler()
        self.interval = settings.REMINDER_CHECK_INTERVAL_MINUTES

    def start(self) -> None:
        logger.info("Starting reminder scheduler")
        self.scheduler.add_job(
            self.check_reminders,
            "interval",
            minutes=self.interval,
            id="reminder_check",
        )
        self.scheduler.start()

    def check_reminders(self) -> None:
        logger.debug("Checking medicine reminders")
        pass

    def stop(self) -> None:
        self.scheduler.shutdown()
