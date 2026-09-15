"""
Database connection management and security dependency injection.
Guarantees:
- Read-only transaction enforcement at PostgreSQL engine level.
- Bearer session token validation and RLS attachment via pub_neural.attach_session().
- Immediate rollback upon error.
"""

from contextlib import contextmanager
import hashlib
from typing import Any, Generator, Optional
import psycopg2
from psycopg2.extras import RealDictCursor


class AuthenticationError(Exception):
    """Raised when authentication fails (missing, malformed, or invalid bearer token)."""
    pass


class ReadOnlyViolationError(Exception):
    """Raised when a mutation operation is detected or attempted."""
    pass


def extract_bearer_token(auth_header: Optional[str]) -> str:
    """
    Extract and validate bearer token from HTTP Authorization header.
    Format must strictly match: 'Bearer <token>'.
    """
    if not auth_header or not auth_header.strip():
        raise AuthenticationError("Missing Authorization header.")

    parts = auth_header.strip().split(" ", 1)
    if len(parts) != 2 or parts[0].lower() != "bearer":
        raise AuthenticationError("Malformed Authorization header. Format must be 'Bearer <token>'.")

    token = parts[1].strip()
    if not token:
        raise AuthenticationError("Empty bearer token provided.")

    return token


@contextmanager
def get_readonly_connection(
    db_url: str,
    bearer_token: Optional[str] = None,
    enforce_auth: bool = True
) -> Generator[Any, None, None]:
    """
    Context manager that acquires a PostgreSQL connection, enforces READ ONLY mode,
    attaches the bearer session, and provides a RealDictCursor.
    """
    conn = None
    try:
        conn = psycopg2.connect(db_url, cursor_factory=RealDictCursor)
        conn.autocommit = False

        # Physical engine-level read-only enforcement
        conn.set_session(readonly=True)

        with conn.cursor() as cur:
            if bearer_token:
                cur.execute("SELECT pub_neural.attach_session(%s) AS attached;", (bearer_token,))
                res = cur.fetchone()
                if not res or not res["attached"]:
                    raise AuthenticationError("Invalid, expired, or revoked bearer session token.")
            elif enforce_auth:
                raise AuthenticationError("Authentication required: no bearer token provided.")

            yield cur

        conn.commit()
    except psycopg2.errors.ReadOnlySqlTransaction as e:
        if conn:
            conn.rollback()
        raise ReadOnlyViolationError(f"Database mutation rejected: transaction is strictly read-only. ({e})")
    except Exception:
        if conn:
            conn.rollback()
        raise
    finally:
        if conn and not conn.closed:
            conn.close()
