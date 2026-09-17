"""
Comprehensive test suite for NeuralExperienceService (Phase D).
Tests cover contract validation, idempotency, event sourcing, candidate findings,
evidence preservation, provenance tracking, and error handling across 18 scenarios.
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
from src.gate.exceptions import GateTransportError, GateValidationError
from src.gate.experience_service import (
    ExperienceSink,
    InMemoryExperienceSink,
    NeuralExperienceService,
)
from src.gate.models import (
    CandidateFinding,
    ExperienceIngestionResult,
    NeuralExperienceRecord,
    TaskEvidence,
)


class TestNeuralExperienceService(unittest.TestCase):
    def setUp(self) -> None:
        self.sink = InMemoryExperienceSink()
        self.service = NeuralExperienceService(sink=self.sink)

        self.valid_evidence = TaskEvidence(
            validation_passed=True,
            worktree_clean=True,
            push_succeeded=True,
            remote_verified=True,
            runtime_verified=True,
            test_summary={"total": 20, "passed": 20, "failed": 0},
            delivery_verified=True,
            governance_verified=True,
        )

        self.valid_finding = CandidateFinding(
            finding_type=KnowledgeClass.LESSON,
            title="Safe Remote Persistence Gate",
            statement="Always verify worktreeClean before remote persistence",
            scope="PROJECT",
            confidence=0.95,
        )

        self.valid_record = NeuralExperienceRecord(
            task_id="TASK-9001",
            project_id="pub-dev-loop",
            repository="pubcoreagencia/pub-dev-loop",
            branch="feat/remote-delivery-gate-phase1",
            commit_sha="1e5efdaecbe0bfdc228fb470288c4fc434f7285c",
            remote_sha="1e5efdaecbe0bfdc228fb470288c4fc434f7285c",
            status=TaskExecutionStatus.COMPLETED,
            objective="Implement remote delivery gate with verified push",
            agent_id="agent:architect:pdl-1",
            changed_files=["src/pdl/persistence/persistence-gate.ts", "tests/gate.test.ts"],
            evidence=self.valid_evidence,
            candidate_findings=[self.valid_finding],
            trace={"execution_duration_ms": 1250, "attempts": 1},
            completed_at="2026-09-14T03:30:00Z",
            ingestion_source="pdl-bidirectional-gate",
        )

    # 1. Valid experience ingestion
    def test_01_valid_experience_ingestion(self) -> None:
        result = self.service.record(self.valid_record)
        self.assertEqual(result.status, ExperienceWritebackStatus.ACCEPTED)
        self.assertTrue(result.is_accepted)
        self.assertFalse(result.is_duplicate)
        self.assertEqual(result.task_id, "TASK-9001")
        self.assertIsNotNone(result.event_id)
        self.assertIsNotNone(result.idempotency_key)
        self.assertEqual(result.candidate_findings_count, 1)

    # 2. Invalid experience
    def test_02_invalid_experience(self) -> None:
        # Pass non-record and invalid type
        result = self.service.record("not-a-record")  # type: ignore
        self.assertEqual(result.status, ExperienceWritebackStatus.INVALID_REQUEST)
        self.assertIn("Invalid experience type", str(result.reason))

    # 3. Minimal valid experience
    def test_03_minimal_valid_experience(self) -> None:
        minimal_evidence = TaskEvidence(
            validation_passed=True,
            worktree_clean=True,
            push_succeeded=False,
            remote_verified=False,
        )
        minimal_record = NeuralExperienceRecord(
            task_id="TASK-MIN-1",
            project_id="pub-neural",
            repository="pubcoreagencia/pub-neural",
            branch="main",
            status=TaskExecutionStatus.COMPLETED,
            objective="Minimal record test",
            evidence=minimal_evidence,
            completed_at="2026-09-14T03:00:00Z",
            # commit_sha, remote_sha, agent_id, trace, changed_files omitted
        )
        result = self.service.record(minimal_record)
        self.assertEqual(result.status, ExperienceWritebackStatus.ACCEPTED)
        self.assertEqual(result.candidate_findings_count, 0)
        self.assertIn("TASK-MIN-1", result.task_id)

    # 4. Provenance preservation
    def test_04_provenance_preservation(self) -> None:
        result = self.service.record(self.valid_record)
        self.assertEqual(result.status, ExperienceWritebackStatus.ACCEPTED)

        event = self.sink.events[str(result.event_id)]
        payload = event["payload"]
        self.assertEqual(payload["taskId"], "TASK-9001")
        self.assertEqual(payload["projectId"], "pub-dev-loop")
        self.assertEqual(payload["repository"], "pubcoreagencia/pub-dev-loop")
        self.assertEqual(payload["branch"], "feat/remote-delivery-gate-phase1")
        self.assertEqual(payload["commitSha"], "1e5efdaecbe0bfdc228fb470288c4fc434f7285c")
        self.assertEqual(payload["remoteSha"], "1e5efdaecbe0bfdc228fb470288c4fc434f7285c")
        self.assertEqual(payload["agentId"], "agent:architect:pdl-1")
        self.assertEqual(payload["changedFiles"], ["src/pdl/persistence/persistence-gate.ts", "tests/gate.test.ts"])

    # 5. Evidence preservation
    def test_05_evidence_preservation(self) -> None:
        result = self.service.record(self.valid_record)
        self.assertEqual(result.status, ExperienceWritebackStatus.ACCEPTED)

        event = self.sink.events[str(result.event_id)]
        evidence = event["payload"]["evidence"]
        self.assertTrue(evidence["validationPassed"])
        self.assertTrue(evidence["worktreeClean"])
        self.assertTrue(evidence["pushSucceeded"])
        self.assertTrue(evidence["remoteVerified"])
        self.assertTrue(evidence["runtimeVerified"])
        self.assertTrue(evidence["deliveryVerified"])
        self.assertTrue(evidence["governanceVerified"])
        self.assertEqual(evidence["testSummary"], {"total": 20, "passed": 20, "failed": 0})

    # 6. Candidate finding preservation
    def test_06_candidate_finding_preservation(self) -> None:
        result = self.service.record(self.valid_record)
        self.assertEqual(result.status, ExperienceWritebackStatus.ACCEPTED)

        event = self.sink.events[str(result.event_id)]
        findings = event["payload"]["candidateFindings"]
        self.assertEqual(len(findings), 1)
        self.assertEqual(findings[0]["finding_type"], "LESSON")
        self.assertEqual(findings[0]["title"], "Safe Remote Persistence Gate")
        self.assertEqual(findings[0]["statement"], "Always verify worktreeClean before remote persistence")
        self.assertEqual(findings[0]["scope"], "PROJECT")
        self.assertEqual(findings[0]["confidence"], 0.95)

    # 7. Candidate != validated invariant
    def test_07_candidate_not_equal_to_validated_invariant(self) -> None:
        result = self.service.record(self.valid_record)
        self.assertEqual(result.status, ExperienceWritebackStatus.ACCEPTED)

        event = self.sink.events[str(result.event_id)]
        # Candidate findings are strictly marked as CANDIDATE, never promoted automatically
        self.assertEqual(event["payload"]["candidateState"], PromotionState.CANDIDATE.value)
        self.assertNotEqual(event["payload"]["candidateState"], PromotionState.VALIDATED.value)
        self.assertNotEqual(event["payload"]["candidateState"], PromotionState.ADOPTED.value)

    # 8. Idempotent duplicate ingestion
    def test_08_idempotent_duplicate_ingestion(self) -> None:
        res1 = self.service.record(self.valid_record)
        self.assertEqual(res1.status, ExperienceWritebackStatus.ACCEPTED)
        self.assertFalse(res1.is_duplicate)

        # Ingest identical record again
        res2 = self.service.record(self.valid_record)
        self.assertEqual(res2.status, ExperienceWritebackStatus.DUPLICATE)
        self.assertTrue(res2.is_duplicate)
        self.assertEqual(res2.event_id, res1.event_id)
        self.assertEqual(res2.idempotency_key, res1.idempotency_key)

    # 9. Invalid timestamp
    def test_09_invalid_timestamp(self) -> None:
        payload = self.valid_record.to_dict()
        payload["completedAt"] = "invalid-date-not-iso"
        result = self.service.record(payload)
        self.assertEqual(result.status, ExperienceWritebackStatus.INVALID_REQUEST)
        self.assertIn("completed_at", str(result.reason))

    # 10. Invalid task/project/repository
    def test_10_invalid_task_project_repository(self) -> None:
        # Missing taskId
        p1 = self.valid_record.to_dict()
        p1["taskId"] = ""
        r1 = self.service.record(p1)
        self.assertEqual(r1.status, ExperienceWritebackStatus.INVALID_REQUEST)

        # Missing projectId
        p2 = self.valid_record.to_dict()
        p2["projectId"] = "   "
        r2 = self.service.record(p2)
        self.assertEqual(r2.status, ExperienceWritebackStatus.INVALID_REQUEST)

        # Missing repository
        p3 = self.valid_record.to_dict()
        p3["repository"] = None
        r3 = self.service.record(p3)
        self.assertEqual(r3.status, ExperienceWritebackStatus.INVALID_REQUEST)

    # 11. Invalid candidate finding
    def test_11_invalid_candidate_finding(self) -> None:
        payload = self.valid_record.to_dict()
        payload["candidateFindings"] = [
            {
                "finding_type": "NON_EXISTENT_CLASS",
                "title": "Bad Finding",
                "statement": "Bad statement",
            }
        ]
        result = self.service.record(payload)
        self.assertEqual(result.status, ExperienceWritebackStatus.INVALID_REQUEST)
        self.assertIn("Invalid knowledge class", str(result.reason))

    # 12. Invalid provenance / evidence
    def test_12_invalid_provenance(self) -> None:
        payload = self.valid_record.to_dict()
        payload["evidence"] = "not-an-evidence-dict"
        result = self.service.record(payload)
        self.assertEqual(result.status, ExperienceWritebackStatus.INVALID_REQUEST)

    # 13. Accepted result fields
    def test_13_accepted_result(self) -> None:
        result = self.service.record(self.valid_record)
        self.assertTrue(result.is_accepted)
        self.assertFalse(result.is_duplicate)
        self.assertEqual(result.status, ExperienceWritebackStatus.ACCEPTED)
        self.assertIsNotNone(result.recorded_at)
        self.assertEqual(result.metadata.get("global_sequence"), 1)

    # 14. Duplicate/idempotent result fields
    def test_14_duplicate_idempotent_result(self) -> None:
        self.service.record(self.valid_record)
        res = self.service.record(self.valid_record)
        self.assertEqual(res.status, ExperienceWritebackStatus.DUPLICATE)
        self.assertTrue(res.is_duplicate)
        self.assertFalse(res.is_accepted)
        self.assertIn("idempotent", str(res.reason).lower())

    # 15. Unavailable backend abstraction
    def test_15_unavailable_backend_abstraction(self) -> None:
        class FailingSink(InMemoryExperienceSink):
            def check_idempotency(self, idempotency_key: str):
                raise GateTransportError("Connection to database port 5432 refused")

        failing_service = NeuralExperienceService(sink=FailingSink())
        result = failing_service.record(self.valid_record)
        self.assertEqual(result.status, ExperienceWritebackStatus.UNAVAILABLE)
        self.assertIn("unavailable", str(result.reason).lower())

    # 16. Internal error handling
    def test_16_internal_error(self) -> None:
        class CrashingSink(InMemoryExperienceSink):
            def append_canonical_event(self, *args, **kwargs):
                raise RuntimeError("Unexpected disk write fault")

        crashing_service = NeuralExperienceService(sink=CrashingSink())
        result = crashing_service.record(self.valid_record)
        self.assertEqual(result.status, ExperienceWritebackStatus.INTERNAL_ERROR)
        self.assertIn("Unexpected internal error", str(result.reason))

    # 17. Event lineage preservation
    def test_17_event_lineage_preservation(self) -> None:
        result = self.service.record(self.valid_record)
        self.assertEqual(result.status, ExperienceWritebackStatus.ACCEPTED)

        event = self.sink.events[str(result.event_id)]
        self.assertEqual(event["stream_id"], "stream:task:TASK-9001")
        self.assertEqual(event["event_type"], "TASK_EXPERIENCE_RECORDED")
        self.assertEqual(event["producer_version"], "v1.0.0")
        self.assertIsNotNone(event["recorded_at"])

    # 18. Ingestion source preservation
    def test_18_ingestion_source_preservation(self) -> None:
        custom_record = self.valid_record
        custom_record.ingestion_source = "pdl-custom-delivery-gate"
        result = self.service.record(custom_record)
        self.assertEqual(result.status, ExperienceWritebackStatus.ACCEPTED)

        event = self.sink.events[str(result.event_id)]
        self.assertEqual(event["payload"]["ingestionSource"], "pdl-custom-delivery-gate")
        self.assertIn("pdl-custom-delivery-gate", result.idempotency_key)


if __name__ == "__main__":
    unittest.main()
