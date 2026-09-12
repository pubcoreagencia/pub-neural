import hashlib
import uuid
from typing import Dict, Any, Optional
from src.ingestion.client import PubNeuralClient


class EvidenceCapturerWorker:
    """Captures grounded textual evidence locators for entities and relations, emitting EVIDENCE_CAPTURED."""

    def __init__(self, client: PubNeuralClient):
        self.client = client

    def capture_evidence(
        self,
        target_type: str,
        target_id: str,
        source_id: str,
        content_hash: str,
        exact_quote: str,
        start_line: int,
        end_line: int,
        context_before: Optional[str] = None,
        context_after: Optional[str] = None,
        confidence: float = 0.98,
        validation_state: str = "UNVERIFIED",
        project_id: str = "pub-ecom",
        trust_zone: str = "tz_internal_holding",
        extractor_version: str = "v1.0.0",
        event_id: Optional[uuid.UUID] = None,
        parent_event_id: Optional[uuid.UUID] = None
    ) -> Dict[str, Any]:
        """Capture grounded evidence locator."""
        if target_type not in ("NODE", "EDGE"):
            raise ValueError(f"INVALID_TARGET_TYPE: Expected 'NODE' or 'EDGE', got '{target_type}'.")

        ns = uuid.UUID("6ba7b810-9dad-11d1-80b4-00c04fd430c8")
        if event_id is None:
            event_id = uuid.uuid5(ns, f"evidence:{target_type}:{target_id}:{content_hash}:{start_line}")

        idempotency_key = f"evidence:{target_type}:{target_id}:{content_hash}:{start_line}"
        existing = self.client.check_idempotency(idempotency_key)
        if existing:
            ev = self.client.get_event_by_id(uuid.UUID(str(existing["resulting_event_id"])))
            return {
                "event_id": str(existing["resulting_event_id"]),
                "global_sequence": ev["global_sequence"] if ev else -1,
                "payload": existing["response_payload"],
                "idempotent_replay": True
            }

        existing_event = self.client.get_event_by_id(event_id)
        if existing_event:
            self.client.record_idempotency(
                idempotency_key=idempotency_key,
                request_hash=hashlib.sha256(idempotency_key.encode("utf-8")).hexdigest(),
                resulting_event_id=event_id,
                response_payload=existing_event["payload"]
            )
            return {
                "event_id": str(event_id),
                "global_sequence": existing_event["global_sequence"],
                "payload": existing_event["payload"],
                "idempotent_replay": True
            }

        payload = {
            "target_type": target_type,
            "target_id": target_id,
            "source_id": source_id,
            "content_hash": content_hash,
            "quote": exact_quote,
            "start_line": start_line,
            "end_line": end_line,
            "context_before": context_before or "",
            "context_after": context_after or "",
            "confidence": confidence,
            "validation_state": validation_state,
            "trust_zone": trust_zone,
            "project_id": project_id,
            "extractor_version": extractor_version
        }

        stream_id = f"stream:evidence:{target_id}"
        parents = [parent_event_id] if parent_event_id else []

        seq = self.client.append_canonical_event(
            event_id=event_id,
            event_type="EVIDENCE_CAPTURED",
            stream_id=stream_id,
            stream_version=None,
            payload=payload,
            parent_event_ids=parents,
            producer_version=f"evidence_capturer:{extractor_version}"
        )

        self.client.record_idempotency(
            idempotency_key=idempotency_key,
            request_hash=hashlib.sha256(idempotency_key.encode("utf-8")).hexdigest(),
            resulting_event_id=event_id,
            response_payload=payload
        )

        return {
            "event_id": str(event_id),
            "global_sequence": seq,
            "payload": payload,
            "idempotent_replay": False
        }

