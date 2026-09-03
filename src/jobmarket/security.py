from __future__ import annotations

import os
import re
from typing import Any


SENSITIVE_ENV_NAMES = (
    "ADZUNA_APP_ID",
    "ADZUNA_APP_KEY",
    "AZURE_STORAGE_KEY",
    "POSTGRES_PASSWORD",
    "GRAFANA_ADMIN_PASSWORD",
    "SMTP_USERNAME",
    "SMTP_PASSWORD",
)

PLACEHOLDER_VALUES = {
    "",
    "admin",
    "change_me",
    "demo",
    "false",
    "jobmarket",
    "localhost",
    "none",
    "replace_me",
    "true",
}

SECRET_QUERY_PARAMS = (
    "app_id",
    "app_key",
    "api_key",
    "key",
    "password",
    "token",
    "secret",
)


def redact_secrets(value: Any) -> str | None:
    if value is None:
        return None

    text = str(value)
    for secret in _current_secret_values():
        text = text.replace(secret, "[REDACTED]")

    for param in SECRET_QUERY_PARAMS:
        text = re.sub(
            rf"(?i)([?&]{re.escape(param)}=)[^&\s]+",
            rf"\1[REDACTED]",
            text,
        )

    return text


def redact_jsonable(value: Any) -> Any:
    if isinstance(value, dict):
        return {key: redact_jsonable(item) for key, item in value.items()}
    if isinstance(value, list):
        return [redact_jsonable(item) for item in value]
    if isinstance(value, tuple):
        return [redact_jsonable(item) for item in value]
    if isinstance(value, str):
        return redact_secrets(value)
    return value


def _current_secret_values() -> list[str]:
    values = []
    for env_name in SENSITIVE_ENV_NAMES:
        env_value = os.getenv(env_name, "")
        if _looks_like_secret(env_value):
            values.append(env_value)
    return sorted(set(values), key=len, reverse=True)


def _looks_like_secret(value: str | None) -> bool:
    if not value:
        return False
    normalized = value.strip().strip("'\"")
    if normalized.lower() in PLACEHOLDER_VALUES:
        return False
    return len(normalized) >= 8
