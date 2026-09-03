from api.main import _contract_filter_values, _normalize_search_result, _split_csv


def test_split_csv_removes_empty_values() -> None:
    assert _split_csv("Python, SQL, , Azure") == ["Python", "SQL", "Azure"]


def test_contract_filter_values_include_adzuna_labels() -> None:
    assert _contract_filter_values("CDI") == ["CDI", "PERMANENT"]


def test_contract_filter_values_include_missing_labels() -> None:
    assert "NOT_SPECIFIED" in _contract_filter_values("Non renseigne")


def test_normalize_search_result_adds_score_and_matched_skills() -> None:
    row = {
        "title": "Data Engineer Azure",
        "company_name": "Example",
        "city": "Paris",
        "contract_type": "PERMANENT",
        "salary_avg": 50000,
        "detected_skills": ["Azure", "Python", "SQL"],
        "description_extract": "Build cloud data products.",
    }

    result = _normalize_search_result(row, "data", ["Python", "PySpark", "Azure"])

    assert result["contract_type"] == "CDI"
    assert result["matched_skills"] == ["Azure", "Python"]
    assert result["search_score"] == 27
