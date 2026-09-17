"""
Configuration management for PUB Neural Operational Runtime API V0.1.
Separate from ConsoleConfig (which is strictly read-only presentation).
"""

from dataclasses import dataclass
import os
from typing import Optional


@dataclass(frozen=True)
class RuntimeConfig:
    """Configuration for operational runtime server boundary."""
    host: str = "127.0.0.1"
    port: int = 8081
    auth_token: Optional[str] = None
    enforce_auth: bool = True
    db_url: str = "postgresql://pub_neural_app:pub_neural_app_secret@localhost:5432/pub_neural"

    @classmethod
    def from_environment(cls) -> "RuntimeConfig":
        host = os.getenv("RUNTIME_HOST", "127.0.0.1")
        port = int(os.getenv("RUNTIME_PORT", "8081"))
        
        # Runtime API token is separate from console session tokens
        auth_token = os.getenv("PUB_NEURAL_RUNTIME_TOKEN") or os.getenv("RUNTIME_API_TOKEN")
        
        # Authentication enforcement can be disabled in test environments via flag
        enforce_raw = os.getenv("RUNTIME_ENFORCE_AUTH", "true").lower()
        enforce_auth = enforce_raw not in ("0", "false", "no", "off")
        
        db_url = os.getenv(
            "PUB_NEURAL_DB_URL",
            "postgresql://pub_neural_app:pub_neural_app_secret@localhost:5432/pub_neural",
        )
        
        return cls(
            host=host,
            port=port,
            auth_token=auth_token,
            enforce_auth=enforce_auth,
            db_url=db_url,
        )
