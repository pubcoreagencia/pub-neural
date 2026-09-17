#!/usr/bin/env python3
"""
Seed & Epistemological Governance Engine for PUB Core Holding Project Ontology (V0.3).
Audits all 57 repositories in pub_neural.project_registry and creates
canonical holding_projects with explicit epistemological status:
- CONFIRMED: Verified from explicit documentation or monorepo unification statements
- PROPOSED: Deterministic rule-based family suggestions with confidence score
- UNCLASSIFIED: Intentionally isolated repositories with project_id = NULL
"""

import os
import subprocess
import psycopg2
from psycopg2.extras import RealDictCursor

# 1. Canonical Project Definitions with Epistemological Metadata
HOLDING_PROJECTS = [
    # --- CONFIRMED PROJECTS (6) ---
    {
        "id": "proj:pub-neural",
        "slug": "pub-neural",
        "display_name": "PUB Neural",
        "description": "Cérebro cognitivo, memória episódica/semântica e orquestrador autônomo com abstenção e governança RLS.",
        "project_type": "PLATFORM",
        "lifecycle_status": "ATIVO",
        "is_active": True,
        "is_archived": False,
        "strategic_priority": "CRITICA",
        "ontology_status": "CONFIRMED",
        "ontology_source": "DOCUMENTATION",
        "ontology_confidence": 1.000,
        "ontology_reason": "Especificação arquitetural formal e codebase canônico do sistema neural da holding.",
    },
    {
        "id": "proj:pub-ecom",
        "slug": "pub-ecom",
        "display_name": "PUB E-Commerce",
        "description": "Hub e monorepo unificado de e-commerce da holding: catálogo, inteligência de vendas e integrações de checkout.",
        "project_type": "PRODUCT",
        "lifecycle_status": "ATIVO",
        "is_active": True,
        "is_archived": False,
        "strategic_priority": "CRITICA",
        "ontology_status": "CONFIRMED",
        "ontology_source": "DOCUMENTATION",
        "ontology_confidence": 1.000,
        "ontology_reason": "Monorepo unificado comprovado por documentação e declaração explícita no repositório pub-ecom.",
    },
    {
        "id": "proj:pub-core",
        "slug": "pub-core",
        "display_name": "PUB Core",
        "description": "Sistema operacional e plataforma institucional central da PUB Core Holding.",
        "project_type": "PLATFORM",
        "lifecycle_status": "ATIVO",
        "is_active": True,
        "is_archived": False,
        "strategic_priority": "CRITICA",
        "ontology_status": "CONFIRMED",
        "ontology_source": "DOCUMENTATION",
        "ontology_confidence": 1.000,
        "ontology_reason": "Plataforma central e portal institucional oficial da holding pubcoreagencia.",
    },
    {
        "id": "proj:pub-records",
        "slug": "pub-records",
        "display_name": "PUB Records",
        "description": "Gravadora digital e hub de produção fonográfica e distribuição de beats musicais unificados.",
        "project_type": "MEDIA",
        "lifecycle_status": "ATIVO",
        "is_active": True,
        "is_archived": False,
        "strategic_priority": "PADRAO",
        "ontology_status": "CONFIRMED",
        "ontology_source": "DOCUMENTATION",
        "ontology_confidence": 1.000,
        "ontology_reason": "Repositório de gravadora com unificação explícita documentada de beats fonográficos.",
    },
    {
        "id": "proj:pub-dev-loop",
        "slug": "pub-dev-loop",
        "display_name": "PUB Dev Loop",
        "description": "Infraestrutura contínua de prototipagem, templates de execução e ciclo de desenvolvimento guiado.",
        "project_type": "INFRASTRUCTURE",
        "lifecycle_status": "ATIVO",
        "is_active": True,
        "is_archived": False,
        "strategic_priority": "ALTA",
        "ontology_status": "CONFIRMED",
        "ontology_source": "DOCUMENTATION",
        "ontology_confidence": 1.000,
        "ontology_reason": "Framework de continuidade e templates de desenvolvimento com documentação interna comprovada.",
    },
    {
        "id": "proj:pub-acp",
        "slug": "pub-acp",
        "display_name": "PUB ACP",
        "description": "Implementação e laboratório de orquestração do protocolo Agent Communication Protocol com Antigravity.",
        "project_type": "INTERNAL_SYSTEM",
        "lifecycle_status": "ATIVO",
        "is_active": True,
        "is_archived": False,
        "strategic_priority": "ALTA",
        "ontology_status": "CONFIRMED",
        "ontology_source": "DOCUMENTATION",
        "ontology_confidence": 1.000,
        "ontology_reason": "Repositórios pub-acp-standalone e pub-acp-lab validados documentalmente no ecossistema neural.",
    },

    # --- PROPOSED PROJECTS (28) ---
    # Nomenclaturas e descrições honestas e não-enfáticas
    {
        "id": "proj:pub-machine",
        "slug": "pub-machine",
        "display_name": "PUB Machine",
        "description": "Projeto proposto associado à família de repositórios pub-machine (prospecção e evolução SaaS). Classificação inicial baseada em nomenclatura.",
        "project_type": "PRODUCT",
        "lifecycle_status": "ATIVO",
        "is_active": True,
        "is_archived": False,
        "strategic_priority": "ALTA",
        "ontology_status": "PROPOSED",
        "ontology_source": "RULE",
        "ontology_confidence": 0.900,
        "ontology_reason": "Agrupamento inferido a partir da taxonomia dos repositórios pub-machine, pub-machine-2 e pub-machine-saas.",
    },
    {
        "id": "proj:pub-films",
        "slug": "pub-films",
        "display_name": "PUB Films",
        "description": "Projeto proposto associado aos repositórios de mídia e landing pages cinematográficas. Classificação inferida por regras.",
        "project_type": "MEDIA",
        "lifecycle_status": "ATIVO",
        "is_active": True,
        "is_archived": False,
        "strategic_priority": "PADRAO",
        "ontology_status": "PROPOSED",
        "ontology_source": "RULE",
        "ontology_confidence": 0.900,
        "ontology_reason": "Agrupamento inferido a partir da nomenclatura dos repositórios pub-films e pub-films-landing.",
    },
    {
        "id": "proj:pub-3d",
        "slug": "pub-3d",
        "display_name": "PUB 3D",
        "description": "Projeto proposto para experiências e metaversos 3D WebGL. Classificação inicial baseada em nomenclatura.",
        "project_type": "PRODUCT",
        "lifecycle_status": "ATIVO",
        "is_active": True,
        "is_archived": False,
        "strategic_priority": "PADRAO",
        "ontology_status": "PROPOSED",
        "ontology_source": "RULE",
        "ontology_confidence": 0.900,
        "ontology_reason": "Agrupamento inferido a partir da taxonomia dos repositórios pub-3d e pub3d-landing.",
    },
    {
        "id": "proj:pub-crypto",
        "slug": "pub-crypto",
        "display_name": "PUB Crypto",
        "description": "Projeto proposto associado a gestão de criptoativos e inteligência on-chain. Classificação inferida por regras.",
        "project_type": "PRODUCT",
        "lifecycle_status": "ATIVO",
        "is_active": True,
        "is_archived": False,
        "strategic_priority": "PADRAO",
        "ontology_status": "PROPOSED",
        "ontology_source": "RULE",
        "ontology_confidence": 0.850,
        "ontology_reason": "Agrupamento inferido a partir dos repositórios pub-crypto e ia-pubcrypto.",
    },
    {
        "id": "proj:pub-food",
        "slug": "pub-food",
        "display_name": "PUB Food",
        "description": "Projeto proposto associado à vertical de gastronomia e delivery. Classificação inferida por nomenclatura.",
        "project_type": "SERVICE",
        "lifecycle_status": "ATIVO",
        "is_active": True,
        "is_archived": False,
        "strategic_priority": "PADRAO",
        "ontology_status": "PROPOSED",
        "ontology_source": "RULE",
        "ontology_confidence": 0.850,
        "ontology_reason": "Agrupamento inferido a partir dos repositórios pub-food e pubfood-control-growth.",
    },
    {
        "id": "proj:pub-growth",
        "slug": "pub-growth",
        "display_name": "PUB Growth AI",
        "description": "Projeto proposto de inteligência de crescimento digital e automação. Classificação inicial baseada em taxonomia.",
        "project_type": "INTERNAL_SYSTEM",
        "lifecycle_status": "ATIVO",
        "is_active": True,
        "is_archived": False,
        "strategic_priority": "PADRAO",
        "ontology_status": "PROPOSED",
        "ontology_source": "RULE",
        "ontology_confidence": 0.850,
        "ontology_reason": "Agrupamento inferido a partir dos repositórios pubgrowthai e pubgrowth-ai-evolution.",
    },
    {
        "id": "proj:pub-scrapping",
        "slug": "pub-scrapping",
        "display_name": "PUB Scrapping",
        "description": "Projeto proposto associado a scrapers e ingestores de marketplaces. Classificação inferida por regras.",
        "project_type": "INTERNAL_SYSTEM",
        "lifecycle_status": "ATIVO",
        "is_active": True,
        "is_archived": False,
        "strategic_priority": "PADRAO",
        "ontology_status": "PROPOSED",
        "ontology_source": "RULE",
        "ontology_confidence": 0.850,
        "ontology_reason": "Agrupamento inferido a partir dos repositórios pub-scrapping e pub-shopee-scraper.",
    },
    {
        "id": "proj:leadcore",
        "slug": "leadcore",
        "display_name": "Leadcore",
        "description": "Projeto proposto associado ao repositório leadcore (inteligência de leads B2B). Classificação inicial baseada em metadados.",
        "project_type": "PRODUCT",
        "lifecycle_status": "ATIVO",
        "is_active": True,
        "is_archived": False,
        "strategic_priority": "ALTA",
        "ontology_status": "PROPOSED",
        "ontology_source": "RULE",
        "ontology_confidence": 0.900,
        "ontology_reason": "Entidade criada a partir do repositório pubcoreagencia/leadcore.",
    },
    {
        "id": "proj:sagaz-farm-os",
        "slug": "sagaz-farm-os",
        "display_name": "Sagaz Farm OS",
        "description": "Projeto proposto associado ao repositório sagaz-farm-os (operações rurais e automação). Classificação inferida por nomenclatura.",
        "project_type": "PRODUCT",
        "lifecycle_status": "ATIVO",
        "is_active": True,
        "is_archived": False,
        "strategic_priority": "ALTA",
        "ontology_status": "PROPOSED",
        "ontology_source": "RULE",
        "ontology_confidence": 0.900,
        "ontology_reason": "Entidade criada a partir do repositório pubcoreagencia/sagaz-farm-os.",
    },
    {
        "id": "proj:pub-imoveis",
        "slug": "pub-imoveis",
        "display_name": "PUB Imóveis",
        "description": "Projeto proposto associado ao repositório pub-imoveis (transações imobiliárias). Classificação inferida por nomenclatura.",
        "project_type": "PRODUCT",
        "lifecycle_status": "ATIVO",
        "is_active": True,
        "is_archived": False,
        "strategic_priority": "PADRAO",
        "ontology_status": "PROPOSED",
        "ontology_source": "RULE",
        "ontology_confidence": 0.900,
        "ontology_reason": "Entidade criada a partir do repositório pubcoreagencia/pub-imoveis.",
    },
    {
        "id": "proj:pub-trade",
        "slug": "pub-trade",
        "display_name": "PUB Trade",
        "description": "Projeto proposto associado ao repositório pub-trade. Classificação inicial baseada em metadados e taxonomia.",
        "project_type": "PRODUCT",
        "lifecycle_status": "ATIVO",
        "is_active": True,
        "is_archived": False,
        "strategic_priority": "PADRAO",
        "ontology_status": "PROPOSED",
        "ontology_source": "RULE",
        "ontology_confidence": 0.900,
        "ontology_reason": "Entidade criada a partir do repositório pubcoreagencia/pub-trade.",
    },
    {
        "id": "proj:pub-bnb",
        "slug": "pub-bnb",
        "display_name": "PUB BNB",
        "description": "Projeto proposto associado ao repositório pub-bnb (gestão de locações por temporada). Classificação inferida por nomenclatura.",
        "project_type": "SERVICE",
        "lifecycle_status": "ATIVO",
        "is_active": True,
        "is_archived": False,
        "strategic_priority": "PADRAO",
        "ontology_status": "PROPOSED",
        "ontology_source": "RULE",
        "ontology_confidence": 0.900,
        "ontology_reason": "Entidade criada a partir do repositório pubcoreagencia/pub-bnb.",
    },
    {
        "id": "proj:pub-textil",
        "slug": "pub-textil",
        "display_name": "PUB Têxtil",
        "description": "Projeto proposto associado ao repositório pub-textil (cadeia de confecção private label). Classificação inferida por nomenclatura.",
        "project_type": "SERVICE",
        "lifecycle_status": "ATIVO",
        "is_active": True,
        "is_archived": False,
        "strategic_priority": "PADRAO",
        "ontology_status": "PROPOSED",
        "ontology_source": "RULE",
        "ontology_confidence": 0.900,
        "ontology_reason": "Entidade criada a partir do repositório pubcoreagencia/pub-textil.",
    },
    {
        "id": "proj:pub-media",
        "slug": "pub-media",
        "display_name": "PUB Media",
        "description": "Projeto proposto associado ao repositório pub-media (mídia e tráfego pago). Classificação inferida por nomenclatura.",
        "project_type": "SERVICE",
        "lifecycle_status": "ATIVO",
        "is_active": True,
        "is_archived": False,
        "strategic_priority": "PADRAO",
        "ontology_status": "PROPOSED",
        "ontology_source": "RULE",
        "ontology_confidence": 0.900,
        "ontology_reason": "Entidade criada a partir do repositório pubcoreagencia/pub-media.",
    },
    {
        "id": "proj:pub-leads",
        "slug": "pub-leads",
        "display_name": "PUB Leads",
        "description": "Projeto proposto associado ao repositório pub-leads (enriquecimento de leads comerciais). Classificação inferida por nomenclatura.",
        "project_type": "SERVICE",
        "lifecycle_status": "ATIVO",
        "is_active": True,
        "is_archived": False,
        "strategic_priority": "PADRAO",
        "ontology_status": "PROPOSED",
        "ontology_source": "RULE",
        "ontology_confidence": 0.900,
        "ontology_reason": "Entidade criada a partir do repositório pubcoreagencia/pub-leads.",
    },
    {
        "id": "proj:pub-ia",
        "slug": "pub-ia",
        "display_name": "PUB IA",
        "description": "Projeto proposto associado ao repositório pub-ia (ferramentas e automações de inteligência artificial). Classificação inferida por regras.",
        "project_type": "INTERNAL_SYSTEM",
        "lifecycle_status": "ATIVO",
        "is_active": True,
        "is_archived": False,
        "strategic_priority": "ALTA",
        "ontology_status": "PROPOSED",
        "ontology_source": "RULE",
        "ontology_confidence": 0.900,
        "ontology_reason": "Entidade criada a partir do repositório pubcoreagencia/pub-ia.",
    },
    {
        "id": "proj:pubet",
        "slug": "pubet",
        "display_name": "PUBET",
        "description": "Projeto proposto associado ao repositório pubet (entretenimento e jogos digitais). Classificação inferida por nomenclatura.",
        "project_type": "PRODUCT",
        "lifecycle_status": "ATIVO",
        "is_active": True,
        "is_archived": False,
        "strategic_priority": "PADRAO",
        "ontology_status": "PROPOSED",
        "ontology_source": "RULE",
        "ontology_confidence": 0.900,
        "ontology_reason": "Entidade criada a partir do repositório pubcoreagencia/pubet.",
    },
    {
        "id": "proj:pub-games-studio",
        "slug": "pub-games-studio",
        "display_name": "PUB Games Studio",
        "description": "Projeto proposto associado ao repositório pub-games-studio (desenvolvimento de jogos e gamificação). Classificação inferida por regras.",
        "project_type": "LABORATORY",
        "lifecycle_status": "ATIVO",
        "is_active": True,
        "is_archived": False,
        "strategic_priority": "PADRAO",
        "ontology_status": "PROPOSED",
        "ontology_source": "RULE",
        "ontology_confidence": 0.900,
        "ontology_reason": "Entidade criada a partir do repositório pubcoreagencia/pub-games-studio.",
    },
    {
        "id": "proj:pub-lancamentos",
        "slug": "pub-lancamentos",
        "display_name": "PUB Lançamentos",
        "description": "Projeto proposto associado ao repositório pub-lancamentos (playbooks de lançamentos). Classificação inferida por nomenclatura.",
        "project_type": "SERVICE",
        "lifecycle_status": "ATIVO",
        "is_active": True,
        "is_archived": False,
        "strategic_priority": "PADRAO",
        "ontology_status": "PROPOSED",
        "ontology_source": "RULE",
        "ontology_confidence": 0.900,
        "ontology_reason": "Entidade criada a partir do repositório pubcoreagencia/pub-lancamentos.",
    },
    {
        "id": "proj:pub-start",
        "slug": "pub-start",
        "display_name": "PUB Start",
        "description": "Projeto proposto associado ao repositório pub-start (incubação e bootstrap de negócios). Classificação inferida por regras.",
        "project_type": "LABORATORY",
        "lifecycle_status": "ATIVO",
        "is_active": True,
        "is_archived": False,
        "strategic_priority": "PADRAO",
        "ontology_status": "PROPOSED",
        "ontology_source": "RULE",
        "ontology_confidence": 0.900,
        "ontology_reason": "Entidade criada a partir do repositório pubcoreagencia/pub-start.",
    },
    {
        "id": "proj:pub-rate-calculator",
        "slug": "pub-rate-calculator",
        "display_name": "PUB Rate Calculator",
        "description": "Projeto proposto associado ao repositório pub-rate-calculator (calculadora de taxas e precificação). Classificação inferida por regras.",
        "project_type": "INTERNAL_SYSTEM",
        "lifecycle_status": "ATIVO",
        "is_active": True,
        "is_archived": False,
        "strategic_priority": "PADRAO",
        "ontology_status": "PROPOSED",
        "ontology_source": "RULE",
        "ontology_confidence": 0.900,
        "ontology_reason": "Entidade criada a partir do repositório pubcoreagencia/pub-rate-calculator.",
    },
    {
        "id": "proj:pub-ops-hub",
        "slug": "pub-ops-hub",
        "display_name": "PUB Ops Hub",
        "description": "Projeto proposto associado ao repositório pub-ops-hub (central integradora de operações). Classificação inferida por regras.",
        "project_type": "INFRASTRUCTURE",
        "lifecycle_status": "ATIVO",
        "is_active": True,
        "is_archived": False,
        "strategic_priority": "PADRAO",
        "ontology_status": "PROPOSED",
        "ontology_source": "RULE",
        "ontology_confidence": 0.900,
        "ontology_reason": "Entidade criada a partir do repositório pubcoreagencia/pub-ops-hub.",
    },
    {
        "id": "proj:pub-9router-cloud",
        "slug": "pub-9router-cloud",
        "display_name": "PUB 9router Cloud",
        "description": "Projeto proposto associado ao repositório pub-9router-cloud (roteamento em nuvem). Classificação inferida por regras.",
        "project_type": "INFRASTRUCTURE",
        "lifecycle_status": "ATIVO",
        "is_active": True,
        "is_archived": False,
        "strategic_priority": "PADRAO",
        "ontology_status": "PROPOSED",
        "ontology_source": "RULE",
        "ontology_confidence": 0.900,
        "ontology_reason": "Entidade criada a partir do repositório pubcoreagencia/pub-9router-cloud.",
    },
    {
        "id": "proj:xp-audio-lab",
        "slug": "xp-audio-lab",
        "display_name": "XP Audio Lab",
        "description": "Projeto proposto associado ao repositório xp-audio-lab (laboratório de áudio e sound design). Classificação inferida por nomenclatura.",
        "project_type": "LABORATORY",
        "lifecycle_status": "ATIVO",
        "is_active": True,
        "is_archived": False,
        "strategic_priority": "PADRAO",
        "ontology_status": "PROPOSED",
        "ontology_source": "RULE",
        "ontology_confidence": 0.900,
        "ontology_reason": "Entidade criada a partir do repositório pubcoreagencia/xp-audio-lab.",
    },
    {
        "id": "proj:buzios-de-cima",
        "slug": "buzios-de-cima",
        "display_name": "Búzios de Cima Drone",
        "description": "Projeto proposto associado ao repositório buzios-de-cima (captação aérea e drones). Classificação inferida por nomenclatura.",
        "project_type": "SERVICE",
        "lifecycle_status": "ATIVO",
        "is_active": True,
        "is_archived": False,
        "strategic_priority": "PADRAO",
        "ontology_status": "PROPOSED",
        "ontology_source": "RULE",
        "ontology_confidence": 0.900,
        "ontology_reason": "Entidade criada a partir do repositório pubcoreagencia/buzios-de-cima.",
    },
    {
        "id": "proj:eternize-seu-pinscher",
        "slug": "eternize-seu-pinscher",
        "display_name": "Eternize Seu Pinscher",
        "description": "Projeto proposto associado ao repositório eternize-seu-pinscher (modelagem e impressão 3D pet). Classificação inferida por regras.",
        "project_type": "PRODUCT",
        "lifecycle_status": "ATIVO",
        "is_active": True,
        "is_archived": False,
        "strategic_priority": "PADRAO",
        "ontology_status": "PROPOSED",
        "ontology_source": "RULE",
        "ontology_confidence": 0.900,
        "ontology_reason": "Entidade criada a partir do repositório pubcoreagencia/eternize-seu-pinscher.",
    },
    {
        "id": "proj:nortefishing",
        "slug": "nortefishing",
        "display_name": "Nortefishing",
        "description": "Projeto proposto associado ao repositório nortefishing (pesca esportiva e operações náuticas). Classificação inferida por nomenclatura.",
        "project_type": "SERVICE",
        "lifecycle_status": "ATIVO",
        "is_active": True,
        "is_archived": False,
        "strategic_priority": "PADRAO",
        "ontology_status": "PROPOSED",
        "ontology_source": "RULE",
        "ontology_confidence": 0.900,
        "ontology_reason": "Entidade criada a partir do repositório pubcoreagencia/nortefishing.",
    },
    {
        "id": "proj:incubacao-labs",
        "slug": "incubacao-labs",
        "display_name": "Incubação & Laboratórios",
        "description": "Laboratório de incubação, prototipagem e projetos exploratórios sem destinação de produção fixa.",
        "project_type": "LABORATORY",
        "lifecycle_status": "ATIVO",
        "is_active": True,
        "is_archived": False,
        "strategic_priority": "PADRAO",
        "ontology_status": "PROPOSED",
        "ontology_source": "RULE",
        "ontology_confidence": 0.850,
        "ontology_reason": "Agrupador inferido para repositórios exploratórios sem projeto específico.",
    },
]

# 2. Association Map: (project_id, repository_id, relationship_type, is_primary, association_status, source, confidence, reason)
ASSOCIATIONS = [
    # PUB E-Commerce (Multi-repo unificado) - CONFIRMED
    ("proj:pub-ecom", "pub-ecom", "PRIMARY", True, "CONFIRMED", "DOCUMENTATION", 1.000, "Monorepo principal do PUB E-Commerce comprovado"),
    ("proj:pub-ecom", "pub-ecom-catalog-worker", "WORKER", False, "CONFIRMED", "DOCUMENTATION", 1.000, "Documentado explicitamente: unificado em pub-ecom"),
    ("proj:pub-ecom", "pub-ecom-landing", "LANDING", False, "CONFIRMED", "DOCUMENTATION", 1.000, "Documentado explicitamente: unificado em pub-ecom"),
    ("proj:pub-ecom", "pubecomhub", "PLATFORM", False, "CONFIRMED", "DOCUMENTATION", 1.000, "Documentado explicitamente: unificado em pub-ecom"),

    # PUB Records (Gravadora e beats unificados) - CONFIRMED
    ("proj:pub-records", "pub-records", "PRIMARY", True, "CONFIRMED", "DOCUMENTATION", 1.000, "Repositório principal da gravadora PUB Records"),
    ("proj:pub-records", "pub-beats", "LEGACY", False, "CONFIRMED", "DOCUMENTATION", 1.000, "Documentado explicitamente: unificado em pub-records (beats/)"),

    # PUB Neural - CONFIRMED
    ("proj:pub-neural", "pub-neural", "PRIMARY", True, "CONFIRMED", "DOCUMENTATION", 1.000, "Repositório canônico do cérebro cognitivo PUB Neural"),
    ("proj:pub-neural", "neural-os", "BACKEND", False, "CONFIRMED", "RULE", 0.950, "Módulo de backend do sistema operacional cognitivo Neural"),

    # PUB Core (Holding portal, OS e plataforma web) - CONFIRMED
    ("proj:pub-core", "pub-core", "PRIMARY", True, "CONFIRMED", "RULE", 0.950, "Core repositório de plataforma institucional"),
    ("proj:pub-core", "pubcore", "PRIMARY", False, "CONFIRMED", "DOCUMENTATION", 0.950, "Plataforma e sistema web principal da PUB Core"),
    ("proj:pub-core", "pub-core-os", "INFRASTRUCTURE", False, "CONFIRMED", "DOCUMENTATION", 0.950, "PUB Core OS - Sistema operacional institucional"),
    ("proj:pub-core", "pub-core-holding-portal", "LANDING", False, "CONFIRMED", "DOCUMENTATION", 0.950, "Portal institucional e comercial da holding"),
    ("proj:pub-core", "pub-co", "LANDING", False, "PROPOSED", "RULE", 0.850, "Portal institucional global de acesso à holding"),
    ("proj:pub-core", "pubcoreagencia.github.io", "LANDING", False, "PROPOSED", "RULE", 0.850, "Página institucional do GitHub Pages da agência"),
    ("proj:pub-core", "pub-agencia-landing", "LANDING", False, "PROPOSED", "RULE", 0.850, "Landing page oficial da agência PUB"),

    # PUB Dev Loop - CONFIRMED
    ("proj:pub-dev-loop", "pub-dev-loop", "PRIMARY", True, "CONFIRMED", "DOCUMENTATION", 1.000, "Infraestrutura principal de desenvolvimento em loop"),
    ("proj:pub-dev-loop", "pub-dev-loop-prototypes", "EXPERIMENT", False, "CONFIRMED", "DOCUMENTATION", 0.950, "Repositório de protótipos de sessões"),
    ("proj:pub-dev-loop", "pub-dev-loop-template", "DOCUMENTATION", False, "CONFIRMED", "DOCUMENTATION", 0.950, "Template para sessões de continuidade"),
    ("proj:pub-dev-loop", "pub-prototype", "EXPERIMENT", False, "PROPOSED", "RULE", 0.850, "Ambiente legado de prototipagem"),

    # PUB ACP - CONFIRMED
    ("proj:pub-acp", "pub-acp-standalone", "PRIMARY", True, "CONFIRMED", "RULE", 0.950, "Implementação autônoma do protocolo ACP"),
    ("proj:pub-acp", "pub-acp-lab", "EXPERIMENT", False, "CONFIRMED", "DOCUMENTATION", 0.950, "Laboratório experimental de orquestração com Antigravity"),

    # PUB Machine - PROPOSED
    ("proj:pub-machine", "pub-machine", "PRIMARY", True, "PROPOSED", "RULE", 0.900, "Motor de prospecção autônoma v1"),
    ("proj:pub-machine", "pub-machine-2", "BACKEND", False, "PROPOSED", "RULE", 0.900, "Evolução autônoma de segunda geração"),
    ("proj:pub-machine", "pub-machine-saas", "PLATFORM", False, "PROPOSED", "RULE", 0.900, "Versão SaaS multi-tenant para clientes externos"),

    # PUB Films - PROPOSED
    ("proj:pub-films", "pub-films", "PRIMARY", True, "PROPOSED", "RULE", 0.900, "Produção audiovisual cinematográfica principal"),
    ("proj:pub-films", "pub-films-landing", "LANDING", False, "PROPOSED", "RULE", 0.900, "Landing page cinematográfica"),

    # PUB 3D - PROPOSED
    ("proj:pub-3d", "pub-3d", "PRIMARY", True, "PROPOSED", "RULE", 0.900, "Experiências e metaversos 3D WebGL"),
    ("proj:pub-3d", "pub3d-landing", "LANDING", False, "PROPOSED", "RULE", 0.900, "Landing page interativa de 3D"),

    # PUB Crypto - PROPOSED
    ("proj:pub-crypto", "pub-crypto", "PRIMARY", True, "PROPOSED", "RULE", 0.850, "Gestão de tesouraria de criptoativos"),
    ("proj:pub-crypto", "ia-pubcrypto", "WORKER", False, "PROPOSED", "RULE", 0.850, "Agente preditivo de inteligência on-chain"),

    # PUB Food - PROPOSED
    ("proj:pub-food", "pub-food", "PRIMARY", True, "PROPOSED", "RULE", 0.850, "Operação central de dark kitchens"),
    ("proj:pub-food", "pubfood-control-growth", "WORKER", False, "PROPOSED", "RULE", 0.800, "Painel de controle de crescimento do setor food"),

    # PUB Growth AI - PROPOSED
    ("proj:pub-growth", "pubgrowthai", "PRIMARY", True, "PROPOSED", "RULE", 0.850, "Hub de automações de growth"),
    ("proj:pub-growth", "pubgrowth-ai-evolution", "EXPERIMENT", False, "PROPOSED", "RULE", 0.800, "Módulo evolutivo de growth com IA"),

    # PUB Scrapping - PROPOSED
    ("proj:pub-scrapping", "pub-scrapping", "PRIMARY", True, "PROPOSED", "RULE", 0.850, "Engenharia central de scrapers"),
    ("proj:pub-scrapping", "pub-shopee-scraper", "WORKER", False, "PROPOSED", "RULE", 0.850, "Worker especializado de scraping Shopee"),

    # Projetos Únicos / Verticais Autônomas - PROPOSED
    ("proj:leadcore", "leadcore", "PRIMARY", True, "PROPOSED", "RULE", 0.900, "Core CRM e inteligência de leads B2B"),
    ("proj:sagaz-farm-os", "sagaz-farm-os", "PRIMARY", True, "PROPOSED", "RULE", 0.900, "Sistema operacional de fazendas"),
    ("proj:pub-imoveis", "pub-imoveis", "PRIMARY", True, "PROPOSED", "RULE", 0.900, "Plataforma de transações imobiliárias"),
    ("proj:pub-trade", "pub-trade", "PRIMARY", True, "PROPOSED", "RULE", 0.900, "Sistemas algorítmicos quantitativos de trade"),
    ("proj:pub-bnb", "pub-bnb", "PRIMARY", True, "PROPOSED", "RULE", 0.900, "Gestão de hospitalidade de temporada"),
    ("proj:pub-textil", "pub-textil", "PRIMARY", True, "PROPOSED", "RULE", 0.900, "Cadeia de suprimentos e confecção private label"),
    ("proj:pub-media", "pub-media", "PRIMARY", True, "PROPOSED", "RULE", 0.900, "Distribuição de mídia e tráfego pago"),
    ("proj:pub-leads", "pub-leads", "PRIMARY", True, "PROPOSED", "RULE", 0.900, "Enriquecimento e geração de leads"),
    ("proj:pub-ia", "pub-ia", "PRIMARY", True, "PROPOSED", "RULE", 0.900, "Hub de IA corporativa"),
    ("proj:pubet", "pubet", "PRIMARY", True, "PROPOSED", "RULE", 0.900, "Plataforma de entretenimento e apostas reguladas"),
    ("proj:pub-games-studio", "pub-games-studio", "PRIMARY", True, "PROPOSED", "RULE", 0.900, "Estúdio de jogos e gamificação"),
    ("proj:pub-lancamentos", "pub-lancamentos", "PRIMARY", True, "PROPOSED", "RULE", 0.900, "Playbooks e infra de lançamentos"),
    ("proj:pub-start", "pub-start", "PRIMARY", True, "PROPOSED", "RULE", 0.900, "Incubadora de bootstrap de negócios"),
    ("proj:pub-rate-calculator", "pub-rate-calculator", "PRIMARY", True, "PROPOSED", "RULE", 0.900, "Calculadora de taxas e precificação"),
    ("proj:pub-ops-hub", "pub-ops-hub", "PRIMARY", True, "PROPOSED", "RULE", 0.900, "Central de operações"),
    ("proj:pub-9router-cloud", "pub-9router-cloud", "PRIMARY", True, "PROPOSED", "RULE", 0.900, "Roteamento inteligente em cloud"),
    ("proj:xp-audio-lab", "xp-audio-lab", "PRIMARY", True, "PROPOSED", "RULE", 0.900, "Laboratório de áudio e sound design"),
    ("proj:buzios-de-cima", "buzios-de-cima", "PRIMARY", True, "PROPOSED", "RULE", 0.900, "Captação aérea audiovisual e drones"),
    ("proj:eternize-seu-pinscher", "eternize-seu-pinscher", "PRIMARY", True, "PROPOSED", "RULE", 0.900, "Eternização e modelagem 3D pet"),
    ("proj:nortefishing", "nortefishing", "PRIMARY", True, "PROPOSED", "RULE", 0.900, "Operação de pesca esportiva"),
]

# Note: 'pub-github-mcp' is intentionally NOT in ASSOCIATIONS.
# It represents an unclassified tool/infrastructure connector, proving the UNCLASSIFIED state!


def run_seed():
    db_vars = subprocess.check_output(["railway", "variables", "--kv"], text=True)
    url = None
    for line in db_vars.splitlines():
        if "PUB_NEURAL_DB_URL=" in line:
            url = line.split("PUB_NEURAL_DB_URL=")[1].strip()
            break

    if not url:
        raise ValueError("Could not find PUB_NEURAL_DB_URL in Railway environment")

    conn = psycopg2.connect(url)
    conn.autocommit = False
    cur = conn.cursor(cursor_factory=RealDictCursor)

    try:
        print("1. Inserting / Updating Holding Projects with Epistemological Metadata...")
        for p in HOLDING_PROJECTS:
            cur.execute("""
                INSERT INTO pub_neural.holding_projects (
                    id, slug, display_name, description, project_type,
                    lifecycle_status, is_active, is_archived, strategic_priority,
                    ontology_status, ontology_source, ontology_confidence, ontology_reason,
                    ontology_verified_at, ontology_verified_by
                ) VALUES (
                    %(id)s, %(slug)s, %(display_name)s, %(description)s, %(project_type)s,
                    %(lifecycle_status)s, %(is_active)s, %(is_archived)s, %(strategic_priority)s,
                    %(ontology_status)s, %(ontology_source)s, %(ontology_confidence)s, %(ontology_reason)s,
                    CASE WHEN %(ontology_status)s = 'CONFIRMED' THEN CURRENT_TIMESTAMP ELSE NULL END,
                    'system:ontology-classifier'
                )
                ON CONFLICT (id) DO UPDATE SET
                    slug = EXCLUDED.slug,
                    display_name = EXCLUDED.display_name,
                    description = EXCLUDED.description,
                    project_type = EXCLUDED.project_type,
                    lifecycle_status = EXCLUDED.lifecycle_status,
                    is_active = EXCLUDED.is_active,
                    is_archived = EXCLUDED.is_archived,
                    strategic_priority = EXCLUDED.strategic_priority,
                    ontology_status = EXCLUDED.ontology_status,
                    ontology_source = EXCLUDED.ontology_source,
                    ontology_confidence = EXCLUDED.ontology_confidence,
                    ontology_reason = EXCLUDED.ontology_reason,
                    ontology_verified_at = EXCLUDED.ontology_verified_at,
                    ontology_verified_by = EXCLUDED.ontology_verified_by,
                    updated_at = CURRENT_TIMESTAMP;
            """, p)

        print("2. Inserting / Updating Project Repository Associations...")
        for a in ASSOCIATIONS:
            cur.execute("""
                INSERT INTO pub_neural.project_repositories (
                    project_id, repository_id, relationship_type, is_primary,
                    association_status, classification_source, classification_confidence,
                    classification_reason
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (project_id, repository_id) DO UPDATE SET
                    relationship_type = EXCLUDED.relationship_type,
                    is_primary = EXCLUDED.is_primary,
                    association_status = EXCLUDED.association_status,
                    classification_source = EXCLUDED.classification_source,
                    classification_confidence = EXCLUDED.classification_confidence,
                    classification_reason = EXCLUDED.classification_reason,
                    updated_at = CURRENT_TIMESTAMP;
            """, a)

        conn.commit()
        print("Ontology seed committed successfully!")

        # Verification audit
        cur.execute("SELECT COUNT(*) AS total_projects FROM pub_neural.holding_projects;")
        tot_proj = cur.fetchone()["total_projects"]

        cur.execute("""
            SELECT ontology_status, COUNT(*) AS count
            FROM pub_neural.holding_projects
            GROUP BY ontology_status;
        """)
        proj_statuses = cur.fetchall()

        cur.execute("SELECT COUNT(DISTINCT repository_id) AS mapped_repos FROM pub_neural.project_repositories;")
        mapped_repos = cur.fetchone()["mapped_repos"]

        cur.execute("SELECT COUNT(*) AS total_repos FROM pub_neural.project_registry;")
        tot_repos = cur.fetchone()["total_repos"]

        cur.execute("""
            SELECT id, repository_name FROM pub_neural.project_registry
            WHERE id NOT IN (SELECT repository_id FROM pub_neural.project_repositories);
        """)
        unclassified = cur.fetchall()

        cur.execute("""
            SELECT association_status, COUNT(*) as count
            FROM pub_neural.project_repositories
            GROUP BY association_status;
        """)
        status_counts = cur.fetchall()

        print("\n=== ONTOLOGY AUDIT REPORT (V0.3) ===")
        print(f"Total Holding Projects: {tot_proj}")
        print("Holding Project Statuses:")
        for ps in proj_statuses:
            print(f"  - {ps['ontology_status']}: {ps['count']}")
        print(f"Total Repositories:     {tot_repos}")
        print(f"Associated Repos:       {mapped_repos}")
        print(f"Unclassified Repos:     {len(unclassified)} -> {[r['id'] for r in unclassified]}")
        print("Association Statuses:")
        for sc in status_counts:
            print(f"  - {sc['association_status']}: {sc['count']}")

    except Exception as e:
        conn.rollback()
        print(f"Error during ontology seed: {e}")
        raise
    finally:
        cur.close()
        conn.close()


if __name__ == "__main__":
    run_seed()
