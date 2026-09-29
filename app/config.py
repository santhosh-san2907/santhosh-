from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "FitBuddy - AI Fitness Plan Generator"
    environment: str = "development"
    debug: bool = True

    database_url: str = "sqlite:///./data/fitbuddy.db"

    gemini_api_key: str = ""
    gemini_workout_model: str = "gemini-2.5-pro"
    gemini_tip_model: str = "gemini-2.5-flash"

    admin_key: str = ""

    max_feedback_length: int = 1000

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()