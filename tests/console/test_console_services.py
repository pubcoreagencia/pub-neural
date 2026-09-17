"""
Unit tests for Console V0 service logic using test doubles.
Verifies:
- Bounded neighborhood traversal (depth <= 2, limit <= 150).
- Entity detail mapping.
- Search result formatting and abstention mapping.
- Timeline event extraction and pagination.
"""

import unittest
from unittest.mock import MagicMock, patch
from datetime import datetime, timezone

from console.backend.services.graph_service import get_entity_detail, get_neighborhood
from console.backend.services.search_service import execute_console_search
from console.backend.services.status_service import get_system_status
from console.backend.services.timeline_service import get_event_detail, get_events_list
from src.retrieval.abstention import AbstentionDecision
from src.retrieval.hybrid_search import HybridSearchResult


class TestConsoleServices(unittest.TestCase):
    """Test suite for service layers."""

    def test_get_entity_detail_found(self):
        mock_cur = MagicMock()
        mock_cur.fetchone.side_effect = [
            # Entity row
            {
                "id": "node-1",
                "entity_type": "DECISION",
                "title": "Dec 1",
                "slug": "dec-1",
                "summary": "Summary",
                "content": "Content",
                "promotion_state": "VALIDATED",
                "promotion_reason": "Pass",
                "conflict_state": "RESOLVED",
                "confidence_score": 0.9,
                "superseded_by": None,
                "valid_from": datetime.now(timezone.utc),
                "valid_until": None,
                "recorded_from": datetime.now(timezone.utc),
                "recorded_until": None,
                "is_active": True,
                "originating_event_id": "00000000-0000-0000-0000-000000000001",
                "last_transition_event_id": None,
                "project_id": "proj-1",
                "trust_zone": "tz_internal_holding",
                "created_at": datetime.now(timezone.utc),
                "updated_at": datetime.now(timezone.utc),
            },
            # Counts
            {"incoming_count": 5, "outgoing_count": 2},
        ]
        mock_cur.fetchall.return_value = [
            # Evidence
            {
                "id": "00000000-0000-0000-0000-000000000002",
                "source_id": "00000000-0000-0000-0000-000000000003",
                "start_line": 10,
                "end_line": 20,
                "exact_quote": "test quote",
                "confidence": 1.0,
                "repository": "repo-a",
                "commit_sha": "abc1234",
                "file_path": "foo.py",
            }
        ]

        entity = get_entity_detail(mock_cur, "node-1")
        self.assertIsNotNone(entity)
        self.assertEqual(entity.id, "node-1")
        self.assertEqual(entity.title, "Dec 1")
        self.assertEqual(entity.incoming_relations_count, 5)
        self.assertEqual(len(entity.evidence), 1)
        self.assertEqual(entity.evidence[0].file_path, "foo.py")

    def test_get_entity_detail_not_found(self):
        mock_cur = MagicMock()
        mock_cur.fetchone.return_value = None
        entity = get_entity_detail(mock_cur, "non-existent")
        self.assertIsNone(entity)

    def test_get_neighborhood_bounded(self):
        mock_cur = MagicMock()
        # Mock edges return
        mock_cur.fetchall.side_effect = [
            # Edges
            [
                {
                    "edge_id": "00000000-0000-0000-0000-000000000010",
                    "source_id": "node-1",
                    "target_id": "node-2",
                    "relation_type": "DEPENDS_ON",
                    "weight": 0.8,
                    "is_bidirectional": False,
                    "trust_zone": "tz_internal_holding",
                    "is_active": True,
                }
            ],
            # Nodes
            [
                {
                    "id": "node-1",
                    "entity_type": "DECISION",
                    "title": "Dec 1",
                    "slug": "dec-1",
                    "summary": "Sum 1",
                    "promotion_state": "VALIDATED",
                    "conflict_state": "RESOLVED",
                    "confidence_score": 1.0,
                    "valid_from": datetime.now(timezone.utc),
                    "valid_until": None,
                    "trust_zone": "tz_internal_holding",
                    "project_id": "p1",
                    "evidence_count": 1,
                },
                {
                    "id": "node-2",
                    "entity_type": "RULE",
                    "title": "Rule 2",
                    "slug": "rule-2",
                    "summary": "Sum 2",
                    "promotion_state": "VALIDATED",
                    "conflict_state": "RESOLVED",
                    "confidence_score": 1.0,
                    "valid_from": datetime.now(timezone.utc),
                    "valid_until": None,
                    "trust_zone": "tz_internal_holding",
                    "project_id": "p1",
                    "evidence_count": 0,
                },
            ],
        ]

        # Request depth 5 and limit 500 -> must bound to depth 2 and limit 150
        graph = get_neighborhood(mock_cur, "node-1", depth=5, limit=500)
        self.assertEqual(graph.hop_depth, 2)
        self.assertEqual(graph.total_nodes, 2)
        self.assertEqual(graph.total_edges, 1)

    def test_timeline_service(self):
        mock_cur = MagicMock()
        mock_cur.fetchall.return_value = [
            {
                "id": "00000000-0000-0000-0000-000000000020",
                "global_sequence": 42,
                "event_type": "DECISION_RATIFIED",
                "event_version": 1,
                "producer_version": "v1.0.0",
                "stream_id": "stream-1",
                "stream_version": 1,
                "actor_id": "actor-ceo",
                "actor_role": "CEO",
                "recorded_at": datetime.now(timezone.utc),
            }
        ]

        events = get_events_list(mock_cur, limit=10, offset=0)
        self.assertEqual(events.total_returned, 1)
        self.assertEqual(events.events[0].global_sequence, 42)
        self.assertEqual(events.events[0].event_type, "DECISION_RATIFIED")



    def test_status_service_capabilities(self):
        mock_cur = MagicMock()
        mock_cur.fetchone.side_effect = [
            {"version": "PostgreSQL 16.3 on x86_64"},
            {"actor_role": "CEO", "active_trust_zone": "tz_internal_holding", "active_project_id": "pub-neural"},
        ]
        mock_cur.fetchall.return_value = [
            {
                "projector_name": "projector_main",
                "last_processed_global_sequence": 142,
                "status": "HEALTHY",
                "last_checkpoint_at": datetime.now(timezone.utc),
                "error_detail": None,
            }
        ]

        status = get_system_status(mock_cur, bearer_token="dummy_token")
        self.assertEqual(status.status, "HEALTHY")
        self.assertEqual(status.active_actor_role, "CEO")
        self.assertEqual(status.active_trust_zone, "tz_internal_holding")
        self.assertEqual(len(status.projector_checkpoints), 1)
        self.assertIn("ACTIVE", status.capabilities["database_engine"])
        self.assertIn("NOT IMPLEMENTED", status.capabilities["production_network_transport"])

    def test_search_service_abstention_mapping(self):
        with patch("console.backend.services.search_service.HybridSearchEngine") as mock_engine_cls:
            mock_engine = MagicMock()
            mock_engine_cls.return_value = mock_engine

            abstention = AbstentionDecision(
                accepted=False,
                reason="Confidence score below threshold",
                top_dense_similarity=0.35,
                top_rrf_score=0.008,
                lexical_candidate_count=0,
                dense_candidate_count=1,
            )

            mock_engine.search_detailed.return_value = {
                "results": [],
                "abstention_decision": abstention,
                "lexical_count": 0,
                "dense_count": 1,
            }

            resp = execute_console_search(
                db_url="postgresql://dummy",
                bearer_token="valid_token",
                query="unsupported query",
            )
            self.assertEqual(resp.status, "ABSTAINED")
            self.assertFalse(resp.abstention_decision.accepted)
            self.assertEqual(len(resp.results), 0)

    def test_get_graph_backbone(self):
        from console.backend.services.graph_service import get_graph_backbone

        mock_cur = MagicMock()
        mock_cur.fetchall.side_effect = [
            # Node rows
            [
                {
                    "id": "project:pub-ecom",
                    "entity_type": "PROJECT",
                    "title": "PUB Ecom",
                    "slug": "pub-ecom",
                    "summary": "Commerce system",
                    "promotion_state": "VALIDATED",
                    "conflict_state": "RESOLVED",
                    "confidence_score": 1.0,
                    "valid_from": datetime.now(timezone.utc),
                    "valid_until": None,
                    "trust_zone": "tz_internal_holding",
                    "project_id": "pub-ecom",
                    "evidence_count": 2,
                },
                {
                    "id": "rule:pub-core:zero-mutation",
                    "entity_type": "RULE",
                    "title": "Zero Mutation",
                    "slug": "zero-mutation",
                    "summary": "Rule",
                    "promotion_state": "VALIDATED",
                    "conflict_state": "RESOLVED",
                    "confidence_score": 1.0,
                    "valid_from": datetime.now(timezone.utc),
                    "valid_until": None,
                    "trust_zone": "tz_internal_holding",
                    "project_id": None,
                    "evidence_count": 5,
                },
            ],
            # Edge rows
            [
                {
                    "edge_id": "00000000-0000-0000-0000-000000000099",
                    "source_id": "project:pub-ecom",
                    "target_id": "rule:pub-core:zero-mutation",
                    "relation_type": "IMPLEMENTS",
                    "weight": 1.0,
                    "is_bidirectional": False,
                    "trust_zone": "tz_internal_holding",
                    "is_active": True,
                }
            ],
        ]

        backbone = get_graph_backbone(mock_cur, limit=50)
        self.assertEqual(backbone.total_nodes, 2)
        self.assertEqual(backbone.total_edges, 1)
        self.assertEqual(backbone.nodes[0].id, "project:pub-ecom")
        self.assertEqual(backbone.edges[0].relation_type, "IMPLEMENTS")

    def test_get_edge_detail_found(self):
        from console.backend.services.graph_service import get_edge_detail

        mock_cur = MagicMock()
        mock_cur.fetchone.return_value = {
            "id": "edge-1",
            "source_id": "node-1",
            "target_id": "node-2",
            "relation_type": "USES",
            "weight": 0.95,
            "is_bidirectional": False,
            "trust_zone": "tz_internal_holding",
            "is_active": True,
            "valid_from": datetime.now(timezone.utc),
            "valid_until": None,
            "recorded_from": datetime.now(timezone.utc),
            "recorded_until": None,
            "originating_event_id": "00000000-0000-0000-0000-000000000001",
            "last_transition_event_id": None,
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc),
        }
        mock_cur.fetchall.return_value = [
            {
                "id": "ev-1",
                "source_id": "src-1",
                "start_line": 15,
                "end_line": 25,
                "exact_quote": "import foo",
                "confidence": 0.95,
                "validation_state": "VALIDATED",
                "extractor_version": "graphify-v8",
                "repository": "pubcore/repo",
                "commit_sha": "abc1234",
                "file_path": "main.py",
            }
        ]

        detail = get_edge_detail(mock_cur, "edge-1")
        self.assertIsNotNone(detail)
        self.assertEqual(detail.id, "edge-1")
        self.assertEqual(detail.relation_type, "USES")
        self.assertEqual(detail.extractor, "graphify-v8")
        self.assertEqual(detail.epistemic_classification, "EXTRACTED")
        self.assertEqual(len(detail.evidence), 1)

    def test_get_edge_detail_not_found(self):
        from console.backend.services.graph_service import get_edge_detail

        mock_cur = MagicMock()
        mock_cur.fetchone.return_value = None
        detail = get_edge_detail(mock_cur, "non-existent")
        self.assertIsNone(detail)

if __name__ == "__main__":
    unittest.main()
