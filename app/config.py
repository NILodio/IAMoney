from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DATABASE_URL: str = "sqlite:///./expenses.db"

    WHATSAPP_VERIFY_TOKEN: str = "change_me"
    WHATSAPP_ACCESS_TOKEN: str = "change_me"
    WHATSAPP_PHONE_NUMBER_ID: str = "change_me"

    OPENAI_API_KEY: str = ""

    # API base URL for MCP server to connect to FastAPI
    API_BASE_URL: str = "http://localhost:8000"

    class Config:
        env_file = ".env"


settings = Settings()
