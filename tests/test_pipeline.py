from __future__ import annotations

import json
import os
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

os.environ["CASEPACKET_LOCAL"] = "1"


class NerTests(unittest.TestCase):
    def test_extracts_indian_theme_observables(self):
        from shared.ner import extract_entities

        text = (
            "Ping seller@example.invalid or +91-90000-00001 "
            "https://sim.casepacket.invalid/x @sim_kyc_desk "
            "wallet 1FakeWalletDemo000000000000000001 "
            "and 0xF00d000000000000000000000000000000000001 "
            "CVE-2024-12345 SIM-AADHAAR-1234-5678-9012"
        )
        entities = extract_entities(text, source="fixture://t", seen_at="2026-09-18T10:00:00Z")
        types = {e["type"] for e in entities}
        values = {e["value"] for e in entities}
        self.assertIn("email", types)
        self.assertIn("phone", types)
        self.assertIn("url", types)
        self.assertIn("domain", types)
        self.assertIn("handle", types)
        self.assertIn("wallet", types)
        self.assertIn("cve", types)
        self.assertIn("aadhaar", types)
        self.assertIn("seller@example.invalid", values)
        self.assertIn("+91-90000-00001", values)
        self.assertTrue(all("stix_id" in e for e in entities))


class ScoringTests(unittest.TestCase):
    def test_high_risk_for_mule_and_kyc(self):
        from shared.ner import extract_entities
        from shared.scoring import score_case

        body = "KYC packs and mule desk, OTP bot, Aadhaar dump"
        entities = extract_entities("a@b.invalid +91-90000-00001 1FakeWalletDemo000000000000000001")
        result = score_case("fake KYC", body, "docs", entities, correlation_bonus=12)
        self.assertGreaterEqual(result["risk"], 70)
        self.assertEqual(result["category"], "docs")
        self.assertTrue(any(f["label"] == "Cross-case correlation" for f in result["risk_factors"]))


class CorrelationAndPacketTests(unittest.TestCase):
    def test_shared_phone_correlates_and_packet_compiles(self):
        from shared.correlation import build_relationships, linked_for_case, refresh_clusters
        from shared.evidence import build_proof_chain
        from shared.ner import extract_entities
        from shared.packet import compile_packet

        a = {
            "id": "CASE-001",
            "title": "A",
            "source": "fixture://marketplace-sim",
            "category": "docs",
            "created_at": "2026-09-18T10:00:00Z",
            "raw_sha256": "aaa",
            "entities": extract_entities("call +91-90000-00001 seller@example.invalid"),
        }
        b = {
            "id": "CASE-007",
            "title": "B",
            "source": "fixture://marketplace-sim",
            "category": "docs",
            "created_at": "2026-09-18T13:00:00Z",
            "raw_sha256": "bbb",
            "entities": extract_entities("again +91-90000-00001"),
        }
        rels = build_relationships([a, b])
        self.assertTrue(rels)
        self.assertGreaterEqual(rels[0]["confidence"], 40)
        mapping = refresh_clusters([a, b], rels)
        self.assertEqual(mapping["CASE-001"], mapping["CASE-007"])
        linked = linked_for_case("CASE-001", rels)
        self.assertEqual(linked[0]["case_id"], "CASE-007")
        a["cluster_id"] = mapping["CASE-001"]
        a["risk"] = 80
        a["risk_band"] = "high"
        a["risk_out_of_ten"] = 8.0
        a["raw_s3_key"] = "raw/2026/09/fix-001.json"
        proof = build_proof_chain(a, linked)
        packet = compile_packet(
            a,
            linked_cases=linked,
            relationships=rels,
            proof_chain=proof,
            execution_arn="arn:aws:states:ap-south-1:000:execution:x",
        )
        self.assertEqual(packet["packet_version"], "1.1")
        self.assertIsInstance(packet["risk"], dict)
        self.assertTrue(packet["relationships"])
        self.assertTrue(packet["proof_chain"])
        self.assertEqual(packet["aws"]["region"], "ap-south-1")


class SeedIntegrityTests(unittest.TestCase):
    def test_twenty_fixtures_exist_and_are_simulated(self):
        files = sorted((ROOT / "fixtures").glob("fix-*.json"))
        self.assertEqual(len(files), 20)
        for path in files:
            data = json.loads(path.read_text(encoding="utf-8"))
            self.assertTrue(data["meta"]["simulated"])
            self.assertIn("SIMULATED", data["title"].upper())


if __name__ == "__main__":
    unittest.main()
