from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_PATH = PROJECT_ROOT / "src"
if str(SRC_PATH) not in sys.path:
    sys.path.insert(0, str(SRC_PATH))

from jobmarket.pipeline import PIPELINE_STEPS, run_all, run_step


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the JobMarket data pipeline.")
    parser.add_argument("--step", choices=PIPELINE_STEPS + ["all"], default="all")
    parser.add_argument("--skip-postgres", action="store_true", help="Run the local demo without loading PostgreSQL.")
    args = parser.parse_args()

    if args.step == "all":
        result = run_all(skip_postgres=args.skip_postgres)
    else:
        result = {args.step: run_step(args.step)}

    print(json.dumps(_stringify(result), indent=2))


def _stringify(value: Any):
    if isinstance(value, Path):
        payload: dict[str, Any] = {"path": str(value)}
        row_count = _count_rows_if_supported(value)
        if row_count is not None:
            payload["row_count"] = row_count
        return payload
    if value is None or isinstance(value, str | int | float | bool):
        return value
    if isinstance(value, dict):
        return {key: _stringify(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_stringify(item) for item in value]
    return str(value)


def _count_rows_if_supported(path: Path) -> int | None:
    if not path.is_file() or path.suffix.lower() not in {".jsonl", ".json"}:
        return None
    with path.open("r", encoding="utf-8") as file:
        return sum(1 for line in file if line.strip())


if __name__ == "__main__":
    main()
