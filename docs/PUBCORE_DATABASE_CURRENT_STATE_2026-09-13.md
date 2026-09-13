# PUBCORE DATABASE CURRENT STATE — 2026-09-13

**Purpose:** canonical evidence patch for the PUB Neural Master Context.

## Verified live database

- Supabase project ref: `ytnmxzzjevdshpbryfyv`
- PostgreSQL: `17.6`
- Audited at: `2026-09-13 01:59:46 UTC`
- Workspace: `contato.pubcore's Workspace`
- Workspace ID: `4f23144e-b825-4529-ab5c-3e8c9d702149`

## Current row counts

```text
workspaces                    1
checklist_companies           1
checklist_daily_completions   1
checklist_tasks               1
kanban_funnels                2
kanban_columns                6
kanban_cards                  2
kanban_attachments            0
kanban_card_links             0
kanban_cards_archive          0
calendar_events               0
completion_reports            0
notes                         0
ponto_sessions                1
shared_items                  0
sticky_notes                  0
```

## Current Kanban

Funnels:
- `Geral`
- `teste`

`Geral` columns:
- Backlog
- Hoje
- Em andamento
- Revisão
- Concluído

Actual live cards: **2**

```text
1. teste | pending | Média | Backlog
2. teste | pending | Média | Hoje
```

## Current task

One live checklist task:

```text
company: asd
title: asdasdasd
status: pending
priority: medium
assignee: null
```

## Historical/current separation

The live project above is **not** the historical PUB Core dataset previously verified with `kanban_cards = 244`.

Therefore:

```text
historical PUB CORE dataset != current active PUBCORE dataset
```

The historical dataset must remain preserved as historical evidence. The active project is authoritative only for current PUBCORE runtime state.

## Historical Supabase evidence

A preserved PUB audit artifact also records the historical endpoint:

`ilpvxbngblkkfjffkbpq.supabase.co`

That endpoint remains historical evidence until its identity is directly reconciled with the current project.

## Forensic rule

Do not restore, migrate, delete, overwrite or mutate historical sources merely to reconcile datasets. Establish provenance first.
