# app/core/config.py
import os
from pydantic_settings import BaseSettings
from dotenv import load_dotenv
from functools import lru_cache

# Load environment variables from .env file
load_dotenv()


class Settings(BaseSettings):
    # Database settings
    DATABASE_URL: str

    # JWT settings
    SECRET_KEY: str
    ALGORITHM: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int


# @lru_cache()  # Cache the settings object
def get_settings():
    return Settings()

# get_settings.cache_clear()

# Get settings instance
settings = get_settings()
