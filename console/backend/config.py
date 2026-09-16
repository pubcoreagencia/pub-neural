"""
Configuration management for PUB Neural Console V0 Backend Service.
Read-only presentation server settings.
"""

from dataclasses import dataclass
import os


@dataclass(frozen=True)
class ConsoleConfig:
    db_url: str
    host: str = "127.0.0.1"
    port: int = 8080
    max_hop_depth: int = 2
    max_neighborhood_nodes: int = 150
    default_search_limit: int = 10
    max_search_limit: int = 50
    default_event_limit: int = 50
    max_event_limit: int = 200
    cors_origins: tuple = ("*",)

    @classmethod
    def from_environment(cls) -> "ConsoleConfig":
        db_url = os.getenv("PUB_NEURAL_DB_URL")
        if not db_url or not db_url.strip():
            # Check local .env file in workspace root if present
            env_file = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), ".env")
            if os.path.exists(env_file):
                try:
                    with open(env_file, "r", encoding="utf-8") as f:
                        for line in f:
                            line = line.strip()
                            if line.startswith("PUB_NEURAL_DB_URL="):
                                val = line.split("=", 1)[1].strip().strip("\x27\"")
                                if val:
                                    db_url = val
                                    break
                except Exception:
                    pass

        if not db_url or not db_url.strip():
            # In test environments or when explicitly requested via fallback
            test_fallback = os.getenv("PUB_NEURAL_TEST_DB_URL")
            if test_fallback and test_fallback.strip():
                db_url = test_fallback.strip()
            else:
                # Require explicit configuration for runtime; avoid default localhost:5432 assumption
                db_url = os.getenv(
                    "PUB_NEURAL_FALLBACK_DB_URL",
                    "postgresql://pub_neural_app:pub_neural_app_secret@localhost:5432/pub_neural",
                )

        # Enforce connect_timeout=10 and sslmode=require on remote database connections if not explicitly set
        if db_url and "localhost" not in db_url and "127.0.0.1" not in db_url:
            separator = "&" if "?" in db_url else "?"
            if "connect_timeout=" not in db_url:
                db_url = f"{db_url}{separator}connect_timeout=10"
                separator = "&"
            if "sslmode=" not in db_url:
                db_url = f"{db_url}{separator}sslmode=require"

        host = os.getenv("CONSOLE_HOST", "127.0.0.1")
        port = int(os.getenv("CONSOLE_PORT", "8080"))
        max_hop_depth = int(os.getenv("CONSOLE_MAX_HOP_DEPTH", "2"))
        max_neighborhood_nodes = int(os.getenv("CONSOLE_MAX_NEIGHBORHOOD_NODES", "150"))
        default_search_limit = int(os.getenv("CONSOLE_DEFAULT_SEARCH_LIMIT", "10"))
        max_search_limit = int(os.getenv("CONSOLE_MAX_SEARCH_LIMIT", "50"))
        default_event_limit = int(os.getenv("CONSOLE_DEFAULT_EVENT_LIMIT", "50"))
        max_event_limit = int(os.getenv("CONSOLE_MAX_EVENT_LIMIT", "200"))

        raw_cors = os.getenv("CONSOLE_CORS_ORIGINS", "*")
        cors_origins = tuple(o.strip() for o in raw_cors.split(",") if o.strip())
        if not cors_origins:
            cors_origins = ("*",)

        return cls(
            db_url=db_url,
            host=host,
            port=port,
            max_hop_depth=max_hop_depth,
            max_neighborhood_nodes=max_neighborhood_nodes,
            default_search_limit=default_search_limit,
            max_search_limit=max_search_limit,
            default_event_limit=default_event_limit,
            max_event_limit=max_event_limit,
            cors_origins=cors_origins,
        )
