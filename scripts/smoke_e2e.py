#!/usr/bin/env python3
"""End-to-end smoke: health → cases → packet → download. No hardcoded cases."""
from __future__ import annotations

import json
import os
import sys
import urllib.error
import urllib.request

BASE = os.environ.get("CASEPACKET_API", "http://127.0.0.1:8000").rstrip("/")
KEY = os.environ.get("CASEPACKET_API_KEY", "")


def req(path: str, method: str = "GET", data: bytes | None = None) -> tuple[int, dict | list | str]:
    headers = {"content-type": "application/json"}
    if KEY:
        headers["x-api-key"] = KEY
    r = urllib.request.Request(BASE + path, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(r, timeout=30) as resp:
            raw = resp.read().decode()
            try:
                return resp.status, json.loads(raw)
            except json.JSONDecodeError:
                return resp.status, raw
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode()


def main() -> int:
    code, health = req("/healthz")
    assert code == 200 and isinstance(health, dict) and health.get("status") == "ok", health
    print("health", health.get("cases"), health.get("mode"))

    code, seed = req("/seed", "POST", b"{}")
    assert code == 200 and isinstance(seed, dict), seed
    print("seeded", seed.get("seeded"))

    code, cases = req("/cases")
    assert code == 200 and isinstance(cases, list) and len(cases) >= 1, cases
    case_id = cases[0]["id"]
    print("top case", case_id, "risk", cases[0].get("risk"))

    code, detail = req(f"/cases/{case_id}")
    assert code == 200 and isinstance(detail, dict), detail
    print("entities", len(detail.get("entities") or []))

    code, started = req(f"/cases/{case_id}/packet", "POST", b"{}")
    assert code == 200 and isinstance(started, dict), started
    print("compile", started.get("status") or started.get("executionArn"))

    code, packet = req(f"/cases/{case_id}/packet")
    assert code == 200 and isinstance(packet, dict) and packet.get("downloadUrl"), packet
    print("packet", packet.get("sha256", "")[:16], "…")

    code, body = req(f"/cases/{case_id}/packet/download")
    assert code == 200 and ("packet_version" in str(body) or isinstance(body, dict)), body
    print("download ok")
    print("E2E PASS")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except AssertionError as e:
        print("E2E FAIL", e, file=sys.stderr)
        raise SystemExit(1)
    except Exception as e:
        print("E2E FAIL", e, file=sys.stderr)
        raise SystemExit(1)
