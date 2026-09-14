# PUB Holding Roadmap — Strategic Consolidation 2026

**Status:** CANONICAL STRATEGIC PROPOSAL / EVOLVING  
**Recorded:** 2026-09-13  
**Scope:** PUB Core Holding  
**Evidence basis:** existing PUB Neural roadmap + 2026 external benchmark on agent architectures + implementation guidance on Context/Skills/Agents/Tools/Evaluation

## 1. Strategic North

PUB should evolve into a Holding that can continuously **research, learn, decide, implement, evaluate and institutionalize**.

Canonical loop:

```text
RESEARCH → BENCHMARK → INTELLIGENCE → DECISION → IMPLEMENTATION → EVAL → NEURAL
    ↑                                                               │
    └────────────────────── institutional learning ─────────────────┘
```

The objective is not maximum agent count or maximum autonomy. The objective is **validated organizational capability**.

## 2. Roadmap Hierarchy

### Phase 0 — Source of Truth
- GitHub as canonical engineering source of truth.
- A stage is closed only after implementation, required gates, commit, push and remote verification.
- Preserve provenance and project scope.

### Phase 1 — PUB Neural Foundation
- Canonical ontology and provenance.
- Append-only events and bi-temporal knowledge.
- Hybrid retrieval.
- Knowledge promotion: `CAPTURED → OBSERVED → EXTRACTED → CANDIDATE → VALIDATED → ADOPTED → INSTITUTIONAL`.
- Contradiction handling and evidence-aware retrieval.

### Phase 2 — PDL Runtime
- Durable task execution.
- Agent/tool routing.
- Workspace isolation.
- Mandatory tests and correction loops.
- Recovery/self-healing.
- Git closure enforcement.
- Neural feedback after execution.

### Phase 3 — Universal Evaluation
- Standard evidence contract for every autonomous action.
- Unit/integration/E2E/UX checks where applicable.
- Regression benchmarks.
- Success criteria before implementation.
- No claim of completion without evidence.

### Phase 4 — PUB Skills System
Adopt a modular capability structure:

```text
project/
├── AGENTS.md
├── context/
├── skills/
│   └── <skill>/
│       ├── SKILL.md
│       ├── references/
│       ├── scripts/
│       └── tests/
├── execution/
└── tests/
```

Rules:
- `AGENTS.md` is the local operating contract and route map.
- `context/` contains project-specific business and architectural context.
- `skills/` contains validated reusable procedures, not arbitrary prompts.
- deterministic scripts belong inside skills when they improve reliability.
- `MEMORY.md`, where useful, is local operational memory, never a substitute for PUB Neural.
- A routine becomes a Skill only after repeated validation and clear reuse value.

### Phase 5 — Research Intelligence
Create the PUB Research Intelligence / Scout capability.

Protocol:

```text
DEFINE QUESTION
→ SCOUT SOURCES
→ FILTER SOURCE QUALITY
→ EXTRACT
→ CROSS-COMPARE WITH PUB
→ BENCHMARK
→ SYNTHESIZE
→ DECIDE
→ PROPOSE IMPLEMENTATION
→ EVALUATE
→ INSTITUTIONALIZE IN NEURAL
```

Sources may include YouTube, GitHub, papers, official documentation, benchmarks, technical communities and real-world cases.

The Scout recommends. Governance/CEO decides. PDL orchestrates. Agents implement. Eval proves. Neural preserves the learning.

### Phase 6 — Tool Registry / MCP Layer
- Unified tool contracts.
- Permission metadata.
- Provenance.
- Read/write classification.
- Replace fragile browser automation with APIs where possible.

### Phase 7 — Multi-Agent
Only split into multiple persistent agents when specialization, context isolation, parallelism or governance justify it.

Target roles may include research, architecture, engineering, QA, analytics, creative and operations.

### Phase 8 — 24/7 Operations
- Persistent runtime.
- Heartbeats.
- Scheduled routines.
- Proactive monitoring.
- Recovery.
- Human approval gates for irreversible/high-risk actions.

VPS, Hermes, OpenClaw and n8n are implementation options, not the architecture itself.

### Phase 9 — PUB Operating System
Integrate Neural, PDL, projects, tools, skills, evaluation, governance and operational channels into one Holding control plane.

### Phase 10 — Progressive Autonomous Enterprise
Autonomy expands only where evidence supports it. Financial, security, production and irreversible actions retain explicit governance according to risk level.

## 3. New Strategic Layer

Research Intelligence is **transversal**, not merely Phase 5. It continuously audits the roadmap and can propose reordering any phase based on new evidence.

```text
EXTERNAL WORLD
      ↓
PUB RESEARCH INTELLIGENCE
      ↓
PUB NEURAL
      ↓
GOVERNANCE / CEO
      ↓
PDL
      ↓
AGENTS + SKILLS + TOOLS
      ↓
EVALUATION
      ↓
PUB NEURAL
```

Therefore the roadmap is a living strategic system, not a static checklist.

## 4. Operating Doctrine

> **Context → Skills → Agents → Tools → Execution → Evaluation → Memory → Institutionalization**

PUB should not merely build agents. PUB should build an organization capable of transforming external knowledge into validated internal capabilities.

## 5. Immediate Priority Order

1. Keep Git closure rule universal.
2. Complete Neural foundation and retrieval/evidence layer.
3. Mature PDL into a verifiable execution runtime.
4. Establish universal evaluation gates.
5. Establish the Skills standard across active repos.
6. Build Research Intelligence as the external benchmark loop.
7. Add tool registry/MCP governance.
8. Introduce multi-agent specialization where justified.
9. Move validated routines to 24/7 execution.
10. Consolidate the Holding control plane.

This order is intentionally conservative: **reliability before scale, evidence before autonomy, institutional memory before organizational multiplication.**
