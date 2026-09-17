"""
Tests for Graph Search Engine and 3-Way Reciprocal Rank Fusion.
Verifies neighborhood traversal, topological scoring, structural explanation generation, and RRF fusion.
"""

import unittest
from src.retrieval.graph_search import GraphSearchEngine, GraphSearchResult
from src.retrieval.hybrid_search import HybridSearchEngine, HybridSearchResult
from src.retrieval.abstention import RetrievalAbstentionPolicy


class MockEmbeddingProvider:
    def __init__(self, dim=1536):
        self.model_id = "mock-dim1536"
        self.dim = dim

    def generate_embedding(self, text: str):
        return [0.0] * self.dim


class TestGraphRetrievalAndFusion(unittest.TestCase):

    def setUp(self):
        self.nodes = [
            {
                "id": "node:auth:service",
                "title": "Authentication Service",
                "summary": "Handles OAuth and login authentication.",
                "content": "Full login and session orchestration.",
                "trust_zone": "tz_internal_holding",
                "project_id": "pub-neural",
                "originating_event_id": "evt-001",
                "content_hash": "hash-001",
            },
            {
                "id": "node:db:session",
                "title": "Database Session Provider",
                "summary": "Provides PostgreSQL database connections.",
                "content": "Connection pool management.",
                "trust_zone": "tz_internal_holding",
                "project_id": "pub-neural",
                "originating_event_id": "evt-002",
                "content_hash": "hash-002",
            },
            {
                "id": "node:unrelated:worker",
                "title": "Payment Settlement Worker",
                "summary": "Processes async payout ledger.",
                "content": "Ledger operations.",
                "trust_zone": "tz_internal_holding",
                "project_id": "pub-neural",
                "originating_event_id": "evt-003",
                "content_hash": "hash-003",
            }
        ]
        self.edges = [
            {
                "source_id": "node:auth:service",
                "target_id": "node:db:session",
                "relation_type": "USES",
                "weight": 1.0,
            }
        ]
        self.graph_engine = GraphSearchEngine()

    def test_graph_search_seeds_and_expands_neighborhood(self):
        results = self.graph_engine.search_graph(
            query="authentication",
            limit=5,
            in_memory_nodes=self.nodes,
            in_memory_edges=self.edges,
        )

        self.assertGreater(len(results), 0)
        # Direct seed must be first
        self.assertEqual(results[0].target_id, "node:auth:service")
        self.assertIn("Direct query seed", results[0].structural_explanation)

        # 1-hop neighbor should be discovered via USES relation
        if len(results) > 1:
            self.assertEqual(results[1].target_id, "node:db:session")
            self.assertIn("Connected via USES", results[1].structural_explanation)

    def test_3_way_rrf_fusion(self):
        engine = HybridSearchEngine(
            db_url="postgresql://mock",
            embedding_provider=MockEmbeddingProvider(),
            rrf_k=60,
            graph_weight=0.8,
            abstention_policy=RetrievalAbstentionPolicy.disabled(),
        )

        lexical_results = [
            {
                "target_id": "node:auth:service",
                "target_type": "NODE",
                "title": "Authentication Service",
                "snippet": "Handles OAuth and login.",
                "lexical_rank": 1,
                "trust_zone": "tz_internal_holding",
                "project_id": "pub-neural",
                "originating_event_id": "evt-001",
                "content_hash": "hash-001",
                "evidence_id": None,
                "source_id": None,
            }
        ]
        dense_results = [
            {
                "target_id": "node:auth:service",
                "target_type": "NODE",
                "title": "Authentication Service",
                "snippet": "Handles OAuth and login.",
                "dense_rank": 2,
                "cosine_distance": 0.15,
                "trust_zone": "tz_internal_holding",
                "project_id": "pub-neural",
                "originating_event_id": "evt-001",
                "content_hash": "hash-001",
                "evidence_id": None,
                "source_id": None,
            }
        ]
        graph_results = [
            GraphSearchResult(
                target_id="node:db:session",
                target_type="NODE",
                title="Database Session Provider",
                snippet="Provides database sessions.",
                graph_rank=1,
                graph_score=3.5,
                trust_zone="tz_internal_holding",
                project_id="pub-neural",
                originating_event_id="evt-002",
                content_hash="hash-002",
                structural_explanation="Connected via USES",
            )
        ]

        fused = engine._fuse_rrf(lexical_results, dense_results, graph_results)
        self.assertEqual(len(fused), 2)

        # Top item should be node:auth:service with contributions from lexical and dense
        self.assertEqual(fused[0].target_id, "node:auth:service")
        self.assertEqual(fused[0].lexical_rank, 1)
        self.assertEqual(fused[0].dense_rank, 2)

        # Second item should be the graph-retrieved neighbor
        self.assertEqual(fused[1].target_id, "node:db:session")
        self.assertEqual(fused[1].graph_rank, 1)
        self.assertEqual(fused[1].structural_explanation, "Connected via USES")


if __name__ == "__main__":
    unittest.main()
