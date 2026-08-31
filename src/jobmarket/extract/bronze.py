from __future__ import annotations

import json
from datetime import UTC, date, datetime
from pathlib import Path
from uuid import uuid4


def write_bronze_records(records: list[dict], bronze_root: Path, source: str, run_id: str | None = None) -> Path:
    load_date = date.today().isoformat()
    ingestion_timestamp = datetime.now(UTC).isoformat()
    run_id = run_id or datetime.now(UTC).strftime("%Y%m%dT%H%M%S") + "-" + uuid4().hex[:8]

    output_dir = bronze_root / f"source={source}" / f"load_date={load_date}" / f"run_id={run_id}"
    output_dir.mkdir(parents=True, exist_ok=True)
    output_file = output_dir / "jobs.jsonl"

    with output_file.open("w", encoding="utf-8") as file:
        for record in records:
            enriched = {
                **record,
                "source": record.get("source") or source,
                "load_date": load_date,
                "ingestion_timestamp": ingestion_timestamp,
            }
            file.write(json.dumps(enriched, ensure_ascii=True) + "\n")

    return output_file


def write_bronze_manifest(bronze_root: Path) -> Path:
    bronze_root.mkdir(parents=True, exist_ok=True)
    manifest_path = bronze_root / "manifest.json"
    payload = {
        "bronze_path": str(bronze_root),
        "generated_at": datetime.now(UTC).isoformat(),
        "principle": "Bronze stores raw JSON records and is append-only.",
    }
    manifest_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return manifest_path

