import json
import os
import threading
import unittest
import urllib.request
import urllib.error

from http.server import HTTPServer

from runtime.backend.config import RuntimeConfig
from runtime.backend.entrypoint import PostgresExperienceSink
from runtime.backend.server import RuntimeRequestHandler
from src.gate.service import NeuralQueryService
from src.gate.retrieval_adapter import HybridSearchAdapter, NeuralResultMapper
from src.retrieval.hybrid_search import HybridSearchEngine
from src.retrieval.embedding_model import MockDeterministicEmbeddingProvider

class TestRuntimePostgresE2E(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.db_url = os.environ.get("PUB_NEURAL_E2E_DB_URL")
        if not cls.db_url:
            raise unittest.SkipTest("PUB_NEURAL_E2E_DB_URL not configured")

        cls.token = "runtime-e2e-token"
        cfg = RuntimeConfig(host="127.0.0.1", port=0, auth_token=cls.token, enforce_auth=True)
        sink = PostgresExperienceSink(cls.db_url)
        engine = HybridSearchEngine(db_url=cls.db_url, embedding_provider=MockDeterministicEmbeddingProvider())
        query_service = NeuralQueryService(
            retrieval_engine=HybridSearchAdapter(engine),
            result_mapper=NeuralResultMapper(),
        )
        from src.gate.experience_service import NeuralExperienceService
        experience_service = NeuralExperienceService(sink=sink, project_catalog=sink)

        RuntimeRequestHandler.server_config = cfg
        RuntimeRequestHandler.query_service = query_service
        RuntimeRequestHandler.experience_service = experience_service
        cls.server = HTTPServer(("127.0.0.1", 0), RuntimeRequestHandler)
        cls.port = cls.server.server_port
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()

    @classmethod
    def tearDownClass(cls):
        if hasattr(cls, "server"):
            cls.server.shutdown()
            cls.server.server_close()

    def post(self, path, payload):
        req = urllib.request.Request(
            f"http://127.0.0.1:{self.port}{path}",
            data=json.dumps(payload).encode(),
            headers={"Content-Type": "application/json", "Authorization": f"Bearer {self.token}"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(req) as response:
                return response.status, json.loads(response.read().decode())
        except urllib.error.HTTPError as exc:
            return exc.code, json.loads(exc.read().decode())

    def test_real_postgres_closed_loop(self):
        suffix = os.urandom(4).hex()
        task_id = f"runtime-e2e-{suffix}"
        title = f"Runtime E2E lesson {suffix}"
        statement = "Candidate experience must survive canonical reduction before retrieval."

        payload = {
            "taskId": task_id,
            "executionId": f"exec-{suffix}",
            "correlationId": f"corr-{suffix}",
            "projectId": "proj:runtime-e2e",
            "repository": "pubcoreagencia/runtime-e2e",
            "branch": "main",
            "status": "COMPLETED",
            "objective": "Prove runtime ingestion reaches reducer and retrieval",
            "occurredAt": "2026-09-17T20:00:00Z",
            "completedAt": "2026-09-17T20:01:00Z",
            "commitSha": "0123456789abcdef0123456789abcdef01234567",
            "evidence": {
                "validationPassed": True,
                "worktreeClean": True,
                "pushSucceeded": True,
                "remoteVerified": True,
                "runtimeVerified": True,
            },
            "candidateFindings": [{
                "finding_type": "LESSON",
                "title": title,
                "statement": statement,
                "scope": "PROJECT",
                "confidence": 0.99,
            }],
        }

        code, accepted = self.post("/api/v1/runtime/experience", payload)
        self.assertEqual(code, 200, accepted)
        self.assertEqual(accepted["status"], "ACCEPTED")
        self.assertFalse(accepted["isDuplicate"])

        import psycopg2
        with psycopg2.connect(self.db_url) as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT id, payload->>'occurredAt', payload->>'completedAt', payload->>'ingestedAt', payload->>'candidateState' FROM pub_neural.neural_events WHERE id=%s::uuid", (accepted["eventId"],))
                row = cur.fetchone()
                self.assertIsNotNone(row)
                self.assertEqual(row[1], "2026-09-17T20:00:00Z")
                self.assertEqual(row[2], "2026-09-17T20:01:00Z")
                self.assertIsNotNone(row[3])
                self.assertEqual(row[4], "CANDIDATE")

                cur.execute("SELECT id, promotion_state, originating_event_id FROM pub_neural.neural_nodes WHERE id LIKE %s", (f"finding:proj:runtime-e2e:{task_id}:%",))
                projected = cur.fetchone()
                self.assertIsNotNone(projected)
                self.assertEqual(projected[1], "CANDIDATE")
                self.assertEqual(str(projected[2]), accepted["eventId"])

        query = {
            "requestId": f"req-{suffix}",
            "taskId": f"query-{suffix}",
            "executionId": f"query-exec-{suffix}",
            "correlationId": f"query-corr-{suffix}",
            "projectId": "proj:runtime-e2e",
            "repository": "pubcoreagencia/runtime-e2e",
            "branch": "main",
            "objective": title,
            "requestedKnowledgeClasses": ["LESSON"],
            "caller": {"actor_id": "pdl-worker", "agent_role": "developer"},
            "timestamp": "2026-09-17T20:02:00Z",
            "limit": 5,
        }
        qcode, result = self.post("/api/v1/runtime/query", query)
        self.assertEqual(qcode, 200)
        self.assertEqual(result["status"], "SUCCESS")
        evidence = result.get("evidence", result.get("results", []))
        self.assertTrue(any(item.get("title") == title for item in evidence))

if __name__ == "__main__":
    unittest.main()
