from sqlalchemy import create_engine
from sqlalchemy.engine import make_url
from sqlalchemy.orm import sessionmaker, DeclarativeBase
from app.core.backend_config import settings

database_url = make_url(settings.DATABASE_URL)
if database_url.drivername == "postgresql":
    database_url = database_url.set(drivername="postgresql+psycopg2")
engine = create_engine(database_url, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

class Base(DeclarativeBase):
    pass

def get_db():
    """
    Dependency to get the database session.
    Yields the session and ensures it is closed after use.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
