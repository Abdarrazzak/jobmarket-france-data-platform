from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv


PROJECT_ROOT = Path(__file__).resolve().parents[2]
load_dotenv(PROJECT_ROOT / ".env")


@dataclass(frozen=True)
class Settings:
    project_root: Path = PROJECT_ROOT
    bronze_path: Path = Path(os.getenv("BRONZE_PATH", PROJECT_ROOT / "data" / "local" / "bronze"))
    silver_path: Path = Path(os.getenv("SILVER_PATH", PROJECT_ROOT / "data" / "local" / "silver"))
    gold_path: Path = Path(os.getenv("GOLD_PATH", PROJECT_ROOT / "data" / "local" / "gold"))
    quality_report_path: Path = Path(
        os.getenv("QUALITY_REPORT_PATH", PROJECT_ROOT / "data" / "local" / "quality" / "quality_report.json")
    )
    user_profile_path: Path = Path(os.getenv("USER_PROFILE_PATH", PROJECT_ROOT / "configs" / "user_profile.json"))

    adzuna_app_id: str | None = os.getenv("ADZUNA_APP_ID")
    adzuna_app_key: str | None = os.getenv("ADZUNA_APP_KEY")

    postgres_host: str = os.getenv("POSTGRES_HOST", "localhost")
    postgres_port: int = int(os.getenv("POSTGRES_PORT", "5432"))
    postgres_db: str = os.getenv("POSTGRES_DB", "jobmarket")
    postgres_user: str = os.getenv("POSTGRES_USER", "jobmarket")
    postgres_password: str = os.getenv("POSTGRES_PASSWORD", "jobmarket")


settings = Settings()

