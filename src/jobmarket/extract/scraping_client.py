from __future__ import annotations

from dataclasses import dataclass

import httpx
from bs4 import BeautifulSoup


@dataclass(frozen=True)
class ScrapingSelectors:
    card: str
    title: str
    company: str
    location: str
    description: str
    url: str | None = None


class StaticJobPageScraper:
    """Small, polite scraper for simple public job-card pages."""

    def fetch_jobs(self, url: str, selectors: ScrapingSelectors, source: str = "web_scraping") -> list[dict]:
        response = httpx.get(url, timeout=30, headers={"User-Agent": "JobMarketStudentProject/1.0"})
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")

        jobs: list[dict] = []
        for index, card in enumerate(soup.select(selectors.card), start=1):
            title = self._text(card, selectors.title)
            company = self._text(card, selectors.company)
            location = self._text(card, selectors.location)
            description = self._text(card, selectors.description)
            link = card.select_one(selectors.url)["href"] if selectors.url and card.select_one(selectors.url) else url

            jobs.append(
                {
                    "source": source,
                    "source_job_id": f"scraped-{index}",
                    "title": title,
                    "company": company,
                    "location_city": location,
                    "location_region": None,
                    "location_country": "France",
                    "description": description,
                    "salary_min": None,
                    "salary_max": None,
                    "contract_type": None,
                    "publication_date": None,
                    "url": link,
                }
            )
        return jobs

    @staticmethod
    def _text(card, selector: str) -> str | None:
        element = card.select_one(selector)
        return element.get_text(" ", strip=True) if element else None

