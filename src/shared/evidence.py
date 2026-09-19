"""ArgusWatch-style proof / evidence chain events."""

from __future__ import annotations

import json

from .packet import utc_now
from .store import sha256_text


def event(
    name: str,
    *,
    component: str,
    input_sha256: str | None = None,
    output_sha256: str | None = None,
    detail: str | None = None,
    at: str | None = None,
    **extra,
) -> dict:
    payload = {
        "event": name,
        "timestamp": at or utc_now(),
        "component": component,
        "input_sha256": input_sha256,
        "output_sha256": output_sha256,
        "detail": detail,
    }
    payload.update(extra)
    return {k: v for k, v in payload.items() if v is not None}


def hash_payload(obj) -> str:
    raw = json.dumps(obj, sort_keys=True, ensure_ascii=False, default=str)
    return sha256_text(raw)


def build_proof_chain(case: dict, relationships_for_case: list[dict], generated_at: str | None = None) -> list[dict]:
    raw_sha = case.get("raw_sha256")
    entities_sha = hash_payload(case.get("entities") or [])
    risk_sha = hash_payload(
        {
            "risk": case.get("risk"),
            "factors": case.get("risk_factors"),
            "explain": case.get("explain"),
        }
    )
    corr_sha = hash_payload(relationships_for_case)
    chain = [
        event(
            "source",
            component="fixture-loader",
            detail=case.get("source"),
            at=case.get("created_at"),
            output_sha256=raw_sha,
        ),
        event(
            "raw_object",
            component="s3-raw",
            input_sha256=raw_sha,
            output_sha256=raw_sha,
            detail=case.get("raw_s3_key"),
            at=case.get("created_at"),
        ),
        event(
            "entity_extraction",
            component="extractor-v2",
            input_sha256=raw_sha,
            output_sha256=entities_sha,
            detail=f"{len(case.get('entities') or [])} observables",
            at=case.get("created_at"),
        ),
        event(
            "correlation",
            component="correlator-misp-lite",
            input_sha256=entities_sha,
            output_sha256=corr_sha,
            detail=f"{len(relationships_for_case)} links",
            at=case.get("created_at"),
        ),
        event(
            "risk_decision",
            component="risk-engine-v2",
            input_sha256=corr_sha,
            output_sha256=risk_sha,
            detail=f"risk={case.get('risk')}",
            at=case.get("created_at"),
        ),
        event(
            "case",
            component="case-store",
            input_sha256=risk_sha,
            output_sha256=raw_sha,
            detail=case.get("id"),
            at=case.get("created_at"),
        ),
    ]
    if case.get("packet_sha256"):
        chain.append(
            event(
                "packet",
                component="compiler-v1",
                input_sha256=risk_sha,
                output_sha256=case.get("packet_sha256"),
                detail=case.get("packet_s3_key"),
                at=generated_at or case.get("packet_generated_at"),
                execution_arn=case.get("execution_arn"),
            )
        )
    return chain
