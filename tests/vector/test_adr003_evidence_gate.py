"""ADR-003 Contractual Regression Suite & Anti-Pattern Gates

Validates:
1. Strict Tri-State policy invariants (DIRECT -> ANSWER, PARTIAL -> ESCALATE).
2. Anti-patterns (high similarity, RRF, isolated lexical hits cannot produce ANSWER).
3. Candidate dominance invariant (10 partial matches produce ESCALATE, direct at rank 5 produces ANSWER).
4. Hard negatives regression (QRY-34, QRY-35, QRY-36 never produce ANSWER).
5. Observability telemetry and fail-closed fallbacks.
"""

import unittest
from typing import Dict, Any, List, Optional


class StrictTriStateAggregator:
    """Reference implementation of ADR-003 Strict Evidence Aggregator."""

    REQUIRED_OBSERVABILITY_FIELDS = [
        "query_id", "query_text", "candidate_document_id", "document_identity",
        "evidence_class", "confidence", "supporting_spans", "provenance",
        "scope", "verifier_version", "aggregation_policy", "retrieval_rank"
    ]

    @classmethod
    def aggregate(cls, candidates: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Strict Tri-State aggregation over candidate pool (K <= 10)."""
        if not candidates:
            return {"action": "ABSTAIN", "reason": "Empty candidate pool"}

        # Check for any valid DIRECT_SUPPORT candidate with valid provenance and scope
        direct_candidates = [
            c for c in candidates
            if c.get("decision") == "DIRECT_SUPPORT"
            and c.get("confidence", 0.0) >= 0.80
            and c.get("scope_match") is True
            and c.get("provenance_complete") is True
        ]

        if direct_candidates:
            # Sort direct candidates by confidence DESC, similarity DESC, rank ASC
            best_direct = sorted(
                direct_candidates,
                key=lambda x: (x.get("confidence", 0.0), x.get("cosine_similarity", 0.0), -x.get("dense_rank", 999)),
                reverse=True
            )[0]

            # Validate mandatory observability fields
            missing_fields = [f for f in cls.REQUIRED_OBSERVABILITY_FIELDS if not best_direct.get(f)]
            if missing_fields:
                # Fail-closed to ESCALATE
                return {
                    "action": "ESCALATE",
                    "reason": f"Fail-closed: missing mandatory telemetry fields {missing_fields}",
                    "candidate": best_direct
                }

            return {
                "action": "ANSWER",
                "reason": "Verified DIRECT_SUPPORT found in candidate pool",
                "candidate": best_direct
            }

        # If no direct support, check if any candidate has partial support or insufficient support
        has_partial = any(c.get("decision") == "PARTIAL_SUPPORT" for c in candidates)
        has_insufficient = any(c.get("decision") == "INSUFFICIENT_SUPPORT" for c in candidates)
        all_out_of_scope = all(c.get("decision") == "OUT_OF_SCOPE" for c in candidates)

        if has_partial or has_insufficient:
            return {
                "action": "ESCALATE",
                "reason": "Candidate pool contains partial or ungrounded evidence; autonomous answer forbidden",
                "candidate": candidates[0]
            }

        if all_out_of_scope:
            return {
                "action": "ABSTAIN",
                "reason": "All candidates are out of project scope",
                "candidate": candidates[0]
            }

        # Default fail-closed fallback
        return {"action": "ESCALATE", "reason": "Fail-closed default"}


class TestADR003StrictEvidenceGate(unittest.TestCase):

    def setUp(self):
        self.aggregator = StrictTriStateAggregator()

    def _create_valid_direct_candidate(self, rank=1, similarity=0.55):
        return {
            "query_id": "QRY-TEST-01",
            "query_text": "teste de arquitetura hexagonal",
            "candidate_document_id": "doc_hash_123",
            "document_identity": "urn:pub:doc:123",
            "dense_rank": rank,
            "cosine_similarity": similarity,
            "decision": "DIRECT_SUPPORT",
            "evidence_class": "HIGH_EVIDENCE",
            "confidence": 0.98,
            "supporting_spans": ["Arquitetura hexagonal implementada com portas e adaptadores."],
            "provenance": {"repo": "pub-neural", "commit": "3bb9edb", "sha256": "abc"},
            "scope": {"project_id": "pub-neural", "trust_zone": "tz_internal_holding"},
            "scope_match": True,
            "provenance_complete": True,
            "verifier_version": "v0.2_strict",
            "aggregation_policy": "STRICT_DIRECT_ONLY",
            "retrieval_rank": rank
        }

    # =========================================================================
    # ANTI-PATTERN TESTS (Section 7)
    # =========================================================================

    def test_anti_pattern_high_similarity_cannot_produce_answer(self):
        """Invariant: Cosine similarity alone, even at 0.99, must NEVER produce ANSWER without direct evidence."""
        cand = {
            "dense_rank": 1,
            "cosine_similarity": 0.9950,
            "decision": "INSUFFICIENT_SUPPORT",
            "confidence": 0.95,
            "scope_match": True,
            "provenance_complete": True
        }
        res = self.aggregator.aggregate([cand])
        self.assertNotEqual(res["action"], "ANSWER")
        self.assertEqual(res["action"], "ESCALATE")

    def test_anti_pattern_rrf_score_cannot_produce_answer(self):
        """Invariant: High RRF ranking alone must NEVER produce ANSWER."""
        cand = {
            "dense_rank": 1,
            "rrf_score": 0.0327, # Max RRF rank 1
            "decision": "INSUFFICIENT_SUPPORT",
            "scope_match": True,
            "provenance_complete": True
        }
        res = self.aggregator.aggregate([cand])
        self.assertNotEqual(res["action"], "ANSWER")
        self.assertEqual(res["action"], "ESCALATE")

    def test_anti_pattern_partial_support_cannot_produce_answer(self):
        """Invariant: PARTIAL_SUPPORT must NEVER produce ANSWER."""
        cand = {
            "dense_rank": 1,
            "cosine_similarity": 0.65,
            "decision": "PARTIAL_SUPPORT",
            "confidence": 0.85,
            "scope_match": True,
            "provenance_complete": True
        }
        res = self.aggregator.aggregate([cand])
        self.assertNotEqual(res["action"], "ANSWER")
        self.assertEqual(res["action"], "ESCALATE")

    def test_anti_pattern_provenance_failure_blocks_answer(self):
        """Invariant: Even if decision is DIRECT_SUPPORT, provenance failure must block ANSWER."""
        cand = self._create_valid_direct_candidate()
        cand["provenance_complete"] = False
        res = self.aggregator.aggregate([cand])
        self.assertNotEqual(res["action"], "ANSWER")
        self.assertIn(res["action"], ["ABSTAIN", "ESCALATE"])

    def test_anti_pattern_scope_failure_blocks_answer(self):
        """Invariant: Scope mismatch must block ANSWER."""
        cand = self._create_valid_direct_candidate()
        cand["scope_match"] = False
        res = self.aggregator.aggregate([cand])
        self.assertNotEqual(res["action"], "ANSWER")

    # =========================================================================
    # CANDIDATE DOMINANCE & POOL DEPTH INVARIANTS (Section 4 & 5)
    # =========================================================================

    def test_ten_partial_support_candidates_must_escalate(self):
        """Invariant: 10 PARTIAL_SUPPORT candidates across ranks 1..10 must produce ESCALATE, never ANSWER."""
        candidates = [
            {
                "dense_rank": r,
                "cosine_similarity": 0.50 - 0.02 * r,
                "decision": "PARTIAL_SUPPORT",
                "confidence": 0.75,
                "scope_match": True,
                "provenance_complete": True
            }
            for r in range(1, 11)
        ]
        res = self.aggregator.aggregate(candidates)
        self.assertEqual(res["action"], "ESCALATE")

    def test_direct_support_at_rank_five_produces_answer(self):
        """Invariant: If ranks 1..4 are partial/insufficient but rank 5 is DIRECT_SUPPORT, action is ANSWER."""
        candidates = [
            {"dense_rank": 1, "decision": "INSUFFICIENT_SUPPORT", "scope_match": True, "provenance_complete": True},
            {"dense_rank": 2, "decision": "INSUFFICIENT_SUPPORT", "scope_match": True, "provenance_complete": True},
            {"dense_rank": 3, "decision": "PARTIAL_SUPPORT", "scope_match": True, "provenance_complete": True},
            {"dense_rank": 4, "decision": "PARTIAL_SUPPORT", "scope_match": True, "provenance_complete": True},
            self._create_valid_direct_candidate(rank=5, similarity=0.45)
        ]
        res = self.aggregator.aggregate(candidates)
        self.assertEqual(res["action"], "ANSWER")
        self.assertEqual(res["candidate"]["dense_rank"], 5)

    # =========================================================================
    # HARD NEGATIVES REGRESSION SUITE (Section 6)
    # =========================================================================

    def test_hard_negative_qry_34_never_answers(self):
        """Invariant: QRY-34 (PyTorch vision) must never answer; candidate rank 5 partial match must ESCALATE."""
        candidates = [
            {"dense_rank": 1, "decision": "INSUFFICIENT_SUPPORT", "cosine_similarity": 0.501285, "scope_match": True, "provenance_complete": True},
            {"dense_rank": 2, "decision": "OUT_OF_SCOPE", "scope_match": True, "provenance_complete": True},
            {"dense_rank": 3, "decision": "OUT_OF_SCOPE", "scope_match": True, "provenance_complete": True},
            {"dense_rank": 4, "decision": "OUT_OF_SCOPE", "scope_match": True, "provenance_complete": True},
            {"dense_rank": 5, "decision": "PARTIAL_SUPPORT", "cosine_similarity": 0.242941, "scope_match": True, "provenance_complete": True}
        ]
        res = self.aggregator.aggregate(candidates)
        self.assertNotEqual(res["action"], "ANSWER")
        self.assertEqual(res["action"], "ESCALATE")

    def test_hard_negative_qry_35_never_answers_despite_high_similarity(self):
        """Invariant: QRY-35 (Kubernetes Istio, sim=0.6779) must never answer; rank 4 partial match must ESCALATE."""
        candidates = [
            {"dense_rank": 1, "decision": "INSUFFICIENT_SUPPORT", "cosine_similarity": 0.677905, "scope_match": True, "provenance_complete": True},
            {"dense_rank": 2, "decision": "INSUFFICIENT_SUPPORT", "cosine_similarity": 0.635400, "scope_match": True, "provenance_complete": True},
            {"dense_rank": 3, "decision": "INSUFFICIENT_SUPPORT", "cosine_similarity": 0.406000, "scope_match": True, "provenance_complete": True},
            {"dense_rank": 4, "decision": "PARTIAL_SUPPORT", "cosine_similarity": 0.404378, "scope_match": True, "provenance_complete": True},
            {"dense_rank": 5, "decision": "OUT_OF_SCOPE", "scope_match": True, "provenance_complete": True}
        ]
        res = self.aggregator.aggregate(candidates)
        self.assertNotEqual(res["action"], "ANSWER")
        self.assertEqual(res["action"], "ESCALATE")

    def test_hard_negative_qry_36_abstains(self):
        """Invariant: QRY-36 (Solidity NFT) has all OUT_OF_SCOPE candidates and must ABSTAIN."""
        candidates = [
            {"dense_rank": r, "decision": "OUT_OF_SCOPE", "cosine_similarity": 0.12 - 0.01 * r, "scope_match": True, "provenance_complete": True}
            for r in range(1, 11)
        ]
        res = self.aggregator.aggregate(candidates)
        self.assertNotEqual(res["action"], "ANSWER")
        self.assertEqual(res["action"], "ABSTAIN")

    # =========================================================================
    # OBSERVABILITY TELEMETRY & FAIL-CLOSED (Section 9 & 10)
    # =========================================================================

    def test_observability_missing_telemetry_fails_closed_to_escalate(self):
        """Invariant: Missing required telemetry fields (e.g. supporting_spans) falls back closed to ESCALATE."""
        cand = self._create_valid_direct_candidate()
        cand["supporting_spans"] = [] # Missing mandatory evidence spans
        res = self.aggregator.aggregate([cand])
        self.assertNotEqual(res["action"], "ANSWER")
        self.assertEqual(res["action"], "ESCALATE")
        self.assertIn("Fail-closed", res["reason"])


if __name__ == "__main__":
    unittest.main()
