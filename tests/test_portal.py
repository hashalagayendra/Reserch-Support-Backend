"""Portal integration tests use production routes and an isolated database."""
from datetime import datetime, timedelta, timezone

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.backend_config import settings
from app.core.security import session_digest, verify_password
from app.db.models import AITool, ApiKey, Project, User, UserSession
from app.db.session import Base, get_db
from app.main import app

ORIGIN = {"Origin": "http://localhost:5173"}
PASSWORD = "correct horse battery staple"


@pytest.fixture
def portal():
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(engine, tables=[User.__table__, UserSession.__table__, Project.__table__, ApiKey.__table__, AITool.__table__])
    factory = sessionmaker(bind=engine)

    def db_override():
        with factory() as db:
            yield db

    app.dependency_overrides[get_db] = db_override
    # Avoid entering lifespan: tests must never connect to the configured database.
    client = TestClient(app)
    yield client, factory
    client.close()
    app.dependency_overrides.clear()
    engine.dispose()


def register(client, email="researcher@example.com"):
    return client.post("/api/v1/auth/register", json={"email": email, "password": PASSWORD}, headers=ORIGIN)


def project(client, name="Adaptive workflow"):
    response = client.post("/api/v1/projects", json={"name": name}, headers=ORIGIN)
    assert response.status_code == 201
    return response.json()["id"]


def test_registration_session_password_and_logout(portal):
    client, factory = portal
    response = register(client, "  RESEARCHER@example.com  ")
    assert response.status_code == 201
    assert response.json()["email"] == "researcher@example.com"
    assert "hashed_password" not in response.json()
    assert "HttpOnly" in response.headers["set-cookie"]
    assert "SameSite=lax" in response.headers["set-cookie"]
    token = client.cookies.get(settings.SESSION_COOKIE_NAME)
    with factory() as db:
        user = db.query(User).one()
        assert user.hashed_password != PASSWORD
        assert verify_password(PASSWORD, user.hashed_password)
        assert db.query(UserSession).one().token_hash == session_digest(token)
    assert client.get("/api/v1/auth/me").status_code == 200
    assert client.post("/api/v1/auth/logout", headers=ORIGIN).status_code == 204
    assert client.get("/api/v1/auth/me").status_code == 401
    client.cookies.set(settings.SESSION_COOKIE_NAME, token)
    assert client.get("/api/v1/auth/me").status_code == 401


def test_login_failure_success_and_session_rotation(portal):
    client, factory = portal
    register(client)
    previous = client.cookies.get(settings.SESSION_COOKIE_NAME)
    assert client.post("/api/v1/auth/login", json={"email": "researcher@example.com", "password": "incorrect-password"}, headers=ORIGIN).status_code == 401
    response = client.post("/api/v1/auth/login", json={"email": "RESEARCHER@example.com", "password": PASSWORD}, headers=ORIGIN)
    assert response.status_code == 200
    assert client.cookies.get(settings.SESSION_COOKIE_NAME) != previous
    with factory() as db:
        assert db.get(UserSession, session_digest(previous)) is None
    assert register(client).status_code == 409


def test_expired_session_is_rejected(portal):
    client, factory = portal
    register(client)
    with factory() as db:
        db.query(UserSession).one().expires_at = datetime.now(timezone.utc) - timedelta(minutes=1)
        db.commit()
    assert client.get("/api/v1/auth/me").status_code == 401
    assert client.get("/api/v1/projects").status_code == 401


def test_projects_and_keys_are_isolated_between_users(portal):
    client, _ = portal
    register(client)
    project_id = project(client, "  My research  ")
    assert client.get(f"/api/v1/projects/{project_id}").json()["name"] == "My research"
    generated = client.post(f"/api/v1/projects/{project_id}/api-keys", headers=ORIGIN)
    assert generated.status_code == 201
    key_id = generated.json()["id"]
    assert generated.json()["key_value"].startswith("rk_")
    assert generated.headers["cache-control"] == "no-store"
    assert len(client.get(f"/api/v1/projects/{project_id}/api-keys").json()) == 1
    register(client, "other@example.com")
    assert client.get("/api/v1/projects").json() == []
    for method, path in [
        ("get", f"/api/v1/projects/{project_id}"),
        ("get", f"/api/v1/projects/{project_id}/api-keys"),
        ("post", f"/api/v1/projects/{project_id}/api-keys"),
        ("delete", f"/api/v1/projects/{project_id}/api-keys/{key_id}"),
    ]:
        assert getattr(client, method)(path, headers=ORIGIN).status_code == 404


def test_generated_key_authenticates_sdk_and_revocation_blocks_it(portal):
    client, _ = portal
    register(client)
    project_id = project(client)
    another_id = project(client, "Another project")
    key = client.post(f"/api/v1/projects/{project_id}/api-keys", headers=ORIGIN).json()
    headers = {"X-API-Key": key["key_value"]}
    assert client.post("/api/v1/ai-tools/", json={"tool_title": "test_tool"}, headers=headers).status_code == 201
    assert client.post("/api/v1/ai-tools/", json={"tool_title": "test_tool", "project_id": another_id}, headers=headers).status_code == 403
    assert client.delete(f"/api/v1/projects/{project_id}/api-keys/{key['id']}", headers=ORIGIN).status_code == 204
    assert client.get(f"/api/v1/projects/{project_id}/api-keys").json() == []
    assert client.post("/api/v1/ai-tools/", json={"tool_title": "test_tool"}, headers=headers).status_code == 403


@pytest.mark.parametrize("origin", [None, "https://untrusted.example", "null"])
def test_untrusted_origins_cannot_write(portal, origin):
    client, _ = portal
    headers = {"Origin": origin} if origin else {}
    assert client.post("/api/v1/auth/register", json={"email": "researcher@example.com", "password": PASSWORD}, headers=headers).status_code == 403


def test_validation_and_unauthenticated_access(portal):
    client, _ = portal
    assert client.get("/api/v1/projects").status_code == 401
    assert client.post("/api/v1/auth/register", json={"email": "not-email", "password": "short"}, headers=ORIGIN).status_code == 422
    register(client)
    assert client.post("/api/v1/projects", json={"name": "   "}, headers=ORIGIN).status_code == 422
    assert client.post("/api/v1/projects", json={"name": "a" * 101}, headers=ORIGIN).status_code == 422
