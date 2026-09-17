# HKUDS Agent Ecosystem Audit — 2026-09-17

## Purpose

Institutionalize the 2026-09-17 audit of eight HKUDS projects as external architectural evidence for PUB Neural, PDL, PUB ACP, and the future Capability Fabric.

This document is a benchmark, not an instruction to copy external architectures.

## Executive synthesis

The audited projects expose complementary patterns:

- **LightRAG** → graph/vector/KV retrieval, hybrid search, reranking, provenance, recovery.
- **DeepTutor** → agent workspace, memory, skills, research, subagents, contextual tools.
- **nanobot** → lightweight agent runtime: MessageBus → AgentLoop → AgentRunner → tools/providers.
- **OpenHarness** → permissions, hooks, approvals, context compression, memory, subagents, credential boundaries.
- **CLI-Anything** → agent-native capability adapters with structured CLI interfaces, state, JSON, undo/redo, and end-to-end tests.
- **AI-Researcher** → research loop connecting literature, hypotheses, implementation, experiments, validation, analysis, and publication.
- **Auto-Deep-Research** → historical reference for autonomous research planning/execution.
- **GraphGPT** → academic reference for graph + LLM interaction.

## PUB architectural mapping

| External reference | Classification | PUB destination | Core lesson |
|---|---|---|---|
| LightRAG | ADAPT | PUB Neural | Retrieval is a subsystem of institutional memory, not the sovereign brain |
| DeepTutor | ADAPT | PUB Neural / PDL | Workspace + tools + skills + memory can form a cognitive execution environment |
| nanobot | ADOPT/ADAPT | PDL | Separate message transport, agent loop, execution runner, providers and tools |
| OpenHarness | ADAPT | PDL / ACP | Permissions, hooks, approvals and credential boundaries must be first-class |
| CLI-Anything | ADAPT | Capability Fabric | External systems should become typed, observable, testable agent capabilities |
| AI-Researcher | ADAPT | PUB Research / Neural | Research should produce evidence, experiments, evaluations and lessons |
| Auto-Deep-Research | OBSERVE | PUB Research | Useful historical pattern, lower implementation priority |
| GraphGPT | OBSERVE | PUB Neural research | Academic graph/LLM ideas, not production runtime foundation |

## Canonical PUB separation

### PUB Neural
**Question:** What do we know, why do we believe it, and what became institutional knowledge?

Responsibilities:
- memory
- evidence
- retrieval
- graph/vector knowledge
- research corpus
- lessons
- patterns
- decisions
- rules
- institutional promotion

### PDL
**Question:** How do agents plan, reason, execute, test, correct and learn?

Responsibilities:
- agent runtime
- planning
- tool execution
- closed-loop work
- research execution
- test/correction loops
- skills
- agent sessions

### PUB ACP
**Question:** Who/what is allowed to execute, where, under which context, and what happened?

Responsibilities:
- dispatch
- project registry
- workspace resolution
- safety gates
- execution context
- lifecycle
- event bus
- run store
- observability
- control

### Capability Fabric
**Question:** What can an agent actually do in the external world?

Responsibilities:
- typed adapters
- CLI capabilities
- MCP capabilities
- API integrations
- domain-specific tools
- validation and observability contracts

## Institutional learning loop

The strongest cross-project pattern is not a single RAG or agent framework. It is the feedback loop:

PDL execution
→ event/evidence
→ PUB Neural capture
→ extraction
→ pattern/lesson candidate
→ validation
→ decision/rule/skill
→ institutional promotion
→ future execution improvement

This aligns with the existing PUB Neural promotion model:

CAPTURED → OBSERVED → EXTRACTED → CANDIDATE → VALIDATED → ADOPTED → INSTITUTIONAL

## Critical engineering finding: embedding provenance

LightRAG surfaced an important retrieval integrity concern: equal embedding dimensions do not guarantee equal semantic spaces.

PUB Neural therefore should treat embedding identity as part of retrieval provenance, including at minimum:

- embedding provider
- embedding model
- embedding model version when available
- embedding dimension
- corpus/version identity
- index/version identity
- creation timestamp

A model/index migration must not silently mix incompatible vector spaces.

## Governance findings

External harnesses reinforce several PUB requirements:

1. Credentials must be capabilities, not ambient agent state.
2. Tool permissions must be explicit and auditable.
3. Workspace/project context must be isolated.
4. Hooks should observe and enforce policy before/after tool execution.
5. Subagent delegation needs bounded authority and traceability.
6. Research output requires evidence provenance.
7. End-to-end capabilities should be testable without relying on GUI behavior.
8. Memory writes should have provenance and promotion state.

## What PUB should NOT do

- Do not merge LightRAG, DeepTutor, nanobot, OpenHarness or other projects into PUB as monoliths.
- Do not replace PUB Neural's institutional model with generic RAG.
- Do not make PDL dependent on one external agent framework.
- Do not make ACP responsible for cognition.
- Do not let external research become undocumented bookmarks.
- Do not copy external project abstractions without mapping them to PUB boundaries.

## Adoption rule

Every external discovery must pass:

**SOURCE → OBSERVATION → EVIDENCE → PATTERN → PUB APPLICABILITY → DECISION → IMPLEMENTATION CANDIDATE → VALIDATION**

Decision vocabulary:

- **OBSERVE** — useful evidence, no immediate architectural adoption.
- **ADOPT** — pattern fits PUB with minimal semantic change.
- **ADAPT** — pattern is useful but must be redesigned around PUB contracts.
- **REJECT** — evidence does not justify adoption or conflicts with PUB governance.

## Priority implications

Near-term:
1. Harden PUB Neural retrieval provenance.
2. Continue retrieval/abstention work without turning Neural into generic RAG.
3. Define PDL agent runtime boundaries using MessageBus/Loop/Runner concepts as reference.
4. Formalize capability contracts for external tools.
5. Add permission/credential governance to execution paths.
6. Connect PDL execution evidence to Neural promotion.

Longer-term:
- autonomous research as a first-class PDL workload
- capability marketplace/fabric
- cross-project institutional learning
- validated skill/rule promotion
- research-to-implementation feedback loops

## Final architectural thesis

The HKUDS ecosystem does not reveal a missing single product that PUB should adopt.

It reveals that PUB is converging toward a **cognitive execution platform** composed of distinct layers:

**PUB Neural = institutional cognition and memory**

**PDL = autonomous engineering/research execution**

**PUB ACP = execution control plane**

**Capability Fabric = world-facing agent capabilities**

The strategic advantage comes from the contracts between these layers, not from reproducing any one external repository.
