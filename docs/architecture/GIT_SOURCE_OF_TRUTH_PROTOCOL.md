# PUB Neural / PDL — Git Source of Truth Protocol

**Status:** CANONICAL DIRECTION
**Date:** 2026-09-12
**Scope:** PUB Neural, PDL, agents, repositories, operational knowledge

## 1. Purpose

PUB Neural shall treat the Git/GitHub ecosystem as the canonical institutional record for versioned software state, decisions, context, evidence, and operational continuity.

This protocol exists so that any authorized human or agent can resume work from the repository without depending on a previous chat session, local machine, private notes, or volatile agent memory.

## 2. Authority Model

GitHub is the canonical institutional persistence layer, but not every artifact has the same evidentiary authority.

The authority hierarchy is:

1. Current runtime / direct evidence
2. Real execution results
3. Tests / QA evidence
4. Code and migrations at the referenced Git commit
5. Code review / approved pull requests
6. Validated decisions and ADRs
7. Master Context and derived documentation
8. Agent memory, chat history, local notes, and personal knowledge tools

When two sources conflict, the higher-authority source wins and the conflict must be recorded rather than silently reconciled.

## 3. Canonical Persistence Rule

If an operational fact, architectural decision, implementation state, invariant, test result, or validated lesson is expected to survive the current session, it must be persisted in the canonical repository.

Chat is a transport layer. Agent memory is a convenience layer. Local workspaces are execution environments. Neither is the institutional source of truth.

## 4. Repository as Institutional Memory

The repository must preserve enough information to reconstruct:

- what the system is;
- what state it is in;
- what changed;
- why it changed;
- what evidence supports the change;
- what remains unresolved;
- how another agent can continue safely.

Preferred artifacts include:

- source code;
- migrations and schemas;
- tests and QA reports;
- ADRs / validated decisions;
- Master Context;
- architecture specifications;
- operational runbooks;
- research/evidence records;
- lessons and known failure modes;
- task/state records when they materially affect continuity.

## 5. Agent Continuity Contract

Every agent operating on PUB Neural should follow this lifecycle:

```text
RETRIEVE CANONICAL STATE
        ↓
UNDERSTAND CURRENT STATE
        ↓
PLAN CHANGE
        ↓
EXECUTE
        ↓
TEST / VALIDATE
        ↓
CAPTURE EVIDENCE
        ↓
UPDATE CANONICAL RECORD
        ↓
COMMIT
        ↓
PUSH
        ↓
HAND OFF CONTEXT
```

An agent must not rely on an undocumented local state as the only record of completed work.

## 6. Source of Truth vs. Derived Projections

Obsidian and other human-facing knowledge interfaces may exist as projections or working surfaces, but they are not canonical authority.

The intended direction is:

```text
CANONICAL REPOSITORIES + RUNTIME EVIDENCE
                 ↓
            PUB NEURAL
                 ↓
       STRUCTURED KNOWLEDGE
                 ↓
        HYBRID RETRIEVAL
                 ↓
        CONTEXT ASSEMBLY
                 ↓
          PDL / AGENTS
                 ↓
             EXECUTION
                 ↓
             EVIDENCE
                 ↓
       GIT / GITHUB RECORD
```

Human-facing tools may consume this knowledge. They must not silently become a competing source of truth.

## 7. Cross-Repository Direction

PUB Neural is intended to become capable of harvesting and reasoning over the broader PUB repository ecosystem, including Master Contexts, governance, RAGs, skills, agents, decisions, patterns, lessons, code, tests, and operational evidence.

The next architectural direction is therefore repository-wide harvesting and synchronization, not creation of a parallel documentation authority.

## 8. Conflict Handling

When an agent discovers conflicting information:

1. identify the conflicting sources;
2. rank them using the authority model;
3. preserve provenance;
4. do not silently overwrite contradictory historical evidence;
5. update the canonical state only after validation;
6. record the resolution when it changes an architectural or operational decision.

## 9. Commit Discipline

Meaningful work must produce meaningful Git history.

Commits should describe the durable state transition they introduce. Large autonomous work should be decomposed into coherent commits where practical so that future agents can inspect, validate, revert, or continue individual steps.

## 10. Definition of Institutional Continuity

PUB Neural reaches institutional continuity when a new authorized agent can enter the repository, retrieve the canonical context, inspect the latest validated state and evidence, understand unresolved work, and continue execution without requiring a human to reconstruct the previous session from chat history.

This protocol is the architectural direction for reaching that state.
