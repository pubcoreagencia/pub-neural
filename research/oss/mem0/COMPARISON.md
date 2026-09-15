# Mem0 vs. PUB Neural — Concrete Comparison

| Capability | PUB Neural | Mem0 | Comparison Analysis |
| :--- | :--- | :--- | :--- |
| **Knowledge Scope** | Institutional organizational memory and governance | Personal agent chat memory and user preferences | PUB Neural models enterprise knowledge; Mem0 models conversation turns. |
| **Event Sourcing** | Strict append-only event ledger (`neural_events`) | Mutable memory store with ADD-only default and delete API | PUB Neural guarantees full auditability; Mem0 can be mutated or wiped. |
| **Graph Modeling** | Relational LPG tables (`neural_nodes`, `neural_edges`) | None in OSS SDK (Graph is proprietary Platform feature) | PUB Neural maintains a native relational graph; Mem0 OSS has no graph relationships. |
| **Hybrid Retrieval** | True dual-leg independent retrieval (FTS + vector) via RRF | Asymmetric boost: Vector generates all candidates; BM25 boosts | PUB Neural guarantees keyword recall for exact code tokens; Mem0 misses candidates if vector misses. |
| **Security & Tenancy**| PostgreSQL Row-Level Security (RLS) + Trust Zones | Application-level query filters (`filters={"user_id": ...}`) | PUB Neural provides database-enforced boundaries; Mem0 has zero database-level authorization. |
| **Ontology & Typing** | 16 entity types, 14 relation types, 8 promotion states | Unstructured text strings with arbitrary metadata | PUB Neural enforces strict typing; Mem0 has no formal ontology. |
