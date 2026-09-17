# PUB Neural | External Capability Allocation

**Status:** Canonical direction
**Date:** 2026-09-16

## Purpose

Registrar a alocação das capacidades observadas no research externo do dia sem importar projetos inteiros e sem criar duplicação arquitetural.

**Princípio:** não importar projetos; importar capacidades comprovadas.

## Research sources

- Graphify: https://github.com/Graphify-Labs/graphify
- PAUL: https://github.com/ChristopherKahler/paul
- Coolify: https://github.com/coollabsio/coolify
- OpenHands: https://github.com/openhands
- Maxun: https://github.com/getmaxun/maxun
- Open WebUI: https://github.com/open-webui/open-webui
- Browser Use: https://github.com/browser-use/browser-use
- Crawl4AI: https://github.com/unclecode/crawl4AI

## Capability allocated to PUB Neural

### 1. Graphify

**Owner:** PUB Neural

Absorb as architectural reference for graph-based knowledge representation, especialmente:

- relações explícitas versus inferidas;
- provenance/evidence por relação;
- confidence da inferência;
- code/repository dependency graph;
- navegação de entidades e relacionamentos.

### Target model

PUB Neural deve evoluir para representar, quando aplicável:

`SOURCE → OBSERVATION → ENTITY → RELATIONSHIP → EVIDENCE → INFERENCE → CONFIDENCE → TEMPORAL_STATE`

Relações extraídas diretamente da evidência devem ser distinguíveis de relações inferidas.

Uma resposta do Neural deve poder apontar para evidência, fonte, commit/documento e, quando disponível, localização precisa da evidência.

### 2. Crawl4AI / Maxun

**Execution owner:** PUB Machine
**Knowledge owner:** PUB Neural

PUB Neural não será crawler.

Quando PUB Machine coletar conteúdo estruturado, o Neural poderá receber:

- documento/fonte;
- observação;
- entidade;
- relacionamento;
- sinal temporal;
- evidência/proveniência;
- chunks e embeddings;
- resultado de extração estruturada.

Fluxo canônico:

`PUB Machine capture → normalize → PUB Neural store/relate/learn`

### 3. Browser Use

**Execution owner:** PUB Machine
**Integration:** ACP/Control Plane
**Knowledge destination:** PUB Neural

Browser Use é referência para capacidade de navegação e interação com Web real. O Neural recebe apenas resultados, evidências e observações relevantes, não controla browser diretamente.

## Non-duplication rules

1. PUB Neural não implementa browser runtime.
2. PUB Neural não implementa crawler runtime.
3. PUB Neural não vira UI operacional.
4. PUB Neural não replica o Control Room.
5. PUB Neural não incorpora código inteiro dos projetos pesquisados.
6. Captura e execução pertencem à infraestrutura de execução; interpretação, memória, relações e conhecimento pertencem ao Neural.

## Implementation priority

### P0
- Provenance/evidence model.
- Explicit vs inferred relationship semantics.
- Confidence and source lineage.
- Temporal/bi-temporal relationship support.
- Integration contract for observations received from PUB Machine.

### P1
- Repository/code graph enrichment.
- Web/document entity extraction ingestion.
- Cross-project relationship graph.

### P2
- Advanced graph traversal and derived insights.
- Continuous knowledge promotion from observations.

## Relationship to other PUB projects

- **PDL:** produces engineering decisions, plans, execution evidence and lessons that may become Neural knowledge.
- **PUB ACP:** provides controlled execution/orchestration boundaries; Neural does not replace ACP.
- **PUB Machine:** captures web/data/execution outputs; Neural institutionalizes the useful information.
- **Control Room:** observes and operates the ecosystem; Neural supplies knowledge and context.

## Operational principle

`PUB Machine captures → PUB Neural understands and remembers → PDL reasons → ACP executes → Control Room observes.`
