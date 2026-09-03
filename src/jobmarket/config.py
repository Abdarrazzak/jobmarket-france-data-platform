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
    data_profile_report_path: Path = Path(
        os.getenv("DATA_PROFILE_REPORT_PATH", PROJECT_ROOT / "data" / "local" / "profiling" / "data_profile.json")
    )
    pipeline_runs_path: Path = Path(
        os.getenv("PIPELINE_RUNS_PATH", PROJECT_ROOT / "data" / "local" / "monitoring" / "pipeline_runs.jsonl")
    )
    user_profile_path: Path = Path(os.getenv("USER_PROFILE_PATH", PROJECT_ROOT / "configs" / "user_profile.json"))
    extraction_plan_path: Path = Path(
        os.getenv("EXTRACTION_PLAN_PATH", PROJECT_ROOT / "configs" / "extraction_plan.json")
    )

    adzuna_app_id: str | None = os.getenv("ADZUNA_APP_ID")
    adzuna_app_key: str | None = os.getenv("ADZUNA_APP_KEY")

    postgres_host: str = os.getenv("POSTGRES_HOST", "localhost")
    postgres_port: int = int(os.getenv("POSTGRES_PORT", "5432"))
    postgres_db: str = os.getenv("POSTGRES_DB", "jobmarket")
    postgres_user: str = os.getenv("POSTGRES_USER", "")
    postgres_password: str = os.getenv("POSTGRES_PASSWORD", "")

    adzuna_description_backfill_max_jobs: int = int(os.getenv("ADZUNA_DESCRIPTION_BACKFILL_MAX_JOBS", "50"))
    adzuna_description_backfill_min_chars: int = int(os.getenv("ADZUNA_DESCRIPTION_BACKFILL_MIN_CHARS", "900"))
    adzuna_description_backfill_max_chars: int = int(os.getenv("ADZUNA_DESCRIPTION_BACKFILL_MAX_CHARS", "20000"))
    adzuna_description_backfill_throttle_seconds: float = float(
        os.getenv("ADZUNA_DESCRIPTION_BACKFILL_THROTTLE_SECONDS", "1.0")
    )
    adzuna_description_backfill_timeout_seconds: float = float(
        os.getenv("ADZUNA_DESCRIPTION_BACKFILL_TIMEOUT_SECONDS", "8.0")
    )
    adzuna_description_backfill_retries: int = int(os.getenv("ADZUNA_DESCRIPTION_BACKFILL_RETRIES", "1"))


settings = Settings()
