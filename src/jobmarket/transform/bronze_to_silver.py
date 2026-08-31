from __future__ import annotations

from pathlib import Path

from pyspark.sql import DataFrame, SparkSession
from pyspark.sql import functions as F
from pyspark.sql.types import DoubleType, StringType

from jobmarket.io import read_json_as_spark, write_parquet


RAW_COLUMNS = [
    "source",
    "source_job_id",
    "title",
    "company",
    "location_city",
    "location_region",
    "location_country",
    "description",
    "salary_min",
    "salary_max",
    "contract_type",
    "publication_date",
    "url",
    "load_date",
    "ingestion_timestamp",
]


def bronze_to_silver(spark: SparkSession, bronze_path: Path, silver_path: Path) -> int:
    raw_jobs = read_json_as_spark(spark, bronze_path)
    silver_jobs = transform_bronze_to_silver(raw_jobs)

    silver_path.mkdir(parents=True, exist_ok=True)
    write_parquet(silver_jobs, silver_path / "jobs", partition_by="load_date")
    return silver_jobs.count()


def transform_bronze_to_silver(raw_jobs: DataFrame) -> DataFrame:
    jobs = raw_jobs
    for column in RAW_COLUMNS:
        if column not in jobs.columns:
            jobs = jobs.withColumn(column, F.lit(None).cast(StringType()))

    cleaned = jobs.select(
        F.sha2(
            F.concat_ws(
                "||",
                F.coalesce(F.col("source").cast(StringType()), F.lit("unknown")),
                F.coalesce(F.col("source_job_id").cast(StringType()), F.col("url").cast(StringType()), F.col("title")),
            ),
            256,
        ).alias("job_id"),
        F.trim(F.col("source").cast(StringType())).alias("source"),
        F.trim(F.col("source_job_id").cast(StringType())).alias("source_job_id"),
        F.regexp_replace(F.trim(F.col("title").cast(StringType())), r"\s+", " ").alias("title"),
        F.regexp_replace(F.trim(F.col("company").cast(StringType())), r"\s+", " ").alias("company"),
        F.regexp_replace(F.trim(F.col("location_city").cast(StringType())), r"\s+", " ").alias("city"),
        F.regexp_replace(F.trim(F.col("location_region").cast(StringType())), r"\s+", " ").alias("region"),
        F.regexp_replace(F.trim(F.col("location_country").cast(StringType())), r"\s+", " ").alias("country"),
        F.regexp_replace(F.trim(F.col("description").cast(StringType())), r"\s+", " ").alias("description"),
        F.col("salary_min").cast(DoubleType()).alias("salary_min"),
        F.col("salary_max").cast(DoubleType()).alias("salary_max"),
        F.upper(F.trim(F.col("contract_type").cast(StringType()))).alias("contract_type"),
        F.to_date(F.col("publication_date")).alias("publication_date"),
        F.trim(F.col("url").cast(StringType())).alias("source_url"),
        F.to_date(F.col("load_date")).alias("load_date"),
        F.to_timestamp(F.col("ingestion_timestamp")).alias("ingestion_timestamp"),
    )

    return (
        cleaned.where(F.col("source").isNotNull() & (F.length(F.trim(F.col("source"))) > 0))
        .where(F.col("title").isNotNull() & (F.length(F.trim(F.col("title"))) > 0))
        .where(F.col("company").isNotNull() & (F.length(F.trim(F.col("company"))) > 0))
        .dropDuplicates(["job_id"])
    )
