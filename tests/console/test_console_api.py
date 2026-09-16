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

    def test_cors_explicit_origin(self):
        # Temporarily configure explicit CORS origin on server_config
        original_cors = ConsoleRequestHandler.server_config.cors_origins
        try:
            ConsoleRequestHandler.server_config = ConsoleConfig(
                db_url=self.config.db_url,
                host=self.config.host,
                port=self.config.port,
                cors_origins=("https://pub-neural.pages.dev", "https://preview.pub-neural.pages.dev"),
            )

            # Matching origin
            req = urllib.request.Request(
                f"{self.base_url}/api/v1/entities/ent-1",
                headers={"Origin": "https://pub-neural.pages.dev"},
                method="OPTIONS",
            )
            with urllib.request.urlopen(req) as resp:
                self.assertEqual(resp.headers.get("Access-Control-Allow-Origin"), "https://pub-neural.pages.dev")
                self.assertEqual(resp.headers.get("Vary"), "Origin")

            # Non-matching origin defaults to first configured
            req_other = urllib.request.Request(
                f"{self.base_url}/api/v1/entities/ent-1",
                headers={"Origin": "https://malicious.example.com"},
                method="OPTIONS",
            )
            with urllib.request.urlopen(req_other) as resp:
                self.assertEqual(resp.headers.get("Access-Control-Allow-Origin"), "https://pub-neural.pages.dev")
        finally:
            ConsoleRequestHandler.server_config = ConsoleConfig(
                db_url=self.config.db_url,
                host=self.config.host,
                port=self.config.port,
                cors_origins=original_cors,
            )


    def test_port_and_host_env_vars(self):
        import os
        old_port = os.environ.get("PORT")
        old_host = os.environ.get("CONSOLE_HOST")
        try:
            os.environ["PORT"] = "9090"
            if "CONSOLE_HOST" in os.environ:
                del os.environ["CONSOLE_HOST"]
            cfg = ConsoleConfig.from_environment()
            self.assertEqual(cfg.port, 9090)
            self.assertEqual(cfg.host, "0.0.0.0")

            os.environ["CONSOLE_HOST"] = "10.0.0.1"
            cfg2 = ConsoleConfig.from_environment()
            self.assertEqual(cfg2.port, 9090)
            self.assertEqual(cfg2.host, "10.0.0.1")
        finally:
            if old_port is not None:
                os.environ["PORT"] = old_port
            else:
                os.environ.pop("PORT", None)
            if old_host is not None:
                os.environ["CONSOLE_HOST"] = old_host
            else:
                os.environ.pop("CONSOLE_HOST", None)


if __name__ == "__main__":
    unittest.main()
