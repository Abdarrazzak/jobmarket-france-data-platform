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
    null_counts = _null_counts(jobs)

    metrics = {
        "generated_at": datetime.now(UTC).isoformat(),
        "total_rows": total_rows,
        "unique_job_ids": unique_job_ids,
        "duplicate_job_ids": total_rows - unique_job_ids,
        "empty_title_rows": jobs.where(F.col("title").isNull() | (F.length(F.trim(F.col("title"))) == 0)).count(),
        "empty_company_rows": jobs.where(F.col("company").isNull() | (F.length(F.trim(F.col("company"))) == 0)).count(),
        "empty_source_rows": jobs.where(F.col("source").isNull() | (F.length(F.trim(F.col("source"))) == 0)).count(),
        "sample_source_rows": jobs.where(F.lower(F.col("source")).contains("sample")).count(),
        "example_url_rows": jobs.where(F.lower(F.coalesce(F.col("source_url"), F.lit(""))).contains("example.com")).count(),
        "non_france_rows": jobs.where(
            F.col("country").isNotNull()
            & (F.length(F.trim(F.col("country"))) > 0)
            & (~F.lower(F.col("country")).isin("france", "fr"))
        ).count(),
        "short_description_rows": jobs.where(F.length(F.coalesce(F.col("description"), F.lit(""))) < 500).count(),
        "salary_coverage_ratio": _ratio(
            jobs.where(F.col("salary_min").isNotNull() | F.col("salary_max").isNotNull()).count(),
            total_rows,
        ),
        "null_counts": null_counts,
        "null_ratios": {column: _ratio(count, total_rows) for column, count in null_counts.items()},
        "source_distribution": _top_counts(jobs, "source"),
        "country_distribution": _top_counts(jobs, "country"),
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
        and metrics["sample_source_rows"] == 0
        and metrics["example_url_rows"] == 0
        and metrics["non_france_rows"] == 0
        and not metrics["missing_schema_columns"]
    )


def _null_counts(jobs) -> dict[str, int]:
    expressions = [
        F.sum(F.when(F.col(column).isNull() | (F.trim(F.col(column).cast("string")) == ""), 1).otherwise(0)).alias(column)
        for column in sorted(EXPECTED_SILVER_COLUMNS & set(jobs.columns))
    ]
    if not expressions:
        return {}
    return jobs.agg(*expressions).first().asDict()


def _top_counts(jobs, column: str, limit: int = 20) -> list[dict]:
    if column not in jobs.columns:
        return []
    rows = (
        jobs.where(F.col(column).isNotNull() & (F.length(F.trim(F.col(column).cast("string"))) > 0))
        .groupBy(column)
        .agg(F.count("*").alias("row_count"))
        .orderBy(F.desc("row_count"), F.asc(column))
        .limit(limit)
        .collect()
    )
    return [{column: row[column], "row_count": row["row_count"]} for row in rows]


def _ratio(numerator: int, denominator: int) -> float:
    if denominator == 0:
        return 0.0
    return round(numerator / denominator, 4)
