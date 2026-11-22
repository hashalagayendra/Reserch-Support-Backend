from types import SimpleNamespace

import pytest
from fastapi import FastAPI, HTTPException
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from app.api.deps import get_api_key
from app.api.portal_deps import get_current_user
from app.api.routers.projects import router
from app.core.security import hash_api_key
from app.db.models import ApiKey, Project, User
from app.db.session import get_db
from scripts.hash_existing_api_keys import hash_existing_keys


def test_creation_storage_listing_authentication_and_revocation():
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    for table in (User.__table__, Project.__table__, ApiKey.__table__):
        table.create(engine)
    with Session(engine) as db:
        db.add(User(id=1, email="test@example.com", hashed_password="unused"))
        db.flush()
        db.add(Project(id=1, user_id=1, name="Test"))
        db.commit()
        app = FastAPI()
        app.include_router(router, prefix="/projects")
        app.dependency_overrides[get_current_user] = lambda: SimpleNamespace(id=1)

        def database():
            yield db
        app.dependency_overrides[get_db] = database
        with TestClient(app) as client:
            headers = {"Origin": "http://127.0.0.1:5173"}
            response = client.post("/projects/1/api-keys", headers=headers)
            assert response.status_code == 201
            created = response.json()
            secret = created["key_value"]
            stored = db.get(ApiKey, created["id"])
            assert stored.key_value == hash_api_key(secret)
            assert stored.key_value != secret
            assert get_api_key(secret, db).id == stored.id
            for invalid in (stored.key_value, secret + "invalid"):
                with pytest.raises(HTTPException):
                    get_api_key(invalid, db)
            listing = client.get("/projects/1/api-keys")
            assert "key_value" not in listing.json()[0]
            assert secret not in listing.text and stored.key_value not in listing.text
            assert listing.json()[0]["key_prefix"] == created["key_prefix"]
            assert listing.headers["Cache-Control"] == "no-store"
            assert client.delete(f"/projects/1/api-keys/{stored.id}", headers=headers).status_code == 204
            with pytest.raises(HTTPException):
                get_api_key(secret, db)

        legacy = "rk_legacy-client-key"
        db.add(ApiKey(project_id=1, key_value=legacy))
        db.commit()
        assert hash_existing_keys(db) == 1
        db.commit()
        assert hash_existing_keys(db) == 0
        assert get_api_key(legacy, db).key_value == hash_api_key(legacy)
    engine.dispose()
