"""
Unit tests for the Bidirectional Neural Knowledge Gate contracts and boundaries.
Verifies all 12 test matrix scenarios required by Phase A:
  1. valid query
  2. invalid query
  3. query with results
  4. abstention
  5. provenance
  6. stale knowledge
  7. conflict
  8. valid experience
  9. invalid experience
  10. invalid knowledge class
  11. authority metadata
  12. failure states
"""

import json
import unittest

from src.gate.enums import (
    AgentRole,
    AuthorityLevel,
    ConflictState,
    FreshnessState,
    GateStatus,
    KnowledgeClass,
    PromotionState,
    TaskExecutionStatus,
)
from src.gate.exceptions import GateValidationError
from src.gate.models import (
    AbstentionMetadata,
    AuthorityMetadata,
    CallerIdentity,
    CandidateFinding,
    ContradictionItem,
    FreshnessMetadata,
    GateFailure,
    NeuralExperienceRecord,
    NeuralKnowledgeItem,
    NeuralQueryRequest,
    NeuralQueryResponse,
    ProvenanceMetadata,
    TaskEvidence,
)


class TestBidirectionalGateContracts(unittest.TestCase):
    """Test suite for Bidirectional Neural Knowledge Gate technical contracts."""

    # -------------------------------------------------------------------------
    # Scenario 1: Valid query
    # -------------------------------------------------------------------------
    def test_01_valid_query(self):
        """Verify that a well-formed query request is accepted and deterministically serialized."""
        caller = CallerIdentity(
            actor_id="agent:pdl:worker-1",
            agent_role=AgentRole.DEVELOPER,
            trust_zone="tz_internal_holding",
        )
        query = NeuralQueryRequest(
            request_id="req-101",
            task_id="task-501",
            project_id="pub-dev-loop",
            repository="pubcoreagencia/pub-dev-loop",
            objective="Retrieve retrieval abstention guidelines and historical decisions",
            requested_knowledge_classes=[KnowledgeClass.DECISION, KnowledgeClass.RULE],
            caller=caller,
            timestamp="2026-09-14T12:00:00Z",
            branch="feat/gate-contracts",
            commit_sha="a1b2c3d4e5f6071829304152637485960718293a",
            filters={"scope": "GLOBAL"},
            limit=5,
        )

        self.assertEqual(query.request_id, "req-101")
        self.assertEqual(query.task_id, "task-501")
        self.assertEqual(query.project_id, "pub-dev-loop")
        self.assertEqual(query.repository, "pubcoreagencia/pub-dev-loop")
        self.assertEqual(len(query.requested_knowledge_classes), 2)
        self.assertEqual(query.limit, 5)

        # Roundtrip to dict
        data = query.to_dict()
        self.assertIsInstance(data, dict)
        self.assertEqual(data["request_id"], "req-101")
        self.assertEqual(data["requested_knowledge_classes"], ["DECISION", "RULE"])
        self.assertEqual(data["caller"]["agent_role"], "developer")

        # Roundtrip from dict
        reconstructed = NeuralQueryRequest.from_dict(data)
        self.assertEqual(reconstructed.request_id, query.request_id)
        self.assertEqual(reconstructed.requested_knowledge_classes, query.requested_knowledge_classes)
        self.assertEqual(reconstructed.caller.agent_role, AgentRole.DEVELOPER)

        # JSON serialization
        json_str = query.to_json()
        from_json_obj = NeuralQueryRequest.from_json(json_str)
        self.assertEqual(from_json_obj.request_id, query.request_id)
        self.assertEqual(from_json_obj.commit_sha, query.commit_sha)

    # -------------------------------------------------------------------------
    # Scenario 2: Invalid query
    # -------------------------------------------------------------------------
    def test_02_invalid_query_missing_or_blank_fields(self):
        """Verify that missing mandatory fields or empty strings raise GateValidationError."""
        caller = CallerIdentity(actor_id="actor-1", agent_role=AgentRole.ARCHITECT)

        # Empty request_id
        with self.assertRaises(GateValidationError) as ctx:
            NeuralQueryRequest(
                request_id="",
                task_id="task-1",
                project_id="pub-neural",
                repository="pubcoreagencia/pub-neural",
                objective="Test objective",
                requested_knowledge_classes=[KnowledgeClass.PATTERN],
                caller=caller,
                timestamp="2026-09-14T12:00:00Z",
            )
        self.assertIn("request_id", str(ctx.exception))

        # Blank objective
        with self.assertRaises(GateValidationError) as ctx:
            NeuralQueryRequest(
                request_id="req-1",
                task_id="task-1",
                project_id="pub-neural",
                repository="pubcoreagencia/pub-neural",
                objective="   ",
                requested_knowledge_classes=[KnowledgeClass.PATTERN],
                caller=caller,
                timestamp="2026-09-14T12:00:00Z",
            )
        self.assertIn("objective", str(ctx.exception))

        # Invalid timestamp
        with self.assertRaises(GateValidationError) as ctx:
            NeuralQueryRequest(
                request_id="req-1",
                task_id="task-1",
                project_id="pub-neural",
                repository="pubcoreagencia/pub-neural",
                objective="Test objective",
                requested_knowledge_classes=[KnowledgeClass.PATTERN],
                caller=caller,
                timestamp="invalid-date-string",
            )
        self.assertIn("timestamp", str(ctx.exception))

        # Out-of-bounds limit
        with self.assertRaises(GateValidationError) as ctx:
            NeuralQueryRequest(
                request_id="req-1",
                task_id="task-1",
                project_id="pub-neural",
                repository="pubcoreagencia/pub-neural",
                objective="Test objective",
                requested_knowledge_classes=[KnowledgeClass.PATTERN],
                caller=caller,
                timestamp="2026-09-14T12:00:00Z",
                limit=100,  # Max is 50
            )
        self.assertIn("limit", str(ctx.exception))

        # Empty knowledge classes list
        with self.assertRaises(GateValidationError) as ctx:
            NeuralQueryRequest(
                request_id="req-1",
                task_id="task-1",
                project_id="pub-neural",
                repository="pubcoreagencia/pub-neural",
                objective="Test objective",
                requested_knowledge_classes=[],
                caller=caller,
                timestamp="2026-09-14T12:00:00Z",
            )
        self.assertIn("requested_knowledge_classes", str(ctx.exception))

    # -------------------------------------------------------------------------
    # Scenario 3: Query with results
    # -------------------------------------------------------------------------
    def test_03_query_with_results(self):
        """Verify successful query response containing structured items and references."""
        item = NeuralKnowledgeItem(
            id="node-decision-001",
            knowledge_class=KnowledgeClass.DECISION,
            title="Adopt Reciprocal Rank Fusion V0.1",
            content="Combine FTS Portuguese and pgvector cosine distance using k=60.",
            scope="GLOBAL",
            relevance_score=0.032,
            confidence_score=0.99,
            promotion_state=PromotionState.VALIDATED,
            conflict_state=ConflictState.RESOLVED,
            provenance=ProvenanceMetadata(
                source_id="src-file-01",
                originating_event_id="ev-999",
                evidence_id="evi-101",
                repository="pubcoreagencia/pub-neural",
                commit_sha="c0ffee1234567890abcdef1234567890abcdef12",
                file_path="docs/ARCHITECTURE_V0_DECISION.md",
                start_line=12,
                end_line=45,
            ),
        )

        response = NeuralQueryResponse(
            request_id="req-101",
            status=GateStatus.SUCCESS,
            results=[item],
            metadata={"latencyMs": 14, "queryEngine": "HybridSearchEngine"},
        )

        self.assertTrue(response.is_success)
        self.assertFalse(response.is_abstention)
        self.assertEqual(len(response.results), 1)
        self.assertEqual(response.source_references, ["src-file-01"])
        self.assertEqual(response.event_references, ["ev-999"])
        self.assertEqual(response.evidence_references, ["evi-101"])

        # Dict and JSON round-trip
        data = response.to_dict()
        self.assertEqual(data["status"], "SUCCESS")
        reconstructed = NeuralQueryResponse.from_dict(data)
        self.assertEqual(reconstructed.request_id, "req-101")
        self.assertEqual(reconstructed.results[0].title, item.title)
        self.assertEqual(reconstructed.results[0].provenance.repository, "pubcoreagencia/pub-neural")

    # -------------------------------------------------------------------------
    # Scenario 4: Abstention
    # -------------------------------------------------------------------------
    def test_04_abstention(self):
        """Verify that abstention cannot be represented merely as results=[] and enforces domain semantics."""
        abstention = AbstentionMetadata(
            abstained=True,
            decision_reason="DENSE_SIMILARITY_BELOW_THRESHOLD",
            top_dense_similarity=0.68,
            top_rrf_score=0.012,
            lexical_candidate_count=0,
            dense_candidate_count=3,
            threshold_applied=0.85,
        )

        response = NeuralQueryResponse(
            request_id="req-abstain-1",
            status=GateStatus.ABSTAIN,
            results=[],
            abstention=abstention,
            reason="Query similarity 0.68 is below calibrated threshold 0.85; abstaining to prevent hallucination.",
        )

        self.assertFalse(response.is_success)
        self.assertTrue(response.is_abstention)
        self.assertIsNotNone(response.abstention)
        self.assertEqual(response.abstention.decision_reason, "DENSE_SIMILARITY_BELOW_THRESHOLD")

        # Invariant: ABSTAIN requires abstention metadata
        with self.assertRaises(GateValidationError) as ctx:
            NeuralQueryResponse(
                request_id="req-err",
                status=GateStatus.ABSTAIN,
                results=[],
                abstention=None,
            )
        self.assertIn("abstention", str(ctx.exception))

        # Invariant: ABSTAIN requires abstention.abstained == True
        with self.assertRaises(GateValidationError) as ctx:
            NeuralQueryResponse(
                request_id="req-err",
                status=GateStatus.ABSTAIN,
                results=[],
                abstention=AbstentionMetadata(abstained=False, decision_reason="ACCEPTED"),
            )
        self.assertIn("abstained == True", str(ctx.exception))

    # -------------------------------------------------------------------------
    # Scenario 5: Provenance
    # -------------------------------------------------------------------------
    def test_05_provenance_validation_and_reconstruction(self):
        """Verify provenance structure, line numbering invariants, and Git lineage checks."""
        # Valid complete provenance
        prov = ProvenanceMetadata(
            source_id="src-001",
            originating_event_id="ev-001",
            evidence_id="evi-001",
            repository="pubcoreagencia/pub-neural",
            commit_sha="1234567890abcdef1234567890abcdef12345678",
            file_path="src/retrieval/abstention.py",
            start_line=10,
            end_line=30,
            exact_quote="Thresholds MUST be calibrated from an independent calibration split",
            content_hash="e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
        )
        self.assertTrue(prov.has_git_provenance())
        self.assertTrue(prov.has_evidence_locator())

        # Invariant: start_line cannot exceed end_line
        with self.assertRaises(GateValidationError) as ctx:
            ProvenanceMetadata(start_line=50, end_line=20)
        self.assertIn("start_line (50) cannot exceed end_line (20)", str(ctx.exception))

        # Invariant: start_line must be >= 1
        with self.assertRaises(GateValidationError) as ctx:
            ProvenanceMetadata(start_line=0, end_line=10)
        self.assertIn("start_line must be >= 1", str(ctx.exception))

        # Partial provenance without Git commit
        partial_prov = ProvenanceMetadata(source_id="src-orphan")
        self.assertFalse(partial_prov.has_git_provenance())

    # -------------------------------------------------------------------------
    # Scenario 6: Stale knowledge
    # -------------------------------------------------------------------------
    def test_06_stale_knowledge(self):
        """Verify handling of stale knowledge items and the STALE response status."""
        freshness = FreshnessMetadata(
            state=FreshnessState.STALE,
            is_stale=True,
            diverged_commit_sha="deadbeef1234567890abcdef1234567890abcdef",
            reason="Referenced file was modified in subsequent commit",
        )

        stale_item = NeuralKnowledgeItem(
            id="node-stale-01",
            knowledge_class=KnowledgeClass.LESSON,
            title="Outdated dependency fix",
            content="Old guidance on pinning package X",
            freshness=freshness,
        )

        response = NeuralQueryResponse(
            request_id="req-stale-check",
            status=GateStatus.STALE,
            results=[stale_item],
            reason="Retrieved knowledge has diverged from target working branch commit",
        )

        self.assertEqual(response.status, GateStatus.STALE)
        self.assertTrue(response.results[0].freshness.is_stale)
        self.assertEqual(response.results[0].freshness.state, FreshnessState.STALE)

        # Invariant: STALE response requires at least one stale item in results
        with self.assertRaises(GateValidationError) as ctx:
            NeuralQueryResponse(
                request_id="req-invalid-stale",
                status=GateStatus.STALE,
                results=[],
                reason="Empty results cannot be status STALE",
            )
        self.assertIn("Status STALE requires at least one stale knowledge item", str(ctx.exception))

    # -------------------------------------------------------------------------
    # Scenario 7: Conflict
    # -------------------------------------------------------------------------
    def test_07_conflict(self):
        """Verify CONFLICT status and contradictory knowledge tracking."""
        contra = ContradictionItem(
            item_a_id="node-rule-01",
            item_b_id="node-rule-02",
            reason="Rule 01 mandates synchronous writeback while Rule 02 specifies async batching",
        )

        response = NeuralQueryResponse(
            request_id="req-conflict-1",
            status=GateStatus.CONFLICT,
            results=[],
            contradictions=[contra],
            reason="Contradictory knowledge detected across active governance rules",
        )

        self.assertEqual(response.status, GateStatus.CONFLICT)
        self.assertEqual(len(response.contradictions), 1)
        self.assertEqual(response.contradictions[0].item_a_id, "node-rule-01")

        # Roundtrip
        data = response.to_dict()
        reconstructed = NeuralQueryResponse.from_dict(data)
        self.assertEqual(len(reconstructed.contradictions), 1)
        self.assertEqual(reconstructed.contradictions[0].reason, contra.reason)

    # -------------------------------------------------------------------------
    # Scenario 8: Valid experience
    # -------------------------------------------------------------------------
    def test_08_valid_experience_writeback(self):
        """Verify complete, valid PDL -> Neural post-task experience writeback contract."""
        evidence = TaskEvidence(
            validation_passed=True,
            worktree_clean=True,
            push_succeeded=True,
            remote_verified=True,
            runtime_verified=True,
            test_summary={"total": 12, "passed": 12, "failed": 0},
            delivery_verified=True,
            governance_verified=True,
        )

        finding = CandidateFinding(
            finding_type=KnowledgeClass.LESSON,
            title="Always calibrate abstention threshold on split dataset",
            statement="Running abstention on uncalibrated cosine thresholds leads to high false negative rates.",
            scope="PROJECT",
            confidence=0.95,
        )

        experience = NeuralExperienceRecord(
            task_id="pdl-task-888",
            project_id="pub-dev-loop",
            repository="pubcoreagencia/pub-dev-loop",
            branch="feat/retrieval-abstention-v0.3",
            commit_sha="d1b6c5146e74f643bc25206fa410de2ca74ca494",
            remote_sha="d1b6c5146e74f643bc25206fa410de2ca74ca494",
            status=TaskExecutionStatus.COMPLETED,
            objective="Institutionalize neural product and continuity principles",
            agent_id="pdl-developer-agent",
            changed_files=["MASTER_CONTEXT.md", "docs/architecture/PUB_NEURAL_OBSERVATORY_PRODUCT_SPEC.md"],
            evidence=evidence,
            candidate_findings=[finding],
            completed_at="2026-09-14T03:12:20Z",
            ingestion_source="pdl-bidirectional-gate",
        )

        self.assertEqual(experience.task_id, "pdl-task-888")
        self.assertEqual(experience.status, TaskExecutionStatus.COMPLETED)
        self.assertTrue(experience.evidence.validation_passed)
        self.assertEqual(len(experience.candidate_findings), 1)

        # Roundtrip to dict and JSON
        data = experience.to_dict()
        self.assertEqual(data["taskId"], "pdl-task-888")
        self.assertEqual(data["evidence"]["worktreeClean"], True)

        reconstructed = NeuralExperienceRecord.from_dict(data)
        self.assertEqual(reconstructed.task_id, experience.task_id)
        self.assertEqual(reconstructed.status, TaskExecutionStatus.COMPLETED)
        self.assertEqual(reconstructed.candidate_findings[0].title, finding.title)

        # JSON roundtrip
        json_str = experience.to_json()
        from_json_obj = NeuralExperienceRecord.from_json(json_str)
        self.assertEqual(from_json_obj.task_id, experience.task_id)
        self.assertEqual(from_json_obj.evidence.test_summary["total"], 12)

    # -------------------------------------------------------------------------
    # Scenario 9: Invalid experience
    # -------------------------------------------------------------------------
    def test_09_invalid_experience_payload(self):
        """Verify that missing mandatory experience fields or invalid types raise GateValidationError."""
        valid_evidence = TaskEvidence(
            validation_passed=True,
            worktree_clean=True,
            push_succeeded=True,
            remote_verified=True,
        )

        # Missing task_id
        with self.assertRaises(GateValidationError) as ctx:
            NeuralExperienceRecord(
                task_id="",
                project_id="pub-dev-loop",
                repository="pubcoreagencia/pub-dev-loop",
                branch="feat/test",
                status=TaskExecutionStatus.COMPLETED,
                objective="Deliver feature",
                evidence=valid_evidence,
                completed_at="2026-09-14T03:00:00Z",
            )
        self.assertIn("task_id", str(ctx.exception))

        # Missing evidence
        with self.assertRaises(GateValidationError) as ctx:
            NeuralExperienceRecord(
                task_id="task-1",
                project_id="pub-dev-loop",
                repository="pubcoreagencia/pub-dev-loop",
                branch="feat/test",
                status=TaskExecutionStatus.COMPLETED,
                objective="Deliver feature",
                evidence=None,  # Invalid
                completed_at="2026-09-14T03:00:00Z",
            )
        self.assertIn("evidence", str(ctx.exception))

        # Invalid timestamp
        with self.assertRaises(GateValidationError) as ctx:
            NeuralExperienceRecord(
                task_id="task-1",
                project_id="pub-dev-loop",
                repository="pubcoreagencia/pub-dev-loop",
                branch="feat/test",
                status=TaskExecutionStatus.COMPLETED,
                objective="Deliver feature",
                evidence=valid_evidence,
                completed_at="not-a-valid-date",
            )
        self.assertIn("completed_at", str(ctx.exception))

    # -------------------------------------------------------------------------
    # Scenario 10: Invalid knowledge class
    # -------------------------------------------------------------------------
    def test_10_invalid_knowledge_class_rejection(self):
        """Verify that arbitrary or unmanaged knowledge class strings are strictly rejected."""
        # Test closed enum parsing
        with self.assertRaises(ValueError) as ctx:
            KnowledgeClass.from_str("ARBITRARY_CLASS")
        self.assertIn("Invalid knowledge class 'ARBITRARY_CLASS'", str(ctx.exception))

        with self.assertRaises(ValueError) as ctx:
            KnowledgeClass.from_str("MAGIC_PROMPT")
        self.assertIn("Must be one of:", str(ctx.exception))

        # Test rejection inside query construction
        caller = CallerIdentity(actor_id="actor-1")
        with self.assertRaises(ValueError):
            NeuralQueryRequest(
                request_id="req-1",
                task_id="task-1",
                project_id="pub-neural",
                repository="pubcoreagencia/pub-neural",
                objective="Test query",
                requested_knowledge_classes=["NON_EXISTENT_CLASS"],
                caller=caller,
                timestamp="2026-09-14T12:00:00Z",
            )

    # -------------------------------------------------------------------------
    # Scenario 11: Authority metadata
    # -------------------------------------------------------------------------
    def test_11_authority_metadata_hierarchy_and_data_only(self):
        """Verify evidence authority hierarchy ranking and enforcement of is_data_only=True."""
        levels = [
            AuthorityLevel.HISTORICAL_MEMORY,
            AuthorityLevel.VALIDATED_KNOWLEDGE,
            AuthorityLevel.TEST_EVIDENCE,
            AuthorityLevel.REAL_EXECUTION,
            AuthorityLevel.RUNTIME_DIRECT_EVIDENCE,
        ]

        # Verify strict ascending rank
        for i in range(len(levels) - 1):
            lower = levels[i]
            higher = levels[i + 1]
            self.assertTrue(higher.is_authoritative_over(lower))
            self.assertFalse(lower.is_authoritative_over(higher))
            self.assertGreater(higher.rank, lower.rank)

        # Verify AuthorityMetadata wrapper
        auth = AuthorityMetadata(level=AuthorityLevel.TEST_EVIDENCE)
        self.assertEqual(auth.rank, 3)
        self.assertTrue(auth.is_data_only)

        # Enforce that Neural knowledge is DATA and cannot have is_data_only=False
        with self.assertRaises(GateValidationError) as ctx:
            AuthorityMetadata(level=AuthorityLevel.RUNTIME_DIRECT_EVIDENCE, is_data_only=False)
        self.assertIn("Neural knowledge must always have is_data_only=True", str(ctx.exception))

    # -------------------------------------------------------------------------
    # Scenario 12: Failure states
    # -------------------------------------------------------------------------
    def test_12_failure_states_and_gate_failure(self):
        """Verify formal failure states and the standardized GateFailure model."""
        failure_statuses = [
            GateStatus.INVALID_REQUEST,
            GateStatus.NO_MATCH,
            GateStatus.ABSTAIN,
            GateStatus.CONFLICT,
            GateStatus.STALE,
            GateStatus.UNAVAILABLE,
            GateStatus.INTERNAL_ERROR,
        ]

        for st in failure_statuses:
            self.assertIsInstance(st.value, str)
            parsed = GateStatus.from_str(st.value)
            self.assertEqual(parsed, st)

        # Test NO_MATCH invariant: must have empty results
        no_match_resp = NeuralQueryResponse(
            request_id="req-nm",
            status=GateStatus.NO_MATCH,
            results=[],
            reason="Search completed; 0 items matched search criteria",
        )
        self.assertEqual(no_match_resp.status, GateStatus.NO_MATCH)
        self.assertEqual(len(no_match_resp.results), 0)

        # Invariant: NO_MATCH cannot contain results
        dummy_item = NeuralKnowledgeItem(
            id="item-1",
            knowledge_class=KnowledgeClass.DECISION,
            title="Dummy",
            content="Dummy content",
        )
        with self.assertRaises(GateValidationError) as ctx:
            NeuralQueryResponse(
                request_id="req-err",
                status=GateStatus.NO_MATCH,
                results=[dummy_item],
            )
        self.assertIn("Status NO_MATCH must have empty results list", str(ctx.exception))

        # Test GateFailure DTO
        gf = GateFailure(
            status=GateStatus.UNAVAILABLE,
            reason="PostgreSQL connection refused on port 5432",
            request_id="req-fail-01",
            details={"host": "localhost", "port": 5432},
        )
        self.assertEqual(gf.status, GateStatus.UNAVAILABLE)
        self.assertEqual(gf.reason, "PostgreSQL connection refused on port 5432")

        gf_dict = gf.to_dict()
        reconstructed_gf = GateFailure.from_dict(gf_dict)
        self.assertEqual(reconstructed_gf.status, GateStatus.UNAVAILABLE)
        self.assertEqual(reconstructed_gf.details["port"], 5432)

    # -------------------------------------------------------------------------
    # Scenario 13: Correlation & Execution Identity Contract
    # -------------------------------------------------------------------------
    def test_13_correlation_and_execution_identity(self):
        """Verify that executionId and correlationId are preserved across query and experience contracts."""
        caller = CallerIdentity(
            actor_id="agent:pdl:worker-1",
            agent_role=AgentRole.DEVELOPER,
        )
        req = NeuralQueryRequest(
            request_id="req-corr-001",
            task_id="task-corr-100",
            execution_id="exec-corr-200",
            correlation_id="corr-thread-300",
            project_id="pub-dev-loop",
            repository="pubcoreagencia/pub-dev-loop",
            objective="Retrieve correlation rules",
            requested_knowledge_classes=[KnowledgeClass.RULE],
            caller=caller,
            timestamp="2026-09-14T12:00:00Z",
        )
        d = req.to_dict()
        self.assertEqual(d["executionId"], "exec-corr-200")
        self.assertEqual(d["correlationId"], "corr-thread-300")
        self.assertEqual(d["taskId"], "task-corr-100")

        reconstructed_req = NeuralQueryRequest.from_dict(d)
        self.assertEqual(reconstructed_req.execution_id, "exec-corr-200")
        self.assertEqual(reconstructed_req.correlation_id, "corr-thread-300")
        self.assertEqual(reconstructed_req.task_id, "task-corr-100")

        # Response
        resp = NeuralQueryResponse(
            request_id="req-corr-001",
            status=GateStatus.SUCCESS,
            task_id="task-corr-100",
            execution_id="exec-corr-200",
            correlation_id="corr-thread-300",
        )
        resp_dict = resp.to_dict()
        self.assertEqual(resp_dict["executionId"], "exec-corr-200")
        self.assertEqual(resp_dict["correlationId"], "corr-thread-300")
        reconstructed_resp = NeuralQueryResponse.from_dict(resp_dict)
        self.assertEqual(reconstructed_resp.execution_id, "exec-corr-200")
        self.assertEqual(reconstructed_resp.correlation_id, "corr-thread-300")


if __name__ == "__main__":
    unittest.main()
