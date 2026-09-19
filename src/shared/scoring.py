"""Rule-based risk scoring with correlation-aware factors."""

from __future__ import annotations

from .ner import HIGH_VALUE_TYPES

KEYWORDS = {
    "aadhaar": 12,
    "kyc": 10,
    "otp": 10,
    "upi": 8,
    "dump": 12,
    "credential": 10,
    "password": 8,
    "wallet": 8,
    "mule": 14,
    "pan card": 10,
    "pan": 6,
    "passport": 10,
    "sim swap": 14,
    "phishing": 10,
    "cvv": 12,
    "fullz": 14,
    "leads": 6,
    "gst": 6,
    "imps": 8,
    "neft": 6,
    "ifsc": 6,
    "otp bot": 16,
    "fake police": 12,
    "cyber cell": 8,
    "refund": 5,
    "loan app": 8,
    "ransomware": 16,
    "malware": 12,
    "marketplace": 6,
    " intern": 4,
}

CATEGORY_BASE = {
    "fraud": 40,
    "credentials": 50,
    "docs": 45,
    "malware": 48,
    "ransomware": 55,
    "marketplace": 35,
    "other": 25,
}

ENTITY_WEIGHTS = {
    "phone": 6,
    "email": 5,
    "wallet": 10,
    "url": 4,
    "handle": 3,
    "domain": 5,
    "onion": 8,
    "ip": 4,
    "hash": 6,
    "cve": 5,
    "aadhaar": 10,
    "pan": 8,
}

TAXONOMY = {
    "docs": "docs",
    "kyc": "docs",
    "documents": "docs",
    "credentials": "credentials",
    "dump": "credentials",
    "fraud": "fraud",
    "scam": "fraud",
    "upi": "fraud",
    "malware": "malware",
    "ransomware": "ransomware",
    "marketplace": "marketplace",
    "other": "other",
}

FACTOR_KEYWORDS = {
    "Identity documents": {"aadhaar", "kyc", "pan", "pan card", "passport", "gst", "fake police"},
    "Data breach": {"dump", "credential", "password", "fullz", "cvv", "ifsc"},
    "Financial fraud": {"upi", "mule", "imps", "neft", "wallet", "refund", "loan app"},
    "Social engineering": {"otp", "otp bot", "phishing", "sim swap", "cyber cell", "leads"},
    "Malware / ransomware": {"ransomware", "malware", "cve"},
}


def map_category(hint: str | None) -> str:
    if not hint:
        return "other"
    key = hint.strip().lower()
    if key in CATEGORY_BASE:
        return key
    return TAXONOMY.get(key, "other")


def risk_band(risk: int) -> str:
    if risk >= 80:
        return "high"
    if risk >= 55:
        return "medium"
    return "low"


def source_label(source: str | None) -> str:
    raw = (source or "").lower()
    mapping = [
        ("market", "Market"),
        ("forum", "Forum"),
        ("telegram", "Telegram"),
        ("loan", "LoanApp"),
        ("voice", "Voice"),
        ("classif", "Classified"),
        ("campus", "Jobs"),
        ("job", "Jobs"),
        ("matrimony", "Social"),
        ("trade", "Trade"),
        ("fixture", "DarkWeb"),
        ("sim", "DarkWeb"),
    ]
    for needle, label in mapping:
        if needle in raw:
            return label
    return "Signal"


def _keyword_points(text: str) -> tuple[int, list[str]]:
    blob = (text or "").lower()
    hits: list[str] = []
    points = 0
    for word in sorted(KEYWORDS, key=len, reverse=True):
        if word in blob:
            hits.append(word.strip())
            points += KEYWORDS[word]
            blob = blob.replace(word, " ")
    return points, hits


def _entity_points(entities: list[dict]) -> int:
    points = 0
    for entity in entities or []:
        points += ENTITY_WEIGHTS.get(entity.get("type"), 2)
    high = sum(1 for e in entities or [] if e.get("type") in HIGH_VALUE_TYPES)
    if high >= 3:
        points += 8
    return points


def build_risk_factors(
    category: str,
    hits: list[str],
    entities: list[dict],
    explain: dict,
    correlation_bonus: int = 0,
) -> list[dict]:
    """Return display factors with absolute point contributions (Darkwolf-style)."""
    factors: list[dict] = []
    cat_pts = explain.get("base", CATEGORY_BASE.get(category, 25))
    factors.append({"label": f"Category · {category}", "points": cat_pts, "weight": 0})

    hit_set = {h.lower() for h in hits}
    for label, words in FACTOR_KEYWORDS.items():
        overlap = hit_set & words
        if overlap:
            pts = sum(KEYWORDS.get(w, 4) for w in overlap)
            factors.append({"label": label, "points": pts, "weight": 0, "hits": sorted(overlap)})

    ent_pts = explain.get("entities", 0)
    if ent_pts:
        factors.append({"label": "Entity density / sensitive IOCs", "points": ent_pts, "weight": 0})

    if correlation_bonus:
        factors.append({"label": "Cross-case correlation", "points": correlation_bonus, "weight": 0})

    factors.append({"label": "Source confidence (fixture)", "points": 5, "weight": 0})

    total = sum(f["points"] for f in factors) or 1
    for f in factors:
        f["weight"] = round(f["points"] / total, 2)
    factors.sort(key=lambda f: -f["points"])
    return factors


def score_case(
    title: str,
    body: str,
    category: str,
    entities: list[dict],
    *,
    correlation_bonus: int = 0,
) -> dict:
    category = map_category(category)
    base = CATEGORY_BASE.get(category, 25)
    text = f"{title or ''}\n{body or ''}"
    kw_points, hits = _keyword_points(text)
    ent_points = _entity_points(entities)
    source_conf = 5
    raw = base + kw_points + ent_points + correlation_bonus + source_conf
    # Soft ceiling: keep relative ranking visible even on dense fixtures.
    risk = max(0, min(100, int(round(raw * 0.92)) if raw > 90 else raw))
    explain = {
        "base": base,
        "keywords": kw_points,
        "entities": ent_points,
        "correlation": correlation_bonus,
        "source_confidence": source_conf,
    }
    return {
        "risk": risk,
        "risk_band": risk_band(risk),
        "risk_out_of_ten": round(risk / 10, 1),
        "category": category,
        "keyword_hits": hits,
        "explain": explain,
        "risk_factors": build_risk_factors(category, hits, entities or [], explain, correlation_bonus),
    }
