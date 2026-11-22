"""One-time update: uv run python -m scripts.hash_existing_api_keys

Stop the backend first. Existing client keys remain valid. No schema change.
"""
from app.core.security import hash_api_key
from app.db.models import ApiKey
from app.db.session import SessionLocal


def hash_existing_keys(db):
    keys = db.query(ApiKey).filter(~ApiKey.key_value.startswith("sha256:")).all()
    for key in keys:
        key.key_value = hash_api_key(key.key_value)
    return len(keys)


if __name__ == "__main__":
    try:
        with SessionLocal.begin() as db:
            count = hash_existing_keys(db)
        print(f"Hashed {count} existing API keys.")
    except Exception as exc:
        print(f"Update failed ({type(exc).__name__}); changes rolled back.")
        raise SystemExit(1) from None
