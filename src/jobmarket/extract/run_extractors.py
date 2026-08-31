from __future__ import annotations

from pathlib import Path

from jobmarket.config import Settings, settings
from jobmarket.extract.adzuna_client import AdzunaClient
from jobmarket.extract.bronze import write_bronze_records
from jobmarket.extract.muse_client import MuseClient
from jobmarket.extract.sample_data import get_sample_jobs


def extract_adzuna(config: Settings = settings) -> Path:
    if config.adzuna_app_id and config.adzuna_app_key and not config.adzuna_app_id.startswith("replace"):
        try:
            records = AdzunaClient(config.adzuna_app_id, config.adzuna_app_key).fetch_jobs()
            return write_bronze_records(records, config.bronze_path, "adzuna")
        except Exception:
            pass

    records = get_sample_jobs("adzuna")
    return write_bronze_records(records, config.bronze_path, "adzuna_sample")


def extract_muse(config: Settings = settings) -> Path:
    try:
        records = MuseClient().fetch_jobs()
        if records:
            return write_bronze_records(records, config.bronze_path, "muse")
    except Exception:
        pass

    records = get_sample_jobs("muse")
    return write_bronze_records(records, config.bronze_path, "muse_sample")


def extract_scraping_sample(config: Settings = settings) -> Path:
    records = get_sample_jobs("scraping")
    return write_bronze_records(records, config.bronze_path, "scraping_sample")

