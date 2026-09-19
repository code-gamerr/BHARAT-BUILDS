"""API Gateway HTTP API (payload 2.0) — all analyst routes."""

from __future__ import annotations

import base64
import json
import os
import re
import sys
from pathlib import Path

SRC = Path(__file__).resolve().parents[1]
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from shared import DEFAULT_API_KEY  # noqa: E402
from shared.routes import (  # noqa: E402
    get_case,
    get_graph,
    get_packet,
    get_packet_pdf,
    health,
    ingest,
    list_cases,
    ops,
    start_packet,
)


def _response(status: int, body: dict | list, origin: str = "*") -> dict:
    return {
        "statusCode": status,
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": origin,
            "Access-Control-Allow-Headers": "content-type,x-api-key",
            "Access-Control-Allow-Methods": "GET,POST,OPTIONS",
        },
        "body": json.dumps(body),
    }


def _bytes_response(status: int, data: bytes, content_type: str, filename: str) -> dict:
    return {
        "statusCode": status,
        "headers": {
            "Content-Type": content_type,
            "Content-Disposition": f'attachment; filename="{filename}"',
            "Access-Control-Allow-Origin": "*",
        },
        "isBase64Encoded": True,
        "body": base64.b64encode(data).decode("ascii"),
    }


def _authorized(event: dict, path: str) -> bool:
    if path == "/healthz" or event.get("requestContext", {}).get("http", {}).get("method") == "OPTIONS":
        return True
    headers = {k.lower(): v for k, v in (event.get("headers") or {}).items()}
    expected = os.environ.get("DEMO_API_KEY") or DEFAULT_API_KEY
    return headers.get("x-api-key") == expected


def lambda_handler(event, context):
    http = event.get("requestContext", {}).get("http", {})
    method = (http.get("method") or "GET").upper()
    path = event.get("rawPath") or http.get("path") or "/"
    origin = "*"

    if method == "OPTIONS":
        return _response(200, {"ok": True}, origin)

    if not _authorized(event, path):
        return _response(401, {"error": "unauthorized"})

    body = event.get("body")
    if event.get("isBase64Encoded") and body:
        body = base64.b64decode(body).decode("utf-8")
    payload = json.loads(body) if body else {}

    if method == "GET" and path == "/healthz":
        return _response(*health())
    if method == "GET" and path == "/ops":
        return _response(*ops())
    if method == "GET" and path == "/graph":
        return _response(*get_graph())
    if method == "GET" and path == "/cases":
        return _response(*list_cases())
    if method == "POST" and path == "/ingest":
        return _response(*ingest(payload))

    case_pdf = re.fullmatch(r"/cases/([^/]+)/packet/pdf", path)
    case_packet = re.fullmatch(r"/cases/([^/]+)/packet", path)
    case_only = re.fullmatch(r"/cases/([^/]+)", path)
    if case_pdf and method == "GET":
        result = get_packet_pdf(case_pdf.group(1))
        if len(result) == 3:
            return _bytes_response(result[0], result[1], result[2], f"{case_pdf.group(1)}-brief.txt")
        return _response(*result)
    if case_packet:
        case_id = case_packet.group(1)
        if method == "POST":
            return _response(*start_packet(case_id))
        if method == "GET":
            return _response(*get_packet(case_id))
    if case_only and method == "GET":
        return _response(*get_case(case_only.group(1)))

    return _response(404, {"error": "not_found", "path": path})
