from api.main import build_prometheus_metrics


def test_build_prometheus_metrics_exports_core_counters() -> None:
    text = build_prometheus_metrics(
        {
            "database_status": "available",
            "warehouse_counts": {
                "fact_jobs": 797,
                "dim_company": 397,
                "dim_location": 141,
                "fact_skills": 334,
                "job_recommendations": 10,
                "ml_salary_feature_rows": 797,
                "ml_salary_training_rows": 250,
                "ml_salary_inference_rows": 547,
            },
            "checks": {
                "sample_source_rows": 0,
                "example_url_rows": 0,
                "non_france_location_rows": 0,
            },
            "description_enrichment": [
                {"status": "updated", "row_count": 11},
                {"status": "failed", "row_count": 31},
            ],
            "status": "PASS",
        }
    )

    assert "jobmarket_api_up 1" in text
    assert "jobmarket_database_up 1" in text
    assert "jobmarket_postgres_up 1" in text
    assert "jobmarket_quality_status 1" in text
    assert "jobmarket_jobs_total 797" in text
    assert "jobmarket_companies_total 397" in text
    assert "jobmarket_skills_total 334" in text
    assert "jobmarket_quality_blocking_issues_total 0" in text
    assert "jobmarket_fact_jobs_total 797" in text
    assert "jobmarket_ml_salary_training_rows 250" in text
    assert 'jobmarket_description_enrichment_total{status="updated"} 11' in text


def test_build_prometheus_metrics_marks_database_down() -> None:
    text = build_prometheus_metrics({"database_status": "unavailable", "status": "FAIL"})

    assert "jobmarket_database_up 0" in text
    assert "jobmarket_postgres_up 0" in text
    assert "jobmarket_quality_status 0" in text
