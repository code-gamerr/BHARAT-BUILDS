from __future__ import annotations

import sys
from pathlib import Path

SRC = Path(__file__).resolve().parents[1]
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from shared.pipeline import compile_case_packet  # noqa: E402


def lambda_handler(event, context):
    result = compile_case_packet(event["case_id"], execution_arn=event.get("execution_arn"))
    return {
        **event,
        "s3_key": result["s3_key"],
        "sha256": result["sha256"],
        "execution_arn": result["execution_arn"],
        "status": "SUCCEEDED",
    }
