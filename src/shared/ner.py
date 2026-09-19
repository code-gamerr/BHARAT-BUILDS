"""Night-Watch–inspired IOC extractor (safe fixture subset). No live crawl."""

from __future__ import annotations

import hashlib
import re
from typing import Iterable
from urllib.parse import urlparse

EMAIL_RE = re.compile(r"\b[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[A-Za-z]{2,24}\b")
PHONE_RE = re.compile(r"(?:(?:\+91|91)[\s-]?)?(?:[6-9]\d{9}|[6-9]\d{4}[\s-]\d{5})")
URL_RE = re.compile(r"https?://[^\s\]\"'<>]+", re.IGNORECASE)
ONION_RE = re.compile(r"\b[a-z2-7]{16,56}\.onion\b", re.IGNORECASE)
DOMAIN_RE = re.compile(
    r"\b(?:[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.)+(?:invalid|example|sim|test|local|onion)\b",
    re.IGNORECASE,
)
IP_RE = re.compile(r"\b(?:(?:25[0-5]|2[0-4]\d|[01]?\d\d?)\.){3}(?:25[0-5]|2[0-4]\d|[01]?\d\d?)\b")
ETH_RE = re.compile(r"\b0x[a-fA-F0-9]{40}\b")
BTC_RE = re.compile(r"\b[13][a-km-zA-HJ-NP-Z1-9]{25,34}\b")
WALLET_LIKE_RE = re.compile(r"\b(?:1Fake|bc1q|XMR)[A-Za-z0-9]{16,60}\b")
HANDLE_RE = re.compile(r"(?<![\w.])@[A-Za-z][A-Za-z0-9_]{2,20}\b")
HASH_RE = re.compile(r"\b[a-fA-F0-9]{32}\b|\b[a-fA-F0-9]{40}\b|\b[a-fA-F0-9]{64}\b")
CVE_RE = re.compile(r"\bCVE-\d{4}-\d{4,7}\b", re.IGNORECASE)
# Obviously synthetic Indian ID patterns for fixtures only
AADHAAR_RE = re.compile(r"\b(?:SIM-AADHAAR|FAKE-AADHAAR)[- ]?\d{4}[- ]?\d{4}[- ]?\d{4}\b", re.IGNORECASE)
PAN_RE = re.compile(r"\b(?:SIM|FAKE)[A-Z]{3}[A-Z]P\d{4}[A-Z]\b")

HIGH_VALUE_TYPES = frozenset({"phone", "email", "wallet", "onion", "aadhaar", "pan"})

PLACEHOLDER_HOSTS = frozenset(
    {
        "example.invalid",
        "example.com",
        "example.org",
        "example.net",
        "invalid",
        "localhost",
        "test",
        "local",
    }
)

EXACT_SCORE = {
    "phone": 40,
    "email": 40,
    "wallet": 35,
    "domain": 30,
    "onion": 30,
    "handle": 25,
    "url": 20,
    "ip": 20,
    "hash": 25,
    "cve": 15,
    "aadhaar": 40,
    "pan": 35,
}


def _dedupe(items: Iterable[dict]) -> list[dict]:
    seen: set[tuple[str, str]] = set()
    out: list[dict] = []
    for item in items:
        key = (item["type"], item["value"].lower())
        if key in seen:
            continue
        seen.add(key)
        out.append(item)
    return out


def normalize_phone(raw: str) -> str:
    digits = re.sub(r"\D", "", raw)
    if digits.startswith("91") and len(digits) == 12:
        digits = digits[2:]
    if len(digits) == 10:
        return f"+91-{digits[:5]}-{digits[5:]}"
    return raw.strip()


def normalize_entity(entity_type: str, value: str) -> str:
    value = value.strip().rstrip(".,);")
    if entity_type == "phone":
        return normalize_phone(value)
    if entity_type in {"email", "handle", "domain", "onion"}:
        return value.lower()
    if entity_type == "url":
        return value.rstrip(").,]")
    if entity_type == "cve":
        return value.upper()
    return value


def stix_id_for(entity_type: str, value: str) -> str:
    digest = hashlib.sha256(f"{entity_type}:{value.lower()}".encode()).hexdigest()[:16]
    return f"indicator--{entity_type}-{digest}"


def enrich_entity(entity: dict, *, source: str, seen_at: str) -> dict:
    etype = entity["type"]
    value = normalize_entity(etype, entity["value"])
    return {
        **entity,
        "type": etype,
        "value": value,
        "confidence": float(entity.get("confidence") or 0.9),
        "first_seen": entity.get("first_seen") or seen_at,
        "last_seen": seen_at,
        "source": source,
        "stix_id": entity.get("stix_id") or stix_id_for(etype, value),
    }


def _is_placeholder_host(host: str) -> bool:
    host = (host or "").lower().rstrip(".")
    if host in PLACEHOLDER_HOSTS:
        return True
    if host.endswith(".invalid") or host.endswith(".example") or host.endswith(".test") or host.endswith(".local"):
        # Keep sim.casepacket.invalid as a real fixture domain signal.
        if host.endswith("casepacket.invalid"):
            return False
        # Bare example.invalid / foo.example.com style placeholders
        labels = host.split(".")
        if labels[-1] in {"invalid", "example", "test", "local"} and labels[0] in {
            "example",
            "test",
            "foo",
            "bar",
            "mail",
            "email",
        }:
            return True
        if host in {"example.invalid", "test.invalid"}:
            return True
        # Email provider style: seller@example.invalid → example.invalid
        if len(labels) == 2 and labels[0] == "example":
            return True
    return False


def _add(found: list[dict], etype: str, raw: str, confidence: float) -> None:
    value = normalize_entity(etype, raw)
    if etype in {"domain", "onion"} and _is_placeholder_host(value):
        return
    found.append(
        {
            "type": etype,
            "value": value,
            "confidence": confidence,
        }
    )


def extract_entities(text: str, *, source: str = "fixture://unknown", seen_at: str | None = None) -> list[dict]:
    """Return OpenCTI-style observable maps from free text."""
    from .packet import utc_now

    blob = text or ""
    found: list[dict] = []
    seen_at = seen_at or utc_now()

    for match in EMAIL_RE.finditer(blob):
        _add(found, "email", match.group(0), 0.97)
    for match in PHONE_RE.finditer(blob):
        _add(found, "phone", match.group(0), 0.95)
    for match in URL_RE.finditer(blob):
        url = match.group(0).rstrip(").,]")
        _add(found, "url", url, 0.93)
        host = urlparse(url).hostname
        if host:
            if host.endswith(".onion"):
                _add(found, "onion", host, 0.94)
            elif not _is_placeholder_host(host):
                _add(found, "domain", host, 0.9)
    for match in ONION_RE.finditer(blob):
        _add(found, "onion", match.group(0), 0.94)
    for match in DOMAIN_RE.finditer(blob):
        host = match.group(0).lower()
        if "@" in host:
            continue
        if host.endswith(".onion"):
            _add(found, "onion", host, 0.94)
        else:
            _add(found, "domain", host, 0.88)
    for match in IP_RE.finditer(blob):
        ip = match.group(0)
        # Skip fake phone-looking fragments already captured
        if not ip.startswith("0."):
            _add(found, "ip", ip, 0.85)
    for match in ETH_RE.finditer(blob):
        _add(found, "wallet", match.group(0), 0.92)
    for match in WALLET_LIKE_RE.finditer(blob):
        _add(found, "wallet", match.group(0), 0.88)
    for match in BTC_RE.finditer(blob):
        value = match.group(0)
        if any(ch.isdigit() for ch in value):
            _add(found, "wallet", value, 0.82)
    for match in HANDLE_RE.finditer(blob):
        _add(found, "handle", match.group(0), 0.9)
    for match in CVE_RE.finditer(blob):
        _add(found, "cve", match.group(0), 0.95)
    for match in AADHAAR_RE.finditer(blob):
        _add(found, "aadhaar", match.group(0).upper(), 0.9)
    for match in PAN_RE.finditer(blob):
        _add(found, "pan", match.group(0).upper(), 0.9)
    # Hashes last; avoid eating wallets/ETH
    wallet_vals = {e["value"].lower() for e in found if e["type"] == "wallet"}
    for match in HASH_RE.finditer(blob):
        value = match.group(0)
        if value.lower() in wallet_vals or value.lower().startswith("0x"):
            continue
        if len(value) in {32, 40, 64}:
            _add(found, "hash", value.lower(), 0.8)

    return [enrich_entity(e, source=source, seen_at=seen_at) for e in _dedupe(found)]
