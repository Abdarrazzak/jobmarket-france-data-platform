from __future__ import annotations

from functools import reduce
from pathlib import Path

from pyspark.sql import DataFrame, SparkSession
from pyspark.sql import functions as F

from jobmarket.io import read_parquet_as_spark, write_parquet


SKILL_PATTERNS: dict[str, str] = {
    "Python": r"(^|[^a-z0-9])python([^a-z0-9]|$)",
    "SQL": r"(^|[^a-z0-9])sql([^a-z0-9]|$)",
    "PostgreSQL": r"(^|[^a-z0-9])postgresql([^a-z0-9]|$)",
    "Power BI": r"(^|[^a-z0-9])power\s*bi([^a-z0-9]|$)",
    "Tableau": r"(^|[^a-z0-9])tableau([^a-z0-9]|$)",
    "Excel": r"(^|[^a-z0-9])excel([^a-z0-9]|$)",
    "Airflow": r"(^|[^a-z0-9])airflow([^a-z0-9]|$)",
    "Docker": r"(^|[^a-z0-9])docker([^a-z0-9]|$)",
    "Kubernetes": r"(^|[^a-z0-9])kubernetes([^a-z0-9]|$)",
    "Azure": r"(^|[^a-z0-9])azure([^a-z0-9]|$)",
    "AWS": r"(^|[^a-z0-9])aws([^a-z0-9]|$)",
    "GCP": r"(^|[^a-z0-9])gcp([^a-z0-9]|$)",
    "Spark": r"(^|[^a-z0-9])spark([^a-z0-9]|$)",
    "PySpark": r"(^|[^a-z0-9])pyspark([^a-z0-9]|$)",
    "Kafka": r"(^|[^a-z0-9])kafka([^a-z0-9]|$)",
    "Databricks": r"(^|[^a-z0-9])databricks([^a-z0-9]|$)",
    "Snowflake": r"(^|[^a-z0-9])snowflake([^a-z0-9]|$)",
    "DBT": r"(^|[^a-z0-9])dbt([^a-z0-9]|$)",
    "Git": r"(^|[^a-z0-9])git([^a-z0-9]|$)",
    "Linux": r"(^|[^a-z0-9])linux([^a-z0-9]|$)",
    "FastAPI": r"(^|[^a-z0-9])fastapi([^a-z0-9]|$)",
}


def extract_skills(spark: SparkSession, silver_path: Path, gold_path: Path) -> int:
    jobs = read_parquet_as_spark(spark, silver_path / "jobs")
    skills = extract_skills_from_jobs(jobs)

    output_path = gold_path / "fact_skills"
    output_path.mkdir(parents=True, exist_ok=True)
    write_parquet(skills, output_path, partition_by="load_date")

    trends = skills.groupBy("load_date", "skill_name").agg(F.countDistinct("job_id").alias("job_count"))
    write_parquet(trends, gold_path / "skill_trends")

    return skills.count()


def extract_skills_from_jobs(jobs: DataFrame) -> DataFrame:
    searchable_jobs = jobs.withColumn(
        "search_text",
        F.lower(F.concat_ws(" ", F.coalesce(F.col("title"), F.lit("")), F.coalesce(F.col("description"), F.lit("")))),
    )

    skill_frames = [
        searchable_jobs.where(F.col("search_text").rlike(pattern)).select(
            "job_id",
            F.lit(skill).alias("skill_name"),
            "source",
            "load_date",
            "ingestion_timestamp",
        )
        for skill, pattern in SKILL_PATTERNS.items()
    ]

    if not skill_frames:
        return searchable_jobs.limit(0).select(
            "job_id",
            F.lit("").alias("skill_name"),
            "source",
            "load_date",
            "ingestion_timestamp",
        )

    return reduce(DataFrame.unionByName, skill_frames).dropDuplicates(["job_id", "skill_name"])
