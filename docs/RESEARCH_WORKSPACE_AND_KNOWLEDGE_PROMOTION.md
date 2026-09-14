# Research Workspace & Knowledge Promotion

**Status:** Architectural pattern, V0.1  
**Scope:** PUB Neural  
**Origin:** Analysis of the NotebookLM + Obsidian workflow presented by Linking Your Thinking with Nick Milo.

## Purpose

The external workflow suggests a useful knowledge-management principle: a research environment should be optimized for investigation and synthesis, while durable organizational knowledge should be curated and promoted separately.

PUB does **not** adopt NotebookLM or Obsidian as architectural dependencies. The insight is vendor-neutral and is expressed here as a PUB Neural pattern.

## Core principle

> **Research is temporary context. Institutional knowledge is curated state.**

PUB Neural should not become a permanent dump of every source, summary, hypothesis, or AI-generated artifact encountered during research.

Instead, investigation should have a bounded **Research Workspace / Research Session** in which evidence can be collected, compared, synthesized, challenged, and prepared for promotion.

## Canonical flow

```text
RESEARCH
   ↓
RAW EVIDENCE
   ↓
RESEARCH WORKSPACE
   ├── sources
   ├── questions
   ├── hypotheses
   ├── extracted insights
   ├── contradictions
   └── provisional outputs
   ↓
CURATION
   ↓
CANDIDATE KNOWLEDGE / DECISION
   ↓
VALIDATION
   ↓
ADOPTION
   ↓
INSTITUTIONAL KNOWLEDGE
```

## Research Workspace

A Research Workspace is temporary processing context for a bounded investigation topic.

It may contain large amounts of material without implying that every artifact deserves permanent retrieval weight or institutional status.

A conceptual session can include:

- research topic and objective;
- source registry and provenance;
- extracted evidence;
- questions and hypotheses;
- conflicting or contradictory evidence;
- synthesized insights;
- candidate decisions;
- generated research outputs;
- validation results;
- promotion status.

The workspace is an **epistemic staging area**, not the organization's memory itself.

## Knowledge promotion

Promotion is the deliberate boundary between information encountered and knowledge trusted by the organization.

The existing PUB Neural lifecycle provides the canonical promotion path:

```text
CAPTURED
   ↓
OBSERVED
   ↓
EXTRACTED
   ↓
CANDIDATE
   ↓
VALIDATED
   ↓
ADOPTED
   ↓
INSTITUTIONAL
```

Research artifacts can remain preserved as evidence and historical context without being promoted into the active institutional knowledge layer.

## Why this matters

Without this separation, a continuously researching AI system risks accumulating:

- duplicate conclusions;
- stale recommendations;
- unverified hypotheses;
- transient context;
- low-value summaries;
- vendor-specific assumptions;
- contradictory information with no provenance or resolution.

The solution is not to delete research. It is to preserve research with provenance while controlling what becomes durable organizational knowledge.

## Relationship to PDL

PUB Neural owns the knowledge/evidence side of the loop. PDL owns governed engineering execution.

The combined pattern is:

```text
RESEARCH
   ↓
EVIDENCE
   ↓
CURATION / PROMOTION
   ↓
PUB NEURAL KNOWLEDGE
   ↓
CONTEXT
   ↓
PDL PLAN / TASK GRAPH
   ↓
EXECUTION
   ↓
VALIDATION
   ↓
LEARNING → PUB NEURAL
```

This complements the PDL `Research → Execution` pattern without duplicating its responsibility.

## Non-goals

- Do not make NotebookLM a PUB dependency.
- Do not make Obsidian a PUB dependency.
- Do not create a second permanent memory layer inside the research workflow.
- Do not automatically promote every AI-generated insight into institutional knowledge.
- Do not confuse source preservation with knowledge adoption.

## Architectural decision

PUB Neural should evolve toward a **knowledge-promotion system**, not merely a retrieval database.

Its value is not only remembering information. Its value is preserving evidence, tracking epistemic status, supporting validation, and promoting sufficiently trusted knowledge into durable organizational state.

This document records the principle. Concrete schema/API implementation should be introduced only when validated against the existing PUB Neural ontology, lifecycle, and retrieval architecture.
