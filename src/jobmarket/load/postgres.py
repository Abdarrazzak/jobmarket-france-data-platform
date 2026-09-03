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
    "CREATE SCHEMA IF NOT EXISTS ml",
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

INDEX_STATEMENTS = [
    "CREATE INDEX IF NOT EXISTS idx_fact_jobs_source ON analytics.fact_jobs(source)",
    "CREATE INDEX IF NOT EXISTS idx_fact_jobs_publication_date ON analytics.fact_jobs(publication_date DESC)",
    "CREATE INDEX IF NOT EXISTS idx_fact_jobs_company_id ON analytics.fact_jobs(company_id)",
    "CREATE INDEX IF NOT EXISTS idx_fact_jobs_location_id ON analytics.fact_jobs(location_id)",
    "CREATE INDEX IF NOT EXISTS idx_dim_company_name ON analytics.dim_company(company_name)",
    "CREATE INDEX IF NOT EXISTS idx_dim_location_country_city ON analytics.dim_location(country, city)",
    "CREATE INDEX IF NOT EXISTS idx_fact_skills_skill_name ON analytics.fact_skills(skill_name)",
    "CREATE UNIQUE INDEX IF NOT EXISTS ux_fact_skills_job_skill ON analytics.fact_skills(job_id, skill_name)",
    "CREATE INDEX IF NOT EXISTS idx_recommendations_score ON analytics.job_recommendations(score DESC)",
]

SERVING_VIEW_STATEMENTS = [
    """
    CREATE OR REPLACE VIEW serving.jobs_public AS
    SELECT
        j.title,
        c.company_name,
        l.city,
        l.region,
        l.country,
        j.contract_type,
        j.experience_level,
        j.salary_min,
        j.salary_max,
        j.salary_avg,
        j.publication_date,
        j.source,
        j.source_url
    FROM analytics.fact_jobs j
    LEFT JOIN analytics.dim_company c ON j.company_id = c.company_id
    LEFT JOIN analytics.dim_location l ON j.location_id = l.location_id
    """,
    """
    CREATE OR REPLACE VIEW serving.market_by_city AS
    SELECT
        l.city,
        l.region,
        l.country,
        COUNT(j.job_id) AS job_count
    FROM analytics.fact_jobs j
    JOIN analytics.dim_location l ON j.location_id = l.location_id
    WHERE l.country = 'France'
      AND l.city IS NOT NULL
      AND TRIM(l.city) <> ''
      AND LOWER(l.city) NOT IN ('france', 'remote', 'teletravail', 'non renseignee')
      AND POSITION('arrondissement' IN LOWER(l.city)) = 0
    GROUP BY l.city, l.region, l.country
    """,
    """
    CREATE OR REPLACE VIEW serving.skill_demand AS
    SELECT
        skill_name,
        COUNT(DISTINCT job_id) AS job_count
    FROM analytics.fact_skills
    GROUP BY skill_name
    """,
]

ML_VIEW_STATEMENTS = [
    """
    CREATE OR REPLACE VIEW ml.salary_prediction_features AS
    WITH skill_features AS (
        SELECT
            job_id,
            COUNT(DISTINCT skill_name) AS skill_count,
            ARRAY_AGG(DISTINCT skill_name ORDER BY skill_name) AS detected_skills,
            MAX(CASE WHEN skill_name = 'Python' THEN 1 ELSE 0 END) AS has_python,
            MAX(CASE WHEN skill_name = 'SQL' THEN 1 ELSE 0 END) AS has_sql,
            MAX(CASE WHEN skill_name = 'PySpark' THEN 1 ELSE 0 END) AS has_pyspark,
            MAX(CASE WHEN skill_name = 'Spark' THEN 1 ELSE 0 END) AS has_spark,
            MAX(CASE WHEN skill_name = 'Airflow' THEN 1 ELSE 0 END) AS has_airflow,
            MAX(CASE WHEN skill_name = 'DBT' THEN 1 ELSE 0 END) AS has_dbt,
            MAX(CASE WHEN skill_name = 'Databricks' THEN 1 ELSE 0 END) AS has_databricks,
            MAX(CASE WHEN skill_name = 'Snowflake' THEN 1 ELSE 0 END) AS has_snowflake,
            MAX(CASE WHEN skill_name = 'Azure' THEN 1 ELSE 0 END) AS has_azure,
            MAX(CASE WHEN skill_name = 'AWS' THEN 1 ELSE 0 END) AS has_aws,
            MAX(CASE WHEN skill_name = 'GCP' THEN 1 ELSE 0 END) AS has_gcp,
            MAX(CASE WHEN skill_name = 'Power BI' THEN 1 ELSE 0 END) AS has_power_bi,
            MAX(CASE WHEN skill_name = 'Tableau' THEN 1 ELSE 0 END) AS has_tableau,
            MAX(CASE WHEN skill_name = 'Docker' THEN 1 ELSE 0 END) AS has_docker,
            MAX(CASE WHEN skill_name = 'Kubernetes' THEN 1 ELSE 0 END) AS has_kubernetes,
            MAX(CASE WHEN skill_name = 'FastAPI' THEN 1 ELSE 0 END) AS has_fastapi
        FROM analytics.fact_skills
        GROUP BY job_id
    )
    SELECT
        j.job_id,
        j.title,
        c.company_name,
        l.city,
        l.region,
        l.country,
        j.contract_type,
        j.experience_level,
        CASE
            WHEN j.experience_level = 'junior' THEN 1
            WHEN j.experience_level = 'not_specified' THEN 2
            WHEN j.experience_level = 'senior' THEN 3
            ELSE 0
        END AS experience_level_encoded,
        j.salary_min,
        j.salary_max,
        j.salary_avg AS target_salary_avg,
        CASE WHEN j.salary_avg IS NOT NULL THEN 1 ELSE 0 END AS has_salary_target,
        CASE
            WHEN j.salary_avg IS NULL THEN 'missing'
            WHEN j.salary_avg < 15000 THEN 'too_low'
            WHEN j.salary_avg > 200000 THEN 'too_high'
            ELSE 'usable'
        END AS salary_quality_flag,
        COALESCE(sf.skill_count, 0) AS skill_count,
        COALESCE(sf.detected_skills, ARRAY[]::TEXT[]) AS detected_skills,
        COALESCE(sf.has_python, 0) AS has_python,
        COALESCE(sf.has_sql, 0) AS has_sql,
        COALESCE(sf.has_pyspark, 0) AS has_pyspark,
        COALESCE(sf.has_spark, 0) AS has_spark,
        COALESCE(sf.has_airflow, 0) AS has_airflow,
        COALESCE(sf.has_dbt, 0) AS has_dbt,
        COALESCE(sf.has_databricks, 0) AS has_databricks,
        COALESCE(sf.has_snowflake, 0) AS has_snowflake,
        COALESCE(sf.has_azure, 0) AS has_azure,
        COALESCE(sf.has_aws, 0) AS has_aws,
        COALESCE(sf.has_gcp, 0) AS has_gcp,
        COALESCE(sf.has_power_bi, 0) AS has_power_bi,
        COALESCE(sf.has_tableau, 0) AS has_tableau,
        COALESCE(sf.has_docker, 0) AS has_docker,
        COALESCE(sf.has_kubernetes, 0) AS has_kubernetes,
        COALESCE(sf.has_fastapi, 0) AS has_fastapi,
        LENGTH(COALESCE(j.description, '')) AS description_length,
        EXTRACT(YEAR FROM j.publication_date)::INTEGER AS publication_year,
        EXTRACT(MONTH FROM j.publication_date)::INTEGER AS publication_month,
        j.source,
        j.publication_date,
        j.load_date,
        j.ingestion_timestamp
    FROM analytics.fact_jobs j
    LEFT JOIN analytics.dim_company c ON j.company_id = c.company_id
    LEFT JOIN analytics.dim_location l ON j.location_id = l.location_id
    LEFT JOIN skill_features sf ON j.job_id = sf.job_id
    WHERE l.country = 'France'
    """,
    """
    CREATE OR REPLACE VIEW ml.salary_training_dataset AS
    SELECT *
    FROM ml.salary_prediction_features
    WHERE salary_quality_flag = 'usable'
    """,
    """
    CREATE OR REPLACE VIEW ml.salary_inference_dataset AS
    SELECT *
    FROM ml.salary_prediction_features
    WHERE salary_quality_flag <> 'usable'
    """,
    """
    CREATE OR REPLACE VIEW ml.salary_prediction_metadata AS
    SELECT
        (SELECT COUNT(*) FROM ml.salary_prediction_features) AS feature_rows,
        (SELECT COUNT(*) FROM ml.salary_training_dataset) AS training_rows,
        (SELECT COUNT(*) FROM ml.salary_inference_dataset) AS inference_rows,
        (SELECT ROUND(AVG(target_salary_avg)::numeric, 2) FROM ml.salary_training_dataset) AS avg_training_salary,
        (SELECT MIN(target_salary_avg) FROM ml.salary_training_dataset) AS min_training_salary,
        (SELECT MAX(target_salary_avg) FROM ml.salary_training_dataset) AS max_training_salary,
        (SELECT COUNT(*) FROM ml.salary_prediction_features WHERE salary_quality_flag = 'too_low') AS excluded_too_low_salary_rows,
        (SELECT COUNT(*) FROM ml.salary_prediction_features WHERE salary_quality_flag = 'too_high') AS excluded_too_high_salary_rows
    """,
]

DROP_ML_VIEW_STATEMENTS = [
    "DROP VIEW IF EXISTS ml.salary_prediction_metadata",
    "DROP VIEW IF EXISTS ml.salary_training_dataset",
    "DROP VIEW IF EXISTS ml.salary_inference_dataset",
    "DROP VIEW IF EXISTS ml.salary_prediction_features",
]

CONFLICT_COLUMNS = {
    "analytics.dim_company": ["company_id"],
    "analytics.dim_location": ["location_id"],
    "analytics.fact_jobs": ["job_id"],
    "analytics.fact_skills": ["job_id", "skill_name"],
    "analytics.job_recommendations": ["recommendation_id"],
}


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
            for statement in INDEX_STATEMENTS:
                cursor.execute(statement)
            cursor.execute("TRUNCATE TABLE analytics.job_recommendations, analytics.fact_skills")

        counts = {
            "dim_company": _load_dataframe(
                connection,
                spark,
                gold_path / "dim_company",
                "analytics.dim_company",
                CONFLICT_COLUMNS["analytics.dim_company"],
            ),
            "dim_location": _load_dataframe(
                connection,
                spark,
                gold_path / "dim_location",
                "analytics.dim_location",
                CONFLICT_COLUMNS["analytics.dim_location"],
            ),
            "fact_jobs": _load_dataframe(
                connection,
                spark,
                gold_path / "fact_jobs",
                "analytics.fact_jobs",
                CONFLICT_COLUMNS["analytics.fact_jobs"],
            ),
            "fact_skills": _load_dataframe(
                connection,
                spark,
                gold_path / "fact_skills",
                "analytics.fact_skills",
                CONFLICT_COLUMNS["analytics.fact_skills"],
            ),
            "job_recommendations": _load_dataframe(
                connection,
                spark,
                gold_path / "job_recommendations",
                "analytics.job_recommendations",
                CONFLICT_COLUMNS["analytics.job_recommendations"],
            ),
        }
        with connection.cursor() as cursor:
            for statement in SERVING_VIEW_STATEMENTS:
                cursor.execute(statement)
            for statement in DROP_ML_VIEW_STATEMENTS:
                cursor.execute(statement)
            for statement in ML_VIEW_STATEMENTS:
                cursor.execute(statement)
        connection.commit()
        return counts
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()


def _load_dataframe(
    connection,
    spark: SparkSession,
    parquet_path: Path,
    table_name: str,
    conflict_columns: list[str],
) -> int:
    dataframe = read_parquet_as_spark(spark, parquet_path)
    columns = dataframe.columns
    rows = [tuple(row[column] for column in columns) for row in dataframe.collect()]
    if not rows:
        return 0

    insert_sql = build_upsert_sql(table_name, columns, conflict_columns)
    with connection.cursor() as cursor:
        execute_values(cursor, insert_sql, rows)
    return len(rows)


def build_upsert_sql(table_name: str, columns: Iterable[str], conflict_columns: Iterable[str]) -> str:
    columns = list(columns)
    conflict_columns = list(conflict_columns)
    insert_columns = ", ".join(columns)
    conflict_target = ", ".join(conflict_columns)
    update_columns = [column for column in columns if column not in conflict_columns]

    if not update_columns:
        return f"INSERT INTO {table_name} ({insert_columns}) VALUES %s ON CONFLICT ({conflict_target}) DO NOTHING"

    update_clause = ", ".join(f"{column} = EXCLUDED.{column}" for column in update_columns)
    return (
        f"INSERT INTO {table_name} ({insert_columns}) VALUES %s "
        f"ON CONFLICT ({conflict_target}) DO UPDATE SET {update_clause}"
    )
