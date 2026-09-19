"""Deterministic CasePacket JSON compiler (STIX-lite + proof chain)."""

from __future__ import annotations

from datetime import datetime, timezone

from . import DISCLAIMER


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def rules_summary(case: dict) -> str:
    entities = case.get("entities") or []
    kinds = sorted({e["type"] for e in entities})
    kind_txt = ", ".join(kinds) if kinds else "no observables"
    links = case.get("linked_cases") or []
    return (
        f"Simulated {case.get('category', 'other')} listing "
        f"“{case.get('title', case['id'])}”. "
        f"Extracted {len(entities)} observables ({kind_txt}). "
        f"Cross-case links: {len(links)}. "
        f"Risk score {case.get('risk', 0)}/100. "
        f"{DISCLAIMER}."
    )


def _stix_pattern(entity: dict) -> str | None:
    value = entity["value"].replace("'", "\\'")
    mapping = {
        "email": f"[email-addr:value = '{value}']",
        "phone": f"[phone-number:value = '{value}']",
        "url": f"[url:value = '{value}']",
        "domain": f"[domain-name:value = '{value}']",
        "onion": f"[domain-name:value = '{value}']",
        "ip": f"[ipv4-addr:value = '{value}']",
        "wallet": f"[cryptocurrency-wallet:address = '{value}']",
        "handle": f"[user-account:display_name = '{value}']",
        "hash": f"[file:hashes.SHA256 = '{value}']" if len(value) == 64 else f"[file:hashes.'MD5/SHA1' = '{value}']",
        "cve": f"[vulnerability:name = '{value}']",
        "aadhaar": f"[x-casepacket-aadhaar:value = '{value}']",
        "pan": f"[x-casepacket-pan:value = '{value}']",
    }
    return mapping.get(entity["type"])


def to_stix_objects(case: dict) -> list[dict]:
    objects: list[dict] = []
    refs: list[str] = []
    for idx, entity in enumerate(case.get("entities") or [], start=1):
        pattern = _stix_pattern(entity)
        if not pattern:
            continue
        oid = entity.get("stix_id") or f"indicator--{case['id'].lower()}-{idx:02d}"
        objects.append(
            {
                "type": "indicator",
                "id": oid,
                "pattern": pattern,
                "pattern_type": "stix",
                "confidence": int(round(float(entity.get("confidence", 0.9)) * 100)),
            }
        )
        refs.append(oid)

    objects.append(
        {
            "type": "observed-data",
            "id": f"observed-data--{case['id'].lower()}",
            "number_observed": 1,
            "first_observed": case.get("created_at") or utc_now(),
            "object_refs": refs,
        }
    )
    objects.append(
        {
            "type": "report",
            "id": f"report--{case['id'].lower()}",
            "name": case.get("title") or case["id"],
            "published": utc_now(),
            "object_refs": refs,
            "labels": [case.get("category") or "other", "simulated"],
        }
    )
    return objects


def compile_packet(
    case: dict,
    *,
    linked_cases: list[dict],
    relationships: list[dict],
    proof_chain: list[dict],
    execution_arn: str,
    generated_at: str | None = None,
    enrichment: str = "rules",
    summary: str | None = None,
) -> dict:
    generated_at = generated_at or utc_now()
    case_view = {**case, "linked_cases": linked_cases}
    return {
        "packet_version": "1.1",
        "case_id": case["id"],
        "generated_at": generated_at,
        "tlp": case.get("tlp") or "TLP:AMBER",
        "summary": summary or case.get("summary") or rules_summary(case_view),
        "risk": {
            "score": case.get("risk", 0),
            "band": case.get("risk_band") or "low",
            "out_of_ten": case.get("risk_out_of_ten"),
            "factors": case.get("risk_factors") or [],
            "explain": case.get("explain") or {},
        },
        "category": case.get("category", "other"),
        "entities": case.get("entities") or [],
        "relationships": relationships,
        "linked_cases": linked_cases,
        "evidence": [
            {
                "kind": "raw",
                "s3": case.get("raw_s3_key"),
                "sha256": case.get("raw_sha256"),
                "source": case.get("source"),
                "captured_at": case.get("created_at"),
            }
        ],
        "timeline": case.get("timeline") or proof_chain,
        "proof_chain": proof_chain,
        "keyword_hits": case.get("keyword_hits") or [],
        "enrichment": enrichment,
        "chain_of_custody": [
            {
                "event": "ingest",
                "at": case.get("created_at") or generated_at,
                "s3": case.get("raw_s3_key"),
                "sha256": case.get("raw_sha256"),
            },
            {
                "event": "compile",
                "at": generated_at,
                "execution_arn": execution_arn,
            },
        ],
        "aws": {
            "execution_arn": execution_arn,
            "region": "ap-south-1",
            "packet_s3_key": case.get("packet_s3_key"),
        },
        "objects": to_stix_objects(case),
        "disclaimer": DISCLAIMER,
    }


def render_pdf_text(packet: dict) -> str:
    """Plain-text LE brief (print as PDF from browser)."""
    risk = packet.get("risk") or {}
    lines = [
        "CASEPACKET — LAW ENFORCEMENT CASE BRIEF",
        "=" * 52,
        f"CASE: {packet.get('case_id')}",
        f"TLP: {packet.get('tlp')}",
        f"GENERATED: {packet.get('generated_at')}",
        "",
        "EXECUTIVE SUMMARY",
        "-" * 52,
        str(packet.get("summary") or ""),
        "",
        "RISK ASSESSMENT",
        "-" * 52,
        f"Score: {risk.get('score')}/100 ({risk.get('band')}) · {risk.get('out_of_ten')}/10",
    ]
    for factor in risk.get("factors") or []:
        lines.append(f"  +{factor.get('points', 0):>3}  {factor.get('label')}")
    lines += ["", "KEY ENTITIES", "-" * 52]
    for ent in packet.get("entities") or []:
        lines.append(f"  [{ent.get('type')}] {ent.get('value')}  conf={ent.get('confidence')}")
    lines += ["", "LINKED CASES", "-" * 52]
    for link in packet.get("linked_cases") or []:
        lines.append(
            f"  {link.get('case_id')}  shared {link.get('shared_type')}={link.get('shared_value')}  {link.get('confidence')}%"
        )
    lines += ["", "EVIDENCE", "-" * 52]
    for ev in packet.get("evidence") or []:
        lines.append(f"  {ev.get('s3')}  sha256={ev.get('sha256')}")
    lines += ["", "PROOF CHAIN", "-" * 52]
    for step in packet.get("proof_chain") or []:
        lines.append(f"  {step.get('timestamp')}  {step.get('event')}  ({step.get('component')})")
    lines += ["", "CHAIN OF CUSTODY", "-" * 52]
    for step in packet.get("chain_of_custody") or []:
        lines.append(f"  {step}")
    aws = packet.get("aws") or {}
    lines += [
        "",
        "AWS EXECUTION",
        "-" * 52,
        f"  region: {aws.get('region')}",
        f"  arn: {aws.get('execution_arn')}",
        "",
        "DISCLAIMER",
        "-" * 52,
        packet.get("disclaimer") or DISCLAIMER,
        "",
    ]
    return "\n".join(lines)
