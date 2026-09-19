"""HTTP route handlers used by the local server and the API Lambda."""

from __future__ import annotations

import os
from urllib.parse import parse_qs

from . import VERSION
from .correlation import build_relationships, graph_payload, linked_for_case
from .evidence import build_proof_chain
from .packet import render_pdf_text
from .pipeline import compile_case_packet, ingest_listing
from .scoring import risk_band, source_label
from .store import get_store, is_local


def _snippet(text: str, n: int = 72) -> str:
    blob = " ".join((text or "").split())
    if len(blob) <= n:
        return blob
    return blob[: n - 1] + "…"


def _public_case(case: dict, store=None) -> dict:
    store = store or get_store()
    cases = store.list_cases()
    relationships = build_relationships(cases)
    linked = case.get("linked_cases") or linked_for_case(case["id"], relationships)
    case_rels = case.get("relationships") or [
        r for r in relationships if r["source_case"] == case["id"] or r["target_case"] == case["id"]
    ]
    proof = case.get("proof_chain") or build_proof_chain(case, linked)
    risk = int(case.get("risk") or 0)
    return {
        "id": case["id"],
        "title": case.get("title"),
        "snippet": _snippet(case.get("title") or case.get("body") or ""),
        "risk": risk,
        "risk_band": case.get("risk_band") or risk_band(risk),
        "risk_out_of_ten": case.get("risk_out_of_ten")
        if case.get("risk_out_of_ten") is not None
        else round(risk / 10, 1),
        "risk_factors": case.get("risk_factors") or [],
        "category": case.get("category"),
        "status": case.get("status"),
        "created_at": case.get("created_at"),
        "cluster_id": case.get("cluster_id"),
        "tlp": case.get("tlp"),
        "source": case.get("source"),
        "source_label": source_label(case.get("source")),
        "entities": case.get("entities") or [],
        "relationships": case_rels,
        "linked_cases": linked,
        "linked_case_ids": [x["case_id"] for x in linked],
        "body": case.get("body"),
        "summary": case.get("summary"),
        "keyword_hits": case.get("keyword_hits") or [],
        "timeline": case.get("timeline") or proof,
        "proof_chain": proof,
        "evidence": [
            {
                "kind": "raw",
                "s3": case.get("raw_s3_key"),
                "sha256": case.get("raw_sha256"),
                "source": case.get("source"),
                "captured_at": case.get("created_at"),
            }
        ],
        "raw_s3_key": case.get("raw_s3_key"),
        "raw_sha256": case.get("raw_sha256"),
        "packet_s3_key": case.get("packet_s3_key"),
        "packet_sha256": case.get("packet_sha256"),
        "packet_generated_at": case.get("packet_generated_at"),
        "execution_arn": case.get("execution_arn"),
        "enrichment": case.get("enrichment") or "rules",
        "explain": case.get("explain") or {},
        "simulated": True,
    }


def health() -> tuple[int, dict]:
    store = get_store()
    checks = store.health_checks()
    ok = all(v in {"ok", "disabled", "enabled"} for v in checks.values())
    return 200 if ok else 503, {
        "status": "ok" if ok else "degraded",
        "version": VERSION,
        "product": "CasePacket",
        "mode": "local" if is_local() else "aws",
        "enrichment": "rules" if os.environ.get("ENABLE_BEDROCK") != "1" else "bedrock-optional",
        "checks": checks,
    }


def ops() -> tuple[int, dict]:
    store = get_store()
    code, health_body = health()
    cases = store.list_cases()
    relationships = build_relationships(cases)
    bands = {"high": 0, "medium": 0, "low": 0}
    ready = 0
    for case in cases:
        bands[risk_band(int(case.get("risk") or 0))] += 1
        if case.get("status") == "packet_ready":
            ready += 1
    return code, {
        **store.get_ops(),
        "health": health_body,
        "stats": {
            "cases": len(cases),
            "packets_ready": ready,
            "clusters": len({c.get("cluster_id") for c in cases if c.get("cluster_id")}),
            "entities": sum(len(c.get("entities") or []) for c in cases),
            "relationships": len(relationships),
            "risk_bands": bands,
        },
    }


def list_cases() -> tuple[int, dict]:
    store = get_store()
    items = [_public_case(c, store) for c in store.list_cases()]
    return 200, {"count": len(items), "cases": items}


def get_case(case_id: str) -> tuple[int, dict]:
    store = get_store()
    case = store.get_case(case_id)
    if not case:
        return 404, {"error": "case_not_found", "id": case_id}
    return 200, _public_case(case, store)


def get_graph() -> tuple[int, dict]:
    store = get_store()
    cases = store.list_cases()
    relationships = build_relationships(cases)
    return 200, graph_payload(cases, relationships)


def start_packet(case_id: str) -> tuple[int, dict]:
    store = get_store()
    case = store.get_case(case_id)
    if not case:
        return 404, {"error": "case_not_found", "id": case_id}

    stages = [
        {"id": "normalize", "label": "Normalize input"},
        {"id": "extract", "label": "Extract entities"},
        {"id": "risk", "label": "Calculate risk"},
        {"id": "correlate", "label": "Correlate cases"},
        {"id": "evidence", "label": "Build evidence chain"},
        {"id": "stix", "label": "Compile STIX objects"},
        {"id": "s3", "label": "Write packet to S3"},
    ]

    if is_local() or not os.environ.get("STATE_MACHINE_ARN"):
        result = compile_case_packet(case_id)
        return 200, {
            "case_id": case_id,
            "status": "SUCCEEDED",
            "execution_arn": result["execution_arn"],
            "s3_key": result["s3_key"],
            "sha256": result["sha256"],
            "mode": "local-sync",
            "stages": [{**s, "status": "SUCCEEDED"} for s in stages],
        }

    import json

    import boto3

    sfn = boto3.client("stepfunctions")
    resp = sfn.start_execution(
        stateMachineArn=os.environ["STATE_MACHINE_ARN"],
        name=f"{case_id}-{os.urandom(3).hex()}",
        input=json.dumps({"case_id": case_id}),
    )
    store.put_ops(
        {
            "last_execution_arn": resp["executionArn"],
            "last_status": "RUNNING",
            "last_case_id": case_id,
            "last_at": resp["startDate"].isoformat()
            if hasattr(resp["startDate"], "isoformat")
            else str(resp["startDate"]),
        }
    )
    return 202, {
        "case_id": case_id,
        "status": "RUNNING",
        "execution_arn": resp["executionArn"],
        "mode": "step-functions",
        "stages": stages,
    }


def get_packet(case_id: str) -> tuple[int, dict]:
    store = get_store()
    case = store.get_case(case_id)
    if not case:
        return 404, {"error": "case_not_found", "id": case_id}
    if case.get("status") != "packet_ready" or not case.get("packet_s3_key"):
        return 404, {
            "error": "packet_not_ready",
            "case_id": case_id,
            "status": case.get("status"),
            "execution_arn": case.get("execution_arn"),
        }
    key = case["packet_s3_key"]
    packet = store.get_packet(key)
    return 200, {
        "case_id": case_id,
        "status": "packet_ready",
        "s3_key": key,
        "sha256": case.get("packet_sha256"),
        "generated_at": case.get("packet_generated_at"),
        "execution_arn": case.get("execution_arn"),
        "download_url": store.download_url(key),
        "pdf_text_url": f"/cases/{case_id}/packet/pdf",
        "packet": packet,
    }


def get_packet_pdf(case_id: str) -> tuple[int, bytes, str] | tuple[int, dict]:
    code, body = get_packet(case_id)
    if code != 200:
        return code, body
    text = render_pdf_text(body["packet"])
    return 200, text.encode("utf-8"), "text/plain; charset=utf-8"


def ingest(listing: dict) -> tuple[int, dict]:
    if not isinstance(listing, dict) or (not listing.get("title") and not listing.get("body")):
        return 400, {"error": "invalid_listing", "hint": "JSON with title/body required"}
    listing.setdefault("meta", {})
    listing["meta"]["simulated"] = True
    case = ingest_listing(listing)
    return 201, _public_case(case)


def download_local(query: str) -> tuple[int, bytes, str] | tuple[int, dict]:
    params = parse_qs(query)
    key = (params.get("key") or [""])[0]
    if not key or ".." in key or key.startswith("/") or "\\" in key:
        return 400, {"error": "bad_key"}
    store = get_store()
    try:
        data = store.get_raw(key)
    except FileNotFoundError:
        return 404, {"error": "not_found"}
    return 200, data, "application/json"
