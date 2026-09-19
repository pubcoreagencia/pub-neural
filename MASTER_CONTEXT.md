# MASTER CONTEXT — PUB NEURAL

**Canonical ID:** `pub-neural`  
**Role:** Cognitive brain of PUB Core Holding  
**Status:** `ONLINE / EM DEV`  
**Priority:** `CRITICAL`  
**Consolidation:** 2026-09-11

> This is the canonical agent-facing context for PUB Neural. It consolidates the institutional architecture, project relationships, governance principles and verified knowledge from the PUB ecosystem. It is an index/context layer, not a replacement for source code, tests, migrations, runtime evidence or project-local documentation.

---

## 1. MISSION

PUB Neural is the cognitive layer of PUB Core Holding.

Its mission is to preserve, relate, validate and retrieve knowledge produced across PUB projects so that knowledge does not die inside the repository that created it.

The Neural must evolve into:

```text
PUB NEURAL
├── Knowledge
├── Memory
├── Governance
├── Skills
├── Agents
├── Decisions
├── Patterns
├── Lessons
├── Sources / Provenance
├── Retrieval
└── Orchestration
```

The projects are the **neurons**. Neural is the **brain**.

---

## 2. CORE ARCHITECTURE

```text
                    PUB CORE HOLDING
                           │
                      PUB NEURAL
                        CÉREBRO
                           │
        ┌──────────────────┼──────────────────┐
        │                  │                  │
     PUB ECOM          PUB DEV LOOP       PUB MACHINE
     neurônio            neurônio           neurônio
        │                  │                  │
        └──────────────────┼──────────────────┘
                           │
                    knowledge / events
                           │
                      PUB NEURAL
```

A project remains authoritative for its implementation. Neural becomes authoritative for **consolidated institutional knowledge**, with provenance back to the source.

Do not blindly clone every file into Neural. Extract and normalize reusable intelligence.

Canonical pipeline:

```text
REPOSITORY → AUDIT → DISCOVERY → CLASSIFICATION → EXTRACTION
→ NORMALIZATION → PROVENANCE → VALIDATION → FUSION → NEURAL
```

### Continuity Architecture

```text
CHAT        = exploração e coordenação
PUB NEURAL  = memória e conhecimento institucional estruturado
PDL         = execução governada
GIT         = estado verificável e fonte de verdade versionada
MATHEUS     = operador/CEO e autoridade final
GPT         = orquestração
AGENTS      = execução técnica
```

A continuidade do ecossistema não depende exclusivamente da janela de contexto volátil de uma conversa. O histórico bruto de sessões pode ser preservado, mas não constitui automaticamente conhecimento institucional. Conhecimento duradouro requer estruturação, proveniência, validação e ratificação.

---

## 3. HIERARCHY OF TRUTH

When contexts conflict, use:

```text
CURRENT RUNTIME / DIRECT EVIDENCE
    > REAL EXECUTION
    > TESTS / QA
    > CODE REVIEW
    > VALIDATED DECISIONS
    > VALIDATED SKILLS / PATTERNS
    > ORGANIZATIONAL MEMORY
    > HISTORICAL DOCUMENTATION
    > HYPOTHESES / PROPOSALS
```

Rules:

- `UNKNOWN` is not `DOES NOT EXIST`.
- Absence of evidence is not evidence of absence.
- Historical documentation must not be treated as current runtime truth without verification.
- Any material claim that can change an implementation decision should be revalidated against the source repository/runtime.

---

## 4. NON-NEGOTIABLE GOVERNANCE

### Zero Fake Work

No agent may claim implementation, testing, research or progress without evidence.

### Persistence First

Important knowledge must survive the agent session. Git, databases and persisted artifacts outrank volatile chat memory.

### Provenance First

Every consolidated knowledge item should preserve, when available:

```yaml
source:
  repository: <repo>
  path: <path>
  ref: <branch/tag>
  commit: <sha>
knowledge:
  type: <type>
  scope: <global|project|agent>
  status: <candidate|validated|adopted|superseded>
  confidence: <low|medium|high>
```

### Project Isolation

Project-specific knowledge is not automatically institutional knowledge. Promotion requires evidence and/or governance.

### CEO Sovereignty

Strategic, security, production and major governance decisions remain subject to the human authority defined by PUB.

### Neural Context Institutionalization Rule

Sempre que uma conversa, sessão de trabalho, pesquisa ou execução produzir conhecimento de valor duradouro para a PUB, esse conhecimento deve ser avaliado para institucionalização.

Quando relevante:
1. Identificar o conhecimento;
2. Atualizar o `MASTER_CONTEXT.md` quando for contexto operacional canônico;
3. Registrar em documentação especializada quando necessário;
4. Criar commit;
5. Fazer push;
6. Verificar paridade local/remota.

Princípios da Institucionalização:
- Chat é espaço de exploração e coordenação.
- `MASTER_CONTEXT.md` é o índice operacional canônico.
- PUB Neural é a memória/conhecimento institucional estruturado.
- Git é a fonte de verdade do estado versionado.
- Runtime, Git e evidência real têm estrita precedência sobre memória histórica.
- Nem toda conversa merece ser institucionalizada.
- Histórico bruto não é automaticamente conhecimento institucional.
- Conhecimento institucional deve preservar proveniência e contexto quando aplicável.

### Human / Model / Executor Separation

Existe uma separação explícita de autoridade operacional:
- **OPERADOR HUMANO (Matheus / CEO):** Autoridade final, direção estratégica e decisão soberana.
- **ORQUESTRADOR (GPT / Central):** Análise, estratégia, decomposição de tarefas e coordenação.
- **EXECUTOR (Agentes / Workers):** Inspeção de código, implementação, testes e execução dentro do escopo estritamente autorizado.

Nenhum agente executor possui autoridade superior ao operador humano.

---

## 5. CANONICAL KNOWLEDGE MODEL

Minimum entities:

```text
PROJECT
REPOSITORY
DOCUMENT
SOURCE
EVIDENCE
EVENT
DECISION
RULE
GOVERNANCE
PATTERN
LESSON
SKILL
AGENT
CONCEPT
```

Memory classes:

```text
EPISODIC   = real events and experiences
SEMANTIC   = concepts, facts and relationships
PROCEDURAL = how to execute something
DECISION   = architectural/strategic decisions
LESSON     = validated learning from experience
PATTERN    = recurring validated structure
SKILL      = reusable capability
GOVERNANCE = rules and limits
```

Canonical relations:

```text
USES
DEPENDS_ON
IMPLEMENTS
DISCOVERED_IN
DERIVED_FROM
VALIDATED_BY
SUPPORTED_BY
CONTRADICTS
SUPERSEDES
RELATED_TO
APPLIES_TO
CREATED_BY
USED_BY
REQUIRES
```

The objective is not merely documents. It is **entities + relationships + evidence + provenance + state**.

---

## 6. KNOWLEDGE PROMOTION

New knowledge must not become institutional law automatically.

```text
CAPTURED → OBSERVED → EXTRACTED → CANDIDATE → VALIDATED → ADOPTED → INSTITUTIONAL
```

Parallel states:

```text
CONTRADICTORY
BLOCKED
SUPERSEDED
DEPRECATED
REJECTED
```

Contradiction handling:

```text
DETECT → PRESERVE SOURCES → COMPARE EVIDENCE → RESOLVE / ESCALATE → SUPERSEDE
```

Never silently delete conflicting knowledge.

---

## 7. VERIFIED PROJECT CONTEXTS

### PUB DEV LOOP
`pubcoreagencia/pub-dev-loop`

Role: autonomous software-development platform / THE OFFICE.

Verified Master Context concepts include:

- cloud-first autonomous engineering;
- durable task queue;
- isolated workers;
- resilient LLM gateway fallback;
- worker sovereignty over workspace;
- persistence-first protocol;
- secret isolation;
- zero fake activity;
- five canonical Office roles: Chief of Staff, Architect, Developer, Reviewer, QA Engineer;
- CEO sovereignty;
- Decision Context Engine;
- Governed Context Assembly;
- organizational memory;
- memory governance;
- pattern detection;
- lesson validation/retrieval;
- feedback loop;
- organizational intelligence/awareness;
- Daily Skill Learning;
- governed autonomous execution;
- multi-project evolution.

Important PDL principle:

```text
CURRENT RUNTIME EVIDENCE > VALIDATED LESSONS > HISTORICAL MEMORY
```

### PUB ECOM
`pubcoreagencia/pub-ecom`

Role: central commerce operator / marketplace foundation.

Verified Master Context state consulted:

- Phase 3.9 = COMPLETE / VERIFIED / FROZEN;
- database foundation 00001 → 00015 frozen;
- Node.js HTTP API;
- PostgreSQL transaction boundaries for checkout;
- database-level inventory reservation;
- checkout lifecycle/expiration;
- secure RPC architecture;
- strict RLS;
- isolated service-role operations;
- CORS allowlist;
- foundation/identity/tenant/catalog/commerce/routing/checkout/API checkout tests;
- Render staging planned, not deployed;
- order post-purchase, payment integrations, operational finance/shipping and Next.js frontend were documented as not implemented in the consulted context.

Important reusable patterns include PostgreSQL, RLS/RBAC, transaction boundaries, state machines, inventory, checkout security, API authorization and separation between client input and authoritative financial values.

### PUB MACHINE
`pubcoreagencia/pub-machine`

Role: automated prospecting and business-generation engine.

Verified context state: `VALIDATED / E2E`, priority `HIGH`.

Validated execution checkpoint: `feat/acp-pub-machine-e2e` at commit `b8c97d8`.

The 2026-09-19 checkpoint materialized and verified the causal vertical slice:

```text
RAW SIGNAL → AUDIENCE PROFILE → SEGMENTATION → INTENT → LEAD INTENT
→ LEAD SCORING → DECISION → ACTIVATION → CONVERSION / RECOVERY → FEEDBACK
```

Explicit contracts added/verified include `activation.contract.ts` and `feedback.contract.ts`. The checkpoint was validated with `npm test`, `npm run build`, `git diff --check`, and a clean worktree before local commit. No external WhatsApp, Meta, Google or CRM provider was faked; in-memory doubles remain test-only infrastructure.

Runtime evidence is recorded separately in `docs/integrations/PUB_MACHINE_GPT_ONLY_ACP_VERTICAL_SLICE_2026-09-19.md` with provenance to PUB MACHINE, ACP Standalone and the GPT Free transport POC.

Treat this as validated project knowledge, not holding-wide mandatory architecture. Reuse requires current repository/runtime verification.

### PUB PROTOTYPE / PP
`pubcoreagencia/pub-prototype`

Role: rapid interface/product prototyping environment.

Verified context state: `VALIDATED / PRODUCTION`, priority `HIGH`.

**PP must remain isolated from PDL.** Neural may know both, but every knowledge item must retain project scope.

#### Validated Milestone: Sovereign Dual Gateway V1 (2026-09-17)
- **Architecture:** Dual Gateway inference routing (`GatewayRouter`) across Gateway A (**OpenRouter**) and Gateway B (**9router Cloud**).
- **Governance:** `100% FREE MODELS ONLY` — `PAID_MODEL_EXECUTION = FORBIDDEN` enforced as a hard gate before any network request. Zero paid execution path, zero paid fallbacks, zero paid overrides.
- **Operational Status:**
  - OpenRouter: 10 live-verified FREE models (Streaming PASS).
  - 9router Cloud (`https://pub-9router-cloud.onrender.com/v1`): 10 live-verified FREE models (Streaming PASS).
  - Total Verified FREE: 20 models.
  - Cross-Gateway Fallback: Bidirectional ($A \to B$ e $B \to A$) orquestrado pelo `GatewayRouter` e validado ao vivo.
  - Infraestrutura 9router: Saneamento de segredos persistido no repositório `pubcoreagencia/pub-9router-cloud` (commit `4d73331`).
  - Implementação PP: Commit `61b91cd`, 63 test files, 428 testes unitários passando.
  - Smoke de Produção: Validado em execução real ponta a ponta no Railway Worker com persistência de commit e checkpoint.
- **Detailed Institutional Document:** [docs/architecture/PUB_PROTOTYPE_DUAL_GATEWAY_V1_HANDOFF.md](file:///Users/user/Documents/antigravity/pub%20neural/docs/architecture/PUB_PROTOTYPE_DUAL_GATEWAY_V1_HANDOFF.md)


### PUB NEURAL
`pubcoreagencia/pub-neural`

Role: cognitive brain, memory and multi-agent orchestration layer.

The inspected main branch contains `MASTER_CONTEXT.md`, `README.md` and `AUTONOMOUS_CYCLE.md`. This Master Context is the canonical consolidation layer; future harvesting will populate the underlying knowledge system.

---

## 8. PDL, NEURAL AND HERMES

```text
PUB NEURAL = memory / knowledge / context
PDL        = autonomous execution / development
HERMES     = intake / transport / capture
```

### 8.1 BIDIRECTIONAL NEURAL KNOWLEDGE GATE — CURRENT STATE

**Status:**
- `E1 = READ PATH ACTIVE` (Pre-Task Knowledge Gate implementado e testado no PDL)
- `E2 = WRITE PATH ACTIVE` (Post-Task Experience Gate implementado e integrado no PDL)
- `F = CONTROLLED END-TO-END VALIDATED` (Integração E2E validada em ambiente controlado com 20 cenários fundamentais)
- `PRODUCTION NETWORK INTEGRATION = NOT IMPLEMENTED` (Target architecture / não ativado em produção)

- `RUNTIME HTTP BOUNDARY = IMPLEMENTED AND VALIDATED`
- `PRODUCTION DEPLOYMENT = NOT YET ESTABLISHED`
- `PRODUCTION OPERATIONAL ROLLOUT = NOT YET ESTABLISHED`

**Consolidation Date:** 2026-09-14 (Phase F Checkpoint)

**Current Reality Baseline:**
- **Implementado e Validado:**
  - Contratos tipados canônicos do Gate (`src/gate/models.py`, `src/gate/enums.py`).
  - `NeuralQueryService` interno e `NeuralExperienceService` no PUB Neural com persistência idempotente e event sourcing.
  - `PreTaskKnowledgeGate` e `PostTaskExperienceGate` no PDL com CQRS estrito e fail-open por padrão.
  - Integração ponta a ponta controlada via bridge in-process/process runner (`src.gate.bridge_runner` e `controlled-transport.ts`), validada sobre o repositório piloto `pubcoreagencia/pub-ecom` (fixture de teste E2E).
  - Preservação estrita de proveniência, linhagem de eventos, idempotência determinística e fronteira de dados inertes (`data_only = true`).
- **Ainda NÃO Implementado:**
  - Transporte HTTP de rede de produção, API REST/FastAPI ativa, conector MCP de produção, daemon permanente em background.
  - Aprendizado autônomo, auto-promoção de conhecimento (`CANDIDATE` não se auto-promove), decisões autônomas, pesquisa autônoma, geração autônoma de backlog, SaaS, Neural Cloud.
  - **Regra:** Não confundir "controlled E2E validated" com "production network integrated".

**Ciclo Cognitivo Validado (Controlled E2E):**
```text
TASK
  ↓
PRE-TASK QUERY (PreTaskKnowledgeGate)
  ↓
RETRIEVAL (NeuralQueryService / HybridSearch)
  ↓
CONTEXT (Data-Only Sanitize / ContextAssemblyEngine)
  ↓
EXECUTION (PDL Governed Execution)
  ↓
FINALIZATION (Worktree Clean, Test Evidence)
  ↓
GOVERNANCE / DELIVERY (RemoteDeliveryGate & PersistenceGate)
  ↓
EXPERIENCE WRITEBACK (PostTaskExperienceGate / NeuralExperienceService)
  ↓
EVENT (TASK_EXPERIENCE_RECORDED)
  ↓
CORRELATION (Task Identity, Commit SHA, Event Lineage)
```

**Princípio de Correlação (Current Architectural Capability):**
O sistema agora relaciona formalmente:
`KNOWLEDGE USED BEFORE EXECUTION + TASK EXECUTION + EXPERIENCE RECORDED AFTER EXECUTION`
A memória institucional deixa de ser apenas armazenamento passivo e passa a possuir um ciclo verificável:
`RETRIEVE → EXECUTE → RECORD → CORRELATE`.

**Distinção de Loops:**
- `CONTROLLED BIDIRECTIONAL LOOP = VALIDATED`
- `AUTONOMOUS COGNITIVE LOOP = NOT IMPLEMENTED` (Não existe auto-autorização, auto-promoção, auto-modificação de governança ou auto-geração de backlog).

**Modelo de Autoridade e Hierarquia da Verdade:**
- Matheus: autoridade humana final
- PDL: execução governada
- PUB Neural: memória/conhecimento institucional (DATA ONLY)
- Git: estado versionado verificável
- Runtime: evidência operacional direta
- Hierarquia estrita: `runtime/direct evidence > real execution > test evidence > validated knowledge > historical memory`.
- Nenhum dado recuperado pode sobrescrever governança, Git ou evidência de runtime.

**Semântica de Falhas e Determinismo:**
- `QUERY FAILURE ≠ TASK FAILURE` (Fail-open: PDL prossegue se o Neural estiver indisponível).
- `WRITEBACK FAILURE ≠ TASK FAILURE` (Falha na gravação de experiência não invalida tarefa já aprovada).
- `NO_MATCH ≠ ABSTAIN` | `UNAVAILABLE ≠ NO_MATCH` | `STALE ≠ UNAVAILABLE` | `DUPLICATE WRITEBACK ≠ EXECUTION FAILURE`.
- `DETERMINISTIC SINGLE-SEAM + IDEMPOTENT WRITEBACK`: exatamente 1 query e 1 tentativa final de writeback por ciclo de tarefa. Retries intermediários não duplicam eventos.

**Repositório Piloto:** `pubcoreagencia/pub-ecom` (Projeto: `pub-ecom`). Classificado estritamente como fixture de teste E2E controlado (nenhuma execução comercial real foi alterada).

**Next Architectural Decision:**
A próxima etapa após a validação controlada é decidir como transformar a integração controlada em integração operacional real (fronteira de transporte de produção, serviço de rede autenticado, piloto operacional, rollout controlado, observabilidade, hardening de segurança). Marcado como: `NEXT DECISION REQUIRED`.

Future casual Instagram capture should feed Hermes and then Neural instead of creating an independent knowledge silo:

```text
SOURCE → HERMES INTAKE → QUEUE → RESOLVE → ANALYZE
→ CANDIDATE → VALIDATE → PUB NEURAL
```

---

## 9. AGENT RETRIEVAL CONTRACT

The purpose of this Master Context is to reduce context fragmentation for agents.

Target expected flow (PROPOSED / TARGET ARCHITECTURE):

```text
AGENT REQUEST
   ↓
IDENTIFY PROJECT / SCOPE
   ↓
CONSULT PUB NEURAL
   ↓
RETRIEVE RELEVANT KNOWLEDGE
   ↓
CHECK PROVENANCE / VALIDITY
   ↓
CHECK CURRENT REPOSITORY / RUNTIME
   ↓
ASSEMBLE MINIMUM RELEVANT CONTEXT
   ↓
ACT
```

Typical questions Neural should answer:

- What decisions already exist for this problem?
- Which PUB project solved something similar?
- Which skills/patterns apply?
- Which governance rules apply?
- Is there contradictory knowledge?
- What evidence supports the recommendation?
- Is this rule global or project-specific?
- What is the latest verified state?

**Agents should receive relevant context, not a dump of every document.**

---

## 10. KNOWLEDGE GRAPH + RAG + DOCUMENTS

Target architecture:

```text
                     PUB NEURAL
                         │
          ┌──────────────┼──────────────┐
          ↓              ↓              ↓
      GRAPH MEMORY   SEMANTIC MEMORY  DOCUMENT MEMORY
       relations       embeddings       Markdown/docs
          └──────────────┼──────────────┘
                         ↓
                  NEURAL RETRIEVAL
```

Start with infrastructure already used by PUB. Do not introduce a specialized graph database until scale or query requirements prove it necessary.

Obsidian is a **human-facing projection**, not the source of truth:

```text
NEURAL DATA → Obsidian
```

Backlinks and graph views are useful for human exploration, while agents consume canonical structured knowledge.

### 10.1 PUB NEURAL OBSERVATORY & PRODUCT VISION

**Status:** `TARGET / FUTURE / NOT IMPLEMENTED`
**Referência Canônica:** [`docs/architecture/PUB_NEURAL_OBSERVATORY_PRODUCT_SPEC.md`](./docs/architecture/PUB_NEURAL_OBSERVATORY_PRODUCT_SPEC.md)

O PUB Neural deverá dispor futuramente de uma experiência visual interativa, convidativa e *product-ready* para exploração da memória institucional, inspirada na clareza relacional de ferramentas como Obsidian, sem se limitar a anotações pessoais.

**Princípios Fundamentais:**
- **Infrastructure-First, Product-Ready:** Nascido primeiramente como infraestrutura interna e cérebro cognitivo da holding, mas desenhado com padrão de produto para permitir futura oferta SaaS B2B sem UX puramente técnica ou inacessível.
- **CEO-First Comprehension:** Permitir que o CEO compreenda o estado essencial da organização em segundos sem exigir domínio de detalhes de banco de dados, embeddings ou bi-temporalidade.

**Camadas Arquiteturais de Produto:**
- **NEURAL ENGINE** (`OPERACIONAL / BASELINE V0.1 CONGELADO`): Event sourcing, projeções relacionais, hybrid retrieval e RLS.
- **NEURAL EXPERIENCE** (`DESIGN / NÃO IMPLEMENTADO`): Superfícies do Observatory:
  - *Neural Graph:* Grafo semântico com relações causais reais (`derived_from`, `affects`, `implemented_by`, `validated_by`, `evolved_into`).
  - *Neural Now:* Visão contextual focada em "o que importa agora?".
  - *Context Inspector:* Inspeção profunda de significado, origem, evidências e cadeia de proveniência.
  - *Neural Activity:* Linha do tempo baseada em eventos reais imutáveis (zero fake animations).
  - *Knowledge Health:* Monitoramento de integridade reutilizando os estados canônicos (`VALIDATED`, `OBSERVED`, `CANDIDATE`, `CONTRADICTORY`, `STALE`, `UNVERIFIED`).
  - *Agents View:* Representação conceitual de papéis cooperativos (*Researcher, Architect, Engineer, Reviewer, Neural*).
- **NEURAL CLOUD** (`FUTURO / NÃO IMPLEMENTADO`): Multi-tenancy externo, federação de workspaces, cotas e faturamento.

---

## 11. MASTER CONTEXT CONSOLIDATION STRATEGY

The Neural should become the single convenient consultation point without destroying project-local source-of-truth documents.

Therefore:

1. Keep project Master Contexts in their original repositories.
2. Harvest them into Neural.
3. Normalize overlapping concepts.
4. Preserve source and commit provenance.
5. Mark project-specific versus institutional knowledge.
6. Detect contradictions.
7. Promote validated reusable knowledge.
8. Make Neural retrieval return the minimum relevant context.

The goal is **one cognitive consultation layer, not one giant undocumented file**.

---

## 12. HARVEST TARGETS

When auditing a PUB repository, inspect at minimum:

```text
MASTER_CONTEXT*.md
*CONTEXT*.md
docs/
README*.md
ADR*
GOVERNANCE*
RAG*
SKILL*
AGENT*
PROMPT*
LESSON*
DECISION*
PATTERN*
architecture docs
tests that prove architectural decisions
workflows / automation
security rules
```

The harvester must distinguish:

```text
SOURCE ARTIFACT
vs
CANONICAL KNOWLEDGE
vs
PROJECT-SPECIFIC IMPLEMENTATION
```

---

## 13. ROADMAP

### Phase 1 — Consolidation
- canonical Master Context;
- repository inventory;
- Master Context discovery;
- source classification;
- provenance.

### Phase 2 — Knowledge Extraction
- governance;
- RAGs;
- skills;
- agents;
- prompts;
- decisions;
- ADRs;
- patterns;
- lessons;
- architecture and security rules.

### Phase 3 — Canonical Knowledge Model
- ontology;
- nodes;
- relations;
- states;
- provenance;
- confidence;
- project scope.

### Phase 4 — Retrieval
- structured search;
- semantic retrieval;
- agent-specific context;
- project filters;
- evidence-aware context assembly.

### Phase 5 — Continuous Learning
- PDL events;
- real task results;
- lessons;
- reusable skills;
- pattern detection.

### Phase 6 — External Intake
- GitHub;
- Web;
- Instagram;
- documents;
- Hermes;
- casual capture.

### Phase 7 — Human Knowledge Interface
- Obsidian projection;
- backlinks;
- graph exploration;
- provenance inspection.

---

## 14. AGENT OPERATING RULE

For every relevant PUB task:

1. Identify target project.
2. Consult this Master Context.
3. Identify global knowledge applicable to the task.
4. Identify project-local knowledge.
5. Check provenance of important claims.
6. Verify current repository/runtime state.
7. Execute.
8. Validate empirically.
9. Persist the result.
10. Promote reusable learning when justified.

**Do not assume. Verify.**

### 14.1 Model Recommendation Workflow

**Status:** `OPERATIONAL PROTOCOL / HUMAN DECISION SUPPORT`

Toda recomendação de modelo de IA formulada por agentes ou operadores dentro do ecossistema PUB deve seguir o protocolo de verificação ativa:

1. **Verificação de Catálogo Real:** Ao sugerir um modelo (ex.: OpenAI, Anthropic, Google, modelos locais/open-source), o agente/operador deve checar o catálogo real e atualizado de modelos disponíveis no momento da recomendação, ou explicitar claramente que a sugestão requer validação prévia das contas, chaves de API e provedores ativos do Matheus.
2. **Critérios Multidimensionais de Seleção:**
   - *Natureza da Tarefa:* Raciocínio profundo e arquitetura (*deep reasoning*) vs execução rápida/stream (*speed/latency*).
   - *Janela de Contexto:* Volume de dados de entrada e complexidade de dependências.
   - *Custo e Cotas:* Disponibilidade de cota, limites de taxa (*rate limits*) e viabilidade econômica para o ciclo operacional.
   - *Complexidade do Domínio:* Nível de criticidade de governança, precisão sintática e risco de alucinação.
3. **Ausência de Integração Dinâmica Automatizada:** Fica estritamente registrado que **não existe integração automatizada com catálogo dinâmico de modelos nesta fase**. A recomendação constitui um protocolo operacional de auxílio à decisão humana, cabendo ao operador/CEO a aprovação e seleção final do runtime de inferência.

---

## 15. CONSOLIDATED SOURCES

This version was built from directly verifiable Master Contexts in the connected PUB repositories, including:

- `pubcoreagencia/pub-neural`
- `pubcoreagencia/pub-dev-loop`
- `pubcoreagencia/pub-ecom`
- `pubcoreagencia/pub-machine`
- `pubcoreagencia/pub-prototype`

The organization contains additional repositories that must continue through the harvesting process. Not being represented in this first consolidation does **not** mean that they contain no relevant knowledge.

---

## 16. CURRENT STATUS

`MASTER_CONTEXT_STATUS = CANONICAL / CONSOLIDATED / EVOLVING`

Current objective:

> Make PUB Neural the single cognitive consultation layer for PUB Holding while preserving every neuron's source of truth, scope and provenance.

Next milestone:

> Build the repository harvester that discovers and extracts Master Contexts, governance, RAGs, skills, agents, decisions, patterns and lessons into structured Neural knowledge.

**Final principle:**

> PUB Neural must remember what PUB has already learned, know where each learning came from, know whether it is still valid, and deliver only the context relevant to the agent that needs to act.

---

## 17. VERIFIED HISTORICAL PUB CORE DATA — LOVABLE CLOUD

**Recorded:** 2026-09-11  
**Knowledge class:** `EPISODIC + SEMANTIC + SOURCE / PROVENANCE`  
**Scope:** `PUB CORE / HISTORICAL INFRASTRUCTURE`  
**Status:** `VALIDATED`  
**Confidence:** `HIGH`

A direct read-only investigation of the Lovable project **Pub Core Executive** established that its connected backend contains substantial historical PUB Core operational data. This is not treated as a hypothesis or reconstruction.

### 17.1 Verified workspace

The historical backend contains a workspace named:

`PUB CORE's Workspace`

The workspace was created in May 2026 and is the workspace identifier used by the historical Central de Arquivos records examined during this investigation.

### 17.2 Verified historical dataset

The connected backend currently exposes the following confirmed records/counts from the historical PUB Core environment:

```text
workspaces       = 7
workspace_members = 7
profiles         = 11
kanban_cards     = 244
files_folders    = 13
files_items      = 47
storage.buckets  = 3
storage.objects  = 71
```

The database schema also contains historical PUB Core domains including calendar, checklist, completion reports, CRM, discography, finance, gratitude, Kanban, notes, personal finance, point tracking, shared items, sticky notes, stock/inventory, trends and workspace governance.

### 17.3 Master/PUB CORE Central de Arquivos

For the identified PUB CORE workspace, 13 historical folders were verified, including verticals and operational areas such as:

```text
CRIATIVOS
PUB IA
PUB ADSENSE
PUBET
PUB CRYPTO
PUB ECOM
PUB FILMS
PUB FOOD
PUB IMOVEIS
PUB LAUNCH
PUB TEXTIL
XPAUDIOLAB
PUB MEDIA
```

The backend contains 47 `files_items` records for the historical file system and corresponding physical objects in the Supabase Storage `files` bucket were directly observed under the same workspace prefix.

Examples of verified historical object names include materials for PUB Ads, Crypto, Ecom, Films, Food, Imóveis, Launch, PUBET, Media and XPAUDIOLAB.

### 17.4 Database metadata + physical Storage evidence

This is an important distinction:

```text
files_items
    ↓
storage_path
    ↓
storage.objects
    ↓
physical Storage object
```

The investigation verified both database-level file metadata and Storage object records. Supabase documents that `storage.objects` stores object metadata while the actual file content is stored by the Storage provider, so these are distinct layers of evidence. citeturn0search0turn0search3

The historical PUB CORE files therefore must not be treated as merely filenames in a database. Physical Storage objects are present in the historical backend.

### 17.5 Historical continuity evidence

The Lovable project edit history aligns with the operational data found in the backend. Verified historical events include:

- June 2026: creation and population of Central de Arquivos material;
- June 2026: creation of Discografia, Trends, Finanças Pessoais and sharing functionality;
- July 2026: Kanban/workspace changes;
- 2026-07-06: historical edit explicitly describing transfer of the Kanban from Luana's workspace to PUB CORE;
- 2026-07-08: historical edit concerning urgent correction of the Central de Arquivos and investigation of Supabase Storage, metadata, workspace ownership/access and workspace migration;
- 2026-08-16: historical developer update removing the `.env` from Git and preserving only an `.env.example` configuration surface.

These events are consistent with a real operational PUB Core environment that was built and used over time, rather than a later empty reconstruction.

### 17.6 Important unresolved identity link

The following claim is **NOT YET DIRECTLY PROVEN** and must remain explicitly unresolved:

```text
Lovable Cloud historical backend
        =
Supabase project OWIM (`owimmytcffoovmokbple`)
```

The historical PUB Core repository contains a Supabase configuration reference to OWIM, and historical commits describe transition toward an external Supabase source of truth. The data found in the Lovable backend strongly matches the historical PUB Core system, but the exact backend identity mapping to OWIM requires one more direct piece of evidence.

Do not convert this unresolved identity link into fact until verified.

### 17.7 Source-of-truth rule for this discovery

Until the backend identity chain is fully resolved:

```text
HISTORICAL DATA EXISTENCE       = CONFIRMED
MASTER/PUB CORE FILES           = CONFIRMED
PHYSICAL STORAGE OBJECTS        = CONFIRMED
LOVABLE HISTORICAL BACKEND      = CONFIRMED
LOVABLE BACKEND = OWIM          = UNRESOLVED
HISTORICAL DATA LOST             = NOT SUPPORTED BY EVIDENCE
```

The correct operational posture is **preservation first**. Do not delete, migrate, overwrite, restore or mutate historical sources merely to simplify the architecture. Preserve the original evidence until provenance is completely mapped.

### 17.8 Neural ingestion requirement

This discovery is now part of PUB Neural's canonical institutional context, but the raw historical data remains project/source-owned.

Neural must represent it as:

```text
SOURCE
  ↓
LOVABLE / PUB CORE EXECUTIVE
  ↓
HISTORICAL PUB CORE BACKEND
  ↓
WORKSPACE: PUB CORE
  ├── operational data
  ├── file metadata
  ├── Storage objects
  └── historical events
  ↓
PUB NEURAL
  ├── semantic facts
  ├── episodic events
  ├── provenance
  ├── confidence
  └── unresolved links
```

Neural must not silently copy every historical file into its own source-of-truth layer. It should index, classify and relate the knowledge while preserving the original source and provenance.

### 17.9 Forensic next step

The remaining high-value investigation is to prove the backend identity chain:

```text
Lovable Cloud
   ↕
Historical Supabase connection
   ↕
OWIM
   ↕
Other Supabase projects / migrations
   ↕
Current PUB Core OS
```

This investigation must remain read-only until an explicit migration/restore instruction is provided.


## 20. VERIFIED PUB MACHINE GPT-ONLY ACP VERTICAL SLICE — 2026-09-19

**Knowledge class:** EPISODIC + SEMANTIC + PROCEDURAL + LESSON + EVIDENCE  
**Scope:** PUB MACHINE / ACP GPT-ONLY RUNTIME  
**Status:** VALIDATED  
**Confidence:** HIGH

Canonical evidence: [docs/integrations/PUB_MACHINE_GPT_ONLY_ACP_VERTICAL_SLICE_2026-09-19.md](./docs/integrations/PUB_MACHINE_GPT_ONLY_ACP_VERTICAL_SLICE_2026-09-19.md)

The checkpoint verifies a GPT-only autonomous execution path through ChatGPT Free, local Chrome/CDP, the PUB-ACP-POC transport on port 5127, ACP Standalone and a governed workspace executor, followed by a real PUB MACHINE causal implementation and validation cycle.

Key runtime learning: the original apparent repetition of git status --short was not established as a deterministic stale-response defect. The observed blocking condition was residual concurrent transport state; restarting the resident transport cleared the state, and subsequent isolated requests returned distinct expected responses.

Key governance learning: an agent complete signal is not sufficient evidence of task completion. Future governed completion should corroborate repository state, required validation, build and acceptance criteria before terminal acceptance.

Promotion remains VALIDATED. This checkpoint is project-scoped evidence and must not silently become a holding-wide mandatory rule.