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
