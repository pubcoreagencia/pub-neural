"""
HTTP REST Server for PUB Neural Operational Runtime API V0.1.
Implements the operational gate boundary on top of Python standard library http.server.

Guarantees:
- Completely decoupled from Console read-only API (console/backend/server.py).
- Operational endpoints:
  * POST /api/v1/runtime/query -> Executes real NeuralQueryService.
  * POST /api/v1/runtime/experience -> Executes real NeuralExperienceService.
- Preserves explicit domain status codes in HTTP responses (SUCCESS, NO_MATCH, ABSTAIN,
  CONFLICT, STALE, ACCEPTED, DUPLICATE, INVALID_REQUEST, UNAVAILABLE, INTERNAL_ERROR).
- Enforces Bearer authentication using RuntimeConfig (PUB_NEURAL_RUNTIME_TOKEN).
- Preserves taskId, executionId, and correlationId.
- Zero external HTTP framework dependencies.
"""

from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, HTTPServer
import json
import os
import sys
from typing import Any, Callable, Dict, Optional
from urllib.parse import urlparse

# Ensure repository root is in sys.path
_CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
_REPO_ROOT = os.path.dirname(os.path.dirname(_CURRENT_DIR))
_SRC_DIR = os.path.join(_REPO_ROOT, "src")
for p in (_REPO_ROOT, _SRC_DIR):
    if p not in sys.path:
        sys.path.insert(0, p)

from runtime.backend.config import RuntimeConfig
from runtime.backend.dependencies import (
    RuntimeAuthenticationError,
    RuntimeAuthorizationError,
    verify_runtime_token,
)
from src.gate.enums import ExperienceWritebackStatus, GateStatus
from src.gate.experience_service import NeuralExperienceService
from src.gate.models import ExperienceIngestionResult, NeuralQueryResponse
from src.gate.service import NeuralQueryService


# HTTP Status Code Mappings
GATE_STATUS_TO_HTTP = {
    GateStatus.SUCCESS: 200,
    GateStatus.NO_MATCH: 200,
    GateStatus.ABSTAIN: 200,
    GateStatus.CONFLICT: 200,
    GateStatus.STALE: 200,
    GateStatus.INVALID_REQUEST: 400,
    GateStatus.UNAVAILABLE: 503,
    GateStatus.INTERNAL_ERROR: 500,
}

EXPERIENCE_STATUS_TO_HTTP = {
    ExperienceWritebackStatus.ACCEPTED: 200,
    ExperienceWritebackStatus.DUPLICATE: 200,
    ExperienceWritebackStatus.INVALID_REQUEST: 400,
    ExperienceWritebackStatus.UNAVAILABLE: 503,
    ExperienceWritebackStatus.INTERNAL_ERROR: 500,
}


class RuntimeRequestHandler(BaseHTTPRequestHandler):
    """Request handler for the operational Neural Runtime API."""

    server_config: RuntimeConfig = RuntimeConfig.from_environment()
    query_service: Optional[NeuralQueryService] = None
    experience_service: Optional[NeuralExperienceService] = None

    def _send_json(self, status_code: int, payload: Dict[str, Any]) -> None:
        """Send JSON HTTP response with security and caching headers."""
        try:
            body = json.dumps(payload, indent=2, ensure_ascii=False).encode("utf-8")
        except Exception as e:
            body = json.dumps({"error": "SerializationError", "detail": str(e)}).encode("utf-8")
            status_code = 500

        self.send_response(status_code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Headers", "Authorization, Content-Type")
        self.send_header("Access-Control-Allow-Methods", "POST, GET, OPTIONS")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def _read_json_body(self) -> Dict[str, Any]:
        """Read and decode JSON request payload safely."""
        try:
            length = int(self.headers.get("Content-Length", 0))
            if length <= 0:
                return {}
            raw_body = self.rfile.read(length).decode("utf-8")
            return json.loads(raw_body)
        except json.JSONDecodeError as jde:
            raise ValueError(f"Malformed JSON payload: {jde}")
        except Exception as e:
            raise ValueError(f"Error reading request body: {e}")

    def _check_auth(self) -> None:
        """Validate bearer authorization against server config."""
        auth_header = self.headers.get("Authorization")
        verify_runtime_token(
            auth_header=auth_header,
            expected_token=self.server_config.auth_token,
            enforce_auth=self.server_config.enforce_auth,
        )

    def do_OPTIONS(self) -> None:
        """Handle CORS preflight requests."""
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Headers", "Authorization, Content-Type")
        self.send_header("Access-Control-Allow-Methods", "POST, GET, OPTIONS")
        self.send_header("Access-Control-Max-Age", "86400")
        self.end_headers()

    def do_GET(self) -> None:
        """Route GET requests (only health check is permitted; operational endpoints require POST)."""
        parsed = urlparse(self.path)
        path = parsed.path.rstrip("/")
        if not path:
            path = "/"

        if path == "/health":
            self._send_json(
                200,
                {
                    "status": "UP",
                    "service": "pub-neural-runtime-backend",
                    "version": "v0.1.0",
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                },
            )
            return

        if path in (
            "/api/v1/runtime/query",
            "/api/v1/runtime/experience",
            "/v1/query",
            "/v1/experience",
        ):
            self._send_json(
                405,
                {
                    "error": "Method Not Allowed",
                    "detail": f"Operational endpoint '{path}' requires HTTP POST.",
                },
            )
            return

        self._send_json(
            404,
            {
                "error": "NotFound",
                "detail": f"Path '{path}' does not match any runtime API route.",
            },
        )

    def do_POST(self) -> None:
        """Handle operational pre-task query and post-task experience writeback."""
        parsed = urlparse(self.path)
        path = parsed.path.rstrip("/")
        if not path:
            path = "/"

        # 1. Route validation
        if path not in (
            "/api/v1/runtime/query",
            "/api/v1/runtime/experience",
            "/v1/query",
            "/v1/experience",
        ):
            self._send_json(
                404,
                {
                    "error": "NotFound",
                    "detail": f"Path '{path}' does not match any operational runtime route.",
                },
            )
            return

        # 2. Authentication Check
        try:
            self._check_auth()
        except RuntimeAuthenticationError as ae:
            self._send_json(401, {"error": "Unauthorized", "detail": str(ae)})
            return
        except RuntimeAuthorizationError as az:
            self._send_json(403, {"error": "Forbidden", "detail": str(az)})
            return

        # 3. Read Body
        try:
            body = self._read_json_body()
        except ValueError as ve:
            self._send_json(400, {"status": "INVALID_REQUEST", "reason": str(ve)})
            return

        # 4. Route Execution
        if path in ("/api/v1/runtime/query", "/v1/query"):
            self._handle_query(body)
        elif path in ("/api/v1/runtime/experience", "/v1/experience"):
            self._handle_experience(body)

    def _handle_query(self, payload: Dict[str, Any]) -> None:
        """Dispatch query to real NeuralQueryService."""
        if not self.query_service:
            self._send_json(
                503,
                {
                    "status": GateStatus.UNAVAILABLE.value,
                    "reason": "NeuralQueryService is not initialized on server.",
                    "request_id": payload.get("request_id", payload.get("requestId", "unknown")),
                },
            )
            return

        try:
            response: NeuralQueryResponse = self.query_service.query(payload)
            http_status = GATE_STATUS_TO_HTTP.get(response.status, 500)
            self._send_json(http_status, response.to_dict())
        except Exception as e:
            req_id = payload.get("request_id", payload.get("requestId", "unknown"))
            self._send_json(
                500,
                {
                    "status": GateStatus.INTERNAL_ERROR.value,
                    "reason": f"Unexpected exception in runtime query handler: {e}",
                    "request_id": req_id,
                },
            )

    def _handle_experience(self, payload: Dict[str, Any]) -> None:
        """Dispatch experience writeback to real NeuralExperienceService."""
        if not self.experience_service:
            t_id = payload.get("taskId", payload.get("task_id", "unknown"))
            self._send_json(
                503,
                {
                    "status": ExperienceWritebackStatus.UNAVAILABLE.value,
                    "reason": "NeuralExperienceService is not initialized on server.",
                    "taskId": t_id,
                    "task_id": t_id,
                },
            )
            return

        try:
            result: ExperienceIngestionResult = self.experience_service.record(payload)
            http_status = EXPERIENCE_STATUS_TO_HTTP.get(result.status, 500)
            self._send_json(http_status, result.to_dict())
        except Exception as e:
            t_id = payload.get("taskId", payload.get("task_id", "unknown"))
            self._send_json(
                500,
                {
                    "status": ExperienceWritebackStatus.INTERNAL_ERROR.value,
                    "reason": f"Unexpected exception in runtime experience handler: {e}",
                    "taskId": t_id,
                    "task_id": t_id,
                },
            )

    def do_PUT(self) -> None:
        self._send_json(405, {"error": "Method Not Allowed", "detail": "PUT is not supported on Runtime API."})

    def do_DELETE(self) -> None:
        self._send_json(405, {"error": "Method Not Allowed", "detail": "DELETE is not supported on Runtime API."})

    def do_PATCH(self) -> None:
        self._send_json(405, {"error": "Method Not Allowed", "detail": "PATCH is not supported on Runtime API."})

    def log_message(self, format: str, *args: Any) -> None:
        """Suppress default stderr HTTP request logging in test/daemon modes."""
        pass


def create_runtime_server(
    config: Optional[RuntimeConfig] = None,
    query_service: Optional[NeuralQueryService] = None,
    experience_service: Optional[NeuralExperienceService] = None,
) -> HTTPServer:
    """Instantiate standard HTTP server configured for the Operational Runtime API."""
    cfg = config or RuntimeConfig.from_environment()
    RuntimeRequestHandler.server_config = cfg
    RuntimeRequestHandler.query_service = query_service
    RuntimeRequestHandler.experience_service = experience_service
    server = HTTPServer((cfg.host, cfg.port), RuntimeRequestHandler)
    return server
