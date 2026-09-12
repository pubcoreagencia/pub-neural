# PUB CORE HISTORICAL BACKEND — FORENSIC RECORD

**Recorded:** 2026-09-11  
**System:** PUB Neural  
**Scope:** PUB Core historical infrastructure  
**Status:** `VALIDATED`  
**Confidence:** `HIGH`  
**Investigation mode:** read-only

## 1. Executive finding

A direct read-only investigation of the Lovable project **Pub Core Executive** verified that its connected backend contains substantial historical PUB Core operational data.

This is not treated as a reconstruction or hypothesis. The backend contains the historical PUB CORE workspace, operational records, file metadata and corresponding Supabase Storage object records.

## 2. Verified backend inventory

Confirmed counts from the historical backend:

| Resource | Count |
|---|---:|
| workspaces | 7 |
| workspace_members | 7 |
| profiles | 11 |
| kanban_cards | 244 |
| files_folders | 13 |
| files_items | 47 |
| storage.buckets | 3 |
| storage.objects | 71 |

The public database schema also contains historical PUB Core domains for calendar, checklist, completion reports, CRM, discography, finance, gratitude, Kanban, notes, personal finance, point tracking, shared items, sticky notes, stock/inventory, trends and workspace governance.

## 3. Master workspace

The historical backend contains a workspace named:

`PUB CORE's Workspace`

The identified workspace is the workspace prefix used by the historical Central de Arquivos records examined during the investigation.

## 4. Historical file system

The workspace contains 13 verified folders, including:

- CRIATIVOS
- PUB IA
- PUB ADSENSE
- PUBET
- PUB CRYPTO
- PUB ECOM
- PUB FILMS
- PUB FOOD
- PUB IMOVEIS
- PUB LAUNCH
- PUB TEXTIL
- XPAUDIOLAB
- PUB MEDIA

There are 47 `files_items` records associated with the workspace.

## 5. Physical Storage evidence

The investigation also directly observed 71 records in `storage.objects`, including objects under the same historical workspace prefix in the `files` bucket.

Examples of verified historical object names include materials for PUB Ads, Crypto, Ecom, Films, Food, Imóveis, Launch, PUBET, Media and XPAUDIOLAB.

The evidence chain is:

```text
files_items
    ↓
storage_path
    ↓
storage.objects
    ↓
physical Storage object
```

Supabase documents that `storage.objects` stores file metadata while the actual objects are stored by the Storage provider. Therefore database metadata and physical Storage presence are separate but complementary evidence layers.

## 6. Historical continuity

The Lovable project edit history is consistent with the data found in the backend. Relevant verified events include:

- June 2026: Central de Arquivos population and related operational features;
- June 2026: Discografia, Trends, Finanças Pessoais and sharing functionality;
- 2026-07-06: historical edit explicitly describing transfer of the Kanban from Luana's workspace to PUB CORE;
- 2026-07-08: historical edit concerning urgent Central de Arquivos correction and investigation of Supabase Storage, metadata, workspace ownership/access and migration;
- 2026-08-16: `.env` removal from Git while retaining `.env.example`.

This continuity strongly supports that the backend represents a real historical PUB Core operating environment.

## 7. Historical Supabase identity

The historical `pubcoreagencia/pubcore` repository contains a Supabase configuration reference to project `owimmytcffoovmokbple`, and historical commits describe a transition toward an external Supabase source of truth.

However, the exact identity mapping:

```text
Lovable Cloud historical backend
        =
Supabase OWIM
```

is **not yet directly proven**.

It must remain `UNRESOLVED` until a direct connection/configuration artifact proves it.

## 8. Current forensic state

```text
PUB CORE historical workspace       = CONFIRMED
Historical file metadata            = CONFIRMED
Historical physical Storage objects= CONFIRMED
Historical operational data         = CONFIRMED
Lovable historical backend          = CONFIRMED
Lovable backend = OWIM              = UNRESOLVED
Historical data permanently lost    = NOT SUPPORTED BY EVIDENCE
```

## 9. Preservation rule

Until the full identity chain is resolved, this source must be treated as a preservation target.

Do not:

- delete historical records;
- overwrite the historical backend;
- migrate objects destructively;
- restore inactive projects merely to test a hypothesis;
- rewrite historical provenance;
- classify unresolved backend identity as fact.

All further work should remain read-only unless an explicit migration or restoration authorization is provided.

## 10. Neural representation

PUB Neural should index the discovery as institutional knowledge while preserving the original source ownership:

```text
LOVABLE / PUB CORE EXECUTIVE
        ↓
HISTORICAL PUB CORE BACKEND
        ↓
PUB CORE WORKSPACE
        ├── operational records
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

The original files remain source artifacts. Neural should consolidate knowledge about them rather than silently becoming their replacement source of truth.

## 11. Next investigation

The next high-value forensic objective is to prove the historical backend identity chain:

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

This record should be updated only with new evidence, preserving prior states and unresolved claims.
