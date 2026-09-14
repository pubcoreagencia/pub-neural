"""
Security and authentication dependencies for the Operational Runtime API.
Guarantees:
- Operational boundary authentication separate from Console read-only session.
- Secure Bearer token validation with constant-time comparison to prevent timing attacks.
- Zero credential logging.
"""

import hmac
from typing import Optional


class RuntimeAuthenticationError(Exception):
    """Raised when authentication fails on the Runtime API."""
    pass


class RuntimeAuthorizationError(Exception):
    """Raised when provided credentials are invalid or forbidden."""
    pass


def extract_bearer_token(auth_header: Optional[str]) -> str:
    """
    Extract and validate bearer token from HTTP Authorization header.
    Format must strictly match: 'Bearer <token>'.
    """
    if not auth_header or not auth_header.strip():
        raise RuntimeAuthenticationError("Missing Authorization header.")

    parts = auth_header.strip().split(" ", 1)
    if len(parts) != 2 or parts[0].lower() != "bearer":
        raise RuntimeAuthenticationError("Malformed Authorization header. Format must be 'Bearer <token>'.")

    token = parts[1].strip()
    if not token:
        raise RuntimeAuthenticationError("Empty bearer token provided.")

    return token


def verify_runtime_token(
    auth_header: Optional[str],
    expected_token: Optional[str],
    enforce_auth: bool = True,
) -> bool:
    """
    Verifies the incoming Authorization header against the configured runtime API token.
    Uses hmac.compare_digest for constant-time comparison.
    Raises RuntimeAuthenticationError (401) on missing/malformed header.
    Raises RuntimeAuthorizationError (403) on token mismatch.
    """
    if not enforce_auth:
        return True

    if not expected_token:
        # If enforcement is active but no server token configured, reject access safely
        raise RuntimeAuthorizationError("Runtime API token is not configured on server.")

    token = extract_bearer_token(auth_header)

    if not hmac.compare_digest(token.encode("utf-8"), expected_token.encode("utf-8")):
        raise RuntimeAuthorizationError("Invalid runtime bearer token.")

    return True
