from __future__ import annotations

from pathlib import Path

from pyspark.sql import SparkSession
from pyspark.sql import functions as F

from jobmarket.io import read_parquet_as_spark, write_parquet


def silver_to_gold(spark: SparkSession, silver_path: Path, gold_path: Path) -> dict[str, int]:
    jobs = read_parquet_as_spark(spark, silver_path / "jobs")
    gold_path.mkdir(parents=True, exist_ok=True)

    enriched_jobs = (
        jobs.withColumn("company_id", F.sha2(F.lower(F.coalesce(F.col("company"), F.lit("unknown"))), 256))
        .withColumn(
            "location_id",
            F.sha2(
                F.lower(
                    F.concat_ws(
                        "||",
                        F.coalesce(F.col("city"), F.lit("unknown")),
                        F.coalesce(F.col("region"), F.lit("unknown")),
                        F.coalesce(F.col("country"), F.lit("unknown")),
                    )
                ),
                256,
            ),
        )
        .withColumn(
            "salary_avg",
            F.when(F.col("salary_min").isNotNull() & F.col("salary_max").isNotNull(), (F.col("salary_min") + F.col("salary_max")) / 2)
            .otherwise(F.coalesce(F.col("salary_min"), F.col("salary_max"))),
        )
        .withColumn(
            "experience_level",
            F.when(F.lower(F.concat_ws(" ", F.col("title"), F.col("description"))).rlike("senior|lead|principal"), "senior")
            .when(F.lower(F.concat_ws(" ", F.col("title"), F.col("description"))).rlike("junior|apprentice|intern"), "junior")
            .otherwise("not_specified"),
        )
    )

    fact_jobs = enriched_jobs.select(
        "job_id",
        "source",
        "title",
        "company_id",
        "location_id",
        "contract_type",
        "experience_level",
        "salary_min",
        "salary_max",
        "salary_avg",
        "description",
        "publication_date",
        "source_url",
        "load_date",
        "ingestion_timestamp",
    )

    dim_company = enriched_jobs.select(
        "company_id",
        F.col("company").alias("company_name"),
        "source",
        "load_date",
        "ingestion_timestamp",
    ).dropDuplicates(["company_id"])

    dim_location = enriched_jobs.select(
        "location_id",
        "city",
        "region",
        "country",
        "source",
        "load_date",
        "ingestion_timestamp",
    ).dropDuplicates(["location_id"])

    statistics = enriched_jobs.agg(
        F.countDistinct("job_id").alias("job_count"),
        F.countDistinct("company_id").alias("company_count"),
        F.round(F.avg("salary_avg"), 2).alias("average_salary"),
    ).withColumn("load_date", F.current_date())

    write_parquet(fact_jobs, gold_path / "fact_jobs", partition_by="load_date")
    write_parquet(dim_company, gold_path / "dim_company")
    write_parquet(dim_location, gold_path / "dim_location")
    write_parquet(statistics, gold_path / "statistics")

    return {
        "fact_jobs": fact_jobs.count(),
        "dim_company": dim_company.count(),
        "dim_location": dim_location.count(),
    }
