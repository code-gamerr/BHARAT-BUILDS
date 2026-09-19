"""API Gateway handlers: health, cases, packet, ingest."""
from __future__ import annotations

import json
import os
import uuid
from decimal import Decimal

import boto3

from casepacket import (
    check_api_key,
    extract_entities,
    ok_json,
    require_simulated,
    score_risk,
    sha256_text,
    utc_now,
)

ddb = boto3.resource("dynamodb")
s3 = boto3.client("s3")
sfn = boto3.client("stepfunctions")

TABLE = os.environ.get("CASES_TABLE", "")
RAW_BUCKET = os.environ.get("RAW_BUCKET", "")
PACKET_BUCKET = os.environ.get("PACKET_BUCKET", "")
STATE_MACHINE_ARN = os.environ.get("STATE_MACHINE_ARN", "")


def _table():
    return ddb.Table(TABLE)


def _decimal(obj):
    if isinstance(obj, list):
        return [_decimal(x) for x in obj]
    if isinstance(obj, dict):
        return {k: _decimal(v) for k, v in obj.items()}
    if isinstance(obj, Decimal):
        return int(obj) if obj % 1 == 0 else float(obj)
    return obj


def health(event, context):
    checks = {"ddb": False, "s3": False}
    try:
        _table().scan(Limit=1)
        checks["ddb"] = True
    except Exception:
        pass
    try:
        if RAW_BUCKET:
            s3.head_bucket(Bucket=RAW_BUCKET)
            checks["s3"] = True
    except Exception:
        pass
    status = "ok" if checks["ddb"] else "degraded"
    return ok_json(
        {
            "status": status,
            "version": "0.1.0",
            "product": "CasePacket",
            "disclaimer": "SIMULATED FIXTURE DATA — NOT OPERATIONAL INTEL",
            "checks": checks,
        }
    )


def handler(event, context):
    method = (event.get("requestContext", {}).get("http", {}) or {}).get("method") or event.get(
        "httpMethod", "GET"
    )
    path = event.get("rawPath") or event.get("path") or ""
    if method == "OPTIONS":
        return ok_json({"ok": True})

    if path.rstrip("/").endswith("/healthz"):
        return health(event, context)

    if not check_api_key(event):
        return ok_json({"error": "unauthorized", "code": "AUTH"}, 401)

    if path.rstrip("/").endswith("/cases") and method == "GET":
        return list_cases()
    if "/cases/" in path and path.rstrip("/").endswith("/packet") and method == "POST":
        case_id = path.split("/cases/")[1].split("/")[0]
        return start_packet(case_id)
    if "/cases/" in path and path.rstrip("/").endswith("/packet") and method == "GET":
        case_id = path.split("/cases/")[1].split("/")[0]
        return get_packet(case_id)
    if "/cases/" in path and method == "GET":
        case_id = path.rstrip("/").split("/")[-1]
        return get_case(case_id)
    if path.rstrip("/").endswith("/ingest") and method == "POST":
        body = event.get("body") or "{}"
        if event.get("isBase64Encoded"):
            import base64

            body = base64.b64decode(body).decode("utf-8")
        return ingest_json(json.loads(body))

    return ok_json({"error": "not_found", "path": path}, 404)


def list_cases():
    resp = _table().scan()
    items = [i for i in resp.get("Items", []) if i.get("sk") == "META"]
    items.sort(key=lambda x: int(x.get("risk", 0)), reverse=True)
    out = [
        {
            "id": i.get("case_id"),
            "title": i.get("title"),
            "risk": int(i.get("risk", 0)),
            "ml_risk": int(i.get("ml_risk", i.get("risk", 0))),
            "category": i.get("category"),
            "cluster_id": i.get("cluster_id"),
            "created_at": i.get("created_at"),
            "status": i.get("status"),
        }
        for i in items
    ]
    return ok_json(_decimal(out))


def get_case(case_id: str):
    meta = _table().get_item(Key={"pk": f"CASE#{case_id}", "sk": "META"}).get("Item")
    if not meta:
        return ok_json({"error": "not_found"}, 404)
    ents = (
        _table()
        .query(
            KeyConditionExpression="pk = :pk AND begins_with(sk, :sk)",
            ExpressionAttributeValues={":pk": f"CASE#{case_id}", ":sk": "ENT#"},
        )
        .get("Items", [])
    )
    meta["entities"] = [
        {
            "type": e.get("etype"),
            "value": e.get("value"),
            "confidence": float(e.get("confidence", 0.9)),
        }
        for e in ents
    ]
    linked: list[str] = []
    cluster_id = meta.get("cluster_id")
    if cluster_id:
        for item in _table().scan().get("Items", []):
            if (
                item.get("sk") == "META"
                and item.get("case_id") != case_id
                and item.get("cluster_id") == cluster_id
            ):
                linked.append(item["case_id"])
    meta["linked_case_ids"] = linked
    return ok_json(_decimal(meta))


def start_packet(case_id: str):
    meta = _table().get_item(Key={"pk": f"CASE#{case_id}", "sk": "META"}).get("Item")
    if not meta:
        return ok_json({"error": "not_found"}, 404)
    if not STATE_MACHINE_ARN:
        return ok_json({"error": "state_machine_missing"}, 500)
    resp = sfn.start_execution(
        stateMachineArn=STATE_MACHINE_ARN,
        name=f"{case_id}-{uuid.uuid4().hex[:8]}",
        input=json.dumps({"case_id": case_id}),
    )
    _table().update_item(
        Key={"pk": f"CASE#{case_id}", "sk": "META"},
        UpdateExpression="SET execution_arn = :a, #s = :s",
        ExpressionAttributeNames={"#s": "status"},
        ExpressionAttributeValues={":a": resp["executionArn"], ":s": "compiling"},
    )
    return ok_json({"executionArn": resp["executionArn"], "case_id": case_id})


def get_packet(case_id: str):
    meta = _table().get_item(Key={"pk": f"CASE#{case_id}", "sk": "META"}).get("Item")
    if not meta:
        return ok_json({"error": "not_found"}, 404)
    key = meta.get("packet_s3_key")
    if not key:
        return ok_json({"status": meta.get("status", "open"), "downloadUrl": None})
    url = s3.generate_presigned_url(
        "get_object",
        Params={"Bucket": PACKET_BUCKET, "Key": key},
        ExpiresIn=900,
    )
    return ok_json(
        {
            "status": meta.get("status"),
            "downloadUrl": url,
            "sha256": meta.get("packet_sha256"),
            "execution_arn": meta.get("execution_arn"),
            "s3_key": key,
        }
    )


def ingest_json(doc: dict):
    require_simulated(doc)
    case_id = doc.get("id") or f"fx-{uuid.uuid4().hex[:8]}"
    raw = json.dumps(doc, ensure_ascii=False).encode("utf-8")
    key = f"raw/{utc_now()[:10]}/{case_id}.json"
    s3.put_object(Bucket=RAW_BUCKET, Key=key, Body=raw, ContentType="application/json")
    body = f"{doc.get('title', '')}\n{doc.get('body', '')}"
    ents = extract_entities(body)
    risk, cat = score_risk(body, ents)
    digest = sha256_text(body)
    cluster_id = None
    for e in ents:
        if e["type"] in ("email", "phone", "wallet"):
            cluster_id = f"CLU-{sha256_text(e['value'])[:10]}"
            break
    item = {
        "pk": f"CASE#{case_id}",
        "sk": "META",
        "case_id": case_id,
        "title": doc.get("title", case_id),
        "body": doc.get("body", ""),
        "risk": risk,
        "ml_risk": risk,
        "category": doc.get("category_hint") or cat,
        "raw_s3_key": key,
        "raw_sha256": digest,
        "tlp": doc.get("tlp", "TLP:AMBER"),
        "status": "open",
        "simulated": True,
        "created_at": utc_now(),
        "cluster_id": cluster_id,
    }
    _table().put_item(Item=item)
    for e in ents:
        _table().put_item(
            Item={
                "pk": f"CASE#{case_id}",
                "sk": f"ENT#{e['type']}#{sha256_text(e['value'])[:16]}",
                "etype": e["type"],
                "value": e["value"],
                "confidence": Decimal(str(e["confidence"])),
            }
        )
    return ok_json({"case_id": case_id, "raw_s3_key": key, "risk": risk, "entities": ents})
