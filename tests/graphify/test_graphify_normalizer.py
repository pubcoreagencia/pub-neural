"""
Tests for Graphify Normalizer.
Verifies parsing, deterministic canonical identity, confidence preservation, and line range extraction.
"""

import json
import unittest
from pathlib import Path

from src.graphify.normalizer import GraphifyNormalizer, RELATION_MAPPING


class TestGraphifyNormalizer(unittest.TestCase):

    def setUp(self):
        self.normalizer = GraphifyNormalizer(
            project_id="pub-neural",
            repository="pubcoreagencia/pub-neural",
        )
        self.fixture_path = Path(__file__).resolve().parent.parent / "fixtures" / "graphify_sample.json"
        with open(self.fixture_path, "r", encoding="utf-8") as f:
            self.sample_data = json.load(f)

    def test_normalize_nodes(self):
        normalized = self.normalizer.normalize(self.sample_data, commit_sha="test-commit-001")
        self.assertEqual(len(normalized.nodes), 4)

        # Verify deterministic IDs
        auth_service = next(n for n in normalized.nodes if n.title == "AuthService")
        self.assertTrue(auth_service.node_id.startswith("concept:pub-neural:authservice-"))
        self.assertEqual(auth_service.entity_type, "CONCEPT")
        self.assertEqual(auth_service.initial_state, "EXTRACTED")
        self.assertEqual(auth_service.confidence_score, 0.95)

        # Verify document node
        doc_node = next(n for n in normalized.nodes if n.file_type == "document")
        self.assertTrue(doc_node.node_id.startswith("document:pub-neural:"))
        self.assertEqual(doc_node.entity_type, "DOCUMENT")

    def test_deterministic_identity_across_runs(self):
        n1 = self.normalizer.normalize(self.sample_data, commit_sha="test-commit-001")
        n2 = self.normalizer.normalize(self.sample_data, commit_sha="test-commit-001")

        self.assertEqual(
            [n.node_id for n in n1.nodes],
            [n.node_id for n in n2.nodes]
        )
        self.assertEqual(
            [e.edge_id for e in n1.edges],
            [e.edge_id for e in n2.edges]
        )

    def test_relation_mapping_and_confidence_preservation(self):
        normalized = self.normalizer.normalize(self.sample_data, commit_sha="test-commit-001")
        self.assertEqual(len(normalized.edges), 3)

        # calls -> USES (EXTRACTED)
        call_edge = next(e for e in normalized.edges if e.confidence_tier == "EXTRACTED" and e.relation_type == "USES")
        self.assertEqual(call_edge.confidence_score, 1.0)
        self.assertEqual(call_edge.confidence_tier, "EXTRACTED")

        # uses -> USES (INFERRED)
        inferred_edge = next(e for e in normalized.edges if e.confidence_tier == "INFERRED")
        self.assertEqual(inferred_edge.confidence_score, 0.65)
        self.assertEqual(inferred_edge.confidence_tier, "INFERRED")

        # references -> RELATED_TO (EXTRACTED)
        ref_edge = next(e for e in normalized.edges if e.relation_type == "RELATED_TO")
        self.assertEqual(ref_edge.confidence_tier, "EXTRACTED")
        self.assertEqual(ref_edge.confidence_score, 0.95)

    def test_evidence_anchors_created(self):
        normalized = self.normalizer.normalize(self.sample_data, commit_sha="test-commit-001")
        self.assertEqual(len(normalized.evidence), 4)
        for ev in normalized.evidence:
            self.assertGreater(ev.end_line, 0)
            self.assertGreaterEqual(ev.end_line, ev.start_line)
            self.assertTrue(bool(ev.file_path))


if __name__ == "__main__":
    unittest.main()
