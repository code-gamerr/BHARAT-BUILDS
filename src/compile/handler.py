"""Step Functions: render CasePacket JSON to S3 (machine-readable findings)."""
from __future__ import annotations

import json
import os

import boto3

from casepacket import sha256_text, utc_now

ddb = boto3.resource("dynamodb")
s3 = boto3.client("s3")
TABLE = os.environ["CASES_TABLE"]
PACKET_BUCKET = os.environ["PACKET_BUCKET"]


def handler(event, context):
    case_id = event["case_id"]
    table = ddb.Table(TABLE)
    meta = table.get_item(Key={"pk": f"CASE#{case_id}", "sk": "META"}).get("Item")
    if not meta:
        raise ValueError(f"missing case {case_id}")
    ents = (
        table.query(
            KeyConditionExpression="pk = :pk AND begins_with(sk, :sk)",
            ExpressionAttributeValues={":pk": f"CASE#{case_id}", ":sk": "ENT#"},
        ).get("Items", [])
    )
    entities = [
        {"type": e.get("etype"), "value": e.get("value"), "confidence": float(e.get("confidence", 0.9))}
        for e in ents
    ]
    objects = []
    for e in entities:
        if e["type"] == "email":
            objects.append(
                {"type": "indicator", "pattern": f"[email-addr:value = '{e['value']}']"}
            )
        elif e["type"] == "phone":
            objects.append({"type": "indicator", "pattern": f"[phone-number:value = '{e['value']}']"})
        elif e["type"] == "wallet":
            objects.append({"type": "indicator", "pattern": f"[crypto:address = '{e['value']}']"})

    # security-audit-skill inspired: machine-readable findings array
    findings = [
        {
            "id": f"F-{i+1}",
            "severity": "medium" if meta.get("risk", 0) >= 50 else "low",
            "title": f"Entity {e['type']}",
            "detail": e["value"],
            "verified": True,
        }
        for i, e in enumerate(entities)
    ]

    linked: list[str] = []
    cluster_id = meta.get("cluster_id")
    if cluster_id:
        for item in table.scan().get("Items", []):
            if (
                item.get("sk") == "META"
                and item.get("case_id") != case_id
                and item.get("cluster_id") == cluster_id
            ):
                linked.append(item["case_id"])

    packet = {
        "packet_version": "1.0",
        "case_id": case_id,
        "generated_at": utc_now(),
        "tlp": meta.get("tlp", "TLP:AMBER"),
        "summary": f"SIMULATED triage for '{meta.get('title')}'. Risk={meta.get('risk')}.",
        "risk": int(meta.get("risk", 0)),
        "entities": entities,
        "findings": findings,
        "linked_case_ids": linked,
        "chain_of_custody": [
            {
                "event": "ingest",
                "at": meta.get("created_at"),
                "s3": meta.get("raw_s3_key"),
                "sha256": meta.get("raw_sha256"),
            },
            {
                "event": "compile",
                "at": utc_now(),
                "execution_arn": meta.get("execution_arn"),
            },
        ],
        "objects": objects,
        "ml": {
            "extractor": "regex" if event.get("enrichment") in (None, "rules", "degraded") else "regex+bedrock",
            "ranker": "bedrock-rft-grpo" if event.get("enrichment") == "regex+bedrock" else "rules",
            "group_size": int(event.get("group_size") or os.environ.get("GRPO_GROUP_SIZE", "13")),
            "train_prompts": int(os.environ.get("GRPO_TRAIN_PROMPTS", "20")),
            "rft_job_arn": os.environ.get("RFT_JOB_ARN") or None,
            "rules_risk": int(event.get("rules_risk", meta.get("risk", 0))),
            "ml_risk": int(meta.get("ml_risk", meta.get("risk", 0))),
            "final_risk": int(meta.get("risk", 0)),
            "enrichment": event.get("enrichment", "rules"),
        },
        "disclaimer": "SIMULATED FIXTURE DATA — NOT OPERATIONAL INTEL",
    }
    body = json.dumps(packet, ensure_ascii=False, indent=2).encode("utf-8")
    key = f"packets/{case_id}/{utc_now().replace(':', '')}.json"
    s3.put_object(Bucket=PACKET_BUCKET, Key=key, Body=body, ContentType="application/json")
    digest = sha256_text(body.decode("utf-8"))
    table.update_item(
        Key={"pk": f"CASE#{case_id}", "sk": "META"},
        UpdateExpression="SET packet_s3_key = :k, packet_sha256 = :h, #s = :s",
        ExpressionAttributeNames={"#s": "status"},
        ExpressionAttributeValues={":k": key, ":h": digest, ":s": "packet_ready"},
    )
    event["packet_s3_key"] = key
    event["packet_sha256"] = digest
    return event
