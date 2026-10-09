from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

class BackendSettings(BaseSettings):
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "Reserch2 API"
    DATABASE_URL: str = "postgresql://dummy_user:dummy_pass@localhost:5432/dummy_db"
    EMBEDDING_MODEL: str = "voyageai/voyage-4-lite"
    ALLOWED_ORIGINS: list[str] = ["http://localhost:5173", "http://127.0.0.1:5173"]
    SESSION_COOKIE_NAME: str = "research_session"
    SESSION_COOKIE_SECURE: bool = False
    SESSION_HOURS: int = Field(default=8, ge=1, le=720)
    ENABLE_CLIENT_TEST_ROUTES: bool = False

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

backend_settings = BackendSettings()

# Alias for backwards compatibility
settings = backend_settings
