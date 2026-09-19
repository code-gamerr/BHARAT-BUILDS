"""Ingest → extract → correlate → score → compile."""

from __future__ import annotations

import json
import os
import uuid
from datetime import datetime, timezone

from . import DISCLAIMER
from .correlation import (
    build_relationships,
    correlation_bonus,
    linked_for_case,
    refresh_clusters,
)
from .evidence import build_proof_chain
from .ner import extract_entities
from .packet import compile_packet, rules_summary, utc_now
from .scoring import map_category, score_case
from .store import Store, get_store, sha256_bytes


def case_id_from_fixture(fixture_id: str) -> str:
    suffix = fixture_id.split("-")[-1]
    if suffix.isdigit():
        return f"CASE-{int(suffix):03d}"
    safe = "".join(ch if ch.isalnum() else "-" for ch in fixture_id).strip("-").upper()
    return f"CASE-{safe[:24]}"


def _refresh_all(store: Store) -> list[dict]:
    cases = store.list_cases()
    relationships = build_relationships(cases)
    mapping = refresh_clusters(cases, relationships)
    # First pass: clusters
    for case in cases:
        case["cluster_id"] = mapping.get(case["id"])
        store.put_case(case)
    # Second pass: correlation-aware risk
    cases = store.list_cases()
    relationships = build_relationships(cases)
    for case in cases:
        bonus = correlation_bonus(case["id"], relationships)
        scored = score_case(
            case.get("title", ""),
            case.get("body", ""),
            case.get("category"),
            case.get("entities") or [],
            correlation_bonus=bonus,
        )
        case.update(scored)
        case["relationships"] = [
            r
            for r in relationships
            if r["source_case"] == case["id"] or r["target_case"] == case["id"]
        ]
        case["linked_cases"] = linked_for_case(case["id"], relationships)
        store.put_case(case)
    store.put_ops({**store.get_ops(), "relationship_count": len(relationships)})
    return store.list_cases()


def extract_enrich(case_id: str, store: Store | None = None) -> dict:
    store = store or get_store()
    case = store.get_case(case_id)
    if not case:
        raise KeyError(case_id)
    text = f"{case.get('title', '')}\n{case.get('body', '')}"
    case["entities"] = extract_entities(
        text,
        source=case.get("source") or "fixture://unknown",
        seen_at=case.get("created_at") or utc_now(),
    )
    case["summary"] = rules_summary(case)
    case["enrichment"] = "rules"
    if os.environ.get("ENABLE_BEDROCK") == "1":
        try:
            from .bedrock import enrich_with_bedrock

            extra = enrich_with_bedrock(case)
            case.update(extra)
            case["enrichment"] = "bedrock"
        except Exception:
            case["enrichment"] = "degraded"
    store.put_case(case)
    return case


def score_cluster(case_id: str, store: Store | None = None) -> dict:
    store = store or get_store()
    case = store.get_case(case_id)
    if not case:
        raise KeyError(case_id)
    if not case.get("entities"):
        case = extract_enrich(case_id, store)
    _refresh_all(store)
    return store.get_case(case_id) or case


def compile_case_packet(case_id: str, execution_arn: str | None = None, store: Store | None = None) -> dict:
    store = store or get_store()
    case = score_cluster(case_id, store)
    cases = store.list_cases()
    relationships = build_relationships(cases)
    linked = linked_for_case(case_id, relationships)
    case_rels = [r for r in relationships if r["source_case"] == case_id or r["target_case"] == case_id]
    execution_arn = execution_arn or (
        f"arn:aws:states:ap-south-1:000000000000:execution:CasePacketCompile:local-{uuid.uuid4().hex[:12]}"
    )
    generated_at = utc_now()
    ts = generated_at.replace(":", "").replace("-", "")
    key = f"packets/{case_id}/{ts}.json"

    proof = build_proof_chain(case, linked, generated_at=generated_at)
    case["timeline"] = proof
    case["linked_cases"] = linked
    case["relationships"] = case_rels
    case["proof_chain"] = proof

    packet = compile_packet(
        case,
        linked_cases=linked,
        relationships=case_rels,
        proof_chain=proof,
        execution_arn=execution_arn,
        generated_at=generated_at,
        enrichment=case.get("enrichment") or "rules",
        summary=case.get("summary"),
    )
    packet_sha = store.put_packet(key, packet)
    case["status"] = "packet_ready"
    case["packet_s3_key"] = key
    case["packet_sha256"] = packet_sha
    case["packet_generated_at"] = generated_at
    case["execution_arn"] = execution_arn
    # Refresh proof with packet hash
    case["proof_chain"] = build_proof_chain(case, linked, generated_at=generated_at)
    packet["proof_chain"] = case["proof_chain"]
    packet["aws"]["packet_s3_key"] = key
    store.put_packet(key, packet)
    store.put_case(case)
    store.put_ops(
        {
            "last_execution_arn": execution_arn,
            "last_status": "SUCCEEDED",
            "last_case_id": case_id,
            "last_at": generated_at,
            "last_s3_key": key,
            "relationship_count": len(relationships),
        }
    )
    return {
        "case": case,
        "packet": packet,
        "s3_key": key,
        "sha256": packet_sha,
        "execution_arn": execution_arn,
    }


def ingest_listing(listing: dict, store: Store | None = None) -> dict:
    store = store or get_store()
    if not listing.get("id"):
        listing = {**listing, "id": f"fix-{uuid.uuid4().hex[:6]}"}
    raw = json.dumps(listing, ensure_ascii=False, indent=2).encode("utf-8")
    digest = sha256_bytes(raw)
    existing = store.find_by_hash(digest)
    if existing:
        return existing

    captured = listing.get("captured_at") or utc_now()
    try:
        year_month = datetime.fromisoformat(captured.replace("Z", "+00:00"))
    except ValueError:
        year_month = datetime.now(timezone.utc)
    case_id = case_id_from_fixture(str(listing["id"]))
    key = f"raw/{year_month.year:04d}/{year_month.month:02d}/{listing['id']}.json"
    store.put_raw(key, raw)

    category = map_category(listing.get("category_hint"))
    case = {
        "id": case_id,
        "fixture_id": listing["id"],
        "title": listing.get("title") or case_id,
        "body": listing.get("body") or "",
        "category": category,
        "category_hint": listing.get("category_hint"),
        "tlp": listing.get("tlp") or "TLP:AMBER",
        "source": listing.get("source") or "fixture://unknown",
        "risk": 0,
        "entities": [],
        "raw_s3_key": key,
        "raw_sha256": digest,
        "cluster_id": None,
        "status": "open",
        "created_at": captured,
        "simulated": True,
        "disclaimer": DISCLAIMER,
        "meta": listing.get("meta") or {"simulated": True},
    }
    store.put_case(case)
    extract_enrich(case_id, store)
    return score_cluster(case_id, store)


def ingest_raw_key(key: str, store: Store | None = None) -> dict:
    store = store or get_store()
    raw = store.get_raw(key)
    listing = json.loads(raw.decode("utf-8"))
    digest = sha256_bytes(raw)
    existing = store.find_by_hash(digest)
    if existing:
        return existing
    return ingest_listing(listing, store)
