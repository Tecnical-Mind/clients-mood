import logging

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger

from app.config import settings
from app.workers import poll_inboxes, send_digests

logger = logging.getLogger(__name__)

_scheduler = BackgroundScheduler()


def start() -> None:
    _scheduler.add_job(
        poll_inboxes.run,
        trigger=IntervalTrigger(minutes=settings.poll_interval_minutes),
        id="poll_inboxes",
        max_instances=1,
        coalesce=True,
    )
    _scheduler.add_job(
        send_digests.run_daily,
        trigger=CronTrigger(hour=settings.digest_daily_hour),
        id="send_daily_digests",
        max_instances=1,
        coalesce=True,
    )
    _scheduler.add_job(
        send_digests.run_weekly,
        trigger=CronTrigger(
            day_of_week=settings.digest_weekly_day, hour=settings.digest_weekly_hour
        ),
        id="send_weekly_digests",
        max_instances=1,
        coalesce=True,
    )
    _scheduler.start()
    logger.info("Scheduler started (poll every %s min)", settings.poll_interval_minutes)


def shutdown() -> None:
    if _scheduler.running:
        _scheduler.shutdown(wait=False)
