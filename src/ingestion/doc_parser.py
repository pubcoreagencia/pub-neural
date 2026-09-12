import hashlib
import uuid
from typing import Dict, Any, List, Optional
from .client import PubNeuralClient


class DocumentParserWorker:
    """Parses documents into deterministic chunks with lexical hashing and line offsets, emitting DOCUMENT_PARSED."""

    def __init__(self, client: PubNeuralClient):
        self.client = client

    def parse_text_units(
        self,
        text_content: str,
        document_id: str,
        source_id: str,
        project_id: str = "pub-ecom",
        parser_version: str = "v1.0.0",
        chunk_line_size: int = 20,
        event_id: Optional[uuid.UUID] = None,
        parent_event_id: Optional[uuid.UUID] = None
    ) -> Dict[str, Any]:
        """Parse text into deterministic line-bounded chunks."""
        lines = text_content.splitlines()
        total_lines = len(lines)
        chunks = []

        chunk_idx = 0
        start = 0
        while start < total_lines:
            end = min(start + chunk_line_size, total_lines)
            chunk_slice = lines[start:end]
            chunk_text = "\n".join(chunk_slice)
            chunk_hash = hashlib.sha256(chunk_text.encode("utf-8")).hexdigest()

            chunk_id = f"chunk:{document_id}:{chunk_idx}"
            chunks.append({
                "chunk_id": chunk_id,
                "start_line": start + 1,
                "end_line": end,
                "chunk_hash": chunk_hash,
                "content": chunk_text
            })

            chunk_idx += 1
            start = end

        content_sha256 = hashlib.sha256(text_content.encode("utf-8")).hexdigest()

        ns = uuid.UUID("6ba7b810-9dad-11d1-80b4-00c04fd430c8")
        if event_id is None:
            event_id = uuid.uuid5(ns, f"parsed:{document_id}:{parser_version}:{content_sha256}:{len(chunks)}")

        idempotency_key = f"parsed:{document_id}:{parser_version}:{content_sha256}"
        existing = self.client.check_idempotency(idempotency_key)
        if existing:
            ev = self.client.get_event_by_id(uuid.UUID(str(existing["resulting_event_id"])))
            return {
                "event_id": str(existing["resulting_event_id"]),
                "global_sequence": ev["global_sequence"] if ev else -1,
                "chunks": existing["response_payload"].get("chunks", chunks),
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
                "chunks": existing_event["payload"].get("chunks", chunks),
                "payload": existing_event["payload"],
                "idempotent_replay": True
            }

        payload = {
            "document_id": document_id,
            "source_id": source_id,
            "parser_version": parser_version,
            "content_hash": content_sha256,
            "text_unit_count": len(chunks),
            "chunks": chunks
        }

        stream_id = f"stream:parsed:{document_id}"
        parents = [parent_event_id] if parent_event_id else []

        seq = self.client.append_canonical_event(
            event_id=event_id,
            event_type="DOCUMENT_PARSED",
            stream_id=stream_id,
            stream_version=None,
            payload=payload,
            parent_event_ids=parents,
            producer_version=f"doc_parser:{parser_version}"
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
            "chunks": chunks,
            "payload": payload,
            "idempotent_replay": False
        }

