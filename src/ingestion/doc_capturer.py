import datetime
import hashlib
import uuid
from typing import Dict, Any, Optional
from .client import PubNeuralClient


class DocumentCaptureWorker:
    """Captures logical documents from ingested sources, preserving lineage and emitting DOCUMENT_CAPTURED."""

    def __init__(self, client: PubNeuralClient):
        self.client = client

    def capture_document(
        self,
        source_id: str,
        file_sha256: str,
        document_title: str,
        raw_byte_size: int,
        project_id: str = "pub-ecom",
        mime_type: str = "text/markdown",
        event_id: Optional[uuid.UUID] = None,
        parent_event_id: Optional[uuid.UUID] = None
    ) -> Dict[str, Any]:
        """Capture logical document representation."""
        ns = uuid.UUID("6ba7b810-9dad-11d1-80b4-00c04fd430c8")
        document_id = f"doc:{project_id}:{uuid.uuid5(ns, f'{source_id}:{file_sha256}')}"

        if event_id is None:
            event_id = uuid.uuid5(ns, f"capture:{document_id}")

        idempotency_key = f"capture_doc:{document_id}"
        existing = self.client.check_idempotency(idempotency_key)
        if existing:
            ev = self.client.get_event_by_id(uuid.UUID(str(existing["resulting_event_id"])))
            return {
                "event_id": str(existing["resulting_event_id"]),
                "global_sequence": ev["global_sequence"] if ev else -1,
                "document_id": document_id,
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
                "document_id": document_id,
                "payload": existing_event["payload"],
                "idempotent_replay": True
            }

        observed_at = datetime.datetime.now(datetime.timezone.utc).isoformat()

        payload = {
            "document_id": document_id,
            "source_id": source_id,
            "file_sha256": file_sha256,
            "document_title": document_title,
            "raw_byte_size": raw_byte_size,
            "mime_type": mime_type,
            "observed_at": observed_at
        }

        stream_id = f"stream:doc:{document_id}"
        parents = [parent_event_id] if parent_event_id else []

        seq = self.client.append_canonical_event(
            event_id=event_id,
            event_type="DOCUMENT_CAPTURED",
            stream_id=stream_id,
            stream_version=None,
            payload=payload,
            parent_event_ids=parents,
            producer_version="doc_capturer:v1.0.0"
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
            "document_id": document_id,
            "payload": payload,
            "idempotent_replay": False
        }

