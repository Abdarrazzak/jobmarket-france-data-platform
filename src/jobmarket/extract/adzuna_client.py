from __future__ import annotations

from typing import Any

import httpx


class AdzunaClient:
    def __init__(self, app_id: str, app_key: str, country: str = "fr") -> None:
        self.app_id = app_id
        self.app_key = app_key
        self.country = country

    def fetch_jobs(self, what: str = "data engineer", where: str = "France", page: int = 1) -> list[dict]:
        url = f"https://api.adzuna.com/v1/api/jobs/{self.country}/search/{page}"
        params = {
            "app_id": self.app_id,
            "app_key": self.app_key,
            "what": what,
            "where": where,
            "results_per_page": 50,
            "content-type": "application/json",
        }
        response = httpx.get(url, params=params, timeout=30)
        response.raise_for_status()
        payload = response.json()
        return [self._normalize_job(job) for job in payload.get("results", [])]

    @staticmethod
    def _normalize_job(job: dict[str, Any]) -> dict:
        company = job.get("company") or {}
        location = job.get("location") or {}
        area = location.get("area") or []

        return {
            "source": "adzuna",
            "source_job_id": str(job.get("id", "")),
            "title": job.get("title"),
            "company": company.get("display_name"),
            "location_city": area[-1] if area else location.get("display_name"),
            "location_region": area[-2] if len(area) >= 2 else None,
            "location_country": area[0] if area else "France",
            "description": job.get("description"),
            "salary_min": job.get("salary_min"),
            "salary_max": job.get("salary_max"),
            "contract_type": job.get("contract_type"),
            "publication_date": job.get("created"),
            "url": job.get("redirect_url"),
        }

