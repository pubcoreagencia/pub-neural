# PUB Neural

Cérebro cognitivo, memória episódica/semântica e orquestrador multiagente.

Consulte o [MASTER_CONTEXT.md](./MASTER_CONTEXT.md) para detalhes completos de governança e arquitetura.

## Neural Runtime Baseline V0.3

- **Architecture chain:** HTTP → Bearer Auth → NeuralQueryService → HybridSearchAdapter → HybridSearchEngine → PostgreSQL (RLS) → Event Sourcing.
- **Implemented & Validated:** Gate contracts, NeuralQueryService, NeuralExperienceService, PreTaskKnowledgeGate, PostTaskExperienceGate, Controlled E2E loop.
- **Pilot / Experimental:** Production HTTP transport, REST/FastAPI API, MCP connector, background daemon.
- **Not Yet Proven:** Autonomous learning, self‑promotion, SaaS offering.
