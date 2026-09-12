import hashlib
import os
import uuid
from typing import Dict, Any, Optional
from .client import PubNeuralClient


class BlobVault:
    """Preserves raw source bytes, verifies cryptographic SHA-256 digests, registers manifests and emits SOURCE_BLOB_VERIFIED."""

    def __init__(self, client: PubNeuralClient, storage_base_dir: str = "/tmp/pub_neural_vault"):
        self.client = client
        self.storage_base_dir = storage_base_dir
        os.makedirs(self.storage_base_dir, exist_ok=True)

    def compute_hashes(self, raw_bytes: bytes) -> tuple[str, str]:
        """Compute strict file_sha256 and normalized content_hash."""
        file_sha256 = hashlib.sha256(raw_bytes).hexdigest()
        # Normalized content hash: strip \r and trailing whitespaces for line-based formats
        try:
            text = raw_bytes.decode("utf-8")
            normalized_lines = [line.rstrip() for line in text.replace("\r\n", "\n").split("\n")]
            normalized_bytes = "\n".join(normalized_lines).strip().encode("utf-8")
            content_hash = hashlib.sha256(normalized_bytes).hexdigest()
        except UnicodeDecodeError:
            content_hash = file_sha256
        return file_sha256, content_hash

    def preserve_and_verify(
        self,
        raw_bytes: bytes,
        mime_type: str = "text/markdown",
        expected_sha256: Optional[str] = None,
        event_id: Optional[uuid.UUID] = None
    ) -> Dict[str, Any]:
        """Verify hash, persist to vault storage, register manifest in DB, and emit SOURCE_BLOB_VERIFIED."""
        file_sha256, content_hash = self.compute_hashes(raw_bytes)

        if expected_sha256 and expected_sha256.lower() != file_sha256.lower():
            raise ValueError(
                f"BLOB_HASH_MISMATCH: Computed SHA-256 '{file_sha256}' does not match expected '{expected_sha256}'."
            )

        byte_size = len(raw_bytes)
        blob_filename = f"{file_sha256}.bin"
        blob_path = os.path.join(self.storage_base_dir, blob_filename)

        # Write immutable binary blob to disk
        with open(blob_path, "wb") as f:
            f.write(raw_bytes)

        storage_uri = f"file://{blob_path}"

        if event_id is None:
            ns = uuid.UUID("6ba7b810-9dad-11d1-80b4-00c04fd430c8")
            event_id = uuid.uuid5(ns, f"blob:{file_sha256}")

        idempotency_key = f"blob:{file_sha256}"
        existing = self.client.check_idempotency(idempotency_key)
        if existing:
            ev = self.client.get_event_by_id(uuid.UUID(str(existing["resulting_event_id"])))
            return {
                "event_id": str(existing["resulting_event_id"]),
                "global_sequence": ev["global_sequence"] if ev else -1,
                "file_sha256": file_sha256,
                "content_hash": content_hash,
                "storage_uri": storage_uri,
                "byte_size": byte_size,
                "idempotent_replay": True
            }

        # Check if canonical event already exists in neural_events
        existing_event = self.client.get_event_by_id(event_id)
        if existing_event:
            # Ensure manifest in source_blobs is also registered if previous run failed before register
            self.client.register_verified_blob(
                file_sha256=file_sha256,
                content_hash=content_hash,
                storage_uri=storage_uri,
                byte_size=byte_size,
                mime_type=mime_type,
                originating_event_id=event_id,
                storage_backend="LOCAL_DISK"
            )
            self.client.record_idempotency(
                idempotency_key=idempotency_key,
                request_hash=hashlib.sha256(idempotency_key.encode("utf-8")).hexdigest(),
                resulting_event_id=event_id,
                response_payload=existing_event["payload"]
            )
            return {
                "event_id": str(event_id),
                "global_sequence": existing_event["global_sequence"],
                "file_sha256": file_sha256,
                "content_hash": content_hash,
                "storage_uri": storage_uri,
                "byte_size": byte_size,
                "idempotent_replay": True
            }

        # 1. Emit SOURCE_BLOB_VERIFIED canonical event first (required as originating_event_id)
        payload = {
            "file_sha256": file_sha256,
            "content_hash": content_hash,
            "storage_uri": storage_uri,
            "byte_size": byte_size,
            "mime_type": mime_type,
            "storage_backend": "LOCAL_DISK"
        }

        stream_id = f"stream:blobs:{file_sha256[:16]}"

        seq = self.client.append_canonical_event(
            event_id=event_id,
            event_type="SOURCE_BLOB_VERIFIED",
            stream_id=stream_id,
            stream_version=1,
            payload=payload,
            producer_version="blob_vault:v1.0.0"
        )

        # 2. Register verified blob manifest in PostgreSQL
        self.client.register_verified_blob(
            file_sha256=file_sha256,
            content_hash=content_hash,
            storage_uri=storage_uri,
            byte_size=byte_size,
            mime_type=mime_type,
            originating_event_id=event_id,
            storage_backend="LOCAL_DISK"
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
            "file_sha256": file_sha256,
            "content_hash": content_hash,
            "storage_uri": storage_uri,
            "byte_size": byte_size,
            "idempotent_replay": False
        }

