from __future__ import annotations

import sys
from pathlib import Path

SRC = Path(__file__).resolve().parents[1]
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from shared.pipeline import extract_enrich  # noqa: E402


def lambda_handler(event, context):
    extract_enrich(event["case_id"])
    return event
