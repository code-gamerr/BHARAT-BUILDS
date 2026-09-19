<<<<<<< HEAD
#!/usr/bin/env python3
"""Upload fixtures to RawBucket (triggers ingest) or POST /ingest.

Fixtures come only from fixtures/*.json — nothing embedded in this script.
API key from --api-key or CASEPACKET_API_KEY / DEMO_API_KEY env (no default secret).
"""
from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

import urllib.request

ROOT = Path(__file__).resolve().parents[1]
FIX = Path(os.environ.get("CASEPACKET_FIXTURES_DIR", ROOT / "fixtures"))


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--api", help="API base URL (uses POST /ingest)")
    p.add_argument(
        "--api-key",
        default=os.environ.get("CASEPACKET_API_KEY") or os.environ.get("DEMO_API_KEY") or "",
    )
    p.add_argument("--bucket", help="S3 raw bucket (aws s3 cp)")
    args = p.parse_args()
    files = sorted(FIX.glob("fx-*.json"))
    if not files:
        print(f"no fixtures in {FIX}", file=sys.stderr)
        return 1
    if args.api:
        for f in files:
            data = f.read_bytes()
            headers = {"content-type": "application/json"}
            if args.api_key:
                headers["x-api-key"] = args.api_key
            req = urllib.request.Request(
                args.api.rstrip("/") + "/ingest",
                data=data,
                headers=headers,
                method="POST",
            )
            with urllib.request.urlopen(req) as resp:
                print(f.name, resp.status, resp.read()[:120])
        return 0
    if args.bucket:
        import subprocess

        for f in files:
            key = f"raw/seed/{f.name}"
            subprocess.check_call(["aws", "s3", "cp", str(f), f"s3://{args.bucket}/{key}"])
            print("uploaded", key)
        return 0
    print("pass --api URL or --bucket NAME", file=sys.stderr)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
=======
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
>>>>>>> Tanish-local
