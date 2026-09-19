"""MISP-inspired correlation: shared observables → scored relationships."""

from __future__ import annotations

from collections import defaultdict
from datetime import datetime

from .ner import EXACT_SCORE, HIGH_VALUE_TYPES, normalize_entity


def _parse_ts(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None


def _hours_apart(a: str | None, b: str | None) -> float | None:
    da, db = _parse_ts(a), _parse_ts(b)
    if not da or not db:
        return None
    return abs((da - db).total_seconds()) / 3600.0


def entity_key(entity: dict) -> tuple[str, str] | None:
    etype = entity.get("type")
    value = entity.get("value")
    if not etype or not value:
        return None
    return etype, normalize_entity(etype, value)


def build_relationships(cases: list[dict]) -> list[dict]:
    """Create OpenCTI-style shared_with edges between cases."""
    index: dict[tuple[str, str], list[dict]] = defaultdict(list)
    by_id = {c["id"]: c for c in cases}

    for case in cases:
        for entity in case.get("entities") or []:
            key = entity_key(entity)
            if not key:
                continue
            index[key].append(
                {
                    "case_id": case["id"],
                    "entity": entity,
                    "source": case.get("source"),
                    "category": case.get("category"),
                    "created_at": case.get("created_at"),
                }
            )

    relationships: list[dict] = []
    seen_pairs: set[tuple[str, str, str, str]] = set()

    for (etype, value), holders in index.items():
        if len(holders) < 2:
            continue
        base = EXACT_SCORE.get(etype, 15)
        for i, left in enumerate(holders):
            for right in holders[i + 1 :]:
                a, b = sorted([left["case_id"], right["case_id"]])
                pair = (a, b, etype, value.lower())
                if pair in seen_pairs:
                    continue
                seen_pairs.add(pair)

                score = base
                reasons = [f"exact {etype}"]
                if left.get("source") and left.get("source") == right.get("source"):
                    score += 10
                    reasons.append("same source")
                if left.get("category") and left.get("category") == right.get("category"):
                    score += 5
                    reasons.append("same category")
                hours = _hours_apart(left.get("created_at"), right.get("created_at"))
                if hours is not None and hours <= 48:
                    score += 5
                    reasons.append("temporal proximity")

                confidence = min(99, score)
                left_ent = left["entity"] if left["case_id"] == a else right["entity"]
                relationships.append(
                    {
                        "source_case": a,
                        "target_case": b,
                        "source_entity": {"type": etype, "value": value, "stix_id": left_ent.get("stix_id")},
                        "target_entity": {"type": etype, "value": value},
                        "relationship_type": "shared_with",
                        "confidence": confidence,
                        "reasons": reasons,
                        "evidence_ids": [by_id[a].get("raw_sha256"), by_id[b].get("raw_sha256")],
                    }
                )
    relationships.sort(key=lambda r: -r["confidence"])
    return relationships


def linked_for_case(case_id: str, relationships: list[dict]) -> list[dict]:
    """Return ranked linked cases with shared entity + confidence %."""
    best: dict[str, dict] = {}
    for rel in relationships:
        other = None
        if rel["source_case"] == case_id:
            other = rel["target_case"]
        elif rel["target_case"] == case_id:
            other = rel["source_case"]
        if not other:
            continue
        current = best.get(other)
        if not current or rel["confidence"] > current["confidence"]:
            best[other] = {
                "case_id": other,
                "relationship_type": rel["relationship_type"],
                "shared_type": rel["source_entity"]["type"],
                "shared_value": rel["source_entity"]["value"],
                "confidence": rel["confidence"],
                "reasons": rel["reasons"],
            }
    return sorted(best.values(), key=lambda x: -x["confidence"])


def correlation_bonus(case_id: str, relationships: list[dict]) -> int:
    links = linked_for_case(case_id, relationships)
    if not links:
        return 0
    # Cap so correlation informs risk without collapsing everything to 100.
    return min(12, 3 * min(len(links), 3) + max(0, (links[0]["confidence"] - 75) // 10))


def refresh_clusters(cases: list[dict], relationships: list[dict] | None = None) -> dict[str, str]:
    """Cluster IDs from high-value shared entities (compat with prior API)."""
    import hashlib
    from collections import defaultdict

    relationships = relationships if relationships is not None else build_relationships(cases)
    parent: dict[str, str] = {c["id"]: c["id"] for c in cases}

    def find(x: str) -> str:
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    def union(a: str, b: str) -> None:
        ra, rb = find(a), find(b)
        if ra != rb:
            parent[rb] = ra

    for rel in relationships:
        if rel["source_entity"]["type"] in HIGH_VALUE_TYPES and rel["confidence"] >= 40:
            union(rel["source_case"], rel["target_case"])

    groups: dict[str, list[str]] = defaultdict(list)
    for case in cases:
        groups[find(case["id"])].append(case["id"])

    mapping: dict[str, str] = {}
    for members in groups.values():
        if len(members) < 2:
            continue
        digest = hashlib.sha256("|".join(sorted(members)).encode()).hexdigest()[:6].upper()
        cluster_id = f"CL-{digest}"
        for member in members:
            mapping[member] = cluster_id
    return mapping


def graph_payload(cases: list[dict], relationships: list[dict]) -> dict:
    nodes = []
    for case in cases:
        nodes.append(
            {
                "id": case["id"],
                "kind": "case",
                "label": case["id"].replace("CASE-", "C-"),
                "risk": case.get("risk", 0),
                "title": case.get("title"),
            }
        )
    entity_nodes: dict[str, dict] = {}
    edges = []
    for rel in relationships:
        eid = f"ENT::{rel['source_entity']['type']}::{rel['source_entity']['value'].lower()}"
        if eid not in entity_nodes:
            entity_nodes[eid] = {
                "id": eid,
                "kind": "entity",
                "type": rel["source_entity"]["type"],
                "label": rel["source_entity"]["value"],
                "confidence": rel["confidence"],
            }
        edges.append(
            {
                "from": rel["source_case"],
                "to": eid,
                "confidence": rel["confidence"],
                "type": "observes",
            }
        )
        edges.append(
            {
                "from": eid,
                "to": rel["target_case"],
                "confidence": rel["confidence"],
                "type": "shared_with",
            }
        )
    nodes.extend(entity_nodes.values())
    return {"nodes": nodes, "edges": edges, "relationship_count": len(relationships)}
