import hashlib
import uuid
from typing import Dict, Any, Optional
from src.ingestion.client import PubNeuralClient


class RelationExtractorWorker:
    """Extracts typed relationships between semantic entities, emitting RELATION_EXTRACTED."""

    def __init__(self, client: PubNeuralClient):
        self.client = client

    def extract_relation(
        self,
        source_id: str,
        relation_type: str,
        target_id: str,
        source_chunk_id: str,
        weight: float = 1.0,
        is_bidirectional: bool = False,
        trust_zone: str = "tz_internal_holding",
        scope: str = "GLOBAL",
        project_id: str = "pub-ecom",
        extractor_version: str = "v1.0.0",
        event_id: Optional[uuid.UUID] = None,
        parent_event_id: Optional[uuid.UUID] = None
    ) -> Dict[str, Any]:
        """Extract relationship and emit canonical RELATION_EXTRACTED event."""
        ns = uuid.UUID("6ba7b810-9dad-11d1-80b4-00c04fd430c8")
        if event_id is None:
            event_id = uuid.uuid5(ns, f"relation:{source_id}:{relation_type}:{target_id}:{source_chunk_id}")

        idempotency_key = f"extract_rel:{source_id}:{relation_type}:{target_id}:{source_chunk_id}"
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
            "source_id": source_id,
            "relation_type": relation_type,
            "target_id": target_id,
            "weight": weight,
            "is_bidirectional": is_bidirectional,
            "trust_zone": trust_zone,
            "scope": scope,
            "source_chunk_id": source_chunk_id,
            "extractor_version": extractor_version
        }

        stream_id = f"stream:rel:{source_id}->{target_id}"
        parents = [parent_event_id] if parent_event_id else []

        seq = self.client.append_canonical_event(
            event_id=event_id,
            event_type="RELATION_EXTRACTED",
            stream_id=stream_id,
            stream_version=None,
            payload=payload,
            parent_event_ids=parents,
            producer_version=f"relation_extractor:{extractor_version}"
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

