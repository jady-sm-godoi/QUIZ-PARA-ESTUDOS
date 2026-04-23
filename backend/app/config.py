from pydantic_settings import BaseSettings
import os


class Settings(BaseSettings):
    openai_api_key: str = ""
    database_url: str = "sqlite:///./quiz.db"
    max_tokens_per_request: int = 15000

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


def get_settings() -> Settings:
    return Settings()


def get_openai_api_key() -> str:
    api_key = os.environ.get("OPENAI_API_KEY", "")
    if not api_key:
        try:
            settings = Settings()
            api_key = settings.openai_api_key
        except:
            pass
    return api_key