from __future__ import annotations

import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
ENV_FILE = PROJECT_ROOT / ".env"

SENSITIVE_ENV_NAMES = {
    "ADZUNA_APP_ID",
    "ADZUNA_APP_KEY",
    "AZURE_STORAGE_KEY",
    "POSTGRES_PASSWORD",
    "GRAFANA_ADMIN_PASSWORD",
    "SMTP_USERNAME",
    "SMTP_PASSWORD",
}

IGNORED_DIRS = {
    ".git",
    ".pytest_cache",
    ".venv",
    "__pycache__",
    "data",
    "logs",
    "reports",
}

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


def main() -> int:
    secrets = load_local_secrets(ENV_FILE)
    if not secrets:
        print("Aucun secret reel detecte dans .env, scan termine.")
        return 0

    leaks: list[tuple[str, Path]] = []
    for file_path in iter_scanned_files(PROJECT_ROOT):
        try:
            content = file_path.read_bytes()
        except OSError:
            continue

        for env_name, secret_value in secrets.items():
            if secret_value.encode("utf-8") in content:
                leaks.append((env_name, file_path.relative_to(PROJECT_ROOT)))

    if leaks:
        print("Fuite potentielle detectee. Les valeurs sont masquees :")
        for env_name, file_path in leaks:
            print(f"- {env_name} trouve dans {file_path}")
        print("Action : retirer la valeur du fichier, la remplacer par une variable d'environnement, puis regenerer le secret.")
        return 1

    print("OK : aucun secret local .env retrouve dans les fichiers du projet.")
    return 0


def load_local_secrets(env_file: Path) -> dict[str, str]:
    if not env_file.exists():
        return {}

    secrets = {}
    for line in env_file.read_text(encoding="utf-8", errors="ignore").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue

        env_name, raw_value = line.split("=", 1)
        env_name = env_name.strip()
        value = raw_value.strip().strip("'\"")

        if env_name in SENSITIVE_ENV_NAMES and looks_like_secret(value):
            secrets[env_name] = value

    return secrets


def looks_like_secret(value: str) -> bool:
    if value.lower() in PLACEHOLDER_VALUES:
        return False
    return len(value) >= 8


def iter_scanned_files(root: Path):
    for file_path in root.rglob("*"):
        if not file_path.is_file():
            continue
        if file_path.name == ".env":
            continue
        if any(part in IGNORED_DIRS for part in file_path.relative_to(root).parts):
            continue
        yield file_path


if __name__ == "__main__":
    sys.exit(main())
