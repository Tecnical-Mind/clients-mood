import uuid
from datetime import datetime

from pydantic import BaseModel, EmailStr, Field, field_validator

from app.models.monitor_config import ConfigStatus, Frequency


class ConfigIn(BaseModel):
    email_to_monitor: EmailStr
    imap_server: str = Field(min_length=1, max_length=255)
    imap_port: int = Field(default=993, ge=1, le=65535)
    imap_password: str = Field(min_length=1)
    report_destination_email: EmailStr
    frequency: Frequency = Frequency.immediate

    @field_validator("imap_server")
    @classmethod
    def strip_server(cls, v: str) -> str:
        return v.strip()


class ConfigPatch(BaseModel):
    email_to_monitor: EmailStr | None = None
    imap_server: str | None = Field(default=None, min_length=1, max_length=255)
    imap_port: int | None = Field(default=None, ge=1, le=65535)
    imap_password: str | None = Field(default=None, min_length=1)
    report_destination_email: EmailStr | None = None
    frequency: Frequency | None = None
    status: ConfigStatus | None = None


class ConfigOut(BaseModel):
    id: uuid.UUID
    email_to_monitor: str
    imap_server: str
    imap_port: int
    report_destination_email: str
    frequency: Frequency
    status: ConfigStatus
    last_checked_at: datetime | None
    last_error: str | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


# Deliberately no password field anywhere above: the API never echoes it
# back after save, in plaintext or otherwise.


KNOWN_IMAP_PROVIDERS: dict[str, tuple[str, int]] = {
    "gmail.com": ("imap.gmail.com", 993),
    "googlemail.com": ("imap.gmail.com", 993),
    "outlook.com": ("outlook.office365.com", 993),
    "hotmail.com": ("outlook.office365.com", 993),
    "live.com": ("outlook.office365.com", 993),
    "yahoo.com": ("imap.mail.yahoo.com", 993),
    "icloud.com": ("imap.mail.me.com", 993),
}
