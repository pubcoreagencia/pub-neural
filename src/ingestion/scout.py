import datetime
import hashlib
import uuid
from typing import Dict, Any, List, Optional
from .client import PubNeuralClient

# Authorized repository allowlist
AUTHORIZED_REPOSITORIES = {
    "pubcore/pub-ecom": {"branch": "main", "project_id": "pub-ecom", "trust_zone": "tz_internal_holding"},
    "pubcore/pub-neural": {"branch": "main", "project_id": "pub-neural", "trust_zone": "tz_internal_holding"},
    "pubcore/holding-governance": {"branch": "main", "project_id": "holding-core", "trust_zone": "tz_internal_holding"},
}

class ScoutWorker:
    """Discovers source files within authorized scopes and emits SOURCE_DISCOVERED events."""

    def __init__(self, client: PubNeuralClient):
        self.client = client

    def discover_source(
        self,
        repository: str,
        commit_sha: str,
        file_path: str,
        branch: str = "main",
        event_id: Optional[uuid.UUID] = None
    ) -> Dict[str, Any]:
        """Validate authorized scope and emit SOURCE_DISCOVERED."""
        if repository not in AUTHORIZED_REPOSITORIES:
            raise ValueError(f"UNAUTHORIZED_SOURCE_SCOPE: Repository '{repository}' is not in the authorized allowlist.")

        repo_conf = AUTHORIZED_REPOSITORIES[repository]
        if branch != repo_conf["branch"]:
            raise ValueError(f"UNAUTHORIZED_BRANCH: Branch '{branch}' is not authorized for repository '{repository}'.")

        if not commit_sha or len(commit_sha) < 7:
            raise ValueError("INVALID_COMMIT_SHA: Must provide a valid git commit SHA.")

        if not file_path or file_path.strip() == "":
            raise ValueError("INVALID_FILE_PATH: File path cannot be empty.")

        if event_id is None:
            # Deterministic UUIDv5 for discovery event
            ns = uuid.UUID("6ba7b810-9dad-11d1-80b4-00c04fd430c8")
            event_id = uuid.uuid5(ns, f"discover:{repository}:{branch}:{commit_sha}:{file_path}")

        idempotency_key = f"scout:{repository}:{branch}:{commit_sha}:{file_path}"
        existing = self.client.check_idempotency(idempotency_key)
        if existing:
            ev = self.client.get_event_by_id(uuid.UUID(str(existing["resulting_event_id"])))
            return {
                "event_id": str(existing["resulting_event_id"]),
                "global_sequence": ev["global_sequence"] if ev else -1,
                "payload": existing["response_payload"],
                "idempotent_replay": True
            }

        # Check if event already exists in neural_events directly
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
            "repository": repository,
            "branch": branch,
            "commit_sha": commit_sha,
            "file_path": file_path,
            "trust_zone": repo_conf["trust_zone"],
            "project_id": repo_conf["project_id"],
            "discovered_at": datetime.datetime.now(datetime.timezone.utc).isoformat()
        }

        stream_id = f"stream:discovery:{repo_conf['project_id']}:{file_path}"

        seq = self.client.append_canonical_event(
            event_id=event_id,
            event_type="SOURCE_DISCOVERED",
            stream_id=stream_id,
            stream_version=None,
            payload=payload,
            producer_version="scout:v1.0.0"
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

