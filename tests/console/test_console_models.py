"""
Unit tests for Console V0 presentation DTOs.
Verifies:
- Type serialization and format invariants.
- Strict exclusion of raw vector embeddings and internal database credentials.
"""

import unittest
from datetime import datetime, timezone
from console.backend.models import (
    AbstentionDecisionDTO,
    EntityDetailDTO,
    EventDetailDTO,
    EventItemDTO,
    EventListResponseDTO,
    EvidenceLocatorDTO,
    GraphEdgeDTO,
    GraphNodeDTO,
    GraphResponseDTO,
    SearchResponseDTO,
    SearchResultItemDTO,
    SystemStatusDTO,
)


class TestConsoleDTOs(unittest.TestCase):
    """Test suite for DTO serialization and secret exclusion."""

    def test_graph_node_and_edge_serialization(self):
        node = GraphNodeDTO(
            id="node-123",
            entity_type="DECISION",
            title="Adopt Hybrid Search",
            slug="adopt-hybrid-search",
            summary="Hybrid search with RRF",
            promotion_state="VALIDATED",
            conflict_state="RESOLVED",
            confidence_score=0.95,
            valid_from="2026-08-01T00:00:00Z",
            valid_until=None,
            trust_zone="tz_internal_holding",
            project_id="pub-neural",
            evidence_count=2,
        )
        data = node.to_dict()
        self.assertEqual(data["id"], "node-123")
        self.assertEqual(data["entity_type"], "DECISION")
        self.assertNotIn("embedding", data)
        self.assertNotIn("machine_secret", data)

        edge = GraphEdgeDTO(
            id="edge-456",
            source_id="node-123",
            target_id="node-789",
            relation_type="USES",
            weight=1.0,
            is_bidirectional=False,
            trust_zone="tz_internal_holding",
            is_active=True,
        )
        edge_data = edge.to_dict()
        self.assertEqual(edge_data["relation_type"], "USES")

        resp = GraphResponseDTO(
            nodes=[node],
            edges=[edge],
            center_node_id="node-123",
            hop_depth=1,
            total_nodes=1,
            total_edges=1,
        )
        resp_data = resp.to_dict()
        self.assertEqual(resp_data["total_nodes"], 1)
        self.assertEqual(resp_data["center_node_id"], "node-123")

    def test_entity_detail_excludes_secrets(self):
        ev = EvidenceLocatorDTO(
            id="ev-1",
            source_id="src-1",
            repository="pubcoreagencia/pub-neural",
            commit_sha="869abfb",
            file_path="src/retrieval/hybrid_search.py",
            start_line=10,
            end_line=25,
            exact_quote="class HybridSearchEngine:",
            confidence=1.0,
        )
        entity = EntityDetailDTO(
            id="ent-1",
            entity_type="RULE",
            title="Mandatory Session Token",
            slug="mandatory-session-token",
            summary="Attach session before query",
            content="Full rule specification here",
            promotion_state="INSTITUTIONAL",
            promotion_reason="Approved in Phase A",
            conflict_state="RESOLVED",
            confidence_score=1.0,
            superseded_by=None,
            valid_from="2026-08-01T00:00:00Z",
            valid_until=None,
            recorded_from="2026-08-01T00:00:00Z",
            recorded_until=None,
            is_active=True,
            originating_event_id="evt-100",
            last_transition_event_id=None,
            project_id="pub-neural",
            trust_zone="tz_internal_holding",
            created_at="2026-08-01T00:00:00Z",
            updated_at="2026-08-01T00:00:00Z",
            evidence=[ev],
            incoming_relations_count=3,
            outgoing_relations_count=1,
        )
        d = entity.to_dict()
        self.assertEqual(d["id"], "ent-1")
        self.assertEqual(len(d["evidence"]), 1)
        # Verify prohibited fields are absent
        self.assertNotIn("embedding", d)
        self.assertNotIn("raw_vector", d)
        self.assertNotIn("db_url", d)
        self.assertNotIn("connection_string", d)

    def test_search_response_with_abstention(self):
        abstention = AbstentionDecisionDTO(
            accepted=False,
            reason="Max dense similarity below threshold",
            top_dense_similarity=0.45,
            top_rrf_score=0.012,
            lexical_candidate_count=0,
            dense_candidate_count=2,
        )
        search_resp = SearchResponseDTO(
            query="unknown topic",
            status="ABSTAINED",
            results=[],
            abstention_decision=abstention,
            lexical_count=0,
            dense_count=2,
        )
        d = search_resp.to_dict()
        self.assertEqual(d["status"], "ABSTAINED")
        self.assertFalse(d["abstention_decision"]["accepted"])
        self.assertEqual(len(d["results"]), 0)


if __name__ == "__main__":
    unittest.main()
