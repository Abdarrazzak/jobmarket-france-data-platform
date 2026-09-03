from api.main import _score_recommendation


def test_score_recommendation_uses_request_parameters() -> None:
    row = {
        "title": "Data Engineer",
        "company_name": "Example",
        "city": "Paris",
        "contract_type": "CDI",
        "experience_level": "junior",
        "salary_avg": 50000,
        "detected_skills": ["Python", "SQL", "Azure"],
    }

    recommendation = _score_recommendation(
        row,
        skills="Python,PySpark,Azure",
        location="Paris",
        experience_level="junior",
        contract_type="CDI",
    )

    assert recommendation["matched_skills"] == ["Azure", "Python"]
    assert recommendation["score"] == 26
    assert recommendation["score_details"] == "skills=2 | location_bonus=3 | contract_bonus=2 | experience_bonus=1"


def test_score_recommendation_maps_adzuna_contract_labels() -> None:
    row = {
        "title": "Data Analyst",
        "company_name": "Example",
        "city": "Lyon",
        "contract_type": "PERMANENT",
        "experience_level": "not_specified",
        "salary_avg": None,
        "detected_skills": [],
    }

    recommendation = _score_recommendation(
        row,
        skills="SQL",
        location="Paris",
        experience_level="junior",
        contract_type="CDI",
    )

    assert recommendation["contract_type"] == "CDI"
    assert recommendation["score"] == 2
