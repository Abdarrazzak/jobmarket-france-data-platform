from __future__ import annotations

from pathlib import Path

from jobmarket.config import Settings, settings
from jobmarket.extract.adzuna_client import AdzunaClient
from jobmarket.extract.bronze import write_bronze_records
from jobmarket.extract.extraction_plan import load_extraction_plan
from jobmarket.extract.focus_filter import filter_jobs_for_focus
from jobmarket.extract.muse_client import MuseClient
from jobmarket.extract.scraping_client import PythonOrgJobsScraper


def extract_adzuna(config: Settings = settings) -> Path:
    extraction_plan = load_extraction_plan(config.extraction_plan_path)
    plan = extraction_plan.get("adzuna", {})
    if config.adzuna_app_id and config.adzuna_app_key and not config.adzuna_app_id.startswith("replace"):
        try:
            client = AdzunaClient(
                config.adzuna_app_id,
                config.adzuna_app_key,
                country=plan.get("country", "fr"),
            )
            records = client.fetch_many(
                queries=plan.get("queries", ["data engineer"]),
                locations=plan.get("locations", ["France"]),
                max_pages_per_search=int(plan.get("max_pages_per_search", 2)),
                results_per_page=int(plan.get("results_per_page", 50)),
                throttle_seconds=float(plan.get("throttle_seconds", 2.7)),
                sort_by=plan.get("sort_by", "date"),
            )
            records = _filter_records(records, extraction_plan)
            if records:
                return write_bronze_records(records, config.bronze_path, "adzuna")
        except Exception as exc:
            raise RuntimeError("Adzuna extraction failed. No sample data will be loaded.") from exc

    raise RuntimeError("Adzuna credentials are missing. No sample data will be loaded.")


def extract_muse(config: Settings = settings) -> Path:
    extraction_plan = load_extraction_plan(config.extraction_plan_path)
    plan = extraction_plan.get("muse", {})
    try:
        records = MuseClient().fetch_many(
            categories=plan.get("categories", ["Data Science", "Software Engineering"]),
            locations=plan.get("locations", ["France", "Remote"]),
            max_pages_per_search=int(plan.get("max_pages_per_search", 3)),
            throttle_seconds=float(plan.get("throttle_seconds", 0.5)),
        )
        records = _filter_records(records, extraction_plan)
        if records:
            return write_bronze_records(records, config.bronze_path, "muse")
    except Exception:
        records = []

    return write_bronze_records(records, config.bronze_path, "muse")


def extract_web_scraping(config: Settings = settings) -> Path:
    extraction_plan = load_extraction_plan(config.extraction_plan_path)
    plan = extraction_plan.get("python_org_scraping", {})
    records: list[dict] = []
    if plan.get("enabled", True):
        try:
            records = PythonOrgJobsScraper().fetch_jobs(
                base_url=plan.get("base_url", "https://www.python.org/jobs/"),
                max_pages=int(plan.get("max_pages", 2)),
                throttle_seconds=float(plan.get("throttle_seconds", 0.5)),
            )
            records = _filter_records(records, extraction_plan)
            if records:
                return write_bronze_records(records, config.bronze_path, "python_org_scraping")
        except Exception:
            records = []

    return write_bronze_records(records, config.bronze_path, "python_org_scraping")



def _filter_records(records: list[dict], extraction_plan: dict) -> list[dict]:
    focus = extraction_plan.get("focus", {})
    if not focus.get("enabled", True):
        return records

    return filter_jobs_for_focus(
        records,
        data_keywords=focus.get("data_keywords"),
        france_terms=focus.get("france_terms"),
    )
