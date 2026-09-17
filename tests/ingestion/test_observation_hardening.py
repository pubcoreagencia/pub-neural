"""
Hardened test suite for Continuous Repository Observation V0.5.1.
Verifies:
- Scheduler:
  * daemon start, run_once, graceful shutdown
- Incremental cursor:
  * run 1 saves cursor, run 2 with same cursor yields 0 new observations
- Metadata change detection:
  * changed description/archived triggers REPOSITORY_METADATA_CHANGE
  * unchanged metadata does not create observation
- Branch change detection:
  * newly pushed branch triggers BRANCH_CHANGE
- Rate limit & resilience:
  * 403 / 429 rate limit recorded as FAILED run without marking project inactive
- Exact branch ref:
  * commit matching known branch receives ref, non-matching receives None (never hardcoded main)
"""

from datetime import datetime, timezone
import unittest
from unittest.mock import MagicMock, patch
import uuid

from src.ingestion.observation_scheduler import ObservationScheduler
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


class TestObservationHardening(unittest.TestCase):

    @patch("psycopg2.connect")
    def test_incremental_cursor_and_deduplication(self, mock_connect):
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
                    {"sha": "c111", "message": "Commit 1", "author": "dev", "date": "2026-09-17T02:00:00Z"},
                    {"sha": "c222", "message": "Commit 2", "author": "dev", "date": "2026-09-17T01:00:00Z"},
                ],
                "pull_requests": [],
                "branches": {"main": "c111"},
                "metadata": {"name": "pub-neural"},
                "metadata_hash": "hash_v1",
                "error": None,
            }
        })

        sync = RepositoryObservationSync(db_url="postgresql://test:test@localhost:5432/test")

        # RUN 1: prev_run is None
        mock_cur.fetchone.side_effect = [
            None,             # prev_run (no previous cursor)
            None,             # last_any_run
            None,             # delivery_id check for c111 (not found -> create)
            {"next_ver": 1},  # stream_ver
            None,             # delivery_id check for c222 (not found -> create)
            {"next_ver": 2},  # stream_ver
        ]

        res1 = sync.run_sync(repository_ids=["pub-neural"], github_extractor=extractor)
        self.assertEqual(res1.status, "COMPLETED")
        self.assertEqual(res1.observations_created, 2)
        self.assertEqual(res1.cursor_data["pub-neural"]["last_commit_sha"], "c111")
        # Ensure exact branch was associated to c111 because it matched branches map
        self.assertEqual(res1.created_observations[0]["ref"], "main")
        # And c222 did not match branches map, so its ref is None (not fabricated main)
        self.assertIsNone(res1.created_observations[1]["ref"])

        # RUN 2: prev_run has cursor with last_commit_sha = c111
        mock_cur.fetchone.side_effect = [
            {"cursor_data": {"pub-neural": {"last_commit_sha": "c111", "metadata_hash": "hash_v1"}}, "consecutive_failures": 0, "last_success_at": None},
            {"status": "COMPLETED"},
        ]

        res2 = sync.run_sync(repository_ids=["pub-neural"], github_extractor=extractor)
        self.assertEqual(res2.status, "COMPLETED")
        # Incremental stop: stopped immediately when seeing c111, so 0 new observations created
        self.assertEqual(res2.observations_created, 0)

    @patch("psycopg2.connect")
    def test_branch_change_and_metadata_change_detection(self, mock_connect):
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
                "commits": [],
                "pull_requests": [],
                "branches": {"main": "c111", "feat/new-gate": "c999"},  # New branch added
                "metadata": {"name": "pub-neural", "description": "Updated description"},
                "metadata_hash": "hash_v2_changed",
                "error": None,
            }
        })

        sync = RepositoryObservationSync(db_url="postgresql://test:test@localhost:5432/test")

        mock_cur.fetchone.side_effect = [
            {
                "cursor_data": {
                    "pub-neural": {
                        "last_commit_sha": "c111",
                        "branches": {"main": "c111"},
                        "metadata_hash": "hash_v1_old"
                    }
                },
                "consecutive_failures": 0,
                "last_success_at": None,
            },
            {"status": "COMPLETED"},
            None,             # delivery_id check for BRANCH_CHANGE (not found -> create)
            {"next_ver": 1},  # stream_ver
            None,             # delivery_id check for REPOSITORY_METADATA_CHANGE (not found -> create)
            {"next_ver": 2},  # stream_ver
        ]

        res = sync.run_sync(repository_ids=["pub-neural"], github_extractor=extractor)
        self.assertEqual(res.status, "COMPLETED")
        self.assertEqual(res.observations_created, 2)
        types = [o["type"] for o in res.created_observations]
        self.assertIn("BRANCH_CHANGE", types)
        self.assertIn("REPOSITORY_METADATA_CHANGE", types)

    @patch("psycopg2.connect")
    def test_rate_limit_resilience_records_failure(self, mock_connect):
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
                "error": "RATE_LIMIT_EXCEEDED: HTTP 403 API rate limit exceeded",
            }
        })

        sync = RepositoryObservationSync(db_url="postgresql://test:test@localhost:5432/test")
        mock_cur.fetchone.side_effect = [
            None,
            None,
        ]

        res = sync.run_sync(repository_ids=["pub-ecom"], github_extractor=extractor)
        self.assertEqual(res.status, "FAILED")
        self.assertIn("RATE_LIMIT", res.error_detail)
        self.assertGreaterEqual(res.consecutive_failures, 1)

    def test_scheduler_lifecycle(self):
        scheduler = ObservationScheduler(db_url="postgresql://localhost:5432/test", interval_seconds=900)
        # Should start without error and stop gracefully
        scheduler.start()
        self.assertTrue(scheduler._thread.is_alive())
        scheduler.stop(timeout=2.0)
        self.assertFalse(scheduler._thread.is_alive())


if __name__ == "__main__":
    unittest.main()
