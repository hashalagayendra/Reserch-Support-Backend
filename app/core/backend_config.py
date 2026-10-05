from pydantic_settings import BaseSettings

class BackendSettings(BaseSettings):
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "Reserch2 API"
    DATABASE_URL: str = "postgresql://dummy_user:dummy_pass@localhost:5432/dummy_db"
    EMBEDDING_MODEL: str = "voyageai/voyage-4-lite"

    class Config:
        env_file = ".env"
        extra = "ignore"

backend_settings = BackendSettings()

# Alias for backwards compatibility
settings = backend_settings
