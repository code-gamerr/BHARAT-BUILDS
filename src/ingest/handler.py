"""S3 Object Created / EventBridge → normalize fixture into a case."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from urllib.parse import unquote_plus

SRC = Path(__file__).resolve().parents[1]
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from shared.pipeline import ingest_listing, ingest_raw_key  # noqa: E402
from shared.store import get_store  # noqa: E402


def _keys_from_event(event: dict) -> list[str]:
    keys: list[str] = []
    for record in event.get("Records") or []:
        s3 = record.get("s3") or {}
        key = (s3.get("object") or {}).get("key")
        if key:
            keys.append(unquote_plus(key))
    detail = event.get("detail") or {}
    key = (detail.get("object") or {}).get("key")
    if key:
        keys.append(unquote_plus(key))
    return keys


def lambda_handler(event, context):
    store = get_store()
    ingested = []
    for key in _keys_from_event(event):
        if not key.startswith("raw/"):
            continue
        ingested.append(ingest_raw_key(key, store)["id"])
    if not ingested and event.get("listing"):
        ingested.append(ingest_listing(event["listing"], store)["id"])
    return {"ingested": ingested, "count": len(ingested), "raw": json.dumps(event)[:200]}
