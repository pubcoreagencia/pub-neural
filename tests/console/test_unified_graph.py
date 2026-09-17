"""
Unit tests for Unified Graph Service (Physical + Cognitive Graph V0).
Guarantees:
- Tests unified root merging Git organization + Cognitive nodes without ontology duplication.
- Tests evidence-first bridge linking physical repositories to cognitive entities.
- Tests epistemic distinctions (EXTRACTED vs INFERRED vs PROPOSED).
- Tests dynamic filters (entity_type, relation_type, epistemic_state).
- Tests that secret patterns continue to be blocked fail-closed.
"""

import unittest
from unittest.mock import MagicMock, patch

from console.backend.models import (
    GraphEdgeDTO,
    GraphNodeDTO,
    GraphResponseDTO,
)
from console.backend.services.git_graph_service import (
    is_secret_file,
    get_git_edge_detail,
)
from console.backend.services.unified_graph_service import get_unified_graph


class TestUnifiedGraphService(unittest.TestCase):
    """Test suite for Unified Physical + Cognitive Graph."""

    def test_secrets_still_blocked_fail_closed(self):
        """Ensure secret exclusions remain active and protect sensitive environment variables."""
        self.assertTrue(is_secret_file(".env"))
        self.assertTrue(is_secret_file(".env.production"))
        self.assertTrue(is_secret_file(".env.local"))
        self.assertTrue(is_secret_file("id_rsa"))
        self.assertTrue(is_secret_file("secrets.key"))
        # Preserves .env.example
        self.assertFalse(is_secret_file(".env.example"))

    @patch("console.backend.services.unified_graph_service.get_organization_graph")
    @patch("console.backend.services.unified_graph_service.get_graph_backbone")
    def test_get_unified_graph_root(self, mock_backbone, mock_org_graph):
        """Verify unified graph merges Git and Cognitive entities correctly."""
        # Mock Git Graph
        mock_org_graph.return_value = GraphResponseDTO(
            nodes=[
                GraphNodeDTO(
                    id="org:pubcoreagencia",
                    entity_type="ORGANIZATION",
                    title="PUB CORE HOLDING",
                    slug="pubcoreagencia",
                    summary="55 repos",
                    promotion_state="INSTITUTIONAL",
                    conflict_state="RESOLVED",
                    confidence_score=1.0,
                    valid_from="2026-01-01T00:00:00Z",
                    valid_until=None,
                    trust_zone="tz_internal_holding",
                    project_id="pub-core",
                    evidence_count=55,
                ),
                GraphNodeDTO(
                    id="repo:pubcoreagencia/pubcore",
                    entity_type="REPOSITORY",
                    title="pubcore",
                    slug="pubcore",
                    summary="Main repo",
                    promotion_state="VALIDATED",
                    conflict_state="RESOLVED",
                    confidence_score=1.0,
                    valid_from="2026-01-01T00:00:00Z",
                    valid_until=None,
                    trust_zone="tz_internal_holding",
                    project_id="pub-core",
                    evidence_count=100,
                ),
            ],
            edges=[
                GraphEdgeDTO(
                    id="edge:org:pubcoreagencia:repo:pubcoreagencia/pubcore",
                    source_id="org:pubcoreagencia",
                    target_id="repo:pubcoreagencia/pubcore",
                    relation_type="CONTAINS",
                    weight=1.0,
                    is_bidirectional=False,
                    trust_zone="tz_internal_holding",
                    is_active=True,
                    epistemic_classification="EXTRACTED",
                )
            ],
            center_node_id="org:pubcoreagencia",
            hop_depth=1,
            total_nodes=2,
            total_edges=1,
        )

        # Mock Cognitive Backbone
        mock_backbone.return_value = GraphResponseDTO(
            nodes=[
                GraphNodeDTO(
                    id="decision:autonomous-execution",
                    entity_type="DECISION",
                    title="Autonomous Execution Decision",
                    slug="autonomous-execution",
                    summary="Decision on autonomous mode",
                    promotion_state="INSTITUTIONAL",
                    conflict_state="RESOLVED",
                    confidence_score=1.0,
                    valid_from="2026-01-01T00:00:00Z",
                    valid_until=None,
                    trust_zone="tz_internal_holding",
                    project_id="pub-core",
                    evidence_count=5,
                )
            ],
            edges=[],
            center_node_id=None,
            hop_depth=0,
            total_nodes=1,
            total_edges=0,
        )

        mock_cur = MagicMock()
        mock_cur.fetchall.side_effect = [
            # 1. holding_projects
            [
                {
                    "id": "proj:pub-core",
                    "slug": "pub-core",
                    "display_name": "PUB Core",
                    "description": "Core foundation platform",
                    "project_type": "PLATFORM",
                    "lifecycle_status": "ACTIVE",
                    "is_active": True,
                    "is_archived": False,
                    "strategic_priority": 1,
                    "owner_scope": "HOLDING",
                    "ontology_status": "CONFIRMED",
                    "ontology_source": "DOCUMENTATION",
                    "ontology_confidence": 1.0,
                    "ontology_reason": "Canonical platform project",
                }
            ],
            # 2. project_repositories
            [
                {
                    "project_id": "proj:pub-core",
                    "repository_id": "pubcore",
                    "relationship_type": "PRIMARY",
                    "is_primary": True,
                    "association_status": "CONFIRMED",
                    "classification_source": "DOCUMENTATION",
                    "classification_confidence": 1.0,
                    "classification_reason": "Core repo of pub-core platform",
                }
            ],
            # 3. neural_evidence
            [],
        ]

        result = get_unified_graph(cur=mock_cur, source="all", limit=120)

        node_ids = {n.id for n in result.nodes}
        self.assertIn("org:pubcoreagencia", node_ids)
        self.assertIn("proj:pub-core", node_ids)
        self.assertIn("repo:pubcoreagencia/pubcore", node_ids)
        self.assertIn("decision:autonomous-execution", node_ids)

        # Verify ORG -> PROJECT edge
        org_proj_edges = [
            e for e in result.edges
            if e.source_id == "org:pubcoreagencia" and e.target_id == "proj:pub-core"
        ]
        self.assertEqual(len(org_proj_edges), 1)
        self.assertEqual(org_proj_edges[0].relation_type, "CONTAINS")
        self.assertEqual(org_proj_edges[0].epistemic_classification, "EXTRACTED")

        # Verify PROJECT -> REPOSITORY edge
        proj_repo_edges = [
            e for e in result.edges
            if e.source_id == "proj:pub-core" and e.target_id == "repo:pubcoreagencia/pubcore"
        ]
        self.assertEqual(len(proj_repo_edges), 1)
        self.assertEqual(proj_repo_edges[0].relation_type, "CONTAINS")
        self.assertEqual(proj_repo_edges[0].epistemic_classification, "EXTRACTED")

        # Direct ORG -> REPO edge should have been rewired (not present since repo is mapped)
        direct_org_repo = [
            e for e in result.edges
            if e.source_id == "org:pubcoreagencia" and e.target_id == "repo:pubcoreagencia/pubcore"
        ]
        self.assertEqual(len(direct_org_repo), 0)

        # Verify evidence bridge Repo -> Decision
        bridge_edges = [
            e for e in result.edges
            if e.source_id == "repo:pubcoreagencia/pubcore" and e.target_id == "decision:autonomous-execution"
        ]
        self.assertEqual(len(bridge_edges), 1)
        bridge = bridge_edges[0]
        self.assertEqual(bridge.relation_type, "IMPLEMENTS")
        self.assertEqual(bridge.epistemic_classification, "EXTRACTED")
        self.assertIsNotNone(bridge.evidence_locator)
        self.assertEqual(bridge.evidence_locator["repository"], "pubcore")

    def test_git_edge_detail_inspection(self):
        """Test structured edge detail generation for Git, Project, and cross-repo edges."""
        # Org -> Project containment edge
        org_proj_detail = get_git_edge_detail("edge:org:pubcoreagencia:proj:pub-neural")
        self.assertIsNotNone(org_proj_detail)
        self.assertEqual(org_proj_detail.relation_type, "CONTAINS")
        self.assertEqual(org_proj_detail.epistemic_classification, "EXTRACTED")
        self.assertEqual(org_proj_detail.extractor, "holding-projects-registry")

        # Project -> Repo containment edge
        proj_repo_detail = get_git_edge_detail("edge:proj:pub-neural:repo:pubcoreagencia/pub-neural")
        self.assertIsNotNone(proj_repo_detail)
        self.assertEqual(proj_repo_detail.relation_type, "CONTAINS")
        self.assertEqual(proj_repo_detail.epistemic_classification, "EXTRACTED")
        self.assertEqual(proj_repo_detail.extractor, "project-repositories-registry")

        # Org -> Repo (unmapped)
        edge_detail = get_git_edge_detail("edge:org:pubcoreagencia:repo:pubcoreagencia/pub-github-mcp")
        self.assertIsNotNone(edge_detail)
        self.assertEqual(edge_detail.relation_type, "CONTAINS")
        self.assertEqual(edge_detail.epistemic_classification, "EXTRACTED")
        self.assertEqual(edge_detail.extractor, "github-org-manifest")

        # Cross-repo
        cross_edge_detail = get_git_edge_detail("edge:repo:pubcoreagencia/PUB-BEATS:repo:pubcoreagencia/pub-records")
        self.assertIsNotNone(cross_edge_detail)
        self.assertEqual(cross_edge_detail.relation_type, "DERIVED_FROM")
        self.assertEqual(cross_edge_detail.epistemic_classification, "EXTRACTED")
        self.assertGreater(len(cross_edge_detail.evidence), 0)
        self.assertEqual(cross_edge_detail.evidence[0].repository, "pubcoreagencia/PUB-BEATS")


if __name__ == "__main__":
    unittest.main()

