import uuid
from datetime import datetime

from pydantic import BaseModel


class AnalysisOut(BaseModel):
    id: uuid.UUID
    sender: str
    subject: str
    received_at: datetime | None
    mood_label: str
    mood_score: float
    mood_summary: str
    requires_attention: bool
    analysis_failed: bool
    analyzed_at: datetime
    report_sent: bool

    model_config = {"from_attributes": True}
