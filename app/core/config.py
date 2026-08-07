from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "Reserch2 API"
    # Using a dummy database URL for demonstration purposes
    DATABASE_URL: str = "postgresql://dummy_user:dummy_pass@localhost:5432/dummy_db"
    DUMMY_API_KEY: str = "dummy_secret_key"
    OPENROUTER_API_KEY: str = ""


    class Config:
        env_file = ".env"

settings = Settings()
