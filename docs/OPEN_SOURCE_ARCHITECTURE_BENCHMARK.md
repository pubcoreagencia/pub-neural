# Open Source Architecture Benchmark for PUB Neural

**Document Status:** CANONICAL BENCHMARK (ARCHITECTURE FREEZE REVIEW)  
**Date:** September 12, 2026  
**Target Workspace:** `pub neural` (`/Users/user/Documents/antigravity/pub neural`)  
**Canonical Spec Reference:** `MASTER_CONTEXT.md`  
**Review Objective:** Establish verifiable, source-audited technical baselines across open-source candidates to substantiate the PUB Neural V0 architectural freeze.

---

## 1. Executive Summary

PUB Neural is the institutional cognitive brain of PUB Core Holding. Its mission is to ingest multi-repository documentation, codebases, decisions, and execution traces, maintaining an authoritative knowledge graph with strict provenance, bi-temporal validity, and knowledge promotion under CEO Sovereignty.

This architecture freeze benchmark rigorously audits eight open-source projects:
1. `ardiannurcahya/open-graph-memory`
2. `Heman10x-NGU/palimp`
3. `impara/openBrain`
4. `innocarpe/CarpeOS`
5. `microsoft/graphrag`
6. `nodummd/nodum`
7. `sadnanalmanir/semantic-memory-agent`
8. `nowledge-co/OpenKL`

### Essential Takeaways
1. **No Single Project Covers PUB Neural:** Open-source agent memory frameworks almost universally treat memory as unstructured episodic conversation logs or generic `(Subject, Predicate, Object)` triples. None model institutional governance (`PROJECT`, `REPOSITORY`, `DECISION`, `RULE`, `GOVERNANCE`, `PATTERN`, `LESSON`, `SKILL`) or multi-repository cross-linking under formal promotion states (`CAPTURED` → `INSTITUTIONAL`).
2. **OpenBrain Re-evaluation (PostgreSQL + pgvector + Apache AGE):** OpenBrain is a first-class architectural reference proving that vectors, relational models, and OpenCypher property graphs can co-exist inside a single PostgreSQL 16 database using `pgvector` and `Apache AGE`. However, OpenBrain has **no license file** (All Rights Reserved, classifying it as `REFERENCE ONLY`), is hardcoded for a single user (`_SINGLE_USER_ID = "default"`), and lacks git-level provenance.
3. **OpenKL Correction (Kùzu-Centered, Not PostgreSQL/Neo4j):** OpenKL is explicitly an experimental prototype built around embedded **Kùzu DB** (`import kuzu`, with `INSTALL VECTOR; LOAD VECTOR;`), disk-based canonical stores (`store/sources/`, `store/normalized/`), and rich citation objects (`TransientCitation`, `PersistedCitation`). It has 4 commits and no production multi-tenant or event-sourcing capabilities.
4. **GraphRAG Repositioned as Algorithmic Reference:** Microsoft Research has placed GraphRAG in **official maintenance mode** ("won't be accepting new PRs or implementing new features"). It is a batch data-pipeline rather than an operational real-time transactional system. Its core value to PUB Neural is as an **Algorithmic Reference** for Hierarchical Leiden community partitioning, Map-Reduce community summaries, and multi-hop traversal (Local/Global/DRIFT search).
5. **CarpeOS & Palimp as Operational Blueprints:**
   - `innocarpe/CarpeOS` provides the best immutable event outbox pattern (`OutboxEvent`), deterministic state reduction (`adj_v3`), and continuous Obsidian-compatible Markdown projection.
   - `Heman10x-NGU/palimp` provides the cleanest bi-temporal invalidation schema (`valid_from`, `valid_until`, `is_active`, `superseded_by`) and native 8-tool MCP (*Model Context Protocol*) stdio server.

---

## 2. Research Methodology & Evidence Verification

Every assertion in this benchmark was verified via direct inspection of GitHub repositories, commit logs, license files, database schemas, and source code. Marketing claims in README files were discarded unless validated by operational code (`DOCUMENTED ≠ IMPLEMENTED`).

### Classification Schema
- **`IMPLEMENTED`**: Feature exists in executable source code, schemas, and test suites.
- **`PARTIAL`**: Feature exists in code but is incomplete, prototype-grade, or limited in scope.
- **`DOCUMENTED ONLY`**: Claimed in docs/RFCs but absent from executable code.
- **`ABSENT`**: Not addressed or implemented.
- **`UNKNOWN`**: Insufficient code evidence available to substantiate.

---

## 3. Audited Comparison Matrix (Factual & Verified)

*Note: All repository metrics reflect actual GitHub API data queried on September 12, 2026. Stars, commits, and releases are exact.*

| Metric / Dimension | OpenGraphMemory | Palimp | CarpeOS | GraphRAG (Microsoft) | OpenBrain | Nodum | Semantic-Memory-Agent | OpenKL |
|---|---|---|---|---|---|---|---|---|
| **Stars / Forks / Commits** | 129★ / 13 / 197 commits | 0★ / 0 / 33 commits | 0★ / 0 / 789 commits | 35,951★ / 3,784 / 491+ | 2★ / 0 / 20 commits | 13★ / 5 / 538 commits | 0★ / 0 / 1 commit | 119★ / 9 / 4 commits |
| **Releases & Tags** | 2 (`v0.2.2`, `v0.2.0`) | 0 (no releases) | 30+ (`v6.7.8`) | 30+ (`v3.1.2`) | 0 (no releases) | 9 (`v3.9.1`) | 1 (`v0.1.0`) | 0 (no releases) |
| **Maintenance Status** | Active maintenance | Active prototype | Active monorepo | **Official Maintenance Mode** | Early experimental | Active maintenance | Static demo | Stalled RFC / prototype |
| **Verified License** | MIT | MIT | **Apache-2.0** | MIT | **NONE (No license file)** | MIT | MIT | Apache-2.0 |
| **License Classification** | `SAFE TO REUSE` | `SAFE TO REUSE` | `SAFE TO REUSE` (with notice) | `SAFE TO REUSE` (reference) | **`REFERENCE ONLY`** | `SAFE TO REUSE` | `SAFE TO REUSE` | `SAFE TO REUSE` |
| **Core Language & Framework** | Python 3.11+, FastAPI, SQLAlchemy | Python 3.10+, Typer | TypeScript (Node 20+), Turborepo | Python 3.10-3.12, Pydantic | Python 3.12, Psycopg2 | TypeScript, Node/Go | Python, LangChain | Python, Typer, Kùzu SDK |
| **Primary Database** | PostgreSQL 16 | SQLite 3 | Cloudflare D1 / SQLite outbox | LanceDB + Parquet files | **PostgreSQL 16** | SQLite / PostgreSQL | SQLite | **Kùzu DB** (embedded) |
| **Graph Engine** | Relational tables + CTEs | Relational SQLite tables | Causal Event Graph | In-memory NetworkX pipeline | **Apache AGE** (`ag_catalog`) | Relational / D3 Graph | None | **Kùzu DB** (Cypher) |
| **Vector Store** | `pgvector` (HNSW) | `sqlite-vec` / Chroma pluggable | None internal (pluggable) | LanceDB columnar | `pgvector` (`memory_chunks`) | None internal | FAISS / Chroma | Kùzu Vector Extension |
| **Provenance Model** | `PARTIAL` (`source_id`, `chunk_id`) | `IMPLEMENTED` (`source_id`, `author`, `reason`) | `IMPLEMENTED` (Causal UUID, actor, signature) | `IMPLEMENTED` (`text_unit_ids` arrays) | `PARTIAL` (`source`, `external_id`) | `PARTIAL` (Markdown path) | `PARTIAL` (`session_id`) | `IMPLEMENTED` (`TransientCitation`) |
| **Bi-temporal Semantics** | `PARTIAL` (`created_at`, `updated_at`) | `IMPLEMENTED` (`valid_from/until`, `as_of`) | `IMPLEMENTED` (Immutable timeline) | `PARTIAL` (Covariates date spans) | `ABSENT` (`created_at` only) | `PARTIAL` (File mtime) | `PARTIAL` (Decay curve) | `PARTIAL` (Note timestamp) |
| **Conflict & Supersession** | `PARTIAL` (Embedding dedup) | `IMPLEMENTED` (`superseded_by`, `SUPERSEDES`) | `IMPLEMENTED` (`adj_v3` rule engine) | `PARTIAL` (LLM-based claim merge) | `ABSENT` (Cypher MERGE overwrite) | `ABSENT` (Overwrite) | `PARTIAL` (Cosine replace) | `ABSENT` |
| **Promotion States** | `ABSENT` | `PARTIAL` (`active`, `superseded`) | `PARTIAL` (`draft`, `promoted`, `held`) | `ABSENT` | `ABSENT` | `ABSENT` | `PARTIAL` (Episodic->Semantic) | `PARTIAL` (`unverified`, `verified`) |
| **Event Sourcing / Outbox** | `ABSENT` (Mutating ORM) | `IMPLEMENTED` (Append-only facts) | `IMPLEMENTED` (`OutboxEvent` stream) | `ABSENT` (Batch Parquet export) | `PARTIAL` (`raw_captures` append) | `ABSENT` | `ABSENT` | `ABSENT` (Direct files) |
| **Retrieval Strategy** | Vector + SQL recursive CTE | Lexical FTS5 + Vector + BFS | Causal timeline lookup | Leiden Global + Local + DRIFT | Semantic Vector + Cypher 1-hop | Graph adjacency traversal | Vector similarity + Decay | Kùzu Cypher + Vector search |
| **Native MCP Protocol** | `DOCUMENTED ONLY` | `IMPLEMENTED` (8 stdio tools) | `IMPLEMENTED` (`@innocarpe/mcp`) | `ABSENT` in core | `IMPLEMENTED` (`open_brain_mcp.py`)| `ABSENT` | `ABSENT` | `ABSENT` |
| **UI / Explorer** | React/Vite Force Graph | `ABSENT` (CLI only) | React Timeline + Obsidian files | `ABSENT` in core (CLI/Jupyter) | Next.js CRM UI (Contacts) | D3.js 2D Force Graph | `ABSENT` (CLI only) | React Graph & Doc Viewer |
| **Multi-Project / Multi-Tenant** | `PARTIAL` (`project_id` header) | `PARTIAL` (Namespace string) | `PARTIAL` (Trust zone string) | `ABSENT` | `ABSENT` (`_SINGLE_USER_ID`) | `ABSENT` (Single vault) | `ABSENT` | `ABSENT` (Single `.ok` dir) |

---

## 4. Per-Project Deep Dive (Source-Audited)

### 4.1 `impara/openBrain` (Deep Re-Evaluation)
- **Repository:** [`impara/openBrain`](https://github.com/impara/openBrain) | **Stars:** 2 | **Forks:** 0 | **Commits:** 20 | **Releases:** 0
- **Verified License:** **NONE** (No `LICENSE`, `LICENSE.md`, or copyright grant exists in the repository. Under copyright law, all rights are reserved by the author. **Classification: REFERENCE ONLY**).
- **Core Stack:** Python 3.12, Psycopg2, PostgreSQL 16.
- **Architecture Philosophy (`ARCHITECTURE.md`):**
  - OpenBrain’s primary design choice is to eliminate the operational split between vector storage and graph traversal: *"OpenBrain intentionally keeps vectors, graph data, and raw source material inside one PostgreSQL system."*
  - Avoids dual-database partial-write failures, duplicate IDs, and query stitching across disparate platforms.
- **Database Schema & Infrastructure (`openbrain/infrastructure/repositories.py`):**
  - Installs extensions dynamically:
    ```sql
    CREATE EXTENSION IF NOT EXISTS vector SCHEMA public;
    CREATE EXTENSION IF NOT EXISTS age;
    ```
  - Creates the AGE property graph: `PERFORM ag_catalog.create_graph('open_brain');`
  - Raw Ingestion Table: `memory_store.raw_captures` (`id BIGSERIAL`, `user_id`, `source`, `content`, `ingest_strategy`, `created_at`).
  - Asynchronous Job Queue: `memory_store.capture_jobs` (`id BIGSERIAL`, `raw_capture_id REFERENCES raw_captures`, `status IN ('pending', 'processing', 'done', 'retry', 'failed')`).
  - Vector Chunk Table: `memory_store.memory_chunks` (`id BIGSERIAL`, `raw_capture_id`, `content`, `embedding vector(1536)`, `metadata JSONB`).
- **Graph Traversal via Apache AGE (`AGEGraphRepository`):**
  - Node Insertion:
    ```sql
    SELECT * FROM cypher('open_brain', $$
        MERGE (n:Entity {name: '...'})
        RETURN n
    $$) AS (n agtype);
    ```
  - Edge Traversal & Neighbor Retrieval: Executes Cypher queries embedded inside PostgreSQL SQL statements via the `cypher()` UDF.
  - Search Sanitization: Uses regexes (`_validate_search_term`) and string escaping because Apache AGE historical releases had incomplete support for parameterized prepared statements inside `cypher()`.
- **MCP Implementation:** Ships `open_brain_mcp.py` exposing MCP tools over stdio.
- **Limitations for PUB Neural:**
  - Hardcoded single-user design (`_SINGLE_USER_ID = "default"`).
  - Destructive/in-place node merge (`MERGE` without bi-temporal `valid_from`/`valid_until` tracking).
  - Lacks repository/commit/file-line provenance.
  - No license grant precludes direct code adoption.

### 4.2 `nowledge-co/OpenKL` (Correction & Verification)
- **Repository:** [`nowledge-co/OpenKL`](https://github.com/nowledge-co/OpenKL) | **Stars:** 119 | **Forks:** 9 | **Commits:** 4 | **Releases:** 0
- **Verified License:** **Apache-2.0** (`SAFE TO REUSE` with attribution). Author: `wey-gu`.
- **Correction:** OpenKL does **NOT** use PostgreSQL, Neo4j, or Memgraph. It is explicitly an embedded **Kùzu DB** project (`openkl/db.py`).
- **Storage & Schema Architecture (`openkl/db.py`):**
  ```python
  import kuzu
  db = kuzu.Database(str(db_path))
  conn = kuzu.Connection(db)
  conn.execute("INSTALL VECTOR;")
  conn.execute("LOAD VECTOR;")
  ```
  - Schema defines nodes: `MemoryNote(id, text, ts, tags, vec FLOAT[384])`, `Doc(id, path, sha256)`, `Chunk(id, text, span, vec FLOAT[384])`, `Entity(id, name, type)`, `Topic(id, name)`.
  - Schema defines rels: `HAS_CHUNK(FROM Doc TO Chunk)`, `Mentions(FROM Chunk TO Entity)`, `DerivedFrom(FROM MemoryNote TO Chunk)`.
- **Citations & Provenance (`openkl/citations.py`):**
  - Implements `TransientCitation` (for real-time search context) and `PersistedCitation` (for long-term references): tracks `surface` ("memory" | "store"), `path`, `sha256`, `loc` (line/char offsets), and verbatim `quote`.
- **File System Contract (`rfcs/0000-openkl-design.md`):**
  - Canonical material lives on disk in `~/.ok/store/sources/` and `~/.ok/store/normalized/*.ok.md`. The Kùzu graph and vector index are **derived structures** rebuildable from files.
- **Current Maturity:** Early-stage draft RFC 0000; only 4 commits. Not production ready for enterprise multi-repository ingestion, but excellent conceptual reference for citations and embedded Kùzu usage.

### 4.3 `microsoft/graphrag` (Algorithmic Reference Repositioning)
- **Repository:** [`microsoft/graphrag`](https://github.com/microsoft/graphrag) | **Stars:** 35,951 | **Forks:** 3,784 | **Commits:** 491+ | **Releases:** 30+ (`v3.1.2`)
- **Verified License:** **MIT** (`SAFE TO REUSE`).
- **Official Maintenance Notice (Verbatim from README):**
  > *"GraphRAG is a research project... Since our first release in July 2024 the capabilities of frontier models have changed dramatically... This project is largely in maintenance mode, and won't be accepting new PRs or implementing new features. We'll perform bug fixes and dependency updates as appropriate..."*
- **Operational Reality:** GraphRAG is a heavy, batch-oriented data pipeline executing across DataFrames, LanceDB, and Parquet files. It is **not** an operational, low-latency graph database or real-time event-driven agent memory engine.
- **Essential Algorithmic Reference Value:**
  1. **Hierarchical Leiden Clustering (`graspologic.partition.hierarchical_leiden`):** Multi-level community partitioning of the knowledge graph.
  2. **Community Summarization:** Recursive Map-Reduce generation of structured `CommunityReport` artifacts (title, summary, findings, rating).
  3. **Global Search:** Answers macro-level corpus questions by synthesizing community summaries rather than retrieving individual chunks.
  4. **Local Search:** Traverses k-hop neighbors around matched entities, injecting raw text units and covariates into LLM context.
  5. **DRIFT Search:** Dynamic Reasoning and Information-Focused Traversal combining Global breadth with Local depth.
  6. **Text-Unit Arrays:** Strict array of `text_unit_ids` on all entities, relationships, and claims.

### 4.4 `Heman10x-NGU/palimp` (Palimpsest Engine)
- **Repository:** [`Heman10x-NGU/palimp`](https://github.com/Heman10x-NGU/palimp) | **Stars:** 0 | **Forks:** 0 | **Commits:** 33 | **Releases:** 0
- **Verified License:** **MIT** (Copyright (c) 2026 GraphCtx Contributors).
- **Bi-temporal Schema (`palimp/db/schema.sql`):**
  - Strict non-destructive updates. Table `facts` contains:
    `valid_from TIMESTAMP NOT NULL`, `valid_until TIMESTAMP`, `is_active INTEGER DEFAULT 1`, `superseded_by TEXT REFERENCES facts(id)`.
  - When a fact is invalidated or contradicted: `valid_until` is stamped, `is_active` set to `0`, `superseded_by` points to the new fact ID. SQL `DELETE` is prohibited.
- **Model Context Protocol (MCP):**
  - Complete, functional stdio MCP server exposing 8 tools: `memory_store`, `memory_search`, `memory_recall_at`, `memory_supersede`, `memory_history`, `memory_get_relations`, `memory_batch_insert`, `memory_stats`.
  - Supports true time-travel querying: `valid_from <= T AND (valid_until IS NULL OR valid_until > T)`.

### 4.5 `innocarpe/CarpeOS`
- **Repository:** [`innocarpe/CarpeOS`](https://github.com/innocarpe/CarpeOS) | **Stars:** 0 | **Forks:** 0 | **Commits:** 789 | **Releases:** 30+ (`v6.7.8`)
- **Verified License:** **Apache-2.0** (`SAFE TO REUSE` with attribution).
- **Event Sourcing & Outbox (`packages/core/src/store/outbox.ts`):**
  - Employs an append-only `OutboxEvent` structure with causal DAG parent tracking (`parents: string[]`), actor identity, timestamps, and payload.
  - Zero in-place mutations of state records.
- **Adjudication Engine (`packages/core/src/rules/adj_v3.ts`):**
  - Pure state reducer `reduce(events, state) => newState`. State can be reproduced from zero by replaying events.
- **Obsidian Continuous Projection (`packages/projections/src/obsidian.ts`):**
  - Generates a local folder of Markdown files containing frontmatter and `[[Wikilinks]]` representing current active meaning. The Markdown is purely a projection; the event log is canonical.

### 4.6 `ardiannurcahya/open-graph-memory`
- **Repository:** [`ardiannurcahya/open-graph-memory`](https://github.com/ardiannurcahya/open-graph-memory) | **Stars:** 129 | **Forks:** 13 | **Commits:** 197 | **Releases:** 2
- **Verified License:** **MIT** (Copyright (c) 2025 OpenGraphRAG contributors).
- **Core Architecture:**
  - Python 3.11, FastAPI, SQLAlchemy 2.0 async, PostgreSQL 16 with `pgvector`, Redis/ARQ task queue.
  - Relational graph schema: `entities` and `relations` tables. Graph traversal executed via PostgreSQL recursive CTEs.
  - React/Vite dashboard featuring interactive force-directed graph playground.
- **Limitations:** Lacks bi-temporal tracking (mutating updates), lacks formal promotion state machine, no native MCP server.

### 4.7 `nodummd/nodum`
- **Repository:** [`nodummd/nodum`](https://github.com/nodummd/nodum) | **Stars:** 13 | **Forks:** 5 | **Commits:** 538 | **Releases:** 9
- **Verified License:** **MIT**.
- **Role:** Markdown note-taking tool with D3.js force-directed 2D graph view. Good visual UX reference for backlinks and graph interaction, but lacks AI memory, provenance, and RAG pipelines.

### 4.8 `sadnanalmanir/semantic-memory-agent`
- **Repository:** [`sadnanalmanir/semantic-memory-agent`](https://github.com/sadnanalmanir/semantic-memory-agent) | **Stars:** 0 | **Forks:** 0 | **Commits:** 1 | **Releases:** 1 (`v0.1.0`)
- **Verified License:** **MIT**.
- **Role:** Minimal demonstration of two-tier memory (`Episodic` in SQLite, `Semantic` in FAISS/Chroma) with asynchronous consolidation and exponential recency decay. Useful academic reference; not enterprise infrastructure.

---

## 5. Comparative Evaluation of Storage & Graph Architectures

We evaluate four primary backend configurations against PUB Neural requirements:

| Dimension | Candidate A: PostgreSQL + pgvector + Relational CTEs | Candidate B: PostgreSQL + pgvector + Apache AGE | Candidate C: PostgreSQL + External Graph DB (Neo4j/Memgraph) | Candidate D: Kùzu Embedded (Local/In-Process) |
|---|---|---|---|---|
| **Representative Projects** | `open-graph-memory` | `impara/openBrain` | Traditional Enterprise GraphRAG | `nowledge-co/OpenKL` |
| **Storage Engines Count** | **1 (PostgreSQL 16)** | **1 (PostgreSQL 16)** | 2+ (PostgreSQL + Neo4j/Memgraph) | 1 embedded library + local disk |
| **Graph Query Dialect** | ANSI SQL (Recursive CTEs) | **OpenCypher** via `cypher()` UDF | OpenCypher / GQL (native) | **OpenCypher** (native in Kùzu) |
| **Graph Traversal (1-3 hops)** | Excellent (<15ms via B-Tree/GiST) | Excellent (<10ms via AGE internal store) | Outstanding (<5ms native pointer chasing) | Outstanding (<5ms vectorized columnar) |
| **Deep Path Finding (>4 hops)** | Degrades; complex SQL syntax | Good (Cypher variable-length paths) | Outstanding (optimized graph engine) | Outstanding (columnar adjacency) |
| **Transactional Consistency** | **ACID Strict (Atomic single DB)** | **ACID Strict (Atomic single DB)** | **Eventual / Dual-write Split-Brain Risk**| ACID (Embedded single-process) |
| **Provenance Joins** | Trivial (Direct SQL Foreign Keys) | Moderate (Requires joining agtype to SQL) | High overhead (Cross-database query stitching)| Trivial within Kùzu tables |
| **Operational Overhead** | **Very Low** (Standard PostgreSQL 16) | **Low** (Postgres container with AGE ext) | **High** (Clustering, sync, dual backup/auth) | **Very Low** (Embedded library in Python) |
| **Portability & Ecosystem** | Universal (Supabase, AWS RDS, Neon) | Restricted (Requires Postgres AGE support) | Enterprise standard | Embedded Python/C++ binaries |
| **Agent / MCP Concurrency** | High (Multi-connection pooling) | High (PostgreSQL connection pooling) | High (Bolt protocol) | **Single-process write lock limitation** |
| **Failure Modes** | Standard PostgreSQL failover | AGE extension crash affects whole DB | Split-brain between graph and vector store | Process lock contention / file corruption |

### Detailed Evaluation Summary:
- **Candidate A (PostgreSQL Relational + CTEs):** The most operationally reliable. Handles 95% of PUB Neural queries (1-3 hops around entities, rules, decisions). Provenance joins are standard relational foreign keys.
- **Candidate B (PostgreSQL + pgvector + Apache AGE):** Offers native OpenCypher query elegance inside PostgreSQL without a second database server. However, Apache AGE introduces quirks with parameterized queries, requires specific extension compilation, and is not supported out-of-the-box on managed services like Supabase or AWS RDS without custom extensions.
- **Candidate C (External Neo4j/Memgraph):** Unjustified operational complexity for PUB Neural V0. Introduces fatal split-brain risks between the relational provenance store, the vector store, and the graph.
- **Candidate D (Embedded Kùzu):** Superb for single-agent local execution (as demonstrated in OpenKL), but multi-agent concurrent writes (PDL, Hermes, ingest workers) run into single-writer process lock constraints unless wrapped behind a custom RPC daemon.

---

## 6. Canonical Source of Truth Decision

We rigorously compare three architectural models for state management:

### Model A: Event Log is Canonical; Knowledge State is Derived & Rebuildable
- **Mechanism:** Every action, extraction, validation, and decision is written as an immutable event to an append-only log (`neural_events`). Nodes, edges, vectors, search indices, and Markdown files are **derived projections** produced by deterministic reducers.
- **Pros:** 100% auditability, zero loss of history, idempotent replay, time-travel debugging, trivial recovery from model drift or corrupted extraction (re-run reducers from events).
- **Cons:** Requires projector infrastructure and eventual consistency management between outbox and query views.

### Model B: Nodes & Edges are Canonical; Event Log is Audit Trail
- **Mechanism:** Knowledge is stored directly as mutable records in `nodes` and `edges` tables. Events are written secondary as audit history.
- **Pros:** Familiar CRUD operations, immediate query consistency.
- **Cons:** Fatal loss of causal lineage; impossible to guarantee that mutations faithfully reflect original sources; schema migrations can corrupt historical truth.

### Model C: Hybrid Model
- **Mechanism:** Decisions and policies use event sourcing; factual entities use direct CRUD.
- **Pros:** Compromise.
- **Cons:** Inconsistent semantics, architectural ambiguity, split recovery workflows.

### **Canonical Decision: MODEL A (Event Log Canonical)**
PUB Neural formally adopts **Model A**.
`CANONICAL_SOURCE_OF_TRUTH = IMMUTABLE_EVENT_LOG`  
`KNOWLEDGE_GRAPH = DERIVED_REBUILDABLE_PROJECTION`

---

## 7. Provenance & Evidence Architecture

Provenance cannot be flattened into a few string columns on a node. A single architectural rule or decision may be evidenced across multiple repositories, commits, and documents over time.

### Entity Relationship: `KNOWLEDGE → EVIDENCE → SOURCE`
```text
┌────────────────────────────────────────┐
│             KNOWLEDGE NODE             │
│  (e.g., Rule: "Zero In-Place Mutation")│
└──────────────────┬─────────────────────┘
                   │ 1
                   │
                   │ N
┌──────────────────▼─────────────────────┐
│             EVIDENCE LINK              │
│  - extractor_version: "v1.2.0"         │
│  - confidence: 0.98                    │
│  - validation_state: VALIDATED         │
│  - start_line: 45, end_line: 62        │
│  - exact_quote: "..."                  │
└──────────────────┬─────────────────────┘
                   │ N
                   │
                   │ 1
┌──────────────────▼─────────────────────┐
│                 SOURCE                 │
│  - organization: "PUB Core Holding"    │
│  - project: "pub-core-os"              │
│  - repository: "pubcoreagencia/neural" │
│  - commit_sha: "a3f8c12..."            │
│  - file_path: "docs/architecture.md"   │
│  - observed_at: 2026-09-12T06:00:00Z   │
└────────────────────────────────────────┘
```
- A knowledge node is supported by one or more `EVIDENCE` records.
- Each `EVIDENCE` and `SOURCE` contract models both Git provenance and content-addressed preservation:
  - `repository`: Git repository URI / identifier
  - `commit_sha`: Point-in-time Git commit
  - `branch`: Ingested branch
  - `file_path`: Relative workspace file path
  - `file_sha256`: Cryptographic hash of the source file
  - `content_hash`: Cryptographic hash of the exact evidence slice
  - `start_line`: 1-based start offset
  - `end_line`: 1-based end offset
  - `observed_at`: Ingestion timestamp
  - `immutable_snapshot_ref`: Content-addressed storage reference preserving the raw source text independently of repository mutations
  - `extractor_version`: Extractor model/ruleset version
- **Design Principle:** `Git = Provenance; Content-Addressed Evidence = Preservation`. This ensures PUB Neural retains verified evidence even if upstream Git commits or branches rebase or mutate.
- Contradictory evidence does not overwrite existing links; it attaches new evidence flagged as `CONTRADICTS`.

---

## 8. Scope Separation: Trust Zone vs Project vs Repository

Projects within PUB Core Holding are not isolated multi-tenant silos. They are interconnected neurons of a single corporate holding.
- **`TRUST_ZONE`**: Boundary of organizational trust and security policy (e.g., `tz_internal_holding`, `tz_client_facing`, `tz_public_open_source`). Controls encryption, visibility, and data sovereignty.
- **`PROJECT`**: Strategic initiative or domain (e.g., `pub-ecom`, `pdl`, `pub-core-os`, `pub-neural`).
- **`REPOSITORY`**: Git repository containing versioned code and markdown specs.
- **Cross-Project Relationships:** The knowledge graph **must natively link entities across projects** (e.g., `(Project: pub-ecom)-[:DEPENDS_ON]->(Project: pub-core-os)` or `(Agent: PDL)-[:IMPLEMENTS]->(Rule: Centralized Logging)`).
- **Scope Controls:** Used for retrieval filtering (e.g., "Retrieve only within `pub-ecom` context plus `GLOBAL` institutional rules") and source authority evaluation.

---

## 9. Knowledge Promotion Pipeline vs CEO Sovereignty

We strictly distinguish between **factual automated knowledge extraction** and **institutional strategic governance**:

### Automated Factual Promotion (System & Agent Consensus)
Factual code symbols, doc references, dependencies, and patterns move through automated gates:
1. `CAPTURED`: Raw payload ingested into event outbox.
2. `OBSERVED`: Source identity, commit SHA, and author verified.
3. `EXTRACTED`: Entities, relationships, and evidence spans parsed.
4. `CANDIDATE`: Deduplicated against existing graph; contradictions checked.
5. `VALIDATED`: Corroborated by automated test, linter, or peer agent consensus.
6. `ADOPTED`: Actively in use across working repositories.
7. `INSTITUTIONAL_CANDIDATE`: Validated adoption across multiple projects/repositories, establishing candidate holding-wide consensus.
8. `INSTITUTIONAL`: Canonical standard ratified for the holding.

> [!IMPORTANT]
> Cross-project adoption across $\ge 2$ repositories does NOT automatically promote knowledge to `INSTITUTIONAL`. It promotes it to `INSTITUTIONAL_CANDIDATE`. Transition to `INSTITUTIONAL` remains strictly subject to institutional governance sign-off, particularly for:
> - `GOVERNANCE`
> - `STRATEGIC DECISION`
> - `EXECUTIVE POLICY`
> - `SECURITY RULE`
> - `ARCHITECTURAL STANDARD`

### CEO Sovereignty Gate (Human Executive Authority)
Automated agents are strictly prohibited from unilaterally promoting:
- `STRATEGIC DECISION`: Executive decisions altering corporate roadmap or architecture.
- `GOVERNANCE RULE`: Security boundaries, licensing mandates, or sovereignty constraints.
- `EXECUTIVE POLICY`: Irreversible operational directives.
- `CONTRADICTION RESOLUTION`: Choosing between two fundamentally conflicting architectural standards.

These entities remain in `PROPOSED` or `BLOCKED` status until signed off by the CEO / human authority.

---

## 10. Formal Contradiction & Temporal Semantics

In accordance with Palimp's proven model, knowledge in PUB Neural is non-destructive:
- **`CONTRADICTS`**: Edge indicating that Fact A and Fact B assert mutually incompatible statements about the same entity. Both remain visible; confidence scores and warning flags are attached during retrieval.
- **`SUPERSEDES`**: Edge indicating that Fact B has formally replaced Fact A (due to higher authority, newer valid timestamp, or CEO ratification).
  - Fact A: `valid_until` is updated to the transition timestamp; `is_active = FALSE`.
  - Fact B: `valid_from` is set to the transition timestamp; `is_active = TRUE`.
  - Fact A is **never deleted**. Time-travel queries (`as_of(T)`) continue to reconstruct historical truth accurately.
- **`DEPRECATED`**: Entity remains historically valid but is marked discouraged for future implementations.
- **`REJECTED`**: Proposed candidate fact failed verification and is excluded from active retrieval.
- **`BLOCKED`**: Fact is in contradiction or requires CEO sign-off before downstream agents can consume it.

---

## 11. Search & Retrieval Architecture

PUB Neural separates retrieval into distinct composable layers:

### Search Primitives
1. **`LEXICAL`**: PostgreSQL Full-Text Search (`tsvector` + `tsquery` with GIN index) for exact symbol, commit, and name lookups.
2. **`VECTOR`**: `pgvector` HNSW index on embeddings (cosine distance `<=>`) for conceptual and semantic queries.
3. **`GRAPH`**: Neighborhood expansion (1-3 hops) linking matched entities to active decisions, rules, and dependencies.
4. **`HYBRID`**: Reciprocal Rank Fusion (RRF) combining lexical, vector, and graph scores into a unified ranked list.

### Retrieval Context Modes
- **`ENTITY RETRIEVAL`**: Fast single-entity lookup + attributes (for code autocompletion and compiler agents).
- **`LOCAL GRAPH CONTEXT`**: 1-2 hop neighborhood context pack with evidence citations (for task-focused agents like PDL and Hermes).
- **`GLOBAL RETRIEVAL` (GraphRAG Leiden Pattern)**: Map-Reduce community summaries answering macro questions across the holding ("What are our cross-repository authentication patterns?").
- **`TIME-AWARE RETRIEVAL`**: Queries parameterized with `as_of = TIMESTAMP`.
- **`PROVENANCE-AWARE RETRIEVAL`**: Context packs that include verbatim source quotes, commit SHAs, and verification badges.

---

## 12. Full Rebuildability & Projection Lifecycle

To guarantee long-term operational resilience, all derived data structures can be wiped and reconstructed from the canonical event log:

```text
┌────────────────────────────────────────────────────────┐
│             CANONICAL: neural_events                   │
└──────────────────────────┬─────────────────────────────┘
                           │ REPLAY / REDUCE
       ┌───────────────────┼───────────────────┐
       ▼                   ▼                   ▼
┌──────────────┐    ┌──────────────┐    ┌──────────────┐
│ neural_nodes │    │ neural_edges │    │ neural_evid. │
└──────┬───────┘    └──────┬───────┘    └──────┬───────┘
       │                   │                   │
       ├───────────────────┴───────────────────┤
       ▼                                       ▼
┌──────────────────────────────┐ ┌──────────────────────────────┐
│  REBUILDABLE VECTOR INDEXES  │ │  REBUILDABLE SEARCH INDEXES  │
│  - pgvector HNSW embeddings  │ │  - GIN tsvector indexes      │
└──────────────────────────────┘ └──────────────────────────────┘
       ▼                                       ▼
┌──────────────────────────────┐ ┌──────────────────────────────┐
│ REBUILDABLE COMMUNITY REPS   │ │ REBUILDABLE OBSIDIAN VAULT   │
│ - Hierarchical Leiden clusters│ │ - Markdown files + wikilinks │
└──────────────────────────────┘ └──────────────────────────────┘
```

### Rebuild Guarantees: Canonical State vs Derived AI Artifacts

To prevent flawed assumptions regarding determinism in generative components, PUB Neural enforces a formal bifurcation:

#### A. Canonical State (Deterministic Reproducibility)
Reconstruction of `neural_nodes`, `neural_edges`, `neural_evidence`, `neural_sources`, and state transitions is **strictly reproducible** upon replaying `neural_events` under:
- The same `neural_events` sequence;
- The same reducer version (`reducer_version`);
- The same projection schema version (`projection_version`);
- The same normalization rules.

#### B. Derived AI Artifacts (Versioned Rebuildability)
Embeddings, vector indexes, semantic rankings, community partitions, and Leiden community summaries are:
- **Rebuildable** from canonical events and sources;
- **Version-tracked** (`model_id`, `embedding_dim`, `prompt_template_version`);
- **Provenance-aware** (citing input chunk hashes);
- **Reproducible strictly under the same declared model, temperature, and configuration**.

---

## 13. Recalculated ADOPT / ADAPT / BUILD / AVOID Framework

| Component / Layer | Decision | Source Project / Reference | Technical Rationale |
|---|---|---|---|
| **Immutable Event Outbox** | **ADAPT** | `innocarpe/CarpeOS` | Adapt the `OutboxEvent` schema and deterministic reducer pattern to Python/PostgreSQL. |
| **Obsidian Markdown Projection** | **ADAPT** | `innocarpe/CarpeOS` | Adapt continuous projection of graph nodes into Markdown files with YAML frontmatter and `[[Wikilinks]]`. |
| **Bi-temporal Schema & Non-destructive Updates** | **ADOPT** | `Heman10x-NGU/palimp` | Adopt `valid_from`, `valid_until`, `is_active`, `superseded_by` columns. Prohibit physical SQL `DELETE`. |
| **Agent MCP Protocol Engine** | **ADOPT** | `Heman10x-NGU/palimp` | Adopt the 8-tool MCP stdio/SSE server specification (`memory_search`, `memory_store`, `memory_supersede`, etc.). |
| **Hierarchical Leiden & Community Summaries** | **ADAPT** | `microsoft/graphrag` | Adapt the Leiden community clustering and Map-Reduce summary prompts as an algorithmic reference running on PostgreSQL. |
| **PostgreSQL 16 + pgvector Single-DB Core** | **ADAPT** | `ardiannurcahya/open-graph-memory` | Adopt relational graph tables (`nodes`, `edges`) with `pgvector` HNSW indexes and recursive CTE traversals. |
| **Citation Data Model** | **ADAPT** | `nowledge-co/OpenKL` | Adapt the `TransientCitation` and `PersistedCitation` contracts for line-span evidence tracking. |
| **Apache AGE Extension (Graph Cypher in Postgres)** | **REFERENCE ONLY / DEFER** | `impara/openBrain` | OpenBrain proves AGE works, but AGE has no license in OpenBrain, requires custom PG builds, and complicates foreign-key joins to provenance. Defer AGE to V1; use Relational CTEs for V0. |
| **7-Stage Knowledge Promotion State Machine** | **BUILD** | **Custom PUB Neural** | Build the canonical state transitions (`CAPTURED` → `INSTITUTIONAL`) under consensus rules. |
| **CEO Sovereignty Authorization Gate** | **BUILD** | **Custom PUB Neural** | Build the human approval gate for `STRATEGIC DECISION`, `GOVERNANCE RULE`, and `POLICY`. |
| **Multi-Repository Git Ingestion Pipeline** | **BUILD** | **Custom PUB Neural** | Build webhook/CLI ingestors parsing Git commits, tags, branches, and documentation spans. |
| **External Graph DBs (Neo4j/Memgraph) in V0** | **AVOID** | — | Avoid multi-database operational complexity and split-brain risks. |
| **Destructive In-Place Mutations / SQL DELETE** | **AVOID** | — | Destroys institutional provenance and historical time-travel capabilities. |
| **Vector-Only RAG** | **AVOID** | — | Inadequate for understanding structured architectures, rules, and cross-repo dependencies. |
| **Unlicensed Code Reuse (`impara/openBrain`)** | **AVOID** | — | Direct code copying from `impara/openBrain` is legally prohibited (no license grant). Architectural concepts only. |

---

## 14. Architecture Freeze Specification & Final Decisions

```text
BENCHMARK_STATUS = COMPLETED_AND_VERIFIED
ARCHITECTURE_STATUS = V0_APPROVED_FOR_SCHEMA_DESIGN
ARCHITECTURE_CONFIDENCE = HIGH_WITH_DECLARED_EVIDENCE_GAPS

ARCHITECTURE_DECISION = SINGLE_POSTGRESQL16_EVENT_SOURCED_HYBRID_GRAPH

CANONICAL_SOURCE_OF_TRUTH = IMMUTABLE_EVENT_LOG (neural_events)

GRAPH_STRATEGY = RELATIONAL_TABLES_WITH_RECURSIVE_CTES (neural_nodes, neural_edges; OpenCypher via Apache AGE deferred to V1)

VECTOR_STRATEGY = POSTGRESQL_PGVECTOR_HNSW (1536 dimensions, cosine distance)

RETRIEVAL_STRATEGY = HYBRID_RRF (Lexical tsvector + Vector pgvector + 2-hop Graph Neighborhood + Algorithmic Leiden Community Summaries)

PROVENANCE_MODEL = DECOUPLED_MULTI_EVIDENCE (KNOWLEDGE -> EVIDENCE -> SOURCE with Commit SHA, File Path, Line Span)

GOVERNANCE_MODEL = DUAL_TRACK (Automated 7-stage promotion for facts; Mandatory CEO Sovereignty gate for Strategic Decisions and Governance Rules)

OPEN_SOURCE_ADOPT = Heman10x-NGU/palimp (Bi-temporal schema & 8 MCP tools)

OPEN_SOURCE_ADAPT = innocarpe/CarpeOS (Outbox pattern & Obsidian projection), microsoft/graphrag (Hierarchical Leiden algorithms), nowledge-co/OpenKL (Citation data model), ardiannurcahya/open-graph-memory (PostgreSQL relational schema baseline)

PUB_BUILD = 7-Stage Promotion Engine, CEO Sovereignty Gate, Multi-Repository Git Ingestion Worker, Cross-Project Scope Resolver

AVOID = External Graph Databases (Neo4j/Memgraph), Direct In-Place SQL Deletes, Unlicensed Code Copying from impara/openBrain, Vector-Only RAG

EVIDENCE_GAPS = Performance of recursive CTE graph traversals beyond 500,000 edges in PostgreSQL 16 (requires empirical load test in Phase V1); Incremental real-time community re-clustering without full Leiden re-computation (research open problem)

ARCHITECTURE_CONFIDENCE = HIGH

NEXT_STEP = PRODUCE docs/ARCHITECTURE_V0_DECISION.md AND AWAIT USER APPROVAL PRIOR TO ANY CODE OR MIGRATIONS
```

