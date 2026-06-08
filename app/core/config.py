import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    app_name: str = "AI Job Application Agent"
    app_env: str = "local"
    log_level: str = "INFO"


settings = Settings(
    app_name=os.getenv("APP_NAME", "AI Job Application Agent"),
    app_env=os.getenv("APP_ENV", "local"),
    log_level=os.getenv("LOG_LEVEL", "INFO"),
)
