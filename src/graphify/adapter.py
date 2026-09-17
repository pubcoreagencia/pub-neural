"""
Graphify External Adapter for PUB Neural.
Handles isolated execution, output reading, security scanning, and size cap enforcement.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
import re
import subprocess
from typing import Any, Dict, List, Optional


class GraphifyExecutionError(Exception):
    """Raised when external Graphify execution or parsing fails."""


class GraphifySecurityError(Exception):
    """Raised when sensitive data or secret leakage is detected in graph output."""


# Default maximum allowed graph.json file size (10 MB)
MAX_GRAPH_BYTES = 10 * 1024 * 1024

# Patterns indicative of credentials, secrets, or private keys that must NEVER be ingested
FORBIDDEN_PATTERNS = [
    re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----", re.IGNORECASE),
    re.compile(r"(?:api[_-]?key|auth[_-]?token|secret[_-]?key|password)\s*[:=]\s*['\"][^\s'\"]{8,}['\"]", re.IGNORECASE),
    re.compile(r"(?:ghp|gho|ghu|ghs|ghr)_[A-Za-z0-9_]{36,}", re.IGNORECASE),
]

FORBIDDEN_FILENAMES = {
    ".env",
    ".env.local",
    ".env.production",
    "id_rsa",
    "id_ed25519",
    "credentials.json",
    "service_account.json",
}


class GraphifyAdapter:
    """
    Adapter interfacing between PUB Neural and external Graphify engine.
    Decoupled via JSON or subprocess execution without monkeypatching runtime.
    """

    def __init__(
        self,
        graphify_bin: str = "graphify",
        max_bytes: int = MAX_GRAPH_BYTES,
        timeout_seconds: int = 120,
    ):
        self.graphify_bin = graphify_bin
        self.max_bytes = max_bytes
        self.timeout_seconds = timeout_seconds

    def parse_graph_json(self, json_path: str | Path) -> Dict[str, Any]:
        """
        Safely load, validate, and security-scan an existing graph.json output.
        Enforces size caps, strict JSON validation, and secret denial.
        """
        path = Path(json_path).resolve()
        if not path.exists():
            raise GraphifyExecutionError(f"Graph file not found: {path}")

        file_size = path.stat().st_size
        if file_size > self.max_bytes:
            raise GraphifyExecutionError(
                f"Graph file size {file_size} exceeds maximum allowable cap {self.max_bytes} bytes."
            )

        try:
            content = path.read_text(encoding="utf-8")
        except Exception as e:
            raise GraphifyExecutionError(f"Failed to read graph file: {e}") from e

        # Security Scan: Fail-closed on forbidden secrets
        self.validate_content_safety(content)

        try:
            data = json.loads(content)
        except json.JSONDecodeError as exc:
            raise GraphifyExecutionError(f"Malformed graph.json: {exc}") from exc

        if not isinstance(data, dict):
            raise GraphifyExecutionError("Invalid graph.json structure: root must be a dictionary.")

        # Ensure minimal required keys
        if "nodes" not in data:
            raise GraphifyExecutionError("Invalid graph.json: missing 'nodes' array.")

        links = data.get("links")
        if links is None:
            links = data.get("edges")
        if links is None or not isinstance(links, list):
            raise GraphifyExecutionError("Invalid graph.json: missing 'links' or 'edges' array.")

        data["links"] = links

        # Verify no forbidden file names in node sources
        for node in data["nodes"]:
            source_file = node.get("source_file", "")
            base = os.path.basename(source_file)
            if base in FORBIDDEN_FILENAMES or base.startswith(".env"):
                raise GraphifySecurityError(
                    f"Forbidden file source detected in node {node.get('id')}: {source_file}"
                )

        return data

    def execute_extraction(
        self,
        target_dir: str | Path,
        output_dir: Optional[str | Path] = None,
    ) -> Dict[str, Any]:
        """
        Execute Graphify as an external subprocess against target_dir and parse output.
        """
        target_path = Path(target_dir).resolve()
        if not target_path.exists():
            raise GraphifyExecutionError(f"Target directory does not exist: {target_path}")

        out_path = Path(output_dir) if output_dir else target_path / "graphify-out"
        graph_file = out_path / "graph.json"

        cmd = [self.graphify_bin, "extract", str(target_path)]
        env = os.environ.copy()
        env["GRAPHIFY_OUT"] = str(out_path)

        try:
            res = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=self.timeout_seconds,
                env=env,
            )
            if res.returncode != 0:
                raise GraphifyExecutionError(
                    f"Graphify extraction failed (exit {res.returncode}): {res.stderr.strip()}"
                )
        except FileNotFoundError:
            raise GraphifyExecutionError(
                f"Graphify binary '{self.graphify_bin}' not found in environment PATH."
            )
        except subprocess.TimeoutExpired as exc:
            raise GraphifyExecutionError(
                f"Graphify extraction timed out after {self.timeout_seconds} seconds."
            ) from exc

        return self.parse_graph_json(graph_file)

    @staticmethod
    def validate_content_safety(raw_text: str) -> None:
        """Scan raw graph payload for credentials or private keys."""
        for pat in FORBIDDEN_PATTERNS:
            if pat.search(raw_text):
                raise GraphifySecurityError(
                    "Security violation: Sensitive credential or private key pattern detected in graph payload."
                )
