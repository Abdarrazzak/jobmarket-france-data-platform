from __future__ import annotations

import json
from pathlib import Path


DEFAULT_EXTRACTION_PLAN = {
    "focus": {
        "enabled": True,
        "data_keywords": [
            "data engineer",
            "data analyst",
            "data scientist",
            "analytics engineer",
            "business intelligence",
            "machine learning",
            "pyspark",
            "databricks",
            "power bi",
        ],
        "france_terms": ["France", "Paris", "Lyon", "Nantes", "Lille"],
    },
    "adzuna": {
        "enabled": True,
        "country": "fr",
        "results_per_page": 50,
        "max_pages_per_search": 5,
        "throttle_seconds": 2.7,
        "sort_by": "date",
        "queries": [
            "data engineer",
            "data analyst",
            "data scientist",
            "analytics engineer",
            "business intelligence",
            "machine learning engineer",
            "data architect",
            "data manager",
            "consultant data",
        ],
        "locations": ["France"],
    },
    "muse": {
        "enabled": True,
        "max_pages_per_search": 2,
        "throttle_seconds": 0.5,
        "categories": ["Data Science"],
        "locations": ["France", "Paris, France"],
    },
    "python_org_scraping": {
        "enabled": False,
        "max_pages": 1,
        "throttle_seconds": 0.5,
        "base_url": "https://www.python.org/jobs/",
    },
}


def load_extraction_plan(path: Path) -> dict:
    if not path.exists():
        return DEFAULT_EXTRACTION_PLAN
    return json.loads(path.read_text(encoding="utf-8"))
