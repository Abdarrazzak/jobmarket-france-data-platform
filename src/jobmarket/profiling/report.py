from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from urllib.parse import urlparse

from pyspark.sql import DataFrame, SparkSession
from pyspark.sql import functions as F

from jobmarket.io import read_parquet_as_spark


def generate_data_profile(
    spark: SparkSession,
    silver_path: Path,
    gold_path: Path,
    report_path: Path,
) -> dict:
    jobs = read_parquet_as_spark(spark, silver_path / "jobs")
    profile = {
        "generated_at": datetime.now(UTC).isoformat(),
        "silver_jobs": _profile_jobs(jobs),
        "gold_tables": _profile_gold_tables(spark, gold_path),
    }

    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(profile, indent=2, ensure_ascii=False), encoding="utf-8")
    _write_markdown_summary(profile, report_path.with_suffix(".md"))
    return profile


def _profile_jobs(jobs: DataFrame) -> dict:
    row_count = jobs.count()
    columns = jobs.columns

    profile = {
        "row_count": row_count,
        "column_count": len(columns),
        "columns": columns,
        "duplicate_job_ids": row_count - jobs.select("job_id").distinct().count() if "job_id" in columns else None,
        "null_counts": _null_counts(jobs),
        "null_ratios": _null_ratios(jobs, row_count),
        "source_distribution": _top_counts(jobs, "source"),
        "country_distribution": _top_counts(jobs, "country"),
        "city_top_10": _top_counts(jobs, "city", limit=10),
        "publication_date_range": _date_range(jobs, "publication_date"),
        "salary_stats": _numeric_stats(jobs, "salary_avg", "salary_min", "salary_max"),
        "description_length_stats": _description_stats(jobs),
        "source_url_domains": _domain_distribution(jobs),
    }
    return profile


def _profile_gold_tables(spark: SparkSession, gold_path: Path) -> dict:
    tables = {}
    for table_name in ("fact_jobs", "dim_company", "dim_location", "fact_skills", "job_recommendations"):
        try:
            dataframe = read_parquet_as_spark(spark, gold_path / table_name)
            tables[table_name] = {
                "row_count": dataframe.count(),
                "columns": dataframe.columns,
            }
        except FileNotFoundError:
            tables[table_name] = {
                "row_count": 0,
                "columns": [],
                "status": "missing",
            }
    return tables


def _null_counts(dataframe: DataFrame) -> dict[str, int]:
    expressions = [
        F.sum(F.when(F.col(column).isNull() | (F.trim(F.col(column).cast("string")) == ""), 1).otherwise(0)).alias(column)
        for column in dataframe.columns
    ]
    return dataframe.agg(*expressions).first().asDict()


def _null_ratios(dataframe: DataFrame, row_count: int) -> dict[str, float]:
    if row_count == 0:
        return {column: 0.0 for column in dataframe.columns}
    return {
        column: round(count / row_count, 4)
        for column, count in _null_counts(dataframe).items()
    }


def _top_counts(dataframe: DataFrame, column: str, limit: int = 20) -> list[dict]:
    if column not in dataframe.columns:
        return []
    rows = (
        dataframe.where(F.col(column).isNotNull() & (F.length(F.trim(F.col(column).cast("string"))) > 0))
        .groupBy(column)
        .agg(F.count("*").alias("row_count"))
        .orderBy(F.desc("row_count"), F.asc(column))
        .limit(limit)
        .collect()
    )
    return [{column: row[column], "row_count": row["row_count"]} for row in rows]


def _date_range(dataframe: DataFrame, column: str) -> dict[str, str | None]:
    if column not in dataframe.columns:
        return {"min": None, "max": None}
    row = dataframe.agg(F.min(column).alias("min"), F.max(column).alias("max")).first()
    return {
        "min": str(row["min"]) if row["min"] is not None else None,
        "max": str(row["max"]) if row["max"] is not None else None,
    }


def _numeric_stats(dataframe: DataFrame, *columns: str) -> dict[str, dict[str, float | None]]:
    stats = {}
    for column in columns:
        if column not in dataframe.columns:
            continue
        row = dataframe.agg(
            F.count(column).alias("non_null_count"),
            F.round(F.min(column), 2).alias("min"),
            F.round(F.avg(column), 2).alias("avg"),
            F.round(F.max(column), 2).alias("max"),
        ).first()
        stats[column] = row.asDict()
    return stats


def _description_stats(dataframe: DataFrame) -> dict[str, float | int | None]:
    if "description" not in dataframe.columns:
        return {}
    row = dataframe.select(F.length(F.coalesce(F.col("description"), F.lit(""))).alias("description_length")).agg(
        F.round(F.min("description_length"), 2).alias("min"),
        F.round(F.avg("description_length"), 2).alias("avg"),
        F.round(F.max("description_length"), 2).alias("max"),
        F.sum(F.when(F.col("description_length") < 500, 1).otherwise(0)).alias("short_description_rows"),
    ).first()
    return row.asDict()


def _domain_distribution(dataframe: DataFrame) -> list[dict]:
    if "source_url" not in dataframe.columns:
        return []

    rows = (
        dataframe.select("source_url")
        .where(F.col("source_url").isNotNull() & (F.length(F.trim(F.col("source_url"))) > 0))
        .limit(10000)
        .collect()
    )
    counts: dict[str, int] = {}
    for row in rows:
        hostname = urlparse(row["source_url"]).hostname or "unknown"
        counts[hostname] = counts.get(hostname, 0) + 1

    return [
        {"domain": domain, "row_count": count}
        for domain, count in sorted(counts.items(), key=lambda item: (-item[1], item[0]))[:20]
    ]


def _write_markdown_summary(profile: dict, output_path: Path) -> None:
    silver = profile["silver_jobs"]
    lines = [
        "# Profilage technique des données",
        "",
        f"- Généré le : {profile['generated_at']}",
        f"- Lignes Silver : {silver['row_count']}",
        f"- Colonnes Silver : {silver['column_count']}",
        f"- Doublons `job_id` : {silver['duplicate_job_ids']}",
        "",
        "## Distribution par source",
        "",
        "| Source | Lignes |",
        "| --- | ---: |",
    ]
    lines.extend(f"| {row.get('source')} | {row['row_count']} |" for row in silver["source_distribution"])

    lines.extend(["", "## Top villes", "", "| Ville | Lignes |", "| --- | ---: |"])
    lines.extend(f"| {row.get('city')} | {row['row_count']} |" for row in silver["city_top_10"])

    lines.extend(["", "## Tables Gold", "", "| Table | Lignes |", "| --- | ---: |"])
    lines.extend(
        f"| {table_name} | {table_profile['row_count']} |"
        for table_name, table_profile in profile["gold_tables"].items()
    )

    output_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
