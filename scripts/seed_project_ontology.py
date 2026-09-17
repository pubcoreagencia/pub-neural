#!/usr/bin/env python3
"""
Seed & Classification Engine for PUB Core Holding Project Ontology (V0.2).
Audits all 57 repositories in pub_neural.project_registry and creates
canonical holding_projects with explicit epistemological status:
- CONFIRMED: Verified from documentation or monorepo unification statements
- PROPOSED: Deterministic rule-based family suggestions with confidence score
- UNCLASSIFIED: Intentionally isolated repositories with project_id = NULL
"""

import os
import subprocess
import psycopg2
from psycopg2.extras import RealDictCursor

# 1. Canonical Project Definitions
HOLDING_PROJECTS = [
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
    },
    {
        "id": "proj:pub-neural",
        "slug": "pub-neural",
        "display_name": "PUB Neural",
        "description": "Cérebro cognitivo, memória episódica/semântica e orquestrador autônomo com abstencao e governança RLS.",
        "project_type": "PLATFORM",
        "lifecycle_status": "ATIVO",
        "is_active": True,
        "is_archived": False,
        "strategic_priority": "CRITICA",
    },
    {
        "id": "proj:pub-machine",
        "slug": "pub-machine",
        "display_name": "PUB Machine",
        "description": "Motor automatizado de prospecção, geração de negócios B2B e evolução SaaS multi-tenant.",
        "project_type": "PRODUCT",
        "lifecycle_status": "ATIVO",
        "is_active": True,
        "is_archived": False,
        "strategic_priority": "ALTA",
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
    },
    {
        "id": "proj:pub-records",
        "slug": "pub-records",
        "display_name": "PUB Records",
        "description": "Gravadora digital, hub de produção fonográfica e distribuição de beats musicais.",
        "project_type": "MEDIA",
        "lifecycle_status": "ATIVO",
        "is_active": True,
        "is_archived": False,
        "strategic_priority": "PADRAO",
    },
    {
        "id": "proj:pub-films",
        "slug": "pub-films",
        "display_name": "PUB Films",
        "description": "Produção audiovisual cinematográfica, publicidade de alto impacto e landing pages cinematográficas.",
        "project_type": "MEDIA",
        "lifecycle_status": "ATIVO",
        "is_active": True,
        "is_archived": False,
        "strategic_priority": "PADRAO",
    },
    {
        "id": "proj:pub-3d",
        "slug": "pub-3d",
        "display_name": "PUB 3D",
        "description": "Experiências imersivas 3D, WebGL e metaversos corporativos interativos.",
        "project_type": "PRODUCT",
        "lifecycle_status": "ATIVO",
        "is_active": True,
        "is_archived": False,
        "strategic_priority": "PADRAO",
    },
    {
        "id": "proj:pub-crypto",
        "slug": "pub-crypto",
        "display_name": "PUB Crypto",
        "description": "Gestão de tesouraria de criptoativos, análise on-chain preditiva e infraestrutura blockchain.",
        "project_type": "PRODUCT",
        "lifecycle_status": "ATIVO",
        "is_active": True,
        "is_archived": False,
        "strategic_priority": "PADRAO",
    },
    {
        "id": "proj:pub-food",
        "slug": "pub-food",
        "display_name": "PUB Food",
        "description": "Operação de dark kitchens, delivery inteligente e controle de crescimento gastronômico.",
        "project_type": "SERVICE",
        "lifecycle_status": "ATIVO",
        "is_active": True,
        "is_archived": False,
        "strategic_priority": "PADRAO",
    },
    {
        "id": "proj:pub-growth",
        "slug": "pub-growth",
        "display_name": "PUB Growth AI",
        "description": "Automações inteligentes de crescimento, evolução de métricas e tração digital com IA.",
        "project_type": "INTERNAL_SYSTEM",
        "lifecycle_status": "ATIVO",
        "is_active": True,
        "is_archived": False,
        "strategic_priority": "PADRAO",
    },
    {
        "id": "proj:pub-scrapping",
        "slug": "pub-scrapping",
        "display_name": "PUB Scrapping",
        "description": "Engenharia de scrapers e ingestores de dados de marketplaces (Shopee, Mercado Livre).",
        "project_type": "INTERNAL_SYSTEM",
        "lifecycle_status": "ATIVO",
        "is_active": True,
        "is_archived": False,
        "strategic_priority": "PADRAO",
    },
    {
        "id": "proj:pub-acp",
        "slug": "pub-acp",
        "display_name": "PUB ACP",
        "description": "Orquestração programática de clientes e agentes autônomos com Google Antigravity.",
        "project_type": "INTERNAL_SYSTEM",
        "lifecycle_status": "ATIVO",
        "is_active": True,
        "is_archived": False,
        "strategic_priority": "ALTA",
    },
    {
        "id": "proj:leadcore",
        "slug": "leadcore",
        "display_name": "Leadcore",
        "description": "Core de inteligência e base unificada de contatos e CRM B2B.",
        "project_type": "PRODUCT",
        "lifecycle_status": "ATIVO",
        "is_active": True,
        "is_archived": False,
        "strategic_priority": "ALTA",
    },
    {
        "id": "proj:sagaz-farm-os",
        "slug": "sagaz-farm-os",
        "display_name": "Sagaz Farm OS",
        "description": "Sistema operacional agrícola e automações de sensoriamento e controle de fazenda.",
        "project_type": "PRODUCT",
        "lifecycle_status": "ATIVO",
        "is_active": True,
        "is_archived": False,
        "strategic_priority": "ALTA",
    },
    {
        "id": "proj:pub-imoveis",
        "slug": "pub-imoveis",
        "display_name": "PUB Imóveis",
        "description": "Plataforma inteligente de transações imobiliárias e tokenização de ativos reais.",
        "project_type": "PRODUCT",
        "lifecycle_status": "ATIVO",
        "is_active": True,
        "is_archived": False,
        "strategic_priority": "PADRAO",
    },
    {
        "id": "proj:pub-trade",
        "slug": "pub-trade",
        "display_name": "PUB Trade",
        "description": "Sistemas algorítmicos automatizados de trading quantitativo.",
        "project_type": "PRODUCT",
        "lifecycle_status": "ATIVO",
        "is_active": True,
        "is_archived": False,
        "strategic_priority": "PADRAO",
    },
    {
        "id": "proj:pub-bnb",
        "slug": "pub-bnb",
        "display_name": "PUB BNB",
        "description": "Gestão algorítmica de locações de temporada e hospitalidade de luxo.",
        "project_type": "SERVICE",
        "lifecycle_status": "ATIVO",
        "is_active": True,
        "is_archived": False,
        "strategic_priority": "PADRAO",
    },
    {
        "id": "proj:pub-textil",
        "slug": "pub-textil",
        "display_name": "PUB Têxtil",
        "description": "Confecção inteligente, private label e cadeia de suprimentos têxtil.",
        "project_type": "SERVICE",
        "lifecycle_status": "ATIVO",
        "is_active": True,
        "is_archived": False,
        "strategic_priority": "PADRAO",
    },
    {
        "id": "proj:pub-media",
        "slug": "pub-media",
        "display_name": "PUB Media",
        "description": "Braço de distribuição de mídia de performance e tráfego pago da holding.",
        "project_type": "SERVICE",
        "lifecycle_status": "ATIVO",
        "is_active": True,
        "is_archived": False,
        "strategic_priority": "PADRAO",
    },
    {
        "id": "proj:pub-leads",
        "slug": "pub-leads",
        "display_name": "PUB Leads",
        "description": "Serviços e automações especializadas de enriquecimento de leads comerciais.",
        "project_type": "SERVICE",
        "lifecycle_status": "ATIVO",
        "is_active": True,
        "is_archived": False,
        "strategic_priority": "PADRAO",
    },
    {
        "id": "proj:pub-ia",
        "slug": "pub-ia",
        "display_name": "PUB IA",
        "description": "Hub e orquestrador de inteligência artificial generativa e preditiva.",
        "project_type": "INTERNAL_SYSTEM",
        "lifecycle_status": "ATIVO",
        "is_active": True,
        "is_archived": False,
        "strategic_priority": "ALTA",
    },
    {
        "id": "proj:pubet",
        "slug": "pubet",
        "display_name": "PUBET",
        "description": "Setor oficial de entretenimento, apostas reguladas e jogos digitais da holding.",
        "project_type": "PRODUCT",
        "lifecycle_status": "ATIVO",
        "is_active": True,
        "is_archived": False,
        "strategic_priority": "PADRAO",
    },
    {
        "id": "proj:pub-games-studio",
        "slug": "pub-games-studio",
        "display_name": "PUB Games Studio",
        "description": "Desenvolvimento de jogos independentes e gamificação corporativa.",
        "project_type": "LABORATORY",
        "lifecycle_status": "ATIVO",
        "is_active": True,
        "is_archived": False,
        "strategic_priority": "PADRAO",
    },
    {
        "id": "proj:pub-lancamentos",
        "slug": "pub-lancamentos",
        "display_name": "PUB Lançamentos",
        "description": "Infraestrutura e playbooks para lançamentos digitais em escala.",
        "project_type": "SERVICE",
        "lifecycle_status": "ATIVO",
        "is_active": True,
        "is_archived": False,
        "strategic_priority": "PADRAO",
    },
    {
        "id": "proj:pub-start",
        "slug": "pub-start",
        "display_name": "PUB Start",
        "description": "Incubadora e framework de bootstrap de novos negócios digitais da PUB Holding.",
        "project_type": "LABORATORY",
        "lifecycle_status": "ATIVO",
        "is_active": True,
        "is_archived": False,
        "strategic_priority": "PADRAO",
    },
    {
        "id": "proj:pub-rate-calculator",
        "slug": "pub-rate-calculator",
        "display_name": "PUB Rate Calculator",
        "description": "Calculadora de taxas operacionais e precificação estratégica de serviços.",
        "project_type": "INTERNAL_SYSTEM",
        "lifecycle_status": "ATIVO",
        "is_active": True,
        "is_archived": False,
        "strategic_priority": "PADRAO",
    },
    {
        "id": "proj:pub-ops-hub",
        "slug": "pub-ops-hub",
        "display_name": "PUB Ops Hub",
        "description": "Central integradora de operações e monitoramento da infraestrutura.",
        "project_type": "INFRASTRUCTURE",
        "lifecycle_status": "ATIVO",
        "is_active": True,
        "is_archived": False,
        "strategic_priority": "PADRAO",
    },
    {
        "id": "proj:pub-9router-cloud",
        "slug": "pub-9router-cloud",
        "display_name": "PUB 9router Cloud",
        "description": "Roteamento inteligente de requisições na nuvem e gateway corporativo.",
        "project_type": "INFRASTRUCTURE",
        "lifecycle_status": "ATIVO",
        "is_active": True,
        "is_archived": False,
        "strategic_priority": "PADRAO",
    },
    {
        "id": "proj:xp-audio-lab",
        "slug": "xp-audio-lab",
        "display_name": "XP Audio Lab",
        "description": "Estúdio oficial de produção de trilhas sonoras, sound design e engenharia de áudio.",
        "project_type": "LABORATORY",
        "lifecycle_status": "ATIVO",
        "is_active": True,
        "is_archived": False,
        "strategic_priority": "PADRAO",
    },
    {
        "id": "proj:buzios-de-cima",
        "slug": "buzios-de-cima",
        "display_name": "Búzios de Cima Drone",
        "description": "Captação aérea, mapeamento e mídia audiovisual com drones em Armação dos Búzios.",
        "project_type": "SERVICE",
        "lifecycle_status": "ATIVO",
        "is_active": True,
        "is_archived": False,
        "strategic_priority": "PADRAO",
    },
    {
        "id": "proj:eternize-seu-pinscher",
        "slug": "eternize-seu-pinscher",
        "display_name": "Eternize Seu Pinscher",
        "description": "Marca de eternização afetiva de animais através de modelagem e impressão 3D.",
        "project_type": "PRODUCT",
        "lifecycle_status": "ATIVO",
        "is_active": True,
        "is_archived": False,
        "strategic_priority": "PADRAO",
    },
    {
        "id": "proj:nortefishing",
        "slug": "nortefishing",
        "display_name": "Nortefishing",
        "description": "Operação náutica e pesca esportiva especializada.",
        "project_type": "SERVICE",
        "lifecycle_status": "ATIVO",
        "is_active": True,
        "is_archived": False,
        "strategic_priority": "PADRAO",
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
    },
]

# 2. Association Map: (project_id, repository_id, relationship_type, is_primary, association_status, source, confidence, reason)
ASSOCIATIONS = [
    # PUB E-Commerce (Multi-repo unificado)
    ("proj:pub-ecom", "pub-ecom", "PRIMARY", True, "CONFIRMED", "DOCUMENTATION", 1.000, "Monorepo principal do PUB E-Commerce"),
    ("proj:pub-ecom", "pub-ecom-catalog-worker", "WORKER", False, "CONFIRMED", "DOCUMENTATION", 1.000, "Documentado explicitamente: unificado em pub-ecom"),
    ("proj:pub-ecom", "pub-ecom-landing", "LANDING", False, "CONFIRMED", "DOCUMENTATION", 1.000, "Documentado explicitamente: unificado em pub-ecom"),
    ("proj:pub-ecom", "pubecomhub", "PLATFORM", False, "CONFIRMED", "DOCUMENTATION", 1.000, "Documentado explicitamente: unificado em pub-ecom"),

    # PUB Records (Gravadora e beats unificados)
    ("proj:pub-records", "pub-records", "PRIMARY", True, "CONFIRMED", "DOCUMENTATION", 1.000, "Repositório principal da gravadora PUB Records"),
    ("proj:pub-records", "pub-beats", "LEGACY", False, "CONFIRMED", "DOCUMENTATION", 1.000, "Documentado explicitamente: unificado em pub-records (beats/)"),

    # PUB Neural
    ("proj:pub-neural", "pub-neural", "PRIMARY", True, "CONFIRMED", "DOCUMENTATION", 1.000, "Repositório canônico do cérebro cognitivo PUB Neural"),
    ("proj:pub-neural", "neural-os", "BACKEND", False, "CONFIRMED", "RULE", 0.950, "Módulo de backend do sistema operacional cognitivo Neural"),

    # PUB Core (Holding portal, OS e plataforma web)
    ("proj:pub-core", "pub-core", "PRIMARY", True, "CONFIRMED", "RULE", 0.950, "Core repositório de plataforma"),
    ("proj:pub-core", "pubcore", "PRIMARY", False, "CONFIRMED", "DOCUMENTATION", 0.950, "Plataforma e sistema web principal da PUB Core"),
    ("proj:pub-core", "pub-core-os", "INFRASTRUCTURE", False, "CONFIRMED", "DOCUMENTATION", 0.950, "PUB Core OS - Sistema operacional institucional"),
    ("proj:pub-core", "pub-core-holding-portal", "LANDING", False, "CONFIRMED", "DOCUMENTATION", 0.950, "Portal institucional e comercial da holding"),
    ("proj:pub-core", "pub-co", "LANDING", False, "PROPOSED", "RULE", 0.850, "Portal institucional global de acesso à holding"),
    ("proj:pub-core", "pubcoreagencia.github.io", "LANDING", False, "PROPOSED", "RULE", 0.850, "Página institucional do GitHub Pages da agência"),
    ("proj:pub-core", "pub-agencia-landing", "LANDING", False, "PROPOSED", "RULE", 0.850, "Landing page oficial da agência PUB"),

    # PUB Dev Loop
    ("proj:pub-dev-loop", "pub-dev-loop", "PRIMARY", True, "CONFIRMED", "DOCUMENTATION", 1.000, "Infraestrutura principal de desenvolvimento em loop"),
    ("proj:pub-dev-loop", "pub-dev-loop-prototypes", "EXPERIMENT", False, "CONFIRMED", "DOCUMENTATION", 0.950, "Repositório de protótipos de sessões"),
    ("proj:pub-dev-loop", "pub-dev-loop-template", "DOCUMENTATION", False, "CONFIRMED", "DOCUMENTATION", 0.950, "Template para sessões de continuidade"),
    ("proj:pub-dev-loop", "pub-prototype", "EXPERIMENT", False, "PROPOSED", "RULE", 0.850, "Ambiente legado de prototipagem"),

    # PUB ACP
    ("proj:pub-acp", "pub-acp-standalone", "PRIMARY", True, "CONFIRMED", "RULE", 0.950, "Implementação autônoma do protocolo ACP"),
    ("proj:pub-acp", "pub-acp-lab", "EXPERIMENT", False, "CONFIRMED", "DOCUMENTATION", 0.950, "Laboratório experimental de orquestração com Antigravity"),

    # PUB Machine
    ("proj:pub-machine", "pub-machine", "PRIMARY", True, "PROPOSED", "RULE", 0.900, "Motor de prospecção autônoma v1"),
    ("proj:pub-machine", "pub-machine-2", "BACKEND", False, "PROPOSED", "RULE", 0.900, "Evolução autônoma de segunda geração"),
    ("proj:pub-machine", "pub-machine-saas", "PLATFORM", False, "PROPOSED", "RULE", 0.900, "Versão SaaS multi-tenant para clientes externos"),

    # PUB Films
    ("proj:pub-films", "pub-films", "PRIMARY", True, "PROPOSED", "RULE", 0.900, "Produção audiovisual cinematográfica principal"),
    ("proj:pub-films", "pub-films-landing", "LANDING", False, "PROPOSED", "RULE", 0.900, "Landing page cinematográfica"),

    # PUB 3D
    ("proj:pub-3d", "pub-3d", "PRIMARY", True, "PROPOSED", "RULE", 0.900, "Experiências e metaversos 3D WebGL"),
    ("proj:pub-3d", "pub3d-landing", "LANDING", False, "PROPOSED", "RULE", 0.900, "Landing page interativa de 3D"),

    # PUB Crypto
    ("proj:pub-crypto", "pub-crypto", "PRIMARY", True, "PROPOSED", "RULE", 0.850, "Gestão de tesouraria de criptoativos"),
    ("proj:pub-crypto", "ia-pubcrypto", "WORKER", False, "PROPOSED", "RULE", 0.850, "Agente preditivo de inteligência on-chain"),

    # PUB Food
    ("proj:pub-food", "pub-food", "PRIMARY", True, "PROPOSED", "RULE", 0.850, "Operação central de dark kitchens"),
    ("proj:pub-food", "pubfood-control-growth", "WORKER", False, "PROPOSED", "RULE", 0.800, "Painel de controle de crescimento do setor food"),

    # PUB Growth AI
    ("proj:pub-growth", "pubgrowthai", "PRIMARY", True, "PROPOSED", "RULE", 0.850, "Hub de automações de growth"),
    ("proj:pub-growth", "pubgrowth-ai-evolution", "EXPERIMENT", False, "PROPOSED", "RULE", 0.800, "Módulo evolutivo de growth com IA"),

    # PUB Scrapping
    ("proj:pub-scrapping", "pub-scrapping", "PRIMARY", True, "PROPOSED", "RULE", 0.850, "Engenharia central de scrapers"),
    ("proj:pub-scrapping", "pub-shopee-scraper", "WORKER", False, "PROPOSED", "RULE", 0.850, "Worker especializado de scraping Shopee"),

    # Projetos Únicos / Verticais Autônomas
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
        print("1. Inserting Holding Projects...")
        for p in HOLDING_PROJECTS:
            cur.execute("""
                INSERT INTO pub_neural.holding_projects (
                    id, slug, display_name, description, project_type,
                    lifecycle_status, is_active, is_archived, strategic_priority
                ) VALUES (
                    %(id)s, %(slug)s, %(display_name)s, %(description)s, %(project_type)s,
                    %(lifecycle_status)s, %(is_active)s, %(is_archived)s, %(strategic_priority)s
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
                    updated_at = CURRENT_TIMESTAMP;
            """, p)

        print("2. Inserting Project Repository Associations...")
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

        print("\n=== ONTOLOGY AUDIT REPORT ===")
        print(f"Total Holding Projects: {tot_proj}")
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
