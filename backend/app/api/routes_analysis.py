from fastapi import APIRouter, Depends
from sqlalchemy import desc
from sqlalchemy.orm import Session

from app.db import get_db
from app.deps import get_current_user
from app.models.email_analysis import EmailAnalysis
from app.models.monitor_config import MonitorConfig
from app.models.user import User
from app.schemas.analysis import AnalysisOut

router = APIRouter(prefix="/api/analysis", tags=["analysis"])


@router.get("", response_model=list[AnalysisOut])
def list_analyses(
    limit: int = 100,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    # Always scoped to the current user's own config — any config_id the
    # client might pass is ignored, never trusted from the request.
    config = db.query(MonitorConfig).filter(MonitorConfig.user_id == user.id).first()
    if config is None:
        return []

    return (
        db.query(EmailAnalysis)
        .filter(EmailAnalysis.config_id == config.id)
        .order_by(desc(EmailAnalysis.analyzed_at))
        .limit(min(limit, 500))
        .all()
    )
