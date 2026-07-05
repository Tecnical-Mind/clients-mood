import logging
from datetime import UTC, datetime

from app.db import SessionLocal
from app.models.email_analysis import EmailAnalysis
from app.models.monitor_config import ConfigStatus, Frequency, MonitorConfig
from app.services.email_sender import send_digest_report

logger = logging.getLogger(__name__)


def _send_for_frequency(db, frequency: Frequency) -> None:
    configs = (
        db.query(MonitorConfig)
        .filter(MonitorConfig.status == ConfigStatus.active, MonitorConfig.frequency == frequency)
        .all()
    )
    for config in configs:
        unreported = (
            db.query(EmailAnalysis)
            .filter(EmailAnalysis.config_id == config.id, EmailAnalysis.report_sent.is_(False))
            .order_by(EmailAnalysis.analyzed_at)
            .all()
        )
        if not unreported:
            continue

        period_start = unreported[0].analyzed_at
        period_end = unreported[-1].analyzed_at
        try:
            send_digest_report(
                config.report_destination_email, unreported, period_start, period_end
            )
        except Exception:  # noqa: BLE001 - one user's failure must not block others
            logger.exception("Failed to send digest for config %s", config.id)
            continue

        now = datetime.now(UTC)
        for analysis in unreported:
            analysis.report_sent = True
            analysis.report_sent_at = now
        db.commit()


def run_daily() -> None:
    db = SessionLocal()
    try:
        _send_for_frequency(db, Frequency.daily)
    finally:
        db.close()


def run_weekly() -> None:
    db = SessionLocal()
    try:
        _send_for_frequency(db, Frequency.weekly)
    finally:
        db.close()
