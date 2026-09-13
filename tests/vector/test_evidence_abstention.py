import unittest

from src.retrieval.evidence_abstention import (
    EvidenceDecision,
    EvidencePolicy,
    EvidenceSignals,
    ReasonCode,
    assess_evidence,
)


class TestEvidenceAbstention(unittest.TestCase):
    def setUp(self):
        self.policy = EvidencePolicy(
            min_coverage=0.80,
            min_verifier_score=0.80,
            min_provenance_quality=0.50,
        )

    def test_sufficient_evidence_answers(self):
        result = assess_evidence(
            EvidenceSignals(
                evidence_coverage=0.95,
                verifier_score=0.92,
                scope_compatible=True,
                contradiction=False,
                provenance_quality=0.90,
            ),
            self.policy,
        )
        self.assertEqual(result.decision, EvidenceDecision.ANSWER)
        self.assertEqual(result.reason_codes, [ReasonCode.SUFFICIENT_EVIDENCE])

    def test_out_of_scope_abstains_before_scores(self):
        result = assess_evidence(
            EvidenceSignals(
                evidence_coverage=1.0,
                verifier_score=1.0,
                scope_compatible=False,
                contradiction=False,
                provenance_quality=1.0,
            ),
            self.policy,
        )
        self.assertEqual(result.decision, EvidenceDecision.ABSTAIN)
        self.assertIn(ReasonCode.OUT_OF_SCOPE, result.reason_codes)

    def test_contradiction_escalates(self):
        result = assess_evidence(
            EvidenceSignals(
                evidence_coverage=1.0,
                verifier_score=0.95,
                scope_compatible=True,
                contradiction=True,
                provenance_quality=1.0,
            ),
            self.policy,
        )
        self.assertEqual(result.decision, EvidenceDecision.ESCALATE)
        self.assertIn(ReasonCode.CONTRADICTORY_EVIDENCE, result.reason_codes)

    def test_low_coverage_abstains(self):
        result = assess_evidence(
            EvidenceSignals(
                evidence_coverage=0.30,
                verifier_score=0.95,
                scope_compatible=True,
                contradiction=False,
                provenance_quality=1.0,
            ),
            self.policy,
        )
        self.assertEqual(result.decision, EvidenceDecision.ABSTAIN)
        self.assertIn(ReasonCode.INSUFFICIENT_COVERAGE, result.reason_codes)

    def test_missing_verifier_escalates(self):
        result = assess_evidence(
            EvidenceSignals(
                evidence_coverage=0.95,
                verifier_score=None,
                scope_compatible=True,
                contradiction=False,
                provenance_quality=0.90,
            ),
            self.policy,
        )
        self.assertEqual(result.decision, EvidenceDecision.ESCALATE)
        self.assertIn(ReasonCode.ESCALATION_REQUIRED, result.reason_codes)

    def test_dense_or_rrf_are_not_used_as_answerability(self):
        # The evaluator intentionally has no dense/RRF parameters. This test
        # documents the architectural separation established by ADR-002.
        result = assess_evidence(
            EvidenceSignals(
                evidence_coverage=0.90,
                verifier_score=0.90,
                scope_compatible=True,
                contradiction=False,
                provenance_quality=0.90,
            ),
            self.policy,
        )
        self.assertEqual(result.decision, EvidenceDecision.ANSWER)


if __name__ == "__main__":
    unittest.main()
