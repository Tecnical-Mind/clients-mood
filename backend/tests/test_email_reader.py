from unittest.mock import MagicMock, patch

from app.services.email_reader import fetch_new_emails, strip_html, suggest_imap_server

SAMPLE_RAW_EMAIL = (
    b"Message-ID: <abc123@example.com>\r\n"
    b"From: Angry Customer <angry@example.com>\r\n"
    b"Subject: This is broken!!!\r\n"
    b"Date: Mon, 5 Jul 2026 10:00:00 +0000\r\n"
    b"Content-Type: text/plain; charset=utf-8\r\n"
    b"\r\n"
    b"This product completely stopped working and I want a refund NOW.\r\n"
)


def _mock_imapclient(select_info, search_result, fetch_result):
    instance = MagicMock()
    instance.__enter__.return_value = instance
    instance.select_folder.return_value = select_info
    instance.search.return_value = search_result
    instance.fetch.return_value = fetch_result
    return instance


def test_fetch_new_emails_first_run_uses_uidvalidity_and_returns_messages():
    select_info = {b"UIDVALIDITY": 1000}
    fetch_result = {42: {b"RFC822": SAMPLE_RAW_EMAIL}}
    mock_instance = _mock_imapclient(select_info, [42], fetch_result)

    with patch("app.services.email_reader.IMAPClient", return_value=mock_instance):
        emails, new_uid, uidvalidity = fetch_new_emails(
            imap_server="imap.example.com",
            imap_port=993,
            username="user@example.com",
            password="app-password",
            last_seen_uid=0,
            last_seen_uidvalidity=None,
        )

    assert new_uid == 42
    assert uidvalidity == 1000
    assert len(emails) == 1
    assert emails[0].message_id == "<abc123@example.com>"
    assert "refund" in emails[0].body
    mock_instance.select_folder.assert_called_once_with("INBOX", readonly=True)


def test_fetch_new_emails_only_returns_uids_above_watermark():
    select_info = {b"UIDVALIDITY": 1000}
    # Server may return the watermark UID itself; must be filtered out.
    mock_instance = _mock_imapclient(select_info, [42, 43], {43: {b"RFC822": SAMPLE_RAW_EMAIL}})

    with patch("app.services.email_reader.IMAPClient", return_value=mock_instance):
        emails, new_uid, _ = fetch_new_emails(
            imap_server="imap.example.com",
            imap_port=993,
            username="user@example.com",
            password="app-password",
            last_seen_uid=42,
            last_seen_uidvalidity=1000,
        )

    assert new_uid == 43
    assert len(emails) == 1


def test_fetch_new_emails_resets_watermark_on_uidvalidity_change():
    select_info = {b"UIDVALIDITY": 2000}  # different from stored 1000
    mock_instance = _mock_imapclient(select_info, [1], {1: {b"RFC822": SAMPLE_RAW_EMAIL}})

    with patch("app.services.email_reader.IMAPClient", return_value=mock_instance):
        emails, new_uid, uidvalidity = fetch_new_emails(
            imap_server="imap.example.com",
            imap_port=993,
            username="user@example.com",
            password="app-password",
            last_seen_uid=999,
            last_seen_uidvalidity=1000,
        )

    assert uidvalidity == 2000
    mock_instance.search.assert_called_once_with(["UID", "1:*"])


def test_strip_html_removes_tags():
    assert strip_html("<p>Hello <b>world</b></p>") == "Hello world"


def test_suggest_imap_server_known_provider():
    assert suggest_imap_server("someone@gmail.com") == ("imap.gmail.com", 993)


def test_suggest_imap_server_unknown_domain():
    assert suggest_imap_server("someone@custom-domain.io") is None
