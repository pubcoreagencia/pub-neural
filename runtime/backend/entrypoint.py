"""
Standalone executable entrypoint for the PUB Neural Operational Runtime API server.
Spins up the real HTTP server connected to PostgreSQL and HybridSearchEngine.
Used for Level 3 Cross-Process Operational Runtime proof and production operation.
"""

import json
import logging
import os
import signal
import sys
import uuid
from typing import Any, Dict, List, Optional

# Ensure repository root is in sys.path
_CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
_REPO_ROOT = os.path.dirname(os.path.dirname(_CURRENT_DIR))
_SRC_DIR = os.path.join(_REPO_ROOT, "src")
for p in (_REPO_ROOT, _SRC_DIR):
    if p not in sys.path:
        sys.path.insert(0, p)

import psycopg2
from runtime.backend.config import RuntimeConfig
from runtime.backend.server import create_runtime_server
from src.gate.experience_service import ExperienceSink, NeuralExperienceService
from src.gate.retrieval_adapter import HybridSearchAdapter, NeuralResultMapper
from src.gate.service import NeuralQueryService
from src.retrieval.embedding_model import MockDeterministicEmbeddingProvider
from src.retrieval.hybrid_search import HybridSearchEngine

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] [NeuralRuntime] %(message)s",
)
logger = logging.getLogger("neural.runtime")


class PostgresExperienceSink(ExperienceSink):
    """
    Durable PostgreSQL-backed ExperienceSink for real cross-process persistence.
    Appends canonical events to pub_neural.neural_events, triggers pub_neural.reduce_event()
    to project into neural_nodes and neural_fts, and manages idempotency records.
    """

    def __init__(self, db_url: str):
        self.db_url = db_url

    def _get_conn(self):
        conn = psycopg2.connect(self.db_url)
        conn.autocommit = False
        return conn

    def is_canonical_project(self, project_id: str) -> bool:
        """Validate project against the canonical holding project catalog."""
        with self._get_conn() as conn:
            with conn.cursor() as cur:
                cur.execute("SET SESSION AUTHORIZATION pub_neural_ceo;")
                cur.execute(
                    """
                    SELECT 1
                    FROM pub_neural.holding_projects
                    WHERE id = %s
                      AND is_active = TRUE
                      AND is_archived = FALSE
                    LIMIT 1;
                    """,
                    (project_id,),
                )
                return cur.fetchone() is not None

    def check_idempotency(self, idempotency_key: str) -> Optional[Dict[str, Any]]:
        with self._get_conn() as conn:
            with conn.cursor() as cur:
                cur.execute("SET SESSION AUTHORIZATION pub_neural_ceo;")
                cur.execute(
                    """
                    SELECT idempotency_key, request_hash, resulting_event_id, response_payload, created_at
                    FROM pub_neural.neural_idempotency_records
                    WHERE idempotency_key = %s AND (expires_at IS NULL OR expires_at > CURRENT_TIMESTAMP);
                    """,
                    (idempotency_key,),
                )
                row = cur.fetchone()
                if not row:
                    return None
                return {
                    "idempotency_key": row[0],
                    "request_hash": row[1],
                    "resulting_event_id": str(row[2]),
                    "response_payload": row[3],
                    "created_at": row[4].isoformat() if hasattr(row[4], "isoformat") else str(row[4]),
                }

    def record_idempotency(
        self,
        idempotency_key: str,
        request_hash: str,
        resulting_event_id: uuid.UUID,
        response_payload: Dict[str, Any],
        ttl_days: int = 30,
    ) -> None:
        with self._get_conn() as conn:
            with conn.cursor() as cur:
                cur.execute("SET SESSION AUTHORIZATION pub_neural_ceo;")
                cur.execute(
                    """
                    INSERT INTO pub_neural.neural_idempotency_records (
                        idempotency_key, actor_id, request_hash, resulting_event_id, response_payload, created_at, expires_at
                    ) VALUES (
                        %s, %s, %s, %s::uuid, %s::jsonb, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP + (%s || ' days')::interval
                    ) ON CONFLICT (idempotency_key) DO UPDATE SET
                        response_payload = EXCLUDED.response_payload,
                        expires_at = EXCLUDED.expires_at;
                    """,
                    (
                        idempotency_key,
                        "pdl:executor",
                        request_hash,
                        str(resulting_event_id),
                        json.dumps(response_payload),
                        ttl_days,
                    ),
                )
                conn.commit()

    def append_idempotent_event(
        self, idempotency_key: str, request_hash: str, event_id: uuid.UUID,
        event_type: str, stream_id: str, payload: Dict[str, Any],
        producer_version: str = "v1.0.0", response_payload: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        with self._get_conn() as conn:
            with conn.cursor() as cur:
                cur.execute("SET SESSION AUTHORIZATION pub_neural_ceo;")
                cur.execute("""
                    INSERT INTO pub_neural.neural_idempotency_records
                        (idempotency_key, actor_id, request_hash, resulting_event_id, response_payload, created_at, expires_at)
                    VALUES (%s, %s, %s, %s::uuid, %s::jsonb, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP + INTERVAL '30 days')
                    ON CONFLICT (idempotency_key) DO NOTHING
                    RETURNING idempotency_key;
                """, (idempotency_key, "pdl:executor", request_hash, str(event_id), json.dumps(response_payload or {})))
                claimed = cur.fetchone()
                if not claimed:
                    cur.execute("SELECT idempotency_key, resulting_event_id, response_payload, created_at FROM pub_neural.neural_idempotency_records WHERE idempotency_key = %s;", (idempotency_key,))
                    row = cur.fetchone()
                    conn.commit()
                    if not row: raise RuntimeError("Idempotency conflict row disappeared")
                    return {"duplicate": True, "idempotency_key": row[0], "resulting_event_id": str(row[1]), "response_payload": row[2], "created_at": row[3].isoformat()}
                cur.execute("""
                    SELECT pub_neural.append_event(%s::uuid, %s, %s, %s, %s, %s::jsonb);
                """, (str(event_id), event_type, stream_id, 1, producer_version, json.dumps(payload)))
                seq = cur.fetchone()[0]
                cur.execute("SELECT pub_neural.reduce_event(e) FROM pub_neural.neural_events e WHERE id = %s::uuid;", (str(event_id),))
                cur.fetchone()
                cur.execute("""UPDATE pub_neural.neural_idempotency_records SET response_payload = %s::jsonb WHERE idempotency_key = %s;""", (json.dumps(response_payload or {}), idempotency_key))
                conn.commit()
                return {"duplicate": False, "global_sequence": seq, "idempotency_key": idempotency_key, "resulting_event_id": str(event_id)}

    def append_canonical_event(        self,
        event_id: uuid.UUID,
        event_type: str,
        stream_id: str,
        stream_version: Optional[int] = None,
        payload: Optional[Dict[str, Any]] = None,
        parent_event_ids: Optional[List[uuid.UUID]] = None,
        producer_version: str = "v1.0.0",
        signature: Optional[str] = None,
    ) -> int:
        with self._get_conn() as conn:
            with conn.cursor() as cur:
                cur.execute("SET SESSION AUTHORIZATION pub_neural_ceo;")
                cur.execute(
                    """
                    SELECT pub_neural.append_event(
                        %s::uuid,
                        %s,
                        %s,
                        %s,
                        %s,
                        %s::jsonb
                    );
                    """,
                    (
                        str(event_id),
                        event_type,
                        stream_id,
                        stream_version or 1,
                        producer_version,
                        json.dumps(payload or {}),
                    ),
                )
                seq = cur.fetchone()[0]

                # Immediately trigger projector reduction to maintain real-time node & FTS sync
                cur.execute(
                    """
                    SELECT pub_neural.reduce_event(e)
                    FROM pub_neural.neural_events e
                    WHERE id = %s::uuid;
                    """,
                    (str(event_id),),
                )
                reduction_res = cur.fetchone()[0]
                logger.info(
                    "Event %s appended (seq=%d). Projector reduction: %s",
                    str(event_id),
                    seq,
                    reduction_res,
                )
                conn.commit()
                return seq


def run_runtime_server():
    cfg = RuntimeConfig.from_environment()
    logger.info("Initializing PUB Neural Operational Runtime API server...")
    logger.info("Configuration: host=%s, port=%s, enforce_auth=%s", cfg.host, cfg.port, cfg.enforce_auth)

    # 1. Instantiate PostgreSQL Sink and Experience Service
    logger.info("Connecting ExperienceSink to PostgreSQL at %s", cfg.db_url)
    exp_sink = PostgresExperienceSink(db_url=cfg.db_url)
    exp_service = NeuralExperienceService(sink=exp_sink, project_catalog=exp_sink)

    # 2. Instantiate HybridSearchEngine and Query Service
    logger.info("Initializing HybridSearchEngine and NeuralQueryService...")
    embed_provider = MockDeterministicEmbeddingProvider()
    search_engine = HybridSearchEngine(db_url=cfg.db_url, embedding_provider=embed_provider)
    retrieval_adapter = HybridSearchAdapter(search_engine)
    result_mapper = NeuralResultMapper()
    query_service = NeuralQueryService(retrieval_engine=retrieval_adapter, result_mapper=result_mapper)

    # 3. Create HTTP Server
    server = create_runtime_server(
        config=cfg,
        query_service=query_service,
        experience_service=exp_service,
    )

    def shutdown_handler(signum, frame):
        logger.info("Received signal %d, shutting down HTTP server...", signum)
        server.server_close()
        sys.exit(0)

    signal.signal(signal.SIGINT, shutdown_handler)
    signal.signal(signal.SIGTERM, shutdown_handler)

    logger.info("PUB Neural Operational Runtime API listening at http://%s:%s", cfg.host, cfg.port)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        logger.info("Shutting down HTTP server cleanly...")
        server.server_close()


if __name__ == "__main__":
    run_runtime_server()
