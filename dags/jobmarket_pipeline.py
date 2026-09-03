from __future__ import annotations

import os
from datetime import datetime, timedelta

from airflow import DAG
from airflow.operators.bash import BashOperator


DEFAULT_ARGS = {
    "owner": "jobmarket",
    "retries": 1,
    "retry_delay": timedelta(minutes=2),
}

JOBMARKET_AIRFLOW_SCHEDULE = os.getenv("JOBMARKET_AIRFLOW_SCHEDULE", "@daily")


def pipeline_task(task_id: str, step: str) -> BashOperator:
    return BashOperator(
        task_id=task_id,
        bash_command=f"PYTHONPATH=/opt/airflow/src python /opt/airflow/scripts/run_local_pipeline.py --step {step}",
    )


with DAG(
    dag_id="jobmarket_pipeline",
    description="JobMarket ELT pipeline from job sources to analytics warehouse.",
    default_args=DEFAULT_ARGS,
    start_date=datetime(2026, 1, 1),
    schedule=JOBMARKET_AIRFLOW_SCHEDULE,
    catchup=False,
    max_active_runs=1,
    dagrun_timeout=timedelta(hours=3),
    tags=["jobmarket", "elt", "pyspark"],
) as dag:
    dag.doc_md = f"""
    # JobMarket automated ELT

    This DAG automates the full JobMarket pipeline: collection, Bronze/Silver/Gold
    transformations, quality checks, PostgreSQL loading, Adzuna description
    enrichment and serving refresh.

    Current schedule: `{JOBMARKET_AIRFLOW_SCHEDULE}`.

    Examples:
    - daily collection: `@daily`
    - weekly collection every Monday at 06:00: `0 6 * * 1`
    """

    extract_adzuna = pipeline_task("extract_adzuna", "extract_adzuna")
    extract_muse = pipeline_task("extract_muse", "extract_muse")
    extract_web_scraping = pipeline_task("extract_web_scraping", "extract_web_scraping")
    store_bronze = pipeline_task("store_bronze", "store_bronze")
    bronze_to_silver = pipeline_task("bronze_to_silver", "bronze_to_silver")
    silver_to_gold = pipeline_task("silver_to_gold", "silver_to_gold")
    extract_skills = pipeline_task("extract_skills", "extract_skills")
    build_recommendations = pipeline_task("build_recommendations", "build_recommendations")
    quality_checks = pipeline_task("quality_checks", "quality_checks")
    data_profile = pipeline_task("data_profile", "data_profile")
    load_postgres = pipeline_task("load_postgres", "load_postgres")
    backfill_adzuna_descriptions = pipeline_task("backfill_adzuna_descriptions", "backfill_adzuna_descriptions")
    refresh_api = pipeline_task("refresh_api", "refresh_api")
    refresh_dashboard = pipeline_task("refresh_dashboard", "refresh_dashboard")

    (
        extract_adzuna
        >> extract_muse
        >> extract_web_scraping
        >> store_bronze
        >> bronze_to_silver
        >> silver_to_gold
        >> extract_skills
        >> build_recommendations
        >> quality_checks
        >> data_profile
        >> load_postgres
        >> backfill_adzuna_descriptions
        >> refresh_api
        >> refresh_dashboard
    )
