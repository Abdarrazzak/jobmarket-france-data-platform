from __future__ import annotations

from typing import Any

import httpx


class MuseClient:
    def fetch_jobs(self, page: int = 1, category: str = "Data Science", location: str = "France") -> list[dict]:
        params = {"page": page, "category": category, "location": location}
        response = httpx.get("https://www.themuse.com/api/public/jobs", params=params, timeout=30)
        response.raise_for_status()
        payload = response.json()
        return [self._normalize_job(job) for job in payload.get("results", [])]

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

