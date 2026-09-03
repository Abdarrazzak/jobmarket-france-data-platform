from jobmarket.load.postgres import DDL_STATEMENTS, ML_VIEW_STATEMENTS


def test_ml_schema_is_created() -> None:
    assert "CREATE SCHEMA IF NOT EXISTS ml" in DDL_STATEMENTS


def test_salary_prediction_views_are_defined() -> None:
    sql = "\n".join(ML_VIEW_STATEMENTS)

    assert "ml.salary_prediction_features" in sql
    assert "ml.salary_training_dataset" in sql
    assert "ml.salary_inference_dataset" in sql
    assert "experience_level_encoded" in sql
    assert "salary_quality_flag" in sql
    assert "has_pyspark" in sql
    assert "target_salary_avg" in sql
