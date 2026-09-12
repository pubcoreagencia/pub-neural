# PUB Neural / PDL — Vector Indexing & Lifecycle Specification (V0.1)

**Status:** IMPLEMENTED & OPERATIONAL  
**Component:** `VectorIndexingWorker` & `MockDeterministicEmbeddingProvider`  
**Security Invariant:** Projections and Vectors are strictly derived; Event Log and Source Blobs are the sole canonical sources.

---

## 1. Vector Lifecycle & Invariants

```text
CANONICAL EVENT LOG (neural_events)
            ↓
   PROJECTOR (run_projector)
            ↓
KNOWLEDGE GRAPH PROJECTIONS (neural_nodes, neural_evidence, neural_fts)
            ↓
VECTOR DERIVATION WORKER (VectorIndexingWorker)
            ↓
DERIVED AI ARTIFACTS (neural_vectors)
```

1. **Non-Canonical Artifact Status:** `neural_vectors` is a derived artifact table. If truncated, 100% of state can be reconstructed by running `sync_all_projections()`.
2. **Crash & Restart Resilience:** Tested via `VECTOR-07` with `SIGKILL` delivery. The worker cleanly resumes without duplicate records or broken lineages.
3. **Rebuild Determinism:** Verified via `VECTOR-08`: `SNAPSHOT_A == SNAPSHOT_B` across all vector records.

---

## 2. Performance Baseline Measurements (Container Environment)

Measured on 100 synthetic knowledge graph entities:
- **Vector Sync Throughput:** 100 nodes embedded and persisted in **1.039s** (~96 vectors/sec).
- **Hybrid Search Latency (FTS + Dense HNSW + RRF):** **27.9ms** end-to-end query time.
- **Pure Lexical Search Latency:** **3.2ms**.
- **Pure Dense Cosine Search Latency:** **6.4ms**.
