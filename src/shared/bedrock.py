"""Optional Bedrock enrichment. Failures must never block packet compile."""

from __future__ import annotations

import json
import os


def enrich_with_bedrock(case: dict) -> dict:
    import boto3

    model_id = os.environ.get("BEDROCK_MODEL_ID", "amazon.titan-text-lite-v1")
    prompt = (
        "Summarize this SIMULATED cybercrime listing in 2 sentences. "
        "Classify as fraud, credentials, docs, or other. "
        "Return JSON {summary, category}.\n\n"
        f"Title: {case.get('title')}\nBody: {case.get('body')}"
    )
    client = boto3.client("bedrock-runtime", region_name=os.environ.get("AWS_REGION", "ap-south-1"))
    resp = client.invoke_model(
        modelId=model_id,
        body=json.dumps({"inputText": prompt, "textGenerationConfig": {"maxTokenCount": 180}}),
    )
    payload = json.loads(resp["body"].read())
    text = payload.get("results", [{}])[0].get("outputText", "")
    try:
        parsed = json.loads(text)
    except json.JSONDecodeError:
        return {"summary": text.strip()[:400]} if text.strip() else {}
    out = {}
    if parsed.get("summary"):
        out["summary"] = str(parsed["summary"])[:600]
    if parsed.get("category") in {"fraud", "credentials", "docs", "other"}:
        out["category"] = parsed["category"]
    return out
