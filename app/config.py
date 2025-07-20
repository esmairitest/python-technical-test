import os
from functools import lru_cache

from pydantic import PostgresDsn
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    db_url: PostgresDsn
    db_test_url: PostgresDsn

    @property
    def target_db_url(self) -> str:
        if os.getenv("ENV") == "TESTING":
            return str(self.db_test_url)
        return str(self.db_url)

    class Config:
        env_file = ".env"
        extra = "ignore"


@lru_cache
def get_settings() -> Settings:
    settings = Settings()
    return settings
