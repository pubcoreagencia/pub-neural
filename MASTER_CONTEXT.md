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

Verified context state: `IDEA / DESIGN`, priority `HIGH`.

Treat documented architecture as intent, not proof of implementation.

### PUB PROTOTYPE / PP
`pubcoreagencia/pub-prototype`

Role: rapid interface/product prototyping environment.

Verified context state: `EM DEV / GITHUB`, priority `HIGH`.  
Verified base commit: `24da7e94e1a9e50b9eddf9ea1f00cf37b466bf73` (`HEAD == origin/main`, working tree clean).  
Canonical benchmark: [`docs/benchmarks/PP_AGENTIC_CAPABILITY_BENCHMARK_2026-09-14.md`](./docs/benchmarks/PP_AGENTIC_CAPABILITY_BENCHMARK_2026-09-14.md).

Proven agentic capability:
- Codebase inspection prior to mutation (read-before-write discipline).
- Surgical alteration of target files (`index.html`, `script.js`) with byte-for-byte preservation of non-target files.
- Automated validation via build, preview and security checks.
- Fail-closed execution under upstream provider timeouts (zero side-effects, zero corrupted files).

Operational rule on models:
- `openrouter/free` is suitable for short/medium exploratory tasks when availability permits.
- `openrouter/free` is NOT deterministic infrastructure for critical workloads due to high provider variability (HTTP 429, timeouts).

**PP must remain isolated from PDL.** Neural may know both, but every knowledge item must retain project scope.


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

PDL consumes Neural knowledge and produces new experiences that may become Neural knowledge.

Future casual Instagram capture should feed Hermes and then Neural instead of creating an independent knowledge silo:

```text
SOURCE → HERMES INTAKE → QUEUE → RESOLVE → ANALYZE
→ CANDIDATE → VALIDATE → PUB NEURAL
```

---

## 9. AGENT RETRIEVAL CONTRACT

The purpose of this Master Context is to reduce context fragmentation for agents.

Expected flow:

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

---

## 18. VERIFIED PUB PROTOTYPE AGENTIC CAPABILITY BENCHMARK

**Recorded:** 2026-09-14  
**Knowledge class:** `EPISODIC + SEMANTIC + PROCEDURAL + LESSON + EVIDENCE`  
**Scope:** `PUB PROTOTYPE / AGENTIC WORKER CAPABILITY`  
**Status:** `VALIDATED`  
**Confidence:** `HIGH`  
**Canonical benchmark report:** [`docs/benchmarks/PP_AGENTIC_CAPABILITY_BENCHMARK_2026-09-14.md`](./docs/benchmarks/PP_AGENTIC_CAPABILITY_BENCHMARK_2026-09-14.md)

An operational evaluation of autonomous agentic capabilities was conducted on PUB Prototype (PP). The results demonstrate real and operational capability for short and medium development tasks, alongside clear architectural boundaries regarding the OpenRouter FREE model tier.

### 18.1 Evaluated System & Base State

- **System:** PUB Prototype autonomous worker
- **Repository:** `pubcoreagencia/pub-prototype`
- **Official Base Commit:** `24da7e94e1a9e50b9eddf9ea1f00cf37b466bf73` (`HEAD == origin/main`, working tree clean)
- **Fixture Repository:** `https://github.com/pubcoreagencia/pub-dev-loop-prototypes.git`
- **Execution Workspace Commits:** `3537dec4b184cd03df5e73162db39c9294b89e45` and `4742d600c48c879184c49044408a5e02663ccbae`  
  *(Note: these were generated in the execution workspace/fixture, NOT in `pub-prototype`. The official commit of `pub-prototype` remains `24da7e94e1a9e50b9eddf9ea1f00cf37b466bf73`)*.

### 18.2 Provider & Routing Configuration

- **Configured Variable:** `OPENROUTER_MODEL=openrouter/free`
- **Configured Routing:** `openrouter/free`
- **Effectively Observed Model:** `cohere/north-mini-code:free` (selected by OpenRouter router in successful runs)

### 18.3 Test Cases & Proven Outcomes

| Case ID | Status | Tool Calls | Effective Model | Checkpoint / Session / Details |
|---|:---:|:---:|---|---|
| **Model Verification** | `PASS` | 2 | `cohere/north-mini-code:free` | Checkpoint: `70cffaa00d873c906e1a4f9636a007a36ecebdfa`<br>`write_file` executed, build `PASS` |
| **PP-AGENT-QUALITY-02** | `PASS` | >0 | `cohere/north-mini-code:free` | Code inspection before edit, surgical alteration of `index.html`, byte-for-byte preservation of `script.js`, validation, build, preview, security |
| **PP-AGENT-QUALITY-03** | `PASS` | >0 | `cohere/north-mini-code:free` | Session: `1087c1b5-ba63-41e1-ba29-882f4f048ebb`<br>Task: `1a864d61-4632-43a3-a054-87815285234d`<br>Checkpoint: `897053ad-edcf-46d2-ae40-61c1a1d5ce59`<br>DOM structure discovery, search by client/service, case-insensitive, empty state, reset, surgical edit of `script.js`, build, preview, validation |
| **PP-AGENT-QUALITY-04** | `BLOCKED` | 0 | Unresponsive | 120s timeout exceeded; 0 tool calls; 0 file mutations; build/preview not run.<br>**Diagnostic:** Upstream provider availability timeout; NOT an agent reasoning failure. Fail-closed safety proved. |
| **PP-AGENT-QUALITY-05** | `PASS` | >0 | `cohere/north-mini-code:free` | Session: `a5e594e9-f484-42e2-ac0d-ae92605b186e`<br>Task: `ad488576-731b-4bd0-bd42-e242710419ab`<br>Checkpoint: `10a50a38-0ee5-49a7-88b3-eb2ae2d79cf1`<br>Objective defect diagnosis, surgical whitespace normalization fix (`trim()`), feature preservation, build, preview, validation |

### 18.4 Proven Operational Capabilities

PUB Prototype proved 11 distinct agentic capabilities:
1. Understanding existing context without prior fine-tuning.
2. Read-before-write inspection of source files.
3. Deciding where to make surgical edits.
4. Correct and disciplined tool-call execution.
5. Modifying code surgically with zero unrelated edits.
6. Preserving scope and unedited files byte-for-byte.
7. Post-alteration validation of results.
8. Clean build execution.
9. Interactive preview generation.
10. Precise diagnosis and correction of objective defects.
11. Operating fail-closed when provider exceeds timeout (zero partial or corrupted state).

### 18.5 Upstream Provider Variability & Failure Modes

The primary bottleneck observed was the volatility of the OpenRouter free routing pool:
- `nex-agi/nex-n2.5-mini:free`: Timed out on heavier tasks (>120s).
- `google/gemma-4-31b-it:free`: Returned HTTP 429 rate limit.
- `poolside/laguna-s-2.1:free`: Returned HTTP 429 rate limit.
- `openrouter/free` (selecting `cohere/north-mini-code:free`): PASS on QUALITY-02, QUALITY-03, QUALITY-05, but timed out on QUALITY-04.

### 18.6 Strategic & Operational Conclusion

- **Operational Suitability:** `openrouter/free` is suitable for short/medium exploratory agentic tasks when provider capacity is available.
- **Architectural Limit:** `openrouter/free` must **never** be treated as deterministic infrastructure for critical workloads or strict SLA pipelines.
- **Fail-Closed Mandate:** Worker timeouts must always abort cleanly without mutating repository state.
- **Classification:** Registered as **verified knowledge**, not opinion.

### 18.7 Relation to Ecosystem & PDL

- **PUB Prototype:** Establishes the operational baseline for the PP worker at commit `24da7e94e1a9e50b9eddf9ea1f00cf37b466bf73`.
- **PUB Neural:** Knowledge enters in state `VALIDATED`. Future promotion to `ADOPTED` or `INSTITUTIONAL` requires ratification through actual holding-wide workflow adoption.
- **Future Link to PDL (PUB Dev Loop):** Lessons regarding read-before-write discipline, single-file surgical edits, and free-tier volatility inform PDL worker design while strictly maintaining project isolation.

