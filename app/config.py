from pydantic_settings import BaseSettings
from pathlib import Path


class Settings(BaseSettings):
    database_url: str
    jwt_secret: str = "my_secret_12345"
    jwt_algorithm: str = "HS256"
    jwt_expire_hours: int = 24

    class Config:
        # ищем .env
        env_file = str(Path(__file__).resolve().parent.parent / ".env")
        env_file_encoding = "utf-8"


settings = Settings()