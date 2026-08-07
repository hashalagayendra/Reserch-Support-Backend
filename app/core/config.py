from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "Reserch2 API"
    # Using a dummy database URL for demonstration purposes
    DATABASE_URL: str = "postgresql://dummy_user:dummy_pass@localhost:5432/dummy_db"
    DUMMY_API_KEY: str = "dummy_secret_key"
    PROJECT_API_KEY: str = "sk-dummy-4e970dfd"
    OPENROUTER_API_KEY: str = ""
    TOOL_DISCOVERY_MODEL: str = "deepseek/deepseek-v4-flash"
    TOOL_DISCOVERY_TEMPERATURE: float = 0.8
    EMBEDDING_MODEL: str = "voyageai/voyage-4-lite"


    class Config:
        env_file = ".env"

settings = Settings()
