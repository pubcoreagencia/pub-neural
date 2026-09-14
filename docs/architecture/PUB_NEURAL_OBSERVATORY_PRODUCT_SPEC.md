# PUB Neural Observatory — Product & Experience Specification

## Status

```text
STATUS: DESIGN_READY
IMPLEMENTATION STATUS: NOT IMPLEMENTED / FUTURE PRODUCT SPECIFICATION
CLASSIFICATION: TARGET / FUTURE / PRODUCT VISION
GOVERNANCE CHECKPOINT: 2026-09-14
```

---

## 1. Vision & Purpose

```text
CLASSIFICATION: PRODUCT VISION (FUTURE / NOT IMPLEMENTED)
```

O **PUB Neural Observatory** é a visão de produto para a camada de experiência visual do PUB Neural. Futuramente, o sistema deverá dispor de uma interface intuitiva, convidativa e *product-ready* para exploração, governança e inspeção da memória institucional da PUB Core Holding.

A referência conceitual é a clareza e densidade relacional de ferramentas de *knowledge graph* (inspirada na estética e navegação fluida de grafos como a do Obsidian), mas **sem ser um mero clone de anotações pessoais**. Trata-se de um observatório de inteligência organizacional orientado a tomada de decisão, auditoria e colaboração entre humanos e agentes autônomos.

### Perguntas Fundamentais que o Observatory Responderá:
1. **O que o Neural sabe?** (Mapa visual do conhecimento estruturado).
2. **Como os conhecimentos estão conectados?** (Relações ontológicas e dependências reais).
3. **De onde uma informação veio?** (Rastreabilidade de repositório, commit, arquivo e autor).
4. **Por que uma decisão existe?** (Justificativa, contexto e alternativas descartadas).
5. **Quais evidências sustentam um conhecimento?** (Citações exatas, linhas de código e testes executados).
6. **O que mudou?** (Timeline de evolução, mutações e substituições).
7. **O que está incerto ou conflitante?** (Itens em estado `CANDIDATE` ou `CONTRADICTORY`).
8. **O que precisa de atenção humana?** (Decisões pendentes de ratificação pelo CEO).

---

## 2. Product Principles

### 2.1 INFRASTRUCTURE-FIRST, PRODUCT-READY

```text
CLASSIFICATION: PRINCIPLE
```

- O PUB Neural nasce e se consolida primeiramente como **infraestrutura interna e cérebro cognitivo** da PUB Core Holding.
- No entanto, a arquitetura de dados e a experiência visual devem nascer preparadas para uma eventual transformação futura em produto SaaS B2B.
- **Diretriz de Design:** Evitar terminologias excessivamente esotéricas ou interfaces de terminal cruas que impeçam o uso por lideranças de negócio. A usabilidade interna deve ter padrão de produto comercial, sem iniciar comercialização prematura.

### 2.2 CEO-FIRST COMPREHENSION

```text
CLASSIFICATION: PRINCIPLE
```

- A experiência visual deve permitir que um CEO ou tomador de decisão compreenda instantaneamente o estado essencial da organização em segundos.
- Não deve ser necessário dominar PostgreSQL, pgvector, HNSW, RRF, Stored Procedures ou bi-temporalidade para responder:
  - *O que o sistema sabe?*
  - *Por que sabe?*
  - *De onde veio?*
  - *O que mudou?*
  - *O que está incerto?*
  - *O que precisa de mim agora?*
- Detalhes matemáticos e de banco de dados continuam disponíveis sob demanda através de níveis de inspeção técnica aprofundada (*progressive disclosure*).

---

## 3. Future Product Layers

```text
CLASSIFICATION: TARGET ARCHITECTURE (NOT IMPLEMENTED)
```

O ecossistema de produto do PUB Neural projeta-se em três camadas canônicas:

```text
┌─────────────────────────────────────────────────────────────┐
│                        NEURAL CLOUD                         │
│   (Futuro SaaS: Workspaces, Multi-Tenancy, Billing, APIs)   │
│   [STATUS: NÃO IMPLEMENTADO / VISÃO FUTURA]                 │
├─────────────────────────────────────────────────────────────┤
│                      NEURAL EXPERIENCE                      │
│   (Observatory: Graph, Now, Inspector, Activity, Health)    │
│   [STATUS: NÃO IMPLEMENTADO / ESPECIFICAÇÃO DE DESIGN]      │
├─────────────────────────────────────────────────────────────┤
│                        NEURAL ENGINE                        │
│   (Postgres 16, pgvector, Event Sourcing, Projector, RLS)   │
│   [STATUS: OPERACIONAL / BASELINE V0.1 CONGELADO]           │
└─────────────────────────────────────────────────────────────┘
```

1. **NEURAL ENGINE (Existente / Baseline V0.1):**
   - Imutabilidade via event sourcing (`pub_neural.neural_events`).
   - Projeções relacionais determinísticas (`projector_engine.sql`).
   - Busca híbrida lexical + vetorial com RRF (`HybridSearchEngine`).
   - RLS, políticas de abstenção e controle de proveniência criptográfica.
2. **NEURAL EXPERIENCE (Futuro / Observatory):**
   - As superfícies visuais de navegação: Graph, Neural Now, Context Inspector, Activity Timeline e Health Monitoring.
3. **NEURAL CLOUD (Futuro / Longo Prazo):**
   - Camada multi-tenant para terceiros, federação de workspaces, cotas, faturamento e integrações externas.

---

## 4. Observatory Visual Modules (Design Target)

```text
CLASSIFICATION: TARGET / FUTURE MODULES (NOT IMPLEMENTED)
```

### 4.1 NEURAL GRAPH (Grafo Semântico Dinâmico)
- **Conceito:** Visualização em grafo onde nós são entidades vivas e arestas são relações causais reais, não mera decoração cosmética.
- **Entidades Representadas:**
  - `PROJECT`, `REPOSITORY`, `DOCUMENT`, `SOURCE`, `EVIDENCE`
  - `DECISION`, `RULE`, `GOVERNANCE`, `PATTERN`, `LESSON`, `SKILL`
  - `COMMIT`, `TEST`, `AGENT`, `TASK`
- **Relações Canônicas Mapeadas:**
  - `DECISION` $\to$ `derived_from` $\to$ `EVIDENCE`
  - `DECISION` $\to$ `affects` $\to$ `PROJECT`
  - `DECISION` $\to$ `implemented_by` $\to$ `COMMIT`
  - `DECISION` $\to$ `validated_by` $\to$ `TEST`
  - `DECISION` $\to$ `evolved_into` $\to$ `RULE`
  - `LESSON` $\to$ `discovered_in` $\to$ `TASK`
  - `PATTERN` $\to$ `supported_by` $\to$ `EVIDENCE`

### 4.2 NEURAL NOW (Visão de Contexto Ativo)
- **Conceito:** Dashboard contextual que responde à pergunta executiva: *"O que importa agora?"*.
- Em vez de sobrecarregar o usuário com o universo de milhares de nós, renderiza um cluster focado contendo:
  - Objetivo em andamento e projeto ativo.
  - Decisões e regras diretamente incidentes sobre a sprint/tarefa.
  - Lições e advertências de falhas passadas pertinentes.
  - Evidências e agentes em execução.
  - Pontos de atenção que demandam revisão ou desempate humano.

### 4.3 CONTEXT INSPECTOR (Inspeção Profunda com Proveniência)
- **Conceito:** Painel lateral de inspeção ativado ao selecionar qualquer entidade no grafo.
- Apresenta significado claro, procedência e cadeia de custódia:
  ```text
  [ENTIDADE]
  DECISION: Adopt Hybrid Retrieval V0.1 (RRF + pgvector)

  [POR QUE EXISTE?]
  Supera deficiências de busca exclusivamente lexical em termos conceituais
  e mitiga alucinações de busca puramente vetorial em nomes de arquivos exatos.

  [ORIGEM & REPOSITÓRIO]
  pubcoreagencia/pub-neural (docs/ARCHITECTURE_V0_DECISION.md)

  [VALIDADE TEMPORAL]
  CURRENT / VALIDATED (Baseline V0.1 Freeze)

  [EVIDÊNCIAS & PROVENIÊNCIA]
  - Commit: f4d6521f18ae5e90...
  - Testes: tests/vector/test_hybrid_retrieval_and_vectors.py (17 PASS)
  - Hash SHA-256: 8d5e86352816c7820d4b...
  ```

### 4.4 NEURAL ACTIVITY (Linha do Tempo Factível)
- **Conceito:** Stream cronológico de eventos reais extraídos diretamente de `pub_neural.neural_events`.
- Exemplos de marcos exibidos:
  - *New evidence captured from repository commit X*
  - *Candidate lesson extracted by developer agent*
  - *Decision ratified by CEO mandate*
  - *Knowledge superseded due to architectural refactoring*
- **Regra Estrita:** Zero animações cosméticas ou gráficos falsos. Todo ponto na linha do tempo reflete um registro imutável do banco de dados.

### 4.5 KNOWLEDGE HEALTH (Monitoramento da Saúde do Conhecimento)
- **Conceito:** Indicadores visuais de integridade da base de conhecimento, reutilizando estritamente a ontologia existente:
  - `VALIDATED`: Conhecimento consolidado com testes e evidências aprovados.
  - `OBSERVED`: Padrão ou fato detectado empiricamente, aguardando validação formal.
  - `CANDIDATE`: Lição recém-ingerida pelo PDL, ainda em escopo local de projeto.
  - `CONTRADICTORY`: Conhecimentos colidentes sinalizados para resolução executiva.
  - `STALE`: Conhecimento apontando para arquivos/commits alterados ou obsoletos.
  - `UNVERIFIED`: Afirmações herdadas sem cadeia completa de evidência.

### 4.6 AGENTS VIEW (Superfície de Operação dos Agentes)
- **Conceito:** Painel conceitual de representação de papéis cooperativos:
  - `Researcher`: Agente de análise de documentação e coleta contextual.
  - `Architect`: Agente de validação de padrões e decisões estruturais.
  - `Engineer`: Especialista executor de código e testes empíricos.
  - `Reviewer`: Auditor de conformidade, segurança e governança.
  - `Neural`: O próprio orquestrador cognitivo mantendo o estado unificado.
- Exibe a tarefa atual, o recorte de contexto neural consumido, as evidências geradas e o estado factual da esteira.
- *Nota Factual:* Esses nomes representam papéis na experiência visual projetada, e não afirmam a existência desses agentes como processos autônomos em runtime hoje.

---

## 5. Implementation Roadmap & Non-Goals

### Roadmap Futuro
- **Fase 1 (Atual):** Especificação conceitual e institucionalização no Master Context.
- **Fase 2 (Próxima):** Conclusão do Bidirectional Neural Knowledge Gate (PDL $\leftrightarrow$ Neural).
- **Fase 3 (Futura):** Prototipagem da interface estática de leitura baseada nas projeções SQL (`neural_nodes`, `neural_edges`).
- **Fase 4 (Futura):** Implementação interativa do grafo, timeline e context inspector.

### Critical Non-Goals (O que NÃO fazer)
- **NÃO** construir frontend web, React, Vue, Next.js ou Svelte nesta fase.
- **NÃO** criar mocks de visualização que simulem interatividade fictícia.
- **NÃO** alterar schemas de banco para acomodar bibliotecas visuais antes do Gate estar funcional.
- **NÃO** desviar recursos da estabilização da esteira governada entre PDL e PUB Neural.
