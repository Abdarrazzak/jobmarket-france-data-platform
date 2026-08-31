from __future__ import annotations

import os
import sys
from pathlib import Path

from pyspark.sql import SparkSession


def create_spark_session(app_name: str = "JobMarketDataPlatform") -> SparkSession:
    _configure_local_java()
    _configure_local_hadoop()
    os.environ.setdefault("SPARK_LOCAL_HOSTNAME", "localhost")
    os.environ.setdefault("SPARK_SCALA_VERSION", "2.13")
    python_dir = str(Path(sys.executable).parent)
    os.environ["PATH"] = python_dir + os.pathsep + os.environ.get("PATH", "")
    if os.name == "nt":
        os.environ["PYSPARK_PYTHON"] = "python"
        os.environ["PYSPARK_DRIVER_PYTHON"] = "python"
    else:
        os.environ.setdefault("PYSPARK_PYTHON", sys.executable)
        os.environ.setdefault("PYSPARK_DRIVER_PYTHON", sys.executable)

    return (
        SparkSession.builder.appName(app_name)
        .master(os.getenv("SPARK_MASTER", "local[1]"))
        .config("spark.driver.host", os.getenv("SPARK_DRIVER_HOST", "127.0.0.1"))
        .config("spark.driver.bindAddress", os.getenv("SPARK_DRIVER_BIND_ADDRESS", "127.0.0.1"))
        .config("spark.hadoop.io.native.lib.available", "false")
        .config("spark.sql.session.timeZone", "UTC")
        .config("spark.default.parallelism", os.getenv("SPARK_DEFAULT_PARALLELISM", "1"))
        .config("spark.sql.shuffle.partitions", os.getenv("SPARK_SHUFFLE_PARTITIONS", "1"))
        .config("spark.python.worker.faulthandler.enabled", "true")
        .config("spark.sql.execution.pyspark.udf.faulthandler.enabled", "true")
        .getOrCreate()
    )


def _configure_local_java() -> None:
    if os.getenv("JAVA_HOME"):
        return

    tableau_java_home = Path(r"C:\Program Files\Tableau\Tableau 2026.2\bin\jre")
    if tableau_java_home.exists():
        os.environ["JAVA_HOME"] = str(tableau_java_home)
        return

    try:
        import jdk4py

        os.environ["JAVA_HOME"] = _windows_short_path(str(jdk4py.JAVA_HOME))
    except Exception:
        return


def _configure_local_hadoop() -> None:
    if os.getenv("HADOOP_HOME"):
        hadoop_bin = Path(os.environ["HADOOP_HOME"]) / "bin"
        os.environ["PATH"] = str(hadoop_bin) + os.pathsep + os.environ.get("PATH", "")
        return

    windows_hadoop_home = Path(r"C:\hadoop")
    if windows_hadoop_home.exists():
        os.environ["HADOOP_HOME"] = str(windows_hadoop_home)
        os.environ["hadoop.home.dir"] = str(windows_hadoop_home)
        os.environ["PATH"] = str(windows_hadoop_home / "bin") + os.pathsep + os.environ.get("PATH", "")


def _windows_short_path(path: str) -> str:
    if os.name != "nt":
        return path
    try:
        import ctypes

        buffer = ctypes.create_unicode_buffer(1024)
        result = ctypes.windll.kernel32.GetShortPathNameW(str(path), buffer, len(buffer))
        return buffer.value if result else path
    except Exception:
        return path
