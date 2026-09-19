"""Zero-dependency local API for the CasePacket console."""

from __future__ import annotations

import json
import os
import sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

os.environ.setdefault("CASEPACKET_LOCAL", "1")
os.environ.setdefault("DEMO_API_KEY", "casepacket-demo-key")
os.environ.setdefault("PUBLIC_BASE_URL", "http://127.0.0.1:8080")

from shared import DEFAULT_API_KEY  # noqa: E402
from shared.routes import (  # noqa: E402
    download_local,
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

PORT = int(os.environ.get("PORT", "8080"))


class Handler(BaseHTTPRequestHandler):
    server_version = "CasePacketLocal/1.0"

    def log_message(self, fmt: str, *args) -> None:
        sys.stderr.write("%s - %s\n" % (self.address_string(), fmt % args))

    def _cors(self) -> None:
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Headers", "content-type,x-api-key")
        self.send_header("Access-Control-Allow-Methods", "GET,POST,OPTIONS")

    def _json(self, status: int, payload: dict | list) -> None:
        body = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self._cors()
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _bytes(self, status: int, data: bytes, content_type: str, disposition: str = "attachment") -> None:
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Disposition", disposition)
        self._cors()
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def _auth_ok(self, path: str) -> bool:
        if path in {"/healthz", "/", "/favicon.ico"}:
            return True
        expected = os.environ.get("DEMO_API_KEY") or DEFAULT_API_KEY
        return self.headers.get("x-api-key") == expected

    def do_OPTIONS(self) -> None:  # noqa: N802
        self.send_response(204)
        self._cors()
        self.end_headers()

    def do_GET(self) -> None:  # noqa: N802
        parsed = urlparse(self.path)
        path = parsed.path.rstrip("/") or "/"
        if path == "/download":
            result = download_local(parsed.query)
            if len(result) == 3:
                self._bytes(*result)
            else:
                self._json(*result)
            return
        if not self._auth_ok(path):
            self._json(401, {"error": "unauthorized"})
            return
        if path == "/":
            html = (
                "<!doctype html><html><body style='font-family:sans-serif;background:#05070a;color:#e8eef8;padding:2rem'>"
                "<h1>CasePacket API</h1>"
                "<p>This is the backend on port 8080.</p>"
                "<p>Open the console at <a style='color:#00e5ff' href='http://127.0.0.1:5173'>http://127.0.0.1:5173</a></p>"
                "<p>Health: <a style='color:#00e5ff' href='/healthz'>/healthz</a></p>"
                "</body></html>"
            ).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self._cors()
            self.send_header("Content-Length", str(len(html)))
            self.end_headers()
            self.wfile.write(html)
            return
        if path == "/healthz":
            self._json(*health())
        elif path == "/ops":
            self._json(*ops())
        elif path == "/graph":
            self._json(*get_graph())
        elif path == "/cases":
            self._json(*list_cases())
        elif path.startswith("/cases/") and path.endswith("/packet/pdf"):
            case_id = path[len("/cases/") : -len("/packet/pdf")]
            result = get_packet_pdf(case_id)
            if len(result) == 3:
                self._bytes(result[0], result[1], result[2], disposition=f'attachment; filename="{case_id}-brief.txt"')
            else:
                self._json(*result)
        elif path.startswith("/cases/") and path.endswith("/packet"):
            case_id = path[len("/cases/") : -len("/packet")]
            self._json(*get_packet(case_id))
        elif path.startswith("/cases/"):
            self._json(*get_case(path.split("/", 2)[-1]))
        else:
            self._json(404, {"error": "not_found", "path": path})

    def do_POST(self) -> None:  # noqa: N802
        parsed = urlparse(self.path)
        path = parsed.path.rstrip("/") or "/"
        if not self._auth_ok(path):
            self._json(401, {"error": "unauthorized"})
            return
        length = int(self.headers.get("Content-Length") or 0)
        raw = self.rfile.read(length) if length else b"{}"
        try:
            payload = json.loads(raw.decode("utf-8") or "{}")
        except json.JSONDecodeError:
            self._json(400, {"error": "invalid_json"})
            return
        if path == "/ingest":
            self._json(*ingest(payload if isinstance(payload, dict) else {}))
        elif path.startswith("/cases/") and path.endswith("/packet"):
            case_id = path[len("/cases/") : -len("/packet")]
            self._json(*start_packet(case_id))
        else:
            self._json(404, {"error": "not_found", "path": path})


def main() -> None:
    host = os.environ.get("HOST", "127.0.0.1")
    server = ThreadingHTTPServer((host, PORT), Handler)
    print(f"CasePacket API  http://{host}:{PORT}", flush=True)
    print("  GET  /healthz  /graph  /cases", flush=True)
    print("  POST /cases/CASE-001/packet", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nbye")


if __name__ == "__main__":
    main()
