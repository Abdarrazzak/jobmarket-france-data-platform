from __future__ import annotations

from jobmarket.config import Settings, settings
from jobmarket.enrich.adzuna_descriptions import backfill_adzuna_descriptions_from_postgres
from jobmarket.extract.bronze import write_bronze_manifest
from jobmarket.extract.run_extractors import extract_adzuna, extract_muse, extract_web_scraping
from jobmarket.load.postgres import load_gold_to_postgres
from jobmarket.quality.checks import run_quality_checks
from jobmarket.recommendation.scoring import build_recommendations
from jobmarket.spark import create_spark_session
from jobmarket.transform.bronze_to_silver import bronze_to_silver
from jobmarket.transform.silver_to_gold import silver_to_gold
from jobmarket.transform.skills import extract_skills


PIPELINE_STEPS = [
    "extract_adzuna",
    "extract_muse",
    "extract_web_scraping",
    "store_bronze",
    "bronze_to_silver",
    "silver_to_gold",
    "extract_skills",
    "build_recommendations",
    "quality_checks",
    "load_postgres",
    "backfill_adzuna_descriptions",
    "refresh_api",
    "refresh_dashboard",
]


def run_step(step: str, config: Settings = settings):
    if step == "extract_adzuna":
        return extract_adzuna(config)
    if step == "extract_muse":
        return extract_muse(config)
    if step == "extract_web_scraping":
        return extract_web_scraping(config)
    if step == "store_bronze":
        return write_bronze_manifest(config.bronze_path)
    if step == "refresh_api":
        return "FastAPI reads the refreshed PostgreSQL warehouse."
    if step == "refresh_dashboard":
        return "Streamlit reads the refreshed FastAPI endpoints."
    if step == "backfill_adzuna_descriptions":
        return backfill_adzuna_descriptions_from_postgres(config)

    spark = create_spark_session(f"JobMarket-{step}")
    try:
        if step == "bronze_to_silver":
            return bronze_to_silver(spark, config.bronze_path, config.silver_path)
        if step == "silver_to_gold":
            return silver_to_gold(spark, config.silver_path, config.gold_path)
        if step == "extract_skills":
            return extract_skills(spark, config.silver_path, config.gold_path)
        if step == "build_recommendations":
            return build_recommendations(spark, config.gold_path, config.user_profile_path)
        if step == "quality_checks":
            return run_quality_checks(spark, config.silver_path, config.quality_report_path)
        if step == "load_postgres":
            return load_gold_to_postgres(spark, config.gold_path, config)
    finally:
        spark.stop()

    raise ValueError(f"Unknown pipeline step: {step}")


def run_all(config: Settings = settings, skip_postgres: bool = False) -> dict[str, object]:
    results: dict[str, object] = {}
    for step in PIPELINE_STEPS:
        if skip_postgres and step in {"load_postgres", "backfill_adzuna_descriptions"}:
            results[step] = "Skipped for local demo without PostgreSQL."
            continue
        results[step] = run_step(step, config)
    return results
