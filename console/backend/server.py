"""
HTTP REST Server for PUB Neural Console V0 Read-Only Service.
Implements the presentation boundary on top of Python standard library http.server.
Guarantees:
- Zero external HTTP framework dependencies required.
- Strictly read-only: POST, PUT, DELETE, PATCH return 405 Method Not Allowed.
- All protected endpoints require Authorization: Bearer <token>.
- Reuses existing HybridSearchEngine and PostgreSQL RLS session attachment.
"""

from datetime import datetime, timezone
import json
import re
import sys
from urllib.parse import parse_qs, urlparse
from http.server import BaseHTTPRequestHandler, HTTPServer
from typing import Any, Callable, Dict, List, Optional, Tuple

from console.backend.config import ConsoleConfig
from console.backend.dependencies import (
    AuthenticationError,
    ReadOnlyViolationError,
    extract_bearer_token,
    get_readonly_connection,
)
from console.backend.services.activity_service import (
    get_governance_review_data,
    get_overview_data,
)
from console.backend.services.auth_service import (
    get_current_session,
    login_actor,
    logout_actor,
)
from console.backend.services.graph_service import get_entity_detail, get_neighborhood
from console.backend.services.search_service import execute_console_search
from console.backend.services.status_service import get_system_status
from console.backend.services.timeline_service import get_event_detail, get_events_list



class ConsoleRequestHandler(BaseHTTPRequestHandler):
    """Request handler enforcing read-only guarantees, bearer auth, and clean JSON responses."""

    server_config: ConsoleConfig = ConsoleConfig.from_environment()

    def _get_cors_allow_origin(self) -> str:
        """Resolve Access-Control-Allow-Origin based on incoming Origin header and config."""
        allowed = getattr(self.server_config, "cors_origins", ("*",))
        if "*" in allowed:
            return "*"
        req_origin = self.headers.get("Origin", "").strip()
        if req_origin and req_origin in allowed:
            return req_origin
        # If no origin or not explicitly allowed, default to the first configured origin
        return allowed[0] if allowed else "*"

    def _send_json(self, status_code: int, payload: Dict[str, Any]) -> None:
        """Send a JSON HTTP response with security headers."""
        try:
            body = json.dumps(payload, indent=2).encode("utf-8")
        except Exception as e:
            body = json.dumps({"error": "SerializationError", "detail": str(e)}).encode("utf-8")
            status_code = 500

        allow_origin = self._get_cors_allow_origin()

        self.send_response(status_code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Access-Control-Allow-Origin", allow_origin)
        if allow_origin != "*":
            self.send_header("Vary", "Origin")
        self.send_header("Access-Control-Allow-Headers", "Authorization, Content-Type")
        self.send_header("Access-Control-Allow-Methods", "GET, OPTIONS")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def _drain_body(self) -> None:
        """Drain any incoming request payload to prevent TCP reset on HTTP/1.1 clients."""
        try:
            length = int(self.headers.get("Content-Length", 0))
            if length > 0:
                self.rfile.read(length)
        except Exception:
            pass

    def do_OPTIONS(self) -> None:
        """Handle CORS preflight requests."""
        allow_origin = self._get_cors_allow_origin()
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", allow_origin)
        if allow_origin != "*":
            self.send_header("Vary", "Origin")
        self.send_header("Access-Control-Allow-Headers", "Authorization, Content-Type")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Max-Age", "86400")
        self.end_headers()

    def do_POST(self) -> None:
        """Handle session authentication requests while prohibiting all data mutations."""
        parsed = urlparse(self.path)
        path = parsed.path.rstrip("/")

        try:
            # 1. Login endpoint: POST /api/v1/auth/login
            if path == "/api/v1/auth/login":
                try:
                    content_len = int(self.headers.get("Content-Length", 0))
                    raw_body = self.rfile.read(content_len).decode("utf-8") if content_len > 0 else "{}"
                    body_json = json.loads(raw_body)
                except Exception:
                    self._send_json(400, {"error": "BadRequest", "detail": "Malformed JSON payload."})
                    return

                actor_id = body_json.get("actor_id")
                secret = body_json.get("secret")
                trust_zone = body_json.get("trust_zone", "tz_internal_holding")
                project_scope = body_json.get("project_scope")

                session_data = login_actor(
                    db_url=self.server_config.db_url,
                    actor_id=actor_id,
                    secret=secret,
                    trust_zone=trust_zone,
                    project_scope=project_scope,
                )
                self._send_json(200, session_data)
                return

            # 2. Logout endpoint: POST /api/v1/auth/logout
            if path == "/api/v1/auth/logout":
                self._drain_body()
                auth_header = self.headers.get("Authorization")
                token = extract_bearer_token(auth_header)
                revoked = logout_actor(self.server_config.db_url, token)
                self._send_json(200, {"revoked": revoked, "status": "LOGGED_OUT"})
                return

            # Explicitly reject all other POST mutations
            self._drain_body()
            self._send_json(
                405,
                {
                    "error": "Method Not Allowed",
                    "detail": "PUB Neural Console API is strictly read-only. Mutation operations (POST) are prohibited.",
                },
            )
        except AuthenticationError as auth_err:
            self._send_json(401, {"error": "Unauthorized", "detail": str(auth_err)})
        except Exception as e:
            self._send_json(500, {"error": "InternalServerError", "detail": str(e)})

    def do_PUT(self) -> None:
        """Explicitly prohibit mutation operations."""
        self._drain_body()
        self._send_json(
            405,
            {
                "error": "Method Not Allowed",
                "detail": "PUB Neural Console API is strictly read-only. Mutation operations (PUT) are prohibited.",
            },
        )

    def do_DELETE(self) -> None:
        """Explicitly prohibit mutation operations."""
        self._drain_body()
        self._send_json(
            405,
            {
                "error": "Method Not Allowed",
                "detail": "PUB Neural Console API is strictly read-only. Mutation operations (DELETE) are prohibited.",
            },
        )

    def do_PATCH(self) -> None:
        """Explicitly prohibit mutation operations."""
        self._drain_body()
        self._send_json(
            405,
            {
                "error": "Method Not Allowed",
                "detail": "PUB Neural Console API is strictly read-only. Mutation operations (PATCH) are prohibited.",
            },
        )

    def do_GET(self) -> None:
        """Route incoming GET requests to the corresponding service handlers."""
        parsed = urlparse(self.path)
        path = parsed.path.rstrip("/")
        if not path:
            path = "/"
        params = parse_qs(parsed.query)

        try:
            # 1. Unauthenticated Health check
            if path == "/health":
                self._send_json(
                    200,
                    {
                        "status": "UP",
                        "service": "pub-neural-console-backend",
                        "version": "v0.1.0",
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                    },
                )
                return

            # 2. System Status (Authenticated or Public connectivity overview)
            if path == "/api/v1/status":
                auth_header = self.headers.get("Authorization")
                token = None
                if auth_header:
                    try:
                        token = extract_bearer_token(auth_header)
                    except AuthenticationError:
                        token = None

                with get_readonly_connection(
                    self.server_config.db_url,
                    bearer_token=token,
                    enforce_auth=False
                ) as cur:
                    status_dto = get_system_status(cur, bearer_token=token)
                    self._send_json(200, status_dto.to_dict())
                return

            # 2b. Session verification: GET /api/v1/auth/session
            if path == "/api/v1/auth/session":
                auth_header = self.headers.get("Authorization")
                token = extract_bearer_token(auth_header)
                session_info = get_current_session(self.server_config.db_url, token)
                self._send_json(200, session_info)
                return

            # All remaining endpoints require Authorization: Bearer <token>
            token = extract_bearer_token(self.headers.get("Authorization"))

            # 3. Overview endpoint (Command Center V0.1)
            if path == "/api/v1/overview":
                window_param = params.get("window_days", [14])[0]
                try:
                    window_days = int(window_param)
                except ValueError:
                    window_days = 14

                with get_readonly_connection(self.server_config.db_url, bearer_token=token) as cur:
                    overview_dto = get_overview_data(cur, window_days=window_days)
                    self._send_json(200, overview_dto.to_dict())
                return

            # 3b. Governance Review endpoint (Knowledge awaiting review)
            if path == "/api/v1/governance/review":
                with get_readonly_connection(self.server_config.db_url, bearer_token=token) as cur:
                    gov_dto = get_governance_review_data(cur)
                    self._send_json(200, gov_dto.to_dict())
                return

            # 4. Search endpoint

            if path == "/api/v1/search":
                q_list = params.get("q")
                if not q_list or not q_list[0].strip():
                    self._send_json(400, {"error": "BadRequest", "detail": "Missing required query parameter 'q'."})
                    return

                query_str = q_list[0].strip()
                entity_type = params.get("entity_type", [None])[0]
                limit = int(params.get("limit", [self.server_config.default_search_limit])[0])

                search_dto = execute_console_search(
                    db_url=self.server_config.db_url,
                    bearer_token=token,
                    query=query_str,
                    entity_type=entity_type,
                    limit=limit,
                )
                self._send_json(200, search_dto.to_dict())
                return

            # 4. Events list endpoint
            if path == "/api/v1/events":
                limit = int(params.get("limit", [self.server_config.default_event_limit])[0])
                offset = int(params.get("offset", [0])[0])
                stream_id = params.get("stream_id", [None])[0]
                event_type = params.get("event_type", [None])[0]

                with get_readonly_connection(self.server_config.db_url, bearer_token=token) as cur:
                    events_dto = get_events_list(
                        cur,
                        limit=limit,
                        offset=offset,
                        stream_id=stream_id,
                        event_type=event_type,
                    )
                    self._send_json(200, events_dto.to_dict())
                return

            # 5. Single Event detail endpoint: /api/v1/events/{event_id}
            match_event = re.match(r"^/api/v1/events/([^/]+)$", path)
            if match_event:
                event_id = match_event.group(1)
                with get_readonly_connection(self.server_config.db_url, bearer_token=token) as cur:
                    ev_dto = get_event_detail(cur, event_id)
                    if not ev_dto:
                        self._send_json(404, {"error": "NotFound", "detail": f"Event '{event_id}' not found."})
                        return
                    self._send_json(200, ev_dto.to_dict())
                return

            # 6. Entity Neighborhood: /api/v1/entities/{entity_id}/neighborhood
            match_neigh = re.match(r"^/api/v1/entities/([^/]+)/neighborhood$", path)
            if match_neigh:
                entity_id = match_neigh.group(1)
                depth = int(params.get("depth", [1])[0])
                limit = int(params.get("limit", [50])[0])

                with get_readonly_connection(self.server_config.db_url, bearer_token=token) as cur:
                    detail = get_entity_detail(cur, entity_id)
                    if not detail:
                        self._send_json(
                            404,
                            {"error": "NotFound", "detail": f"Entity '{entity_id}' not found or unauthorized under RLS."},
                        )
                        return

                    graph_dto = get_neighborhood(cur, entity_id, depth=depth, limit=limit)
                    self._send_json(200, graph_dto.to_dict())
                return

            # 7. Entity Detail endpoint: /api/v1/entities/{entity_id}
            match_entity = re.match(r"^/api/v1/entities/([^/]+)$", path)
            if match_entity:
                entity_id = match_entity.group(1)
                with get_readonly_connection(self.server_config.db_url, bearer_token=token) as cur:
                    detail_dto = get_entity_detail(cur, entity_id)
                    if not detail_dto:
                        self._send_json(
                            404,
                            {"error": "NotFound", "detail": f"Entity '{entity_id}' not found or unauthorized under RLS."},
                        )
                        return
                    self._send_json(200, detail_dto.to_dict())
                return

            # No route matched
            self._send_json(404, {"error": "NotFound", "detail": f"Path '{path}' does not match any console API route."})

        except (AuthenticationError, PermissionError) as auth_err:
            self._send_json(401, {"error": "Unauthorized", "detail": str(auth_err)})
        except ReadOnlyViolationError as ro_err:
            self._send_json(403, {"error": "Forbidden", "detail": str(ro_err)})
        except ValueError as val_err:
            self._send_json(400, {"error": "BadRequest", "detail": str(val_err)})
        except Exception as unhandled_err:
            import traceback
            traceback.print_exc()
            self._send_json(
                500,
                {
                    "error": "InternalServerError",
                    "detail": f"An unexpected error occurred while processing read-only request: {unhandled_err}",
                },
            )

    def log_message(self, format: str, *args: Any) -> None:
        """Suppress default stderr HTTP request logging in test/library modes."""
        pass


def create_console_server(config: Optional[ConsoleConfig] = None) -> HTTPServer:
    """Instantiate standard HTTP server configured for the Console API."""
    cfg = config or ConsoleConfig.from_environment()
    ConsoleRequestHandler.server_config = cfg
    server = HTTPServer((cfg.host, cfg.port), ConsoleRequestHandler)
    return server


if __name__ == "__main__":
    cfg = ConsoleConfig.from_environment()
    server = create_console_server(cfg)
    print(f"PUB Neural Console V0 Read-Only Backend serving at http://{cfg.host}:{cfg.port}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down Console server...")
        server.server_close()
