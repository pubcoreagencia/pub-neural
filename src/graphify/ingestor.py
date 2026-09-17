"""
Graphify Ingestion Orchestrator for PUB Neural.
Translates normalized Graphify graphs into canonical PUB Neural events (ENTITY_EXTRACTED,
RELATION_EXTRACTED, EVIDENCE_CAPTURED), ensuring idempotency and bi-temporal preservation.
"""

from __future__ import annotations

import hashlib
import uuid
from typing import Any, Dict, List, Optional
from .normalizer import NormalizedGraph, NormalizedNode, NormalizedEdge, NormalizedEvidence


class GraphifyIngestor:
    """
    Ingests normalized Graphify representations into PUB Neural.
    Emits canonical events via PubNeuralClient or returns event batch for dry-run/mock execution.
    """

    def __init__(self, client: Optional[Any] = None):
        self.client = client

    def build_event_batch(self, graph: NormalizedGraph) -> Dict[str, Any]:
        """
        Build complete canonical event payload batch from NormalizedGraph without writing to DB.
        Useful for verification, dry-run, testing, and memory ingestion.
        """
        events: List[Dict[str, Any]] = []

        # 1. ENTITY_EXTRACTED Events
        for node in graph.nodes:
            payload = {
                "node_id": node.node_id,
                "entity_type": node.entity_type,
                "title": node.title,
                "slug": node.slug,
                "summary": node.summary,
                "content": node.content,
                "trust_zone": graph.trust_zone,
                "scope": "GLOBAL",
                "project_id": graph.project_id,
                "initial_state": node.initial_state,
                "confidence_score": node.confidence_score,
                "source_file": node.source_file,
                "source_location": node.source_location,
                "extractor_version": "graphify:v8",
                "commit_sha": graph.commit_sha,
                "repository": graph.repository,
            }
            events.append({
                "event_id": str(node.event_id),
                "event_type": "ENTITY_EXTRACTED",
                "stream_id": f"stream:entity:{node.node_id}",
                "payload": payload,
            })

        # 2. RELATION_EXTRACTED Events
        for edge in graph.edges:
            payload = {
                "source_id": edge.source_id,
                "relation_type": edge.relation_type,
                "target_id": edge.target_id,
                "weight": edge.weight,
                "confidence_score": edge.confidence_score,
                "confidence_tier": edge.confidence_tier,
                "is_bidirectional": edge.is_bidirectional,
                "trust_zone": graph.trust_zone,
                "scope": "GLOBAL",
                "project_id": graph.project_id,
                "source_file": edge.source_file,
                "extractor_version": "graphify:v8",
                "commit_sha": graph.commit_sha,
                "repository": graph.repository,
            }
            events.append({
                "event_id": str(edge.event_id),
                "event_type": "RELATION_EXTRACTED",
                "stream_id": f"stream:rel:{edge.source_id}->{edge.target_id}",
                "payload": payload,
            })

        # 3. Snapshot summary & deduplication metrics
        snapshot_id = hashlib.sha256(
            f"{graph.repository}:{graph.commit_sha}:{len(graph.nodes)}:{len(graph.edges)}".encode("utf-8")
        ).hexdigest()

        return {
            "snapshot_id": snapshot_id,
            "repository": graph.repository,
            "commit_sha": graph.commit_sha,
            "project_id": graph.project_id,
            "node_count": len(graph.nodes),
            "edge_count": len(graph.edges),
            "evidence_count": len(graph.evidence),
            "events": events,
        }

    def ingest(self, graph: NormalizedGraph) -> Dict[str, Any]:
        """
        Execute idempotent ingestion of NormalizedGraph into PUB Neural event stream.
        """
        batch = self.build_event_batch(graph)

        if not self.client:
            return {
                "status": "DRY_RUN",
                "snapshot_id": batch["snapshot_id"],
                "events_generated": len(batch["events"]),
                "nodes_count": batch["node_count"],
                "edges_count": batch["edge_count"],
            }

        # Real execution via PubNeuralClient
        events_emitted = 0
        events_deduplicated = 0

        for item in batch["events"]:
            ev_id = uuid.UUID(item["event_id"])
            idempotency_key = f"graphify:{ev_id}"

            existing = self.client.check_idempotency(idempotency_key)
            if existing:
                events_deduplicated += 1
                continue

            existing_ev = self.client.get_event_by_id(ev_id)
            if existing_ev:
                self.client.record_idempotency(
                    idempotency_key=idempotency_key,
                    request_hash=hashlib.sha256(idempotency_key.encode("utf-8")).hexdigest(),
                    resulting_event_id=ev_id,
                    response_payload=existing_ev["payload"],
                )
                events_deduplicated += 1
                continue

            # Append canonical event
            self.client.append_canonical_event(
                event_id=ev_id,
                event_type=item["event_type"],
                stream_id=item["stream_id"],
                payload=item["payload"],
                producer_version="graphify_adapter:v1.0.0",
            )
            self.client.record_idempotency(
                idempotency_key=idempotency_key,
                request_hash=hashlib.sha256(idempotency_key.encode("utf-8")).hexdigest(),
                resulting_event_id=ev_id,
                response_payload=item["payload"],
            )
            events_emitted += 1

        return {
            "status": "COMMITTED",
            "snapshot_id": batch["snapshot_id"],
            "events_emitted": events_emitted,
            "events_deduplicated": events_deduplicated,
            "total_events": len(batch["events"]),
        }
