"""Bedrock RFT reward Lambda — GRPO preference for LE triage briefs (docs/ml.md)."""
from __future__ import annotations

import json
import re
from typing import Any

HYPE = re.compile(
    r"guaranteed\s+hack|real\s+\.onion|how\s+to\s+phish|buy\s+ransomware",
    re.I,
)
RISK_RE = re.compile(r"\brisk\b|\bTLP\b|\bHIGH\b|\bMEDIUM\b|\bLOW\b|\b\d{1,3}/100\b", re.I)
WORD_RE = re.compile(r"\b\w+\b")


def _text_from_event(event: dict[str, Any]) -> str:
    if isinstance(event.get("output"), str):
        return event["output"]
    if isinstance(event.get("completion"), str):
        return event["completion"]
    if isinstance(event.get("response"), str):
        return event["response"]
    for key in ("outputs", "candidates", "completions"):
        vals = event.get(key)
        if isinstance(vals, list) and vals:
            first = vals[0]
            if isinstance(first, str):
                return first
            if isinstance(first, dict):
                return str(first.get("text") or first.get("content") or first)
    return json.dumps(event)[:4000]


def _entities_from_event(event: dict[str, Any]) -> list[str]:
    ents: list[str] = []
    for key in ("entities", "reference_entities", "ground_truth_entities"):
        raw = event.get(key)
        if isinstance(raw, list):
            for e in raw:
                if isinstance(e, str):
                    ents.append(e)
                elif isinstance(e, dict) and e.get("value"):
                    ents.append(str(e["value"]))
    prompt = str(event.get("prompt") or event.get("input") or "")
    if "ENTITIES:" in prompt:
        part = prompt.split("ENTITIES:", 1)[1].split("\n", 1)[0]
        ents.extend([x.strip() for x in part.split(",") if x.strip()])
    return ents


def score_brief(text: str, entities: list[str] | None = None) -> float:
    entities = entities or []
    if not text.strip():
        return 0.0
    score = 0.0
    upper = text.upper()
    if "SIMULATED" in upper or "TLP" in upper:
        score += 2.0
    if any(e and str(e).lower() in text.lower() for e in entities):
        score += 2.0
    if RISK_RE.search(text):
        score += 2.0
    if 40 <= len(WORD_RE.findall(text)) <= 120:
        score += 1.0
    if HYPE.search(text):
        score -= 5.0
    return float(score)


def handler(event, context):
    if isinstance(event, str):
        event = json.loads(event)

    if isinstance(event.get("candidates"), list):
        ents = _entities_from_event(event)
        scores = [
            score_brief(
                c if isinstance(c, str) else str(c.get("text") or c.get("content") or ""),
                ents,
            )
            for c in event["candidates"]
        ]
        return {"scores": scores, "score": scores[0] if scores else 0.0}

    text = _text_from_event(event)
    return {"score": score_brief(text, _entities_from_event(event))}
