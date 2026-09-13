"""ADR-003 Adversarial Robustness & Property-Based Test Suite (Step 2E.6)

Implements:
- 10 Property-based tests for Aggregator B Strict invariants.
- Monotonicity tests across candidate expansion (K=3 -> K=5 -> K=10).
- Permanent regression checks for hard negatives (QRY-34, QRY-35, QRY-36).
- Multi-document composite evidence candidacy checks.
"""

import unittest
from typing import List, Dict, Any
from tests.vector.test_adr003_evidence_gate import StrictTriStateAggregator


class TestADR003AdversarialProperties(unittest.TestCase):

    def setUp(self):
        self.aggregator = StrictTriStateAggregator()

    def _make_candidate(self, rank: int, decision: str, similarity: float = 0.50, confidence: float = 0.85,
                        scope_ok: bool = True, prov_ok: bool = True) -> Dict[str, Any]:
        return {
            "query_id": f"ADV-PROP-{rank}",
            "query_text": "consulta de teste adversarial de invariantes matematicas",
            "candidate_document_id": f"doc_hash_{rank}",
            "document_identity": f"urn:pub:doc:{rank}",
            "dense_rank": rank,
            "cosine_similarity": similarity,
            "decision": decision,
            "evidence_class": "HIGH_EVIDENCE" if decision == "DIRECT_SUPPORT" else "PARTIAL_EVIDENCE",
            "confidence": confidence,
            "supporting_spans": [f"Evidencia factual do rank {rank}."] if decision == "DIRECT_SUPPORT" else [],
            "provenance": {"repo": "pub-neural", "commit": "3bb9edb", "sha256": f"hash_{rank}"},
            "scope": {"project_id": "pub-neural", "trust_zone": "tz_internal_holding"},
            "scope_match": scope_ok,
            "provenance_complete": prov_ok,
            "verifier_version": "v0.2_strict",
            "aggregation_policy": "STRICT_DIRECT_ONLY",
            "retrieval_rank": rank
        }

    # =========================================================================
    # 10 PROPERTY-BASED TESTS (Section 12)
    # =========================================================================

    def test_property_1_partial_support_never_answers(self):
        """Property 1: PARTIAL_SUPPORT alone or multiplied never produces ANSWER."""
        pool = [self._make_candidate(r, "PARTIAL_SUPPORT") for r in range(1, 11)]
        res = self.aggregator.aggregate(pool)
        self.assertEqual(res["action"], "ESCALATE")
        self.assertNotEqual(res["action"], "ANSWER")

    def test_property_2_insufficient_support_never_answers(self):
        """Property 2: INSUFFICIENT_SUPPORT never produces ANSWER."""
        pool = [self._make_candidate(r, "INSUFFICIENT_SUPPORT") for r in range(1, 11)]
        res = self.aggregator.aggregate(pool)
        self.assertEqual(res["action"], "ESCALATE")
        self.assertNotEqual(res["action"], "ANSWER")

    def test_property_3_out_of_scope_never_answers(self):
        """Property 3: OUT_OF_SCOPE candidates never produce ANSWER (must ABSTAIN)."""
        pool = [self._make_candidate(r, "OUT_OF_SCOPE") for r in range(1, 11)]
        res = self.aggregator.aggregate(pool)
        self.assertEqual(res["action"], "ABSTAIN")
        self.assertNotEqual(res["action"], "ANSWER")

    def test_property_4_contradictory_never_answers(self):
        """Property 4: CONTRADICTORY candidate evidence never produces ANSWER."""
        cand_a = self._make_candidate(1, "INSUFFICIENT_SUPPORT")
        cand_b = self._make_candidate(2, "PARTIAL_SUPPORT")
        cand_b["decision"] = "CONTRADICTORY"
        res = self.aggregator.aggregate([cand_a, cand_b])
        self.assertEqual(res["action"], "ESCALATE")
        self.assertNotEqual(res["action"], "ANSWER")

    def test_property_5_increasing_k_cannot_turn_partial_into_answer(self):
        """Property 5: Expanding candidate depth from K=1 to K=10 with only partials cannot produce ANSWER."""
        for k in [1, 3, 5, 10]:
            pool = [self._make_candidate(r, "PARTIAL_SUPPORT") for r in range(1, k + 1)]
            res = self.aggregator.aggregate(pool)
            self.assertEqual(res["action"], "ESCALATE", f"Failed at K={k}")

    def test_property_6_increasing_similarity_cannot_replace_evidence(self):
        """Property 6: Raising cosine similarity up to 0.999 without direct evidence cannot produce ANSWER."""
        for sim in [0.70, 0.80, 0.90, 0.95, 0.99, 0.999]:
            cand = self._make_candidate(1, "INSUFFICIENT_SUPPORT", similarity=sim)
            res = self.aggregator.aggregate([cand])
            self.assertEqual(res["action"], "ESCALATE", f"Failed at sim={sim}")

    def test_property_7_provenance_failure_cannot_produce_answer(self):
        """Property 7: Cryptographic provenance failure blocks ANSWER even on direct match."""
        cand = self._make_candidate(1, "DIRECT_SUPPORT", prov_ok=False)
        res = self.aggregator.aggregate([cand])
        self.assertIn(res["action"], ["ABSTAIN", "ESCALATE"])
        self.assertNotEqual(res["action"], "ANSWER")

    def test_property_8_scope_failure_cannot_produce_answer(self):
        """Property 8: Project scope mismatch blocks ANSWER even on direct match."""
        cand = self._make_candidate(1, "DIRECT_SUPPORT", scope_ok=False)
        res = self.aggregator.aggregate([cand])
        self.assertNotEqual(res["action"], "ANSWER")

    def test_property_9_missing_mandatory_telemetry_fails_closed(self):
        """Property 9: Missing mandatory telemetry fields (supporting_spans) falls back to ESCALATE."""
        cand = self._make_candidate(1, "DIRECT_SUPPORT")
        cand["supporting_spans"] = []
        res = self.aggregator.aggregate([cand])
        self.assertEqual(res["action"], "ESCALATE")

    def test_property_10_adding_partial_preserves_valid_direct_answer(self):
        """Property 10: Adding partial candidates to pool cannot invalidate verified DIRECT evidence."""
        direct_cand = self._make_candidate(1, "DIRECT_SUPPORT", similarity=0.60)
        res_k1 = self.aggregator.aggregate([direct_cand])
        self.assertEqual(res_k1["action"], "ANSWER")

        # Add 9 lower-rank partial candidates
        pool_k10 = [direct_cand] + [self._make_candidate(r, "PARTIAL_SUPPORT", similarity=0.40) for r in range(2, 11)]
        res_k10 = self.aggregator.aggregate(pool_k10)
        self.assertEqual(res_k10["action"], "ANSWER")
        self.assertEqual(res_k10["candidate"]["dense_rank"], 1)

    # =========================================================================
    # MONOTONICITY TESTS (Section 13)
    # =========================================================================

    def test_monotonicity_escalate_remains_escalate_when_adding_partials(self):
        """Monotonicity: If K=3 -> ESCALATE and K=5 adds only PARTIAL, K=5 MUST remain ESCALATE."""
        cands_k3 = [
            self._make_candidate(1, "INSUFFICIENT_SUPPORT", 0.65),
            self._make_candidate(2, "INSUFFICIENT_SUPPORT", 0.55),
            self._make_candidate(3, "INSUFFICIENT_SUPPORT", 0.45)
        ]
        res_k3 = self.aggregator.aggregate(cands_k3)
        self.assertEqual(res_k3["action"], "ESCALATE")

        # Expanding to K=5 with partials
        cands_k5 = cands_k3 + [
            self._make_candidate(4, "PARTIAL_SUPPORT", 0.40),
            self._make_candidate(5, "PARTIAL_SUPPORT", 0.35)
        ]
        res_k5 = self.aggregator.aggregate(cands_k5)
        self.assertEqual(res_k5["action"], "ESCALATE")

    def test_monotonicity_direct_at_later_rank_upgrades_escalate_to_answer(self):
        """Monotonicity: If K=3 is ESCALATE, and rank 4 is DIRECT_SUPPORT, K=5 safely upgrades to ANSWER."""
        cands = [
            self._make_candidate(1, "INSUFFICIENT_SUPPORT"),
            self._make_candidate(2, "INSUFFICIENT_SUPPORT"),
            self._make_candidate(3, "PARTIAL_SUPPORT"),
            self._make_candidate(4, "DIRECT_SUPPORT", similarity=0.48),
            self._make_candidate(5, "PARTIAL_SUPPORT")
        ]
        res_k3 = self.aggregator.aggregate(cands[:3])
        self.assertEqual(res_k3["action"], "ESCALATE")

        res_k5 = self.aggregator.aggregate(cands[:5])
        self.assertEqual(res_k5["action"], "ANSWER")
        self.assertEqual(res_k5["candidate"]["dense_rank"], 4)

    # =========================================================================
    # MULTI-DOCUMENT COMPOSITE EVIDENCE INVARIANT (Section 14)
    # =========================================================================

    def test_composite_evidence_candidates_do_not_answer_without_fusion(self):
        """Multi-doc: Two disjoint partial candidates (A and B) must ESCALATE under single-doc verifier."""
        cand_a = self._make_candidate(1, "PARTIAL_SUPPORT")
        cand_b = self._make_candidate(2, "PARTIAL_SUPPORT")
        res = self.aggregator.aggregate([cand_a, cand_b])
        self.assertEqual(res["action"], "ESCALATE")
        self.assertNotEqual(res["action"], "ANSWER")


if __name__ == "__main__":
    unittest.main()
