# PUB Research Intelligence Protocol

**Recorded:** 2026-09-13  
**Status:** STRATEGIC NORTH / DESIGN  
**Scope:** PUB Core Holding

## Purpose

PUB needs a repeatable way to learn from the external world instead of depending on isolated research sessions. Research must become an organizational capability that feeds the same knowledge, governance, implementation and evaluation loop used by the Holding.

## Role Separation

```text
SCOUT / RESEARCH INTELLIGENCE
    discovers and compares

PUB NEURAL
    preserves context, provenance and learning

GOVERNANCE / CEO
    decides what PUB adopts

PDL
    orchestrates execution

AGENTS
    perform specialized work

SKILLS
    encode validated reusable procedures

TOOLS
    provide controlled external capabilities

EVAL
    proves whether the change worked
```

## Investigation Protocol

1. **Define** the strategic or technical question.
2. **Scout** a diverse source set: YouTube, GitHub, papers, official documentation, benchmarks, communities and real cases.
3. **Classify** sources by evidence quality and separate primary evidence from opinion, tutorial and marketing.
4. **Extract** architectures, patterns, technologies, metrics, tradeoffs, failures and operational constraints.
5. **Cross-compare** against the current PUB repositories, runtime evidence and existing Neural knowledge.
6. **Benchmark** what PUB already has, what is missing, what is superior, what is obsolete and what is only repackaging.
7. **Synthesize** a new perception instead of producing a source-by-source summary.
8. **Decide** using explicit outcomes: `KEEP`, `IMPROVE`, `ADOPT`, `REJECT`, `DEFER`, `INVESTIGATE`.
9. **Propose implementation** with dependencies, risk, scope, tests and success criteria.
10. **Implement only after governance** when the proposal changes strategic architecture, security, production or other protected areas.
11. **Evaluate** empirically.
12. **Institutionalize** validated findings in Neural with provenance and promotion state.

## Research Record

Each material research cycle should produce a durable record containing, at minimum:

```yaml
research:
subject:
question:
sources:
evidence:
findings:
benchmark:
pub_current_state:
gaps:
rejected_claims:
recommendations:
implementation_priorities:
success_criteria:
confidence:
status:
provenance:
```

## Evidence Discipline

The Research Intelligence system must not convert popularity into truth.

Claims should be tagged conceptually as:

- `EVIDENCE` — directly supported by a primary or reproducible source;
- `OBSERVATION` — observed in a practical implementation;
- `INFERENCE` — reasoned conclusion from evidence;
- `HYPOTHESIS` — not yet validated;
- `MARKETING_CLAIM` — promotional claim requiring independent evidence;
- `REJECTED` — contradicted or not valuable for PUB.

## First Benchmark Case

The 2026-09-13 agent research dossier containing 19 YouTube videos is the first informal benchmark for this capability.

The benchmark confirmed several architectural principles relevant to PUB:

- harness/context is as important as the model;
- Skills are useful for deterministic reusable procedures;
- agents are valuable for investigation and non-deterministic decisions;
- subagents are useful when specialization or context economy justifies them;
- memory must be persistent and governed;
- progressive disclosure reduces context waste;
- MCP/tool layers are plumbing, not the organizational brain;
- evaluation, guardrails and human approval are mandatory for meaningful autonomy;
- 24/7 execution is a runtime capability, not proof of intelligence;
- multi-agent architectures should follow actual specialization needs, not agent-count vanity;
- browser automation is useful but less reliable than direct APIs where available;
- n8n can serve deterministic workflows but should not replace PUB's core orchestration architecture.

The strongest strategic conclusion was:

> PUB's main gap is not lack of AI capability. It is the fragmentation between research, memory, orchestration, skills, tools, evaluation and implementation.

## Relationship to Neural

Research findings follow the same promotion discipline as all other knowledge:

```text
RESEARCH
→ FINDING
→ PATTERN / LESSON
→ CANDIDATE
→ VALIDATED
→ DECISION
→ RULE / SKILL / IMPLEMENTATION
→ INSTITUTIONAL
```

Conflicting evidence must remain visible. Research never silently overwrites prior knowledge.

## Relationship to the Roadmap

Research Intelligence is a **transversal capability**. It continuously evaluates the roadmap itself and may recommend changing phase order, technology choices, architecture or priorities. Such changes remain subject to governance.
