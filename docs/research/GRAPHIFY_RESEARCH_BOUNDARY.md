# PUB NEURAL — GRAPHIFY RESEARCH BOUNDARY & GOVERNANCE SPECIFICATION

**Status:** CANONICAL BOUNDARY CONTRACT  
**Document ID:** `docs/research/GRAPHIFY_RESEARCH_BOUNDARY.md`  
**Consolidation Date:** 2026-09-17  

---

## 1. Definição do Papel da Engine

```text
GRAPHIFY
=
STRUCTURAL EXTRACTION CAPABILITY
```

### O que o Graphify PODE fazer:
- Analisar repositórios e código fonte (ASTs Tree-sitter, imports, definições, chamadas);
- Extrair entidades de código (módulos, classes, funções, tabelas, schemas);
- Extrair relações estruturais (`CALLS`, `IMPORTS`, `CONTAINS`, `BELONGS_TO`);
- Construir grafos locais de sintaxe e dependência;
- Detectar partições e comunidades via modularidade Louvain / Leiden;
- Fornecer métricas topológicas (pontes, nós centrais / god-nodes, densidade estrutural).

### O que o Graphify NÃO PODE fazer:
- **Decidir o que é verdade institucional:** Toda relação extraída é candidata ou factual de código, não uma diretriz da holding;
- **Promover conhecimento:** Graphify não transiciona estados para `VALIDATED`, `ADOPTED` ou `INSTITUTIONAL`;
- **Definir governança:** Graphify não dita regras arquiteturais ou restrições de negócio;
- **Substituir o Research:** Graphify não formula perguntas, não valida hipóteses e não sintetiza decisões;
- **Substituir o Neural Memory:** Graphify é efêmero/extrator; a memória canônica reside no PostgreSQL (`neural_events`, `neural_nodes`, `neural_edges`);
- **Substituir o Hybrid Retrieval:** O grafo gerado é apenas 1 das 3 pernas da busca híbrida (FTS + Vector + Graph);
- **Criar a ontologia canônica:** Graphify obedece aos mapeamentos do `GraphifyNormalizer`, sem forjar tipos fora do enum fechado do Neural.

---

## 2. Fronteira de Segurança e Sandboxing

Graphify opera sob **estrito princípio de menor privilégio**. Ele **NUNCA** acessa diretamente o banco de dados do Neural (`neural_events`, `neural_nodes`).

```text
┌────────────────────────────────────────────────────────┐
│                   EXTERNAL CODEBASE                    │
│            (Snapshot / Git Clone no Worker)            │
└──────────────────────────┬─────────────────────────────┘
                           │
                           ▼
┌────────────────────────────────────────────────────────┐
│                  SANDBOX RUNTIME                       │
│  - Isolado do banco de dados (Zero DB credentials)     │
│  - Executa: `graphify extract <dir> --out graph.json`  │
│  - Timeouts defensivos e limites de memória de SO      │
└──────────────────────────┬─────────────────────────────┘
                           │ Emite artefato estático
                           ▼
┌────────────────────────────────────────────────────────┐
│               ARTIFACT SECURITY BOUNDARY               │
│                     (graph.json)                       │
│  - Sanitização de credenciais e segredos vazados       │
│  - Validação estrita de JSON Schema                    │
│  - Defesa contra ataques de negação (Caps de nós/edges)│
└──────────────────────────┬─────────────────────────────┘
                           │
                           ▼
┌────────────────────────────────────────────────────────┐
│                 PUB NEURAL INGESTION                   │
│             (Adapter → Normalizer → Ingestor)          │
│  - Converte nós e links para eventos canônicos         │
│  - Persiste via pub_neural.append_event()              │
└────────────────────────────────────────────────────────┘
```

---

## 3. Design da Futura Automação (Future Graphify Worker)

Embora a implementação de código esteja congelada nesta etapa, o desenho arquitetural do futuro worker fica formalizado:

```text
Research Task / Ingestion Event
      ↓
Extraction Job Enqueued
      ↓
Graphify Worker (Ephemeral Sandbox)
      ↓
graph.json (Validated Artifact)
      ↓
GraphifyAdapter (Caps & Secrets Check)
      ↓
GraphifyNormalizer (Canonical Mapping)
      ↓
GraphifyIngestor (Events Appended)
```

### Especificação de Engenharia do Worker:
1. **Trigger:** Evento de novo commit em repositório monitorado ou despacho sob demanda de uma `ResearchTask`.
2. **Queue:** Fila de jobs assíncronos desacoplada do runtime HTTP principal.
3. **Retry & Backoff:** Máximo de 3 tentativas com backoff exponencial; falhas definitivas movem para Dead Letter Queue (DLQ).
4. **Timeouts:** Limite rígido de 300 segundos por repositório médio (ou 600 segundos para monorepos grandes).
5. **Idempotency:** A chave de idempotência é construída sobre `repository:commit_sha:extractor_version:graphify_v8`.
6. **Resource Limits:** Processo encapsulado com limites de memória (ex: 2GB RAM máx) e limite de saída (máx 10.000 nós, 50.000 arestas).
7. **LLM Provider (Semântica):** Opcional e restrito à classificação semântica secundária (OpenAI / Anthropic / Gemini via Gateway com rate-limiting).
8. **Secrets Isolation:** Nenhuma variável de conexão de banco (`DATABASE_URL`) é injetada no subprocesso do Graphify.

---

## 4. Governança e Promoção Epistemológica

A transição de conhecimento segue o modelo canônico de promoção:

```text
EXTRACTED (Graphify AST: conf 0.90) 
    ou
INFERRED (Graphify Co-occurrence: conf 0.65)
    ↓
OBSERVED (Eventos canônicos ENTITY_EXTRACTED / RELATION_EXTRACTED)
    ↓
CANDIDATE (Nós e arestas projetados com flag CANDIDATE)
    ↓
VALIDATED (Verificação empírica por testes e verifier agent)
    ↓
ADOPTED (Aprovado para uso ativo em tarefas de engenharia)
    ↓
INSTITUTIONAL (Ratificado pelo CEO Sovereign em MASTER_CONTEXT.md)
```

> [!CAUTION]
> **REGRA DE GOVERNANÇA ABSOLUTA:**
> O Graphify **jamais promove conhecimento sozinho**. Relações inferidas iniciam como `CANDIDATE` com confiança rebaixada e nunca substituem validações empíricas humanas ou de testes.
