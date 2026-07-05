from unittest.mock import patch

from app.models.magic_link import MagicLinkToken
from app.models.user import User
from app.security import hash_token


def test_request_link_creates_user_and_sends_email(client, db_session):
    with patch("app.api.routes_auth.send_magic_link_email") as mock_send:
        resp = client.post("/api/auth/request-link", json={"email": "new@example.com"})

    assert resp.status_code == 200
    user = db_session.query(User).filter(User.email == "new@example.com").first()
    assert user is not None
    mock_send.assert_called_once()
    sent_to, sent_link = mock_send.call_args[0]
    assert sent_to == "new@example.com"
    assert "/verify?token=" in sent_link


def test_verify_sets_session_cookie_and_consumes_token(client, db_session, test_user):
    with patch("app.api.routes_auth.send_magic_link_email") as mock_send:
        client.post("/api/auth/request-link", json={"email": test_user.email})
    raw_token = mock_send.call_args[0][1].split("token=")[1]

    resp = client.get(f"/api/auth/verify?token={raw_token}", follow_redirects=False)
    assert resp.status_code in (302, 307)
    assert "session" in resp.cookies

    record = (
        db_session.query(MagicLinkToken)
        .filter(MagicLinkToken.token_hash == hash_token(raw_token))
        .first()
    )
    assert record.consumed_at is not None

    # Reusing the same token must fail (single-use).
    resp2 = client.get(f"/api/auth/verify?token={raw_token}", follow_redirects=False)
    assert "error=invalid_link" in resp2.headers["location"]


def test_me_requires_auth(client):
    resp = client.get("/api/auth/me")
    assert resp.status_code == 401


def test_me_returns_current_user(auth_client, test_user):
    resp = auth_client.get("/api/auth/me")
    assert resp.status_code == 200
    assert resp.json()["email"] == test_user.email
