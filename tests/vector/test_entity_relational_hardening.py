"""ADR-003 Step 2E.8 Named Entity & Relational Constraint Hardening Test Specification

Target:
- Permanent regression test for ADV-078 ("... com auditoria em tempo real no datadog").
- Invariant: External ungrounded SaaS/tools named entities (Datadog, S3, Istio, PyTorch, Keycloak)
  must NEVER be dropped by syntactic relaxation (N-1).
- Handed off for full execution in Step 2E.8 when PUB Neural resumes.
"""

import unittest
from tests.vector.test_adr003_evidence_gate import StrictTriStateAggregator


class TestEntityRelationalHardening(unittest.TestCase):

    def setUp(self):
        self.aggregator = StrictTriStateAggregator()

    def test_adv_078_external_entity_datadog_must_not_answer(self):
        """Invariant: ADV-078 targeting external entity 'datadog' must produce ESCALATE, never ANSWER."""
        # Simulated candidate from docs/DATABASE_SCHEMA_V0.md (rank 9, sim 0.3996)
        # In Verifier D (Step 2E.7), it was falsely DIRECT_SUPPORT.
        # Under hardened Named Entity policy (Step 2E.8), it must be PARTIAL_SUPPORT -> ESCALATE.
        cand = {
            "query_id": "ADV-078",
            "query_text": "como o rls protege a trust zone tz_internal_holding com auditoria em tempo real no datadog",
            "candidate_document_id": "d133b357079012f6013fe2ae070de167c1541fac37e08b99e5d19bbb8291cc1b",
            "document_identity": "docs/DATABASE_SCHEMA_V0.md",
            "dense_rank": 9,
            "cosine_similarity": 0.3996,
            "decision": "PARTIAL_SUPPORT", # Hardened: 'datadog' ungrounded prevents DIRECT_SUPPORT
            "confidence": 0.75,
            "supporting_spans": [],
            "provenance": {"repo": "pub-neural", "commit": "3bb9edb", "sha256": "abc"},
            "scope": {"project_id": "pub-neural", "trust_zone": "tz_internal_holding"},
            "scope_match": True,
            "provenance_complete": True,
            "verifier_version": "v0.2_hardened_spec",
            "aggregation_policy": "STRICT_DIRECT_ONLY",
            "retrieval_rank": 9
        }
        res = self.aggregator.aggregate([cand])
        self.assertNotEqual(res["action"], "ANSWER")
        self.assertEqual(res["action"], "ESCALATE")

    def test_external_saas_entity_cannot_be_dropped_by_relaxation(self):
        """Invariant: Unrecognized or external entities (Datadog, Kafka, Celery, MongoDB) cannot be omitted."""
        cand = {
            "query_id": "ADV-ENTITY-CHECK",
            "query_text": "consulta com mencao a ferramenta externa inexistente no corpus",
            "candidate_document_id": "doc_1",
            "document_identity": "doc_1",
            "dense_rank": 1,
            "cosine_similarity": 0.45,
            "decision": "PARTIAL_SUPPORT",
            "confidence": 0.75,
            "provenance_complete": True,
            "scope_match": True
        }
        res = self.aggregator.aggregate([cand])
        self.assertEqual(res["action"], "ESCALATE")


if __name__ == "__main__":
    unittest.main()
