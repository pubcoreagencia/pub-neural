# PUB Neural Console V0 — Architecture Specification

## 1. Overview & Core Philosophy

The **PUB Neural Console V0** is a strictly **read-only** operator interface for exploring the PUB Neural institutional knowledge graph, event ledger, and runtime status.

### Core Architectural Invariants
1. **Read-Only Boundary**: The Console never mutates, executes tasks, creates decisions, promotes entities, or alters governance. Mutation HTTP methods (`POST`, `PUT`, `DELETE`, `PATCH`) return `405 Method Not Allowed`.
2. **Single Source of Truth**:
   - Git remains the sole authority over application code.
   - The PostgreSQL 16 + pgvector neural database remains the sole authority over knowledge, events, and temporal state.
3. **No Alternative Stores**: No Neo4j, Redis, SQLite, or secondary cache stores are introduced.
4. **Deterministic Graph Layout**: Node and edge positioning is deterministic and bounded, without physics-based simulation engines (`d3-force`).

---

## 2. System Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              BROWSER CLIENT                                 │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │ TOP BAR: System Status (Health, PG Engine, Capabilities, Mode Toggle) │  │
│  ├─────────────────┬─────────────────────────────┬───────────────────────┤  │
│  │ EXPLORER        │ CENTER VIEW                 │ DEEP INSPECTOR        │  │
│  │ - Hybrid Search │ - GraphCanvas (@xyflow)     │ - Entity Inspector    │  │
│  │ - Entity List   │   OR                        │   OR                  │  │
│  │ - Abstention UI │ - TimelineView (Events)     │ - Event Inspector     │  │
│  └─────────────────┴─────────────────────────────┴───────────────────────┘  │
└──────────────────────────────────────┬──────────────────────────────────────┘
                                       │ HTTP / Bearer Auth
                                       ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                    READ-ONLY BACKEND SERVICE (:8080)                        │
│  - Python Standard Library HTTPServer (Zero external framework deps)        │
│  - Presentation boundaries / typed DTOs (Zero row or secret leakage)        │
│  - RLS Session Attachment (pub_neural_app db_role)                          │
└──────────────────────────────────────┬──────────────────────────────────────┘
                                       │ SQL (READ ONLY)
                                       ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│               CANONICAL POSTGRESQL 16 + PGVECTOR CONTAINER                  │
│  - Schema: pub_neural (15 tables, RLS enforced)                             │
│  - Event Sourcing: pub_neural.neural_events & neural_event_parents           │
│  - Projections: neural_nodes, neural_edges, neural_evidence                 │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 3. Endpoints Contract

All endpoints except `/health` and unauthenticated status checks require `Authorization: Bearer <session_token>`.

| Method | Route | Description | Query Parameters |
| :--- | :--- | :--- | :--- |
| `GET` | `/health` | Unauthenticated liveness check | None |
| `GET` | `/api/v1/status` | System operational state & capabilities | None |
| `GET` | `/api/v1/search` | Hybrid FTS + pgvector semantic search | `q` (required), `entity_type`, `limit` (max 50) |
| `GET` | `/api/v1/entities/{id}` | Entity detail with bi-temporal bounds & evidence | None |
| `GET` | `/api/v1/entities/{id}/neighborhood` | Bounded graph neighborhood | `depth` (1-2), `limit` (max 150) |
| `GET` | `/api/v1/events` | Chronological event ledger feed | `limit` (max 200), `offset`, `stream_id`, `event_type` |
| `GET` | `/api/v1/events/{id}` | Single event detail, causality parents & payload | None |

---

## 4. Synchronized Bidirectional Navigation

The human exploration workflow is fully bidirectional between the spatial graph, chronological timeline, and deep inspector:

```
[Graph Entity Node] ──(Click Node)──────────► [Entity Inspector]
        ▲                                            │
        │                                 (Click Originating Event)
  (Focus in Graph)                                   ▼
        │                                    [Event Timeline]
        │                                            │
[Event Inspector] ◄──(Click Event Row)───────────────┘
```

- **Graph Entity → Inspector**: Clicking an entity node in the canvas or search sidebar opens the Entity Inspector with provenance, evidence quotes, and bi-temporal bounds.
- **Entity Inspector → Timeline**: Clicking the `Originating Event` link switches the center pane to `TimelineView`, focuses the specific event, and opens the `EventInspector`.
- **Timeline → Event Inspector**: Clicking any event card opens its causal predecessors, stream governance, and sanitized JSON audit payload in the right pane.
- **Event Inspector → Graph**: If the event is associated with an entity (via `node_id`, `entity_id`, or `entity:` stream prefix), a prominent `Focus in Graph →` button switches the center view to `GraphCanvas` and focuses that node.

---

## 5. Three-Tier Temporal Model

PUB Neural strictly separates three distinct temporal dimensions to prevent temporal confusion:

1. **Event Time (Ledger Clock)**:
   - Field: `recorded_at` in `neural_events`.
   - Semantics: The immutable, monotonic instant when the transition occurred in the system.
   - UI Label: `EVENT TIME (IMMUTABLE LEDGER RECORD)`.
2. **Business Validity Time**:
   - Fields: `valid_from` and `valid_until` in `neural_nodes`.
   - Semantics: The real-world duration during which the decision, rule, pattern, or policy is active and applicable.
   - UI Label: `BUSINESS TIME (VALIDITY)`.
3. **System Audit Time**:
   - Fields: `recorded_from` and `recorded_until` in `neural_nodes`.
   - Semantics: The database record transaction duration in the relational projection.
   - UI Label: `SYSTEM TIME (AUDIT RECORD)`.

---

## 6. Status Semantic Mapping

The `SystemStatusBar` maps system state deterministically to avoid masking errors or generating false alarms:

| Semantic State | Condition | Visual Treatment |
| :--- | :--- | :--- |
| `HEALTHY` | `database_connected == true` and zero projection errors | Green badge (`#34d399`) |
| `DEGRADED` | Database connected but checkpoint errors present or partial availability | Amber badge (`#fcd34d`) |
| `UNAVAILABLE` | `database_connected == false` or backend offline | Crimson badge (`#f87171`) |
| `ERROR` | API request failure or 500 error | Bright red badge (`#fca5a5`) |

---

## 7. Performance & Security Guarantees

- **Bounded Queries**:
  - Events endpoint enforces `min(limit, 200)`.
  - Graph neighborhood enforces `depth <= 2` and `limit <= 150`.
  - Search limits bounded to `max_search_limit = 50`.
- **Zero Secret Leakage**:
  - Backend recursively redacts credential keys: `machine_secret`, `secret`, `password`, `token`, `bearer_token`, `session_token_hash`, `private_key`.
  - Frontend never exposes raw tokens, secrets, or internal digests.
- **RLS Session Enforcement**:
  - Connections attach session context via `pub_neural.establish_session_context` and evaluate all projection queries under Row Level Security.
