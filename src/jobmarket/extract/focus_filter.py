from __future__ import annotations

import unicodedata


DEFAULT_DATA_KEYWORDS = [
    "analytics engineer",
    "bi analyst",
    "big data",
    "business intelligence",
    "data analyst",
    "data architect",
    "data engineer",
    "data manager",
    "data product",
    "data scientist",
    "databricks",
    "dbt",
    "etl",
    "elt",
    "machine learning",
    "ml engineer",
    "power bi",
    "pyspark",
    "snowflake",
]

DEFAULT_FRANCE_TERMS = [
    "france",
    "paris",
    "ile-de-france",
    "lyon",
    "toulouse",
    "nantes",
    "lille",
    "bordeaux",
    "marseille",
    "rennes",
    "montpellier",
    "grenoble",
    "strasbourg",
    "nice",
]


def filter_jobs_for_focus(
    records: list[dict],
    data_keywords: list[str] | None = None,
    france_terms: list[str] | None = None,
) -> list[dict]:
    keywords = data_keywords or DEFAULT_DATA_KEYWORDS
    location_terms = france_terms or DEFAULT_FRANCE_TERMS

    return [
        record
        for record in records
        if _is_data_job(record, keywords) and _is_french_market_job(record, location_terms)
    ]


def _is_data_job(record: dict, keywords: list[str]) -> bool:
    searchable_text = _normalize(
        " ".join(
            str(record.get(field) or "")
            for field in ("title", "description", "contract_type")
        )
    )
    return any(_normalize(keyword) in searchable_text for keyword in keywords)


def _is_french_market_job(record: dict, france_terms: list[str]) -> bool:
    location_text = _normalize(
        " ".join(
            str(record.get(field) or "")
            for field in ("location_city", "location_region", "location_country")
        )
    )
    return any(_normalize(term) in location_text for term in france_terms)


def _normalize(value: str) -> str:
    ascii_value = unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode("ascii")
    return " ".join(ascii_value.lower().split())
