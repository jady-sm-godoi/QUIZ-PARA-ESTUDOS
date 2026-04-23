from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    openai_api_key: str
    database_url: str = "sqlite:///./quiz.db"
    max_tokens_per_request: int = 15000

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()