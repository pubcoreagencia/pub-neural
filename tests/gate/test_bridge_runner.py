"""
Unit tests for the Phase F Bridge Runner (src.gate.bridge_runner).
Verifies that the CLI/in-process bridge correctly invokes real NeuralQueryService
and NeuralExperienceService, enforces idempotency, validates payloads,
and preserves candidate findings.
"""

import json
import os
import tempfile
import unittest
import uuid
from typing import Any, Dict

from src.gate.bridge_runner import (
    PILOT_PROJECT_ID,
    PILOT_REPOSITORY,
    FileBackedExperienceSink,
    FixtureRetrievalEngine,
    build_pilot_knowledge_fixture,
    handle_dump_events,
    handle_experience,
    handle_query,
)


class TestBridgeRunner(unittest.TestCase):
    """Test suite for BridgeRunner CLI / in-process execution."""

    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.sink_file = os.path.join(self.temp_dir.name, f"test_sink_{uuid.uuid4().hex}.json")

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def _build_valid_query_json(self) -> str:
        return json.dumps({
            "request_id": "req-test-runner-01",
            "task_id": "task-test-runner-01",
            "project_id": PILOT_PROJECT_ID,
            "repository": PILOT_REPOSITORY,
            "objective": "Verify checkout idempotency and transaction integrity",
            "caller": {"actor_id": "pdl-agent", "agent_role": "developer"},
            "requested_knowledge_classes": ["RULE"],
            "timestamp": "2026-09-14T05:00:00.000Z",
            "limit": 5,
        })

    def _build_valid_experience_json(self, task_id: str = "task-test-runner-01") -> str:
        return json.dumps({
            "taskId": task_id,
            "projectId": PILOT_PROJECT_ID,
            "repository": PILOT_REPOSITORY,
            "branch": "feat/checkout-idempotency",
            "status": "COMPLETED",
            "objective": "Verify checkout idempotency rules",
            "evidence": {
                "validationPassed": True,
                "worktreeClean": True,
                "pushSucceeded": True,
                "remoteVerified": True,
            },
            "candidateFindings": [
                {
                    "findingType": "LESSON",
                    "title": "Idempotency key uniqueness observation",
                    "statement": "Observed key conflict handled gracefully.",
                    "confidence": 0.9,
                    "scope": "PROJECT",
                }
            ],
            "completedAt": "2026-09-14T05:10:00.000Z",
        })

    def test_01_pilot_fixture_integrity(self) -> None:
        """Verify pilot knowledge fixture is structured correctly with inert data boundary note."""
        fixture = build_pilot_knowledge_fixture()
        self.assertEqual(len(fixture), 1)
        item = fixture[0]
        self.assertEqual(item.id, "ecom-fixture-rule-001")
        self.assertEqual(item.project_id, PILOT_PROJECT_ID)
        self.assertIn("ignore previous instructions", item.content)
        self.assertTrue(item.authority.is_data_only)

    def test_02_handle_query_pilot_mode(self) -> None:
        """Verify handle_query returns SUCCESS with pilot fixture."""
        req_json = self._build_valid_query_json()
        res = handle_query(req_json, mode="pilot")
        self.assertEqual(res["status"], "SUCCESS")
        self.assertEqual(len(res["results"]), 1)
        self.assertEqual(res["results"][0]["id"], "ecom-fixture-rule-001")
        self.assertIn("fixture-src-ecom", res["source_references"])

    def test_03_handle_query_empty_mode(self) -> None:
        """Verify handle_query in empty mode returns NO_MATCH."""
        req_json = self._build_valid_query_json()
        res = handle_query(req_json, mode="empty")
        self.assertEqual(res["status"], "NO_MATCH")
        self.assertEqual(len(res["results"]), 0)

    def test_04_handle_query_abstain_mode(self) -> None:
        """Verify handle_query in abstain mode returns ABSTAIN with metadata."""
        req_json = self._build_valid_query_json()
        res = handle_query(req_json, mode="abstain")
        self.assertEqual(res["status"], "ABSTAIN")
        self.assertTrue(res["abstention"]["abstained"])

    def test_05_handle_experience_accepted_and_persisted(self) -> None:
        """Verify handle_experience records event and persists to sink file."""
        rec_json = self._build_valid_experience_json("task-persisted-01")
        res = handle_experience(rec_json, sink_path=self.sink_file)
        self.assertEqual(res["status"], "ACCEPTED")
        self.assertFalse(res["isDuplicate"])
        self.assertIsNotNone(res["eventId"])

        # Inspect dumped sink events
        dumped = handle_dump_events(self.sink_file)
        self.assertEqual(dumped["count"], 1)
        event = list(dumped["events"].values())[0]
        self.assertEqual(event["event_type"], "TASK_EXPERIENCE_RECORDED")
        self.assertEqual(event["stream_id"], "stream:task:task-persisted-01")
        self.assertEqual(event["payload"]["candidateState"], "CANDIDATE")

    def test_06_handle_experience_idempotent_duplicate(self) -> None:
        """Verify repeated handle_experience call yields DUPLICATE with preserved event ID."""
        rec_json = self._build_valid_experience_json("task-dup-01")
        res1 = handle_experience(rec_json, sink_path=self.sink_file)
        self.assertEqual(res1["status"], "ACCEPTED")

        res2 = handle_experience(rec_json, sink_path=self.sink_file)
        self.assertEqual(res2["status"], "DUPLICATE")
        self.assertTrue(res2["isDuplicate"])
        self.assertEqual(res2["eventId"], res1["eventId"])

        # Exactly 1 event stored
        dumped = handle_dump_events(self.sink_file)
        self.assertEqual(dumped["count"], 1)

    def test_07_handle_experience_simulate_unavailable(self) -> None:
        """Verify simulated unavailable mode returns UNAVAILABLE without failure."""
        rec_json = self._build_valid_experience_json("task-unavail-01")
        res = handle_experience(rec_json, sink_path=self.sink_file, simulate_unavailable=True)
        self.assertEqual(res["status"], "UNAVAILABLE")


if __name__ == "__main__":
    unittest.main()
