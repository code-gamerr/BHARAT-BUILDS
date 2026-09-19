<<<<<<< HEAD
"""Step Functions: risk score + clustering; optional ML blend (docs/ml.md)."""
from __future__ import annotations

import os

import boto3

from casepacket import score_risk, sha256_text

ddb = boto3.resource("dynamodb")
TABLE = os.environ["CASES_TABLE"]
GRPO_GROUP_SIZE = int(os.environ.get("GRPO_GROUP_SIZE", "13"))
ENABLE_BEDROCK = os.environ.get("ENABLE_BEDROCK", "0") == "1"


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
    body = f"{meta.get('title', '')}\n{meta.get('body', '')}"
    entity_dicts = [{"type": e["etype"], "value": e["value"]} for e in ents]
    rules_risk, cat = score_risk(body, entity_dicts)
    cluster_id = None
    for e in ents:
        if e.get("etype") in ("email", "phone", "wallet"):
            cluster_id = f"CLU-{sha256_text(e['value'])[:10]}"
            break

    # Until RFT custom model is attached, ml_risk mirrors rules (degraded OK)
    ml_risk = rules_risk
    if ENABLE_BEDROCK:
        # placeholder for InvokeModel on RFT custom model — never block compile
        try:
            ml_risk = rules_risk  # swap when BEDROCK_CUSTOM_MODEL_ID set
        except Exception:
            ml_risk = rules_risk

    final_risk = int(round(0.6 * rules_risk + 0.4 * ml_risk))
    enrichment = event.get("enrichment") or ("degraded" if ENABLE_BEDROCK else "rules")

    table.update_item(
        Key={"pk": f"CASE#{case_id}", "sk": "META"},
        UpdateExpression="SET risk = :r, ml_risk = :m, category = :c, cluster_id = :cl",
        ExpressionAttributeValues={
            ":r": final_risk,
            ":m": ml_risk,
            ":c": cat,
            ":cl": cluster_id,
        },
    )
    event["risk"] = final_risk
    event["rules_risk"] = rules_risk
    event["ml_risk"] = ml_risk
    event["category"] = cat
    event["cluster_id"] = cluster_id
    event["group_size"] = GRPO_GROUP_SIZE
    event["enrichment"] = enrichment
=======
from __future__ import annotations

import sys
from pathlib import Path

SRC = Path(__file__).resolve().parents[1]
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from shared.pipeline import score_cluster  # noqa: E402


def lambda_handler(event, context):
    score_cluster(event["case_id"])
>>>>>>> Tanish-local
    return event
