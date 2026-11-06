from pydantic_settings import BaseSettings

class ClientSideTestSettings(BaseSettings):
    DUMMY_API_KEY: str = "dummy_secret_key"
    PROJECT_API_KEY: str = "sk-dummy-4e970dfd"
    OPENROUTER_API_KEY: str = ""
    TOOL_DISCOVERY_MODEL: str = "deepseek/deepseek-v4-flash"
    TOOL_DISCOVERY_TEMPERATURE: float = 0.8
    MAIN_WORKFLOW_MODEL: str = "deepseek/deepseek-v4-flash"
    MAIN_WORKFLOW_TEMPERATURE: float = 0.0
    ERROR_CORRECTION_MODEL: str = "deepseek/deepseek-v4-flash"
    ERROR_CORRECTION_TEMPERATURE: float = 0.2
    EMBEDDING_MODEL: str = "voyageai/voyage-4-lite"
    TOOL_DB_BASE_URL: str = "http://127.0.0.1:8000/api/v1"

    class Config:
        env_file = ".env"
        extra = "ignore"

client_side_test_settings = ClientSideTestSettings()

# Alias for backwards compatibility
settings = client_side_test_settings
