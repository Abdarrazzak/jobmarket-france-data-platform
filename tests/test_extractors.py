from jobmarket.extract.extraction_plan import DEFAULT_EXTRACTION_PLAN


def test_default_extraction_plan_targets_france() -> None:
    assert DEFAULT_EXTRACTION_PLAN["adzuna"]["country"] == "fr"
    assert DEFAULT_EXTRACTION_PLAN["adzuna"]["locations"] == ["France"]


def test_default_extraction_plan_has_no_sample_source() -> None:
    assert "sample" not in str(DEFAULT_EXTRACTION_PLAN).lower()
