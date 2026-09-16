"""
Unit tests for Operational Knowledge Loop V0.1.
Covers:
  A. ADOPTED retrieval -> promotion_state = ADOPTED
  B. CANDIDATE retrieval -> promotion_state = CANDIDATE
  C. Mixed maturity retrieval -> both appear with respective states, no artificial rank boost
  D. Out-of-domain -> ABSTAIN / zero results
  E. Consumption round-trip -> consumed_knowledge_ids preserved across serialization/deserialization
  F. Consumption does not mutate state -> ADOPTED remains ADOPTED; CANDIDATE remains CANDIDATE
  G. Absence of promotion_state -> None / UNKNOWN (never defaults to VALIDATED)
  H. Temporal metadata -> propagation of valid_from, valid_until, recorded_from, recorded_until
  I. Agent cannot modify consumed knowledge -> fail closed
  J. Conflict handling -> safe contradiction handling
  K. Replay and idempotent experience recording
"""

from datetime import datetime, timezone
import json
import unittest
import uuid

from src.gate.enums import (
    AgentRole,
    AuthorityLevel,
    ConflictState,
    ExperienceWritebackStatus,
    FreshnessState,
    GateStatus,
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
    AbstentionMetadata,
    CallerIdentity,
    CandidateFinding,
    ContradictionItem,
    FreshnessMetadata,
    NeuralExperienceRecord,
    NeuralKnowledgeItem,
    NeuralQueryRequest,
    NeuralQueryResponse,
    ProvenanceMetadata,
    TaskEvidence,
)
from src.gate.retrieval_adapter import (
    NeuralResultMapper,
    NeuralRetrievalEngine,
    RetrievalBatch,
)
from src.gate.service import NeuralQueryService
from src.retrieval.abstention import AbstentionDecision
from src.retrieval.hybrid_search import HybridSearchResult


class FakeRetrievalEngine(NeuralRetrievalEngine):
    def __init__(self, batch: RetrievalBatch):
        self.batch = batch

    def search_knowledge(
        self,
        query: str,
        trust_zone=None,
        project_id=None,
        bearer_token=None,
        limit=5,
        knowledge_classes=None,
        filters=None,
    ) -> RetrievalBatch:
        return self.batch


class TestOperationalKnowledgeLoop(unittest.TestCase):
    def setUp(self) -> None:
        self.sink = InMemoryExperienceSink()
        self.experience_service = NeuralExperienceService(sink=self.sink)
        self.mapper = NeuralResultMapper()

        self.valid_caller = CallerIdentity(
            actor_id="actor:operator:ceo",
            agent_role=AgentRole.CHIEF_OF_STAFF,
            trust_zone="tz_internal_holding",
        )

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

    def test_a_adopted_retrieval_preserves_state(self) -> None:
        """A. ADOPTED retrieval -> promotion_state = ADOPTED."""
        raw_result = HybridSearchResult(
            target_id="finding:pub-neural:task-runtime-remote-db-integration:1",
            target_type="NODE",
            title="Search Path Pgcrypto Resolution",
            snippet="search_path must include extensions schema for digest function",
            lexical_rank=1,
            dense_rank=1,
            rrf_score=0.032,
            trust_zone="tz_internal_holding",
            project_id="pub-neural",
            originating_event_id="00000000-0000-0000-0000-000000000006",
            content_hash="abc123hash",
            promotion_state="ADOPTED",
            conflict_state="RESOLVED",
            last_transition_event_id="00000000-0000-0000-0000-000000000007",
            valid_from="2026-09-15T00:00:00Z",
            valid_until=None,
            recorded_from="2026-09-15T00:00:00Z",
            recorded_until=None,
        )

        batch = RetrievalBatch(results=[raw_result])
        service = NeuralQueryService(retrieval_engine=FakeRetrievalEngine(batch))

        req = NeuralQueryRequest(
            request_id="req-test-adopted",
            task_id="task-test-adopted",
            project_id="pub-neural",
            repository="pubcoreagencia/pub-neural",
            objective="Retrieve adopted database fix",
            requested_knowledge_classes=[KnowledgeClass.LESSON],
            caller=self.valid_caller,
            timestamp=datetime.now(timezone.utc).isoformat(),
        )

        resp = service.query(req)
        self.assertEqual(resp.status, GateStatus.SUCCESS)
        self.assertEqual(len(resp.results), 1)

        item = resp.results[0]
        self.assertEqual(item.id, "finding:pub-neural:task-runtime-remote-db-integration:1")
        self.assertEqual(item.promotion_state, PromotionState.ADOPTED)
        self.assertEqual(item.conflict_state, ConflictState.RESOLVED)
        self.assertEqual(item.provenance.originating_event_id, "00000000-0000-0000-0000-000000000006")
        self.assertEqual(item.provenance.last_transition_event_id, "00000000-0000-0000-0000-000000000007")
        self.assertEqual(item.freshness.valid_from, "2026-09-15T00:00:00Z")

    def test_b_candidate_retrieval_preserves_state(self) -> None:
        """B. CANDIDATE retrieval -> promotion_state = CANDIDATE."""
        raw_result = HybridSearchResult(
            target_id="finding:pub-neural:task-runtime-remote-db-integration:2",
            target_type="NODE",
            title="Repository Observations Contract",
            snippet="Observation table requires specific fields",
            lexical_rank=1,
            dense_rank=2,
            rrf_score=0.028,
            trust_zone="tz_internal_holding",
            project_id="pub-neural",
            originating_event_id="00000000-0000-0000-0000-000000000008",
            content_hash="def456hash",
            promotion_state="CANDIDATE",
            conflict_state="RESOLVED",
            last_transition_event_id=None,
        )

        batch = RetrievalBatch(results=[raw_result])
        service = NeuralQueryService(retrieval_engine=FakeRetrievalEngine(batch))

        req = NeuralQueryRequest(
            request_id="req-test-candidate",
            task_id="task-test-candidate",
            project_id="pub-neural",
            repository="pubcoreagencia/pub-neural",
            objective="Retrieve candidate finding",
            requested_knowledge_classes=[KnowledgeClass.LESSON],
            caller=self.valid_caller,
            timestamp=datetime.now(timezone.utc).isoformat(),
        )

        resp = service.query(req)
        self.assertEqual(resp.status, GateStatus.SUCCESS)
        self.assertEqual(len(resp.results), 1)

        item = resp.results[0]
        self.assertEqual(item.promotion_state, PromotionState.CANDIDATE)
        self.assertEqual(item.conflict_state, ConflictState.RESOLVED)

    def test_c_mixed_maturity_retrieval_preserves_states_and_ranking(self) -> None:
        """C. Mixed maturity retrieval: both appear with accurate states, RRF score determines rank."""
        candidate_item = HybridSearchResult(
            target_id="finding:pub-neural:candidate:1",
            target_type="NODE",
            title="Candidate Item (Higher RRF)",
            snippet="Higher relevance match",
            lexical_rank=1,
            dense_rank=1,
            rrf_score=0.033,
            trust_zone="tz_internal_holding",
            project_id="pub-neural",
            originating_event_id="ev-1",
            content_hash="hash1",
            promotion_state="CANDIDATE",
        )
        adopted_item = HybridSearchResult(
            target_id="finding:pub-neural:adopted:1",
            target_type="NODE",
            title="Adopted Item (Lower RRF)",
            snippet="Slightly lower relevance match",
            lexical_rank=2,
            dense_rank=2,
            rrf_score=0.031,
            trust_zone="tz_internal_holding",
            project_id="pub-neural",
            originating_event_id="ev-2",
            content_hash="hash2",
            promotion_state="ADOPTED",
        )

        batch = RetrievalBatch(results=[candidate_item, adopted_item])
        service = NeuralQueryService(retrieval_engine=FakeRetrievalEngine(batch))

        req = NeuralQueryRequest(
            request_id="req-mixed",
            task_id="task-mixed",
            project_id="pub-neural",
            repository="pubcoreagencia/pub-neural",
            objective="Query matching mixed maturity items",
            requested_knowledge_classes=[KnowledgeClass.LESSON],
            caller=self.valid_caller,
            timestamp=datetime.now(timezone.utc).isoformat(),
        )

        resp = service.query(req)
        self.assertEqual(resp.status, GateStatus.SUCCESS)
        self.assertEqual(len(resp.results), 2)

        self.assertEqual(resp.results[0].id, "finding:pub-neural:candidate:1")
        self.assertEqual(resp.results[0].promotion_state, PromotionState.CANDIDATE)

        self.assertEqual(resp.results[1].id, "finding:pub-neural:adopted:1")
        self.assertEqual(resp.results[1].promotion_state, PromotionState.ADOPTED)

    def test_d_out_of_domain_abstention(self) -> None:
        """D. Out-of-domain -> explicit ABSTAIN and zero results."""
        decision = AbstentionDecision(
            accepted=False,
            reason="Abstained: query out-of-domain",
            top_dense_similarity=0.25,
            top_rrf_score=0.005,
            lexical_candidate_count=0,
            dense_candidate_count=0,
        )
        batch = RetrievalBatch(results=[], abstention_decision=decision)
        service = NeuralQueryService(retrieval_engine=FakeRetrievalEngine(batch))

        req = NeuralQueryRequest(
            request_id="req-abstain",
            task_id="task-abstain",
            project_id="pub-neural",
            repository="pubcoreagencia/pub-neural",
            objective="Irrelevant out of domain text query",
            requested_knowledge_classes=[KnowledgeClass.LESSON],
            caller=self.valid_caller,
            timestamp=datetime.now(timezone.utc).isoformat(),
        )

        resp = service.query(req)
        self.assertEqual(resp.status, GateStatus.ABSTAIN)
        self.assertTrue(resp.is_abstention)
        self.assertEqual(len(resp.results), 0)
        self.assertIsNotNone(resp.abstention)
        self.assertTrue(resp.abstention.abstained)

    def test_e_consumption_round_trip_serialization(self) -> None:
        """E. Consumption round-trip -> consumed_knowledge_ids preserved across dict/JSON."""
        consumed = [
            "finding:pub-neural:task-runtime-remote-db-integration:1",
            "rule:pub-core:zero-silent-failure",
        ]

        record = NeuralExperienceRecord(
            task_id="TASK-CONSUME-1",
            project_id="pub-neural",
            repository="pubcoreagencia/pub-neural",
            branch="feat/retrieval-abstention-v0.3",
            commit_sha="4a6664953099495d93840b725d8fa637d60113b9",
            status=TaskExecutionStatus.COMPLETED,
            objective="Execute task consuming adopted database finding",
            evidence=self.valid_evidence,
            completed_at="2026-09-16T12:00:00Z",
            consumed_knowledge_ids=consumed,
        )

        d = record.to_dict()
        self.assertEqual(d["consumed_knowledge_ids"], consumed)
        self.assertEqual(d["consumedKnowledgeIds"], consumed)

        from_snake = NeuralExperienceRecord.from_dict(d)
        self.assertEqual(from_snake.consumed_knowledge_ids, consumed)

        camel_only = {k: v for k, v in d.items() if not k.startswith("consumed_")}
        from_camel = NeuralExperienceRecord.from_dict(camel_only)
        self.assertEqual(from_camel.consumed_knowledge_ids, consumed)

        json_str = record.to_json()
        from_json = NeuralExperienceRecord.from_json(json_str)
        self.assertEqual(from_json.consumed_knowledge_ids, consumed)

    def test_f_consumption_does_not_mutate_state(self) -> None:
        """F. Consumption does not mutate state: ADOPTED remains ADOPTED; CANDIDATE remains CANDIDATE."""
        adopted_node_id = "finding:pub-neural:task-runtime-remote-db-integration:1"
        candidate_node_id = "finding:pub-neural:task-runtime-remote-db-integration:2"

        record = NeuralExperienceRecord(
            task_id="TASK-EXEC-CONSUMPTION",
            project_id="pub-neural",
            repository="pubcoreagencia/pub-neural",
            branch="feat/retrieval-abstention-v0.3",
            commit_sha="4a6664953099495d93840b725d8fa637d60113b9",
            status=TaskExecutionStatus.COMPLETED,
            objective="Verify consumption immutability",
            evidence=self.valid_evidence,
            completed_at="2026-09-16T12:05:00Z",
            consumed_knowledge_ids=[adopted_node_id, candidate_node_id],
        )

        res = self.experience_service.record(record)
        self.assertEqual(res.status, ExperienceWritebackStatus.ACCEPTED)

        stored_event = self.sink.events[str(res.event_id)]
        payload = stored_event["payload"]

        self.assertEqual(payload["consumed_knowledge_ids"], [adopted_node_id, candidate_node_id])
        self.assertEqual(payload["candidateState"], PromotionState.CANDIDATE.value)

        raw_adopted = HybridSearchResult(
            target_id=adopted_node_id,
            target_type="NODE",
            title="Adopted Finding",
            snippet="...",
            lexical_rank=1,
            dense_rank=1,
            rrf_score=0.03,
            trust_zone="tz_internal_holding",
            project_id="pub-neural",
            originating_event_id="ev-orig",
            content_hash="hash",
            promotion_state="ADOPTED",
        )
        mapped_adopted = self.mapper.map_result(raw_adopted)
        self.assertEqual(mapped_adopted.promotion_state, PromotionState.ADOPTED)

        raw_candidate = HybridSearchResult(
            target_id=candidate_node_id,
            target_type="NODE",
            title="Candidate Finding",
            snippet="...",
            lexical_rank=2,
            dense_rank=2,
            rrf_score=0.02,
            trust_zone="tz_internal_holding",
            project_id="pub-neural",
            originating_event_id="ev-orig2",
            content_hash="hash2",
            promotion_state="CANDIDATE",
        )
        mapped_candidate = self.mapper.map_result(raw_candidate)
        self.assertEqual(mapped_candidate.promotion_state, PromotionState.CANDIDATE)

    def test_g_absence_of_promotion_state_never_defaults_to_validated(self) -> None:
        """G. Absence of promotion_state -> None / UNKNOWN (never defaults to VALIDATED)."""
        raw_unlabeled = HybridSearchResult(
            target_id="finding:unlabeled:1",
            target_type="NODE",
            title="Unlabeled Finding",
            snippet="...",
            lexical_rank=1,
            dense_rank=1,
            rrf_score=0.03,
            trust_zone="tz_internal_holding",
            project_id="pub-neural",
            originating_event_id="ev-orig",
            content_hash="hash",
            promotion_state=None,
            conflict_state=None,
        )

        mapped = self.mapper.map_result(raw_unlabeled)
        self.assertIsNone(mapped.promotion_state)
        self.assertNotEqual(mapped.promotion_state, PromotionState.VALIDATED)

        d = mapped.to_dict()
        self.assertIsNone(d["promotion_state"])

        from_d = NeuralKnowledgeItem.from_dict(d)
        self.assertIsNone(from_d.promotion_state)

        raw_unknown = {"promotion_state": "UNKNOWN", "conflict_state": "UNKNOWN", "id": "item-1", "knowledge_class": "LESSON", "title": "T", "content": "C"}
        item_unknown = NeuralKnowledgeItem.from_dict(raw_unknown)
        self.assertEqual(item_unknown.promotion_state, PromotionState.UNKNOWN)
        self.assertEqual(item_unknown.conflict_state, ConflictState.UNKNOWN)

    def test_h_temporal_metadata_propagation(self) -> None:
        """H. Temporal metadata -> propagation of valid_from, valid_until, recorded_from, recorded_until."""
        raw = HybridSearchResult(
            target_id="finding:temporal:1",
            target_type="NODE",
            title="Temporal Finding",
            snippet="...",
            lexical_rank=1,
            dense_rank=1,
            rrf_score=0.03,
            trust_zone="tz_internal_holding",
            project_id="pub-neural",
            originating_event_id="ev-orig",
            content_hash="hash",
            promotion_state="ADOPTED",
            valid_from="2026-09-01T00:00:00Z",
            valid_until="2026-12-31T23:59:59Z",
            recorded_from="2026-09-01T00:00:00Z",
            recorded_until="2026-09-15T00:00:00Z",
            last_transition_event_id="ev-trans-123",
        )

        mapped = self.mapper.map_result(raw)
        self.assertEqual(mapped.freshness.valid_from, "2026-09-01T00:00:00Z")
        self.assertEqual(mapped.freshness.valid_until, "2026-12-31T23:59:59Z")
        self.assertEqual(mapped.provenance.recorded_from, "2026-09-01T00:00:00Z")
        self.assertEqual(mapped.provenance.recorded_until, "2026-09-15T00:00:00Z")
        self.assertEqual(mapped.provenance.last_transition_event_id, "ev-trans-123")

    def test_i_agent_cannot_modify_consumed_knowledge(self) -> None:
        """I. Agent cannot modify consumed knowledge: FAIL CLOSED."""
        malformed_record = {
            "taskId": "TASK-TAMPER-1",
            "projectId": "pub-neural",
            "repository": "pubcoreagencia/pub-neural",
            "branch": "feat/tamper",
            "status": "COMPLETED",
            "objective": "Attempt to promote knowledge via experience payload",
            "evidence": self.valid_evidence.to_dict(),
            "completedAt": "2026-09-16T12:10:00Z",
            "consumedKnowledgeIds": ["finding:pub-neural:task-runtime-remote-db-integration:1"],
            "promotionState": "INSTITUTIONAL",
            "promotedByAgent": True,
        }

        res = self.experience_service.record(malformed_record)
        self.assertEqual(res.status, ExperienceWritebackStatus.ACCEPTED)

        stored_payload = self.sink.events[str(res.event_id)]["payload"]
        self.assertEqual(stored_payload["candidateState"], PromotionState.CANDIDATE.value)
        self.assertNotIn("promotion_state", stored_payload)

    def test_j_conflict_handling(self) -> None:
        """J. Conflict handling: contradictory experience creates new candidate finding without overwriting adopted node."""
        contradicting_finding = CandidateFinding(
            finding_type=KnowledgeClass.LESSON,
            title="Contradicting Extension Finding",
            statement="search_path does not need extensions schema if public is used",
            scope="PROJECT",
            confidence=0.8,
        )

        record = NeuralExperienceRecord(
            task_id="TASK-CONTRADICT-1",
            project_id="pub-neural",
            repository="pubcoreagencia/pub-neural",
            branch="feat/test-contradiction",
            status=TaskExecutionStatus.COMPLETED,
            objective="Record finding that contradicts adopted knowledge",
            evidence=self.valid_evidence,
            completed_at="2026-09-16T12:15:00Z",
            candidate_findings=[contradicting_finding],
            consumed_knowledge_ids=["finding:pub-neural:task-runtime-remote-db-integration:1"],
        )

        res = self.experience_service.record(record)
        self.assertEqual(res.status, ExperienceWritebackStatus.ACCEPTED)
        self.assertEqual(res.candidate_findings_count, 1)

        stored_payload = self.sink.events[str(res.event_id)]["payload"]
        self.assertEqual(stored_payload["candidateState"], PromotionState.CANDIDATE.value)
        self.assertEqual(stored_payload["consumedKnowledgeIds"], ["finding:pub-neural:task-runtime-remote-db-integration:1"])

    def test_k_idempotency_and_replay(self) -> None:
        """K. Duplicate experience recording is strictly idempotent."""
        record = NeuralExperienceRecord(
            task_id="TASK-IDEMPOTENT-1",
            project_id="pub-neural",
            repository="pubcoreagencia/pub-neural",
            branch="feat/retrieval-abstention-v0.3",
            commit_sha="4a6664953099495d93840b725d8fa637d60113b9",
            status=TaskExecutionStatus.COMPLETED,
            objective="Execute idempotent writeback",
            evidence=self.valid_evidence,
            completed_at="2026-09-16T12:20:00Z",
            consumed_knowledge_ids=["finding:pub-neural:task-runtime-remote-db-integration:1"],
        )

        res1 = self.experience_service.record(record)
        self.assertEqual(res1.status, ExperienceWritebackStatus.ACCEPTED)
        self.assertFalse(res1.is_duplicate)

        res2 = self.experience_service.record(record)
        self.assertEqual(res2.status, ExperienceWritebackStatus.DUPLICATE)
        self.assertTrue(res2.is_duplicate)
        self.assertEqual(res1.event_id, res2.event_id)


if __name__ == "__main__":
    unittest.main()
