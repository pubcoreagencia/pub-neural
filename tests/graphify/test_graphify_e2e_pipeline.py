"""
End-to-end integration proof test for the complete Graphify pipeline in PUB Neural:
  Fixture Repo -> Graphify Output -> Adapter -> Normalizer -> Ingestor ->
  Canonical Events -> GraphSearch -> HybridSearch (3-Way) -> Research Intelligence.
"""

import json
import unittest
from pathlib import Path

from src.graphify.adapter import GraphifyAdapter
from src.graphify.normalizer import GraphifyNormalizer
from src.graphify.ingestor import GraphifyIngestor
from src.retrieval.graph_search import GraphSearchEngine
from src.retrieval.hybrid_search import HybridSearchEngine
from src.retrieval.abstention import RetrievalAbstentionPolicy
from src.research.graph_intelligence import ResearchGraphIntelligence


class TestRealE2EGraphifyIntegration(unittest.TestCase):
    """
    Validates that real structured data flows end-to-end across all integration layers.
    Exposes explicitly which components are real and which boundaries are mocked.
    """

    def setUp(self):
        # 1. Real Fixture file representing Graphify external output
        self.fixture_path = Path(__file__).resolve().parent.parent / "fixtures" / "graphify_sample.json"
        with open(self.fixture_path, "r", encoding="utf-8") as f:
            self.fixture_data = json.load(f)

    def test_complete_e2e_data_pipeline(self):
        # STEP 1: Adapter (REAL security scanner and file parser)
        adapter = GraphifyAdapter()
        parsed_data = adapter.parse_graph_json(self.fixture_path)
        self.assertIn("nodes", parsed_data)
        self.assertIn("links", parsed_data)
        self.assertEqual(len(parsed_data["nodes"]), 4)

        # STEP 2: Normalizer (REAL canonical mapper & deterministic UUID generator)
        normalizer = GraphifyNormalizer(project_id="pub-neural", repository="pubcoreagencia/pub-neural")
        normalized = normalizer.normalize(parsed_data, commit_sha="e2e-sha-999")
        self.assertEqual(len(normalized.nodes), 4)
        self.assertEqual(len(normalized.edges), 3)
        self.assertEqual(len(normalized.evidence), 4)

        # Epistemic assertion: EXTRACTED vs INFERRED
        extracted_edges = [e for e in normalized.edges if e.confidence_tier == "EXTRACTED"]
        inferred_edges = [e for e in normalized.edges if e.confidence_tier == "INFERRED"]
        self.assertEqual(len(extracted_edges), 2)
        self.assertEqual(len(inferred_edges), 1)
        self.assertAlmostEqual(inferred_edges[0].confidence_score, 0.65)

        # STEP 3: Ingestor (REAL event generation)
        ingestor = GraphifyIngestor(client=None)
        batch = ingestor.build_event_batch(normalized)
        self.assertEqual(batch["node_count"], 4)
        self.assertEqual(batch["edge_count"], 3)
        self.assertEqual(len(batch["events"]), 7)  # 4 entities + 3 relations

        # STEP 4: Graph Retrieval (REAL BFS neighborhood expansion over normalized graph)
        graph_nodes = [
            {
                "id": n.node_id,
                "title": n.title,
                "summary": n.summary,
                "content": n.content,
                "trust_zone": normalized.trust_zone,
                "project_id": normalized.project_id,
                "originating_event_id": str(n.event_id),
                "content_hash": n.content_hash,
            }
            for n in normalized.nodes
        ]
        graph_edges = [
            {
                "source_id": e.source_id,
                "target_id": e.target_id,
                "relation_type": e.relation_type,
                "weight": e.weight,
            }
            for e in normalized.edges
        ]

        graph_engine = GraphSearchEngine()
        graph_results = graph_engine.search_graph(
            query="login",
            limit=5,
            in_memory_nodes=graph_nodes,
            in_memory_edges=graph_edges,
        )
        self.assertGreaterEqual(len(graph_results), 2)
        self.assertTrue("login" in graph_results[0].target_id)
        # Login calls get_db_session -> must be discovered as connected neighbor
        self.assertTrue(any("get-db-session" in r.target_id for r in graph_results))

        # STEP 5: Hybrid Retrieval (REAL 3-Way RRF Fusion)
        class MockDim1536Provider:
            model_id = "mock-1536"
            def generate_embedding(self, _):
                return [0.0] * 1536

        hybrid_engine = HybridSearchEngine(
            db_url="postgresql://mock",
            embedding_provider=MockDim1536Provider(),
            graph_engine=graph_engine,
            abstention_policy=RetrievalAbstentionPolicy.disabled(),
        )

        lexical_candidates = [
            {
                "target_id": graph_nodes[0]["id"],
                "target_type": "NODE",
                "title": graph_nodes[0]["title"],
                "snippet": graph_nodes[0]["summary"],
                "lexical_rank": 1,
                "trust_zone": "tz_internal_holding",
                "project_id": "pub-neural",
                "originating_event_id": graph_nodes[0]["originating_event_id"],
                "content_hash": graph_nodes[0]["content_hash"],
                "evidence_id": None,
                "source_id": None,
            }
        ]
        dense_candidates = [
            {
                "target_id": graph_nodes[0]["id"],
                "target_type": "NODE",
                "title": graph_nodes[0]["title"],
                "snippet": graph_nodes[0]["summary"],
                "dense_rank": 1,
                "cosine_distance": 0.12,
                "trust_zone": "tz_internal_holding",
                "project_id": "pub-neural",
                "originating_event_id": graph_nodes[0]["originating_event_id"],
                "content_hash": graph_nodes[0]["content_hash"],
                "evidence_id": None,
                "source_id": None,
            }
        ]

        fused = hybrid_engine._fuse_rrf(lexical_candidates, dense_candidates, graph_results)
        self.assertGreaterEqual(len(fused), 2)
        top_fused = fused[0]
        self.assertEqual(top_fused.target_id, graph_nodes[0]["id"])
        # Both lexical and dense contributed
        self.assertEqual(top_fused.lexical_rank, 1)
        self.assertEqual(top_fused.dense_rank, 1)

        # Neighbor from graph contributed with graph_rank
        graph_only_item = next(f for f in fused if f.target_id != graph_nodes[0]["id"])
        self.assertIsNotNone(graph_only_item.graph_rank)
        self.assertIsNotNone(graph_only_item.structural_explanation)

        # STEP 6: Research Intelligence (REAL Topological Cognitive Service)
        intel = ResearchGraphIntelligence.from_normalized_graph(normalized)
        all_ids = list(intel.nodes.keys())

        login_id = next(i for i in all_ids if "login" in i)
        db_id = next(i for i in all_ids if "get-db-session" in i)

        # Path discovery
        path = intel.find_shortest_path(login_id, db_id)
        self.assertIsNotNone(path)
        self.assertEqual(path.length, 1)
        self.assertEqual(path.relations, ["USES"])

        # Dependency & Hub analysis
        deps = intel.analyze_dependencies(login_id)
        self.assertIn(db_id, deps.dependencies)

        # Change impact / ripple analysis
        impact = intel.analyze_affected_components([db_id], max_depth=2)
        self.assertIn(login_id, impact.affected_nodes)


if __name__ == "__main__":
    unittest.main()
