"""Step Functions: re-extract entities; optional Bedrock enrich (degrades cleanly)."""
from __future__ import annotations

import json
import os
from decimal import Decimal

import boto3

from casepacket import extract_entities, sha256_text

ddb = boto3.resource("dynamodb")
TABLE = os.environ["CASES_TABLE"]
BEDROCK_MODEL = os.environ.get("BEDROCK_MODEL_ID", "")
ENABLE_BEDROCK = os.environ.get("ENABLE_BEDROCK", "0") == "1"


def handler(event, context):
    case_id = event["case_id"]
    table = ddb.Table(TABLE)
    meta = table.get_item(Key={"pk": f"CASE#{case_id}", "sk": "META"}).get("Item")
    if not meta:
        raise ValueError(f"missing case {case_id}")
    body = f"{meta.get('title', '')}\n{meta.get('body', '')}"
    ents = extract_entities(body)
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

    enrichment = "rules"
    if ENABLE_BEDROCK and BEDROCK_MODEL:
        try:
            br = boto3.client("bedrock-runtime")
            # Model body is account/model-specific; failure → degraded (packet still ships)
            br.invoke_model(
                modelId=BEDROCK_MODEL,
                contentType="application/json",
                accept="application/json",
                body=json.dumps(
                    {
                        "messages": [
                            {
                                "role": "user",
                                "content": [
                                    {
                                        "text": "One-line SIMULATED LE triage summary only. Mark TLP."
                                    }
                                ],
                            }
                        ]
                    }
                ).encode("utf-8"),
            )
            enrichment = "regex+bedrock"
        except Exception:
            enrichment = "degraded"

    event["entity_count"] = len(ents)
    event["enrichment"] = enrichment
    return event
