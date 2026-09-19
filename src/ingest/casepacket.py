"""
Shared CasePacket helpers — NER + risk scoring.
Risk weights load from YAML (CASEPACKET_RISK_RULES / config/risk_rules.yaml).
No case/listing content is hardcoded here.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
from datetime import datetime, timezone
from functools import lru_cache
from pathlib import Path
from typing import Any

EMAIL_RE = re.compile(r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+")
PHONE_RE = re.compile(r"(?:\+91[\s-]?)?[6-9]\d{9}")
URL_RE = re.compile(r"https?://[^\s<>\"']+")
HANDLE_RE = re.compile(r"(?<!\w)@[A-Za-z0-9_]{3,32}")
WALLET_RE = re.compile(r"\b(?:bc1|[13])[a-zA-HJ-NP-Z0-9]{25,62}\b|\b0x[a-fA-F0-9]{40}\b")


def _repo_root() -> Path:
    env = os.environ.get("CASEPACKET_ROOT")
    if env:
        return Path(env)
    # src/shared/casepacket.py → repo root
    return Path(__file__).resolve().parents[2]


@lru_cache(maxsize=1)
def load_risk_rules() -> dict[str, Any]:
    candidates: list[Path] = []
    env = os.environ.get("CASEPACKET_RISK_RULES")
    if env:
        candidates.append(Path(env))
    here = Path(__file__).resolve().parent
    candidates.append(here / "risk_rules.yaml")
    candidates.append(_repo_root() / "config" / "risk_rules.yaml")
    p = next((c for c in candidates if c.is_file()), None)
    if p is None:
        raise FileNotFoundError(f"risk rules not found; tried: {[str(c) for c in candidates]}")
    text = p.read_text(encoding="utf-8")
    try:
        import yaml  # type: ignore

        data = yaml.safe_load(text)
    except ImportError:
        # minimal YAML subset for our flat file (no PyYAML in Lambda by default)
        data = _parse_simple_risk_yaml(text)
    if not isinstance(data, dict):
        raise ValueError("risk_rules.yaml must be a mapping")
    return data


def _parse_simple_risk_yaml(text: str) -> dict[str, Any]:
    """Tiny parser for our risk_rules.yaml shape when PyYAML is absent."""
    out: dict[str, Any] = {"keywords": {}, "category_rules": {}}
    section = None
    for raw in text.splitlines():
        line = raw.split("#", 1)[0].rstrip()
        if not line.strip():
            continue
        if line.startswith(" ") and ":" in line:
            k, v = line.strip().split(":", 1)
            k, v = k.strip(), v.strip()
            if section == "keywords":
                out["keywords"][k] = int(v)
            elif section == "category_rules":
                out["category_rules"][k] = int(v)
            continue
        if line.endswith(":") and not line.startswith(" "):
            section = line[:-1].strip()
            continue
        if ":" in line and not line.startswith(" "):
            k, v = line.split(":", 1)
            out[k.strip()] = int(v.strip()) if v.strip().isdigit() else v.strip()
            section = None
    return out


def utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_text(text: str) -> str:
    return sha256_bytes(text.encode("utf-8"))


def extract_entities(text: str) -> list[dict[str, Any]]:
    found: list[dict[str, Any]] = []
    seen: set[tuple[str, str]] = set()

    def add(etype: str, value: str, confidence: float = 0.9) -> None:
        key = (etype, value.lower())
        if key in seen:
            return
        seen.add(key)
        found.append({"type": etype, "value": value, "confidence": confidence})

    for m in EMAIL_RE.findall(text):
        add("email", m)
    for m in PHONE_RE.findall(text):
        add("phone", re.sub(r"\s+", "", m))
    for m in URL_RE.findall(text):
        add("url", m.rstrip(".,)"))
    for m in HANDLE_RE.findall(text):
        add("handle", m)
    for m in WALLET_RE.findall(text):
        add("wallet", m)
    return found


def score_risk(text: str, entities: list[dict[str, Any]]) -> tuple[int, str]:
    rules = load_risk_rules()
    per = int(rules.get("entity_points_per_item", 8))
    cap = int(rules.get("entity_points_cap", 40))
    keywords = rules.get("keywords") or {}
    cats = rules.get("category_rules") or {}
    high_min = int(cats.get("high_min", 70))
    mid_min = int(cats.get("mid_min", 40))

    t = text.lower()
    score = min(cap, per * len(entities))
    for kw, pts in keywords.items():
        if str(kw).lower() in t:
            score += int(pts)
    score = max(0, min(100, score))
    if score >= high_min:
        cat = "credentials" if "credential" in t or "otp" in t else "fraud"
    elif score >= mid_min:
        cat = "docs" if "kyc" in t else "scam"
    else:
        cat = "other"
    if "category_hint" in rules:
        pass
    return score, cat


def require_simulated(doc: dict[str, Any]) -> None:
    if not doc.get("simulated", doc.get("meta", {}).get("simulated")):
        raise ValueError("document must set simulated=true (or meta.simulated)")


def ok_json(body: Any, status: int = 200, headers: dict | None = None) -> dict:
    h = {
        "content-type": "application/json",
        "access-control-allow-origin": os.environ.get("CORS_ORIGIN", "*"),
        "access-control-allow-headers": "content-type,x-api-key",
    }
    if headers:
        h.update(headers)
    return {"statusCode": status, "headers": h, "body": json.dumps(body)}


def check_api_key(event: dict) -> bool:
    expected = os.environ.get("CASEPACKET_API_KEY") or os.environ.get("DEMO_API_KEY") or ""
    if not expected:
        return True
    headers = {k.lower(): v for k, v in (event.get("headers") or {}).items()}
    return headers.get("x-api-key") == expected
