import logging
from dataclasses import dataclass
from datetime import UTC, datetime
from email import message_from_bytes
from email.header import decode_header
from email.message import Message
from email.utils import parsedate_to_datetime
from html.parser import HTMLParser

from imapclient import IMAPClient

from app.schemas.config import KNOWN_IMAP_PROVIDERS

logger = logging.getLogger(__name__)


class _HTMLStripper(HTMLParser):
    def __init__(self):
        super().__init__()
        self._chunks: list[str] = []

    def handle_data(self, data: str) -> None:
        self._chunks.append(data)

    def get_text(self) -> str:
        return "".join(self._chunks)


def strip_html(html: str) -> str:
    stripper = _HTMLStripper()
    stripper.feed(html)
    return stripper.get_text()


def suggest_imap_server(email_address: str) -> tuple[str, int] | None:
    domain = email_address.rsplit("@", 1)[-1].lower()
    return KNOWN_IMAP_PROVIDERS.get(domain)


def _decode(value: str | None) -> str:
    if not value:
        return ""
    parts = decode_header(value)
    decoded = ""
    for text, encoding in parts:
        if isinstance(text, bytes):
            decoded += text.decode(encoding or "utf-8", errors="replace")
        else:
            decoded += text
    return decoded


def _extract_body(msg: Message) -> str:
    if msg.is_multipart():
        plain, html = None, None
        for part in msg.walk():
            content_type = part.get_content_type()
            if part.get_content_disposition() == "attachment":
                continue
            if content_type == "text/plain" and plain is None:
                plain = part.get_payload(decode=True)
                plain_charset = part.get_content_charset() or "utf-8"
                plain = plain.decode(plain_charset, errors="replace") if plain else None
            elif content_type == "text/html" and html is None:
                html = part.get_payload(decode=True)
                html_charset = part.get_content_charset() or "utf-8"
                html = html.decode(html_charset, errors="replace") if html else None
        if plain:
            return plain
        if html:
            return strip_html(html)
        return ""
    else:
        payload = msg.get_payload(decode=True)
        charset = msg.get_content_charset() or "utf-8"
        text = payload.decode(charset, errors="replace") if payload else ""
        if msg.get_content_type() == "text/html":
            return strip_html(text)
        return text


@dataclass
class FetchedEmail:
    uid: int
    message_id: str
    sender: str
    subject: str
    body: str
    received_at: datetime | None


def fetch_new_emails(
    *,
    imap_server: str,
    imap_port: int,
    username: str,
    password: str,
    last_seen_uid: int,
    last_seen_uidvalidity: int | None,
) -> tuple[list[FetchedEmail], int, int]:
    """Connects read-only and returns (new_emails, new_last_seen_uid, uidvalidity).

    Uses UID SEARCH rather than date-based SINCE search: UIDs are monotonically
    increasing and never reused within one UIDVALIDITY epoch, so this correctly
    picks up only genuinely new messages regardless of overlapping poll windows.
    """
    with IMAPClient(imap_server, port=imap_port, ssl=True) as client:
        client.login(username, password)
        select_info = client.select_folder("INBOX", readonly=True)
        uidvalidity = select_info[b"UIDVALIDITY"]

        if last_seen_uidvalidity is not None and uidvalidity != last_seen_uidvalidity:
            # Server reset UID numbering; stored UIDs are no longer meaningful.
            logger.warning("UIDVALIDITY changed for %s, resetting UID watermark", username)
            last_seen_uid = 0

        start_uid = last_seen_uid + 1
        uids = client.search(["UID", f"{start_uid}:*"])
        # An empty mailbox / no new mail can return the last known UID again
        # per RFC 3501 range semantics; filter defensively.
        uids = sorted(uid for uid in uids if uid > last_seen_uid)

        emails: list[FetchedEmail] = []
        if uids:
            response = client.fetch(uids, ["RFC822"])
            for uid, data in response.items():
                raw = data.get(b"RFC822")
                if raw is None:
                    continue
                msg = message_from_bytes(raw)
                message_id = _decode(msg.get("Message-ID")) or f"<no-id-uid-{uid}>"
                sender = _decode(msg.get("From"))
                subject = _decode(msg.get("Subject"))
                body = _extract_body(msg)
                received_at = None
                try:
                    date_header = msg.get("Date")
                    if date_header:
                        received_at = parsedate_to_datetime(date_header)
                        if received_at.tzinfo is None:
                            received_at = received_at.replace(tzinfo=UTC)
                except (TypeError, ValueError):
                    received_at = None
                emails.append(
                    FetchedEmail(
                        uid=uid,
                        message_id=message_id,
                        sender=sender,
                        subject=subject,
                        body=body[:8000],
                        received_at=received_at,
                    )
                )

        new_watermark = max(uids) if uids else last_seen_uid
        return emails, new_watermark, uidvalidity
