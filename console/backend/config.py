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

    @classmethod
    def from_environment(cls) -> "ConsoleConfig":
        db_url = os.getenv(
            "PUB_NEURAL_DB_URL",
            "postgresql://pub_neural_app:pub_neural_app_secret@localhost:5432/pub_neural",
        )
        host = os.getenv("CONSOLE_HOST", "127.0.0.1")
        port = int(os.getenv("CONSOLE_PORT", "8080"))
        max_hop_depth = int(os.getenv("CONSOLE_MAX_HOP_DEPTH", "2"))
        max_neighborhood_nodes = int(os.getenv("CONSOLE_MAX_NEIGHBORHOOD_NODES", "150"))
        default_search_limit = int(os.getenv("CONSOLE_DEFAULT_SEARCH_LIMIT", "10"))
        max_search_limit = int(os.getenv("CONSOLE_MAX_SEARCH_LIMIT", "50"))
        default_event_limit = int(os.getenv("CONSOLE_DEFAULT_EVENT_LIMIT", "50"))
        max_event_limit = int(os.getenv("CONSOLE_MAX_EVENT_LIMIT", "200"))

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
        )
