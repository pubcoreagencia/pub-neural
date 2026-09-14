# Architectural Decision: getzep/graphiti

## Final Decision
```text
DECISION: INSPIRE — temporal/contradiction patterns (ALGORITHMIC INSPIRATION)
```

## Concrete Rationale
1. **Code Adoption Rejected:** Importing `graphiti-core` is strictly prohibited because it introduces a hard dependency on Neo4j or FalkorDB, violating PUB Neural's single-store PostgreSQL 16 architecture.
2. **Algorithmic Value Adopted:** Graphiti's prompt-driven contradiction detection (`dedupe_edges.py`) and four-timestamp edge invalidation model (`valid_at`, `invalid_at`, `created_at`, `expired_at`) provide a validated algorithmic blueprint.
3. **Execution Plan:** In a future phase, port the edge invalidation prompt logic into a native Python worker that executes relational transitions against `pub_neural.neural_edges` in PostgreSQL.
