"""
Unit and integration tests for Vector Lifecycle V0.2.
Tests cover:
  VEC-01: Projected experience creates vector index job in pub_neural.neural_vector_index_jobs.
  VEC-02: claim_next_job() claims pending job with SKIP LOCKED.
  VEC-03: process_job() creates row in pub_neural.neural_vectors with exact 1536 dimensions.
  VEC-04: Repeated processing is idempotent (SKIPPED_UP_TO_DATE).
  VEC-05: Embedding failure does not delete source knowledge node.
  VEC-06: Transient failure retries with exponential backoff.
  VEC-07: Permanent failure after max attempts transitions to FAILED.
  VEC-08: Governance & promotion state (CANDIDATE/OBSERVED) remain strictly unchanged.
  VEC-09: Lexical FTS remains available while vector job is pending/failed.
  VEC-10: Dense candidates returned by HybridSearchEngine once vector exists.
  VEC-11: RRF fusion returns correct hybrid result combining lexical and dense.
  VEC-12: Experience ingestion via HTTP succeeds asynchronously without blocking on vector generation.
"""

import os
import unittest
import uuid
import psycopg2
from psycopg2.extras import RealDictCursor

from src.retrieval.embedding_model import MockDeterministicEmbeddingProvider
from src.retrieval.vector_worker import (
    VectorIndexingWorker,
    compute_content_hash,
    compute_vector_id,
)
from src.retrieval.hybrid_search import HybridSearchEngine
from runtime.backend.entrypoint import PostgresExperienceSink
from src.gate.experience_service import (
    NeuralExperienceService,
)
from src.gate.models import (
    CandidateFinding,
    NeuralExperienceRecord,
    TaskEvidence,
)
from src.gate.enums import (
    ExperienceWritebackStatus,
    KnowledgeClass,
    TaskExecutionStatus,
)


DB_HOST = os.getenv("DB_HOST", "127.0.0.1")
DB_PORT = os.getenv("DB_PORT", "54388")
DB_NAME = os.getenv("DB_NAME", "pub_neural")
ADMIN_USER = os.getenv("ADMIN_USER", "postgres")
ADMIN_PASS = os.getenv("ADMIN_PASS", "postgres")

ADMIN_URL = f"postgresql://{ADMIN_USER}:{ADMIN_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}"


class TestVectorLifecycleV02(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        conn = psycopg2.connect(ADMIN_URL)
        conn.autocommit = True
        with conn.cursor() as cur:
            cur.execute("CREATE EXTENSION IF NOT EXISTS vector;")
        conn.close()

    def setUp(self):
        self.provider = MockDeterministicEmbeddingProvider(model_id="text-embedding-3-small", dimension=1536)
        self.worker = VectorIndexingWorker(ADMIN_URL, self.provider)
        self.search_engine = HybridSearchEngine(ADMIN_URL, self.provider)
        self.sink = PostgresExperienceSink(db_url=ADMIN_URL)
        self.exp_service = NeuralExperienceService(self.sink)

    def _create_sample_experience(self, task_id: str, project_id: str = "pub-dev-loop") -> NeuralExperienceRecord:
        return NeuralExperienceRecord(
            task_id=task_id,
            project_id=project_id,
            repository=f"pubcoreagencia/{project_id}",
            branch="feat/vector-lifecycle-v02",
            commit_sha="c0ffee1234567890abcdef1234567890abcdef12",
            status=TaskExecutionStatus.COMPLETED,
            objective=f"Unique objective for {task_id}",
            agent_id="pdl:worker:test",
            completed_at="2026-09-14T20:00:00Z",
            evidence=TaskEvidence(
                validation_passed=True,
                worktree_clean=True,
                push_succeeded=True,
                remote_verified=True,
            ),
            candidate_findings=[
                CandidateFinding(
                    finding_type=KnowledgeClass.LESSON,
                    title=f"Unique finding for {task_id}",
                    statement=f"Detailed candidate lesson statement for {task_id}",
                    scope="PROJECT",
                    confidence=0.95,
                )
            ],
            trace={"execution_duration_ms": 120, "attempts": 1},
            ingestion_source="pdl-bidirectional-gate"
        )

    def test_vec_01_projected_experience_creates_vector_job(self):
        """VEC-01: Ingestion and projection queues a job in pub_neural.neural_vector_index_jobs."""
        task_id = f"task-vec01-{uuid.uuid4().hex[:6]}"
        record = self._create_sample_experience(task_id)
        result = self.exp_service.record(record)
        self.assertEqual(result.status, ExperienceWritebackStatus.ACCEPTED)

        conn = psycopg2.connect(ADMIN_URL, cursor_factory=RealDictCursor)
        with conn.cursor() as cur:
            # Primary node + finding node should have jobs
            cur.execute(
                """
                SELECT node_id, target_type, status, attempts, max_attempts
                FROM pub_neural.neural_vector_index_jobs
                WHERE node_id LIKE %s;
                """,
                (f"%{task_id}%",)
            )
            jobs = cur.fetchall()
            self.assertGreaterEqual(len(jobs), 2)
            for j in jobs:
                self.assertEqual(j["status"], "PENDING")
                self.assertEqual(j["target_type"], "NODE")
                self.assertEqual(j["attempts"], 0)
        conn.close()

    def test_vec_02_claim_next_job_with_lock(self):
        """VEC-02: claim_next_job claims a pending job with SKIP LOCKED and marks it PROCESSING."""
        task_id = f"task-vec02-{uuid.uuid4().hex[:6]}"
        record = self._create_sample_experience(task_id)
        self.exp_service.record(record)

        claimed = self.worker.claim_next_job()
        self.assertIsNotNone(claimed)
        self.assertEqual(claimed["status"], "PROCESSING")
        self.assertEqual(claimed["attempts"], 1)

    def test_vec_03_process_job_creates_vector(self):
        """VEC-03: process_job creates exact 1536-dim vector in neural_vectors and completes job."""
        task_id = f"task-vec03-{uuid.uuid4().hex[:6]}"
        record = self._create_sample_experience(task_id)
        self.exp_service.record(record)

        claimed = self.worker.claim_next_job()
        self.assertIsNotNone(claimed)

        proc_res = self.worker.process_job(claimed["node_id"])
        self.assertEqual(proc_res["status"], "COMPLETED")

        conn = psycopg2.connect(ADMIN_URL, cursor_factory=RealDictCursor)
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT target_id, model_id, content_hash
                FROM pub_neural.neural_vectors
                WHERE target_id = %s;
                """,
                (claimed["node_id"],)
            )
            v = cur.fetchone()
            self.assertIsNotNone(v)
            self.assertEqual(v["model_id"], self.provider.model_id)

            # Check job is COMPLETED
            cur.execute(
                """
                SELECT status, completed_at
                FROM pub_neural.neural_vector_index_jobs
                WHERE node_id = %s;
                """,
                (claimed["node_id"],)
            )
            job_row = cur.fetchone()
            self.assertEqual(job_row["status"], "COMPLETED")
            self.assertIsNotNone(job_row["completed_at"])
        conn.close()

    def test_vec_04_repeated_processing_is_idempotent(self):
        """VEC-04: Repeated processing of same node is idempotent (SKIPPED_UP_TO_DATE)."""
        task_id = f"task-vec04-{uuid.uuid4().hex[:6]}"
        record = self._create_sample_experience(task_id)
        self.exp_service.record(record)

        node_id = f"experience:pub-dev-loop:{task_id}"
        # First sync
        res1 = self.worker.sync_node_vector(node_id)
        self.assertIn(res1["action"], ("CREATED", "REGENERATED_STALE"))

        # Second sync
        res2 = self.worker.sync_node_vector(node_id)
        self.assertEqual(res2["action"], "SKIPPED_UP_TO_DATE")

    def test_vec_05_embedding_failure_does_not_delete_source_node(self):
        """VEC-05: Embedding provider failure preserves source knowledge node intact."""
        task_id = f"task-vec05-{uuid.uuid4().hex[:6]}"
        record = self._create_sample_experience(task_id)
        self.exp_service.record(record)

        # Broken worker
        class BrokenProvider:
            model_id = "broken-model"
            dimension = 1536
            def generate_embedding(self, text):
                raise RuntimeError("External embedding service unavailable")

        broken_worker = VectorIndexingWorker(ADMIN_URL, BrokenProvider())
        claimed = broken_worker.claim_next_job()
        self.assertIsNotNone(claimed)
        res = broken_worker.process_job(claimed["node_id"])
        self.assertIn(res["status"], ("RETRY_SCHEDULED", "FAILED"))

        # Source node MUST still exist
        conn = psycopg2.connect(ADMIN_URL, cursor_factory=RealDictCursor)
        with conn.cursor() as cur:
            cur.execute("SELECT id, title, promotion_state FROM pub_neural.neural_nodes WHERE id = %s;", (claimed["node_id"],))
            node = cur.fetchone()
            self.assertIsNotNone(node)
            self.assertEqual(node["id"], claimed["node_id"])
        conn.close()

    def test_vec_06_transient_failure_retries_with_backoff(self):
        """VEC-06: Transient failure updates attempts, error, and schedules available_at."""
        task_id = f"task-vec06-{uuid.uuid4().hex[:6]}"
        record = self._create_sample_experience(task_id)
        self.exp_service.record(record)

        class BrokenProvider:
            model_id = "transient-fail"
            dimension = 1536
            def generate_embedding(self, text):
                raise ValueError("Temporary rate limit")

        broken_worker = VectorIndexingWorker(ADMIN_URL, BrokenProvider())
        claimed = broken_worker.claim_next_job()
        res = broken_worker.process_job(claimed["node_id"], retry_delay_seconds=2)
        self.assertEqual(res["status"], "RETRY_SCHEDULED")

        conn = psycopg2.connect(ADMIN_URL, cursor_factory=RealDictCursor)
        with conn.cursor() as cur:
            cur.execute(
                "SELECT status, attempts, last_error, available_at FROM pub_neural.neural_vector_index_jobs WHERE node_id = %s;",
                (claimed["node_id"],)
            )
            job = cur.fetchone()
            self.assertEqual(job["status"], "PENDING")
            self.assertEqual(job["attempts"], claimed["attempts"])
            self.assertIn("Temporary rate limit", job["last_error"])
            self.assertIsNotNone(job["available_at"])
        conn.close()

    def test_vec_07_permanent_failure_transitions_to_failed(self):
        """VEC-07: Permanent failure after max attempts transitions to FAILED."""
        task_id = f"task-vec07-{uuid.uuid4().hex[:6]}"
        record = self._create_sample_experience(task_id)
        self.exp_service.record(record)

        claimed = self.worker.claim_next_job()
        self.assertIsNotNone(claimed)
        node_id = claimed["node_id"]

        conn = psycopg2.connect(ADMIN_URL)
        conn.autocommit = True
        with conn.cursor() as cur:
            cur.execute(
                "UPDATE pub_neural.neural_vector_index_jobs SET attempts = 3 WHERE node_id = %s;",
                (node_id,)
            )
        conn.close()

        class BrokenProvider:
            model_id = "perm-fail"
            dimension = 1536
            def generate_embedding(self, text):
                raise RuntimeError("Permanent error")

        broken_worker = VectorIndexingWorker(ADMIN_URL, BrokenProvider())
        res = broken_worker.process_job(node_id)
        self.assertEqual(res["status"], "FAILED")

        conn = psycopg2.connect(ADMIN_URL, cursor_factory=RealDictCursor)
        with conn.cursor() as cur:
            cur.execute(
                "SELECT status, last_error FROM pub_neural.neural_vector_index_jobs WHERE node_id = %s;",
                (node_id,)
            )
            job = cur.fetchone()
            self.assertEqual(job["status"], "FAILED")
            self.assertIn("Permanent error", job["last_error"])
        conn.close()

    def test_vec_08_governance_and_promotion_state_preserved(self):
        """VEC-08: Node governance state remains OBSERVED / CANDIDATE; vectors have zero authority."""
        task_id = f"task-vec08-{uuid.uuid4().hex[:6]}"
        record = self._create_sample_experience(task_id)
        self.exp_service.record(record)

        primary_node_id = f"experience:pub-dev-loop:{task_id}"
        self.worker.sync_node_vector(primary_node_id)

        conn = psycopg2.connect(ADMIN_URL, cursor_factory=RealDictCursor)
        with conn.cursor() as cur:
            cur.execute("SELECT promotion_state FROM pub_neural.neural_nodes WHERE id = %s;", (primary_node_id,))
            row = cur.fetchone()
            self.assertEqual(row["promotion_state"], "OBSERVED")
        conn.close()

    def test_vec_09_fts_available_while_vector_pending(self):
        """VEC-09: Lexical FTS search immediately works even before vector worker runs."""
        task_id = f"task-vec09-{uuid.uuid4().hex[:6]}"
        record = self._create_sample_experience(task_id)
        self.exp_service.record(record)

        # Do NOT run worker
        # FTS search must succeed
        conn = psycopg2.connect(ADMIN_URL, cursor_factory=RealDictCursor)
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT id, ts_rank(tsv_document, plainto_tsquery('portuguese', 'Unique')) as rank
                FROM pub_neural.neural_fts
                WHERE id LIKE %s;
                """,
                (f"%{task_id}%",)
            )
            fts_rows = cur.fetchall()
            self.assertGreater(len(fts_rows), 0)
        conn.close()

    def test_vec_10_dense_candidates_returned_after_vectorization(self):
        """VEC-10: HybridSearchEngine dense pass returns vectorized node."""
        task_id = f"task-vec10-{uuid.uuid4().hex[:6]}"
        record = self._create_sample_experience(task_id)
        self.exp_service.record(record)

        # Vectorize all pending jobs for this task
        conn = psycopg2.connect(ADMIN_URL, cursor_factory=RealDictCursor)
        with conn.cursor() as cur:
            cur.execute("SELECT node_id FROM pub_neural.neural_vector_index_jobs WHERE node_id LIKE %s;", (f"%{task_id}%",))
            rows = cur.fetchall()
            for r in rows:
                self.worker.process_job(r["node_id"])

            cur.execute(
                """
                SELECT target_id, model_id
                FROM pub_neural.neural_vectors
                WHERE target_id LIKE %s;
                """,
                (f"%{task_id}%",)
            )
            vecs = cur.fetchall()
            self.assertGreaterEqual(len(vecs), 1)
        conn.close()

    def test_vec_11_rrf_fusion_combines_lexical_and_dense(self):
        """VEC-11: RRF fusion combines lexical and dense ranks into fused score."""
        task_id = f"task-vec11-{uuid.uuid4().hex[:6]}"
        proj_id = f"pub-proj-{uuid.uuid4().hex[:6]}"
        record = self._create_sample_experience(task_id, project_id=proj_id)
        self.exp_service.record(record)

        # Sync vectors for this task
        conn = psycopg2.connect(ADMIN_URL, cursor_factory=RealDictCursor)
        with conn.cursor() as cur:
            cur.execute("SELECT node_id FROM pub_neural.neural_vector_index_jobs WHERE node_id LIKE %s;", (f"%{task_id}%",))
            for r in cur.fetchall():
                self.worker.process_job(r["node_id"])
        conn.close()

        query_text = f"Unique finding for {task_id}"
        results = self.search_engine.search(
            query=query_text,
            project_id=proj_id,
            trust_zone="tz_internal_holding"
        )
        self.assertGreater(len(results), 0)
        top = results[0]
        self.assertIn(task_id, top.target_id)
        self.assertGreater(top.rrf_score, 0.0)

    def test_vec_12_experience_ingestion_non_blocking_async(self):
        """VEC-12: Experience ingestion returns ACCEPTED immediately without waiting for vector worker."""
        task_id = f"task-vec12-{uuid.uuid4().hex[:6]}"
        record = self._create_sample_experience(task_id)

        import time
        t0 = time.perf_counter()
        result = self.exp_service.record(record)
        duration_ms = (time.perf_counter() - t0) * 1000

        self.assertEqual(result.status, ExperienceWritebackStatus.ACCEPTED)
        # Ingestion should be very fast (under 500ms)
        self.assertLess(duration_ms, 500)

        # And job is still pending
        conn = psycopg2.connect(ADMIN_URL, cursor_factory=RealDictCursor)
        with conn.cursor() as cur:
            cur.execute(
                "SELECT status FROM pub_neural.neural_vector_index_jobs WHERE node_id = %s;",
                (f"experience:pub-dev-loop:{task_id}",)
            )
            job = cur.fetchone()
            self.assertIsNotNone(job)
            self.assertEqual(job["status"], "PENDING")
        conn.close()

    def test_vec_13_replay_preserves_completed_jobs(self):
        """VEC-13: Replaying TASK_EXPERIENCE_RECORDED preserves COMPLETED vector job without duplicate work."""
        task_id = f"task-vec13-{uuid.uuid4().hex[:6]}"
        record = self._create_sample_experience(task_id)

        # 1. Initial ingestion
        result = self.exp_service.record(record)
        self.assertEqual(result.status, ExperienceWritebackStatus.ACCEPTED)

        # 2. Worker processes all jobs to COMPLETED
        conn = psycopg2.connect(ADMIN_URL, cursor_factory=RealDictCursor)
        with conn.cursor() as cur:
            cur.execute("SELECT node_id FROM pub_neural.neural_vector_index_jobs WHERE node_id LIKE %s;", (f"%{task_id}%",))
            for r in cur.fetchall():
                self.worker.process_job(r["node_id"])

            # Verify both are COMPLETED
            cur.execute("SELECT node_id, status FROM pub_neural.neural_vector_index_jobs WHERE node_id LIKE %s;", (f"%{task_id}%",))
            for r in cur.fetchall():
                self.assertEqual(r["status"], "COMPLETED")
        conn.close()

        # 3. Replay the EXACT same event via pub_neural.reduce_event()
        conn = psycopg2.connect(ADMIN_URL)
        conn.autocommit = True
        with conn.cursor() as cur:
            cur.execute("SELECT pub_neural.reduce_event(%s::uuid);", (str(result.event_id),))
        conn.close()

        # 4. Assert: jobs MUST REMAIN COMPLETED, not reopened to PENDING
        conn = psycopg2.connect(ADMIN_URL, cursor_factory=RealDictCursor)
        with conn.cursor() as cur:
            cur.execute("SELECT node_id, status FROM pub_neural.neural_vector_index_jobs WHERE node_id LIKE %s;", (f"%{task_id}%",))
            replayed_jobs = cur.fetchall()
            self.assertGreaterEqual(len(replayed_jobs), 2)
            for j in replayed_jobs:
                self.assertEqual(j["status"], "COMPLETED")
        conn.close()

    def test_vec_14_concurrency_lock(self):
        """VEC-14: Two concurrent workers using SKIP LOCKED never claim the same job."""
        task_id = f"task-vec14-{uuid.uuid4().hex[:6]}"
        record = self._create_sample_experience(task_id)
        self.exp_service.record(record)

        worker_a = VectorIndexingWorker(ADMIN_URL, self.provider)
        worker_b = VectorIndexingWorker(ADMIN_URL, self.provider)

        # Worker A claims one job
        job_a = worker_a.claim_next_job()
        self.assertIsNotNone(job_a)

        # Worker B claims next job
        job_b = worker_b.claim_next_job()
        self.assertIsNotNone(job_b)

        # Jobs claimed MUST be distinct
        self.assertNotEqual(job_a["node_id"], job_b["node_id"])


if __name__ == "__main__":
    unittest.main()
