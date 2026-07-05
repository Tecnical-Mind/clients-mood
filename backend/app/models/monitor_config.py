import enum
import uuid
from datetime import UTC, datetime

from sqlalchemy import BigInteger, DateTime, Enum, ForeignKey, Integer, String, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base


class Frequency(str, enum.Enum):
    immediate = "immediate"
    daily = "daily"
    weekly = "weekly"


class ConfigStatus(str, enum.Enum):
    active = "active"
    paused = "paused"


class MonitorConfig(Base):
    __tablename__ = "monitor_configs"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,  # one config per user for MVP
    )

    email_to_monitor: Mapped[str] = mapped_column(String(320), nullable=False)
    imap_server: Mapped[str] = mapped_column(String(255), nullable=False)
    imap_port: Mapped[int] = mapped_column(Integer, default=993)
    imap_password_encrypted: Mapped[str] = mapped_column(String, nullable=False)

    report_destination_email: Mapped[str] = mapped_column(String(320), nullable=False)
    frequency: Mapped[Frequency] = mapped_column(
        Enum(Frequency, name="frequency_enum"), default=Frequency.immediate
    )
    status: Mapped[ConfigStatus] = mapped_column(
        Enum(ConfigStatus, name="config_status_enum"), default=ConfigStatus.active
    )

    last_checked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_seen_uid: Mapped[int] = mapped_column(BigInteger, default=0)
    last_seen_uidvalidity: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    last_error: Mapped[str | None] = mapped_column(String, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
    )
