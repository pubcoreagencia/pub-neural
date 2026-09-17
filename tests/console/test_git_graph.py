"""
Unit tests for Git Graph Service and API routes.
"""

import unittest
from unittest.mock import MagicMock, patch

from console.backend.services.git_graph_service import (
    is_secret_file,
    get_git_topology,
    get_git_node_detail,
)

SAMPLE_TREE = [
    {"path": ".env", "type": "blob", "sha": "secret_sha", "size": 100},
    {"path": ".env.local", "type": "blob", "sha": "secret_sha2", "size": 100},
    {"path": ".env.example", "type": "blob", "sha": "example_sha", "size": 150},
    {"path": "package.json", "type": "blob", "sha": "pkg_sha", "size": 1200},
    {"path": "MASTER_CONTEXT.md", "type": "blob", "sha": "mc_sha", "size": 3400},
    {"path": "src", "type": "tree", "sha": "src_tree_sha"},
    {"path": "src/App.tsx", "type": "blob", "sha": "app_sha", "size": 2500},
    {"path": "src/components", "type": "tree", "sha": "comp_tree_sha"},
    {"path": "src/components/Header.tsx", "type": "blob", "sha": "header_sha", "size": 800},
    {"path": "certs/server.key", "type": "blob", "sha": "key_sha", "size": 500},
]


class TestGitGraphService(unittest.TestCase):
    """Test suite for Git Graph Service."""

    def test_secret_exclusion_filter(self):
        self.assertTrue(is_secret_file(".env"))
        self.assertTrue(is_secret_file(".env.production"))
        self.assertTrue(is_secret_file("secrets/app.key"))
        self.assertTrue(is_secret_file("certs/id_rsa"))
        # .env.example must NOT be excluded
        self.assertFalse(is_secret_file(".env.example"))
        self.assertFalse(is_secret_file("package.json"))
        self.assertFalse(is_secret_file("src/App.tsx"))

    @patch("console.backend.services.git_graph_service.fetch_git_tree_remote")
    def test_get_git_topology_root_lod(self, mock_fetch):
        mock_fetch.return_value = (SAMPLE_TREE, "commit_sha_12345678")

        result = get_git_topology(
            repo="pubcoreagencia/pubcore",
            branch="main",
            base_path="",
            depth=1,
            limit=50,
        )

        node_ids = {n.id for n in result.nodes}
        # Repo root & commit must exist
        self.assertIn("repo:pubcoreagencia/pubcore", node_ids)
        self.assertIn("commit:pubcoreagencia/pubcore@commit_s", node_ids)

        # Depth 1 items: .env.example, package.json, MASTER_CONTEXT.md, src (tree)
        self.assertIn("dir:pubcoreagencia/pubcore@main:src", node_ids)
        self.assertIn("file:pubcoreagencia/pubcore@main:.env.example", node_ids)
        self.assertIn("file:pubcoreagencia/pubcore@main:package.json", node_ids)
        self.assertIn("file:pubcoreagencia/pubcore@main:MASTER_CONTEXT.md", node_ids)

        # Secrets must NOT be present
        self.assertNotIn("file:pubcoreagencia/pubcore@main:.env", node_ids)
        self.assertNotIn("file:pubcoreagencia/pubcore@main:.env.local", node_ids)
        self.assertNotIn("file:pubcoreagencia/pubcore@main:certs/server.key", node_ids)

        # Subpaths (> 1 hop) must not be in depth=1
        self.assertNotIn("file:pubcoreagencia/pubcore@main:src/App.tsx", node_ids)

        # Check edge structure
        edge_targets = {e.target_id for e in result.edges}
        self.assertIn("dir:pubcoreagencia/pubcore@main:src", edge_targets)
        self.assertIn("file:pubcoreagencia/pubcore@main:package.json", edge_targets)

    @patch("console.backend.services.git_graph_service.fetch_git_tree_remote")
    def test_get_git_topology_directory_expansion(self, mock_fetch):
        mock_fetch.return_value = (SAMPLE_TREE, "commit_sha_12345678")

        # Expanding "src"
        result = get_git_topology(
            repo="pubcoreagencia/pubcore",
            branch="main",
            base_path="src",
            depth=1,
            limit=50,
        )

        node_ids = {n.id for n in result.nodes}
        self.assertIn("dir:pubcoreagencia/pubcore@main:src", node_ids)
        self.assertIn("file:pubcoreagencia/pubcore@main:src/App.tsx", node_ids)
        self.assertIn("dir:pubcoreagencia/pubcore@main:src/components", node_ids)
        # components/Header.tsx is depth 2 relative to src, so excluded at depth 1
        self.assertNotIn("file:pubcoreagencia/pubcore@main:src/components/Header.tsx", node_ids)

    @patch("console.backend.services.git_graph_service.fetch_git_tree_remote")
    def test_get_git_node_detail_file(self, mock_fetch):
        mock_fetch.return_value = (SAMPLE_TREE, "commit_sha_12345678")

        detail = get_git_node_detail("file:pubcoreagencia/pubcore@main:MASTER_CONTEXT.md")
        self.assertIsNotNone(detail)
        self.assertEqual(detail["entity_type"], "DOCUMENT")
        self.assertEqual(detail["slug"], "MASTER_CONTEXT.md")
        self.assertIn("git_metadata", detail)
        self.assertEqual(detail["git_metadata"]["type"], "blob")
        self.assertEqual(detail["git_metadata"]["sha"], "mc_sha")


if __name__ == "__main__":
    unittest.main()
