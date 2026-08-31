from __future__ import annotations

import hashlib
import json
import re
import time
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any, Iterable
from urllib.parse import urlparse

import httpx
import psycopg2
from bs4 import BeautifulSoup
from psycopg2.extras import RealDictCursor, execute_values

from jobmarket.config import Settings, settings
from jobmarket.recommendation.scoring import load_user_profile
from jobmarket.transform.skills import SKILL_PATTERNS


REQUEST_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/126.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "fr-FR,fr;q=0.9,en;q=0.8",
    "Connection": "close",
}

DESCRIPTION_LOG_DDL = """
CREATE TABLE IF NOT EXISTS analytics.description_enrichment_log (
    job_id TEXT PRIMARY KEY,
    source_url TEXT,
    status TEXT,
    original_length INTEGER,
    enriched_length INTEGER,
    error_message TEXT,
    scraped_at TIMESTAMP
)
"""


@dataclass(frozen=True)
class BackfillResult:
    candidate_jobs: int
    updated_jobs: int
    skipped_jobs: int
    failed_jobs: int
    refreshed_skills: int
    refreshed_recommendations: int


class AdzunaDescriptionScraper:
    def __init__(self, timeout_seconds: float = 30.0, max_description_chars: int = 20000, retries: int = 3) -> None:
        self.timeout_seconds = timeout_seconds
        self.max_description_chars = max_description_chars
        self.retries = retries

    def fetch_description(self, url: str) -> str | None:
        last_error: Exception | None = None
        for attempt in range(1, self.retries + 1):
            try:
                with httpx.Client(
                    follow_redirects=True,
                    timeout=httpx.Timeout(self.timeout_seconds),
                    headers=REQUEST_HEADERS,
                ) as client:
                    response = client.get(url)
                    response.raise_for_status()
                    return self.extract_description(response.text)
            except (httpx.HTTPError, OSError) as exc:
                last_error = exc
                if attempt < self.retries:
                    time.sleep(0.8 * attempt)

        if last_error:
            raise last_error
        return None

    def extract_description(self, html_text: str) -> str | None:
        soup = BeautifulSoup(html_text, "html.parser")
        candidates: list[str] = []

        candidates.extend(_extract_json_ld_descriptions(soup))
        candidates.extend(_extract_meta_descriptions(soup))
        candidates.extend(_extract_description_blocks(soup))

        cleaned_candidates = [_clean_description(candidate) for candidate in candidates]
        useful_candidates = [candidate for candidate in cleaned_candidates if len(candidate) >= 50]
        if not useful_candidates:
            fallback = _clean_description(soup.get_text(" ", strip=True))
            useful_candidates = [fallback] if len(fallback) >= 150 else []
        if not useful_candidates:
            return None

        best_description = max(useful_candidates, key=len)
        return best_description[: self.max_description_chars]


def backfill_adzuna_descriptions_from_postgres(config: Settings = settings) -> dict[str, int]:
    max_jobs = config.adzuna_description_backfill_max_jobs
    min_chars = config.adzuna_description_backfill_min_chars
    throttle_seconds = config.adzuna_description_backfill_throttle_seconds
    scraper = AdzunaDescriptionScraper(max_description_chars=config.adzuna_description_backfill_max_chars)

    connection = psycopg2.connect(
        host=config.postgres_host,
        port=config.postgres_port,
        dbname=config.postgres_db,
        user=config.postgres_user,
        password=config.postgres_password,
    )
    connection.autocommit = False

    updated_jobs = 0
    skipped_jobs = 0
    failed_jobs = 0

    try:
        _ensure_log_table(connection)
        rows = _fetch_adzuna_jobs(connection, max_jobs=max_jobs, min_chars=min_chars)

        for row in rows:
            job_id = row["job_id"]
            source_url = row["source_url"]
            current_description = row.get("description") or ""
            original_length = len(current_description)

            if not source_url or not _is_adzuna_url(source_url):
                skipped_jobs += 1
                _log_backfill(connection, job_id, source_url, "skipped_non_adzuna_url", original_length, 0)
                continue

            try:
                enriched_description = scraper.fetch_description(source_url)
                enriched_length = len(enriched_description or "")
                if enriched_description and enriched_length > original_length + 50:
                    _update_job_description(connection, job_id, enriched_description)
                    updated_jobs += 1
                    _log_backfill(connection, job_id, source_url, "updated", original_length, enriched_length)
                else:
                    skipped_jobs += 1
                    _log_backfill(connection, job_id, source_url, "skipped_no_longer_description", original_length, enriched_length)
            except Exception as exc:
                failed_jobs += 1
                _log_backfill(connection, job_id, source_url, "failed", original_length, 0, str(exc)[:500])

            time.sleep(throttle_seconds)

        refreshed_skills = refresh_fact_skills_from_postgres(connection)
        refreshed_recommendations = refresh_job_recommendations_from_postgres(connection, config)
        connection.commit()

        result = BackfillResult(
            candidate_jobs=len(rows),
            updated_jobs=updated_jobs,
            skipped_jobs=skipped_jobs,
            failed_jobs=failed_jobs,
            refreshed_skills=refreshed_skills,
            refreshed_recommendations=refreshed_recommendations,
        )
        return result.__dict__
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()


def refresh_fact_skills_from_postgres(connection) -> int:
    with connection.cursor(cursor_factory=RealDictCursor) as cursor:
        cursor.execute(
            """
            SELECT job_id, title, description, source, load_date, ingestion_timestamp
            FROM analytics.fact_jobs
            """
        )
        rows = cursor.fetchall()

    skill_rows = []
    for row in rows:
        search_text = f"{row.get('title') or ''} {row.get('description') or ''}".lower()
        for skill_name, pattern in SKILL_PATTERNS.items():
            if re.search(pattern, search_text):
                skill_rows.append(
                    (
                        row["job_id"],
                        skill_name,
                        row["source"],
                        row["load_date"],
                        row["ingestion_timestamp"],
                    )
                )

    with connection.cursor() as cursor:
        cursor.execute("TRUNCATE TABLE analytics.fact_skills")
        if skill_rows:
            execute_values(
                cursor,
                """
                INSERT INTO analytics.fact_skills
                (job_id, skill_name, source, load_date, ingestion_timestamp)
                VALUES %s
                """,
                skill_rows,
            )

    return len(skill_rows)


def refresh_job_recommendations_from_postgres(connection, config: Settings = settings) -> int:
    profile = load_user_profile(config.user_profile_path)
    requested_skills = {str(skill).lower() for skill in profile.get("skills", [])}
    requested_location = str(profile.get("location", "")).lower()
    requested_contract = str(profile.get("contract_type", "")).upper()
    requested_experience = str(profile.get("experience_level", "")).lower()
    top_n = int(profile.get("top_n", 10))
    input_skills = ", ".join(profile.get("skills", []))

    with connection.cursor(cursor_factory=RealDictCursor) as cursor:
        cursor.execute(
            """
            SELECT
                j.job_id,
                j.title,
                c.company_name,
                l.city,
                j.contract_type,
                j.experience_level,
                j.salary_avg,
                j.load_date,
                j.ingestion_timestamp,
                COALESCE(
                    ARRAY_AGG(DISTINCT fs.skill_name) FILTER (WHERE fs.skill_name IS NOT NULL),
                    ARRAY[]::TEXT[]
                ) AS skills
            FROM analytics.fact_jobs j
            LEFT JOIN analytics.dim_company c ON j.company_id = c.company_id
            LEFT JOIN analytics.dim_location l ON j.location_id = l.location_id
            LEFT JOIN analytics.fact_skills fs ON j.job_id = fs.job_id
            GROUP BY
                j.job_id,
                j.title,
                c.company_name,
                l.city,
                j.contract_type,
                j.experience_level,
                j.salary_avg,
                j.load_date,
                j.ingestion_timestamp
            """
        )
        jobs = cursor.fetchall()

    recommendations = []
    for job in jobs:
        matched_skill_count = len({skill.lower() for skill in job["skills"]} & requested_skills)
        location_bonus = 3 if requested_location and requested_location in str(job.get("city") or "").lower() else 0
        contract_bonus = 2 if str(job.get("contract_type") or "").upper() == requested_contract else 0
        experience_bonus = 1 if str(job.get("experience_level") or "").lower() == requested_experience else 0
        score = matched_skill_count * 10 + location_bonus + contract_bonus + experience_bonus

        recommendations.append(
            (
                _recommendation_id(job["job_id"], input_skills),
                job["job_id"],
                job["title"],
                job["company_name"],
                job["city"],
                job["contract_type"],
                job["experience_level"],
                job["salary_avg"],
                input_skills,
                score,
                (
                    f"skills={matched_skill_count} | "
                    f"location_bonus={location_bonus} | "
                    f"contract_bonus={contract_bonus} | "
                    f"experience_bonus={experience_bonus}"
                ),
                job["load_date"],
                job["ingestion_timestamp"],
            )
        )

    recommendations = sorted(recommendations, key=lambda row: (row[9], row[7] or 0), reverse=True)[:top_n]

    with connection.cursor() as cursor:
        cursor.execute("TRUNCATE TABLE analytics.job_recommendations")
        if recommendations:
            execute_values(
                cursor,
                """
                INSERT INTO analytics.job_recommendations
                (
                    recommendation_id,
                    job_id,
                    title,
                    company_name,
                    city,
                    contract_type,
                    experience_level,
                    salary_avg,
                    input_skills,
                    score,
                    score_details,
                    load_date,
                    ingestion_timestamp
                )
                VALUES %s
                """,
                recommendations,
            )

    return len(recommendations)


def _fetch_adzuna_jobs(connection, max_jobs: int, min_chars: int) -> list[dict]:
    with connection.cursor(cursor_factory=RealDictCursor) as cursor:
        cursor.execute(
            """
            SELECT job_id, source_url, COALESCE(description, '') AS description
            FROM analytics.fact_jobs
            WHERE source = 'adzuna'
              AND source_url IS NOT NULL
              AND LENGTH(COALESCE(description, '')) < %s
            ORDER BY publication_date DESC NULLS LAST, job_id
            LIMIT %s
            """,
            (min_chars, max_jobs),
        )
        return [dict(row) for row in cursor.fetchall()]


def _ensure_log_table(connection) -> None:
    with connection.cursor() as cursor:
        cursor.execute(DESCRIPTION_LOG_DDL)


def _update_job_description(connection, job_id: str, description: str) -> None:
    with connection.cursor() as cursor:
        cursor.execute("UPDATE analytics.fact_jobs SET description = %s WHERE job_id = %s", (description, job_id))


def _log_backfill(
    connection,
    job_id: str,
    source_url: str | None,
    status: str,
    original_length: int,
    enriched_length: int,
    error_message: str | None = None,
) -> None:
    with connection.cursor() as cursor:
        cursor.execute(
            """
            INSERT INTO analytics.description_enrichment_log
            (job_id, source_url, status, original_length, enriched_length, error_message, scraped_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (job_id)
            DO UPDATE SET
                source_url = EXCLUDED.source_url,
                status = EXCLUDED.status,
                original_length = EXCLUDED.original_length,
                enriched_length = EXCLUDED.enriched_length,
                error_message = EXCLUDED.error_message,
                scraped_at = EXCLUDED.scraped_at
            """,
            (job_id, source_url, status, original_length, enriched_length, error_message, datetime.now(UTC)),
        )


def _extract_json_ld_descriptions(soup: BeautifulSoup) -> list[str]:
    descriptions: list[str] = []
    for script in soup.select("script[type='application/ld+json']"):
        raw_json = script.string or script.get_text(strip=True)
        if not raw_json:
            continue
        try:
            payload = json.loads(raw_json)
        except json.JSONDecodeError:
            continue
        for item in _iter_json_objects(payload):
            item_type = item.get("@type")
            item_types = item_type if isinstance(item_type, list) else [item_type]
            if "JobPosting" in item_types and item.get("description"):
                descriptions.append(str(item["description"]))
    return descriptions


def _extract_meta_descriptions(soup: BeautifulSoup) -> list[str]:
    descriptions: list[str] = []
    for selector in (
        "meta[property='og:description']",
        "meta[name='description']",
        "meta[name='twitter:description']",
    ):
        element = soup.select_one(selector)
        if element and element.get("content"):
            descriptions.append(str(element["content"]))
    return descriptions


def _extract_description_blocks(soup: BeautifulSoup) -> list[str]:
    descriptions: list[str] = []
    markers = ("description", "job-description", "job_description", "jobDescription", "details")
    for element in soup.find_all(["article", "main", "section", "div"]):
        attributes = " ".join(
            " ".join(value) if isinstance(value, list) else str(value)
            for value in element.attrs.values()
        )
        if any(marker.lower() in attributes.lower() for marker in markers):
            descriptions.append(element.get_text(" ", strip=True))
    return descriptions


def _iter_json_objects(payload: Any) -> Iterable[dict]:
    if isinstance(payload, dict):
        yield payload
        for value in payload.values():
            yield from _iter_json_objects(value)
    elif isinstance(payload, list):
        for item in payload:
            yield from _iter_json_objects(item)


def _clean_description(description: str) -> str:
    text = BeautifulSoup(description, "html.parser").get_text(" ", strip=True)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def _is_adzuna_url(url: str) -> bool:
    hostname = urlparse(url).hostname or ""
    return hostname == "adzuna.fr" or hostname.endswith(".adzuna.fr")


def _recommendation_id(job_id: str, input_skills: str) -> str:
    return hashlib.sha256(f"{job_id}||{input_skills}".encode("utf-8")).hexdigest()
