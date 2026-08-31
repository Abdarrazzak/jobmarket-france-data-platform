from __future__ import annotations

import time
from typing import Any

import httpx


class MuseClient:
    def fetch_jobs(self, page: int = 1, category: str | None = None, location: str | None = None) -> list[dict]:
        params = {"page": page, "category": category, "location": location}
        params = {key: value for key, value in params.items() if value}
        response = httpx.get("https://www.themuse.com/api/public/jobs", params=params, timeout=30)
        response.raise_for_status()
        payload = response.json()
        return [self._normalize_job(job) for job in payload.get("results", [])]

    def fetch_many(
        self,
        categories: list[str],
        locations: list[str],
        max_pages_per_search: int = 3,
        throttle_seconds: float = 0.5,
    ) -> list[dict]:
        records: list[dict] = []

        for category in categories:
            for location in locations:
                for page in range(1, max_pages_per_search + 1):
                    page_records = self.fetch_jobs(page=page, category=category, location=location)
                    records.extend(page_records)
                    if not page_records:
                        break
                    time.sleep(throttle_seconds)

        return _deduplicate(records)

    @staticmethod
    def _normalize_job(job: dict[str, Any]) -> dict:
        company = job.get("company") or {}
        locations = job.get("locations") or []
        levels = job.get("levels") or []
        refs = job.get("refs") or {}

        return {
            "source": "muse",
            "source_job_id": str(job.get("id", "")),
            "title": job.get("name"),
            "company": company.get("name"),
            "location_city": locations[0].get("name") if locations else None,
            "location_region": None,
            "location_country": "France",
            "description": job.get("contents"),
            "salary_min": None,
            "salary_max": None,
            "contract_type": levels[0].get("name") if levels else None,
            "publication_date": job.get("publication_date"),
            "url": refs.get("landing_page"),
        }


def _deduplicate(records: list[dict]) -> list[dict]:
    deduplicated: dict[tuple[str, str], dict] = {}
    for record in records:
        key = (record.get("source") or "", record.get("source_job_id") or record.get("url") or "")
        deduplicated[key] = record
    return list(deduplicated.values())
