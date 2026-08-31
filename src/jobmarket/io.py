from __future__ import annotations

import json
import os
import shutil
from pathlib import Path

import pandas as pd
from pyspark.sql import DataFrame, SparkSession


def read_json_as_spark(spark: SparkSession, path: Path) -> DataFrame:
    if not _use_python_local_io():
        return spark.read.option("recursiveFileLookup", "true").json(str(path))

    files = [str(file_path.resolve()) for file_path in sorted(Path(path).rglob("jobs.jsonl"))]
    if not files:
        raise FileNotFoundError(f"No Bronze JSON records found under {path}")
    return spark.read.json(files)


def read_parquet_as_spark(spark: SparkSession, path: Path) -> DataFrame:
    if not _use_python_local_io():
        return spark.read.parquet(str(path))

    files = [str(file_path.resolve()) for file_path in sorted(Path(path).rglob("*.parquet"))]
    if not files:
        raise FileNotFoundError(f"No Parquet files found under {path}")
    return spark.read.parquet(*files)


def write_parquet(dataframe: DataFrame, path: Path, partition_by: str | None = None) -> None:
    if not _use_python_local_io():
        writer = dataframe.write.mode("overwrite")
        if partition_by:
            writer = writer.partitionBy(partition_by)
        writer.parquet(str(path))
        return

    if path.exists():
        shutil.rmtree(path)
    path.mkdir(parents=True, exist_ok=True)

    rows = [row.asDict(recursive=True) for row in dataframe.collect()]
    pandas_frame = pd.DataFrame(rows, columns=dataframe.columns)
    pandas_frame.to_parquet(path / "part-00000.parquet", index=False)


def _use_python_local_io() -> bool:
    return os.name == "nt" and os.getenv("SPARK_FORCE_HADOOP_IO") != "1"
