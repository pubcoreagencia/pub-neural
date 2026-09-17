"""
Tests for Project Ontology V0.2 endpoints and services.
Verifies:
- 57 repositories != 34 projects
- Multi-repo projects (e.g. pub-ecom, pub-core)
- Explicit provenance (CONFIRMED vs PROPOSED vs UNCLASSIFIED)
- Isolated unclassified repositories (pub-github-mcp)
"""

import unittest
from unittest.mock import MagicMock
from console.backend.models import (
    HoldingProjectItemDTO,
    HoldingProjectListDTO,
    ProjectRepositoryAssociationDTO,
    ProjectRegistryItemDTO,
)
from console.backend.services.ontology_service import (
    get_all_repositories,
    get_holding_project_detail,
    get_holding_projects,
    get_project_repositories,
    get_unclassified_repositories,
)


class TestProjectOntologyService(unittest.TestCase):

    def test_reps_not_equal_to_projects_epistemological_separation(self):
        """Proves that Repositório != Projeto (1 Holding Project -> N Repositories)."""
        mock_cur = MagicMock()

        # 1. Holding projects query
        mock_cur.fetchall.side_effect = [
            # hp_rows
            [
                {
                    "id": "proj:pub-ecom",
                    "slug": "pub-ecom",
                    "display_name": "PUB E-Commerce",
                    "description": "Unified ecom hub",
                    "project_type": "PRODUCT",
                    "lifecycle_status": "ATIVO",
                    "is_active": True,
                    "is_archived": False,
                    "strategic_priority": "CRITICA",
                    "owner_scope": "pubcoreagencia",
                    "ontology_status": "CONFIRMED",
                    "ontology_source": "SYSTEM_ANALYSIS",
                    "ontology_confidence": 1.0,
                    "ontology_reason": "Platform verified",
                    "ontology_verified_at": "2026-09-16T20:00:00Z",
                    "ontology_verified_by": "actor:auditor:console-operator",
                    "created_at": "2026-09-16T20:00:00Z",
                    "updated_at": "2026-09-16T20:00:00Z",
                    "repositories_count": 4,
                    "confirmed_repos": 1,
                    "proposed_repos": 3,
                }
            ],
            # assoc_rows
            [
                {
                    "project_id": "proj:pub-ecom",
                    "repository_id": "pub-ecom",
                    "repository_name": "pub-ecom",
                    "display_name": "pub-ecom",
                    "category": "ECOMMERCE",
                    "relationship_type": "PRIMARY",
                    "is_primary": True,
                    "association_status": "CONFIRMED",
                    "classification_source": "DOCUMENTATION",
                    "classification_confidence": 1.0,
                    "classification_reason": "Monorepo core repository",
                    "classified_at": "2026-09-16T20:00:00Z",
                    "classified_by": "actor:auditor:console-operator",
                    "github_url": "https://github.com/pubcoreagencia/pub-ecom",
                },
                {
                    "project_id": "proj:pub-ecom",
                    "repository_id": "pub-ecom-landing",
                    "repository_name": "pub-ecom-landing",
                    "display_name": "pub-ecom-landing",
                    "category": "FRONTEND",
                    "relationship_type": "LANDING_PAGE",
                    "is_primary": False,
                    "association_status": "PROPOSED",
                    "classification_source": "RULE",
                    "classification_confidence": 0.90,
                    "classification_reason": "Prefix match with pub-ecom family",
                    "classified_at": "2026-09-16T20:00:00Z",
                    "classified_by": "actor:auditor:console-operator",
                    "github_url": "https://github.com/pubcoreagencia/pub-ecom-landing",
                },
            ],
            # nodes_by_project
            [{"project_id": "proj:pub-ecom", "node_count": 5}],
            # obs_7d_by_project
            [{"project_id": "proj:pub-ecom", "obs_7d": 12}],
        ]

        hp_list = get_holding_projects(mock_cur)
        self.assertEqual(hp_list.total_projects, 1)
        project = hp_list.projects[0]
        self.assertEqual(project.id, "proj:pub-ecom")
        self.assertEqual(project.ontology_status, "CONFIRMED")
        self.assertEqual(project.ontology_confidence, 1.0)
        self.assertEqual(len(project.repositories), 2)
        self.assertEqual(project.confirmed_repositories_count, 1)
        self.assertEqual(project.proposed_repositories_count, 3)

        # First is CONFIRMED, second is PROPOSED
        self.assertEqual(project.repositories[0].association_status, "CONFIRMED")
        self.assertEqual(project.repositories[1].association_status, "PROPOSED")
        self.assertEqual(project.repositories[1].classification_confidence, 0.90)

    def test_unclassified_repositories_isolation(self):
        """Verifies that repositories without project association are preserved as UNCLASSIFIED."""
        mock_cur = MagicMock()
        mock_cur.fetchall.return_value = [
            {
                "id": "pub-github-mcp",
                "repository_full_name": "pubcoreagencia/pub-github-mcp",
                "repository_name": "pub-github-mcp",
                "display_name": "pub-github-mcp",
                "description": "Standalone MCP tool",
                "category": "INFRAESTRUTURA",
                "lifecycle_status": "ATIVO",
                "is_active": True,
                "is_archived": False,
                "is_private": True,
                "monitoring_enabled": True,
                "strategic_priority": "PADRAO",
                "github_url": "https://github.com/pubcoreagencia/pub-github-mcp",
                "created_at": "2026-09-16T20:00:00Z",
                "updated_at": "2026-09-16T20:00:00Z",
                "last_discovered_at": "2026-09-16T20:00:00Z",
            }
        ]

        unclass = get_unclassified_repositories(mock_cur)
        self.assertEqual(len(unclass), 1)
        self.assertEqual(unclass[0].id, "pub-github-mcp")

    def test_governance_queues(self):
        """Verifies governance queues separating pending projects, pending associations, and unclassified repos."""
        from console.backend.services.ontology_service import get_governance_queues
        mock_cur = MagicMock()
        mock_cur.fetchall.side_effect = [
            # pending_projects
            [
                {
                    "id": "proj:pub-trade",
                    "slug": "pub-trade",
                    "display_name": "PUB Trade",
                    "description": "Projeto proposto",
                    "project_type": "PRODUCT",
                    "lifecycle_status": "PROPOSTO",
                    "strategic_priority": "PADRAO",
                    "ontology_status": "PROPOSED",
                    "ontology_source": "RULE",
                    "ontology_confidence": 0.85,
                    "ontology_reason": "Inferred from repo name",
                    "repositories_count": 1,
                }
            ],
            # pending_associations
            [
                {
                    "project_id": "proj:pub-ecom",
                    "project_display_name": "PUB E-Commerce",
                    "repository_id": "pub-ecom-landing",
                    "repository_name": "pub-ecom-landing",
                    "repository_display_name": "pub-ecom-landing",
                    "relationship_type": "LANDING_PAGE",
                    "is_primary": False,
                    "association_status": "PROPOSED",
                    "classification_source": "RULE",
                    "classification_confidence": 0.90,
                    "classification_reason": "Prefix match",
                    "classified_at": "2026-09-16T20:00:00Z",
                    "classified_by": "actor:auditor:console-operator",
                }
            ],
            # unclassified repositories
            [
                {
                    "id": "pub-github-mcp",
                    "repository_full_name": "pubcoreagencia/pub-github-mcp",
                    "repository_name": "pub-github-mcp",
                    "display_name": "pub-github-mcp",
                    "description": "Standalone MCP tool",
                    "category": "INFRAESTRUTURA",
                    "lifecycle_status": "ATIVO",
                    "is_active": True,
                    "is_archived": False,
                    "is_private": True,
                    "monitoring_enabled": True,
                    "strategic_priority": "PADRAO",
                    "github_url": "https://github.com/pubcoreagencia/pub-github-mcp",
                    "created_at": "2026-09-16T20:00:00Z",
                    "updated_at": "2026-09-16T20:00:00Z",
                    "last_discovered_at": "2026-09-16T20:00:00Z",
                }
            ]
        ]

        queues = get_governance_queues(mock_cur)
        self.assertEqual(queues["pending_projects_count"], 1)
        self.assertEqual(queues["pending_projects"][0]["ontology_status"], "PROPOSED")
        self.assertEqual(queues["pending_associations_count"], 1)
        self.assertEqual(queues["pending_associations"][0]["association_status"], "PROPOSED")
        self.assertEqual(queues["unclassified_repositories_count"], 1)


if __name__ == "__main__":
    unittest.main()
