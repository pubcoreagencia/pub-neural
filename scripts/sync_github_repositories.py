#!/usr/bin/env python3
"""
Synchronizes GitHub repositories from the pubcoreagencia organization into pub_neural.project_registry.
Ensures idempotent execution, preserves historical records, and categorizes products.
"""

import json
import os
import subprocess
import sys
from typing import Any, Dict, List
import psycopg2
from psycopg2.extras import execute_values


def infer_category(name: str, desc: str) -> str:
    name_lower = name.lower()
    desc_lower = (desc or "").lower()

    if any(k in name_lower for k in ["neural", "ia", "growth", "lead", "agent"]):
        return "INTELIGENCIA_ARTIFICIAL"
    if any(k in name_lower for k in ["ecom", "catalog", "shopee", "scrapping"]):
        return "COMMERCE"
    if any(k in name_lower for k in ["films", "media", "3d", "beats", "records"]):
        return "AUDIOVISUAL_E_MIDIA"
    if any(k in name_lower for k in ["machine", "dev-loop", "prototype", "core-os", "router", "ops", "mcp"]):
        return "INFRAESTRUTURA_E_CORE"
    if any(k in name_lower for k in ["imoveis", "bnb", "trade", "crypto"]):
        return "FINANCAS_E_ATIVOS"
    if any(k in name_lower for k in ["food", "textil", "farm", "fishing"]):
        return "VERTICAIS_OPERACIONAIS"
    return "PRODUTO_E_LABS"


def infer_display_name(name: str) -> str:
    parts = name.replace("_", "-").split("-")
    cleaned = [p.upper() if p.lower() in ["pub", "os", "ia", "crm", "api", "ui", "acp", "bnb", "3d"] else p.capitalize() for p in parts]
    return " ".join(cleaned)


def sync_repositories(db_url: str) -> int:
    cmd = ["gh", "repo", "list", "pubcoreagencia", "--limit", "150", "--json", "name,description,isArchived,url,updatedAt,createdAt,isPrivate"]
    res = subprocess.run(cmd, capture_output=True, text=True, check=True)
    repos: List[Dict[str, Any]] = json.loads(res.stdout)

    rows = []
    for r in repos:
        name = r["name"]
        slug = name.lower()
        full_name = f"pubcoreagencia/{name}"
        desc = r.get("description") or ""
        is_archived = bool(r.get("isArchived"))
        is_private = bool(r.get("isPrivate"))
        category = infer_category(name, desc)
        display_name = infer_display_name(name)
        github_url = r.get("url") or f"https://github.com/pubcoreagencia/{name}"

        lifecycle = "ARQUIVADO" if is_archived else "ATIVO"
        is_active = not is_archived

        rows.append((
            slug,
            full_name,
            name,
            display_name,
            desc,
            category,
            lifecycle,
            is_active,
            is_archived,
            is_private,
            True,  # monitoring_enabled
            "ESTRATEGICO" if "neural" in slug or "core" in slug else "OPERACIONAL",
            github_url
        ))

    conn = psycopg2.connect(db_url)
    with conn:
        with conn.cursor() as cur:
            query = """
                INSERT INTO pub_neural.project_registry (
                    id, repository_full_name, repository_name, display_name,
                    description, category, lifecycle_status, is_active,
                    is_archived, is_private, monitoring_enabled, strategic_priority,
                    github_url, updated_at, last_discovered_at
                ) VALUES %s
                ON CONFLICT (id) DO UPDATE SET
                    repository_full_name = EXCLUDED.repository_full_name,
                    repository_name = EXCLUDED.repository_name,
                    display_name = EXCLUDED.display_name,
                    description = COALESCE(NULLIF(EXCLUDED.description, ''), pub_neural.project_registry.description),
                    category = EXCLUDED.category,
                    lifecycle_status = EXCLUDED.lifecycle_status,
                    is_active = EXCLUDED.is_active,
                    is_archived = EXCLUDED.is_archived,
                    is_private = EXCLUDED.is_private,
                    github_url = EXCLUDED.github_url,
                    updated_at = CURRENT_TIMESTAMP,
                    last_discovered_at = CURRENT_TIMESTAMP;
            """
            template = "(%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)"
            execute_values(cur, query, rows, template=template)

    print(f"Synced {len(rows)} repositories into pub_neural.project_registry.")
    return len(rows)


if __name__ == "__main__":
    db_url = os.environ.get("PUB_NEURAL_DB_URL")
    if not db_url:
        db_url = "postgresql://postgres.edorvqdgqgpiwxozolzx:PUBrecords%405929@aws-0-sa-east-1.pooler.supabase.com:5432/postgres?sslmode=require&connect_timeout=10"
    sync_repositories(db_url)
