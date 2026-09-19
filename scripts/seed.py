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
