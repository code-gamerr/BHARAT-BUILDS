"""Local unit tests — no AWS required."""
from casepacket import extract_entities, score_risk


def test_entities():
    text = "Contact seller@example.invalid or +91-9000000001 wallet 0x1111222233334444555566667777888899990000 @scamdemo"
    ents = extract_entities(text)
    types = {e["type"] for e in ents}
    assert "email" in types
    assert "phone" in types
    assert "wallet" in types
    assert "handle" in types


def test_risk():
    ents = extract_entities("phishing OTP KYC mule dump")
    risk, cat = score_risk("phishing OTP KYC mule dump", ents)
    assert risk >= 40
