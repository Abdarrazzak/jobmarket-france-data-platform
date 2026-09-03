import json

import pytest

from jobmarket.monitoring.pipeline_runs import execute_with_monitoring, read_latest_pipeline_runs


def test_execute_with_monitoring_writes_success_log(tmp_path) -> None:
    log_path = tmp_path / "pipeline_runs.jsonl"

    results = execute_with_monitoring(["a", "b"], lambda step: {"step": step}, log_path)

    runs = read_latest_pipeline_runs(log_path)
    assert results == {"a": {"step": "a"}, "b": {"step": "b"}}
    assert runs[0]["status"] == "SUCCESS"
    assert [step["status"] for step in runs[0]["steps"]] == ["SUCCESS", "SUCCESS"]


def test_execute_with_monitoring_writes_failed_log(tmp_path) -> None:
    log_path = tmp_path / "pipeline_runs.jsonl"

    def runner(step: str):
        if step == "bad":
            raise RuntimeError("boom")
        return "ok"

    with pytest.raises(RuntimeError):
        execute_with_monitoring(["ok", "bad"], runner, log_path)

    run = json.loads(log_path.read_text(encoding="utf-8").strip())
    assert run["status"] == "FAILED"
    assert run["steps"][-1]["step"] == "bad"
    assert run["steps"][-1]["status"] == "FAILED"
