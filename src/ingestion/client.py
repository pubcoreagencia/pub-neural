import hashlib
import json
import uuid
from typing import Any, Dict, List, Optional
import psycopg2
from psycopg2.extras import RealDictCursor


class PubNeuralClient:
    """Client for interacting with PUB Neural database via controlled append_event and session attachment."""

    def __init__(
        self,
        db_url: str,
        actor_id: str,
        machine_secret: str,
        requested_trust_zone: str = "tz_internal_holding",
        requested_project: Optional[str] = None,
        db_user: str = "pub_neural_app"
    ):
        self.db_url = db_url
        self.actor_id = actor_id
        self.machine_secret = machine_secret
        self.requested_trust_zone = requested_trust_zone
        self.requested_project = requested_project
        self.db_user = db_user
        self.bearer_token: Optional[str] = None
        self._conn = None

    def connect(self):
        """Establish database connection."""
        self._conn = psycopg2.connect(self.db_url, cursor_factory=RealDictCursor)
        self._conn.autocommit = False

    def close(self):
        if self._conn and not self._conn.closed:
            self._conn.close()

    def establish_session(self) -> str:
        """Call pub_neural.establish_session_context to obtain opaque 256-bit bearer token."""
        if not self._conn or self._conn.closed:
            self.connect()

        with self._conn.cursor() as cur:
            cur.execute(
                """
                SELECT pub_neural.establish_session_context(
                    %s, %s, %s, %s
                ) AS token;
                """,
                (self.actor_id, self.machine_secret, self.requested_trust_zone, self.requested_project)
            )
            res = cur.fetchone()
            self.bearer_token = res["token"]
            self._conn.commit()
            return self.bearer_token

    def attach_current_session(self, cur):
        """Attach bearer token to the current transaction."""
        if not self.bearer_token:
            self.establish_session()

        cur.execute("SELECT pub_neural.attach_session(%s) AS attached;", (self.bearer_token,))
        res = cur.fetchone()
        if not res or not res["attached"]:
            raise PermissionError(f"Session attachment failed for actor {self.actor_id}")

    def append_canonical_event(
        self,
        event_id: uuid.UUID,
        event_type: str,
        stream_id: str,
        stream_version: Optional[int] = None,
        payload: Dict[str, Any] = None,
        parent_event_ids: Optional[List[uuid.UUID]] = None,
        producer_version: str = "v1.0.0",
        signature: Optional[str] = None
    ) -> int:
        """Append an event via pub_neural.append_event with attached bearer session."""
        if not self._conn or self._conn.closed:
            self.connect()

        if parent_event_ids is None:
            parent_event_ids = []
        if payload is None:
            payload = {}

        with self._conn.cursor() as cur:
            # 1. Attach session for this transaction
            self.attach_current_session(cur)

            # Auto-resolve stream_version if None or <= 0
            if stream_version is None or stream_version <= 0:
                cur.execute(
                    "SELECT COALESCE(MAX(stream_version), 0) + 1 AS next_ver FROM pub_neural.neural_events WHERE stream_id = %s;",
                    (stream_id,)
                )
                stream_version = cur.fetchone()["next_ver"]

            try:
                cur.execute(
                    """
                    SELECT pub_neural.append_event(
                        p_event_id := %s::UUID,
                        p_event_type := %s::VARCHAR,
                        p_stream_id := %s::VARCHAR,
                        p_stream_version := %s::BIGINT,
                        p_producer_version := %s::VARCHAR,
                        p_payload := %s::JSONB,
                        p_parent_event_ids := %s::UUID[],
                        p_signature := %s::TEXT
                    ) AS global_sequence;
                    """,
                    (
                        str(event_id),
                        event_type,
                        stream_id,
                        stream_version,
                        producer_version,
                        json.dumps(payload),
                        [str(pid) for pid in parent_event_ids],
                        signature
                    )
                )
                res = cur.fetchone()
                seq = res["global_sequence"]
                self._conn.commit()
                return seq
            except Exception:
                self._conn.rollback()
                raise

    def register_verified_blob(
        self,
        file_sha256: str,
        content_hash: str,
        storage_uri: str,
        byte_size: int,
        mime_type: str,
        originating_event_id: uuid.UUID,
        storage_backend: str = "LOCAL_DISK"
    ):
        """Call pub_neural.register_verified_blob."""
        if not self._conn or self._conn.closed:
            self.connect()

        with self._conn.cursor() as cur:
            self.attach_current_session(cur)
            cur.execute(
                """
                SELECT pub_neural.register_verified_blob(
                    p_file_sha256 := %s,
                    p_content_hash := %s,
                    p_storage_uri := %s,
                    p_storage_backend := %s,
                    p_byte_size := %s,
                    p_mime_type := %s,
                    p_event_id := %s
                );
                """,
                (
                    file_sha256,
                    content_hash,
                    storage_uri,
                    storage_backend,
                    byte_size,
                    mime_type,
                    str(originating_event_id)
                )
            )
            self._conn.commit()

    def _normalize_idempotency_key(self, idempotency_key: str) -> str:
        if len(idempotency_key) > 120:
            prefix = idempotency_key[:56]
            h = hashlib.sha256(idempotency_key.encode("utf-8")).hexdigest()
            return f"{prefix}:{h}"[:128]
        return idempotency_key

    def check_idempotency(self, idempotency_key: str) -> Optional[Dict[str, Any]]:
        """Check pub_neural.neural_idempotency_records for an existing record."""
        if not self._conn or self._conn.closed:
            self.connect()

        key = self._normalize_idempotency_key(idempotency_key)
        with self._conn.cursor() as cur:
            cur.execute(
                """
                SELECT idempotency_key, actor_id, request_hash, resulting_event_id, response_payload, created_at, expires_at
                FROM pub_neural.neural_idempotency_records
                WHERE idempotency_key = %s;
                """,
                (key,)
            )
            res = cur.fetchone()
            if res:
                return dict(res)
            return None

    def record_idempotency(
        self,
        idempotency_key: str,
        request_hash: str,
        resulting_event_id: uuid.UUID,
        response_payload: Dict[str, Any],
        ttl_days: int = 30
    ):
        """Record processed result in pub_neural.neural_idempotency_records."""
        if not self._conn or self._conn.closed:
            self.connect()

        key = self._normalize_idempotency_key(idempotency_key)
        with self._conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO pub_neural.neural_idempotency_records (
                    idempotency_key,
                    actor_id,
                    request_hash,
                    resulting_event_id,
                    response_payload,
                    created_at,
                    expires_at
                ) VALUES (
                    %s,
                    %s,
                    %s,
                    %s,
                    %s,
                    CURRENT_TIMESTAMP,
                    CURRENT_TIMESTAMP + (%s || ' days')::interval
                ) ON CONFLICT (idempotency_key) DO UPDATE SET
                    response_payload = EXCLUDED.response_payload;
                """,
                (
                    key,
                    self.actor_id,
                    request_hash,
                    str(resulting_event_id),
                    json.dumps(response_payload),
                    str(ttl_days)
                )
            )
            self._conn.commit()

    def get_event_by_id(self, event_id: uuid.UUID) -> Optional[Dict[str, Any]]:
        """Fetch canonical event by id."""
        if not self._conn or self._conn.closed:
            self.connect()

        with self._conn.cursor() as cur:
            cur.execute(
                """
                SELECT id, event_type, global_sequence, stream_id, stream_version, payload, recorded_at
                FROM pub_neural.neural_events
                WHERE id = %s;
                """,
                (str(event_id),)
            )
            res = cur.fetchone()
            if res:
                return dict(res)
            return None
