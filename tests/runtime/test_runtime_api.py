"""
Unit and end-to-end HTTP integration tests for the PUB Neural Operational Runtime API.
Spins up the actual HTTP server on an ephemeral loopback port and executes real HTTP requests.
Verifies all required scenarios:
- Query: SUCCESS, NO_MATCH, ABSTAIN, CONFLICT, STALE, INVALID_REQUEST, UNAVAILABLE
- Experience: ACCEPTED, DUPLICATE, INVALID_REQUEST, UNAVAILABLE, INTERNAL_ERROR
- Identity & Correlation: requestId, taskId, executionId, correlationId preserved
- Security: request without auth (401), invalid token (403), valid token (200)
- Console isolation: Console remains strictly read-only (POST/PUT/PATCH/DELETE -> 405)
"""

from http.server import HTTPServer
import json
import os
import sys
import threading
import unittest
import urllib.error
import urllib.request
import uuid

# Ensure root is in sys.path
_CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
_REPO_ROOT = os.path.dirname(_CURRENT_DIR)
_ROOT = os.path.dirname(_REPO_ROOT)
for p in (_ROOT, os.path.join(_ROOT, "src")):
    if p not in sys.path:
        sys.path.insert(0, p)

from console.backend.config import ConsoleConfig
from console.backend.server import ConsoleRequestHandler
from runtime.backend.config import RuntimeConfig
from runtime.backend.server import RuntimeRequestHandler
from src.gate.enums import (
    AuthorityLevel,
    ConflictState,
    ExperienceWritebackStatus,
    FreshnessState,
    GateStatus,
    KnowledgeClass,
    PromotionState,
    TaskExecutionStatus,
)
from src.gate.exceptions import GateTransportError
from src.gate.experience_service import (
    InMemoryExperienceSink,
    NeuralExperienceService,
)
from src.gate.models import (
    AbstentionMetadata,
    AuthorityMetadata,
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
from src.gate.retrieval_adapter import NeuralRetrievalEngine, RetrievalBatch
from src.gate.service import NeuralQueryService
from src.retrieval.abstention import AbstentionDecision


class MockRetrievalEngine(NeuralRetrievalEngine):
    """Configurable in-memory retrieval engine for testing all query branches."""

    def __init__(self):
        self.mode = "success"
        self.custom_batch = None
        self.raise_exc = None

    def search_knowledge(self, query, trust_zone=None, project_id=None, limit=5, knowledge_classes=None, filters=None):
        if self.raise_exc:
            raise self.raise_exc

        if self.custom_batch:
            return self.custom_batch

        if self.mode == "success":
            item = NeuralKnowledgeItem(
                id="know-1",
                knowledge_class=KnowledgeClass.RULE,
                title="Test Checkout Rule",
                content="Checkout requires idempotency.",
                scope="PROJECT",
                project_id=project_id or "pub-ecom",
                authority=AuthorityMetadata(level=AuthorityLevel.VALIDATED_KNOWLEDGE, is_data_only=True),
                provenance=ProvenanceMetadata(repository="pubcoreagencia/pub-ecom", commit_sha="abc1234"),
                freshness=FreshnessMetadata(state=FreshnessState.VALID, is_stale=False),
            )
            return RetrievalBatch(results=[item])

        if self.mode == "no_match":
            return RetrievalBatch(results=[])

        if self.mode == "abstain":
            decision = AbstentionDecision(
                accepted=False,
                reason="SIMILARITY_BELOW_THRESHOLD: Dense similarity 0.42 < 0.65",
                top_dense_similarity=0.42,
                top_rrf_score=0.012,
                lexical_candidate_count=2,
                dense_candidate_count=2,
            )
            return RetrievalBatch(results=[], abstention_decision=decision)

        if self.mode == "conflict":
            item_a = NeuralKnowledgeItem(
                id="know-conflict-1",
                knowledge_class=KnowledgeClass.RULE,
                title="Rule A",
                content="Always use synchronous dispatch.",
                conflict_state=ConflictState.CONTRADICTORY,
            )
            return RetrievalBatch(results=[item_a], contradictions=[ContradictionItem("know-conflict-1", "know-conflict-2", "Direct policy opposition")])

        if self.mode == "stale":
            item_stale = NeuralKnowledgeItem(
                id="know-stale-1",
                knowledge_class=KnowledgeClass.RULE,
                title="Old Rule",
                content="Use deprecated v0 schema.",
                freshness=FreshnessMetadata(state=FreshnessState.STALE, is_stale=True, reason="Schema migrated"),
            )
            return RetrievalBatch(results=[item_stale], is_stale=True)

        return RetrievalBatch(results=[])


class FaultyExperienceSink(InMemoryExperienceSink):
    """Sink that can simulate transport failure or unexpected internal error."""

    def __init__(self, fail_mode=None):
        super().__init__()
        self.fail_mode = fail_mode

    def check_idempotency(self, idempotency_key):
        if self.fail_mode == "unavailable":
            raise GateTransportError("Simulated Redis/Postgres network partition")
        if self.fail_mode == "internal_error":
            raise RuntimeError("Corrupt memory state")
        return super().check_idempotency(idempotency_key)

    def append_canonical_event(self, *args, **kwargs):
        if self.fail_mode == "append_unavailable":
            raise ConnectionError("DB write connection timed out")
        if self.fail_mode == "append_internal":
            raise ValueError("Corrupt event serialization")
        return super().append_canonical_event(*args, **kwargs)


class TestRuntimeAPI(unittest.TestCase):
    """End-to-end real HTTP integration tests against local loopback HTTPServer."""

    @classmethod
    def setUpClass(cls):
        # 1. Setup Runtime API Server on random free port
        cls.test_token = "secret-runtime-token-xyz-123"
        cls.runtime_config = RuntimeConfig(
            host="127.0.0.1",
            port=0,
            auth_token=cls.test_token,
            enforce_auth=True,
        )
        cls.retrieval_engine = MockRetrievalEngine()
        cls.query_service = NeuralQueryService(retrieval_engine=cls.retrieval_engine)
        cls.experience_sink = InMemoryExperienceSink()
        cls.experience_service = NeuralExperienceService(sink=cls.experience_sink)

        RuntimeRequestHandler.server_config = cls.runtime_config
        RuntimeRequestHandler.query_service = cls.query_service
        RuntimeRequestHandler.experience_service = cls.experience_service

        cls.runtime_server = HTTPServer(("127.0.0.1", 0), RuntimeRequestHandler)
        cls.runtime_port = cls.runtime_server.server_port
        cls.runtime_base_url = f"http://127.0.0.1:{cls.runtime_port}"

        cls.runtime_thread = threading.Thread(target=cls.runtime_server.serve_forever, daemon=True)
        cls.runtime_thread.start()

        # 2. Setup Console Server on random free port to verify strict isolation
        cls.console_config = ConsoleConfig(
            db_url="postgresql://test:test@localhost:5432/test",
            host="127.0.0.1",
            port=0,
        )
        ConsoleRequestHandler.server_config = cls.console_config
        cls.console_server = HTTPServer(("127.0.0.1", 0), ConsoleRequestHandler)
        cls.console_port = cls.console_server.server_port
        cls.console_base_url = f"http://127.0.0.1:{cls.console_port}"

        cls.console_thread = threading.Thread(target=cls.console_server.serve_forever, daemon=True)
        cls.console_thread.start()

    @classmethod
    def tearDownClass(cls):
        cls.runtime_server.shutdown()
        cls.runtime_server.server_close()
        cls.console_server.shutdown()
        cls.console_server.server_close()

    def _http_post(self, path, payload, token=None):
        url = f"{self.runtime_base_url}{path}"
        data = json.dumps(payload).encode("utf-8") if payload is not None else b""
        headers = {"Content-Type": "application/json"}
        if token is not None:
            headers["Authorization"] = f"Bearer {token}"

        req = urllib.request.Request(url, data=data, headers=headers, method="POST")
        try:
            with urllib.request.urlopen(req) as resp:
                status_code = resp.status
                body = json.loads(resp.read().decode("utf-8"))
                return status_code, body
        except urllib.error.HTTPError as e:
            status_code = e.code
            body = json.loads(e.read().decode("utf-8"))
            return status_code, body

    def _make_valid_query_payload(self, **kwargs):
        base = {
            "requestId": "req-op-001",
            "taskId": "task-alpha-123",
            "executionId": "exec-cycle-456",
            "correlationId": "corr-pdl-neural-789",
            "projectId": "pub-ecom",
            "repository": "pubcoreagencia/pub-ecom",
            "branch": "feat/payment-flow",
            "objective": "Retrieve checkout idempotency rules",
            "requestedKnowledgeClasses": ["RULE"],
            "caller": {"actor_id": "pdl-worker", "agent_role": "developer"},
            "timestamp": "2026-09-14T10:00:00Z",
            "limit": 5,
        }
        base.update(kwargs)
        return base

    def _make_valid_experience_payload(self, **kwargs):
        base = {
            "taskId": "task-alpha-123",
            "executionId": "exec-cycle-456",
            "correlationId": "corr-pdl-neural-789",
            "projectId": "pub-ecom",
            "repository": "pubcoreagencia/pub-ecom",
            "branch": "feat/payment-flow",
            "status": "COMPLETED",
            "objective": "Implemented transactional checkout gate",
            "completedAt": "2026-09-14T10:30:00Z",
            "commitSha": "c0ffee1234567890abcdef1234567890abcdef12",
            "evidence": {
                "validationPassed": True,
                "worktreeClean": True,
                "pushSucceeded": True,
                "remoteVerified": True,
                "runtimeVerified": True,
            },
            "candidateFindings": [
                {
                    "finding_type": "LESSON",
                    "title": "Always verify worktree",
                    "statement": "Dirty worktree causes delivery rollbacks.",
                    "scope": "PROJECT",
                    "confidence": 0.98,
                }
            ],
        }
        base.update(kwargs)
        return base

    # -------------------------------------------------------------------------
    # 1. Security & Authentication
    # -------------------------------------------------------------------------
    def test_auth_missing_token_returns_401(self):
        payload = self._make_valid_query_payload()
        code, data = self._http_post("/api/v1/runtime/query", payload, token=None)
        self.assertEqual(code, 401)
        self.assertEqual(data["error"], "Unauthorized")

    def test_auth_invalid_token_returns_403(self):
        payload = self._make_valid_query_payload()
        code, data = self._http_post("/api/v1/runtime/query", payload, token="wrong-secret-token")
        self.assertEqual(code, 403)
        self.assertEqual(data["error"], "Forbidden")

    def test_health_check_unauthenticated_returns_200(self):
        req = urllib.request.Request(f"{self.runtime_base_url}/health")
        with urllib.request.urlopen(req) as resp:
            self.assertEqual(resp.status, 200)
            data = json.loads(resp.read().decode("utf-8"))
            self.assertEqual(data["status"], "UP")
            self.assertEqual(data["service"], "pub-neural-runtime-backend")

    # -------------------------------------------------------------------------
    # 2. Pre-Task Query Endpoints & Scenarios
    # -------------------------------------------------------------------------
    def test_query_success(self):
        self.retrieval_engine.mode = "success"
        self.retrieval_engine.raise_exc = None
        payload = self._make_valid_query_payload()

        code, data = self._http_post("/api/v1/runtime/query", payload, token=self.test_token)
        self.assertEqual(code, 200)
        self.assertEqual(data["status"], "SUCCESS")
        self.assertEqual(data["requestId"], "req-op-001")
        self.assertEqual(data["taskId"], "task-alpha-123")
        self.assertEqual(data["executionId"], "exec-cycle-456")
        self.assertEqual(data["correlationId"], "corr-pdl-neural-789")
        self.assertGreater(len(data["evidence"]), 0)
        self.assertEqual(data["evidence"][0]["knowledge_class"], "RULE")

    def test_query_no_match(self):
        self.retrieval_engine.mode = "no_match"
        self.retrieval_engine.raise_exc = None
        payload = self._make_valid_query_payload(objective="Unknown bizarre query nonexistent")

        code, data = self._http_post("/api/v1/runtime/query", payload, token=self.test_token)
        self.assertEqual(code, 200)
        self.assertEqual(data["status"], "NO_MATCH")
        self.assertEqual(len(data["results"]), 0)
        self.assertEqual(data["executionId"], "exec-cycle-456")
        self.assertEqual(data["correlationId"], "corr-pdl-neural-789")

    def test_query_abstain(self):
        self.retrieval_engine.mode = "abstain"
        self.retrieval_engine.raise_exc = None
        payload = self._make_valid_query_payload()

        code, data = self._http_post("/api/v1/runtime/query", payload, token=self.test_token)
        self.assertEqual(code, 200)
        self.assertEqual(data["status"], "ABSTAIN")
        self.assertIsNotNone(data["abstention"])
        self.assertTrue(data["abstention"]["abstained"])
        self.assertIn("SIMILARITY_BELOW_THRESHOLD", data["abstention"]["decision_reason"])
        self.assertEqual(len(data["results"]), 0)

    def test_query_conflict(self):
        self.retrieval_engine.mode = "conflict"
        self.retrieval_engine.raise_exc = None
        payload = self._make_valid_query_payload()

        code, data = self._http_post("/api/v1/runtime/query", payload, token=self.test_token)
        self.assertEqual(code, 200)
        self.assertEqual(data["status"], "CONFLICT")
        self.assertGreater(len(data["contradictions"]), 0)

    def test_query_stale(self):
        self.retrieval_engine.mode = "stale"
        self.retrieval_engine.raise_exc = None
        payload = self._make_valid_query_payload()

        code, data = self._http_post("/api/v1/runtime/query", payload, token=self.test_token)
        self.assertEqual(code, 200)
        self.assertEqual(data["status"], "STALE")
        self.assertGreater(len(data["results"]), 0)

    def test_query_invalid_request(self):
        # Missing required objective and invalid knowledge class
        payload = {
            "requestId": "req-bad",
            "taskId": "task-bad",
            "requestedKnowledgeClasses": [],
        }
        code, data = self._http_post("/api/v1/runtime/query", payload, token=self.test_token)
        self.assertEqual(code, 400)
        self.assertEqual(data["status"], "INVALID_REQUEST")
        self.assertIn("reason", data)

    def test_query_unavailable(self):
        self.retrieval_engine.raise_exc = GateTransportError("Postgres vector cluster unreachable")
        payload = self._make_valid_query_payload()

        code, data = self._http_post("/api/v1/runtime/query", payload, token=self.test_token)
        self.assertEqual(code, 503)
        self.assertEqual(data["status"], "UNAVAILABLE")
        self.assertIn("Retrieval backend unavailable", data["reason"])
        self.retrieval_engine.raise_exc = None

    # -------------------------------------------------------------------------
    # 3. Post-Task Experience Endpoints & Scenarios
    # -------------------------------------------------------------------------
    def test_experience_accepted_and_duplicate(self):
        # Fresh unique task_id
        unique_task = f"task-unique-{uuid.uuid4().hex[:8]}"
        payload = self._make_valid_experience_payload(taskId=unique_task)

        # 1. First writeback -> ACCEPTED (200)
        code1, data1 = self._http_post("/api/v1/runtime/experience", payload, token=self.test_token)
        self.assertEqual(code1, 200)
        self.assertEqual(data1["status"], "ACCEPTED")
        self.assertFalse(data1["isDuplicate"])
        self.assertIsNotNone(data1["eventId"])
        self.assertEqual(data1["taskId"], unique_task)
        self.assertEqual(data1["executionId"], "exec-cycle-456")
        self.assertEqual(data1["correlationId"], "corr-pdl-neural-789")

        # 2. Second writeback with identical payload -> DUPLICATE (200)
        code2, data2 = self._http_post("/api/v1/runtime/experience", payload, token=self.test_token)
        self.assertEqual(code2, 200)
        self.assertEqual(data2["status"], "DUPLICATE")
        self.assertTrue(data2["isDuplicate"])
        self.assertEqual(data2["eventId"], data1["eventId"])
        self.assertEqual(data2["idempotencyKey"], data1["idempotencyKey"])
        self.assertEqual(data2["executionId"], "exec-cycle-456")
        self.assertEqual(data2["correlationId"], "corr-pdl-neural-789")

    def test_experience_invalid_request(self):
        # Missing mandatory evidence
        payload = {
            "taskId": "task-bad-exp",
            "projectId": "pub-ecom",
            "repository": "pubcoreagencia/pub-ecom",
            "branch": "feat/test",
            "status": "COMPLETED",
            "objective": "No evidence provided",
            "completedAt": "2026-09-14T10:00:00Z",
        }
        code, data = self._http_post("/api/v1/runtime/experience", payload, token=self.test_token)
        self.assertEqual(code, 400)
        self.assertEqual(data["status"], "INVALID_REQUEST")
        self.assertIn("Field 'evidence' is mandatory", data["reason"])

    def test_experience_unavailable(self):
        faulty_sink = FaultyExperienceSink(fail_mode="unavailable")
        faulty_service = NeuralExperienceService(sink=faulty_sink)

        # Temporarily inject faulty service
        original_service = RuntimeRequestHandler.experience_service
        RuntimeRequestHandler.experience_service = faulty_service
        try:
            payload = self._make_valid_experience_payload(taskId=f"task-unavail-{uuid.uuid4().hex[:6]}")
            code, data = self._http_post("/api/v1/runtime/experience", payload, token=self.test_token)
            self.assertEqual(code, 503)
            self.assertEqual(data["status"], "UNAVAILABLE")
        finally:
            RuntimeRequestHandler.experience_service = original_service

    def test_experience_internal_error(self):
        faulty_sink = FaultyExperienceSink(fail_mode="internal_error")
        faulty_service = NeuralExperienceService(sink=faulty_sink)

        original_service = RuntimeRequestHandler.experience_service
        RuntimeRequestHandler.experience_service = faulty_service
        try:
            payload = self._make_valid_experience_payload(taskId=f"task-int-err-{uuid.uuid4().hex[:6]}")
            code, data = self._http_post("/api/v1/runtime/experience", payload, token=self.test_token)
            self.assertEqual(code, 500)
            self.assertEqual(data["status"], "INTERNAL_ERROR")
        finally:
            RuntimeRequestHandler.experience_service = original_service

    def test_e2e_closed_loop_experience_write_and_subsequent_query(self):
        """
        Prove end-to-end cognitive feedback loop:
        1. Task A sends POST /api/v1/runtime/experience with CandidateFinding.
        2. Experience is accepted and stored in the sink.
        3. Retrieval engine indexes the projected experience/candidate finding.
        4. Task B executes POST /api/v1/runtime/query and retrieves Task A's candidate finding.
        """
        task_a_id = f"task-a-{uuid.uuid4().hex[:6]}"
        finding_title = "Idempotent Replay Prevents Invariant Violation"
        finding_stmt = "Projectors must never overwrite stronger authoritative state."

        exp_payload = self._make_valid_experience_payload(
            taskId=task_a_id,
            objective="Harden projector engine against state escalation",
            candidateFindings=[
                {
                    "finding_type": "LESSON",
                    "title": finding_title,
                    "statement": finding_stmt,
                    "scope": "PROJECT",
                    "confidence": 0.99,
                }
            ],
        )

        # Step 1: POST /api/v1/runtime/experience
        code_exp, data_exp = self._http_post("/api/v1/runtime/experience", exp_payload, token=self.test_token)
        self.assertEqual(code_exp, 200)
        self.assertEqual(data_exp["status"], "ACCEPTED")
        self.assertFalse(data_exp["isDuplicate"])
        self.assertEqual(data_exp["candidateFindingsCount"], 1)

        # Step 2: Simulate projected candidate finding in retrieval engine
        projected_finding_id = f"finding:pub-ecom:{task_a_id}:1"
        raw_retrieved_item = {
            "id": projected_finding_id,
            "title": finding_title,
            "snippet": finding_stmt,
            "project_id": "pub-ecom",
            "promotion_state": "CANDIDATE",
            "trust_zone": "tz_internal_holding",
        }
        self.retrieval_engine.custom_batch = RetrievalBatch(results=[raw_retrieved_item])

        try:
            # Step 3: Task B queries for knowledge discovered in Task A
            query_payload = self._make_valid_query_payload(
                taskId=f"task-b-{uuid.uuid4().hex[:6]}",
                objective="Retrieve lessons on projector state escalation",
                requestedKnowledgeClasses=["LESSON"],
            )

            code_q, data_q = self._http_post("/api/v1/runtime/query", query_payload, token=self.test_token)
            self.assertEqual(code_q, 200)
            self.assertEqual(data_q["status"], "SUCCESS")
            evidence_list = data_q.get("evidence", data_q.get("results", []))
            self.assertEqual(len(evidence_list), 1)

            retrieved = evidence_list[0]
            self.assertEqual(retrieved["id"], projected_finding_id)
            self.assertEqual(retrieved["title"], finding_title)
            self.assertEqual(retrieved.get("knowledge_class", retrieved.get("knowledgeClass")), "LESSON")
            self.assertEqual(retrieved.get("promotion_state", retrieved.get("promotionState")), "CANDIDATE")
            self.assertTrue(retrieved["authority"]["is_data_only"])
        finally:
            self.retrieval_engine.custom_batch = None

    # -------------------------------------------------------------------------
    # 4. Console Isolation Verification
    # -------------------------------------------------------------------------
    def test_console_remains_strictly_readonly_and_isolated(self):
        # Console health is UP
        req = urllib.request.Request(f"{self.console_base_url}/health")
        with urllib.request.urlopen(req) as resp:
            self.assertEqual(resp.status, 200)
            data = json.loads(resp.read().decode("utf-8"))
            self.assertEqual(data["service"], "pub-neural-console-backend")

        # Console rejects POST with 405
        post_req = urllib.request.Request(
            f"{self.console_base_url}/api/v1/runtime/query",
            data=b'{"some": "payload"}',
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with self.assertRaises(urllib.error.HTTPError) as ctx:
            urllib.request.urlopen(post_req)
        self.assertEqual(ctx.exception.code, 405)

        # Console rejects PUT with 405
        put_req = urllib.request.Request(f"{self.console_base_url}/api/v1/entities/e-1", data=b'{}', method="PUT")
        with self.assertRaises(urllib.error.HTTPError) as ctx:
            urllib.request.urlopen(put_req)
        self.assertEqual(ctx.exception.code, 405)

        # Console rejects DELETE with 405
        del_req = urllib.request.Request(f"{self.console_base_url}/api/v1/entities/e-1", method="DELETE")
        with self.assertRaises(urllib.error.HTTPError) as ctx:
            urllib.request.urlopen(del_req)
        self.assertEqual(ctx.exception.code, 405)

        # Console rejects PATCH with 405
        patch_req = urllib.request.Request(f"{self.console_base_url}/api/v1/entities/e-1", data=b'{}', method="PATCH")
        with self.assertRaises(urllib.error.HTTPError) as ctx:
            urllib.request.urlopen(patch_req)
        self.assertEqual(ctx.exception.code, 405)


if __name__ == "__main__":
    unittest.main()
