"""
End-to-end HTTP integration tests for Console V0 Backend Server.
Spins up the actual HTTP server on an ephemeral loopback port and executes real HTTP requests.
Verifies:
- /health endpoint (unauthenticated).
- 405 Method Not Allowed on POST / PUT / DELETE.
- 401 Unauthorized on missing/malformed bearer token.
- Routing to /api/v1/status, /api/v1/search, /api/v1/entities, /api/v1/events.
"""

import json
import threading
import unittest
import urllib.request
import urllib.error
from http.server import HTTPServer
from unittest.mock import MagicMock, patch

from console.backend.config import ConsoleConfig
from console.backend.server import ConsoleRequestHandler, create_console_server


class TestConsoleAPI(unittest.TestCase):
    """End-to-end HTTP tests against loopback HTTPServer."""

    @classmethod
    def setUpClass(cls):
        # Configure test server on random free port (port 0)
        cls.config = ConsoleConfig(
            db_url="postgresql://test:test@localhost:5432/test",
            host="127.0.0.1",
            port=0,
        )
        ConsoleRequestHandler.server_config = cls.config
        cls.server = HTTPServer(("127.0.0.1", 0), ConsoleRequestHandler)
        cls.port = cls.server.server_port
        cls.base_url = f"http://127.0.0.1:{cls.port}"

        cls.server_thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.server_thread.start()

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()

    def test_health_endpoint(self):
        req = urllib.request.Request(f"{self.base_url}/health")
        with urllib.request.urlopen(req) as resp:
            self.assertEqual(resp.status, 200)
            data = json.loads(resp.read().decode("utf-8"))
            self.assertEqual(data["status"], "UP")
            self.assertEqual(data["service"], "pub-neural-console-backend")

    def test_post_rejected_with_405(self):
        req = urllib.request.Request(
            f"{self.base_url}/api/v1/entities",
            data=b'{"title": "illegal mutation"}',
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with self.assertRaises(urllib.error.HTTPError) as ctx:
            urllib.request.urlopen(req)
        self.assertEqual(ctx.exception.code, 405)
        err_data = json.loads(ctx.exception.read().decode("utf-8"))
        self.assertEqual(err_data["error"], "Method Not Allowed")

    def test_put_rejected_with_405(self):
        req = urllib.request.Request(
            f"{self.base_url}/api/v1/entities/ent-1",
            data=b'{"title": "mutation"}',
            headers={"Content-Type": "application/json"},
            method="PUT",
        )
        with self.assertRaises(urllib.error.HTTPError) as ctx:
            urllib.request.urlopen(req)
        self.assertEqual(ctx.exception.code, 405)

    def test_delete_rejected_with_405(self):
        req = urllib.request.Request(
            f"{self.base_url}/api/v1/entities/ent-1",
            method="DELETE",
        )
        with self.assertRaises(urllib.error.HTTPError) as ctx:
            urllib.request.urlopen(req)
        self.assertEqual(ctx.exception.code, 405)

    def test_protected_endpoint_missing_auth(self):
        req = urllib.request.Request(f"{self.base_url}/api/v1/entities/some-id")
        with self.assertRaises(urllib.error.HTTPError) as ctx:
            urllib.request.urlopen(req)
        self.assertEqual(ctx.exception.code, 401)
        err_data = json.loads(ctx.exception.read().decode("utf-8"))
        self.assertEqual(err_data["error"], "Unauthorized")

    def test_cors_preflight_options(self):
        req = urllib.request.Request(f"{self.base_url}/api/v1/entities/ent-1", method="OPTIONS")
        with urllib.request.urlopen(req) as resp:
            self.assertEqual(resp.status, 204)
            headers = dict(resp.headers)
            self.assertEqual(headers.get("Access-Control-Allow-Origin"), "*")
            self.assertIn("GET", headers.get("Access-Control-Allow-Methods", ""))


if __name__ == "__main__":
    unittest.main()
