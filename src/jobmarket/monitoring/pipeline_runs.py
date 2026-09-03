from __future__ import annotations

import json
import traceback
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from time import perf_counter
from typing import Any, Callable
from uuid import uuid4

from jobmarket.security import redact_jsonable, redact_secrets


@dataclass
class StepRun:
    step: str
    status: str
    started_at: str
    finished_at: str
    duration_seconds: float
    result: Any = None
    error: str | None = None


@dataclass
class PipelineRun:
    run_id: str = field(default_factory=lambda: uuid4().hex)
    status: str = "RUNNING"
    started_at: str = field(default_factory=lambda: datetime.now(UTC).isoformat())
    finished_at: str | None = None
    duration_seconds: float | None = None
    steps: list[StepRun] = field(default_factory=list)


def execute_with_monitoring(
    steps: list[str],
    runner: Callable[[str], Any],
    log_path: Path,
    skip_steps: set[str] | None = None,
) -> dict[str, Any]:
    skip_steps = skip_steps or set()
    pipeline_run = PipelineRun()
    start_time = perf_counter()
    results: dict[str, Any] = {}

    try:
        for step in steps:
            if step in skip_steps:
                results[step] = "Skipped."
                pipeline_run.steps.append(
                    StepRun(
                        step=step,
                        status="SKIPPED",
                        started_at=datetime.now(UTC).isoformat(),
                        finished_at=datetime.now(UTC).isoformat(),
                        duration_seconds=0.0,
                        result="Skipped.",
                    )
                )
                continue

            step_start_at = datetime.now(UTC).isoformat()
            step_start = perf_counter()
            try:
                result = runner(step)
                duration = round(perf_counter() - step_start, 3)
                step_run = StepRun(
                    step=step,
                    status="SUCCESS",
                    started_at=step_start_at,
                    finished_at=datetime.now(UTC).isoformat(),
                    duration_seconds=duration,
                    result=redact_jsonable(_jsonable(result)),
                )
                results[step] = result
                pipeline_run.steps.append(step_run)
            except Exception as exc:
                duration = round(perf_counter() - step_start, 3)
                pipeline_run.steps.append(
                    StepRun(
                        step=step,
                        status="FAILED",
                        started_at=step_start_at,
                        finished_at=datetime.now(UTC).isoformat(),
                        duration_seconds=duration,
                        error=redact_secrets(f"{type(exc).__name__}: {exc}"),
                        result={"traceback": redact_secrets(traceback.format_exc(limit=5))},
                    )
                )
                pipeline_run.status = "FAILED"
                raise

        pipeline_run.status = "SUCCESS"
        return results
    finally:
        pipeline_run.finished_at = datetime.now(UTC).isoformat()
        pipeline_run.duration_seconds = round(perf_counter() - start_time, 3)
        append_pipeline_run(log_path, pipeline_run)


def append_pipeline_run(log_path: Path, pipeline_run: PipelineRun) -> None:
    log_path.parent.mkdir(parents=True, exist_ok=True)
    with log_path.open("a", encoding="utf-8") as log_file:
        log_file.write(json.dumps(_pipeline_run_as_dict(pipeline_run), ensure_ascii=False) + "\n")


def read_latest_pipeline_runs(log_path: Path, limit: int = 10) -> list[dict]:
    if not log_path.exists():
        return []
    rows = []
    with log_path.open("r", encoding="utf-8") as log_file:
        for line in log_file:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows[-limit:][::-1]


def _pipeline_run_as_dict(pipeline_run: PipelineRun) -> dict:
    return {
        "run_id": pipeline_run.run_id,
        "status": pipeline_run.status,
        "started_at": pipeline_run.started_at,
        "finished_at": pipeline_run.finished_at,
        "duration_seconds": pipeline_run.duration_seconds,
        "steps": [step.__dict__ for step in pipeline_run.steps],
    }


def _jsonable(value: Any) -> Any:
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, dict):
        return {str(key): _jsonable(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_jsonable(item) for item in value]
    if isinstance(value, tuple):
        return [_jsonable(item) for item in value]
    try:
        json.dumps(value)
        return value
    except TypeError:
        return str(value)
