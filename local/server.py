"""
Local CasePacket API — no AWS required.
All case data loaded from fixtures/ or POST /ingest (nothing hardcoded).
"""
from __future__ import annotations

import json
import os
import re
import sys
import uuid
from pathlib import Path
from typing import Any

from fastapi import FastAPI, Header, HTTPException
from fastapi.middleware.cors import CORSMiddleware

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src" / "shared"))

from casepacket import (  # noqa: E402
    extract_entities,
    require_simulated,
    score_risk,
    sha256_text,
    utc_now,
)

FIXTURES = Path(os.environ.get("CASEPACKET_FIXTURES_DIR", ROOT / "fixtures"))
DATA = Path(os.environ.get("CASEPACKET_DATA_DIR", ROOT / "data"))
STORE = DATA / "cases.json"
PACKETS = (DATA / "packets").resolve()
API_KEY = os.environ.get("CASEPACKET_API_KEY", "")
ALLOW_ANON = os.environ.get("CASEPACKET_ALLOW_ANON", "1") == "1"
CASE_ID_RE = re.compile(r"^[A-Za-z0-9._-]{1,64}$")

app = FastAPI(title="CasePacket Local", version="0.2.0")
_cors = [o.strip() for o in os.environ.get("CORS_ORIGIN", "*").split(",") if o.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors,
    allow_credentials=False if _cors == ["*"] else True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def _safe_case_id(raw: str) -> str:
    if not CASE_ID_RE.match(raw):
        raise HTTPException(400, detail={"error": "invalid_case_id"})
    return raw


def _packet_path(case_id: str) -> Path:
    path = (PACKETS / f"{case_id}.json").resolve()
    if not path.is_relative_to(PACKETS):
        raise HTTPException(400, detail={"error": "invalid_path"})
    return path


def _load_store() -> dict[str, Any]:
    if not STORE.is_file():
        return {"cases": {}}
    return json.loads(STORE.read_text(encoding="utf-8"))


def _save_store(store: dict[str, Any]) -> None:
    DATA.mkdir(parents=True, exist_ok=True)
    STORE.write_text(json.dumps(store, indent=2, ensure_ascii=False), encoding="utf-8")


def _auth(x_api_key: str | None) -> None:
    if not API_KEY:
        if ALLOW_ANON:
            return
        raise HTTPException(401, detail={"error": "api_key_required", "code": "AUTH"})
    if x_api_key != API_KEY:
        raise HTTPException(401, detail={"error": "unauthorized", "code": "AUTH"})


def _ingest_doc(doc: dict[str, Any], store: dict[str, Any]) -> dict[str, Any]:
    require_simulated(doc)
    raw_id = str(doc.get("id") or f"fx-{uuid.uuid4().hex[:8]}")
    if not CASE_ID_RE.match(raw_id):
        raise ValueError("invalid case id")
    case_id = raw_id
    body = f"{doc.get('title', '')}\n{doc.get('body', '')}"
    ents = extract_entities(body)
    risk, cat = score_risk(body, ents)
    # cluster by first high-value entity across store
    cluster_id = None
    for e in ents:
        if e["type"] in ("email", "phone", "wallet"):
            cluster_id = f"CLU-{sha256_text(e['value'])[:10]}"
            break
    case = {
        "case_id": case_id,
        "title": doc.get("title", case_id),
        "body": doc.get("body", ""),
        "risk": risk,
        "ml_risk": risk,
        "category": doc.get("category_hint") or cat,
        "raw_sha256": sha256_text(body),
        "tlp": doc.get("tlp", "TLP:AMBER"),
        "status": "open",
        "simulated": True,
        "created_at": doc.get("captured_at") or utc_now(),
        "cluster_id": cluster_id,
        "entities": ents,
        "source": doc.get("source"),
        "packet_path": None,
        "packet_sha256": None,
        "execution_arn": None,
    }
    store.setdefault("cases", {})[case_id] = case
    return case


def seed_from_fixtures(store: dict[str, Any] | None = None) -> int:
    store = store if store is not None else _load_store()
    if not FIXTURES.is_dir():
        raise FileNotFoundError(f"fixtures dir missing: {FIXTURES}")
    n = 0
    for path in sorted(FIXTURES.glob("*.json")):
        doc = json.loads(path.read_text(encoding="utf-8"))
        _ingest_doc(doc, store)
        n += 1
    _save_store(store)
    return n


@app.on_event("startup")
def startup() -> None:
    DATA.mkdir(parents=True, exist_ok=True)
    PACKETS.mkdir(parents=True, exist_ok=True)
    store = _load_store()
    if not store.get("cases") and FIXTURES.is_dir():
        seed_from_fixtures(store)


@app.get("/healthz")
def healthz():
    store = _load_store()
    return {
        "status": "ok",
        "version": "0.2.0",
        "product": "CasePacket",
        "mode": "local",
        "cases": len(store.get("cases", {})),
        "fixtures_dir": str(FIXTURES),
        "data_dir": str(DATA),
        "api_key_required": bool(API_KEY),
        "disclaimer": "Data from fixtures/ingest only — configure paths via env",
    }


@app.post("/seed")
def seed(x_api_key: str | None = Header(default=None)):
    _auth(x_api_key)
    store: dict[str, Any] = {"cases": {}}
    n = seed_from_fixtures(store)
    return {"seeded": n, "cases": n}


@app.get("/cases")
def list_cases(x_api_key: str | None = Header(default=None)):
    _auth(x_api_key)
    store = _load_store()
    rows = []
    for c in store.get("cases", {}).values():
        rows.append(
            {
                "id": c["case_id"],
                "title": c["title"],
                "risk": c["risk"],
                "ml_risk": c.get("ml_risk", c["risk"]),
                "category": c.get("category"),
                "cluster_id": c.get("cluster_id"),
                "created_at": c.get("created_at"),
                "status": c.get("status"),
            }
        )
    rows.sort(key=lambda x: int(x.get("risk") or 0), reverse=True)
    return rows


@app.get("/cases/{case_id}")
def get_case(case_id: str, x_api_key: str | None = Header(default=None)):
    _auth(x_api_key)
    case_id = _safe_case_id(case_id)
    store = _load_store()
    c = store.get("cases", {}).get(case_id)
    if not c:
        raise HTTPException(404, detail={"error": "not_found"})
    out = dict(c)
    cid = c.get("cluster_id")
    out["linked_case_ids"] = [
        oid
        for oid, oc in store.get("cases", {}).items()
        if oid != case_id and cid and oc.get("cluster_id") == cid
    ]
    return out


@app.post("/ingest")
def ingest(doc: dict[str, Any], x_api_key: str | None = Header(default=None)):
    _auth(x_api_key)
    store = _load_store()
    try:
        case = _ingest_doc(doc, store)
    except ValueError as e:
        raise HTTPException(400, detail={"error": str(e)}) from e
    _save_store(store)
    return {
        "case_id": case["case_id"],
        "risk": case["risk"],
        "entities": case["entities"],
    }


@app.post("/cases/{case_id}/packet")
def start_packet(case_id: str, x_api_key: str | None = Header(default=None)):
    _auth(x_api_key)
    case_id = _safe_case_id(case_id)
    store = _load_store()
    c = store.get("cases", {}).get(case_id)
    if not c:
        raise HTTPException(404, detail={"error": "not_found"})

    entities = c.get("entities") or []
    findings = [
        {
            "id": f"F-{i+1}",
            "severity": "medium" if c.get("risk", 0) >= 50 else "low",
            "title": f"Entity {e['type']}",
            "detail": e["value"],
            "verified": True,
        }
        for i, e in enumerate(entities)
    ]
    objects = []
    for e in entities:
        if e["type"] == "email":
            objects.append({"type": "indicator", "pattern": f"[email-addr:value = '{e['value']}']"})
        elif e["type"] == "phone":
            objects.append({"type": "indicator", "pattern": f"[phone-number:value = '{e['value']}']"})
        elif e["type"] == "wallet":
            objects.append({"type": "indicator", "pattern": f"[crypto:address = '{e['value']}']"})

    execution = f"local:compile:{case_id}:{uuid.uuid4().hex[:8]}"
    packet = {
        "packet_version": "1.0",
        "case_id": case_id,
        "generated_at": utc_now(),
        "tlp": c.get("tlp", "TLP:AMBER"),
        "summary": f"Triage for '{c.get('title')}'. Risk={c.get('risk')}.",
        "risk": int(c.get("risk", 0)),
        "entities": entities,
        "findings": findings,
        "linked_case_ids": [
            oid
            for oid, oc in store.get("cases", {}).items()
            if oid != case_id and oc.get("cluster_id") and oc.get("cluster_id") == c.get("cluster_id")
        ],
        "chain_of_custody": [
            {"event": "ingest", "at": c.get("created_at"), "sha256": c.get("raw_sha256")},
            {"event": "compile", "at": utc_now(), "execution_arn": execution},
        ],
        "objects": objects,
        "ml": {
            "extractor": "regex",
            "ranker": "rules",
            "group_size": 13,
            "train_prompts": 20,
            "rules_file": str(ROOT / "config" / "risk_rules.yaml"),
            "rules_risk": int(c.get("risk", 0)),
            "ml_risk": int(c.get("ml_risk", c.get("risk", 0))),
            "final_risk": int(c.get("risk", 0)),
            "enrichment": "rules",
        },
        "disclaimer": "SIMULATED FIXTURE DATA — NOT OPERATIONAL INTEL",
    }
    PACKETS.mkdir(parents=True, exist_ok=True)
    out = _packet_path(case_id)
    raw = json.dumps(packet, indent=2, ensure_ascii=False).encode("utf-8")
    out.write_bytes(raw)
    digest = sha256_text(raw.decode("utf-8"))
    c["status"] = "packet_ready"
    c["packet_path"] = str(out)
    c["packet_sha256"] = digest
    c["execution_arn"] = execution
    store["cases"][case_id] = c
    _save_store(store)
    return {"executionArn": execution, "case_id": case_id, "status": "packet_ready"}


@app.get("/cases/{case_id}/packet")
def get_packet(case_id: str, x_api_key: str | None = Header(default=None)):
    _auth(x_api_key)
    case_id = _safe_case_id(case_id)
    store = _load_store()
    c = store.get("cases", {}).get(case_id)
    if not c:
        raise HTTPException(404, detail={"error": "not_found"})
    path = _packet_path(case_id)
    if not path.is_file():
        return {"status": c.get("status", "open"), "downloadUrl": None}
    return {
        "status": c.get("status"),
        "downloadUrl": f"/cases/{case_id}/packet/download",
        "sha256": c.get("packet_sha256"),
        "execution_arn": c.get("execution_arn"),
        "local_path": str(path),
    }


@app.get("/cases/{case_id}/packet/download")
def download_packet(case_id: str, x_api_key: str | None = Header(default=None)):
    _auth(x_api_key)
    from fastapi.responses import FileResponse

    case_id = _safe_case_id(case_id)
    store = _load_store()
    c = store.get("cases", {}).get(case_id)
    if not c:
        raise HTTPException(404, detail={"error": "not_found"})
    path = _packet_path(case_id)
    if not path.is_file():
        raise HTTPException(404, detail={"error": "not_found"})
    return FileResponse(path, media_type="application/json", filename=f"{case_id}.json")
