import hashlib
import re
import unicodedata
import uuid
from typing import Dict, Any, List, Optional
from src.ingestion.client import PubNeuralClient


class EntityExtractorWorker:
    """Extracts semantic knowledge entities from parsed chunks, emitting ENTITY_EXTRACTED."""

    def __init__(self, client: PubNeuralClient):
        self.client = client

    def format_node_id(self, entity_type: str, project_id: str, title: str) -> str:
        """Derive canonical deterministic collision-resistant node_id supporting Unicode."""
        # Normalize Unicode to NFKD and strip diacritics
        nfkd = unicodedata.normalize('NFKD', title.strip())
        ascii_text = nfkd.encode('ASCII', 'ignore').decode('ASCII').lower()
        clean_slug = re.sub(r'[^a-z0-9]+', '-', ascii_text).strip('-')
        if not clean_slug:
            clean_slug = "entity"

        # Truncate slug if necessary and append 8-char SHA-256 digest of original exact title
        # to ensure collision resistance across distinct titles that normalize similarly
        title_hash = hashlib.sha256(title.strip().encode("utf-8")).hexdigest()[:8]
        slug = f"{clean_slug[:40]}-{title_hash}"
        return f"{entity_type.lower()}:{project_id}:{slug}"

    def extract_entity(
        self,
        entity_type: str,
        title: str,
        summary: str,
        content: str,
        source_chunk_id: str,
        project_id: str = "pub-ecom",
        trust_zone: str = "tz_internal_holding",
        initial_state: str = "CANDIDATE",
        confidence_score: float = 0.95,
        extractor_version: str = "v1.0.0",
        event_id: Optional[uuid.UUID] = None,
        parent_event_id: Optional[uuid.UUID] = None
    ) -> Dict[str, Any]:
        """Extract typed entity and emit canonical ENTITY_EXTRACTED event."""
        node_id = self.format_node_id(entity_type, project_id, title)
        slug = node_id.replace(":", "-")

        ns = uuid.UUID("6ba7b810-9dad-11d1-80b4-00c04fd430c8")
        if event_id is None:
            event_id = uuid.uuid5(ns, f"entity:{node_id}:{source_chunk_id}")

        idempotency_key = f"extract_entity:{node_id}:{source_chunk_id}"
        existing = self.client.check_idempotency(idempotency_key)
        if existing:
            ev = self.client.get_event_by_id(uuid.UUID(str(existing["resulting_event_id"])))
            return {
                "event_id": str(existing["resulting_event_id"]),
                "global_sequence": ev["global_sequence"] if ev else -1,
                "node_id": node_id,
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
                "node_id": node_id,
                "payload": existing_event["payload"],
                "idempotent_replay": True
            }

        payload = {
            "node_id": node_id,
            "entity_type": entity_type,
            "title": title,
            "slug": slug,
            "summary": summary,
            "content": content,
            "trust_zone": trust_zone,
            "scope": "GLOBAL",
            "project_id": project_id,
            "initial_state": initial_state,
            "confidence_score": confidence_score,
            "source_chunk_id": source_chunk_id,
            "extractor_version": extractor_version
        }

        stream_id = f"stream:entity:{node_id}"
        parents = [parent_event_id] if parent_event_id else []

        seq = self.client.append_canonical_event(
            event_id=event_id,
            event_type="ENTITY_EXTRACTED",
            stream_id=stream_id,
            stream_version=None,
            payload=payload,
            parent_event_ids=parents,
            producer_version=f"entity_extractor:{extractor_version}"
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
            "node_id": node_id,
            "payload": payload,
            "idempotent_replay": False
        }

