from __future__ import annotations

from pathlib import Path
from typing import Iterable

import psycopg2
from psycopg2.extras import execute_values
from pyspark.sql import SparkSession

from jobmarket.config import Settings, settings
from jobmarket.io import read_parquet_as_spark


DDL_STATEMENTS = [
    "CREATE SCHEMA IF NOT EXISTS analytics",
    "CREATE SCHEMA IF NOT EXISTS serving",
    """
    CREATE TABLE IF NOT EXISTS analytics.fact_jobs (
        job_id TEXT PRIMARY KEY,
        source TEXT,
        title TEXT,
        company_id TEXT,
        location_id TEXT,
        contract_type TEXT,
        experience_level TEXT,
        salary_min DOUBLE PRECISION,
        salary_max DOUBLE PRECISION,
        salary_avg DOUBLE PRECISION,
        description TEXT,
        publication_date DATE,
        source_url TEXT,
        load_date DATE,
        ingestion_timestamp TIMESTAMP
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS analytics.dim_company (
        company_id TEXT PRIMARY KEY,
        company_name TEXT,
        source TEXT,
        load_date DATE,
        ingestion_timestamp TIMESTAMP
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS analytics.dim_location (
        location_id TEXT PRIMARY KEY,
        city TEXT,
        region TEXT,
        country TEXT,
        source TEXT,
        load_date DATE,
        ingestion_timestamp TIMESTAMP
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS analytics.fact_skills (
        job_id TEXT,
        skill_name TEXT,
        source TEXT,
        load_date DATE,
        ingestion_timestamp TIMESTAMP
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS analytics.job_recommendations (
        recommendation_id TEXT PRIMARY KEY,
        job_id TEXT,
        title TEXT,
        company_name TEXT,
        city TEXT,
        contract_type TEXT,
        experience_level TEXT,
        salary_avg DOUBLE PRECISION,
        input_skills TEXT,
        score DOUBLE PRECISION,
        score_details TEXT,
        load_date DATE,
        ingestion_timestamp TIMESTAMP
    )
    """,
]


def load_gold_to_postgres(spark: SparkSession, gold_path: Path, config: Settings = settings) -> dict[str, int]:
    connection = psycopg2.connect(
        host=config.postgres_host,
        port=config.postgres_port,
        dbname=config.postgres_db,
        user=config.postgres_user,
        password=config.postgres_password,
    )
    connection.autocommit = False

    try:
        with connection.cursor() as cursor:
            for statement in DDL_STATEMENTS:
                cursor.execute(statement)
            for table in [
                "analytics.job_recommendations",
                "analytics.fact_skills",
                "analytics.fact_jobs",
                "analytics.dim_company",
                "analytics.dim_location",
            ]:
                cursor.execute(f"TRUNCATE TABLE {table}")

        counts = {
            "dim_company": _load_dataframe(connection, spark, gold_path / "dim_company", "analytics.dim_company"),
            "dim_location": _load_dataframe(connection, spark, gold_path / "dim_location", "analytics.dim_location"),
            "fact_jobs": _load_dataframe(connection, spark, gold_path / "fact_jobs", "analytics.fact_jobs"),
            "fact_skills": _load_dataframe(connection, spark, gold_path / "fact_skills", "analytics.fact_skills"),
            "job_recommendations": _load_dataframe(
                connection,
                spark,
                gold_path / "job_recommendations",
                "analytics.job_recommendations",
            ),
        }
        connection.commit()
        return counts
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()


def _load_dataframe(connection, spark: SparkSession, parquet_path: Path, table_name: str) -> int:
    dataframe = read_parquet_as_spark(spark, parquet_path)
    columns = dataframe.columns
    rows = [tuple(row[column] for column in columns) for row in dataframe.collect()]
    if not rows:
        return 0

    placeholders = ", ".join(columns)
    insert_sql = f"INSERT INTO {table_name} ({placeholders}) VALUES %s"
    with connection.cursor() as cursor:
        execute_values(cursor, insert_sql, rows)
    return len(rows)
