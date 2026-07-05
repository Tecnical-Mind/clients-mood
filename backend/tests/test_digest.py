from unittest.mock import patch

from app.models.email_analysis import EmailAnalysis
from app.models.monitor_config import Frequency, MonitorConfig
from app.workers import send_digests


def _make_config(db_session, user, frequency=Frequency.daily):
    config = MonitorConfig(
        user_id=user.id,
        email_to_monitor="inbox@example.com",
        imap_server="imap.example.com",
        imap_password_encrypted="ciphertext",
        report_destination_email="reports@example.com",
        frequency=frequency,
    )
    db_session.add(config)
    db_session.commit()
    return config


def _make_analysis(db_session, config, message_id, report_sent=False):
    analysis = EmailAnalysis(
        config_id=config.id,
        message_id=message_id,
        imap_uid=1,
        sender="a@example.com",
        subject="subj",
        mood_label="negativo",
        mood_score=-0.5,
        mood_summary="summary",
        requires_attention=True,
        report_sent=report_sent,
    )
    db_session.add(analysis)
    db_session.commit()
    return analysis


def test_daily_digest_sends_and_marks_reported(db_session, test_user, monkeypatch):
    config = _make_config(db_session, test_user)
    a1 = _make_analysis(db_session, config, "<m1@example.com>")
    a2 = _make_analysis(db_session, config, "<m2@example.com>")

    monkeypatch.setattr(send_digests, "SessionLocal", lambda: db_session)
    # Prevent the fixture's own close() from ending the shared test session.
    monkeypatch.setattr(db_session, "close", lambda: None)

    with patch("app.workers.send_digests.send_digest_report") as mock_send:
        send_digests.run_daily()

    mock_send.assert_called_once()
    db_session.refresh(a1)
    db_session.refresh(a2)
    assert a1.report_sent is True
    assert a2.report_sent is True


def test_daily_digest_skips_when_nothing_unreported(db_session, test_user, monkeypatch):
    config = _make_config(db_session, test_user)
    _make_analysis(db_session, config, "<m1@example.com>", report_sent=True)

    monkeypatch.setattr(send_digests, "SessionLocal", lambda: db_session)
    monkeypatch.setattr(db_session, "close", lambda: None)

    with patch("app.workers.send_digests.send_digest_report") as mock_send:
        send_digests.run_daily()

    mock_send.assert_not_called()


def test_weekly_config_not_included_in_daily_run(db_session, test_user, monkeypatch):
    config = _make_config(db_session, test_user, frequency=Frequency.weekly)
    _make_analysis(db_session, config, "<m1@example.com>")

    monkeypatch.setattr(send_digests, "SessionLocal", lambda: db_session)
    monkeypatch.setattr(db_session, "close", lambda: None)

    with patch("app.workers.send_digests.send_digest_report") as mock_send:
        send_digests.run_daily()

    mock_send.assert_not_called()
