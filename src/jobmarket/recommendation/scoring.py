from __future__ import annotations

import json
from pathlib import Path

from pyspark.sql import SparkSession
from pyspark.sql import functions as F

from jobmarket.io import read_parquet_as_spark, write_parquet


def load_user_profile(profile_path: Path) -> dict:
    if profile_path.exists():
        return json.loads(profile_path.read_text(encoding="utf-8"))
    return {
        "skills": ["Python", "SQL", "PySpark"],
        "location": "Paris",
        "experience_level": "junior",
        "contract_type": "CDI",
        "top_n": 10,
    }


def build_recommendations(spark: SparkSession, gold_path: Path, profile_path: Path) -> int:
    profile = load_user_profile(profile_path)
    fact_jobs = read_parquet_as_spark(spark, gold_path / "fact_jobs")
    fact_skills = read_parquet_as_spark(spark, gold_path / "fact_skills")
    dim_company = read_parquet_as_spark(spark, gold_path / "dim_company")
    dim_location = read_parquet_as_spark(spark, gold_path / "dim_location")

    requested_skills = [skill.lower() for skill in profile.get("skills", [])]
    requested_location = str(profile.get("location", "")).lower()
    requested_contract = str(profile.get("contract_type", "")).upper()
    requested_experience = str(profile.get("experience_level", "")).lower()
    top_n = int(profile.get("top_n", 10))

    matched_skills = (
        fact_skills.where(F.lower(F.col("skill_name")).isin(requested_skills))
        .groupBy("job_id")
        .agg(F.countDistinct("skill_name").alias("matched_skill_count"), F.collect_set("skill_name").alias("matched_skills"))
    )

    jobs = (
        fact_jobs.join(dim_company.select("company_id", "company_name"), "company_id", "left")
        .join(dim_location.select("location_id", "city", "region", "country"), "location_id", "left")
        .join(matched_skills, "job_id", "left")
        .fillna({"matched_skill_count": 0})
    )

    recommendations = (
        jobs.withColumn("location_bonus", F.when(F.lower(F.col("city")).contains(requested_location), F.lit(3)).otherwise(F.lit(0)))
        .withColumn("contract_bonus", F.when(F.col("contract_type") == requested_contract, F.lit(2)).otherwise(F.lit(0)))
        .withColumn("experience_bonus", F.when(F.col("experience_level") == requested_experience, F.lit(1)).otherwise(F.lit(0)))
        .withColumn("score", F.col("matched_skill_count") * F.lit(10) + F.col("location_bonus") + F.col("contract_bonus") + F.col("experience_bonus"))
        .withColumn("input_skills", F.lit(", ".join(profile.get("skills", []))))
        .withColumn(
            "score_details",
            F.concat_ws(
                " | ",
                F.concat(F.lit("skills="), F.col("matched_skill_count")),
                F.concat(F.lit("location_bonus="), F.col("location_bonus")),
                F.concat(F.lit("contract_bonus="), F.col("contract_bonus")),
                F.concat(F.lit("experience_bonus="), F.col("experience_bonus")),
            ),
        )
        .orderBy(F.desc("score"), F.desc("salary_avg"))
        .limit(top_n)
        .select(
            F.sha2(F.concat_ws("||", F.col("job_id"), F.col("input_skills")), 256).alias("recommendation_id"),
            "job_id",
            "title",
            "company_name",
            "city",
            "contract_type",
            "experience_level",
            "salary_avg",
            "input_skills",
            "score",
            "score_details",
            "load_date",
            "ingestion_timestamp",
        )
    )

    write_parquet(recommendations, gold_path / "job_recommendations")
    return recommendations.count()
