import os
from dataclasses import dataclass

DEFAULT_CORS_ALLOW_ORIGINS = (
    "http://127.0.0.1:5173",
    "http://localhost:5173",
    "https://humeyrapolat.github.io",
)


@dataclass(frozen=True)
class Settings:
    app_name: str = "AI Job Application Agent"
    app_env: str = "local"
    log_level: str = "INFO"
    cors_allow_origins: tuple[str, ...] = DEFAULT_CORS_ALLOW_ORIGINS


def _parse_csv_env(value: str | None, default: tuple[str, ...]) -> tuple[str, ...]:
    if value is None:
        return default

    items = tuple(item.strip() for item in value.split(",") if item.strip())
    return items or default


def get_api_key() -> str | None:
    """Shared-secret key that protects endpoints exposing stored candidate data.

    Read lazily (per call) rather than frozen on `settings`, so it can be
    rotated without a restart and so tests can set/unset it per-test.
    """
    return os.getenv("API_KEY")


settings = Settings(
    app_name=os.getenv("APP_NAME", "AI Job Application Agent"),
    app_env=os.getenv("APP_ENV", "local"),
    log_level=os.getenv("LOG_LEVEL", "INFO"),
    cors_allow_origins=_parse_csv_env(
        os.getenv("CORS_ALLOW_ORIGINS"),
        DEFAULT_CORS_ALLOW_ORIGINS,
    ),
)
