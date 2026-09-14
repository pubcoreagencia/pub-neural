import hashlib
import uuid
from typing import Any, Dict, List, Optional
import psycopg2
from psycopg2.extras import RealDictCursor, register_uuid

from .embedding_model import EmbeddingModelProvider


# Register UUID adapter for psycopg2
register_uuid()

# Fixed namespace for deterministic UUIDv5 generation matching Schema V0 contract
PUB_NEURAL_VECTOR_NS = uuid.UUID("0191e4f0-0000-7000-8000-000000000000")


def compute_content_hash(text: str) -> str:
    """Deterministic SHA-256 content hash."""
    return hashlib.sha256(text.strip().encode("utf-8")).hexdigest()


def compute_vector_id(target_type: str, target_id: str, model_id: str) -> uuid.UUID:
    """
    Compute deterministic UUIDv5 for vector entity.
    Contract: target_type + ":" + target_id + ":" + model_id
    """
    key = f"{target_type}:{target_id}:{model_id}"
    return uuid.uuid5(PUB_NEURAL_VECTOR_NS, key)


class VectorIndexingWorker:
    """
    Worker for populating and maintaining pub_neural.neural_vectors.
    Consumes projected neural_nodes and neural_evidence entities.
    Enforces:
      - Content-addressable embedding identity (target_type + target_id + model_id).
      - Semantic idempotency: duplicate runs produce identical vector state without churn.
      - Staleness detection: checks content_hash against projection text; regenerates on drift.
      - Dual model coexistence: allows multiple models (e.g. v1, v2) for the same target entity.
      - Non-destructive rebuildability: vectors can be deleted and 100% regenerated from source nodes/evidence.
    """

    def __init__(self, db_url: str, embedding_provider: EmbeddingModelProvider):
        self.db_url = db_url
        self.provider = embedding_provider
        self._conn = None

    def _get_connection(self):
        if not self._conn or self._conn.closed:
            self._conn = psycopg2.connect(self.db_url, cursor_factory=RealDictCursor)
            self._conn.autocommit = False
        return self._conn

    def close(self):
        if self._conn and not self._conn.closed:
            self._conn.close()

    def sync_node_vector(self, node_id: str) -> Optional[Dict[str, Any]]:
        """
        Derive vector for a node from neural_nodes.
        Text source: title + '\n' + (summary or '') + '\n' + (content or '')
        """
        conn = self._get_connection()
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT id, title, summary, content, trust_zone, project_id, originating_event_id
                FROM pub_neural.neural_nodes
                WHERE id = %s AND is_active = TRUE;
                """,
                (node_id,)
            )
            node = cur.fetchone()
            if not node:
                conn.rollback()
                return None

            text = f"{node['title']}\n{node['summary'] or ''}\n{node['content'] or ''}".strip()
            current_hash = compute_content_hash(text)
            vector_id = compute_vector_id("NODE", node_id, self.provider.model_id)

            # Check existing vector
            cur.execute(
                """
                SELECT id, content_hash, originating_event_id
                FROM pub_neural.neural_vectors
                WHERE target_type = 'NODE' AND target_id = %s AND model_id = %s;
                """,
                (node_id, self.provider.model_id)
            )
            existing = cur.fetchone()

            if existing:
                if existing["content_hash"] == current_hash:
                    # Already up to date, idempotent no-op
                    conn.rollback()
                    return {
                        "action": "SKIPPED_UP_TO_DATE",
                        "vector_id": str(existing["id"]),
                        "target_type": "NODE",
                        "target_id": node_id,
                        "model_id": self.provider.model_id,
                        "content_hash": current_hash
                    }
                else:
                    # Stale vector detected: update vector embedding and content_hash
                    embedding = self.provider.generate_embedding(text)
                    cur.execute(
                        """
                        UPDATE pub_neural.neural_vectors
                        SET embedding = %s::vector(1536),
                            content_hash = %s,
                            originating_event_id = %s::uuid,
                            trust_zone = %s,
                            project_id = %s,
                            created_at = CURRENT_TIMESTAMP
                        WHERE id = %s::uuid;
                        """,
                        (
                            embedding,
                            current_hash,
                            str(node["originating_event_id"]),
                            node["trust_zone"],
                            node["project_id"],
                            str(vector_id)
                        )
                    )
                    conn.commit()
                    return {
                        "action": "REGENERATED_STALE",
                        "vector_id": str(vector_id),
                        "target_type": "NODE",
                        "target_id": node_id,
                        "model_id": self.provider.model_id,
                        "content_hash": current_hash
                    }
            else:
                # Insert new vector
                embedding = self.provider.generate_embedding(text)
                cur.execute(
                    """
                    INSERT INTO pub_neural.neural_vectors (
                        id, target_type, target_id, trust_zone, project_id, model_id,
                        embedding, content_hash, originating_event_id, created_at
                    ) VALUES (
                        %s::uuid, 'NODE', %s, %s, %s, %s, %s::vector(1536), %s, %s::uuid, CURRENT_TIMESTAMP
                    )
                    ON CONFLICT (target_type, target_id, model_id) DO UPDATE SET
                        embedding = EXCLUDED.embedding,
                        content_hash = EXCLUDED.content_hash,
                        originating_event_id = EXCLUDED.originating_event_id,
                        trust_zone = EXCLUDED.trust_zone,
                        project_id = EXCLUDED.project_id,
                        created_at = CURRENT_TIMESTAMP;
                    """,
                    (
                        str(vector_id),
                        node_id,
                        node["trust_zone"],
                        node["project_id"],
                        self.provider.model_id,
                        embedding,
                        current_hash,
                        str(node["originating_event_id"])
                    )
                )
                conn.commit()
                return {
                    "action": "CREATED",
                    "vector_id": str(vector_id),
                    "target_type": "NODE",
                    "target_id": node_id,
                    "model_id": self.provider.model_id,
                    "content_hash": current_hash
                }

    def sync_evidence_vector(self, evidence_id: str) -> Optional[Dict[str, Any]]:
        """
        Derive vector for an evidence entity from neural_evidence.
        Text source: exact_quote + '\n' + (context_before or '') + '\n' + (context_after or '')
        """
        conn = self._get_connection()
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT id, exact_quote, context_before, context_after, trust_zone, project_id, originating_event_id
                FROM pub_neural.neural_evidence
                WHERE id = %s::uuid;
                """,
                (evidence_id,)
            )
            ev = cur.fetchone()
            if not ev:
                conn.rollback()
                return None

            text = f"{ev['exact_quote']}\n{ev['context_before'] or ''}\n{ev['context_after'] or ''}".strip()
            current_hash = compute_content_hash(text)
            vector_id = compute_vector_id("EVIDENCE", evidence_id, self.provider.model_id)

            cur.execute(
                """
                SELECT id, content_hash, originating_event_id
                FROM pub_neural.neural_vectors
                WHERE target_type = 'EVIDENCE' AND target_id = %s AND model_id = %s;
                """,
                (evidence_id, self.provider.model_id)
            )
            existing = cur.fetchone()

            if existing:
                if existing["content_hash"] == current_hash:
                    conn.rollback()
                    return {
                        "action": "SKIPPED_UP_TO_DATE",
                        "vector_id": str(existing["id"]),
                        "target_type": "EVIDENCE",
                        "target_id": evidence_id,
                        "model_id": self.provider.model_id,
                        "content_hash": current_hash
                    }
                else:
                    embedding = self.provider.generate_embedding(text)
                    cur.execute(
                        """
                        UPDATE pub_neural.neural_vectors
                        SET embedding = %s::vector(1536),
                            content_hash = %s,
                            originating_event_id = %s::uuid,
                            trust_zone = %s,
                            project_id = %s,
                            created_at = CURRENT_TIMESTAMP
                        WHERE id = %s::uuid;
                        """,
                        (
                            embedding,
                            current_hash,
                            str(ev["originating_event_id"]),
                            ev["trust_zone"],
                            ev["project_id"],
                            str(vector_id)
                        )
                    )
                    conn.commit()
                    return {
                        "action": "REGENERATED_STALE",
                        "vector_id": str(vector_id),
                        "target_type": "EVIDENCE",
                        "target_id": evidence_id,
                        "model_id": self.provider.model_id,
                        "content_hash": current_hash
                    }
            else:
                embedding = self.provider.generate_embedding(text)
                cur.execute(
                    """
                    INSERT INTO pub_neural.neural_vectors (
                        id, target_type, target_id, trust_zone, project_id, model_id,
                        embedding, content_hash, originating_event_id, created_at
                    ) VALUES (
                        %s::uuid, 'EVIDENCE', %s, %s, %s, %s, %s::vector(1536), %s, %s::uuid, CURRENT_TIMESTAMP
                    )
                    ON CONFLICT (target_type, target_id, model_id) DO UPDATE SET
                        embedding = EXCLUDED.embedding,
                        content_hash = EXCLUDED.content_hash,
                        originating_event_id = EXCLUDED.originating_event_id,
                        trust_zone = EXCLUDED.trust_zone,
                        project_id = EXCLUDED.project_id,
                        created_at = CURRENT_TIMESTAMP;
                    """,
                    (
                        str(vector_id),
                        evidence_id,
                        ev["trust_zone"],
                        ev["project_id"],
                        self.provider.model_id,
                        embedding,
                        current_hash,
                        str(ev["originating_event_id"])
                    )
                )
                conn.commit()
                return {
                    "action": "CREATED",
                    "vector_id": str(vector_id),
                    "target_type": "EVIDENCE",
                    "target_id": evidence_id,
                    "model_id": self.provider.model_id,
                    "content_hash": current_hash
                }

    def sync_all_projections(self) -> Dict[str, int]:
        """
        Sync all active nodes and evidence into neural_vectors.
        """
        conn = self._get_connection()
        stats = {"nodes_processed": 0, "evidence_processed": 0}
        with conn.cursor() as cur:
            cur.execute("SELECT id FROM pub_neural.neural_nodes WHERE is_active = TRUE ORDER BY id;")
            node_ids = [r["id"] for r in cur.fetchall()]

            cur.execute("SELECT id::text FROM pub_neural.neural_evidence ORDER BY id;")
            evidence_ids = [r["id"] for r in cur.fetchall()]

        for nid in node_ids:
            res = self.sync_node_vector(nid)
            if res:
                stats["nodes_processed"] += 1

        for eid in evidence_ids:
            res = self.sync_evidence_vector(eid)
            if res:
                stats["evidence_processed"] += 1

        return stats

    def claim_next_job(self) -> Optional[Dict[str, Any]]:
        """
        Claim the next pending or retryable vector index job using SELECT ... FOR UPDATE SKIP LOCKED.
        Transitions job state to 'PROCESSING' with locked_at timestamp.
        Returns job row dict or None if queue is empty.
        """
        conn = self._get_connection()
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT node_id, target_type, status, attempts, max_attempts
                FROM pub_neural.neural_vector_index_jobs
                WHERE status = 'PENDING'
                  AND available_at <= CURRENT_TIMESTAMP
                ORDER BY available_at ASC, node_id ASC
                FOR UPDATE SKIP LOCKED
                LIMIT 1;
                """
            )
            job = cur.fetchone()
            if not job:
                conn.rollback()
                return None

            cur.execute(
                """
                UPDATE pub_neural.neural_vector_index_jobs
                SET status = 'PROCESSING',
                    locked_at = CURRENT_TIMESTAMP,
                    attempts = attempts + 1,
                    updated_at = CURRENT_TIMESTAMP
                WHERE node_id = %s;
                """,
                (job["node_id"],)
            )
            conn.commit()
            job["status"] = "PROCESSING"
            job["attempts"] = job["attempts"] + 1
            return job

    def process_job(self, node_id: str, retry_delay_seconds: int = 5) -> Dict[str, Any]:
        """
        Process a single claimed vector job for node_id:
        1. Invokes sync_node_vector(node_id).
        2. On success: marks job COMPLETED, completed_at = CURRENT_TIMESTAMP.
        3. On transient error: increments attempts, schedules available_at with backoff.
           If attempts >= max_attempts, marks status FAILED.
        Preserves source knowledge node intact under all outcomes.
        """
        conn = self._get_connection()
        try:
            res = self.sync_node_vector(node_id)
            with conn.cursor() as cur:
                cur.execute(
                    """
                    UPDATE pub_neural.neural_vector_index_jobs
                    SET status = 'COMPLETED',
                        completed_at = CURRENT_TIMESTAMP,
                        last_error = NULL,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE node_id = %s;
                    """,
                    (node_id,)
                )
                conn.commit()
            return {"status": "COMPLETED", "node_id": node_id, "detail": res}
        except Exception as e:
            err_msg = str(e)
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT attempts, max_attempts
                    FROM pub_neural.neural_vector_index_jobs
                    WHERE node_id = %s;
                    """,
                    (node_id,)
                )
                row = cur.fetchone()
                attempts = row["attempts"] if row else 1
                max_attempts = row["max_attempts"] if row else 3

                if attempts >= max_attempts:
                    cur.execute(
                        """
                        UPDATE pub_neural.neural_vector_index_jobs
                        SET status = 'FAILED',
                            last_error = %s,
                            updated_at = CURRENT_TIMESTAMP
                        WHERE node_id = %s;
                        """,
                        (err_msg, node_id)
                    )
                else:
                    delay = retry_delay_seconds * (2 ** (attempts - 1))
                    cur.execute(
                        """
                        UPDATE pub_neural.neural_vector_index_jobs
                        SET status = 'PENDING',
                            available_at = CURRENT_TIMESTAMP + (%s || ' seconds')::interval,
                            last_error = %s,
                            updated_at = CURRENT_TIMESTAMP
                        WHERE node_id = %s;
                        """,
                        (delay, err_msg, node_id)
                    )
                conn.commit()
            return {"status": "FAILED" if attempts >= max_attempts else "RETRY_SCHEDULED", "node_id": node_id, "error": err_msg}

    def process_pending_jobs(self, max_batch: int = 50) -> Dict[str, int]:
        """
        Drain pending vector indexing jobs up to max_batch.
        Safe for concurrent invocation across multiple worker processes.
        """
        stats = {"claimed": 0, "completed": 0, "failed": 0, "retried": 0}
        for _ in range(max_batch):
            job = self.claim_next_job()
            if not job:
                break
            stats["claimed"] += 1
            result = self.process_job(job["node_id"])
            if result["status"] == "COMPLETED":
                stats["completed"] += 1
            elif result["status"] == "FAILED":
                stats["failed"] += 1
            else:
                stats["retried"] += 1
        return stats

