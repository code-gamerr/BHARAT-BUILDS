"""Load the 20 simulated fixtures into the local (or AWS) store."""

from __future__ import annotations

import json
import os
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

os.environ.setdefault("CASEPACKET_LOCAL", "1")

from shared.pipeline import ingest_listing  # noqa: E402
from shared.store import LOCAL_DIR, reset_store_cache  # noqa: E402


def main() -> None:
    fixtures_dir = ROOT / "fixtures"
    files = sorted(fixtures_dir.glob("fix-*.json"))
    if len(files) < 20:
        raise SystemExit(f"Expected 20 fixtures, found {len(files)}")

    if os.environ.get("CASEPACKET_LOCAL", "1") == "1":
        if LOCAL_DIR.exists():
            shutil.rmtree(LOCAL_DIR)
        reset_store_cache()

    for path in files:
        listing = json.loads(path.read_text(encoding="utf-8"))
        ingest_listing(listing)

    from shared.store import get_store

    loaded = get_store().list_cases()
    print(f"Seeded {len(loaded)} cases (simulated=true)\n")
    print(f"{'ID':<10} {'RISK':<6} {'CLUSTER':<12} TITLE")
    for case in loaded:
        print(f"{case['id']:<10} {case.get('risk'):<6} {case.get('cluster_id') or '-':<12} {case['title']}")
    print("\nNext:")
    print("  py scripts/local_server.py")
    print("  cd web && npm install && npm run dev")


if __name__ == "__main__":
    main()
