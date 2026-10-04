from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from contextlib import asynccontextmanager
import uvicorn

from app.core.config import settings
from app.api.router import api_router
from app.db.session import engine
from app.db.models import Base

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Create tables for demonstration purposes. In a real app, use Alembic migrations.
    try:
        with engine.connect() as conn:
            conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector;"))
            conn.commit()
        Base.metadata.create_all(bind=engine)
        print("Database tables created/verified successfully on startup.")
    except Exception as e:
        print(f"Warning: Could not connect to the database to create tables. {e}")
    yield

app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    lifespan=lifespan
)

# Set up CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix=settings.API_V1_STR)

@app.get("/")
def root():
    return {"message": "Welcome to Reserch2 API. Go to /docs for the swagger UI."}

def start():
    """
    This function is used as the entry point for the `reserch2` CLI script.
    """
    uvicorn.run("app.main:app", host="127.0.0.1", port=8000, reload=True)
