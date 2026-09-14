# PUB Neural Console V0 — Integration Specification

```text
STATUS: NOT IMPLEMENTED / FUTURE DESIGN SPECIFICATION
```

## 1. System Placement
`@xyflow/react` is selected as the graph visualization engine for the future **PUB Neural Console**.

```text
┌──────────────────────────────────────────────┐
│            PUB NEURAL CORE (PG16)            │
│   (Canonical Source of Truth & Governance)   │
└──────────────────────┬───────────────────────┘
                       │ Read-Only SQL / Bearer Session
                       ▼
┌──────────────────────────────────────────────┐
│           PUB NEURAL CONSOLE (V0)            │
│ ┌──────────────────────────────────────────┐ │
│ │ Graph View Motor: @xyflow/react          │ │
│ │ • Custom Nodes: DECISION, RULE, PATTERN  │ │
│ │ • Custom Edges: USES, DEPENDS_ON         │ │
│ │ • Layout Engine: Dagre + d3-force        │ │
│ └──────────────────────────────────────────┘ │
│ ┌──────────────────────────────────────────┐ │
│ │ Search, Inspector, Timeline (Pure React) │ │
│ └──────────────────────────────────────────┘ │
└──────────────────────────────────────────────┘
```

## 2. Layout Strategy
1. **Lineage & Provenance Views:** Use `@dagrejs/dagre` for top-to-bottom hierarchical layout (`SourceBlob` $ightarrow$ `Evidence` $ightarrow$ `Node` $ightarrow$ `Decision`).
2. **Knowledge Exploration Views:** Use `d3-force` to pre-calculate force-directed equilibrium coordinates, feeding `{ x, y }` positions to React Flow nodes.

## 3. Boundaries & Invariants
* React Flow is strictly a presentation component.
* It will never persist state directly or act as a source of truth.
* All displayed knowledge is fetched from PostgreSQL via authenticated read-only queries.
