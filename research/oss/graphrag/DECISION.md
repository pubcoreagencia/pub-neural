# Architectural Decision: microsoft/graphrag

## Final Decision
```text
DECISION: INSPIRE — community detection / global retrieval patterns (ALGORITHMIC INSPIRATION)
```

## Concrete Rationale
1. **Code & Storage Adoption Rejected:** GraphRAG's codebase is in official maintenance mode and relies on Parquet/LanceDB file storage, which is incompatible with PUB Neural's transactional PostgreSQL 16 foundation.
2. **Algorithmic Value Adopted:**
   * **Hierarchical Leiden Clustering:** The mathematical clustering algorithm and community report prompts directly inform how PUB Neural will populate its existing `pub_neural.neural_community_reports` table.
   * **DRIFT / Global Query Patterns:** The concept of querying pre-computed community summaries to answer broad institutional questions provides a blueprint for future high-level retrieval.
3. **Execution Plan:** In a future phase, create a background worker in Python that reads nodes and edges from PostgreSQL, executes Leiden clustering via `graspologic`, generates community reports via LLM, and writes them back to PostgreSQL.
