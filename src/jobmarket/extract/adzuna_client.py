from __future__ import annotations

import time
from typing import Any

import httpx

from jobmarket.extract.location_normalizer import normalize_adzuna_location


class AdzunaClient:
    def __init__(self, app_id: str, app_key: str, country: str = "fr") -> None:
        self.app_id = app_id
        self.app_key = app_key
        self.country = country

    def fetch_jobs(
        self,
        what: str = "data engineer",
        where: str = "France",
        page: int = 1,
        results_per_page: int = 50,
        sort_by: str | None = "date",
        retries: int = 3,
    ) -> list[dict]:
        url = f"https://api.adzuna.com/v1/api/jobs/{self.country}/search/{page}"
        params = {
            "app_id": self.app_id,
            "app_key": self.app_key,
            "what": what,
            "where": where,
            "results_per_page": results_per_page,
            "content-type": "application/json",
        }
        if sort_by:
            params["sort_by"] = sort_by

        last_error: Exception | None = None
        for attempt in range(1, retries + 1):
            try:
                response = httpx.get(url, params=params, timeout=30)
                if response.status_code in {429, 500, 502, 503, 504} and attempt < retries:
                    time.sleep(2.0 * attempt)
                    continue
                response.raise_for_status()
                payload = response.json()
                return [self._normalize_job(job) for job in payload.get("results", [])]
            except httpx.HTTPError as exc:
                last_error = exc
                if attempt < retries:
                    time.sleep(2.0 * attempt)

        if last_error:
            raise last_error
        return []

    def fetch_many(
        self,
        queries: list[str],
        locations: list[str],
        max_pages_per_search: int = 2,
        results_per_page: int = 50,
        throttle_seconds: float = 2.7,
        sort_by: str | None = "date",
    ) -> list[dict]:
        records: list[dict] = []

        for query in queries:
            for location in locations:
                for page in range(1, max_pages_per_search + 1):
                    try:
                        page_records = self.fetch_jobs(
                            what=query,
                            where=location,
                            page=page,
                            results_per_page=results_per_page,
                            sort_by=sort_by,
                        )
                    except httpx.HTTPError:
                        break
                    if not page_records:
                        break
                    records.extend(page_records)
                    time.sleep(throttle_seconds)

        return _deduplicate(records)

    @staticmethod
    def _normalize_job(job: dict[str, Any]) -> dict:
        company = job.get("company") or {}
        location = job.get("location") or {}
        area = location.get("area") or []
        normalized_location = normalize_adzuna_location(area, location.get("display_name"))

        return {
            "source": "adzuna",
            "source_job_id": str(job.get("id", "")),
            "title": job.get("title"),
            "company": company.get("display_name"),
            **normalized_location,
            "description": job.get("description"),
            "salary_min": job.get("salary_min"),
            "salary_max": job.get("salary_max"),
            "contract_type": job.get("contract_type"),
            "publication_date": job.get("created"),
            "url": job.get("redirect_url"),
        }


def _deduplicate(records: list[dict]) -> list[dict]:
    deduplicated: dict[tuple[str, str], dict] = {}
    for record in records:
        key = (record.get("source") or "", record.get("source_job_id") or record.get("url") or "")
        deduplicated[key] = record
    return list(deduplicated.values())
