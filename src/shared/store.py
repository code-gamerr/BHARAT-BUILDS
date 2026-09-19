"""Storage adapter: local JSON/files or DynamoDB + S3."""

from __future__ import annotations

import hashlib
import json
import os
import threading
from pathlib import Path
from typing import Any
from urllib.parse import quote

ROOT = Path(__file__).resolve().parents[2]
LOCAL_DIR = ROOT / ".local"
LOCAL_DB = LOCAL_DIR / "db.json"
LOCAL_S3 = LOCAL_DIR / "s3"


def project_root() -> Path:
    return ROOT


def is_local() -> bool:
    if os.environ.get("CASEPACKET_LOCAL") == "1":
        return True
    if os.environ.get("TABLE_NAME") and os.environ.get("BUCKET_NAME"):
        return False
    return True


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_text(text: str) -> str:
    return sha256_bytes(text.encode("utf-8"))


class Store:
    def get_case(self, case_id: str) -> dict | None: ...
    def list_cases(self) -> list[dict]: ...
    def put_case(self, case: dict) -> dict: ...
    def find_by_hash(self, digest: str) -> dict | None: ...
    def put_raw(self, key: str, body: bytes, content_type: str = "application/json") -> str: ...
    def get_raw(self, key: str) -> bytes: ...
    def put_packet(self, key: str, packet: dict) -> str: ...
    def get_packet(self, key: str) -> dict: ...
    def download_url(self, key: str, ttl_seconds: int = 600) -> str: ...
    def get_ops(self) -> dict: ...
    def put_ops(self, ops: dict) -> dict: ...
    def health_checks(self) -> dict: ...


class LocalStore(Store):
    def __init__(self) -> None:
        LOCAL_DIR.mkdir(parents=True, exist_ok=True)
        (LOCAL_S3 / "raw").mkdir(parents=True, exist_ok=True)
        (LOCAL_S3 / "packets").mkdir(parents=True, exist_ok=True)
        self._lock = threading.Lock()
        if not LOCAL_DB.exists():
            self._write({"cases": {}, "ops": {}})

    def _read(self) -> dict:
        if not LOCAL_DB.exists():
            return {"cases": {}, "ops": {}}
        return json.loads(LOCAL_DB.read_text(encoding="utf-8"))

    def _write(self, db: dict) -> None:
        LOCAL_DB.write_text(json.dumps(db, indent=2), encoding="utf-8")

    def get_case(self, case_id: str) -> dict | None:
        with self._lock:
            return self._read()["cases"].get(case_id)

    def list_cases(self) -> list[dict]:
        with self._lock:
            cases = list(self._read()["cases"].values())
        cases.sort(key=lambda c: (-int(c.get("risk") or 0), c.get("created_at") or ""))
        return cases

    def put_case(self, case: dict) -> dict:
        with self._lock:
            db = self._read()
            db["cases"][case["id"]] = case
            self._write(db)
        return case

    def find_by_hash(self, digest: str) -> dict | None:
        with self._lock:
            for case in self._read()["cases"].values():
                if case.get("raw_sha256") == digest:
                    return case
        return None

    def put_raw(self, key: str, body: bytes, content_type: str = "application/json") -> str:
        path = LOCAL_S3 / key
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(body)
        return key

    def get_raw(self, key: str) -> bytes:
        return (LOCAL_S3 / key).read_bytes()

    def put_packet(self, key: str, packet: dict) -> str:
        body = json.dumps(packet, indent=2).encode("utf-8")
        path = LOCAL_S3 / key
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(body)
        return sha256_bytes(body)

    def get_packet(self, key: str) -> dict:
        return json.loads((LOCAL_S3 / key).read_text(encoding="utf-8"))

    def download_url(self, key: str, ttl_seconds: int = 600) -> str:
        base = os.environ.get("PUBLIC_BASE_URL", "http://127.0.0.1:8080")
        return f"{base}/download?key={quote(key)}"

    def get_ops(self) -> dict:
        with self._lock:
            return dict(self._read().get("ops") or {})

    def put_ops(self, ops: dict) -> dict:
        with self._lock:
            db = self._read()
            db["ops"] = ops
            self._write(db)
        return ops

    def health_checks(self) -> dict:
        return {
            "store": "ok" if LOCAL_DB.exists() or True else "missing",
            "s3": "ok" if LOCAL_S3.exists() else "missing",
            "bedrock": "disabled",
        }


class AwsStore(Store):
    def __init__(self) -> None:
        import boto3

        self.table_name = os.environ["TABLE_NAME"]
        self.bucket = os.environ["BUCKET_NAME"]
        self.ddb = boto3.resource("dynamodb").Table(self.table_name)
        self.s3 = boto3.client("s3")

    def _item_to_case(self, item: dict) -> dict:
        from decimal import Decimal

        case = {k: v for k, v in item.items() if k not in {"pk", "sk", "gsi1pk"}}
        if isinstance(case.get("risk"), Decimal):
            case["risk"] = int(case["risk"])
        return case

    def get_case(self, case_id: str) -> dict | None:
        resp = self.ddb.get_item(Key={"pk": f"CASE#{case_id}", "sk": "META"})
        item = resp.get("Item")
        return self._item_to_case(item) if item else None

    def list_cases(self) -> list[dict]:
        items: list[dict] = []
        kwargs: dict[str, Any] = {
            "FilterExpression": "sk = :sk",
            "ExpressionAttributeValues": {":sk": "META"},
        }
        while True:
            resp = self.ddb.scan(**kwargs)
            items.extend(resp.get("Items") or [])
            if "LastEvaluatedKey" not in resp:
                break
            kwargs["ExclusiveStartKey"] = resp["LastEvaluatedKey"]
        cases = [self._item_to_case(i) for i in items if str(i.get("pk", "")).startswith("CASE#")]
        cases.sort(key=lambda c: (-int(c.get("risk") or 0), c.get("created_at") or ""))
        return cases

    def put_case(self, case: dict) -> dict:
        item = {
            **case,
            "pk": f"CASE#{case['id']}",
            "sk": "META",
            "gsi1pk": "CASE",
        }
        self.ddb.put_item(Item=item)
        for entity in case.get("entities") or []:
            self.ddb.put_item(
                Item={
                    "pk": f"ENTITY#{entity['type']}#{entity['value']}",
                    "sk": f"CASE#{case['id']}",
                    "case_id": case["id"],
                    "type": entity["type"],
                    "value": entity["value"],
                }
            )
        if case.get("cluster_id"):
            self.ddb.put_item(
                Item={
                    "pk": f"CLUSTER#{case['cluster_id']}",
                    "sk": f"CASE#{case['id']}",
                    "case_id": case["id"],
                }
            )
        return case

    def find_by_hash(self, digest: str) -> dict | None:
        from boto3.dynamodb.conditions import Attr

        resp = self.ddb.scan(FilterExpression=Attr("raw_sha256").eq(digest))
        for item in resp.get("Items") or []:
            if item.get("sk") == "META":
                return self._item_to_case(item)
        return None

    def put_raw(self, key: str, body: bytes, content_type: str = "application/json") -> str:
        self.s3.put_object(Bucket=self.bucket, Key=key, Body=body, ContentType=content_type)
        return key

    def get_raw(self, key: str) -> bytes:
        return self.s3.get_object(Bucket=self.bucket, Key=key)["Body"].read()

    def put_packet(self, key: str, packet: dict) -> str:
        body = json.dumps(packet, indent=2).encode("utf-8")
        self.s3.put_object(Bucket=self.bucket, Key=key, Body=body, ContentType="application/json")
        return sha256_bytes(body)

    def get_packet(self, key: str) -> dict:
        body = self.s3.get_object(Bucket=self.bucket, Key=key)["Body"].read()
        return json.loads(body)

    def download_url(self, key: str, ttl_seconds: int = 600) -> str:
        return self.s3.generate_presigned_url(
            "get_object",
            Params={"Bucket": self.bucket, "Key": key},
            ExpiresIn=ttl_seconds,
        )

    def get_ops(self) -> dict:
        resp = self.ddb.get_item(Key={"pk": "OPS#GLOBAL", "sk": "META"})
        item = resp.get("Item") or {}
        return {k: v for k, v in item.items() if k not in {"pk", "sk"}}

    def put_ops(self, ops: dict) -> dict:
        self.ddb.put_item(Item={**ops, "pk": "OPS#GLOBAL", "sk": "META"})
        return ops

    def health_checks(self) -> dict:
        checks = {"store": "error", "s3": "error", "bedrock": "disabled"}
        try:
            self.ddb.get_item(Key={"pk": "OPS#GLOBAL", "sk": "META"})
            checks["store"] = "ok"
        except Exception as exc:  # pragma: no cover
            checks["store"] = str(exc)[:80]
        try:
            self.s3.head_bucket(Bucket=self.bucket)
            checks["s3"] = "ok"
        except Exception as exc:  # pragma: no cover
            checks["s3"] = str(exc)[:80]
        if os.environ.get("ENABLE_BEDROCK") == "1":
            checks["bedrock"] = "enabled"
        return checks


_STORE: Store | None = None


def get_store() -> Store:
    global _STORE
    if _STORE is None:
        _STORE = LocalStore() if is_local() else AwsStore()
    return _STORE


def reset_store_cache() -> None:
    global _STORE
    _STORE = None
