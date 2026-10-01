from __future__ import annotations

import subprocess
from pathlib import Path

from jobmarket.security import redact_jsonable, redact_secrets


def test_env_file_is_not_tracked_by_git() -> None:
    result = subprocess.run(
        ["git", "ls-files", ".env"],
        check=True,
        capture_output=True,
        text=True,
    )

    assert result.stdout.strip() == ""


def test_redact_secrets_masks_env_values_and_query_params(monkeypatch) -> None:
    monkeypatch.setenv("ADZUNA_APP_KEY", "real_secret_value_123")
    text = "GET /x?app_key=real_secret_value_123&app_id=visible_id"

    redacted = redact_secrets(text)

    assert redacted is not None
    assert "real_secret_value_123" not in redacted
    assert "app_key=[REDACTED]" in redacted
    assert "app_id=[REDACTED]" in redacted


def test_redact_jsonable_masks_nested_strings(monkeypatch) -> None:
    monkeypatch.setenv("SMTP_PASSWORD", "smtp_secret_value")
    payload = {"error": "SMTP failed with smtp_secret_value", "items": ["safe"]}

    redacted = redact_jsonable(payload)

    assert redacted["error"] == "SMTP failed with [REDACTED]"
    assert redacted["items"] == ["safe"]


def test_env_example_uses_placeholders_for_api_keys() -> None:
    env_example = Path(".env.example").read_text(encoding="utf-8")

    assert "ADZUNA_APP_KEY=replace_me" in env_example
    assert "AZURE_STORAGE_KEY=" not in env_example


def test_publishable_files_do_not_contain_postgres_demo_password() -> None:
    publishable_files = [
        Path(".env.example"),
        Path("docker-compose.yml"),
        Path("docker-compose.monitoring.yml"),
        Path("docs/POSTGRESQL.md"),
        Path("scripts/create_postgres_database.sql"),
    ]
    forbidden_values = [
        "POSTGRES_PASSWORD=jobmarket",
        "POSTGRES_PASSWORD:-jobmarket",
        "password: jobmarket",
        "Password postgres: jobmarket",
        "WITH PASSWORD 'jobmarket'",
        "GRAFANA_ADMIN_PASSWORD=admin",
        "GRAFANA_ADMIN_PASSWORD:-admin",
    ]

    for file_path in publishable_files:
        content = file_path.read_text(encoding="utf-8")
        for forbidden_value in forbidden_values:
            assert forbidden_value not in content, f"{forbidden_value} found in {file_path}"


def test_publishable_files_do_not_contain_local_absolute_paths() -> None:
    excluded_dirs = {
        ".git",
        ".venv",
        ".pytest_cache",
        "__pycache__",
        "data",
        "logs",
        "reports",
    }
    scanned_suffixes = {
        ".env.example",
        ".json",
        ".md",
        ".py",
        ".ps1",
        ".sql",
        ".toml",
        ".txt",
        ".yaml",
        ".yml",
    }
    forbidden_fragments = [
        "C:" + "\\Users" + "\\abdho",
        "C:" + "/Users/abdho",
        "C:" + "\\Program Files" + "\\Tableau",
        "C:" + "\\hadoop",
    ]

    for file_path in Path(".").rglob("*"):
        if not file_path.is_file():
            continue
        if any(part in excluded_dirs for part in file_path.parts):
            continue
        if file_path.suffix not in scanned_suffixes and file_path.name != ".env.example":
            continue

        content = file_path.read_text(encoding="utf-8", errors="ignore")
        for forbidden_fragment in forbidden_fragments:
            assert forbidden_fragment not in content, f"{forbidden_fragment} found in {file_path}"
