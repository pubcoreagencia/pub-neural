# PUB System Architecture — Neural Institutional Record

**Status:** CANONICAL / ACTIVE
**Date:** 2026-09-13
**Source:** `pubcoreagencia/pub-dev-loop/docs/architecture/PUB_SYSTEM_ARCHITECTURE.md`
**Purpose:** Preserve the institutional architecture in PUB Neural with source provenance.

## Final Model

```text
MATHEUS
  ↓
DIRECTION / IDEAS
  ↓
PDL
  ↓
PLANNING + GOVERNANCE + SPECIALISTS
  ↓
EXECUTION
  ↓
TEST / QA / AUTO-CORRECTION
  ↓
PERSISTENCE
  ↓
GIT
  ↓
RUNTIME
  ↓
PUB NEURAL LEARNING
  ↓
NEXT USEFUL TASK
  ↺
```

## Explicit AG Boundary

**AG is not part of the final architecture.**

AG is a temporary development instrument used to construct PDL while PDL is incomplete. It must not become a PDL runtime dependency or final executor abstraction.

The final target is PDL autonomous daily development without AG.

## System Roles

### Obsidian
Human thinking layer:

- ideas;
- strategy;
- hypotheses;
- planning;
- human-readable notes.

Not implementation truth.

### Git / GitHub
Project implementation truth:

- code;
- tests;
- migrations;
- configuration;
- documentation;
- history;
- versioned evidence.

### Runtime
Operational truth for what is actually running.

### PUB Neural
Institutional intelligence and memory:

- extract knowledge from projects;
- preserve provenance;
- relate projects and decisions;
- retain lessons and patterns;
- detect contradictions;
- serve relevant context to PDL.

Neural is not a replacement for project repositories.

### PDL
Autonomous development loop:

- receives direction;
- discovers/prioritizes work;
- retrieves knowledge;
- inspects projects;
- selects capabilities;
- plans;
- executes;
- validates;
- corrects;
- persists;
- verifies runtime;
- learns;
- continues.

## Development Retrieval Rule

When developing a project, PDL should use both Git and Neural:

```text
PROJECT IDENTIFICATION
        ↓
PUB NEURAL CONTEXT
        ↓
CURRENT GIT / SOURCE
        ↓
RUNTIME WHEN RELEVANT
        ↓
CROSS-CHECK
        ↓
PLAN / DEVELOP
```

**Git answers what exists. Neural answers what PUB knows about it.**

If implementation evidence conflicts with historical Neural knowledge, current runtime/source wins for implementation truth. Neural must preserve provenance and update/supersede stale knowledge rather than silently masking the conflict.

## Neural Learning Loop

After meaningful development milestones:

```text
GIT / RUNTIME
 → AUDIT
 → EXTRACT
 → NORMALIZE
 → PROVENANCE
 → VALIDATE
 → FUSE
 → PUB NEURAL
```

Extract durable intelligence rather than blindly copying source trees.

Priority:

- architecture;
- decisions;
- governance;
- fixes;
- incidents;
- lessons;
- patterns;
- skills;
- constraints;
- validation evidence;
- project relationships.

## Persistence Rule

```text
VALIDATE
→ EVIDENCE
→ COMMIT
→ PUSH
→ VERIFY REMOTE
→ VERIFY RUNTIME WHEN APPLICABLE
→ NEURAL INGESTION
→ CONTINUE
```

Meaningful local-only work is incomplete.

## End State

The intended operational state is:

> **Matheus provides direction. PDL develops the PUB every day. PUB Neural remembers what the PUB has learned. Git records what was actually built. Obsidian remains the human thinking surface.**

## Provenance

Canonical implementation architecture:

- Repository: `pubcoreagencia/pub-dev-loop`
- Path: `docs/architecture/PUB_SYSTEM_ARCHITECTURE.md`
- Architectural commit: `4ef0688e01dc442e50caae7bfb0a70fd94caecf5`

This Neural copy is an institutional record. The PDL repository remains the source for the architecture document itself; Neural is the knowledge layer that preserves and relates it.
