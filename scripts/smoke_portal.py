"""Exercise portal routes against configured PostgreSQL, then roll back all rows.

Run explicitly with: python -m scripts.smoke_portal
Never prints credentials, cookies or generated keys. Missing tables must first
be created by normal backend startup. This is separate from isolated pytest tests.
"""
import secrets

import httpx
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.backend_config import settings
from app.db.session import engine, get_db
from app.main import app


def check(response, expected: int, step: str):
    if response.status_code != expected:
        raise RuntimeError(f"{step}: HTTP {response.status_code}, expected {expected}")
    return response


def main():
    headers = {"Origin": settings.ALLOWED_ORIGINS[0]}
    credentials = {"email": f"smoke-{secrets.token_hex(8)}@example.com", "password": secrets.token_urlsafe(24)}
    with engine.connect() as connection:
        transaction = connection.begin()
        session = Session(bind=connection, join_transaction_mode="create_savepoint")

        def transactional_db():
            yield session

        app.dependency_overrides[get_db] = transactional_db
        client = TestClient(app)
        try:
            check(client.post("/api/v1/auth/register", json=credentials, headers=headers), 201, "Registration")
            check(client.get("/api/v1/auth/me"), 200, "Session restoration")
            check(client.post("/api/v1/auth/logout", headers=headers), 204, "Logout")
            check(client.post("/api/v1/auth/login", json=credentials, headers=headers), 200, "Login")
            project = check(client.post("/api/v1/projects", json={"name": "Temporary portal smoke test"}, headers=headers), 201, "Project creation").json()
            project_path = f"/api/v1/projects/{project['id']}"
            check(client.get(project_path), 200, "Project detail")
            key = check(client.post(project_path + "/api-keys", headers=headers), 201, "Key generation").json()
            check(client.get(project_path + "/api-keys"), 200, "Key viewing")
            sdk_headers = {"X-API-Key": key["key_value"]}
            check(client.post("/api/v1/ai-tools/", json={"tool_title": "temporary_smoke_tool"}, headers=sdk_headers), 201, "SDK authentication")
            check(client.delete(project_path + f"/api-keys/{key['id']}", headers=headers), 204, "Revocation")
            check(client.post("/api/v1/ai-tools/", json={"tool_title": "temporary_smoke_tool"}, headers=sdk_headers), 403, "Revoked SDK key")
            check(client.post("/api/v1/auth/logout", headers=headers), 204, "Final logout")
            print("PostgreSQL smoke passed: authentication, projects, keys, SDK access and revocation.")
        finally:
            client.close()
            session.close()
            transaction.rollback()
            app.dependency_overrides.clear()
            print("Smoke transaction rolled back; no test accounts, projects or keys retained.")
    with httpx.Client(base_url="http://127.0.0.1:5173", timeout=20) as browser_origin:
        check(browser_origin.get("/api/v1/auth/me"), 401, "Vite API proxy")
        check(browser_origin.get("/login"), 200, "Frontend route")
    print("Frontend route and same-origin API proxy passed.")


if __name__ == "__main__":
    try:
        main()
    except Exception as error:
        # SQL driver tracebacks can include query parameters; keep secrets out of logs.
        print(f"Live smoke failed ({type(error).__name__}). Inspect locally without sharing credentials.")
        raise SystemExit(1) from None
