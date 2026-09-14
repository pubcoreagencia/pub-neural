# PUB Dual-AG Engineering Protocol

**Status:** CANONICAL OPERATING PROTOCOL / ACTIVE
**Recorded:** 2026-09-13
**Scope:** PUB Core Holding — all engineering repositories
**Applies to:** Antigravity on PC + Antigravity on Mac, coordinated by the human CEO and GPT while PDL is not yet the primary engineering runtime.

## 1. Purpose

Define the temporary operating model for full-stack engineering across the PUB Holding while PDL is being built and validated.

This protocol is intentionally designed as a bridge to PDL. The goal is not to create a parallel permanent process, but to operate today in a way that can later be automated by PDL without changing the underlying governance principles.

## 2. Operating Model

```text
                         CEO / GOVERNANCE
                                |
                                v
                         GPT ORCHESTRATOR
                                |
                +---------------+---------------+
                |                               |
                v                               v
             AG PC                           AG MAC
          Executor A                       Executor B
                |                               |
                +---------------+---------------+
                                |
                                v
                             GITHUB
                       source of truth
                                |
                   +------------+------------+
                   |                         |
                   v                         v
             PROJECT REPO               PUB NEURAL
           implementation            institutional memory
```

### Roles

**CEO / Governance**

Sets priorities, approves protected or irreversible changes, resolves conflicts, and remains the final authority for Holding-level decisions.

**GPT Orchestrator**

Transforms objectives into executable tasks, selects the right execution lane, inspects results, challenges unsupported completion claims, and decides the next step.

**AG PC**

Primary execution lane. It may perform full-stack implementation, refactoring, integration, backend, frontend, tests, debugging, and other assigned engineering work.

**AG Mac**

Parallel execution lane. It may perform independent implementation, audits, tests, UX validation, research-driven engineering, documentation, or work on another repository/task.

**GitHub**

Canonical source of truth for implementation state. Local state, AG output, terminal claims, and chat summaries never outrank the remote repository.

**PUB Neural**

Institutional memory and evidence layer. It records validated knowledge, decisions, patterns, lessons, provenance, and cross-project learning. It does not replace the project repository.

**PDL**

Future autonomous execution/control layer. This protocol is a manual operating approximation of the execution loop PDL is intended to automate.

## 3. Core Principle: One Task, One Owner

At any moment, a mutable code surface must have a single active executor.

Two AG instances must not independently modify the same repository/scope at the same time unless the work has an explicit partition that prevents overlap.

Every task must have, at minimum:

```text
TASK ID
REPOSITORY
BASE / BRANCH
EXECUTOR: PC | MAC
SCOPE
OBJECTIVE
ACCEPTANCE CRITERIA
```

Example:

```text
TASK-042
Repo: pub-dev-loop
Base: main
Executor: AG-PC
Scope: src/pdl/runtime/*
Objective: implement durable task persistence
Acceptance: tests pass + CI verify green
```

## 4. Execution Lanes

### AG PC — Primary Lane

Default for the highest-priority implementation unless there is a clear reason to assign the task elsewhere.

Typical work:

- core implementation;
- backend/frontend integration;
- refactors;
- database/runtime work;
- bug fixes;
- test-driven correction;
- integration and release preparation.

### AG Mac — Parallel Lane

Default for work that can be safely isolated from the primary lane.

Typical work:

- independent repository work;
- audits and code review;
- test expansion;
- UX/browser validation;
- documentation;
- external benchmark implementation follow-up;
- second implementation of a clearly separated scope;
- research-to-code experiments.

The roles are operational defaults, not permanent technical specializations. Either AG can perform full-stack work.

## 5. Task Lifecycle

Every engineering task follows the same lifecycle:

```text
INTAKE
  -> SCOPE
  -> ASSIGN
  -> SYNC BASE
  -> EXECUTE
  -> TEST
  -> CORRECT
  -> REVIEW
  -> COMMIT
  -> PUSH
  -> VERIFY REMOTE
  -> CLOSE
```

A task is not complete because the AG says it is complete.

A task is complete only when the required evidence exists.

## 6. Mandatory Start Gate

Before an AG begins a mutable task, it must establish:

```text
repository
current branch
current HEAD
working-tree state
assigned scope
task objective
acceptance criteria
```

The executor must be aware of relevant recent remote changes before modifying code.

If the repository or branch state is ambiguous, the task remains unassigned until the ambiguity is resolved.

## 7. Parallel Work Rules

### Allowed

Two AGs may work simultaneously when:

- they use different repositories; or
- they use different branches and scopes with no overlapping mutable files; or
- one AG is read-only/audit/validation while the other owns the mutable implementation scope.

### Not Allowed

Two AGs must not concurrently edit the same mutable files or the same tightly coupled code path without an explicit coordination point.

Avoid splitting work merely for the appearance of parallelism. Parallelism is justified by independent scope, reduced cycle time, or specialized validation.

## 8. Git Is the Synchronization Boundary

GitHub is the synchronization boundary between the two machines.

The canonical closure rule remains:

```text
IMPLEMENT
  -> TEST
  -> COMMIT
  -> PUSH
  -> VERIFY REMOTE
  -> DECLARE CLOSED
  -> NEXT STAGE
```

Local commit without push is not closure.

Push without remote verification is not closure.

A green local test does not override a failing remote CI check.

No force-push is permitted unless explicitly governed and justified.

## 9. Handoff Protocol

When work moves from one AG to the other, the handoff is based on Git state and explicit task state, not on conversational memory alone.

Minimum handoff record:

```text
TASK ID
REPO
BRANCH
HEAD / COMMIT
WHAT CHANGED
TESTS RUN
KNOWN FAILURES
NEXT ACTION
FILES / SCOPE OWNED
```

The receiving AG must refresh from the authoritative remote state before continuing.

## 10. GPT Orchestration Rules

GPT acts as the coordinator between the two execution lanes.

GPT must:

1. maintain the priority order;
2. assign ownership explicitly;
3. prevent overlapping mutable scopes;
4. require evidence for completion claims;
5. distinguish implementation from validation;
6. enforce the global Git closure rule;
7. use PUB Neural for institutional context and lessons;
8. turn recurring friction into candidate Skills, Tools, Evals, or PDL capabilities.

GPT must not treat AG prose as proof when repository state or test evidence can verify the claim directly.

## 11. Research and External Learning

External research may feed an engineering task, but research does not directly become implementation merely because an external source claims it is effective.

The preferred flow is:

```text
RESEARCH
  -> BENCHMARK
  -> GAP ANALYSIS
  -> DECISION
  -> TASK
  -> IMPLEMENTATION
  -> EVAL
  -> NEURAL
```

This keeps the dual-AG operation aligned with the PUB Research Intelligence Protocol.

## 12. Validation Standard

Validation should be proportional to the change, but every completion claim must identify its evidence.

Possible evidence layers:

```text
unit tests
integration tests
E2E / UX tests
static/type validation
build
security checks
CI
runtime verification
Git remote state
```

For consequential changes, the highest available relevant gate is preferred.

## 13. Failure Handling

Failure is part of the normal engineering loop.

When validation fails:

```text
FAIL
  -> CLASSIFY
  -> INVESTIGATE
  -> CORRECT
  -> RE-RUN TARGETED TESTS
  -> RE-RUN REQUIRED GATES
```

Do not hide failures by weakening assertions, removing meaningful tests, bypassing gates, or silently changing acceptance criteria.

If a failure reveals a reusable lesson or a missing capability, record it for Neural and/or convert it into a candidate Skill, Eval, Tool, or PDL requirement.

## 14. Engineering Queue

The Holding should maintain one prioritized execution queue conceptually shared by both AGs.

```text
P0  critical / blocking / governance / security
P1  highest-value product and runtime work
P2  enabling work / debt / quality
P3  experiments / non-critical improvements
RESEARCH  external intelligence and benchmark work
```

The queue is a prioritization mechanism, not a substitute for project-specific roadmaps.

A task enters an execution lane only after its objective and acceptance criteria are clear enough to evaluate.

## 15. Standard Task Contract

Use this compact contract for tasks routed to either AG:

```text
TASK: <id>
REPO: <owner/name>
BRANCH: <branch>
EXECUTOR: PC | MAC
PRIORITY: P0 | P1 | P2 | P3 | RESEARCH
OBJECTIVE: <one concrete outcome>
SCOPE: <files/modules/area>
CONSTRAINTS: <important rules>
ACCEPTANCE:
  - <criterion>
  - <criterion>
TESTS / GATES:
  - <required validation>
CLOSURE:
  - commit
  - push
  - remote verification
```

## 16. Relationship to Project Files

This protocol is Holding-level. Each project may add project-specific operating context through:

- `AGENTS.md` for local operating rules and project map;
- `context/` for current project context and decisions;
- `skills/` for validated reusable procedures;
- `execution/` for generated execution artifacts;
- tests/evals for proof;
- project documentation for implementation truth.

A project's local rules may be stricter than this protocol, but may not weaken global governance rules such as Git closure, protected-path controls, or explicit CEO authority.

## 17. Relationship to PUB Neural and PDL

The operating stack is:

```text
CONTEXT
  -> SKILLS
  -> AGENTS
  -> TOOLS
  -> EXECUTION
  -> EVALUATION
  -> MEMORY
  -> INSTITUTIONALIZATION
```

The current manual implementation is:

```text
GPT
  -> AG PC / AG Mac
  -> GitHub
  -> tests / CI
  -> PUB Neural
```

The target implementation is:

```text
GPT / GOVERNANCE
  -> PDL
  -> agent(s) + skills + tools
  -> tests / evals
  -> GitHub
  -> PUB Neural
```

Therefore every recurring manual coordination step should be considered a candidate requirement for PDL automation.

## 18. Anti-Patterns

The following are explicitly discouraged:

- two AGs editing the same mutable scope without coordination;
- treating local disk as canonical state;
- declaring completion before remote verification;
- starting work without knowing branch/HEAD/scope;
- using the second AG merely to increase activity instead of reducing cycle time;
- copying large context blocks manually when canonical project context exists;
- creating a Skill before a procedure is stable enough to validate;
- replacing PUB Neural with a simple local memory file;
- turning every deterministic workflow into an autonomous agent;
- adopting external tools because of demonstrations or marketing claims without benchmark/evidence.

## 19. Operational Goal

The success criterion for this protocol is not "use two AGs more intensely."

It is:

> **Maximize safe engineering throughput now while collecting the operational patterns that PDL will later automate.**

The dual-AG setup is therefore a controlled bridge from manual orchestration to an autonomous PUB engineering runtime.

## 20. Closure

This protocol becomes active for PUB engineering operations immediately upon publication in PUB Neural and remains in force until replaced by a newer governed protocol.

Changes to this protocol follow the same global Git closure rule used by the Holding.
