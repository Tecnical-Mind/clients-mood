import uuid
from datetime import UTC, datetime

from sqlalchemy import (
    BigInteger,
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    String,
    Text,
    UniqueConstraint,
    Uuid,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base


class EmailAnalysis(Base):
    __tablename__ = "email_analyses"
    __table_args__ = (
        UniqueConstraint("config_id", "message_id", name="uq_config_message"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    config_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("monitor_configs.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    message_id: Mapped[str] = mapped_column(String(998), nullable=False)
    imap_uid: Mapped[int] = mapped_column(BigInteger, nullable=False)
    sender: Mapped[str] = mapped_column(String(320), nullable=False)
    subject: Mapped[str] = mapped_column(String(998), default="")
    received_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    mood_label: Mapped[str] = mapped_column(String(32), nullable=False)
    mood_score: Mapped[float] = mapped_column(Float, nullable=False)
    mood_summary: Mapped[str] = mapped_column(Text, default="")
    requires_attention: Mapped[bool] = mapped_column(Boolean, default=False)
    analysis_failed: Mapped[bool] = mapped_column(Boolean, default=False)

    analyzed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC)
    )
    report_sent: Mapped[bool] = mapped_column(Boolean, default=False)
    report_sent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
