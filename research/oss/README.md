# PUB NEURAL — OSS ARCHITECTURAL INTELLIGENCE & RESEARCH

## 1. Purpose & Scope
This directory contains architectural research, technical comparisons, and governance decisions regarding external open-source software (OSS) evaluated for the PUB Neural ecosystem.

---

## 2. Critical Source-of-Truth Rule

> [!IMPORTANT]
> **OSS research artifacts are references and benchmark specifications only.**
> 
> They are **NOT**:
> * A source of truth for PUB Neural;
> * Runtime dependencies (unless explicitly adopted in the presentation layer);
> * An authority over PUB Neural architecture or governance;
> * Governance mechanisms or approval authorities;
> * A replacement for Git version control;
> * A replacement for PostgreSQL 16 + pgvector;
> * A replacement for the canonical PUB Neural ontology (16 entity types, 14 relation types).

---

## 3. Decision Framework & Taxonomy

To prevent architectural drift and dependency pollution, all evaluated projects are categorized into strictly distinct decision types:

1. **`CODE ADOPTION`**: Actual code or library dependency integrated into a specific subsystem (e.g., UI component in the presentation layer).
2. **`ALGORITHMIC INSPIRATION`**: Mathematical, algorithmic, or prompt-engineering patterns ported to run natively on PUB Neural's PostgreSQL/Python stack, with zero vendor code or external database dependencies.
3. **`ARCHITECTURAL REFERENCE`**: Structural patterns, schemas, or API ergonomics studied to inform internal designs without adopting code or algorithms.
4. **`REJECT`**: Incompatible paradigms, conflicting storage engines, or unneeded operational complexity explicitly prohibited from entering the codebase.

---

## 4. Audited Projects & Decisions Summary

| Project | Repository | Decision Type | Classification | Target Scope |
| :--- | :--- | :--- | :--- | :--- |
| **React Flow** | `xyflow/xyflow` | **CODE ADOPTION** | `ADOPT — presentation layer` | Future PUB Neural Console (Graph View) |
| **Graphiti** | `getzep/graphiti` | **ALGORITHMIC INSPIRATION** | `INSPIRE — temporal/contradiction patterns` | Future Candidate Invalidation Worker |
| **GraphRAG** | `microsoft/graphrag` | **ALGORITHMIC INSPIRATION** | `INSPIRE — community detection / global retrieval patterns` | Future Background Leiden Worker |
| **Mem0** | `mem0ai/mem0` | **ARCHITECTURAL REFERENCE** | `INSPIRE — memory extraction / agent ergonomics` | Future Gate Client SDK Ergonomics |
| **Apache AGE** | `apache/age` | **ARCHITECTURAL REFERENCE** | `INSPIRE — openCypher in relational SQL` | Reference only (Relational CTEs retained) |
| **pyeventsourcing** | `pyeventsourcing/eventsourcing` | **ARCHITECTURAL REFERENCE** | `INSPIRE — DDD event-sourcing / OCC` | Reference only (PL/pgSQL engine retained) |
| **Marquez** | `MarquezProject/marquez` | **ARCHITECTURAL REFERENCE** | `INSPIRE — OpenLineage derivation DAGs` | Reference for provenance schemas |
| **Letta** | `letta-ai/letta` | **ARCHITECTURAL REFERENCE** | `INSPIRE — Tiered agent memory on PG16` | Reference for memory lifecycle |
| **TerminusDB** | `terminusdb/terminusdb` | **REJECT** | `REJECT — incompatible standalone stack` | Prohibited (Rust/Prolog standalone) |

---

## 5. Architectural Decision: PUB Neural Console V0

```text
STATUS: NOT IMPLEMENTED / FUTURE SPECIFICATION
```

* **Role:** Read-only visual presentation layer for inspecting knowledge nodes, bi-temporal windows, provenance traces, and system health.
* **Initial Graph Visualization Motor:** `@xyflow/react` (`xyflow/xyflow`).
* **Layout Calculation Engines (External):**
  * `@dagrejs/dagre`: Directed hierarchical layouts (for Lineage & Provenance DAGs).
  * `d3-force`: Physics force-directed simulation (for Organic Knowledge Graph Explorer).
* **Boundaries:** The Console connects strictly via read-only SQL queries with session bearer tokens. It possesses zero authority to bypass Row-Level Security (RLS) or mutate the canonical event ledger.

---

## 6. Future Benchmarks (Planned / Not Implemented)

The following benchmark specifications are defined for empirical validation during future phases:

### Benchmark A: Graphiti Temporal Contradiction Handling
* **Status:** `FUTURE / NOT IMPLEMENTED`
* **Focus:** Port Graphiti's `dedupe_edges.py` prompt heuristics to a background worker; test precision of setting `invalid_at` / `superseded_by` on conflicting assertions without Neo4j.

### Benchmark B: GraphRAG Hierarchical Leiden
* **Status:** `FUTURE / NOT IMPLEMENTED`
* **Focus:** Execute `graspologic_native` hierarchical Leiden clustering against relational node/edge dumps; evaluate modularity and token costs of populating `pub_neural.neural_community_reports`.

### Benchmark C: PUB Neural RRF vs. Alternative Retrieval
* **Status:** `FUTURE / NOT IMPLEMENTED`
* **Focus:** Quantify recall and nDCG of PUB Neural's two-leg independent RRF (PostgreSQL FTS + pgvector Cosine) against vector-only candidate selection with sparse reranking.

### Benchmark D: React Flow vs. Cytoscape.js Rendering
* **Status:** `FUTURE / NOT IMPLEMENTED`
* **Focus:** Benchmark client-side frame rates (FPS) and memory footprints when rendering 250, 500, 1,000, and 2,500 custom entity cards during pan and zoom.

---

## 7. Operational & Architectural Invariants

* **Single Operational Database:** PostgreSQL 16+ with `pgvector` and `pgcrypto`. External graph engines (Neo4j, FalkorDB) or columnar stores (LanceDB, Parquet) are strictly prohibited.
* **Append-Only Event Store:** `pub_neural.neural_events` is immutable; physical deletions or in-place mutations are rejected by database triggers.
* **Sovereign Governance:** Database Row-Level Security (RLS), actor roles, and CEO sovereignty override all application-level logic.
* **No Overclaiming:**
  * Background Leiden worker: `NOT IMPLEMENTED`
  * Interactive Console: `NOT IMPLEMENTED`
  * HTTP / REST / MCP transport: `NOT IMPLEMENTED` (CLI bridge runner is the canonical boundary)
  * Real-time network integration: `NOT IMPLEMENTED`
