from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db import get_db
from app.deps import get_current_user
from app.models.monitor_config import MonitorConfig
from app.models.user import User
from app.schemas.config import KNOWN_IMAP_PROVIDERS, ConfigIn, ConfigOut, ConfigPatch
from app.security import encrypt_password

router = APIRouter(prefix="/api/config", tags=["config"])


def _get_own_config_or_404(db: Session, user: User) -> MonitorConfig:
    config = db.query(MonitorConfig).filter(MonitorConfig.user_id == user.id).first()
    if config is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No config found")
    return config


@router.get("/providers")
def list_known_providers():
    return {domain: {"server": s, "port": p} for domain, (s, p) in KNOWN_IMAP_PROVIDERS.items()}


@router.get("/me", response_model=ConfigOut)
def get_my_config(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return _get_own_config_or_404(db, user)


@router.post("", response_model=ConfigOut, status_code=status.HTTP_201_CREATED)
def create_config(
    body: ConfigIn, db: Session = Depends(get_db), user: User = Depends(get_current_user)
):
    existing = db.query(MonitorConfig).filter(MonitorConfig.user_id == user.id).first()
    if existing is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Config already exists for this user; use PATCH to update it",
        )

    config = MonitorConfig(
        user_id=user.id,
        email_to_monitor=body.email_to_monitor.lower(),
        imap_server=body.imap_server,
        imap_port=body.imap_port,
        imap_password_encrypted=encrypt_password(body.imap_password),
        report_destination_email=body.report_destination_email.lower(),
        frequency=body.frequency,
    )
    db.add(config)
    db.commit()
    db.refresh(config)
    return config


@router.patch("/{config_id}", response_model=ConfigOut)
def patch_config(
    config_id: str,
    body: ConfigPatch,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    config = _get_own_config_or_404(db, user)
    if str(config.id) != config_id:
        # Never let a user address another user's config, even by id.
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No config found")

    data = body.model_dump(exclude_unset=True)
    password = data.pop("imap_password", None)
    if password:
        config.imap_password_encrypted = encrypt_password(password)

    for field in ("email_to_monitor", "report_destination_email"):
        if field in data and data[field]:
            data[field] = data[field].lower()

    for field, value in data.items():
        setattr(config, field, value)

    db.commit()
    db.refresh(config)
    return config


@router.get("/{config_id}", response_model=ConfigOut)
def get_config(
    config_id: str, db: Session = Depends(get_db), user: User = Depends(get_current_user)
):
    config = _get_own_config_or_404(db, user)
    if str(config.id) != config_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No config found")
    return config
