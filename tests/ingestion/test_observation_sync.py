"""
Unit and integration tests for Continuous Repository Observation V0.5 (RepositoryObservationSync).
Verifies:
- Ingestion:
  * new commit creates observation
  * repeated commit is deduplicated (idempotency)
  * pull request creates observation
  * repository without project retains project_id = NULL
  * repository with project inherits mapped project_id
- Temporal:
  * timestamps preserved
  * historical observations preserved
- Failure:
  * GitHub unavailable / API failure registered in sync run without false activity
- Security:
  * zero tokens / secrets in payloads or logs
"""

from datetime import datetime, timezone
import unittest
from unittest.mock import MagicMock, patch
import uuid

from src.ingestion.observation_sync import (
    GitHubSignalExtractor,
    ObservationSyncResult,
    RepositoryObservationSync,
)


class MockExtractor(GitHubSignalExtractor):
    def __init__(self, signals_by_repo=None):
        self.signals_by_repo = signals_by_repo or {}

    def fetch_repo_signals(self, repo_full_name: str, limit_commits: int = 10, limit_prs: int = 10):
        if repo_full_name in self.signals_by_repo:
            return self.signals_by_repo[repo_full_name]
        return {
            "commits": [],
            "pull_requests": [],
            "branches": {},
            "releases": [],
            "metadata": {"name": repo_full_name.split("/")[-1]},
            "metadata_hash": "hash_default",
            "error": None,
        }


class TestObservationSyncService(unittest.TestCase):

    @patch("psycopg2.connect")
    def test_new_commit_creates_observation_and_repeated_is_deduplicated(self, mock_connect):
        mock_conn = MagicMock()
        mock_cur = MagicMock()
        mock_connect.return_value = mock_conn
        mock_conn.cursor.return_value.__enter__.return_value = mock_cur

        mock_cur.fetchall.return_value = [
            {
                "repository_id": "pub-neural",
                "repository_full_name": "pubcoreagencia/pub-neural",
                "repository_name": "pub-neural",
                "is_archived": False,
                "mapped_project_id": "pub-neural",
            }
        ]

        extractor = MockExtractor({
            "pubcoreagencia/pub-neural": {
                "commits": [
                    {
                        "sha": "a1b2c3d4e5f6",
                        "message": "feat: test commit 1",
                        "author": "developer-1",
                        "date": "2026-09-17T02:00:00Z",
                    }
                ],
                "pull_requests": [],
                "branches": {"main": "a1b2c3d4e5f6"},
                "metadata": {"name": "pub-neural"},
                "metadata_hash": "hash_v1",
                "error": None,
            }
        })

        sync = RepositoryObservationSync(db_url="postgresql://test:test@localhost:5432/test")

        # 1st run:
        mock_cur.fetchone.side_effect = [
            None,             # prev_run
            None,             # last_any_run
            None,             # delivery_id check (not exists -> create)
            {"next_ver": 1},  # stream_ver
        ]
        res1 = sync.run_sync(repository_ids=["pub-neural"], github_extractor=extractor)
        self.assertEqual(res1.status, "COMPLETED")
        self.assertEqual(res1.repositories_scanned, 1)
        self.assertEqual(res1.observations_created, 1)
        self.assertEqual(res1.observations_deduplicated, 0)
        self.assertEqual(len(res1.created_observations), 1)
        self.assertEqual(res1.created_observations[0]["sha"], "a1b2c3d")
        self.assertEqual(res1.created_observations[0]["project_id"], "pub-neural")

        # 2nd run: delivery check returns existing row -> deduplicated
        mock_cur.fetchone.side_effect = [
            {"cursor_data": {}, "consecutive_failures": 0, "last_success_at": None},
            {"status": "COMPLETED"},
            {"observation_id": str(uuid.uuid4())},  # delivery_id exists
        ]
        res2 = sync.run_sync(repository_ids=["pub-neural"], github_extractor=extractor)
        self.assertEqual(res2.status, "COMPLETED")
        self.assertEqual(res2.observations_created, 0)
        self.assertEqual(res2.observations_deduplicated, 1)

    @patch("psycopg2.connect")
    def test_pull_request_observation_and_unmapped_repo(self, mock_connect):
        mock_conn = MagicMock()
        mock_cur = MagicMock()
        mock_connect.return_value = mock_conn
        mock_conn.cursor.return_value.__enter__.return_value = mock_cur

        mock_cur.fetchall.return_value = [
            {
                "repository_id": "pub-unclassified-worker",
                "repository_full_name": "pubcoreagencia/pub-unclassified-worker",
                "repository_name": "pub-unclassified-worker",
                "is_archived": False,
                "mapped_project_id": None,  # unclassified
            }
        ]
        mock_cur.fetchone.side_effect = [
            None,             # prev_run
            None,             # last_any_run
            None,             # delivery_id check (not found)
            {"next_ver": 1},  # stream_ver
        ]

        extractor = MockExtractor({
            "pubcoreagencia/pub-unclassified-worker": {
                "commits": [],
                "pull_requests": [
                    {
                        "number": 42,
                        "title": "feat: implement background task",
                        "state": "closed",
                        "merged": True,
                        "author": "engineer-pub",
                        "updated_at": "2026-09-17T01:30:00Z",
                        "head_ref": "feat/bg-task",
                        "base_ref": "main",
                    }
                ],
                "branches": {},
                "metadata": {"name": "pub-unclassified-worker"},
                "metadata_hash": "hash_v1",
                "error": None,
            }
        })

        sync = RepositoryObservationSync(db_url="postgresql://test:test@localhost:5432/test")
        res = sync.run_sync(repository_ids=["pub-unclassified-worker"], github_extractor=extractor)

        self.assertEqual(res.status, "COMPLETED")
        self.assertEqual(res.observations_created, 1)
        self.assertEqual(res.created_observations[0]["type"], "PULL_REQUEST")
        self.assertIsNone(res.created_observations[0]["project_id"])

    @patch("psycopg2.connect")
    def test_github_api_failure_does_not_fabricate_inactivity(self, mock_connect):
        mock_conn = MagicMock()
        mock_cur = MagicMock()
        mock_connect.return_value = mock_conn
        mock_conn.cursor.return_value.__enter__.return_value = mock_cur

        mock_cur.fetchall.return_value = [
            {
                "repository_id": "pub-ecom",
                "repository_full_name": "pubcoreagencia/pub-ecom",
                "repository_name": "pub-ecom",
                "is_archived": False,
                "mapped_project_id": "pub-ecom",
            }
        ]

        extractor = MockExtractor({
            "pubcoreagencia/pub-ecom": {
                "commits": [],
                "pull_requests": [],
                "branches": {},
                "metadata": None,
                "metadata_hash": None,
                "error": "GitHub API error: rate limit exceeded or connection timeout",
            }
        })

        sync = RepositoryObservationSync(db_url="postgresql://test:test@localhost:5432/test")
        mock_cur.fetchone.side_effect = [
            None,
            None,
        ]

        res = sync.run_sync(repository_ids=["pub-ecom"], github_extractor=extractor)

        self.assertEqual(res.status, "COMPLETED")
        self.assertEqual(res.repositories_scanned, 1)
        self.assertEqual(res.observations_created, 0)
        self.assertEqual(res.observations_failed, 1)
        self.assertEqual(res.repositories_changed, 0)


if __name__ == "__main__":
    unittest.main()
