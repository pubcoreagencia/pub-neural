"""
Authentication and session management service for PUB Neural Console.
Integrates strictly with:
- pub_neural.establish_session_context(actor_id, secret, trust_zone, project)
- pub_neural.active_sessions
- pub_neural.trusted_actors
"""

from datetime import datetime, timezone
import hashlib
from typing import Any, Dict, Optional
import psycopg2
from psycopg2.extras import RealDictCursor

from console.backend.dependencies import AuthenticationError


def login_actor(
    db_url: str,
    actor_id: str,
    secret: str,
    trust_zone: str = "tz_internal_holding",
    project_scope: Optional[str] = None
) -> Dict[str, Any]:
    """
    Authenticate an operator actor using pub_neural.establish_session_context.
    Returns session token and metadata.
    """
    if not actor_id or not actor_id.strip():
        raise AuthenticationError("Missing required field: actor_id")
    if not secret or not secret.strip():
        raise AuthenticationError("Missing required field: secret")

    conn = None
    try:
        conn = psycopg2.connect(db_url, cursor_factory=RealDictCursor)
        conn.autocommit = True
        with conn.cursor() as cur:
            try:
                cur.execute(
                    "SELECT pub_neural.establish_session_context(%s, %s, %s, %s) AS token;",
                    (actor_id.strip(), secret.strip(), trust_zone.strip(), project_scope)
                )
                row = cur.fetchone()
                if not row or not row["token"]:
                    raise AuthenticationError("Failed to establish session.")
                raw_token = row["token"]
            except psycopg2.Error as pg_err:
                msg = str(pg_err).strip()
                if "Authentication failed" in msg:
                    raise AuthenticationError("Invalid actor ID or machine secret.")
                if "Authorization failed" in msg:
                    raise AuthenticationError(f"Actor not authorized for requested trust zone/project: {msg}")
                raise AuthenticationError(f"Authentication error: {msg}")

            # Fetch session metadata using token hash
            token_hash = hashlib.sha256(raw_token.encode("utf-8")).hexdigest()
            cur.execute("""
                SELECT actor_id, actor_role, active_trust_zone, active_project_id, expires_at
                FROM pub_neural.active_sessions
                WHERE session_token_hash = %s;
            """, (token_hash,))
            session_row = cur.fetchone()

            if not session_row:
                raise AuthenticationError("Session registered but metadata unretrievable.")

            expires_at = session_row["expires_at"]
            expires_iso = expires_at.isoformat() if hasattr(expires_at, "isoformat") else str(expires_at)

            return {
                "token": raw_token,
                "actor_id": session_row["actor_id"],
                "actor_role": str(session_row["actor_role"]),
                "trust_zone": session_row["active_trust_zone"],
                "project_scope": session_row["active_project_id"],
                "expires_at": expires_iso,
            }
    finally:
        if conn and not conn.closed:
            conn.close()


def get_current_session(db_url: str, bearer_token: str) -> Dict[str, Any]:
    """
    Validate active session token and return its metadata without secrets.
    """
    if not bearer_token or not bearer_token.strip():
        raise AuthenticationError("No session token provided.")

    token_hash = hashlib.sha256(bearer_token.strip().encode("utf-8")).hexdigest()
    conn = None
    try:
        conn = psycopg2.connect(db_url, cursor_factory=RealDictCursor)
        conn.autocommit = True
        with conn.cursor() as cur:
            cur.execute("""
                SELECT s.actor_id, s.actor_role, s.active_trust_zone, s.active_project_id, s.expires_at, a.is_active
                FROM pub_neural.active_sessions s
                JOIN pub_neural.trusted_actors a ON s.actor_id = a.actor_id
                WHERE s.session_token_hash = %s
                  AND s.expires_at > CURRENT_TIMESTAMP;
            """, (token_hash,))
            row = cur.fetchone()
            if not row or not row["is_active"]:
                raise AuthenticationError("Invalid, expired, or revoked session token.")

            expires_at = row["expires_at"]
            expires_iso = expires_at.isoformat() if hasattr(expires_at, "isoformat") else str(expires_at)

            return {
                "authenticated": True,
                "actor_id": row["actor_id"],
                "actor_role": str(row["actor_role"]),
                "trust_zone": row["active_trust_zone"],
                "project_scope": row["active_project_id"],
                "expires_at": expires_iso,
            }
    finally:
        if conn and not conn.closed:
            conn.close()


def logout_actor(db_url: str, bearer_token: str) -> bool:
    """
    Revoke current session in active_sessions table.
    """
    if not bearer_token or not bearer_token.strip():
        return False

    token_hash = hashlib.sha256(bearer_token.strip().encode("utf-8")).hexdigest()
    conn = None
    try:
        conn = psycopg2.connect(db_url, cursor_factory=RealDictCursor)
        conn.autocommit = True
        with conn.cursor() as cur:
            cur.execute("""
                DELETE FROM pub_neural.active_sessions
                WHERE session_token_hash = %s;
            """, (token_hash,))
            return cur.rowcount > 0
    finally:
        if conn and not conn.closed:
            conn.close()
