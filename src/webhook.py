import os
import hmac
import hashlib
import json
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, Optional

import psycopg2.errors
from fastapi import FastAPI, Header, HTTPException, Request, status
from fastapi.responses import JSONResponse

# Import client and repository allowlist
from src.ingestion.client import PubNeuralClient
from src.ingestion.scout import AUTHORIZED_REPOSITORIES

# Process‑wide configuration (static)
DB_URL = os.getenv("PUB_NEURAL_DB_URL", "postgresql://localhost/pub_neural")
ACTOR_ID = os.getenv("PUB_NEURAL_ACTOR_ID", "webhook_observer")
MACHINE_SECRET = os.getenv("PUB_NEURAL_MACHINE_SECRET", "change-me")
# NOTE: GITHUB_WEBHOOK_SECRET will be read at verification time

app = FastAPI(title="PUB Neural Repository Observation Webhook")


def verify_hmac_signature(body: bytes, signature_header: Optional[str]) -> bool:
    """Validate the GitHub HMAC SHA256 signature.

    The secret is obtained from the environment at call time so that tests can
    override it without reloading the module.
    """
    if not signature_header:
        return False
    try:
        sha_name, signature = signature_header.split('=')
    except ValueError:
        return False
    if sha_name != "sha256":
        return False
    secret = os.getenv("GITHUB_WEBHOOK_SECRET", "webhook-secret")
    mac = hmac.new(secret.encode(), msg=body, digestmod=hashlib.sha256)
    return hmac.compare_digest(mac.hexdigest(), signature)


def _extract_details(event: Dict[str, Any]) -> Dict[str, Any]:
    """Return a minimal ``details`` dict with only fields that are present.
    This keeps the stored payload small and complies with the V0.1 contract.
    """
    details: Dict[str, Any] = {}
    # Generic action
    if "action" in event:
        details["action"] = event["action"]
    # Ref information
    if "ref" in event:
        details["ref"] = event["ref"]
    if "before" in event:
        details["before"] = event["before"]
    if "after" in event:
        details["after"] = event["after"]
    # Pull request number
    pr = event.get("pull_request")
    if isinstance(pr, dict) and "number" in pr:
        details["pull_request_number"] = pr["number"]
    # Issue number
    issue = event.get("issue")
    if isinstance(issue, dict) and "number" in issue:
        details["issue_number"] = issue["number"]
    # Workflow run id
    workflow = event.get("workflow_run")
    if isinstance(workflow, dict) and "id" in workflow:
        details["workflow_run_id"] = workflow["id"]
    # Commit info
    head = event.get("head_commit")
    if isinstance(head, dict):
        if "message" in head:
            details["commit_message"] = head["message"]
        author = head.get("author")
        if isinstance(author, dict) and "name" in author:
            details["commit_author"] = author["name"]
    return details


@app.post("/github/webhook")
async def github_webhook(
    request: Request,
    x_hub_signature_256: Optional[str] = Header(None, alias="X-Hub-Signature-256"),
    x_github_delivery: Optional[str] = Header(None, alias="X-GitHub-Delivery"),
    x_github_event: Optional[str] = Header(None, alias="X-GitHub-Event"),
):
    # ---------------------------------------------------------------------
    # 1. Delivery‑ID validation (must happen before any HMAC work)
    # ---------------------------------------------------------------------
    if not x_github_delivery:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Missing X-GitHub-Delivery header (delivery_id)"
        )

    # ---------------------------------------------------------------------
    # 2. Read raw body for HMAC verification and later payload hashing
    # ---------------------------------------------------------------------
    raw_body = await request.body()
    if not verify_hmac_signature(raw_body, x_hub_signature_256):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid HMAC signature"
        )

    # ---------------------------------------------------------------------
    # 3. Parse JSON payload
    # ---------------------------------------------------------------------
    try:
        payload_json: Dict[str, Any] = json.loads(raw_body)
    except json.JSONDecodeError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid JSON payload"
        )

    # ---------------------------------------------------------------------
    # 4. Resolve repository to authoritative project/trust zone
    # ---------------------------------------------------------------------
    repository = payload_json.get("repository", {}).get("full_name")
    if not repository:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Missing repository information in payload"
        )
    if repository not in AUTHORIZED_REPOSITORIES:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"UNAUTHORIZED_REPOSITORY: {repository}"
        )
    repo_conf = AUTHORIZED_REPOSITORIES[repository]
    project_id = repo_conf["project_id"]
    trust_zone = repo_conf["trust_zone"]

    # ---------------------------------------------------------------------
    # 5. Create a request‑local client with the resolved scope and establish session
    # ---------------------------------------------------------------------
    client = PubNeuralClient(
        db_url=os.getenv("PUB_NEURAL_DB_URL", DB_URL),
        actor_id=os.getenv("PUB_NEURAL_ACTOR_ID", ACTOR_ID),
        machine_secret=os.getenv("PUB_NEURAL_MACHINE_SECRET", MACHINE_SECRET),
        requested_trust_zone=trust_zone,
        requested_project=project_id,
    )
    try:
        client.establish_session()
    except psycopg2.errors.RaiseException as exc:
        err_msg = str(exc)
        if "Authentication failed:" in err_msg or "Authorization failed:" in err_msg:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=err_msg.strip()
            )
        raise

    # ---------------------------------------------------------------------
    # 6. Idempotency – use delivery_id as the unique key (must happen after session)
    # ---------------------------------------------------------------------
    idempotency_key = f"github_observation:{x_github_delivery}"
    existing = client.check_idempotency(idempotency_key)
    if existing:
        # Replay – event already persisted, respond 200 without creating a new one
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={"detail": "Replay detected – event already persisted"}
        )

    # ---------------------------------------------------------------------
    # 7. Build minimal observation payload (no full raw webhook stored)
    # ---------------------------------------------------------------------
    minimal_payload = {
        "ref": payload_json.get("ref"),
        "sha": payload_json.get("after") or payload_json.get("head_commit", {}).get("id"),
        "details": _extract_details(payload_json),
    }

    observation_payload: Dict[str, Any] = {
        "observation_id": str(uuid.uuid4()),
        "source": "github",
        "source_event_id": payload_json.get("hook_id"),
        "repository": repository,
        "project_id": project_id,
        "trust_zone": trust_zone,
        "event_type": x_github_event,
        "observed_at": datetime.now(timezone.utc).isoformat(),
        "external_actor": payload_json.get("sender", {}).get("login"),
        "internal_actor": ACTOR_ID,
        "payload": minimal_payload,
        "provenance": {
            "delivery_id": x_github_delivery,
            "received_at": datetime.now(timezone.utc).isoformat(),
            "payload_hash": hashlib.sha256(raw_body).hexdigest(),
        },
    }

    # ---------------------------------------------------------------------
    # 8. Persist the canonical event
    # ---------------------------------------------------------------------
    event_id = uuid.uuid4()
    try:
        global_seq = client.append_canonical_event(
            event_id=event_id,
            event_type="REPOSITORY_OBSERVED",
            stream_id=idempotency_key,
            stream_version=None,
            payload=observation_payload,
            parent_event_ids=None,
        )
    except PermissionError as perm_err:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(perm_err))
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc))

    # ---------------------------------------------------------------------
    # 9. Record idempotency information
    # ---------------------------------------------------------------------
    request_hash = hashlib.sha256(raw_body).hexdigest()
    client.record_idempotency(
        idempotency_key=idempotency_key,
        request_hash=request_hash,
        resulting_event_id=event_id,
        response_payload={"global_sequence": global_seq, "status": "created"},
        ttl_days=30,
    )

    # ---------------------------------------------------------------------
    # 10. Return success (202 Accepted)
    # ---------------------------------------------------------------------
    return JSONResponse(
        status_code=status.HTTP_202_ACCEPTED,
        content={"detail": "Event persisted", "global_sequence": global_seq},
    )
