from __future__ import annotations

import json
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_PATH = PROJECT_ROOT / "src"
if str(SRC_PATH) not in sys.path:
    sys.path.insert(0, str(SRC_PATH))

from jobmarket.enrich.adzuna_descriptions import backfill_adzuna_descriptions_from_postgres


def main() -> None:
    result = backfill_adzuna_descriptions_from_postgres()
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
