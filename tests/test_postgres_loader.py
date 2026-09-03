from jobmarket.load.postgres import build_upsert_sql


def test_build_upsert_sql_updates_non_key_columns() -> None:
    sql = build_upsert_sql(
        "analytics.fact_jobs",
        ["job_id", "title", "source"],
        ["job_id"],
    )

    assert "ON CONFLICT (job_id) DO UPDATE" in sql
    assert "title = EXCLUDED.title" in sql
    assert "source = EXCLUDED.source" in sql
    assert "job_id = EXCLUDED.job_id" not in sql


def test_build_upsert_sql_can_do_nothing_when_only_keys_are_present() -> None:
    sql = build_upsert_sql(
        "analytics.fact_skills",
        ["job_id", "skill_name"],
        ["job_id", "skill_name"],
    )

    assert sql.endswith("ON CONFLICT (job_id, skill_name) DO NOTHING")
