"""
Timeline and event lineage service for PUB Neural Console V0.
Queries canonical event ledger and causal DAG links.
Ensures sensitive secrets and credentials inside event payloads are sanitized.
"""

from typing import Any, Dict, List, Optional
from console.backend.models import (
    EventDetailDTO,
    EventItemDTO,
    EventListResponseDTO,
    serialize_val,
)

SENSITIVE_KEYS = {
    "machine_secret", "secret", "password", "token", "bearer_token",
    "session_token_hash", "private_key", "credential_identity"
}


def sanitize_payload(obj: Any) -> Any:
    """Recursively redact sensitive credentials in event payloads."""
    if isinstance(obj, dict):
        sanitized = {}
        for k, v in obj.items():
            if k.lower() in SENSITIVE_KEYS:
                sanitized[k] = "[REDACTED]"
            else:
                sanitized[k] = sanitize_payload(v)
        return sanitized
    elif isinstance(obj, list):
        return [sanitize_payload(item) for item in obj]
    return obj


def get_events_list(
    cur,
    limit: int = 50,
    offset: int = 0,
    stream_id: Optional[str] = None,
    event_type: Optional[str] = None,
) -> EventListResponseDTO:
    """Fetch paginated event list ordered by global sequence descending."""
    bounded_limit = max(1, min(limit, 200))
    bounded_offset = max(0, offset)

    sql = """
        SELECT 
            id, global_sequence, event_type, event_version, producer_version,
            stream_id, stream_version, actor_id, actor_role, recorded_at
        FROM pub_neural.neural_events
    """
    conditions = []
    params: List[Any] = []

    if stream_id:
        conditions.append("stream_id = %s")
        params.append(stream_id)
    if event_type:
        conditions.append("event_type = %s")
        params.append(event_type)

    if conditions:
        sql += " WHERE " + " AND ".join(conditions)

    sql += " ORDER BY global_sequence DESC LIMIT %s OFFSET %s;"
    params.extend([bounded_limit, bounded_offset])

    cur.execute(sql, tuple(params))
    rows = cur.fetchall()

    events = [
        EventItemDTO(
            id=str(r["id"]),
            global_sequence=int(r["global_sequence"]),
            event_type=str(r["event_type"]),
            event_version=int(r["event_version"]),
            producer_version=str(r["producer_version"]),
            stream_id=str(r["stream_id"]),
            stream_version=int(r["stream_version"]),
            actor_id=str(r["actor_id"]),
            actor_role=str(r["actor_role"]),
            recorded_at=serialize_val(r["recorded_at"]),
        )
        for r in rows
    ]

    return EventListResponseDTO(
        events=events,
        total_returned=len(events),
        limit=bounded_limit,
        offset=bounded_offset,
    )


def get_event_detail(cur, event_id: str) -> Optional[EventDetailDTO]:
    """Fetch single event with causal parent IDs and sanitized payload."""
    sql = """
        SELECT 
            id, global_sequence, event_type, event_version, payload_schema_version,
            producer_version, stream_id, stream_version, actor_id, actor_role,
            payload, signature, recorded_at
        FROM pub_neural.neural_events
        WHERE id = %s;
    """
    cur.execute(sql, (event_id,))
    row = cur.fetchone()
    if not row:
        return None

    # Fetch causal DAG parent event IDs
    parents_sql = """
        SELECT parent_event_id 
        FROM pub_neural.neural_event_parents 
        WHERE event_id = %s
        ORDER BY created_at ASC;
    """
    cur.execute(parents_sql, (event_id,))
    parent_rows = cur.fetchall()
    parent_ids = [str(pr["parent_event_id"]) for pr in parent_rows]

    return EventDetailDTO(
        id=str(row["id"]),
        global_sequence=int(row["global_sequence"]),
        event_type=str(row["event_type"]),
        event_version=int(row["event_version"]),
        payload_schema_version=int(row["payload_schema_version"]),
        producer_version=str(row["producer_version"]),
        stream_id=str(row["stream_id"]),
        stream_version=int(row["stream_version"]),
        actor_id=str(row["actor_id"]),
        actor_role=str(row["actor_role"]),
        payload=sanitize_payload(row["payload"]),
        signature=row.get("signature"),
        recorded_at=serialize_val(row["recorded_at"]),
        parent_event_ids=parent_ids,
    )
