from jobmarket.transform.skills import SKILL_PATTERNS


def test_required_skills_are_configured() -> None:
    expected_skills = {"Python", "SQL", "PySpark", "Azure", "Airflow", "Docker", "FastAPI"}

    assert expected_skills <= set(SKILL_PATTERNS)

