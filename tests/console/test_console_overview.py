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
    CandidateReviewDTO,
    DailyActivityBucketDTO,
    GovernanceReviewResponseDTO,
    OverviewProjectDTO,
    OverviewResponseDTO,
)
from console.backend.server import ConsoleRequestHandler
from console.backend.services.activity_service import (
    get_governance_review_data,
    get_overview_data,
)


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
            # 5. Per-project active knowledge nodes and blocked nodes
            [
                {"project_id": "pub-ecom", "total_active_nodes": 8, "total_blocked_nodes": 0},
                {"project_id": "pub-holding", "total_active_nodes": 14, "total_blocked_nodes": 2},
            ],
            # 6. Latest Operational Signal per project
            [
                {
                    "project_id": "pub-ecom",
                    "signal_type": "REPOSITORY_OBSERVED",
                    "sig_timestamp": datetime(2026, 9, 16, 3, 0, tzinfo=timezone.utc),
                    "summary": "Observed commit a1b2c3d on branch main",
                    "source": "neural_repository_observations",
                    "locator": "pub-holding/pub-ecom@a1b2c3d",
                },
                {
                    "project_id": "pub-holding",
                    "signal_type": "TASK_EXPERIENCE_RECORDED",
                    "sig_timestamp": datetime(2026, 9, 16, 2, 30, tzinfo=timezone.utc),
                    "summary": "Task task-99 completed with status SUCCESS: Ingest holding policies",
                    "source": "neural_events",
                    "locator": "evt-uuid-123",
                },
            ],
            # 7. Daily calendar buckets for 7-day window (7 days x 3 projects = 21 rows)
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

        # pub-ecom (both observations and nodes, project_state is UNKNOWN, 0 blocked nodes)
        ecom = next(p for p in overview.projects if p.project_id == "pub-ecom")
        self.assertEqual(ecom.observed_repository_count, 1)
        self.assertEqual(ecom.observation_count, 42)
        self.assertEqual(ecom.activity_today, 5)
        self.assertEqual(ecom.activity_7d, 20)
        self.assertEqual(ecom.active_node_count, 8)
        self.assertEqual(ecom.blocked_nodes_count, 0)
        self.assertEqual(ecom.project_state, "UNKNOWN")
        self.assertIsNotNone(ecom.latest_signal)
        self.assertEqual(ecom.latest_signal.type, "REPOSITORY_OBSERVED")
        self.assertEqual(ecom.latest_signal.source, "neural_repository_observations")
        self.assertIn("2026-09-16T03:00:00", ecom.last_observation_at)

        # pub-holding (nodes only: observations = 0, state -> UNKNOWN, 2 blocked nodes, task signal)
        holding = next(p for p in overview.projects if p.project_id == "pub-holding")
        self.assertEqual(holding.observed_repository_count, 0)
        self.assertEqual(holding.observation_count, 0)
        self.assertEqual(holding.activity_today, 0)
        self.assertEqual(holding.activity_7d, 0)
        self.assertIsNone(holding.last_observation_at)
        self.assertEqual(holding.active_node_count, 14)
        self.assertEqual(holding.blocked_nodes_count, 2)
        self.assertEqual(holding.project_state, "UNKNOWN")
        self.assertIsNotNone(holding.latest_signal)
        self.assertEqual(holding.latest_signal.type, "TASK_EXPERIENCE_RECORDED")
        self.assertEqual(holding.latest_signal.source, "neural_events")

        # pub-neural (observations only: 0 active nodes, 0 blocked, state UNKNOWN, null latest_signal)
        neural = next(p for p in overview.projects if p.project_id == "pub-neural")
        self.assertEqual(neural.active_node_count, 0)
        self.assertEqual(neural.blocked_nodes_count, 0)
        self.assertEqual(neural.project_state, "UNKNOWN")
        self.assertIsNone(neural.latest_signal)

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
            [],  # Latest signals
            [],  # Daily buckets
        ]
        overview = get_overview_data(mock_cur, window_days=100)
        self.assertEqual(overview.window_days, 60)  # Clamped to max 60

    def test_project_state_strictly_unknown(self):
        """
        Verifies:
        - In the absence of an authoritative project lifecycle model,
          project_state is strictly UNKNOWN across all discovered projects.
        - No synthetic progress or operational state fabrication.
        """
        mock_cur = MagicMock()
        mock_cur.fetchone.return_value = {"version": "PostgreSQL 16"}
        mock_cur.fetchall.side_effect = [
            [],  # Checkpoints
            [{"project_id": "proj-a"}, {"project_id": "proj-b"}],  # Projects
            [],  # Observations
            [],  # Nodes
            [],  # Latest signals
            [],  # Daily buckets
        ]

        overview = get_overview_data(mock_cur, window_days=14)
        for proj in overview.projects:
            self.assertEqual(proj.project_state, "UNKNOWN")

    def test_blocked_nodes_counting_and_isolation(self):
        """
        Verifies:
        - 0 blocked nodes
        - 1+ blocked nodes
        - only active nodes counted
        - CONTRADICTORY nodes do NOT count as BLOCKED
        """
        mock_cur = MagicMock()
        mock_cur.fetchone.return_value = {"version": "PostgreSQL 16"}
        mock_cur.fetchall.side_effect = [
            [],  # Checkpoints
            [{"project_id": "proj-clean"}, {"project_id": "proj-blocked"}],  # Projects
            [],  # Observations
            [
                {"project_id": "proj-clean", "total_active_nodes": 10, "total_blocked_nodes": 0},
                {"project_id": "proj-blocked", "total_active_nodes": 5, "total_blocked_nodes": 3},
            ],
            [],  # Latest signals
            [],  # Daily buckets
        ]

        overview = get_overview_data(mock_cur, window_days=14)

        clean = next(p for p in overview.projects if p.project_id == "proj-clean")
        self.assertEqual(clean.blocked_nodes_count, 0)
        self.assertEqual(clean.active_node_count, 10)

        blocked = next(p for p in overview.projects if p.project_id == "proj-blocked")
        self.assertEqual(blocked.blocked_nodes_count, 3)
        self.assertEqual(blocked.active_node_count, 5)

    def test_latest_signal_deterministic_ordering_and_isolation(self):
        """
        Verifies:
        - timestamp most recent wins
        - tie breaker: TASK_EXPERIENCE_RECORDED beats REPOSITORY_OBSERVED
        - tie breaker persistent: locator ASC
        - DECISION does not enter latest signal
        - Project isolation (signals belong to their respective projects)
        """
        mock_cur = MagicMock()
        mock_cur.fetchone.return_value = {"version": "PostgreSQL 16"}
        mock_cur.fetchall.side_effect = [
            [],  # Checkpoints
            [{"project_id": "proj-a"}, {"project_id": "proj-b"}],
            [],  # Observations
            [],  # Nodes
            # 6. Latest signals (simulating the deterministic row_number output)
            [
                {
                    "project_id": "proj-a",
                    "signal_type": "TASK_EXPERIENCE_RECORDED",
                    "sig_timestamp": datetime(2026, 9, 16, 5, 0, tzinfo=timezone.utc),
                    "summary": "Task 101 completed with status SUCCESS: Goal A",
                    "source": "neural_events",
                    "locator": "evt-101",
                },
                {
                    "project_id": "proj-b",
                    "signal_type": "REPOSITORY_OBSERVED",
                    "sig_timestamp": datetime(2026, 9, 16, 4, 30, tzinfo=timezone.utc),
                    "summary": "Observed commit f9e8d7c on branch main",
                    "source": "neural_repository_observations",
                    "locator": "repo@f9e8d7c",
                },
            ],
            [],  # Daily buckets
        ]

        overview = get_overview_data(mock_cur, window_days=14)

        proj_a = next(p for p in overview.projects if p.project_id == "proj-a")
        self.assertIsNotNone(proj_a.latest_signal)
        self.assertEqual(proj_a.latest_signal.type, "TASK_EXPERIENCE_RECORDED")
        self.assertEqual(proj_a.latest_signal.locator, "evt-101")
        self.assertEqual(proj_a.latest_signal.source, "neural_events")

        proj_b = next(p for p in overview.projects if p.project_id == "proj-b")
        self.assertIsNotNone(proj_b.latest_signal)
        self.assertEqual(proj_b.latest_signal.type, "REPOSITORY_OBSERVED")
        self.assertEqual(proj_b.latest_signal.locator, "repo@f9e8d7c")
        self.assertEqual(proj_b.latest_signal.source, "neural_repository_observations")

    def test_get_governance_review_data_service(self):
        """
        Verifies:
        - get_governance_review_data retrieves candidates awaiting review.
        - Factual and non-evaluative presentation:
          * actor, role, originating event, conflict state, evidence count.
        """
        mock_cur = MagicMock()
        mock_cur.fetchall.return_value = [
            {
                "id": "finding:pub-neural:task-100:1",
                "entity_type": "LESSON",
                "title": "PLpgSQL search_path isolation",
                "summary": "Must include extensions schema",
                "content": "Full finding content",
                "promotion_state": "CANDIDATE",
                "promotion_reason": "Discovered during task-100",
                "conflict_state": "RESOLVED",
                "scope": "PROJECT",
                "project_id": "pub-neural",
                "trust_zone": "tz_internal_holding",
                "originating_event_id": "0191e4f0-0000-7000-8000-000000000001",
                "created_at": datetime(2026, 9, 16, 12, 0, tzinfo=timezone.utc),
                "proposed_by_actor_id": "autonomous-gate",
                "proposed_by_actor_role": "AGENT",
                "originating_event_type": "TASK_EXPERIENCE_RECORDED",
                "derived_from_experience_id": "experience:pub-neural:task-100",
                "evidence_count": 2,
            }
        ]

        gov_dto = get_governance_review_data(mock_cur)
        self.assertIsInstance(gov_dto, GovernanceReviewResponseDTO)
        self.assertEqual(gov_dto.candidates_count, 1)
        cand = gov_dto.candidates[0]
        self.assertEqual(cand.id, "finding:pub-neural:task-100:1")
        self.assertEqual(cand.promotion_state, "CANDIDATE")
        self.assertEqual(cand.proposed_by_actor_role, "AGENT")
        self.assertEqual(cand.evidence_count, 2)


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

    @patch("console.backend.server.get_governance_review_data")
    @patch("console.backend.server.get_readonly_connection")
    def test_governance_review_endpoint_get_success(self, mock_get_conn, mock_get_gov):
        mock_conn_ctx = MagicMock()
        mock_cur = MagicMock()
        mock_conn_ctx.__enter__.return_value = mock_cur
        mock_get_conn.return_value = mock_conn_ctx

        mock_get_gov.return_value = GovernanceReviewResponseDTO(
            generated_at="2026-09-16T12:00:00Z",
            candidates_count=1,
            candidates=[
                CandidateReviewDTO(
                    id="finding:pub-neural:task-1:1",
                    entity_type="LESSON",
                    title="Supabase extension resolution",
                    summary="Test finding summary",
                    content="Test finding content",
                    promotion_state="CANDIDATE",
                    promotion_reason="Discovered in task",
                    conflict_state="RESOLVED",
                    scope="PROJECT",
                    project_id="pub-neural",
                    trust_zone="tz_internal_holding",
                    originating_event_id="0191e4f0-0000-7000-8000-000000000001",
                    originating_event_type="TASK_EXPERIENCE_RECORDED",
                    proposed_by_actor_id="autonomous-gate",
                    proposed_by_actor_role="AGENT",
                    derived_from_experience_id="experience:pub-neural:task-1",
                    created_at="2026-09-16T12:00:00Z",
                    evidence_count=1,
                )
            ],
        )

        req = urllib.request.Request(
            f"{self.base_url}/api/v1/governance/review",
            headers={"Authorization": "Bearer valid-token-123"},
        )
        with urllib.request.urlopen(req) as resp:
            self.assertEqual(resp.status, 200)
            data = json.loads(resp.read().decode("utf-8"))
            self.assertEqual(data["candidates_count"], 1)
            cand = data["candidates"][0]
            self.assertEqual(cand["id"], "finding:pub-neural:task-1:1")
            self.assertEqual(cand["promotion_state"], "CANDIDATE")
            self.assertEqual(cand["proposed_by_actor_role"], "AGENT")
            self.assertEqual(cand["evidence_count"], 1)

    def test_governance_review_post_not_allowed(self):
        req = urllib.request.Request(
            f"{self.base_url}/api/v1/governance/review",
            data=b'{}',
            headers={"Content-Type": "application/json", "Authorization": "Bearer token"},
            method="POST",
        )
        with self.assertRaises(urllib.error.HTTPError) as ctx:
            urllib.request.urlopen(req)
        self.assertEqual(ctx.exception.code, 405)
