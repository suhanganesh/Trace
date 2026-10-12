from functools import lru_cache
from pathlib import Path

from dotenv import load_dotenv
from pydantic_settings import BaseSettings, SettingsConfigDict

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
ENV_FILE = PROJECT_ROOT / ".env"

load_dotenv(ENV_FILE)


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=str(ENV_FILE), extra="ignore")

    mongodb_uri: str = ""
    mongodb_database: str = "retailrocket_analytics"
    mongodb_deployment_mode: str = "compact"
    api_host: str = "127.0.0.1"
    api_port: int = 8000
    frontend_url: str = "http://127.0.0.1:5173"

    def cors_allowed_origins(self) -> list[str]:
        """Local dev origins (Vite defaults to 127.0.0.1; browsers may use localhost)."""
        primary = self.frontend_url.rstrip("/")
        origins = [primary]
        if "localhost" in primary:
            origins.append(primary.replace("localhost", "127.0.0.1"))
        if "127.0.0.1" in primary:
            origins.append(primary.replace("127.0.0.1", "localhost"))
        return list(dict.fromkeys(origins))

    @property
    def processing_summary_path(self) -> Path:
        return PROJECT_ROOT / "data" / "processed" / "processing_summary.json"

    @property
    def mongodb_import_report_path(self) -> Path:
        return PROJECT_ROOT / "data" / "processed" / "mongodb_import_report.json"


@lru_cache
def get_settings() -> Settings:
    return Settings()
