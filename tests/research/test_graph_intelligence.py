"""
Tests for Research Graph Intelligence.
Verifies shortest path discovery, dependency analysis, hub/god-node detection, and change impact propagation.
"""

import json
import unittest
from pathlib import Path

from src.graphify.normalizer import GraphifyNormalizer
from src.research.graph_intelligence import ResearchGraphIntelligence


class TestResearchGraphIntelligence(unittest.TestCase):

    def setUp(self):
        normalizer = GraphifyNormalizer(project_id="pub-neural")
        fixture_path = Path(__file__).resolve().parent.parent / "fixtures" / "graphify_sample.json"
        with open(fixture_path, "r", encoding="utf-8") as f:
            sample_data = json.load(f)
        normalized = normalizer.normalize(sample_data, commit_sha="test-commit")
        self.intel = ResearchGraphIntelligence.from_normalized_graph(normalized)

    def test_shortest_path(self):
        nodes = list(self.intel.nodes.keys())
        self.assertGreaterEqual(len(nodes), 2)

        src = next(n for n in nodes if "login" in n)
        tgt = next(n for n in nodes if "get-db-session" in n)

        path_res = self.intel.find_shortest_path(src, tgt)
        self.assertIsNotNone(path_res)
        self.assertEqual(path_res.length, 1)
        self.assertEqual(path_res.path, [src, tgt])
        self.assertIn("USES", path_res.relations)

    def test_dependency_analysis(self):
        nodes = list(self.intel.nodes.keys())
        auth_svc = next(n for n in nodes if "authservice" in n)

        summary = self.intel.analyze_dependencies(auth_svc)
        self.assertIsNotNone(summary)
        self.assertEqual(summary.component_id, auth_svc)
        self.assertGreater(summary.total_degree, 0)

    def test_god_nodes_detection(self):
        gods = self.intel.detect_god_nodes(top_n=3)
        self.assertLessEqual(len(gods), 3)
        # Degree must be non-negative integer
        for node_id, degree in gods:
            self.assertGreaterEqual(degree, 0)

    def test_affected_components_ripple_analysis(self):
        nodes = list(self.intel.nodes.keys())
        db_session = next(n for n in nodes if "get-db-session" in n)

        # When db_session changes, login and AuthService (callers) must be marked affected
        affected = self.intel.analyze_affected_components([db_session], max_depth=2)
        self.assertIn(db_session, affected.changed_nodes)
        self.assertGreater(len(affected.affected_nodes), 0)


if __name__ == "__main__":
    unittest.main()
