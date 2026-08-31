from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Any

import psycopg2
from fastapi import FastAPI, Query
from psycopg2.extras import RealDictCursor


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_PATH = PROJECT_ROOT / "src"
if str(SRC_PATH) not in sys.path:
    sys.path.insert(0, str(SRC_PATH))

app = FastAPI(
    title="JobMarket Data Platform API",
    description="REST API exposing job market analytics, skills and recommendations.",
    version="0.1.0",
)


def _connection_params() -> dict[str, Any]:
    return {
        "host": os.getenv("POSTGRES_HOST", "localhost"),
        "port": int(os.getenv("POSTGRES_PORT", "5432")),
        "dbname": os.getenv("POSTGRES_DB", "jobmarket"),
        "user": os.getenv("POSTGRES_USER", "jobmarket"),
        "password": os.getenv("POSTGRES_PASSWORD", "jobmarket"),
    }


def _fetch_all(sql: str, params: tuple = ()) -> list[dict] | None:
    try:
        with psycopg2.connect(**_connection_params()) as connection:
            with connection.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute(sql, params)
                return [dict(row) for row in cursor.fetchall()]
    except Exception:
        return None


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "service": "jobmarket-api"}


@app.get("/jobs")
def get_jobs(limit: int = Query(50, ge=1, le=500)) -> list[dict]:
    rows = _fetch_all(
        """
        SELECT
            j.title,
            c.company_name,
            l.city,
            l.region,
            l.country,
            j.contract_type,
            j.experience_level,
            j.salary_min,
            j.salary_max,
            j.salary_avg,
            j.publication_date,
            j.source,
            j.source_url
        FROM analytics.fact_jobs j
        LEFT JOIN analytics.dim_company c ON j.company_id = c.company_id
        LEFT JOIN analytics.dim_location l ON j.location_id = l.location_id
        WHERE l.country = 'France'
          AND l.city IS NOT NULL
          AND TRIM(l.city) <> ''
          AND LOWER(l.city) NOT IN ('france', 'remote', 'teletravail', 'non renseignee')
          AND POSITION('arrondissement' IN LOWER(l.city)) = 0
        ORDER BY j.publication_date DESC NULLS LAST
        LIMIT %s
        """,
        (limit,),
    )
    return rows if rows is not None else []


@app.get("/companies")
def get_companies(limit: int = Query(50, ge=1, le=500)) -> list[dict]:
    rows = _fetch_all(
        """
        SELECT
            c.company_name,
            COUNT(j.job_id) AS job_count
        FROM analytics.dim_company c
        LEFT JOIN analytics.fact_jobs j ON c.company_id = j.company_id
        GROUP BY c.company_id, c.company_name
        ORDER BY job_count DESC, c.company_name
        LIMIT %s
        """,
        (limit,),
    )
    if rows is not None:
        return rows

    return []


@app.get("/skills")
def get_skills(limit: int = Query(30, ge=1, le=100)) -> list[dict]:
    rows = _fetch_all(
        """
        SELECT skill_name, COUNT(DISTINCT job_id) AS job_count
        FROM analytics.fact_skills
        GROUP BY skill_name
        ORDER BY job_count DESC, skill_name
        LIMIT %s
        """,
        (limit,),
    )
    if rows is not None:
        return rows

    return []


@app.get("/recommendations")
def get_recommendations(
    skills: str = Query("Python,SQL,PySpark,Azure"),
    location: str = Query("Paris"),
    experience_level: str = Query("junior"),
    contract_type: str = Query("CDI"),
    limit: int = Query(10, ge=1, le=50),
) -> list[dict]:
    rows = _fetch_all(
        """
        SELECT
            title,
            company_name,
            city,
            contract_type,
            experience_level,
            salary_avg,
            input_skills,
            score,
            score_details
        FROM analytics.job_recommendations
        ORDER BY score DESC, salary_avg DESC NULLS LAST
        LIMIT %s
        """,
        (limit,),
    )
    if rows is not None:
        return rows

    return []


@app.get("/statistics")
def get_statistics() -> dict:
    job_count = _fetch_all("SELECT COUNT(*) AS value FROM analytics.fact_jobs")
    company_count = _fetch_all("SELECT COUNT(*) AS value FROM analytics.dim_company")
    salary = _fetch_all("SELECT ROUND(AVG(salary_avg)::numeric, 2) AS value FROM analytics.fact_jobs WHERE salary_avg IS NOT NULL")
    top_cities = _fetch_all(
        """
        SELECT l.city, COUNT(j.job_id) AS job_count
        FROM analytics.fact_jobs j
        JOIN analytics.dim_location l ON j.location_id = l.location_id
        WHERE l.country = 'France'
          AND l.city IS NOT NULL
          AND TRIM(l.city) <> ''
          AND LOWER(l.city) NOT IN ('france', 'remote', 'teletravail', 'non renseignee')
          AND POSITION('arrondissement' IN LOWER(l.city)) = 0
        GROUP BY l.city
        ORDER BY job_count DESC
        LIMIT 10
        """
    )
    top_skills = _fetch_all(
        """
        SELECT skill_name, COUNT(DISTINCT job_id) AS job_count
        FROM analytics.fact_skills
        GROUP BY skill_name
        ORDER BY job_count DESC
        LIMIT 10
        """
    )

    if job_count is not None:
        return {
            "job_count": job_count[0]["value"],
            "company_count": company_count[0]["value"] if company_count else 0,
            "average_salary": salary[0]["value"] if salary and salary[0]["value"] is not None else None,
            "top_cities": top_cities or [],
            "top_skills": top_skills or [],
        }
    return {
        "job_count": 0,
        "company_count": 0,
        "average_salary": None,
        "top_cities": [],
        "top_skills": [],
    }
