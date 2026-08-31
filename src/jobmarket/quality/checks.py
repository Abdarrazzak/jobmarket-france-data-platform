from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path

from pyspark.sql import SparkSession
from pyspark.sql import functions as F

from jobmarket.io import read_parquet_as_spark


EXPECTED_SILVER_COLUMNS = {
    "job_id",
    "source",
    "title",
    "company",
    "city",
    "region",
    "country",
    "description",
    "salary_min",
    "salary_max",
    "contract_type",
    "publication_date",
    "source_url",
    "load_date",
    "ingestion_timestamp",
}


def run_quality_checks(spark: SparkSession, silver_path: Path, report_path: Path) -> dict:
    jobs = read_parquet_as_spark(spark, silver_path / "jobs")
    total_rows = jobs.count()
    unique_job_ids = jobs.select("job_id").distinct().count()

    metrics = {
        "generated_at": datetime.now(UTC).isoformat(),
        "total_rows": total_rows,
        "unique_job_ids": unique_job_ids,
        "duplicate_job_ids": total_rows - unique_job_ids,
        "empty_title_rows": jobs.where(F.col("title").isNull() | (F.length(F.trim(F.col("title"))) == 0)).count(),
        "empty_company_rows": jobs.where(F.col("company").isNull() | (F.length(F.trim(F.col("company"))) == 0)).count(),
        "empty_source_rows": jobs.where(F.col("source").isNull() | (F.length(F.trim(F.col("source"))) == 0)).count(),
        "missing_schema_columns": sorted(EXPECTED_SILVER_COLUMNS - set(jobs.columns)),
    }
    metrics["status"] = "PASS" if _is_success(metrics) else "FAIL"

    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(metrics, indent=2), encoding="utf-8")
    return metrics


def _is_success(metrics: dict) -> bool:
    return (
        metrics["duplicate_job_ids"] == 0
        and metrics["empty_title_rows"] == 0
        and metrics["empty_company_rows"] == 0
        and metrics["empty_source_rows"] == 0
        and not metrics["missing_schema_columns"]
    )
