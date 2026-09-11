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