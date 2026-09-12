import datetime
import hashlib
import uuid
from typing import Dict, Any, Optional
from .client import PubNeuralClient
from .scout import AUTHORIZED_REPOSITORIES


class SourceIngestorWorker:
    """Ingests discovered sources backed by verified blobs, emitting SOURCE_INGESTED."""

    def __init__(self, client: PubNeuralClient):
        self.client = client

    def ingest_source(
        self,
        repository: str,
        commit_sha: str,
        file_path: str,
        file_sha256: str,
        branch: Optional[str] = None,
        trust_zone: Optional[str] = None,
        project_id: Optional[str] = None,
        observed_at: Optional[str] = None,
        event_id: Optional[uuid.UUID] = None,
        parent_event_id: Optional[uuid.UUID] = None
    ) -> Dict[str, Any]:
        """Emit SOURCE_INGESTED linking to verified blob manifest with strict scope validation."""
        if repository not in AUTHORIZED_REPOSITORIES:
            raise ValueError(f"UNAUTHORIZED_SOURCE_SCOPE: Repository '{repository}' is not in authorized allowlist.")

        repo_conf = AUTHORIZED_REPOSITORIES[repository]

        # Enforce canonical branch, trust_zone, project_id from allowlist if omitted or validate if passed
        resolved_branch = repo_conf["branch"]
        if branch is not None and branch != resolved_branch:
            raise ValueError(f"UNAUTHORIZED_BRANCH: Branch '{branch}' violates allowlist branch '{resolved_branch}'.")

        resolved_trust_zone = repo_conf["trust_zone"]
        if trust_zone is not None and trust_zone != resolved_trust_zone:
            raise ValueError(f"UNAUTHORIZED_TRUST_ZONE: Trust zone '{trust_zone}' violates allowlist '{resolved_trust_zone}'.")

        resolved_project_id = repo_conf["project_id"]
        if project_id is not None and project_id != resolved_project_id:
            raise ValueError(f"UNAUTHORIZED_PROJECT_ID: Project ID '{project_id}' violates allowlist '{resolved_project_id}'.")

        ns = uuid.UUID("6ba7b810-9dad-11d1-80b4-00c04fd430c8")
        source_id = uuid.uuid5(ns, f"{repository}:{commit_sha}:{file_path}")

        if observed_at is None:
            observed_at = datetime.datetime.now(datetime.timezone.utc).isoformat()

        if event_id is None:
            event_id = uuid.uuid5(ns, f"ingest:{source_id}:{file_sha256}")

        idempotency_key = f"source_ingest:{repository}:{commit_sha}:{file_path}:{file_sha256}"
        existing = self.client.check_idempotency(idempotency_key)
        if existing:
            ev = self.client.get_event_by_id(uuid.UUID(str(existing["resulting_event_id"])))
            return {
                "event_id": str(existing["resulting_event_id"]),
                "global_sequence": ev["global_sequence"] if ev else -1,
                "source_id": str(source_id),
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
                "source_id": str(source_id),
                "payload": existing_event["payload"],
                "idempotent_replay": True
            }

        payload = {
            "source_id": str(source_id),
            "repository": repository,
            "branch": resolved_branch,
            "commit_sha": commit_sha,
            "file_path": file_path,
            "file_sha256": file_sha256,
            "trust_zone": resolved_trust_zone,
            "project_id": resolved_project_id,
            "observed_at": observed_at
        }

        stream_id = f"stream:source:{source_id}"
        parents = [parent_event_id] if parent_event_id else []

        seq = self.client.append_canonical_event(
            event_id=event_id,
            event_type="SOURCE_INGESTED",
            stream_id=stream_id,
            stream_version=None,
            payload=payload,
            parent_event_ids=parents,
            producer_version="source_ingestor:v1.0.0"
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
            "source_id": str(source_id),
            "payload": payload,
            "idempotent_replay": False
        }

