"""Unit tests for GRPO reward (docs/ml.md eval bar)."""
from handler import score_brief


def test_prefers_entity_rich_simulated():
    good = (
        "SIMULATED TLP:AMBER triage. Risk 72/100. Contact seller@example.invalid "
        "mentioned in body. Entities first, concise LE brief for analyst queue. "
        "No operational crawl claims. Recommend correlate wallet and phone next. "
        "Packet compile remains rules-first if Bedrock degraded. "
        + " ".join(["note"] * 8)
    )
    bad = "lol"
    assert score_brief(good, ["seller@example.invalid"]) > score_brief(bad, ["seller@example.invalid"])


def test_hype_penalized():
    text = "guaranteed hack buy ransomware " + "word " * 50
    assert score_brief(text, []) < 0
