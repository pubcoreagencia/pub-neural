"""
Tests for Graphify Ingestor and Adapter.
Verifies batch generation, idempotency, adapter security guards, and failure handling.
"""

import json
import tempfile
import unittest
from pathlib import Path

from src.graphify.adapter import GraphifyAdapter, GraphifyExecutionError, GraphifySecurityError
from src.graphify.ingestor import GraphifyIngestor
from src.graphify.normalizer import GraphifyNormalizer


class MockPubNeuralClient:
    def __init__(self):
        self.events = []
        self.idempotency = {}

    def check_idempotency(self, key):
        return self.idempotency.get(key)

    def record_idempotency(self, idempotency_key, request_hash, resulting_event_id, response_payload):
        self.idempotency[idempotency_key] = {
            "resulting_event_id": str(resulting_event_id),
            "response_payload": response_payload,
        }

    def get_event_by_id(self, event_id):
        for e in self.events:
            if str(e["event_id"]) == str(event_id):
                return e
        return None

    def append_canonical_event(self, event_id, event_type, stream_id, payload, producer_version="v1.0.0"):
        self.events.append({
            "event_id": str(event_id),
            "event_type": event_type,
            "stream_id": stream_id,
            "payload": payload,
        })
        return len(self.events)


class TestGraphifyIngestion(unittest.TestCase):

    def setUp(self):
        self.normalizer = GraphifyNormalizer(project_id="pub-neural")
        self.fixture_path = Path(__file__).resolve().parent.parent / "fixtures" / "graphify_sample.json"
        with open(self.fixture_path, "r", encoding="utf-8") as f:
            self.sample_data = json.load(f)
        self.normalized = self.normalizer.normalize(self.sample_data, commit_sha="comm-001")

    def test_build_event_batch(self):
        ingestor = GraphifyIngestor(client=None)
        batch = ingestor.build_event_batch(self.normalized)

        self.assertEqual(batch["node_count"], 4)
        self.assertEqual(batch["edge_count"], 3)
        self.assertEqual(len(batch["events"]), 7)
        self.assertTrue(bool(batch["snapshot_id"]))

    def test_idempotent_ingestion_with_mock_client(self):
        client = MockPubNeuralClient()
        ingestor = GraphifyIngestor(client=client)

        # Run 1: Emit all events
        res1 = ingestor.ingest(self.normalized)
        self.assertEqual(res1["status"], "COMMITTED")
        self.assertEqual(res1["events_emitted"], 7)
        self.assertEqual(res1["events_deduplicated"], 0)
        self.assertEqual(len(client.events), 7)

        # Run 2: Full deduplication, 0 new events
        res2 = ingestor.ingest(self.normalized)
        self.assertEqual(res2["status"], "COMMITTED")
        self.assertEqual(res2["events_emitted"], 0)
        self.assertEqual(res2["events_deduplicated"], 7)
        self.assertEqual(len(client.events), 7)

    def test_adapter_security_blocks_private_key(self):
        adapter = GraphifyAdapter()
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as tf:
            tf.write(json.dumps({
                "nodes": [{"id": "key", "source_file": "secret.txt"}],
                "links": [],
                "secret": "-----BEGIN RSA PRIVATE KEY-----\nMIIEowIBAAKCAQEA0...",
            }))
            tf_path = tf.name

        try:
            with self.assertRaises(GraphifySecurityError):
                adapter.parse_graph_json(tf_path)
        finally:
            Path(tf_path).unlink(missing_ok=True)

    def test_adapter_security_blocks_env_file_source(self):
        adapter = GraphifyAdapter()
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as tf:
            tf.write(json.dumps({
                "nodes": [{"id": "node-1", "source_file": ".env.production"}],
                "links": [],
            }))
            tf_path = tf.name

        try:
            with self.assertRaises(GraphifySecurityError):
                adapter.parse_graph_json(tf_path)
        finally:
            Path(tf_path).unlink(missing_ok=True)

    def test_adapter_rejects_missing_or_malformed_file(self):
        adapter = GraphifyAdapter()
        with self.assertRaises(GraphifyExecutionError):
            adapter.parse_graph_json("/non/existent/path/graph.json")


if __name__ == "__main__":
    unittest.main()
