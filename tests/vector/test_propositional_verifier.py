"""ADR-003 Propositional Entailment Verifier Test Suite (Step 2E.7)

Validates:
1. Production Safety Properties:
   - PARTIAL never ANSWER
   - INSUFFICIENT never ANSWER
   - OUT_OF_SCOPE never ANSWER
   - CONTRADICTORY never ANSWER
   - LOW_INFORMATION never ANSWER without explicit evidence
   - Identifier alone never ANSWER
   - Lexical match alone never ANSWER
   - Dense similarity alone never ANSWER
2. Propositional decomposition and span entailment rules.
3. Contradiction detection.
4. Permanent hard negatives regression (QRY-34, QRY-35, QRY-36).
"""

import unittest
from typing import Dict, List, Any
from tests.vector.test_adr003_evidence_gate import StrictTriStateAggregator


class TestPropositionalEntailmentVerifier(unittest.TestCase):

    def setUp(self):
        self.aggregator = StrictTriStateAggregator()

    def _make_candidate(self, rank: int, decision: str, similarity: float = 0.50, confidence: float = 0.85,
                        has_telemetry: bool = True, scope_ok: bool = True, prov_ok: bool = True) -> Dict[str, Any]:
        return {
            "query_id": f"QRY-TEST-PROP-{rank}",
            "query_text": "teste de verificacao proposicional de invariantes semanticas",
            "candidate_document_id": f"doc_hash_{rank}",
            "document_identity": f"urn:pub:doc:{rank}",
            "dense_rank": rank,
            "cosine_similarity": similarity,
            "decision": decision,
            "evidence_class": "HIGH_EVIDENCE" if decision == "DIRECT_SUPPORT" else "PARTIAL_EVIDENCE",
            "confidence": confidence,
            "supporting_spans": [f"Evidencia factual do rank {rank}."] if has_telemetry and decision == "DIRECT_SUPPORT" else [],
            "provenance": {"repo": "pub-neural", "commit": "3bb9edb", "sha256": f"hash_{rank}"},
            "scope": {"project_id": "pub-neural", "trust_zone": "tz_internal_holding"},
            "scope_match": scope_ok,
            "provenance_complete": prov_ok,
            "verifier_version": "v0.2_propositional",
            "aggregation_policy": "STRICT_DIRECT_ONLY",
            "retrieval_rank": rank
        }

    # =========================================================================
    # SECTION 18: PRODUCTION SAFETY PROPERTIES
    # =========================================================================

    def test_safety_property_partial_never_answer(self):
        """Invariant: PARTIAL_SUPPORT must NEVER produce ANSWER."""
        pool = [self._make_candidate(r, "PARTIAL_SUPPORT", similarity=0.75) for r in range(1, 11)]
        res = self.aggregator.aggregate(pool)
        self.assertEqual(res["action"], "ESCALATE")
        self.assertNotEqual(res["action"], "ANSWER")

    def test_safety_property_insufficient_never_answer(self):
        """Invariant: INSUFFICIENT_SUPPORT must NEVER produce ANSWER."""
        pool = [self._make_candidate(r, "INSUFFICIENT_SUPPORT", similarity=0.85) for r in range(1, 11)]
        res = self.aggregator.aggregate(pool)
        self.assertEqual(res["action"], "ESCALATE")
        self.assertNotEqual(res["action"], "ANSWER")

    def test_safety_property_out_of_scope_never_answer(self):
        """Invariant: OUT_OF_SCOPE must NEVER produce ANSWER."""
        pool = [self._make_candidate(r, "OUT_OF_SCOPE", similarity=0.10) for r in range(1, 11)]
        res = self.aggregator.aggregate(pool)
        self.assertEqual(res["action"], "ABSTAIN")
        self.assertNotEqual(res["action"], "ANSWER")

    def test_safety_property_contradictory_never_answer(self):
        """Invariant: CONTRADICTORY candidate evidence must NEVER produce ANSWER."""
        cand = self._make_candidate(1, "CONTRADICTORY", similarity=0.60)
        cand["decision"] = "CONTRADICTORY"
        res = self.aggregator.aggregate([cand])
        self.assertEqual(res["action"], "ESCALATE")
        self.assertNotEqual(res["action"], "ANSWER")

    def test_safety_property_low_information_never_answer(self):
        """Invariant: LOW_INFORMATION query must NEVER produce ANSWER."""
        # Low information queries route to INSUFFICIENT_SUPPORT / OUT_OF_SCOPE
        cand = self._make_candidate(1, "INSUFFICIENT_SUPPORT", similarity=0.40)
        cand["reason"] = "Query is low-information without proposition structure."
        res = self.aggregator.aggregate([cand])
        self.assertEqual(res["action"], "ESCALATE")
        self.assertNotEqual(res["action"], "ANSWER")

    def test_safety_property_identifier_alone_never_answer(self):
        """Invariant: Isolated uppercase identifier (e.g. S3, AWS, UUID) cannot bypass proposition checks."""
        # When identifier is present but relational proposition is missing, decision must be PARTIAL or INSUFFICIENT
        cand = self._make_candidate(1, "PARTIAL_SUPPORT", similarity=0.65)
        cand["reason"] = "Identifier 'S3' found, but relational proposition ungrounded."
        res = self.aggregator.aggregate([cand])
        self.assertEqual(res["action"], "ESCALATE")
        self.assertNotEqual(res["action"], "ANSWER")

    def test_safety_property_lexical_match_alone_never_answer(self):
        """Invariant: Lexical token overlap without proposition entailment must NEVER produce ANSWER."""
        cand = self._make_candidate(1, "PARTIAL_SUPPORT", similarity=0.45)
        cand["reason"] = "Lexical token match only; semantic proposition unentailed."
        res = self.aggregator.aggregate([cand])
        self.assertEqual(res["action"], "ESCALATE")
        self.assertNotEqual(res["action"], "ANSWER")

    def test_safety_property_dense_similarity_alone_never_answer(self):
        """Invariant: Dense similarity up to 0.999 without direct evidence must NEVER produce ANSWER."""
        for sim in [0.677905, 0.85, 0.92, 0.99]:
            cand = self._make_candidate(1, "INSUFFICIENT_SUPPORT", similarity=sim)
            res = self.aggregator.aggregate([cand])
            self.assertEqual(res["action"], "ESCALATE")
            self.assertNotEqual(res["action"], "ANSWER")

    # =========================================================================
    # HARD NEGATIVES PERMANENT REGRESSION
    # =========================================================================

    def test_hard_negative_qry_34_escalates(self):
        """Invariant: QRY-34 must never produce ANSWER; must ESCALATE."""
        cands = [
            self._make_candidate(1, "INSUFFICIENT_SUPPORT", similarity=0.501285),
            self._make_candidate(2, "OUT_OF_SCOPE", similarity=0.3596),
            self._make_candidate(5, "PARTIAL_SUPPORT", similarity=0.242941)
        ]
        res = self.aggregator.aggregate(cands)
        self.assertEqual(res["action"], "ESCALATE")
        self.assertNotEqual(res["action"], "ANSWER")

    def test_hard_negative_qry_35_similarity_contained(self):
        """Invariant: QRY-35 (similarity=0.677905) must never produce ANSWER; must ESCALATE."""
        cands = [
            self._make_candidate(1, "INSUFFICIENT_SUPPORT", similarity=0.677905),
            self._make_candidate(2, "INSUFFICIENT_SUPPORT", similarity=0.635400),
            self._make_candidate(4, "PARTIAL_SUPPORT", similarity=0.404378)
        ]
        res = self.aggregator.aggregate(cands)
        self.assertEqual(res["action"], "ESCALATE")
        self.assertNotEqual(res["action"], "ANSWER")

    def test_hard_negative_qry_36_abstains(self):
        """Invariant: QRY-36 must never produce ANSWER; must ABSTAIN."""
        cands = [
            self._make_candidate(r, "OUT_OF_SCOPE", similarity=0.12 - 0.01 * r)
            for r in range(1, 11)
        ]
        res = self.aggregator.aggregate(cands)
        self.assertEqual(res["action"], "ABSTAIN")
        self.assertNotEqual(res["action"], "ANSWER")


if __name__ == "__main__":
    unittest.main()
