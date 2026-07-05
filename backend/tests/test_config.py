import uuid

from app.models.monitor_config import MonitorConfig
from app.models.user import User
from app.security import decrypt_password


def _payload(**overrides):
    payload = {
        "email_to_monitor": "inbox@example.com",
        "imap_server": "imap.example.com",
        "imap_port": 993,
        "imap_password": "super-secret-app-password",
        "report_destination_email": "reports@example.com",
        "frequency": "immediate",
    }
    payload.update(overrides)
    return payload


def test_create_config_encrypts_password_and_never_returns_it(auth_client, db_session, test_user):
    resp = auth_client.post("/api/config", json=_payload())
    assert resp.status_code == 201
    body = resp.json()
    assert "imap_password" not in body
    assert "imap_password_encrypted" not in body

    stored = db_session.query(MonitorConfig).filter(MonitorConfig.user_id == test_user.id).first()
    assert stored.imap_password_encrypted != "super-secret-app-password"
    assert decrypt_password(stored.imap_password_encrypted) == "super-secret-app-password"


def test_create_config_twice_conflicts(auth_client):
    first = auth_client.post("/api/config", json=_payload())
    assert first.status_code == 201
    second = auth_client.post("/api/config", json=_payload())
    assert second.status_code == 409


def test_patch_status_pauses_config(auth_client):
    created = auth_client.post("/api/config", json=_payload()).json()
    resp = auth_client.patch(f"/api/config/{created['id']}", json={"status": "paused"})
    assert resp.status_code == 200
    assert resp.json()["status"] == "paused"


def test_cannot_access_another_users_config(auth_client, db_session):
    # test_user needs their own config first, since the lookup is scoped by
    # the caller's user_id before the path's config_id is ever compared.
    auth_client.post("/api/config", json=_payload())

    other_user = User(id=uuid.uuid4(), email="other@example.com")
    db_session.add(other_user)
    other_config = MonitorConfig(
        user_id=other_user.id,
        email_to_monitor="other-inbox@example.com",
        imap_server="imap.example.com",
        imap_password_encrypted="ciphertext",
        report_destination_email="other-reports@example.com",
    )
    db_session.add(other_config)
    db_session.commit()

    resp = auth_client.get(f"/api/config/{other_config.id}")
    assert resp.status_code == 404
