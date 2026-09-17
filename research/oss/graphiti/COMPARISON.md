# Graphiti vs. PUB Neural — Concrete Comparison

| Capability | PUB Neural | Graphiti | Comparison Analysis |
| :--- | :--- | :--- | :--- |
| **Storage Engine** | PostgreSQL 16 + pgvector | Neo4j / FalkorDB | Graphiti requires external graph database clusters; PUB Neural uses a single ACID relational store. |
| **Event Sourcing** | Append-only canonical ledger (`neural_events`) with causal DAG | Episodic input nodes with mutable in-place graph state | PUB Neural guarantees auditability and deterministic replay; Graphiti mutates graph state in place. |
| **Temporal Model** | Bi-temporal (`valid_from/until` + `recorded_from/until`) | Bi-temporal edge model (`valid_at`, `invalid_at`, `created_at`, `expired_at`) | Architecturally aligned. Graphiti's edge model is a validated algorithmic pattern. |
| **Contradiction Handling** | `neural_conflict_state` + `superseded_by` foreign keys | LLM prompt classifies contradiction and sets `invalid_at` | Graphiti's prompt strategy is highly effective and can inspire PUB Neural workers. |
| **Governance & Security** | PostgreSQL Row-Level Security (RLS) + CEO sovereignty | Application-level Cypher filtering (`WHERE n.group_id = ...`) | PUB Neural enforces database engine-level security; Graphiti has no database-enforced multi-tenancy. |
| **Ontology Model** | Closed domain enums (16 entities, 14 relations) | Pydantic classes or open-ended learned ontology | PUB Neural prevents schema drift; Graphiti is flexible but susceptible to loose naming. |
| **Abstention Gate** | Explicit `RetrievalAbstentionPolicy` evaluating scores | None (relies on downstream LLM prompts) | PUB Neural provides deterministic guarantees against ungrounded hallucinations. |
