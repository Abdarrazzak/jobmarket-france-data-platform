from jobmarket.extract.focus_filter import filter_jobs_for_focus


def test_focus_filter_keeps_data_jobs_in_france() -> None:
    records = [
        {
            "title": "Data Engineer",
            "description": "Build PySpark pipelines.",
            "location_city": "Paris",
            "location_country": "France",
        },
        {
            "title": "Backend Developer",
            "description": "Build APIs.",
            "location_city": "Paris",
            "location_country": "France",
        },
        {
            "title": "Data Analyst",
            "description": "SQL dashboards.",
            "location_city": "Berlin",
            "location_country": "Germany",
        },
    ]

    filtered = filter_jobs_for_focus(records)

    assert filtered == [records[0]]
