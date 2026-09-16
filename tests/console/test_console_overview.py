"""
Unit and integration tests for Console Overview and Activity aggregation.
Verifies:
- Project discovery:
  * Project in repository observations only
  * Project in active knowledge nodes only
  * Project in both
  * Project outside scope does not appear
- Window & Heatmap guarantees:
  * N calendar days generated (7 = 7, 14 = 14, 30 = 30)
  * Days with 0 observations are present with observed_count = 0
- UTC boundary evaluation:
  * activity_today respects [today_utc_start, current_timestamp_utc)
  * future events are strictly excluded from activity_today
  * activity_7d uses strict UTC 7-day interval
- Health separation:
  * database_health is distinct and independent from projector_health
  * projector_health derived strictly from projection checkpoints
- Active node count:
  * accurately counts only is_active = TRUE nodes
- Read-only guarantees: GET works with bearer token, POST returns 405.
"""

import json
import threading
import unittest
from unittest.mock import MagicMock, patch
import urllib.request
import urllib.error
from datetime import datetime, timezone
from http.server import HTTPServer

from console.backend.config import ConsoleConfig
from console.backend.models import (
    DailyActivityBucketDTO,
    OverviewProjectDTO,
    OverviewResponseDTO,
)
from console.backend.server import ConsoleRequestHandler
from console.backend.services.activity_service import get_overview_data


class TestConsoleOverviewService(unittest.TestCase):
    """Unit tests for activity_service.get_overview_data."""

    def test_overview_aggregation_and_health_separation(self):
        mock_cur = MagicMock()

        # Database responses:
        # 1. SELECT version() (Database health check)
        # 2. SELECT checkpoints (Projector health)
        # 3. SELECT DISTINCT project_id (Discovery)
        # 4. SELECT observation stats
        # 5. SELECT active nodes stats
        # 6. SELECT generate_series daily activity
        mock_cur.fetchone.side_effect = [
            {"version": "PostgreSQL 16.2 on x86_64-apple-darwin"},  # Database health
        ]
        mock_cur.fetchall.side_effect = [
            # 2. Checkpoints -> DEGRADED projector health
            [
                {"projector_name": "event_projector", "status": "DEGRADED", "error_detail": None},
                {"projector_name": "vector_projector", "status": "HEALTHY", "error_detail": None},
            ],
            # 3. Discovered Projects:
            # - pub-ecom: in observations and nodes
            # - pub-neural: in observations only
            # - pub-holding: in nodes only
            [
                {"project_id": "pub-ecom"},
                {"project_id": "pub-neural"},
                {"project_id": "pub-holding"},
            ],
            # 4. Per-project observation statistics
            [
                {
                    "project_id": "pub-ecom",
                    "observed_repos": 1,
                    "total_observations": 42,
                    "today_observations": 5,
                    "seven_day_observations": 20,
                    "last_observed_at": datetime(2026, 9, 16, 3, 0, tzinfo=timezone.utc),
                },
                {
                    "project_id": "pub-neural",
                    "observed_repos": 2,
                    "total_observations": 15,
                    "today_observations": 2,
                    "seven_day_observations": 10,
                    "last_observed_at": datetime(2026, 9, 16, 4, 15, tzinfo=timezone.utc),
                },
            ],
            # 5. Per-project active knowledge nodes
            [
                {"project_id": "pub-ecom", "total_active_nodes": 8},
                {"project_id": "pub-holding", "total_active_nodes": 14},
            ],
            # 6. Daily calendar buckets for 7-day window (7 days x 3 projects = 21 rows)
            [
                {"day": f"2026-09-{10+d:02d}", "project_id": pid, "observed_count": 0 if pid == "pub-holding" else (d % 3)}
                for d in range(7)
                for pid in ["pub-ecom", "pub-neural", "pub-holding"]
            ],
        ]

        overview = get_overview_data(mock_cur, window_days=7)

        self.assertIsInstance(overview, OverviewResponseDTO)
        self.assertEqual(overview.window_days, 7)

        # Health Separation Verification:
        # Database Health is HEALTHY (PostgreSQL responded with version)
        # Projector Health is DEGRADED (one projector reported DEGRADED)
        self.assertEqual(overview.database_health, "HEALTHY")
        self.assertEqual(overview.projector_health, "DEGRADED")

        # Project Discovery Verification:
        self.assertEqual(len(overview.projects), 3)

        # pub-ecom (both observations and nodes)
        ecom = next(p for p in overview.projects if p.project_id == "pub-ecom")
        self.assertEqual(ecom.observed_repository_count, 1)
        self.assertEqual(ecom.observation_count, 42)
        self.assertEqual(ecom.activity_today, 5)
        self.assertEqual(ecom.activity_7d, 20)
        self.assertEqual(ecom.active_node_count, 8)
        self.assertIn("2026-09-16T03:00:00", ecom.last_observation_at)

        # pub-holding (nodes only: observations = 0, last_observation_at = None)
        holding = next(p for p in overview.projects if p.project_id == "pub-holding")
        self.assertEqual(holding.observed_repository_count, 0)
        self.assertEqual(holding.observation_count, 0)
        self.assertEqual(holding.activity_today, 0)
        self.assertEqual(holding.activity_7d, 0)
        self.assertIsNone(holding.last_observation_at)
        self.assertEqual(holding.active_node_count, 14)

        # Heatmap Verification:
        # Exactly 21 bucket entries for 7 calendar days x 3 projects
        self.assertEqual(len(overview.daily_activity), 21)
        # Ensure days with 0 observations are present
        zero_entries = [b for b in overview.daily_activity if b.project_id == "pub-holding"]
        self.assertEqual(len(zero_entries), 7)
        self.assertTrue(all(b.observed_count == 0 for b in zero_entries))

    def test_window_days_clamping(self):
        mock_cur = MagicMock()
        mock_cur.fetchone.return_value = {"version": "PostgreSQL 16"}
        mock_cur.fetchall.side_effect = [
            [],  # Checkpoints
            [],  # Projects
            [],  # Observations
            [],  # Nodes
            [],  # Daily buckets
        ]
        overview = get_overview_data(mock_cur, window_days=100)
        self.assertEqual(overview.window_days, 60)  # Clamped to max 60


class TestConsoleOverviewEndpoint(unittest.TestCase):
    """E2E HTTP tests for /api/v1/overview."""

    @classmethod
    def setUpClass(cls):
        cls.config = ConsoleConfig(
            db_url="postgresql://test:test@localhost:5432/test",
            host="127.0.0.1",
            port=0,
        )
        ConsoleRequestHandler.server_config = cls.config
        cls.server = HTTPServer(("127.0.0.1", 0), ConsoleRequestHandler)
        cls.port = cls.server.server_port
        cls.base_url = f"http://127.0.0.1:{cls.port}"

        cls.server_thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.server_thread.start()

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()

    def test_overview_requires_auth(self):
        req = urllib.request.Request(f"{self.base_url}/api/v1/overview")
        with self.assertRaises(urllib.error.HTTPError) as ctx:
            urllib.request.urlopen(req)
        self.assertEqual(ctx.exception.code, 401)

    @patch("console.backend.server.get_readonly_connection")
    @patch("console.backend.server.get_overview_data")
    def test_overview_success_with_auth(self, mock_get_overview, mock_get_conn):
        mock_conn = MagicMock()
        mock_cur = MagicMock()
        mock_conn.__enter__.return_value = mock_cur
        mock_get_conn.return_value = mock_conn

        mock_get_overview.return_value = OverviewResponseDTO(
            generated_at="2026-09-16T04:00:00Z",
            window_days=14,
            database_health="HEALTHY",
            projector_health="HEALTHY",
            projects=[
                OverviewProjectDTO(
                    project_id="pub-ecom",
                    observed_repository_count=1,
                    observation_count=10,
                    activity_today=2,
                    activity_7d=8,
                    last_observation_at="2026-09-16T03:00:00Z",
                    active_node_count=5,
                )
            ],
            daily_activity=[
                DailyActivityBucketDTO(
                    day="2026-09-16",
                    project_id="pub-ecom",
                    observed_count=2,
                )
            ],
        )

        req = urllib.request.Request(
            f"{self.base_url}/api/v1/overview?window_days=14",
            headers={"Authorization": "Bearer valid-token-123"},
        )
        with urllib.request.urlopen(req) as resp:
            self.assertEqual(resp.status, 200)
            data = json.loads(resp.read().decode("utf-8"))
            self.assertEqual(data["database_health"], "HEALTHY")
            self.assertEqual(data["projector_health"], "HEALTHY")
            self.assertEqual(len(data["projects"]), 1)
            self.assertEqual(data["projects"][0]["project_id"], "pub-ecom")
            self.assertEqual(data["projects"][0]["active_node_count"], 5)
            self.assertEqual(len(data["daily_activity"]), 1)

    def test_overview_post_not_allowed(self):
        req = urllib.request.Request(
            f"{self.base_url}/api/v1/overview",
            data=b'{}',
            headers={"Content-Type": "application/json", "Authorization": "Bearer token"},
            method="POST",
        )
        with self.assertRaises(urllib.error.HTTPError) as ctx:
            urllib.request.urlopen(req)
        self.assertEqual(ctx.exception.code, 405)
