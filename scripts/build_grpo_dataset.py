#!/usr/bin/env python3
"""Build ml/datasets/grpo_train.jsonl from fixtures/ (≥12 prompts). No hardcoded cases."""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FIX = ROOT / "fixtures"
OUT = ROOT / "ml" / "datasets" / "grpo_train.jsonl"


def main() -> int:
    files = sorted(FIX.glob("fx-*.json"))
    if len(files) < 12:
        print(f"need ≥12 fixtures, found {len(files)}", file=sys.stderr)
        return 1
    OUT.parent.mkdir(parents=True, exist_ok=True)
    lines = []
    for f in files:
        doc = json.loads(f.read_text(encoding="utf-8"))
        prompt = (
            "Rank/write an LE triage brief for this SIMULATED listing:\n"
            f"TITLE: {doc.get('title', '')}\n"
            f"BODY: {doc.get('body', '')}\n"
            f"CATEGORY_HINT: {doc.get('category_hint', '')}\n"
            "Prefer: clear risk, entities first, TLP/SIMULATED marked, no hype."
        )
        lines.append(json.dumps({"prompt": prompt}, ensure_ascii=False))
    OUT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"wrote {len(lines)} prompts → {OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
