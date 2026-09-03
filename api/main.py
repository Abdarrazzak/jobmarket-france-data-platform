from __future__ import annotations

import os
import smtplib
import sys
from email.message import EmailMessage
from pathlib import Path
from typing import Any

import psycopg2
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Query, Response
from pydantic import BaseModel, Field
from psycopg2.extras import RealDictCursor


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_PATH = PROJECT_ROOT / "src"
if str(SRC_PATH) not in sys.path:
    sys.path.insert(0, str(SRC_PATH))
load_dotenv(PROJECT_ROOT / ".env")

app = FastAPI(
    title="JobMarket Data Platform API",
    description="REST API exposing job market analytics, skills and recommendations.",
    version="0.1.0",
)


class EmailAlertRequest(BaseModel):
    recipient_email: str = Field(..., min_length=3)
    recipient_name: str = ""
    query: str = ""
    city: str = ""
    skills: str = ""
    contract_type: str = ""
    experience_level: str = ""
    source: str = ""
    min_salary: float | None = Field(default=None, ge=0)
    limit: int = Field(default=15, ge=1, le=50)

NON_CITY_LABELS = {
    "bourgogne-franche-comté",
    "deux-sèvres",
    "finistère",
    "gironde",
    "morbihan",
    "orne",
    "provence-alpes-côte d'azur",
    "puy-de-dôme",
}


def _sql_quote(value: str) -> str:
    return "'" + value.replace("'", "''") + "'"


NON_CITY_LABELS_SQL = ", ".join(_sql_quote(value) for value in sorted(NON_CITY_LABELS))


def _city_filter_sql(alias: str) -> str:
    return f"""
        {alias}.country = 'France'
        AND {alias}.city IS NOT NULL
        AND TRIM({alias}.city) <> ''
        AND LOWER({alias}.city) NOT IN ('france', 'remote', 'teletravail', 'non renseignee', {NON_CITY_LABELS_SQL})
        AND POSITION('arrondissement' IN LOWER({alias}.city)) = 0
        AND POSITION('canton' IN LOWER({alias}.city)) = 0
    """


def _connection_params() -> dict[str, Any]:
    return {
        "host": os.getenv("POSTGRES_HOST", "localhost"),
        "port": int(os.getenv("POSTGRES_PORT", "5432")),
        "dbname": os.getenv("POSTGRES_DB", "jobmarket"),
        "user": os.getenv("POSTGRES_USER", ""),
        "password": os.getenv("POSTGRES_PASSWORD", ""),
    }


def _fetch_all(sql: str, params: tuple = ()) -> list[dict] | None:
    try:
        with psycopg2.connect(**_connection_params()) as connection:
            with connection.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute(sql, params)
                return [dict(row) for row in cursor.fetchall()]
    except Exception:
        return None


def _fetch_one(sql: str, params: tuple = ()) -> dict | None:
    rows = _fetch_all(sql, params)
    if not rows:
        return None
    return rows[0]


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "service": "jobmarket-api"}


@app.get("/jobs")
def get_jobs(limit: int = Query(50, ge=1, le=500)) -> list[dict]:
    rows = _fetch_all(
        f"""
        SELECT
            title,
            company_name,
            city,
            region,
            country,
            contract_type,
            experience_level,
            salary_min,
            salary_max,
            salary_avg,
            publication_date,
            source,
            source_url
        FROM serving.jobs_public jp
        WHERE {_city_filter_sql("jp")}
        ORDER BY jp.publication_date DESC NULLS LAST
        LIMIT %s
        """,
        (limit,),
    )
    return [_normalize_public_job(row) for row in rows] if rows is not None else []


@app.get("/search/options")
def get_search_options() -> dict:
    cities = _fetch_all(
        f"""
        SELECT l.city, COUNT(j.job_id) AS job_count
        FROM analytics.fact_jobs j
        JOIN analytics.dim_location l ON j.location_id = l.location_id
        WHERE {_city_filter_sql("l")}
        GROUP BY l.city
        ORDER BY job_count DESC, l.city
        LIMIT 300
        """
    )
    skills = _fetch_all(
        """
        SELECT skill_name, COUNT(DISTINCT job_id) AS job_count
        FROM analytics.fact_skills
        GROUP BY skill_name
        ORDER BY job_count DESC, skill_name
        LIMIT 100
        """
    )
    contracts = _fetch_all(
        """
        SELECT DISTINCT contract_type
        FROM analytics.fact_jobs
        WHERE contract_type IS NOT NULL
          AND TRIM(contract_type) <> ''
        ORDER BY contract_type
        """
    )
    experience_levels = _fetch_all(
        """
        SELECT DISTINCT experience_level
        FROM analytics.fact_jobs
        WHERE experience_level IS NOT NULL
          AND TRIM(experience_level) <> ''
        ORDER BY experience_level
        """
    )
    sources = _fetch_all(
        """
        SELECT DISTINCT source
        FROM analytics.fact_jobs
        WHERE source IS NOT NULL
          AND TRIM(source) <> ''
        ORDER BY source
        """
    )

    return {
        "cities": cities or [],
        "skills": skills or [],
        "contract_types": sorted(
            {
                contract
                for row in contracts or []
                if (contract := _normalize_contract_type(row.get("contract_type")))
            }
        ),
        "experience_levels": [row["experience_level"] for row in experience_levels or []],
        "sources": [row["source"] for row in sources or []],
    }


@app.get("/jobs/search")
def search_jobs(
    query: str = Query("", description="Keyword searched in title, company and description."),
    city: str = Query("", description="City filter."),
    skills: str = Query("", description="Comma-separated skills. Matches at least one selected skill."),
    contract_type: str = Query("", description="Contract filter, for example CDI."),
    experience_level: str = Query("", description="Experience filter."),
    source: str = Query("", description="Source filter."),
    min_salary: float | None = Query(None, ge=0),
    limit: int = Query(100, ge=1, le=500),
) -> list[dict]:
    where_clauses = [_city_filter_sql("l")]
    params: list[Any] = []

    clean_query = query.strip().lower()
    if clean_query:
        like_query = f"%{clean_query}%"
        where_clauses.append(
            """
            (
                LOWER(j.title) LIKE %s
                OR LOWER(c.company_name) LIKE %s
                OR LOWER(COALESCE(j.description, '')) LIKE %s
            )
            """
        )
        params.extend([like_query, like_query, like_query])

    if city.strip():
        where_clauses.append("LOWER(l.city) LIKE %s")
        params.append(f"%{city.strip().lower()}%")

    requested_skills = _split_csv(skills)
    if requested_skills:
        where_clauses.append(
            """
            EXISTS (
                SELECT 1
                FROM analytics.fact_skills fs_filter
                WHERE fs_filter.job_id = j.job_id
                  AND LOWER(fs_filter.skill_name) = ANY(%s)
            )
            """
        )
        params.append([skill.lower() for skill in requested_skills])

    if contract_type.strip():
        where_clauses.append("UPPER(COALESCE(j.contract_type, '')) = ANY(%s)")
        params.append(_contract_filter_values(contract_type))

    if experience_level.strip():
        where_clauses.append("LOWER(j.experience_level) = %s")
        params.append(experience_level.strip().lower())

    if source.strip():
        where_clauses.append("LOWER(j.source) = %s")
        params.append(source.strip().lower())

    if min_salary is not None:
        where_clauses.append("j.salary_avg >= %s")
        params.append(min_salary)

    params.append(limit)
    rows = _fetch_all(
        f"""
        WITH job_skills AS (
            SELECT
                job_id,
                COUNT(DISTINCT skill_name) AS skill_count,
                ARRAY_AGG(DISTINCT skill_name ORDER BY skill_name) AS detected_skills
            FROM analytics.fact_skills
            GROUP BY job_id
        )
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
            j.source_url,
            COALESCE(js.skill_count, 0) AS skill_count,
            COALESCE(js.detected_skills, ARRAY[]::TEXT[]) AS detected_skills,
            LEFT(COALESCE(j.description, ''), 280) AS description_extract
        FROM analytics.fact_jobs j
        LEFT JOIN analytics.dim_company c ON j.company_id = c.company_id
        LEFT JOIN analytics.dim_location l ON j.location_id = l.location_id
        LEFT JOIN job_skills js ON j.job_id = js.job_id
        WHERE {" AND ".join(where_clauses)}
        ORDER BY j.publication_date DESC NULLS LAST, j.salary_avg DESC NULLS LAST
        LIMIT %s
        """,
        tuple(params),
    )
    if rows is None:
        return []

    results = [
        _normalize_search_result(row, clean_query, requested_skills)
        for row in rows
    ]
    results.sort(key=lambda row: (row["search_score"], row.get("publication_date") or ""), reverse=True)
    return results


@app.post("/alerts/email/preview")
def preview_email_alert(request: EmailAlertRequest) -> dict:
    _validate_email_address(request.recipient_email)
    jobs = _alert_jobs(request)
    subject, body = _build_alert_email(request, jobs)
    return {
        "configured": _smtp_configured(),
        "sent": False,
        "recipient_email": request.recipient_email,
        "job_count": len(jobs),
        "subject": subject,
        "body": body,
        "jobs": jobs[:5],
    }


@app.post("/alerts/email/send")
def send_email_alert(request: EmailAlertRequest) -> dict:
    _validate_email_address(request.recipient_email)
    jobs = _alert_jobs(request)
    subject, body = _build_alert_email(request, jobs)
    try:
        _send_email_message(request.recipient_email, subject, body)
    except RuntimeError as exc:
        return {
            "configured": False,
            "sent": False,
            "message": str(exc),
            "recipient_email": request.recipient_email,
            "job_count": len(jobs),
            "subject": subject,
            "body": body,
            "jobs": jobs[:5],
        }
    except Exception as exc:
        raise HTTPException(
            status_code=502,
            detail="Email send failed. Check SMTP settings and credentials.",
        ) from exc

    return {
        "configured": True,
        "sent": True,
        "message": "Email alert sent.",
        "recipient_email": request.recipient_email,
        "job_count": len(jobs),
        "subject": subject,
        "body": body,
        "jobs": jobs[:5],
    }


@app.get("/sources")
def get_sources() -> list[dict]:
    rows = _fetch_all(
        """
        SELECT
            source,
            COUNT(*) AS job_count,
            MIN(publication_date) AS first_publication_date,
            MAX(publication_date) AS latest_publication_date,
            MAX(ingestion_timestamp) AS latest_ingestion_timestamp
        FROM analytics.fact_jobs
        GROUP BY source
        ORDER BY job_count DESC, source
        """
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
            j.title,
            c.company_name,
            l.city,
            j.contract_type,
            j.experience_level,
            j.salary_avg,
            j.source,
            j.source_url,
            COALESCE(
                ARRAY_AGG(DISTINCT fs.skill_name) FILTER (WHERE fs.skill_name IS NOT NULL),
                ARRAY[]::TEXT[]
            ) AS detected_skills
        FROM analytics.fact_jobs j
        LEFT JOIN analytics.dim_company c ON j.company_id = c.company_id
        LEFT JOIN analytics.dim_location l ON j.location_id = l.location_id
        LEFT JOIN analytics.fact_skills fs ON j.job_id = fs.job_id
        WHERE l.country = 'France'
        GROUP BY
            j.job_id,
            j.title,
            c.company_name,
            l.city,
            j.contract_type,
            j.experience_level,
            j.salary_avg,
            j.source,
            j.source_url
        """,
    )
    if rows is None:
        return []

    recommendations = [
        _score_recommendation(row, skills, location, experience_level, contract_type)
        for row in rows
    ]
    recommendations.sort(key=lambda row: (row["score"], row.get("salary_avg") or 0), reverse=True)
    return recommendations[:limit]


@app.get("/statistics")
def get_statistics() -> dict:
    job_count = _fetch_all("SELECT COUNT(*) AS value FROM analytics.fact_jobs")
    company_count = _fetch_all("SELECT COUNT(*) AS value FROM analytics.dim_company")
    salary_summary = _fetch_one(
        """
        SELECT
            COUNT(*) AS salary_job_count,
            ROUND(AVG(salary_avg)::numeric, 2) AS average_salary,
            ROUND(PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY salary_avg)::numeric, 2) AS median_salary,
            ROUND(MIN(salary_avg)::numeric, 2) AS min_salary,
            ROUND(MAX(salary_avg)::numeric, 2) AS max_salary
        FROM analytics.fact_jobs
        WHERE salary_avg IS NOT NULL
        """
    )
    top_cities = _fetch_all(
        f"""
        SELECT
            l.city,
            MAX(l.region) AS region,
            COUNT(j.job_id) AS job_count
        FROM analytics.fact_jobs j
        JOIN analytics.dim_location l ON j.location_id = l.location_id
        WHERE {_city_filter_sql("l")}
        GROUP BY l.city
        ORDER BY job_count DESC, l.city
        LIMIT 10
        """
    )
    top_regions = _fetch_all(
        f"""
        SELECT
            l.region,
            COUNT(j.job_id) AS job_count
        FROM analytics.fact_jobs j
        JOIN analytics.dim_location l ON j.location_id = l.location_id
        WHERE {_city_filter_sql("l")}
          AND l.region IS NOT NULL
          AND TRIM(l.region) <> ''
        GROUP BY l.region
        ORDER BY job_count DESC, l.region
        LIMIT 10
        """
    )
    top_skills = _fetch_all(
        """
        SELECT skill_name, job_count
        FROM serving.skill_demand
        ORDER BY job_count DESC
        LIMIT 10
        """
    )
    top_companies = _fetch_all(
        """
        SELECT
            c.company_name,
            COUNT(j.job_id) AS job_count
        FROM analytics.dim_company c
        LEFT JOIN analytics.fact_jobs j ON c.company_id = j.company_id
        GROUP BY c.company_id, c.company_name
        ORDER BY job_count DESC, c.company_name
        LIMIT 10
        """
    )
    contract_distribution = _fetch_all(
        """
        SELECT
            COALESCE(NULLIF(contract_type, ''), 'NON_RENSEIGNE') AS contract_type,
            COUNT(*) AS job_count
        FROM analytics.fact_jobs
        GROUP BY COALESCE(NULLIF(contract_type, ''), 'NON_RENSEIGNE')
        ORDER BY job_count DESC
        """
    )
    source_distribution = _fetch_all(
        """
        SELECT source, COUNT(*) AS job_count
        FROM analytics.fact_jobs
        GROUP BY source
        ORDER BY job_count DESC, source
        """
    )
    salary_buckets = _fetch_all(
        """
        SELECT
            salary_bucket,
            COUNT(*) AS job_count
        FROM (
            SELECT
                CASE
                    WHEN salary_avg < 30000 THEN '< 30k'
                    WHEN salary_avg < 40000 THEN '30k - 40k'
                    WHEN salary_avg < 50000 THEN '40k - 50k'
                    WHEN salary_avg < 60000 THEN '50k - 60k'
                    WHEN salary_avg < 80000 THEN '60k - 80k'
                    ELSE '80k+'
                END AS salary_bucket,
                CASE
                    WHEN salary_avg < 30000 THEN 1
                    WHEN salary_avg < 40000 THEN 2
                    WHEN salary_avg < 50000 THEN 3
                    WHEN salary_avg < 60000 THEN 4
                    WHEN salary_avg < 80000 THEN 5
                    ELSE 6
                END AS sort_order
            FROM analytics.fact_jobs
            WHERE salary_avg IS NOT NULL
        ) buckets
        GROUP BY salary_bucket, sort_order
        ORDER BY sort_order
        """
    )
    salary_by_contract = _fetch_all(
        """
        SELECT
            COALESCE(NULLIF(contract_type, ''), 'NON_RENSEIGNE') AS contract_type,
            COUNT(*) AS job_count,
            ROUND(AVG(salary_avg)::numeric, 2) AS average_salary
        FROM analytics.fact_jobs
        WHERE salary_avg IS NOT NULL
        GROUP BY COALESCE(NULLIF(contract_type, ''), 'NON_RENSEIGNE')
        ORDER BY average_salary DESC NULLS LAST
        LIMIT 8
        """
    )
    publication_trend = _fetch_all(
        """
        SELECT
            publication_date::date AS publication_day,
            COUNT(*) AS job_count
        FROM analytics.fact_jobs
        WHERE publication_date IS NOT NULL
        GROUP BY publication_date::date
        ORDER BY publication_day
        """
    )

    if job_count is not None:
        return {
            "job_count": job_count[0]["value"],
            "company_count": company_count[0]["value"] if company_count else 0,
            "average_salary": salary_summary.get("average_salary") if salary_summary else None,
            "salary_summary": salary_summary or {},
            "top_cities": top_cities or [],
            "top_regions": top_regions or [],
            "top_skills": top_skills or [],
            "top_companies": top_companies or [],
            "contract_distribution": _normalize_contract_distribution(contract_distribution or []),
            "source_distribution": source_distribution or [],
            "salary_buckets": salary_buckets or [],
            "salary_by_contract": _normalize_contract_salary_rows(salary_by_contract or []),
            "publication_trend": publication_trend or [],
        }
    return {
        "job_count": 0,
        "company_count": 0,
        "average_salary": None,
        "salary_summary": {},
        "top_cities": [],
        "top_regions": [],
        "top_skills": [],
        "top_companies": [],
        "contract_distribution": [],
        "source_distribution": [],
        "salary_buckets": [],
        "salary_by_contract": [],
        "publication_trend": [],
    }


@app.get("/ml/salary/features")
def get_salary_prediction_features(limit: int = Query(50, ge=1, le=500)) -> list[dict]:
    rows = _fetch_all(
        """
        SELECT
            title,
            company_name,
            city,
            region,
            contract_type,
            experience_level,
            experience_level_encoded,
            target_salary_avg,
            has_salary_target,
            salary_quality_flag,
            skill_count,
            detected_skills,
            has_python,
            has_sql,
            has_pyspark,
            has_spark,
            has_airflow,
            has_dbt,
            has_databricks,
            has_snowflake,
            has_azure,
            has_aws,
            has_gcp,
            has_power_bi,
            has_tableau,
            has_docker,
            has_kubernetes,
            has_fastapi,
            description_length,
            publication_year,
            publication_month,
            source
        FROM ml.salary_prediction_features
        ORDER BY has_salary_target DESC, publication_date DESC NULLS LAST
        LIMIT %s
        """,
        (limit,),
    )
    return [_normalize_ml_feature_row(row) for row in rows] if rows is not None else []


@app.get("/ml/salary/training")
def get_salary_training_dataset(limit: int = Query(50, ge=1, le=500)) -> list[dict]:
    rows = _fetch_all(
        """
        SELECT *
        FROM ml.salary_training_dataset
        ORDER BY publication_date DESC NULLS LAST
        LIMIT %s
        """,
        (limit,),
    )
    return [_normalize_ml_feature_row(row) for row in rows] if rows is not None else []


@app.get("/ml/salary/metadata")
def get_salary_prediction_metadata() -> dict:
    metadata = _fetch_one("SELECT * FROM ml.salary_prediction_metadata")
    return metadata or {
        "feature_rows": 0,
        "training_rows": 0,
        "inference_rows": 0,
        "avg_training_salary": None,
        "min_training_salary": None,
        "max_training_salary": None,
    }


def _score_recommendation(
    row: dict,
    skills: str,
    location: str,
    experience_level: str,
    contract_type: str,
) -> dict:
    row = dict(row)
    requested_skills = {
        skill.strip().lower()
        for skill in skills.split(",")
        if skill.strip()
    }
    row["contract_type"] = _normalize_contract_type(row.get("contract_type"))
    detected_skills = row.pop("detected_skills") or []
    matched_skills = sorted(
        skill
        for skill in detected_skills
        if str(skill).lower() in requested_skills
    )
    location_bonus = 3 if location and location.lower() in str(row.get("city") or "").lower() else 0
    contract_bonus = 2 if row.get("contract_type") == _normalize_contract_type(contract_type) else 0
    experience_bonus = (
        1
        if str(row.get("experience_level") or "").lower() == experience_level.lower()
        else 0
    )
    score = len(matched_skills) * 10 + location_bonus + contract_bonus + experience_bonus

    return {
        **row,
        "input_skills": ", ".join(skill.strip() for skill in skills.split(",") if skill.strip()),
        "matched_skills": matched_skills,
        "score": score,
        "score_details": (
            f"skills={len(matched_skills)} | "
            f"location_bonus={location_bonus} | "
            f"contract_bonus={contract_bonus} | "
            f"experience_bonus={experience_bonus}"
        ),
    }


def _normalize_public_job(row: dict) -> dict:
    row = dict(row)
    row["contract_type"] = _normalize_contract_type(row.get("contract_type"))
    return row


def _normalize_ml_feature_row(row: dict) -> dict:
    row = dict(row)
    row.pop("job_id", None)
    row["contract_type"] = _normalize_contract_type(row.get("contract_type"))
    return row


def _normalize_search_result(row: dict, query: str, requested_skills: list[str]) -> dict:
    row = dict(row)
    row["contract_type"] = _normalize_contract_type(row.get("contract_type"))
    detected_skills = row.get("detected_skills") or []
    requested_skill_set = {skill.lower() for skill in requested_skills}
    matched_skills = sorted(
        skill
        for skill in detected_skills
        if str(skill).lower() in requested_skill_set
    )

    title = str(row.get("title") or "").lower()
    company = str(row.get("company_name") or "").lower()
    description = str(row.get("description_extract") or "").lower()
    query_bonus = 0
    if query:
        query_bonus += 5 if query in title else 0
        query_bonus += 2 if query in company else 0
        query_bonus += 1 if query in description else 0

    salary_bonus = 1 if row.get("salary_avg") is not None else 0
    row["matched_skills"] = matched_skills
    row["search_score"] = len(matched_skills) * 10 + query_bonus + salary_bonus
    return row


def _normalize_contract_type(value: Any) -> str | None:
    if value is None:
        return None
    normalized = str(value).strip().upper().replace("-", "_").replace(" ", "_")
    if not normalized or normalized in {"NONE", "NAN", "NULL", "NON_RENSEIGNE", "NOT_SPECIFIED"}:
        return "Non renseigne"
    mapping = {
        "PERMANENT": "CDI",
        "FULL_TIME": "TEMPS_PLEIN",
        "PART_TIME": "TEMPS_PARTIEL",
        "CONTRACT": "CDD",
        "TEMPORARY": "CDD",
        "INTERNSHIP": "STAGE",
        "APPRENTICESHIP": "ALTERNANCE",
    }
    return mapping.get(normalized, normalized)


def _normalize_contract_distribution(rows: list[dict]) -> list[dict]:
    counts: dict[str, int] = {}
    for row in rows:
        label = _normalize_contract_type(row.get("contract_type")) or "Non renseigne"
        counts[label] = counts.get(label, 0) + int(row.get("job_count") or 0)
    return [
        {"contract_type": label, "job_count": count}
        for label, count in sorted(counts.items(), key=lambda item: (-item[1], item[0]))
    ]


def _normalize_contract_salary_rows(rows: list[dict]) -> list[dict]:
    normalized_rows = []
    for row in rows:
        normalized_rows.append(
            {
                **row,
                "contract_type": _normalize_contract_type(row.get("contract_type")) or "Non renseigne",
            }
        )
    return normalized_rows


def _contract_filter_values(value: str) -> list[str]:
    normalized = _normalize_contract_type(value)
    if normalized == "Non renseigne":
        return ["", "NON_RENSEIGNE", "NOT_SPECIFIED", "NONE", "NAN", "NULL"]
    reverse_mapping = {
        "CDI": ["CDI", "PERMANENT"],
        "CDD": ["CDD", "CONTRACT", "TEMPORARY"],
        "STAGE": ["STAGE", "INTERNSHIP"],
        "ALTERNANCE": ["ALTERNANCE", "APPRENTICESHIP"],
        "TEMPS_PLEIN": ["TEMPS_PLEIN", "FULL_TIME"],
        "TEMPS_PARTIEL": ["TEMPS_PARTIEL", "PART_TIME"],
    }
    return reverse_mapping.get(normalized or "", [str(value).strip().upper()])


def _split_csv(value: str) -> list[str]:
    return [item.strip() for item in value.split(",") if item.strip()]


def _alert_jobs(request: EmailAlertRequest) -> list[dict]:
    return search_jobs(
        query=request.query,
        city=request.city,
        skills=request.skills,
        contract_type=request.contract_type,
        experience_level=request.experience_level,
        source=request.source,
        min_salary=request.min_salary,
        limit=request.limit,
    )


def _build_alert_email(request: EmailAlertRequest, jobs: list[dict]) -> tuple[str, str]:
    location = request.city.strip() or "France"
    subject = f"Alerte JobMarket - {len(jobs)} offres data - {location}"
    greeting_name = request.recipient_name.strip()
    greeting = f"Bonjour {greeting_name}," if greeting_name else "Bonjour,"

    criteria = [
        ("Mot-cle", request.query),
        ("Ville", request.city),
        ("Competences", request.skills),
        ("Contrat", request.contract_type),
        ("Niveau", request.experience_level),
        ("Source", request.source),
        ("Salaire minimum", _format_salary(request.min_salary) if request.min_salary else ""),
    ]

    lines = [
        greeting,
        "",
        f"JobMarket a trouve {len(jobs)} offre(s) correspondant a tes criteres.",
        "",
        "Criteres de recherche:",
    ]
    lines.extend(
        f"- {label}: {value}"
        for label, value in criteria
        if value is not None and str(value).strip()
    )
    if not any(value is not None and str(value).strip() for _, value in criteria):
        lines.append("- Toutes les offres data France")

    lines.extend(["", "Top offres:"])
    if not jobs:
        lines.append("- Aucune offre trouvee pour le moment.")
    for index, job in enumerate(jobs[: request.limit], start=1):
        title = job.get("title") or "Titre non renseigne"
        company = job.get("company_name") or "Entreprise non renseignee"
        city = job.get("city") or "Ville non renseignee"
        contract = job.get("contract_type") or "Contrat non renseigne"
        salary = _format_salary(job.get("salary_avg"))
        skills = ", ".join(job.get("matched_skills") or job.get("detected_skills") or [])
        score = job.get("search_score", 0)
        url = job.get("source_url") or ""

        lines.append(f"{index}. {title} - {company} - {city} - {contract} - {salary} - score {score}")
        if skills:
            lines.append(f"   Competences: {skills}")
        if url:
            lines.append(f"   Lien: {url}")

    lines.extend(
        [
            "",
            "Message genere automatiquement par le projet JobMarket Data Platform.",
        ]
    )
    return subject, "\n".join(lines)


def _format_salary(value: Any) -> str:
    if value is None or value == "":
        return "Salaire non renseigne"
    try:
        return f"{float(value):,.0f} EUR".replace(",", " ")
    except (TypeError, ValueError):
        return str(value)


def _validate_email_address(value: str) -> None:
    email = value.strip()
    if "@" not in email or "." not in email.rsplit("@", 1)[-1]:
        raise HTTPException(status_code=400, detail="Recipient email address is invalid.")


def _smtp_settings() -> dict[str, Any]:
    return {
        "host": os.getenv("SMTP_HOST", "").strip(),
        "port": int(os.getenv("SMTP_PORT", "587") or 587),
        "username": os.getenv("SMTP_USERNAME", "").strip(),
        "password": os.getenv("SMTP_PASSWORD", ""),
        "from_email": os.getenv("SMTP_FROM_EMAIL", "").strip(),
        "from_name": os.getenv("SMTP_FROM_NAME", "JobMarket Alerting").strip(),
        "use_tls": os.getenv("SMTP_USE_TLS", "true").strip().lower() not in {"0", "false", "no"},
    }


def _smtp_configured(settings: dict[str, Any] | None = None) -> bool:
    settings = settings or _smtp_settings()
    host = str(settings.get("host") or "").lower()
    has_sender = bool(settings.get("from_email"))
    if "gmail" in host:
        return bool(settings.get("host") and has_sender and settings.get("username") and settings.get("password"))
    return bool(settings.get("host") and has_sender)


def _send_email_message(recipient_email: str, subject: str, body: str) -> None:
    settings = _smtp_settings()
    if not _smtp_configured(settings):
        raise RuntimeError("SMTP is not configured. Set SMTP_HOST and SMTP_FROM_EMAIL to enable sending.")

    message = EmailMessage()
    from_label = settings["from_email"]
    if settings.get("from_name"):
        from_label = f"{settings['from_name']} <{settings['from_email']}>"
    message["From"] = from_label
    message["To"] = recipient_email.strip()
    message["Subject"] = subject
    message.set_content(body)

    with smtplib.SMTP(settings["host"], settings["port"], timeout=15) as server:
        if settings["use_tls"]:
            server.starttls()
        if settings["username"]:
            server.login(settings["username"], settings["password"])
        server.send_message(message)


@app.get("/monitoring/warehouse")
def get_warehouse_monitoring() -> dict:
    counts = _fetch_one(
        """
        SELECT
            (SELECT COUNT(*) FROM analytics.fact_jobs) AS fact_jobs,
            (SELECT COUNT(*) FROM analytics.dim_company) AS dim_company,
            (SELECT COUNT(*) FROM analytics.dim_location) AS dim_location,
            (SELECT COUNT(*) FROM analytics.fact_skills) AS fact_skills,
            (SELECT COUNT(*) FROM analytics.job_recommendations) AS job_recommendations,
            (SELECT COUNT(*) FROM ml.salary_prediction_features) AS ml_salary_feature_rows,
            (SELECT COUNT(*) FROM ml.salary_training_dataset) AS ml_salary_training_rows,
            (SELECT COUNT(*) FROM ml.salary_inference_dataset) AS ml_salary_inference_rows
        """
    )
    if counts is None:
        return {"database_status": "unavailable", "checks": {}}

    checks = _fetch_one(
        """
        SELECT
            (SELECT COUNT(*) FROM analytics.fact_jobs WHERE LOWER(source) LIKE '%%sample%%') AS sample_source_rows,
            (SELECT COUNT(*) FROM analytics.fact_jobs WHERE LOWER(COALESCE(source_url, '')) LIKE '%%example.com%%') AS example_url_rows,
            (
                SELECT COUNT(*)
                FROM analytics.dim_location
                WHERE country IS NOT NULL
                  AND TRIM(country) <> ''
                  AND LOWER(country) NOT IN ('france', 'fr')
            ) AS non_france_location_rows,
            (SELECT MAX(ingestion_timestamp) FROM analytics.fact_jobs) AS latest_ingestion_timestamp
        """
    )
    enrichment_rows = _fetch_all(
        """
        SELECT status, COUNT(*) AS row_count
        FROM analytics.description_enrichment_log
        GROUP BY status
        ORDER BY row_count DESC, status
        """
    )

    blocking_counts = [
        checks.get("sample_source_rows", 0) if checks else 0,
        checks.get("example_url_rows", 0) if checks else 0,
        checks.get("non_france_location_rows", 0) if checks else 0,
    ]
    return {
        "database_status": "available",
        "warehouse_counts": counts,
        "checks": checks or {},
        "description_enrichment": enrichment_rows or [],
        "status": "PASS" if all(count == 0 for count in blocking_counts) else "FAIL",
    }


@app.get("/metrics")
def get_prometheus_metrics() -> Response:
    monitoring = get_warehouse_monitoring()
    return Response(
        content=build_prometheus_metrics(monitoring),
        media_type="text/plain; version=0.0.4; charset=utf-8",
    )


def build_prometheus_metrics(monitoring: dict) -> str:
    database_up = 1 if monitoring.get("database_status") == "available" else 0
    quality_pass = 1 if monitoring.get("status") == "PASS" else 0
    counts = monitoring.get("warehouse_counts") or {}
    checks = monitoring.get("checks") or {}
    enrichment_rows = monitoring.get("description_enrichment") or []
    blocking_issues = sum(
        _numeric_metric_value(checks.get(key, 0))
        for key in ["sample_source_rows", "example_url_rows", "non_france_location_rows"]
    )

    lines = [
        "# HELP jobmarket_api_up JobMarket API availability.",
        "# TYPE jobmarket_api_up gauge",
        "jobmarket_api_up 1",
        "# HELP jobmarket_database_up PostgreSQL warehouse availability.",
        "# TYPE jobmarket_database_up gauge",
        f"jobmarket_database_up {database_up}",
        "# HELP jobmarket_postgres_up PostgreSQL warehouse availability alias.",
        "# TYPE jobmarket_postgres_up gauge",
        f"jobmarket_postgres_up {database_up}",
        "# HELP jobmarket_quality_status Data quality status, 1 means PASS.",
        "# TYPE jobmarket_quality_status gauge",
        f"jobmarket_quality_status {quality_pass}",
    ]

    for metric_name, value in {
        "jobmarket_jobs_total": counts.get("fact_jobs", 0),
        "jobmarket_companies_total": counts.get("dim_company", 0),
        "jobmarket_skills_total": counts.get("fact_skills", 0),
        "jobmarket_fact_jobs_total": counts.get("fact_jobs", 0),
        "jobmarket_dim_company_total": counts.get("dim_company", 0),
        "jobmarket_dim_location_total": counts.get("dim_location", 0),
        "jobmarket_fact_skills_total": counts.get("fact_skills", 0),
        "jobmarket_job_recommendations_total": counts.get("job_recommendations", 0),
        "jobmarket_ml_salary_feature_rows": counts.get("ml_salary_feature_rows", 0),
        "jobmarket_ml_salary_training_rows": counts.get("ml_salary_training_rows", 0),
        "jobmarket_ml_salary_inference_rows": counts.get("ml_salary_inference_rows", 0),
        "jobmarket_quality_blocking_issues_total": blocking_issues,
        "jobmarket_quality_sample_source_rows": checks.get("sample_source_rows", 0),
        "jobmarket_quality_example_url_rows": checks.get("example_url_rows", 0),
        "jobmarket_quality_non_france_location_rows": checks.get("non_france_location_rows", 0),
    }.items():
        lines.append(f"# TYPE {metric_name} gauge")
        lines.append(f"{metric_name} {_numeric_metric_value(value)}")

    lines.append("# HELP jobmarket_description_enrichment_total Adzuna description enrichment rows by status.")
    lines.append("# TYPE jobmarket_description_enrichment_total gauge")
    for row in enrichment_rows:
        status = _prometheus_label_value(row.get("status", "unknown"))
        value = _numeric_metric_value(row.get("row_count", 0))
        lines.append(f'jobmarket_description_enrichment_total{{status="{status}"}} {value}')

    return "\n".join(lines) + "\n"


def _numeric_metric_value(value: Any) -> int | float:
    if value is None:
        return 0
    try:
        return int(value)
    except (TypeError, ValueError):
        try:
            return float(value)
        except (TypeError, ValueError):
            return 0


def _prometheus_label_value(value: Any) -> str:
    return str(value).replace("\\", "\\\\").replace("\n", "\\n").replace('"', '\\"')
