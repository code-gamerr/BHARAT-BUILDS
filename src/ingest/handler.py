<<<<<<< HEAD
"""S3 → DynamoDB ingest (fixtures only)."""
from __future__ import annotations

import json
import os
import urllib.parse
from decimal import Decimal

import boto3

from casepacket import extract_entities, require_simulated, score_risk, sha256_text, utc_now

s3 = boto3.client("s3")
ddb = boto3.resource("dynamodb")
TABLE = os.environ["CASES_TABLE"]


def handler(event, context):
    table = ddb.Table(TABLE)
    for rec in event.get("Records", []):
        bucket = rec["s3"]["bucket"]["name"]
        key = urllib.parse.unquote_plus(rec["s3"]["object"]["key"])
        obj = s3.get_object(Bucket=bucket, Key=key)
        raw = obj["Body"].read()
        doc = json.loads(raw)
        require_simulated(doc)
        case_id = doc.get("id") or key.split("/")[-1].replace(".json", "")
        body = f"{doc.get('title', '')}\n{doc.get('body', '')}"
        ents = extract_entities(body)
        risk, cat = score_risk(body, ents)
        cluster_id = None
        for e in ents:
            if e["type"] in ("email", "phone", "wallet"):
                cluster_id = f"CLU-{sha256_text(e['value'])[:10]}"
                break
        table.put_item(
            Item={
                "pk": f"CASE#{case_id}",
                "sk": "META",
                "case_id": case_id,
                "title": doc.get("title", case_id),
                "body": doc.get("body", ""),
                "risk": risk,
                "ml_risk": risk,
                "category": doc.get("category_hint") or cat,
                "raw_s3_key": key,
                "raw_sha256": sha256_text(body),
                "tlp": doc.get("tlp", "TLP:AMBER"),
                "status": "open",
                "simulated": True,
                "created_at": utc_now(),
                "cluster_id": cluster_id,
            }
        )
        for e in ents:
            table.put_item(
                Item={
                    "pk": f"CASE#{case_id}",
                    "sk": f"ENT#{e['type']}#{sha256_text(e['value'])[:16]}",
                    "etype": e["type"],
                    "value": e["value"],
                    "confidence": Decimal(str(e["confidence"])),
                }
            )
    return {"ok": True}
=======
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
>>>>>>> Tanish-local
