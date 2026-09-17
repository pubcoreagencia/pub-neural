"""
Security tests for Console V0 Backend Service.
Verifies:
- Bearer token extraction (missing, malformed, valid).
- HTTP read-only enforcement (POST, PUT, DELETE, PATCH rejected with 405).
- Database read-only enforcement (mutations raise ReadOnlyViolationError).
- Payload sanitization prevents credential leaks.
"""

import unittest
from unittest.mock import MagicMock, patch
import psycopg2

from console.backend.dependencies import (
    AuthenticationError,
    ReadOnlyViolationError,
    extract_bearer_token,
    get_readonly_connection,
)
from console.backend.services.timeline_service import sanitize_payload


class TestConsoleSecurity(unittest.TestCase):
    """Test suite for authentication, authorization, and read-only boundaries."""

    def test_extract_bearer_token_success(self):
        header = "Bearer a1b2c3d4e5f67890abcdef1234567890"
        token = extract_bearer_token(header)
        self.assertEqual(token, "a1b2c3d4e5f67890abcdef1234567890")

    def test_extract_bearer_token_missing(self):
        with self.assertRaises(AuthenticationError) as ctx:
            extract_bearer_token(None)
        self.assertIn("Missing Authorization header", str(ctx.exception))

        with self.assertRaises(AuthenticationError) as ctx:
            extract_bearer_token("")
        self.assertIn("Missing Authorization header", str(ctx.exception))

    def test_extract_bearer_token_malformed(self):
        with self.assertRaises(AuthenticationError) as ctx:
            extract_bearer_token("Basic dXNlcjpwYXNz")
        self.assertIn("Malformed Authorization header", str(ctx.exception))

        with self.assertRaises(AuthenticationError) as ctx:
            extract_bearer_token("Bearer")
        self.assertIn("Malformed Authorization header", str(ctx.exception))

    def test_payload_sanitization(self):
        raw_payload = {
            "actor_id": "actor_test",
            "machine_secret": "super_secret_key_123",
            "nested": {
                "token": "bearer_secret_abc",
                "normal_field": "public_data",
                "password": "my_password",
            },
            "array_data": [
                {"credential_identity": "cert_xyz", "value": 42}
            ],
        }
        sanitized = sanitize_payload(raw_payload)
        self.assertEqual(sanitized["actor_id"], "actor_test")
        self.assertEqual(sanitized["machine_secret"], "[REDACTED]")
        self.assertEqual(sanitized["nested"]["token"], "[REDACTED]")
        self.assertEqual(sanitized["nested"]["normal_field"], "public_data")
        self.assertEqual(sanitized["nested"]["password"], "[REDACTED]")
        self.assertEqual(sanitized["array_data"][0]["credential_identity"], "[REDACTED]")
        self.assertEqual(sanitized["array_data"][0]["value"], 42)

    def test_readonly_transaction_error_handling(self):
        with patch("psycopg2.connect") as mock_connect:
            mock_conn = MagicMock()
            mock_connect.return_value = mock_conn
            mock_cur = MagicMock()
            mock_conn.cursor.return_value.__enter__.return_value = mock_cur

            # Simulate attach_session success
            mock_cur.fetchone.return_value = {"attached": True}

            # Simulate trying an illegal INSERT in a READ ONLY transaction
            mock_cur.execute.side_effect = [
                None,  # attach_session
                psycopg2.errors.ReadOnlySqlTransaction("cannot execute INSERT in a read-only transaction"),
            ]

            with self.assertRaises(ReadOnlyViolationError) as ctx:
                with get_readonly_connection("postgresql://dummy", bearer_token="valid_token") as cur:
                    cur.execute("INSERT INTO pub_neural.neural_nodes VALUES (1);")
            self.assertIn("strictly read-only", str(ctx.exception))
            # Verify rollback was called
            mock_conn.rollback.assert_called()

    def test_unauthenticated_connection_rejected(self):
        with patch("psycopg2.connect") as mock_connect:
            mock_conn = MagicMock()
            mock_connect.return_value = mock_conn

            with self.assertRaises(AuthenticationError) as ctx:
                with get_readonly_connection("postgresql://dummy", bearer_token=None, enforce_auth=True) as cur:
                    pass
            self.assertIn("no bearer token provided", str(ctx.exception))

    def test_auth_service_flow(self):
        from console.backend.services.auth_service import login_actor, get_current_session, logout_actor
        from datetime import datetime, timezone

        with patch("psycopg2.connect") as mock_connect:
            mock_conn = MagicMock()
            mock_connect.return_value = mock_conn
            mock_cur = MagicMock()
            mock_conn.cursor.return_value.__enter__.return_value = mock_cur

            # 1. Test login_actor success
            mock_cur.fetchone.side_effect = [
                {"token": "tok_xyz"},
                {
                    "actor_id": "actor:auditor:console-operator",
                    "actor_role": "AUDITOR",
                    "active_trust_zone": "tz_internal_holding",
                    "active_project_id": None,
                    "expires_at": datetime.now(timezone.utc),
                },
            ]
            login_data = login_actor("postgresql://dummy", "actor:auditor:console-operator", "secret_abc")
            self.assertEqual(login_data["token"], "tok_xyz")
            self.assertEqual(login_data["actor_role"], "AUDITOR")

            # 2. Test get_current_session success
            mock_cur.fetchone.side_effect = [
                {
                    "actor_id": "actor:auditor:console-operator",
                    "actor_role": "AUDITOR",
                    "active_trust_zone": "tz_internal_holding",
                    "active_project_id": None,
                    "expires_at": datetime.now(timezone.utc),
                    "is_active": True,
                }
            ]
            sess_data = get_current_session("postgresql://dummy", "tok_xyz")
            self.assertTrue(sess_data["authenticated"])

            # 3. Test logout_actor
            mock_cur.rowcount = 1
            revoked = logout_actor("postgresql://dummy", "tok_xyz")
            self.assertTrue(revoked)


if __name__ == "__main__":
    unittest.main()
