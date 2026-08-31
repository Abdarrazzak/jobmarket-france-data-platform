from __future__ import annotations

import re
import time
from dataclasses import dataclass
from datetime import datetime
from urllib.parse import urljoin

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


class PythonOrgJobsScraper:
    def fetch_jobs(self, base_url: str = "https://www.python.org/jobs/", max_pages: int = 2, throttle_seconds: float = 0.5) -> list[dict]:
        records: list[dict] = []

        for page in range(1, max_pages + 1):
            url = base_url if page == 1 else f"{base_url}?page={page}"
            response = httpx.get(url, timeout=30, headers={"User-Agent": "JobMarketStudentProject/1.0"})
            response.raise_for_status()
            page_records = self._parse_jobs(response.text, url)
            records.extend(page_records)
            if not page_records:
                break
            time.sleep(throttle_seconds)

        return _deduplicate(records)

    def _parse_jobs(self, html: str, page_url: str) -> list[dict]:
        soup = BeautifulSoup(html, "html.parser")
        jobs: list[dict] = []

        for card in soup.select("ol.list-recent-jobs li"):
            title_link = card.select_one("h2 a")
            if not title_link:
                continue

            location_link = card.select_one("span.listing-location a")
            text = card.get_text(" ", strip=True)
            company = self._extract_company(card)
            posted_date = self._extract_posted_date(text)
            job_url = urljoin(page_url, title_link.get("href", ""))

            jobs.append(
                {
                    "source": "python_org_scraping",
                    "source_job_id": job_url,
                    "title": title_link.get_text(" ", strip=True),
                    "company": company,
                    "location_city": location_link.get_text(" ", strip=True) if location_link else None,
                    "location_region": None,
                    "location_country": None,
                    "description": text,
                    "salary_min": None,
                    "salary_max": None,
                    "contract_type": None,
                    "publication_date": posted_date,
                    "url": job_url,
                }
            )

        return jobs

    @staticmethod
    def _extract_company(card) -> str | None:
        title = card.select_one("h2")
        location = card.select_one("span.listing-location")
        if not title or not location:
            return None
        current = title.find_next_sibling(string=True)
        if current and current.strip():
            return current.strip()
        text = card.get_text("\n", strip=True).splitlines()
        return text[1].strip() if len(text) > 1 else None

    @staticmethod
    def _extract_posted_date(text: str) -> str | None:
        match = re.search(r"Posted:\s*(\d{1,2}\s+[A-Za-z]+\s+\d{4})", text)
        if not match:
            return None
        try:
            return datetime.strptime(match.group(1), "%d %B %Y").date().isoformat()
        except ValueError:
            return None


def _deduplicate(records: list[dict]) -> list[dict]:
    deduplicated: dict[tuple[str, str], dict] = {}
    for record in records:
        key = (record.get("source") or "", record.get("source_job_id") or record.get("url") or "")
        deduplicated[key] = record
    return list(deduplicated.values())
