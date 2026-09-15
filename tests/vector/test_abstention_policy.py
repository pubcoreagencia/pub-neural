import os
import unittest

from src.retrieval.abstention import RetrievalAbstentionPolicy
from src.retrieval.hybrid_search import HybridSearchEngine


class FakeResult:
    def __init__(self, rrf_score: float = 0.016):
        self.rrf_score = rrf_score


class FakeEmbeddingProvider:
    model_id = "test-model"


class TestRetrievalAbstentionPolicy(unittest.TestCase):
    def test_disabled_policy_accepts_without_gate(self):
        policy = RetrievalAbstentionPolicy.disabled()
        decision = policy.evaluate([], [], [])

        self.assertTrue(decision.accepted)
        self.assertEqual(decision.reason, "POLICY_DISABLED")
        self.assertIsNone(decision.top_dense_similarity)

    def test_enabled_policy_requires_threshold(self):
        with self.assertRaises(ValueError):
            RetrievalAbstentionPolicy(enabled=True)

    def test_unsupported_dense_candidate_can_be_rejected(self):
        policy = RetrievalAbstentionPolicy(
            enabled=True,
            min_dense_similarity=0.90,
            accept_on_lexical_candidate=False,
        )
        decision = policy.evaluate(
            lexical_results=[],
            dense_results=[{"cosine_distance": 0.12}],
            fused_results=[FakeResult()],
        )

        self.assertFalse(decision.accepted)
        self.assertEqual(decision.reason, "DENSE_SIMILARITY_BELOW_THRESHOLD")
        self.assertAlmostEqual(decision.top_dense_similarity, 0.88)

    def test_strong_dense_candidate_is_accepted(self):
        policy = RetrievalAbstentionPolicy(
            enabled=True,
            min_dense_similarity=0.90,
            accept_on_lexical_candidate=False,
        )
        decision = policy.evaluate(
            lexical_results=[],
            dense_results=[{"cosine_distance": 0.05}],
            fused_results=[FakeResult()],
        )

        self.assertTrue(decision.accepted)
        self.assertEqual(decision.reason, "DENSE_SIMILARITY_ABOVE_THRESHOLD")
        self.assertAlmostEqual(decision.top_dense_similarity, 0.95)

    def test_lexical_evidence_can_short_circuit_dense_gate(self):
        policy = RetrievalAbstentionPolicy(
            enabled=True,
            min_dense_similarity=0.95,
            accept_on_lexical_candidate=True,
        )
        decision = policy.evaluate(
            lexical_results=[{"target_id": "NODE:exact"}],
            dense_results=[{"cosine_distance": 0.30}],
            fused_results=[FakeResult()],
        )

        self.assertTrue(decision.accepted)
        self.assertEqual(decision.reason, "LEXICAL_EVIDENCE_PRESENT")

    def test_enabled_policy_abstains_when_no_dense_candidate_exists(self):
        policy = RetrievalAbstentionPolicy(
            enabled=True,
            min_dense_similarity=0.90,
            accept_on_lexical_candidate=False,
        )
        decision = policy.evaluate([], [], [])

        self.assertFalse(decision.accepted)
        self.assertEqual(decision.reason, "NO_DENSE_CANDIDATE")

    def test_environment_factory_defaults_to_disabled(self):
        previous = {
            key: os.environ.get(key)
            for key in (
                "PUB_NEURAL_ABSTENTION_ENABLED",
                "PUB_NEURAL_MIN_DENSE_SIMILARITY",
                "PUB_NEURAL_ABSTENTION_ACCEPT_LEXICAL",
            )
        }
        try:
            for key in previous:
                os.environ.pop(key, None)
            policy = RetrievalAbstentionPolicy.from_environment()
            self.assertFalse(policy.enabled)
        finally:
            for key, value in previous.items():
                if value is None:
                    os.environ.pop(key, None)
                else:
                    os.environ[key] = value

    def test_environment_factory_reads_enabled_threshold(self):
        previous = {
            key: os.environ.get(key)
            for key in (
                "PUB_NEURAL_ABSTENTION_ENABLED",
                "PUB_NEURAL_MIN_DENSE_SIMILARITY",
                "PUB_NEURAL_ABSTENTION_ACCEPT_LEXICAL",
            )
        }
        try:
            os.environ["PUB_NEURAL_ABSTENTION_ENABLED"] = "1"
            os.environ["PUB_NEURAL_MIN_DENSE_SIMILARITY"] = "0.91"
            os.environ["PUB_NEURAL_ABSTENTION_ACCEPT_LEXICAL"] = "0"
            policy = RetrievalAbstentionPolicy.from_environment()
            self.assertTrue(policy.enabled)
            self.assertAlmostEqual(policy.min_dense_similarity, 0.91)
            self.assertFalse(policy.accept_on_lexical_candidate)
        finally:
            for key, value in previous.items():
                if value is None:
                    os.environ.pop(key, None)
                else:
                    os.environ[key] = value

    def test_environment_factory_fails_closed_when_enabled_without_threshold(self):
        previous = {
            key: os.environ.get(key)
            for key in (
                "PUB_NEURAL_ABSTENTION_ENABLED",
                "PUB_NEURAL_MIN_DENSE_SIMILARITY",
                "PUB_NEURAL_ABSTENTION_ACCEPT_LEXICAL",
            )
        }
        try:
            os.environ["PUB_NEURAL_ABSTENTION_ENABLED"] = "true"
            os.environ.pop("PUB_NEURAL_MIN_DENSE_SIMILARITY", None)
            with self.assertRaises(ValueError):
                RetrievalAbstentionPolicy.from_environment()
        finally:
            for key, value in previous.items():
                if value is None:
                    os.environ.pop(key, None)
                else:
                    os.environ[key] = value

    def test_engine_uses_environment_policy_when_policy_not_supplied(self):
        previous = {
            key: os.environ.get(key)
            for key in (
                "PUB_NEURAL_ABSTENTION_ENABLED",
                "PUB_NEURAL_MIN_DENSE_SIMILARITY",
                "PUB_NEURAL_ABSTENTION_ACCEPT_LEXICAL",
            )
        }
        try:
            os.environ["PUB_NEURAL_ABSTENTION_ENABLED"] = "1"
            os.environ["PUB_NEURAL_MIN_DENSE_SIMILARITY"] = "0.92"
            os.environ["PUB_NEURAL_ABSTENTION_ACCEPT_LEXICAL"] = "0"

            engine = HybridSearchEngine(
                db_url="postgresql://unused",
                embedding_provider=FakeEmbeddingProvider(),
            )

            self.assertTrue(engine.abstention_policy.enabled)
            self.assertAlmostEqual(engine.abstention_policy.min_dense_similarity, 0.92)
            self.assertFalse(engine.abstention_policy.accept_on_lexical_candidate)
        finally:
            for key, value in previous.items():
                if value is None:
                    os.environ.pop(key, None)
                else:
                    os.environ[key] = value


if __name__ == "__main__":
    unittest.main()
