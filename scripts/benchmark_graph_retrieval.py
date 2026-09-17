#!/usr/bin/env python3
"""
Micro-benchmark script comparing:
A. Existing Retrieval (Lexical + Dense Vector)
B. Graph Retrieval (Topological / Neighborhood)
C. 3-Way Hybrid Retrieval (Lexical + Dense + Graph)
"""

import time
from src.retrieval.graph_search import GraphSearchEngine
from src.retrieval.hybrid_search import HybridSearchEngine
from src.retrieval.abstention import RetrievalAbstentionPolicy


class BenchmarkEmbeddingProvider:
    def __init__(self, dim=1536):
        self.model_id = "bench-dim1536"
        self.dim = dim

    def generate_embedding(self, text: str):
        # Deterministic synthetic vector
        return [0.01 * (i % 10) for i in range(self.dim)]


def run_benchmark():
    print("==========================================================")
    print(" PUB NEURAL — RETRIEVAL MODALITY BENCHMARK EVALUATION")
    print("==========================================================")

    # Synthetic corpus with connected knowledge graph
    nodes = [
        {
            "id": f"node:component:{i}",
            "title": f"Component Service {i}",
            "summary": f"Service handling domain operations {i} and authentication security.",
            "content": f"Implementation details for component {i}.",
            "trust_zone": "tz_internal_holding",
            "project_id": "pub-neural",
            "originating_event_id": f"evt-{i}",
            "content_hash": f"hash-{i}",
        }
        for i in range(50)
    ]
    edges = [
        {
            "source_id": f"node:component:{i}",
            "target_id": f"node:component:{(i + 1) % 50}",
            "relation_type": "USES" if i % 2 == 0 else "DEPENDS_ON",
            "weight": 1.0,
        }
        for i in range(50)
    ]

    graph_engine = GraphSearchEngine()
    hybrid_engine = HybridSearchEngine(
        db_url="postgresql://mock",
        embedding_provider=BenchmarkEmbeddingProvider(),
        rrf_k=60,
        graph_weight=0.8,
        graph_engine=graph_engine,
        abstention_policy=RetrievalAbstentionPolicy.disabled(),
    )

    query = "authentication security"

    # Pre-generate lexical and dense candidates
    lexical_candidates = [
        {
            "target_id": f"node:component:{i}",
            "target_type": "NODE",
            "title": f"Component Service {i}",
            "snippet": f"Service handling domain operations {i}",
            "lexical_rank": i + 1,
            "trust_zone": "tz_internal_holding",
            "project_id": "pub-neural",
            "originating_event_id": f"evt-{i}",
            "content_hash": f"hash-{i}",
            "evidence_id": None,
            "source_id": None,
        }
        for i in range(15)
    ]

    dense_candidates = [
        {
            "target_id": f"node:component:{14 - i}",
            "target_type": "NODE",
            "title": f"Component Service {14 - i}",
            "snippet": f"Service handling domain operations {14 - i}",
            "dense_rank": i + 1,
            "cosine_distance": 0.05 + 0.02 * i,
            "trust_zone": "tz_internal_holding",
            "project_id": "pub-neural",
            "originating_event_id": f"evt-{14 - i}",
            "content_hash": f"hash-{14 - i}",
            "evidence_id": None,
            "source_id": None,
        }
        for i in range(15)
    ]

    # Mode A: Existing (Lexical + Dense)
    t0 = time.perf_counter()
    iterations = 1000
    for _ in range(iterations):
        res_a = hybrid_engine._fuse_rrf(lexical_candidates, dense_candidates, graph_results=None)
    lat_a = (time.perf_counter() - t0) / iterations * 1000

    # Mode B: Graph Only
    t0 = time.perf_counter()
    for _ in range(iterations):
        res_b = graph_engine.search_graph(
            query=query, limit=15, in_memory_nodes=nodes, in_memory_edges=edges
        )
    lat_b = (time.perf_counter() - t0) / iterations * 1000

    # Mode C: 3-Way Hybrid (Lexical + Dense + Graph)
    graph_candidates = graph_engine.search_graph(
        query=query, limit=15, in_memory_nodes=nodes, in_memory_edges=edges
    )
    t0 = time.perf_counter()
    for _ in range(iterations):
        res_c = hybrid_engine._fuse_rrf(lexical_candidates, dense_candidates, graph_candidates)
    lat_c = (time.perf_counter() - t0) / iterations * 1000

    print(f"Mode A (Lexical + Dense):     Latency: {lat_a:.3f} ms | Candidates Fused: {len(res_a)}")
    print(f"Mode B (Graph Only):          Latency: {lat_b:.3f} ms | Candidates Traversed: {len(res_b)}")
    print(f"Mode C (3-Way Hybrid Fusion): Latency: {lat_c:.3f} ms | Final Fused Set: {len(res_c)}")
    print("----------------------------------------------------------")
    print("Top 3 Mode C Results with Structural Provenance:")
    for r in res_c[:3]:
        print(f" - [{r.target_id}] RRF: {r.rrf_score:.5f} | Lexical: #{r.lexical_rank} | Dense: #{r.dense_rank} | Graph: #{r.graph_rank} | Explanation: {r.structural_explanation}")
    print("==========================================================")


if __name__ == "__main__":
    run_benchmark()
