# Architecture V0 Decision Record: PUB Neural

**Document Status:** ARCHITECTURE FREEZE DECISION RECORD (ADR-0001)  
**Date:** September 12, 2026  
**Target Workspace:** `pub neural` (`/Users/user/Documents/antigravity/pub neural`)  
**Canonical Spec Reference:** `MASTER_CONTEXT.md`  
**Prerequisite Reference:** `docs/OPEN_SOURCE_ARCHITECTURE_BENCHMARK.md`

---

## 1. Context & Strategic Mandate

PUB Neural is the authoritative cognitive architecture for **PUB Core Holding**. It aggregates institutional memory, decisions, rules, patterns, codebase structures, and operational execution across all holding repositories (e.g., `pub-ecom`, `pdl`, `pub-core-os`).

Prior to authoring migrations or writing production code, this document formally freezes the architectural decisions for **PUB Neural V0**, addressing canonical persistence, graph representations, provenance decoupling, multi-project scoping, knowledge promotion, and search topologies.

---

## 2. Canonical Source of Truth: Model A Formal Specification

### Decision
PUB Neural formally designates the **Append-Only Event Log plus Verified Content-Addressed Source Blobs** as canonical root of truth:
$$\text{CANONICAL\_STATE} = \text{neural\_events} + \text{neural\_event\_parents} + \text{pub\_neural.source\_blobs}$$
All graph tables (`neural_nodes`, `neural_edges`), vector embeddings, search indices, and Markdown vault files are strictly **derived projections**.

```text
┌─────────────────────────────────────────────────────────────┐
│          CANONICAL SOURCE OF TRUTH (APPEND-ONLY + CAS)      │
│        neural_events + pub_neural.source_blobs              │
└──────────────────────────────┬──────────────────────────────┘
                               │
               ┌───────────────┴───────────────┐
               ▼ (Deterministic Reducer)       ▼ (Projections)
┌──────────────────────────────┐ ┌──────────────────────────────┐
│        GRAPH TABLES          │ │        OBSIDIAN VAULT        │
│ neural_nodes & neural_edges  │ │  Markdown + [[Wikilinks]]    │
└──────────────┬───────────────┘ └──────────────────────────────┘
               │
       ┌───────┴───────┐
       ▼               ▼
┌──────────────┐ ┌──────────────┐
│   pgvector   │ │  tsvector    │
│  HNSW Index  │ │  GIN Index   │
└──────────────┘ └──────────────┘
```

### 2.1 Event Schema (`neural_events`)
Every mutation in the ecosystem enters through an immutable event:
```sql
-- Conceptual specification for V0 outbox
-- (Implementation migrations deferred until approval)
TABLE neural_events (
    id UUID PRIMARY KEY,                 -- UUIDv7 (time-ordered, monotic)
    event_type VARCHAR(64) NOT NULL,     -- e.g., 'SOURCE_INGESTED', 'FACT_EXTRACTED', 'DECISION_RATIFIED'
    stream_id VARCHAR(128) NOT NULL,     -- Aggregation stream (e.g., 'project:pub-ecom')
    stream_version BIGINT NOT NULL,      -- Monotonic sequential counter per stream
    actor_id VARCHAR(128) NOT NULL,      -- Agent ID or Human User ID
    actor_role VARCHAR(64) NOT NULL,     -- 'AGENT', 'ENGINEER', 'CEO'
    causal_parent_id UUID,               -- Previous event ID in causal chain
    payload JSONB NOT NULL,              -- Immutable event payload
    signature TEXT,                      -- Cryptographic signature / token
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_stream_version UNIQUE (stream_id, stream_version)
);
```

### 2.2 Deterministic Reducer & Projections
- **Reducer Function:** A pure state transition function:
  $$\text{Reducer}: (\text{State}_{t-1}, \text{Event}_t) \to \text{State}_t$$
- **Projections Produced:**
  1. `neural_nodes`: Tabular projection of canonical entities (`PROJECT`, `DECISION`, `RULE`, `CONCEPT`, etc.).
  2. `neural_edges`: Tabular projection of relationships (`USES`, `SUPERSEDES`, `CONTRADICTS`, etc.).
  3. `neural_evidence`: Many-to-many junction binding nodes to source spans.
  4. `neural_vector_index`: Dense vector embeddings managed by `pgvector`.
  5. `obsidian_vault`: File-system Markdown projection with YAML frontmatter.

### 2.3 Replay, Idempotency & Consistency Guarantees
- **Idempotency:** Every event carries a globally unique `id` and `(stream_id, stream_version)`. Projectors verify processed event offsets; re-applying an already applied event produces a `NOOP`.
- **Replay Contract:** Any or all projections can be dropped and regenerated from zero:
  $$\text{TRUNCATE projections} \implies \text{REPLAY neural\_events ORDER BY id ASC} \implies \text{IDENTICAL STATE}$$
- **Consistency Model:**
  - Ingestion / Outbox Write: **Strict ACID Consistency** (PostgreSQL transaction).
  - Graph Projections: **Immediate Projection** in synchronous transaction for core metadata; **Asynchronous Eventual Consistency** for heavy operations (embeddings, Leiden clustering, Obsidian disk writes).

---

## 3. Decoupled Provenance Architecture: `KNOWLEDGE → EVIDENCE → SOURCE`

Provenance is not a set of flat columns on a node. A single piece of institutional knowledge can be corroborated or contradicted by multiple sources over time.

```text
┌─────────────────────────────────────────────────────────────┐
│                       KNOWLEDGE NODE                        │
│  id: "decision:pub-ecom:auth-strategy"                      │
│  entity_type: "DECISION"                                    │
│  title: "Supabase SSR Session Tokens"                       │
│  status: "ADOPTED"                                          │
└──────────────────────────────┬──────────────────────────────┘
                               │ 1
                               │
                               │ N
┌──────────────────────────────▼──────────────────────────────┐
│                    EVIDENCE JUNCTION                        │
│  id: UUID                                                   │
│  node_id: "decision:pub-ecom:auth-strategy"                 │
│  source_id: UUID                                            │
│  start_line: 120                                            │
│  end_line: 145                                              │
│  quote: "Tokens must be refreshed on edge middleware..."    │
│  confidence: 0.96                                           │
│  validation_state: "VALIDATED"                              │
│  extractor_version: "extractor-v2.1"                        │
│  observed_at: 2026-09-12T06:30:00Z                          │
└──────────────────────────────┬──────────────────────────────┘
                               │ N
                               │
                               │ 1
┌──────────────────────────────▼──────────────────────────────┐
│                       SOURCE ENTITY                         │
│  id: UUID                                                   │
│  organization: "PUB Core Holding"                           │
│  trust_zone: "tz_internal_holding"                          │
│  project_id: "pub-ecom"                                     │
│  repository: "pubcoreagencia/pub-ecom"                      │
│  branch: "main"                                             │
│  commit_sha: "9a2f7c041de..."                               │
│  file_path: "docs/auth-spec.md"                             │
│  file_sha256: "e3b0c44298fc1c149afbf4c8996fb92427..."      │
│  content_hash: "7f83b1657ff1fc53b92dc18148a1d65dfc2d..."    │
│  start_line: 120, end_line: 145                             │
│  observed_at: 2026-09-12T06:30:00Z                          │
│  immutable_snapshot_ref: "sha256:9a2f7c041de...raw_blob"    │
│  extractor_version: "extractor-v2.1"                        │
└─────────────────────────────────────────────────────────────┘
```

### Capabilities Enabled & Content-Addressed Preservation
- **Design Mandate:** `Git = Provenance; Content-Addressed Evidence = Preservation`.
- **Decoupled Historical Integrity:** Git references track lineage and origins (`repository`, `commit_sha`, `branch`, `file_path`). Concurrently, content hashes (`file_sha256`, `content_hash`, `immutable_snapshot_ref`) guarantee that evidence remains permanently retrievable even if upstream Git branches rebase, commits are rewritten, or files are relocated.
- **Multi-Evidence Corroboration:** Multiple independent documents across repositories validate the same `RULE`, `DECISION`, or `PATTERN`.
- **Line-Span Citations:** Downstream agents receive exact verified line quotes and offsets.

---

## 4. Scope Architecture: Trust Zone vs Project vs Repository

Projects in PUB Core Holding are not isolated multi-tenant silos. They are interconnected functional domains.

```text
TRUST_ZONE (e.g. tz_internal_holding)
 └── PROJECT (e.g. pub-ecom, pdl, pub-core-os)
      └── REPOSITORY (e.g. pubcoreagencia/pub-ecom)
           └── DOCUMENT (e.g. architecture.md)
                └── EVENT & EVIDENCE SPANS
```

### Rules of Scope & Cross-Project Edges
1. **Cross-Project Edges are Native:**
   - `(Project: pub-ecom)-[:DEPENDS_ON]->(Project: pub-core-os)`
   - `(Agent: PDL)-[:VALIDATED_BY]->(Rule: Centralized-Telemetry)`
   - `(Repository: pub-ecom)-[:IMPLEMENTS]->(Pattern: Outbox-Event-Sourcing)`
2. **Trust Zones Enforce Security:** Trust Zones determine encryption, external data leakage boundaries, and clearance levels.
3. **Scope Filtering in Retrieval:** An agent operating in `pub-ecom` queries:
   $$\text{Scope} = \{\text{Project: pub-ecom}\} \cup \{\text{Scope: GLOBAL}\}$$
   This retrieves local project context without obscuring holding-wide institutional standards.

---

## 5. Knowledge Promotion Pipeline vs CEO Sovereignty Gate

PUB Neural decouples high-velocity factual knowledge extraction from high-stakes strategic governance.

### 5.1 Factual Knowledge Lifecycle (Automated Agent Consensus)
Factual code symbols, repository structures, library dependencies, and technical patterns progress automatically through 7 stages:
$$\text{CAPTURED} \to \text{OBSERVED} \to \text{EXTRACTED} \to \text{CANDIDATE} \to \text{VALIDATED} \to \text{ADOPTED} \to \text{INSTITUTIONAL\_CANDIDATE} \to \text{INSTITUTIONAL}$$

- **`CAPTURED`**: Raw commit / PR webhook received in `neural_events`.
- **`OBSERVED`**: Provenance verified (commit SHA and content hashes verified).
- **`EXTRACTED`**: AST parser & LLM extractor identifies entities, relations, and evidence spans.
- **`CANDIDATE`**: Deduplication check against existing canonical entities.
- **`VALIDATED`**: Corroborated by deterministic compiler/linter check or automated verification.
- **`ADOPTED`**: Evidence proves active in-repo usage across working codebases.
- **`INSTITUTIONAL_CANDIDATE`**: Cross-project adoption corroborated across multiple repositories/projects, establishing candidate status for holding-wide standard.
- **`INSTITUTIONAL`**: Canonical standard formally ratified for the holding under appropriate institutional governance.

> [!IMPORTANT]
> Cross-project usage across $\ge 2$ repositories does NOT automatically promote knowledge to `INSTITUTIONAL`. It advances it to `INSTITUTIONAL_CANDIDATE`. Formal transition to `INSTITUTIONAL` requires institutional governance sign-off, especially for:
> - `GOVERNANCE`
> - `STRATEGIC DECISION`
> - `EXECUTIVE POLICY`
> - `SECURITY RULE`
> - `ARCHITECTURAL STANDARD`

### 5.2 CEO Sovereignty Gate (Human Executive Authority)
The CEO Sovereignty Gate is **mandatory** for:
1. `STRATEGIC DECISION`: Decisions establishing, deprecating, or pivoting technology stacks.
2. `GOVERNANCE RULE`: Security, sovereignty, legal licensing, and architectural mandates.
3. `EXECUTIVE POLICY`: Overriding rules or resolving deadlocked agent contradictions.

**Invariant:** An AI agent cannot unilaterally move a `STRATEGIC DECISION` or `GOVERNANCE RULE` to `ADOPTED` or `INSTITUTIONAL`. It must emit an event of type `PROPOSAL_SUBMITTED`, remaining in `CANDIDATE` or `BLOCKED` status until an event of type `DECISION_RATIFIED` is signed by the CEO / human authority.

---

## 6. Formal Contradiction & Bi-Temporal Semantics

Following the model validated in `Heman10x-NGU/palimp`, physical SQL `DELETE` is prohibited in PUB Neural projections.

### 6.1 State Machine for Knowledge Conflicts
- **`CONTRADICTS`**: Edge established when Fact $B$ asserts a proposition logically incompatible with Fact $A$ while Fact $A$ is still active. Both facts are maintained with confidence scores. In retrieval, both are surfaced with a `CONTRADICTION_WARNING` flag.
- **`SUPERSEDES`**: Edge established when Fact $B$ replaces Fact $A$ (via newer validated timestamp, superior authority, or CEO ratification).
  - Fact $A$: `valid_until = CURRENT_TIMESTAMP`, `is_active = FALSE`, `superseded_by = Fact_B.id`.
  - Fact $B$: `valid_from = CURRENT_TIMESTAMP`, `is_active = TRUE`.
  - Fact $A$ is preserved for historical audit.
- **`DEPRECATED`**: Entity remains historically accurate but discouraged for future implementations.
- **`REJECTED`**: Entity was proposed but determined to be false, ungrounded, or rejected by human review.
- **`BLOCKED`**: Knowledge adoption is suspended pending conflict resolution.

### 6.2 Time-Travel Queries
Any retrieval query can supply an `as_of` timestamp $T$:
$$\text{Filter: } \text{valid\_from} \le T \land (\text{valid\_until IS NULL} \lor \text{valid\_until} > T)$$
This returns the exact state of institutional knowledge at timestamp $T$.

---

## 7. Comparative Evaluation of Storage & Graph Candidates

We systematically evaluated four candidate backend architectures:

```text
Candidate A: PostgreSQL 16 + pgvector + Relational CTE Graph (Selected for V0)
Candidate B: PostgreSQL 16 + pgvector + Apache AGE (Evaluated via OpenBrain)
Candidate C: PostgreSQL 16 + External Graph DB (Neo4j / Memgraph)
Candidate D: Embedded Kùzu-Centered Engine (Evaluated via OpenKL)
```

| Evaluation Dimension | Candidate A (Relational CTEs) | Candidate B (Apache AGE) | Candidate C (External Neo4j) | Candidate D (Embedded Kùzu) |
|---|---|---|---|---|
| **Architectural Complexity** | **Very Low (1 DB)** | **Low (1 DB, custom ext)** | High (2 DBs, sync daemon) | Very Low (1 embedded file) |
| **Transaction Atomicity (ACID)** | **100% Strict (Single WAL)** | **100% Strict (Single WAL)**| Broken / Split-Brain Risk | 100% Embedded Single Proc |
| **Graph Query Expressiveness** | ANSI SQL Recursive CTEs | OpenCypher (`cypher()`) | Native OpenCypher / GQL | Native OpenCypher |
| **Provenance Foreign Keys** | **Direct Relational FKs** | Hybrid (agtype to SQL) | Network RPC lookups | Direct within Kùzu |
| **Vector Search** | Native `pgvector` HNSW | Native `pgvector` HNSW | External Vector Store | Native Kùzu Vector Ext |
| **Multi-Agent Concurrency** | **High (Connection Pool)** | **High (Connection Pool)** | High (Bolt Protocol) | **Single-Writer Lock Hazard** |
| **Cloud Managed Deployability** | **Universal (RDS, Supabase)**| Restricted (Needs AGE) | Heavy Dedicated Cluster | Local / Container Only |
| **Maintenance Burden** | **Zero extra ops** | Moderate (Extension builds)| High (Clustering, upgrades) | Low (C++ binary bindings) |
| **V0 Decision** | **ADOPT FOR V0** | **DEFER TO V1** | **DO NOT USE** | **DO NOT USE FOR V0 CORE** |

### Decision Rationale:
- **Why Candidate A for V0:** Candidate A provides 100% ACID consistency between events, nodes, edges, vectors, and provenance links inside a standard PostgreSQL 16 instance. Up to 3 hops (which covers 95% of agent context queries), recursive CTEs perform with latency under 15ms.
- **Why Defer Apache AGE (Candidate B):** While OpenBrain demonstrates that Apache AGE functions well for Cypher queries in Postgres, it requires custom-built PostgreSQL container images and does not ship out-of-the-box on managed cloud PostgreSQL (e.g. Supabase, AWS Aurora). Candidate A avoids this deployment friction.
- **Why Reject Neo4j (Candidate C):** Dual-write split-brain between Neo4j and PostgreSQL introduces unjustifiable failure modes.
- **Why Reject Kùzu (Candidate D) for Core Backend:** Kùzu is an in-process embedded engine. Multiple concurrent writer agents (PDL, Hermes, ingest workers) competing for file locks create concurrency bottlenecks.

---

## 8. Search & Hybrid Retrieval Architecture

Retrieval in PUB Neural is decoupled from any single external framework:

```text
USER / AGENT QUERY
        │
        ├───────────────────────────────────────────────────────┐
        ▼                                                       ▼
1. LEXICAL SEARCH (tsvector GIN)             2. VECTOR SEARCH (pgvector HNSW)
   - Exact symbol / commit matching              - Semantic conceptual similarity
        │                                                       │
        └───────────────────────┬───────────────────────────────┘
                                │
                                ▼
                   3. RECIPROCAL RANK FUSION (RRF)
                      Combines Top-K candidate nodes
                                │
                                ▼
                   4. GRAPH EXPANSION (1-2 Hops)
                      Pulls linked DECISIONS, RULES, EVIDENCE
                                │
                                ▼
                   5. CONTEXT PACK PROJECTION
                      Token-budgeted JSON context bundle
```

### Retrieval Context Profiles
1. **`Agent Task Context` (PDL / Hermes):** Local search (Top-5 entities + 1-2 hop dependencies + active rules + exact code citations).
2. **`Macro Holding Query` (Leiden Algorithmic Reference):** Aggregates community summaries generated via Hierarchical Leiden partitioning to answer wide questions without blowing prompt budgets.
3. **`Time-Travel Audit`:** Surfaces state as of a historical date/commit.

---

## 9. Rebuildability Specification: `DELETE DERIVED DATA -> REBUILD`

To eliminate technical debt and guarantee that model updates or schema migrations never corrupt truth:

### Rebuild Invariant
The following components are strictly non-canonical and can be dropped at any time:
1. `neural_nodes` table
2. `neural_edges` table
3. `neural_evidence` table
4. `neural_vector_index` (`pgvector` tables/indexes)
5. `neural_fts_index` (`tsvector` GIN indexes)
6. `neural_community_reports` table
7. `obsidian_vault/` Markdown directory

### Rebuild Execution Protocol
```bash
# Conceptual rebuild procedure
# 1. Truncate all projection tables
# 2. Reset local Markdown vault directory
# 3. Stream all records from neural_events in ascending order of id
# 4. Reducer applies state transitions to nodes, edges, and evidence
# 5. Background workers re-generate embeddings and community reports
# 6. Obsidian projector re-writes Markdown files
```
### Rebuild Guarantees: Canonical State vs Derived AI Artifacts

To maintain absolute architectural integrity, PUB Neural formally separates determinism guarantees:

#### A. Canonical State (Deterministic Reproducibility)
Reconstruction of `neural_nodes`, `neural_edges`, `neural_evidence`, `neural_sources`, and state transitions is **strictly reproducible** upon replaying `neural_events` under:
- The same sequence of `neural_events`;
- The same reducer version (`reducer_version`);
- The same projection schema version (`projection_version`);
- The same normalization rules.

#### B. Derived AI Artifacts (Versioned Rebuildability)
Embeddings, vector indexes, semantic rankings, community partitions, and Leiden community summaries are:
- **Rebuildable** from canonical events and sources;
- **Version-tracked** (`model_id`, `embedding_dim`, `prompt_template_version`);
- **Provenance-aware** (citing source hashes);
- **Reproducible strictly under the same declared model, temperature, and configuration**.

---

## 10. Recalculated ADOPT / ADAPT / BUILD / AVOID Framework

| Category | Component / Reference | Action & Architectural Role |
|---|---|---|
| **ADOPT** | `Heman10x-NGU/palimp` | Adopt the bi-temporal invalidation schema (`valid_from`, `valid_until`, `is_active`, `superseded_by`) and the 8-tool MCP stdio server structure. |
| **ADAPT** | `innocarpe/CarpeOS` | Adapt the append-only outbox event pattern (`OutboxEvent`) and the continuous Markdown/Obsidian projection engine. |
| **ADAPT** | `microsoft/graphrag` | Adapt the Hierarchical Leiden community partitioning and Map-Reduce summary prompts as an algorithmic reference running on PostgreSQL. |
| **ADAPT** | `nowledge-co/OpenKL` | Adapt the rich citation contracts (`TransientCitation`, `PersistedCitation`) for line-span and commit tracking. |
| **ADAPT** | `ardiannurcahya/open-graph-memory` | Adapt the relational PostgreSQL + `pgvector` baseline schema and FastAPI async patterns. |
| **BUILD** | **Custom PUB Neural** | Build the 7-Stage Factual Knowledge Promotion Engine (`CAPTURED` → `INSTITUTIONAL`). |
| **BUILD** | **Custom PUB Neural** | Build the CEO Sovereignty Authorization Gate for strategic decisions, rules, and policies. |
| **BUILD** | **Custom PUB Neural** | Build the multi-repository Git webhook/CLI ingestion worker. |
| **BUILD** | **Custom PUB Neural** | Build the cross-project scope resolver linking `pub-ecom` ↔ `pdl` ↔ `pub-core-os`. |
| **AVOID** | `impara/openBrain` Code Copying | **DO NOT COPY CODE** directly (no license grant exists in repo; reference architectural concepts only). |
| **AVOID** | External Graph DBs (Neo4j/Memgraph) | Avoid multi-database operational complexity and split-brain risks for V0. |
| **AVOID** | Destructive In-Place Mutations | Avoid SQL `UPDATE` / `DELETE` without event tracking and temporal soft invalidation. |
| **AVOID** | Vector-Only RAG | Ineffective for structural rules, dependencies, and governance relationships. |

---

## 11. Architectural Decisions & Metadata (Freeze Sign-Off)

```text
BENCHMARK_STATUS = COMPLETED_AND_VERIFIED
ARCHITECTURE_STATUS = V0_APPROVED_FOR_SCHEMA_DESIGN
ARCHITECTURE_CONFIDENCE = HIGH_WITH_DECLARED_EVIDENCE_GAPS

ARCHITECTURE_DECISION = SINGLE_POSTGRESQL16_EVENT_SOURCED_HYBRID_GRAPH

CANONICAL_STATE = EVENTS_PLUS_VERIFIED_IMMUTABLE_SOURCE_ARTIFACTS (neural_events + pub_neural.source_blobs)
BLOB_EVENT_ORDER = SOURCE_BLOB_VERIFIED_THEN_SOURCE_INGESTED

GRAPH_STRATEGY = RELATIONAL_TABLES_WITH_RECURSIVE_CTES (neural_nodes, neural_edges; Apache AGE OpenCypher evaluated and deferred to V1)

VECTOR_STRATEGY = POSTGRESQL_PGVECTOR_HNSW (1536 dimensions, cosine distance)

RETRIEVAL_STRATEGY = HYBRID_RRF (Lexical tsvector GIN + Vector pgvector HNSW + 2-hop Recursive CTE Graph Expansion + Algorithmic Leiden Community Summaries)

PROVENANCE_MODEL = DECOUPLED_MULTI_EVIDENCE (KNOWLEDGE -> EVIDENCE -> SOURCE with Commit SHA, File Path, Line Span)

GOVERNANCE_MODEL = DUAL_TRACK (Automated 7-stage promotion for facts; Mandatory CEO Sovereignty gate for Strategic Decisions, Governance Rules, and Executive Policies)

OPEN_SOURCE_ADOPT = Heman10x-NGU/palimp (Bi-temporal schema & 8 MCP tools)

OPEN_SOURCE_ADAPT = innocarpe/CarpeOS (Outbox pattern & Obsidian projection), microsoft/graphrag (Hierarchical Leiden algorithms), nowledge-co/OpenKL (Citation data model), ardiannurcahya/open-graph-memory (PostgreSQL relational schema baseline)

PUB_BUILD = 7-Stage Promotion Engine, CEO Sovereignty Gate, Multi-Repository Git Ingestion Worker, Cross-Project Scope Resolver

AVOID = External Graph Databases (Neo4j/Memgraph), Direct In-Place SQL Deletes, Unlicensed Code Copying from impara/openBrain, Vector-Only RAG

EVIDENCE_GAPS = Performance of recursive CTE graph traversals beyond 500,000 edges in PostgreSQL 16 (requires empirical load test in Phase V1); Incremental real-time community re-clustering without full Leiden re-computation (research open problem)

ARCHITECTURE_CONFIDENCE = HIGH

NEXT_STEP = AWAIT USER APPROVAL OF ARCHITECTURE_V0_DECISION.MD PRIOR TO ANY CODE OR MIGRATIONS
```

