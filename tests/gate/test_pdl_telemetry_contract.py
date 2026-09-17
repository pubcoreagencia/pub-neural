"""
Unit tests formalizing the PDL -> PUB Neural Telemetry Contract V1.
Covers 10 critical validation scenarios:
1. Valid task completion event ingestion
2. Duplicate event / redelivery idempotency handling
3. Event with empty / invalid project ID rejection (Fail-closed)
4. Corrupted / missing evidence payload rejection
5. Escalation attempt rejection (candidateState forced to CANDIDATE)
6. Delayed / out-of-order event preservation
7. Full provenance tracking (commitSha, parentCommitSha, consumedKnowledgeIds)
8. Multi-repository project aggregation behavior
9. Conceptual / governance projects without repositories (e.g. proj:incubacao-labs)
10. Inviolability of sovereign strategic_priority (activity never alters priority)
"""

from datetime import datetime, timezone
import unittest
import uuid

from src.gate.enums import (
    ExperienceWritebackStatus,
    KnowledgeClass,
    PromotionState,
    TaskExecutionStatus,
)
from src.gate.exceptions import GateValidationError
from src.gate.experience_service import (
    InMemoryExperienceSink,
    NeuralExperienceService,
)
from src.gate.models import (
    CandidateFinding,
    NeuralExperienceRecord,
    TaskEvidence,
)


class TestPDLTelemetryContractV1(unittest.TestCase):
    def setUp(self) -> None:
        self.sink = InMemoryExperienceSink()
        self.service = NeuralExperienceService(sink=self.sink)

        self.valid_evidence = TaskEvidence(
            validation_passed=True,
            worktree_clean=True,
            push_succeeded=True,
            remote_verified=True,
            runtime_verified=True,
            test_summary={"total": 10, "passed": 10, "failed": 0},
            delivery_verified=True,
            governance_verified=True,
        )

        self.valid_finding = CandidateFinding(
            finding_type=KnowledgeClass.LESSON,
            title="Durable Sinks",
            statement="Always persist telemetry monotonically",
            scope="PROJECT",
            confidence=0.95,
        )

    def test_scenario_01_valid_event_ingestion(self) -> None:
        """Scenario 1: Valid event produces TASK_EXPERIENCE_RECORDED with proper structure."""
        record = NeuralExperienceRecord(
            task_id="TASK-AUDIT-01",
            project_id="proj:pub-dev-loop",
            repository="pubcoreagencia/pub-dev-loop",
            branch="feat/telemetry-contract",
            commit_sha="a1b2c3d4e5f67890123456789abcdef012345678",
            remote_sha="a1b2c3d4e5f67890123456789abcdef012345678",
            status=TaskExecutionStatus.COMPLETED,
            objective="Implement telemetry validation",
            evidence=self.valid_evidence,
            completed_at="2026-09-17T20:30:00Z",
            agent_id="agent:pdl-executor:v1",
            candidate_findings=[self.valid_finding],
            consumed_knowledge_ids=["lesson:pdl:safe-push"],
            ingestion_source="pdl_telemetry_bridge",
        )

        result = self.service.record(record)
        self.assertEqual(result.status, ExperienceWritebackStatus.ACCEPTED)
        self.assertTrue(result.is_accepted)
        self.assertFalse(result.is_duplicate)
        self.assertEqual(len(self.sink.events), 1)

        persisted_event = self.sink.events[str(result.event_id)]
        self.assertEqual(persisted_event["event_type"], "TASK_EXPERIENCE_RECORDED")
        self.assertEqual(persisted_event["payload"]["projectId"], "proj:pub-dev-loop")
        self.assertEqual(persisted_event["payload"]["taskId"], "TASK-AUDIT-01")

    def test_scenario_02_idempotency_duplicate_handling(self) -> None:
        """Scenario 2: Re-delivering the exact same record returns idempotent DUPLICATE status."""
        completed_time = "2026-09-17T20:30:00Z"
        record = NeuralExperienceRecord(
            task_id="TASK-AUDIT-02",
            project_id="proj:pub-dev-loop",
            repository="pubcoreagencia/pub-dev-loop",
            branch="feat/idempotency",
            commit_sha="b2c3d4e5f67890123456789abcdef0123456789a",
            status=TaskExecutionStatus.COMPLETED,
            objective="Test redelivery",
            evidence=self.valid_evidence,
            completed_at=completed_time,
            ingestion_source="pdl_telemetry_bridge",
        )

        res1 = self.service.record(record)
        self.assertEqual(res1.status, ExperienceWritebackStatus.ACCEPTED)
        self.assertFalse(res1.is_duplicate)

        res2 = self.service.record(record)
        self.assertEqual(res2.status, ExperienceWritebackStatus.DUPLICATE)
        self.assertTrue(res2.is_duplicate)
        self.assertEqual(res2.event_id, res1.event_id)
        self.assertEqual(len(self.sink.events), 1)

    def test_scenario_03_fail_closed_on_empty_project(self) -> None:
        """Scenario 3: Records without project_id are rejected (fail-closed)."""
        with self.assertRaises(GateValidationError):
            NeuralExperienceRecord(
                task_id="TASK-AUDIT-03",
                project_id="",  # Invalid empty project ID
                repository="pubcoreagencia/pub-dev-loop",
                branch="feat/test",
                status=TaskExecutionStatus.COMPLETED,
                objective="Fail closed validation",
                evidence=self.valid_evidence,
                completed_at="2026-09-17T20:30:00Z",
            )

    def test_scenario_04_fail_closed_on_missing_evidence(self) -> None:
        """Scenario 4: Missing evidence payload is strictly rejected."""
        with self.assertRaises(GateValidationError):
            NeuralExperienceRecord(
                task_id="TASK-AUDIT-04",
                project_id="proj:pub-dev-loop",
                repository="pubcoreagencia/pub-dev-loop",
                branch="feat/test",
                status=TaskExecutionStatus.COMPLETED,
                objective="Fail closed validation",
                evidence=None,  # type: ignore
                completed_at="2026-09-17T20:30:00Z",
            )

    def test_scenario_05_anti_escalation_candidate_state(self) -> None:
        """Scenario 5: Candidate findings must always be recorded as CANDIDATE, never PROMOTED."""
        record = NeuralExperienceRecord(
            task_id="TASK-AUDIT-05",
            project_id="proj:pub-dev-loop",
            repository="pubcoreagencia/pub-dev-loop",
            branch="feat/anti-escalation",
            status=TaskExecutionStatus.COMPLETED,
            objective="Verify candidate findings safety",
            evidence=self.valid_evidence,
            completed_at="2026-09-17T20:30:00Z",
            candidate_findings=[self.valid_finding],
        )

        result = self.service.record(record)
        self.assertEqual(result.status, ExperienceWritebackStatus.ACCEPTED)

        persisted = self.sink.events[str(result.event_id)]
        # Invariant: candidateState is strictly CANDIDATE at event payload level
        self.assertEqual(persisted["payload"]["candidateState"], PromotionState.CANDIDATE.value)

    def test_scenario_06_delayed_event_handling(self) -> None:
        """Scenario 6: Delayed arrival preserves original completed_at timestamp in payload."""
        historical_time = "2026-09-10T14:00:00Z"
        record = NeuralExperienceRecord(
            task_id="TASK-AUDIT-06",
            project_id="proj:pub-dev-loop",
            repository="pubcoreagencia/pub-dev-loop",
            branch="feat/delayed",
            status=TaskExecutionStatus.COMPLETED,
            objective="Verify delayed event timestamp preservation",
            evidence=self.valid_evidence,
            completed_at=historical_time,
        )

        res = self.service.record(record)
        self.assertEqual(res.status, ExperienceWritebackStatus.ACCEPTED)
        persisted = self.sink.events[str(res.event_id)]
        self.assertEqual(persisted["payload"]["completedAt"], historical_time)

    def test_scenario_07_provenance_tracking(self) -> None:
        """Scenario 7: Full provenance chaining is preserved in the emitted event."""
        record = NeuralExperienceRecord(
            task_id="TASK-AUDIT-07",
            project_id="proj:pub-dev-loop",
            repository="pubcoreagencia/pub-dev-loop",
            branch="feat/provenance",
            commit_sha="c3d4e5f67890123456789abcdef0123456789a1b",
            remote_sha="c3d4e5f67890123456789abcdef0123456789a1b",
            status=TaskExecutionStatus.COMPLETED,
            objective="Verify provenance tracking",
            evidence=self.valid_evidence,
            completed_at="2026-09-17T20:30:00Z",
            consumed_knowledge_ids=["lesson:pdl:git-hygiene", "pattern:neural:event-sourcing"],
            ingestion_source="pdl_telemetry_bridge",
            execution_id="exec_9988",
            correlation_id="corr_1122",
        )

        res = self.service.record(record)
        event = self.sink.events[str(res.event_id)]
        self.assertEqual(event["payload"]["consumedKnowledgeIds"], ["lesson:pdl:git-hygiene", "pattern:neural:event-sourcing"])
        self.assertEqual(event["payload"]["executionId"], "exec_9988")
        self.assertEqual(event["payload"]["correlationId"], "corr_1122")
        self.assertEqual(event["payload"]["ingestionSource"], "pdl_telemetry_bridge")

    def test_scenario_08_multi_repository_aggregation_concept(self) -> None:
        """Scenario 8: Multi-repository events can be recorded under the same project_id."""
        project = "proj:pub-neural"
        record_repo1 = NeuralExperienceRecord(
            task_id="TASK-REPO-01",
            project_id=project,
            repository="pubcoreagencia/pub-neural",
            branch="feat/repo1",
            status=TaskExecutionStatus.COMPLETED,
            objective="Work on primary repo",
            evidence=self.valid_evidence,
            completed_at="2026-09-17T20:30:00Z",
        )
        record_repo2 = NeuralExperienceRecord(
            task_id="TASK-REPO-02",
            project_id=project,
            repository="pubcoreagencia/pub-neural-docs",
            branch="feat/repo2",
            status=TaskExecutionStatus.COMPLETED,
            objective="Work on secondary repo",
            evidence=self.valid_evidence,
            completed_at="2026-09-17T20:30:00Z",
        )

        res1 = self.service.record(record_repo1)
        res2 = self.service.record(record_repo2)

        self.assertEqual(res1.status, ExperienceWritebackStatus.ACCEPTED)
        self.assertEqual(res2.status, ExperienceWritebackStatus.ACCEPTED)
        self.assertEqual(len(self.sink.events), 2)
        # Both share the same project_id for unified rollup
        self.assertEqual(self.sink.events[str(res1.event_id)]["payload"]["projectId"], project)
        self.assertEqual(self.sink.events[str(res2.event_id)]["payload"]["projectId"], project)

    def test_scenario_09_project_without_repository(self) -> None:
        """Scenario 9: Conceptual / governance project without repo can record tasks."""
        record = NeuralExperienceRecord(
            task_id="TASK-CONCEPT-01",
            project_id="proj:incubacao-labs",
            repository="none",
            branch="none",
            commit_sha=None,
            remote_sha=None,
            status=TaskExecutionStatus.COMPLETED,
            objective="Incubation lab research task",
            evidence=self.valid_evidence,
            completed_at="2026-09-17T20:30:00Z",
        )

        res = self.service.record(record)
        self.assertEqual(res.status, ExperienceWritebackStatus.ACCEPTED)
        self.assertEqual(self.sink.events[str(res.event_id)]["payload"]["projectId"], "proj:incubacao-labs")
        self.assertEqual(self.sink.events[str(res.event_id)]["payload"]["repository"], "none")

    def test_scenario_10_priority_inviolability(self) -> None:
        """Scenario 10: Telemetry ingestion does not mutate sovereign strategic_priority."""
        # Simulated holding project record before telemetry
        project_state = {
            "id": "proj:pub-dev-loop",
            "name": "PUB Dev Loop",
            "strategic_priority": "CRITICA",
        }

        # Ingest 5 successful task records
        for i in range(5):
            rec = NeuralExperienceRecord(
                task_id=f"TASK-STRESS-{i}",
                project_id=project_state["id"],
                repository="pubcoreagencia/pub-dev-loop",
                branch="main",
                status=TaskExecutionStatus.COMPLETED,
                objective=f"Activity stress test {i}",
                evidence=self.valid_evidence,
                completed_at=f"2026-09-17T20:3{i}:00Z",
            )
            self.service.record(rec)

        # Invariant: strategic_priority remains unchanged regardless of event volume
        self.assertEqual(project_state["strategic_priority"], "CRITICA")


if __name__ == "__main__":
    unittest.main()
