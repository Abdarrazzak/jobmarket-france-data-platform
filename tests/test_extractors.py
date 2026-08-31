from jobmarket.extract.sample_data import get_sample_jobs


def test_sample_jobs_have_required_fields() -> None:
    required_fields = {"source", "source_job_id", "title", "company", "description", "url"}

    for job in get_sample_jobs():
        assert required_fields <= set(job)


def test_sample_jobs_cover_three_source_types() -> None:
    sources = {job["source"] for job in get_sample_jobs()}

    assert any(source.startswith("adzuna") for source in sources)
    assert any(source.startswith("muse") for source in sources)
    assert any(source.startswith("scraping") for source in sources)

