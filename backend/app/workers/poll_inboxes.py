import logging
from datetime import UTC, datetime

from sqlalchemy.exc import IntegrityError

from app.db import SessionLocal
from app.models.email_analysis import EmailAnalysis
from app.models.monitor_config import ConfigStatus, Frequency, MonitorConfig
from app.security import decrypt_password
from app.services.email_reader import fetch_new_emails
from app.services.email_sender import send_immediate_report
from app.services.llm import analyze_email

logger = logging.getLogger(__name__)


def _process_config(db, config: MonitorConfig) -> None:
    password = decrypt_password(config.imap_password_encrypted)
    try:
        emails, new_uid, uidvalidity = fetch_new_emails(
            imap_server=config.imap_server,
            imap_port=config.imap_port,
            username=config.email_to_monitor,
            password=password,
            last_seen_uid=config.last_seen_uid,
            last_seen_uidvalidity=config.last_seen_uidvalidity,
        )
    except Exception as exc:  # noqa: BLE001 - one bad inbox must not kill the loop
        logger.exception("IMAP poll failed for config %s", config.id)
        config.last_error = str(exc)[:500]
        db.commit()
        return

    for fetched in emails:
        result = analyze_email(fetched.sender, fetched.subject, fetched.body)
        analysis = EmailAnalysis(
            config_id=config.id,
            message_id=fetched.message_id,
            imap_uid=fetched.uid,
            sender=fetched.sender,
            subject=fetched.subject,
            received_at=fetched.received_at,
            mood_label=result.mood_label,
            mood_score=result.mood_score,
            mood_summary=result.summary,
            requires_attention=result.requires_attention,
            analysis_failed=result.failed,
        )
        try:
            with db.begin_nested():
                db.add(analysis)
                db.flush()
        except IntegrityError:
            # Already processed this message_id for this config (e.g. after a
            # UIDVALIDITY reset re-fetched an old message) - skip it. Using a
            # SAVEPOINT here means this rollback only undoes this one insert,
            # not the whole poll batch's progress so far.
            continue

        if config.frequency == Frequency.immediate:
            try:
                send_immediate_report(config.report_destination_email, analysis)
                analysis.report_sent = True
                analysis.report_sent_at = datetime.now(UTC)
            except Exception:  # noqa: BLE001
                logger.exception("Failed to send immediate report for analysis %s", analysis.id)

    config.last_seen_uid = new_uid
    config.last_seen_uidvalidity = uidvalidity
    config.last_checked_at = datetime.now(UTC)
    config.last_error = None
    db.commit()


def run() -> None:
    db = SessionLocal()
    try:
        configs = db.query(MonitorConfig).filter(MonitorConfig.status == ConfigStatus.active).all()
        for config in configs:
            try:
                _process_config(db, config)
            except Exception:  # noqa: BLE001 - isolate failures per user
                logger.exception("Unhandled error processing config %s", config.id)
                db.rollback()
    finally:
        db.close()
