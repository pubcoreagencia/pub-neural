"""
Project Ontology Service for PUB Neural Command Center (V0.2).
Implements the canonical Holding -> Project -> Repository hierarchy.
Ensures REPOSITÓRIO != PROJETO, with factual provenance tracking
(CONFIRMED vs PROPOSED vs UNCLASSIFIED).
"""

from typing import Any, Dict, List, Optional
from console.backend.models import (
    HoldingProjectItemDTO,
    HoldingProjectListDTO,
    ProjectRegistryItemDTO,
    ProjectRegistryListDTO,
    ProjectRepositoryAssociationDTO,
    serialize_val,
)


def get_holding_projects(
    cur,
    project_type: Optional[str] = None,
    lifecycle_status: Optional[str] = None,
    is_active: Optional[bool] = None,
    ontology_status: Optional[str] = None,
) -> HoldingProjectListDTO:
    """
    Returns all holding projects from pub_neural.holding_projects
    joined with their repository associations and factual metrics.
    """
    query = """
        SELECT
            hp.id,
            hp.slug,
            hp.display_name,
            hp.description,
            hp.project_type,
            hp.lifecycle_status,
            hp.is_active,
            hp.is_archived,
            hp.strategic_priority,
            hp.owner_scope,
            hp.ontology_status,
            hp.ontology_source,
            hp.ontology_confidence,
            hp.ontology_reason,
            hp.ontology_verified_at,
            hp.ontology_verified_by,
            hp.created_at,
            hp.updated_at,
            COUNT(pr.repository_id) AS repositories_count,
            COUNT(pr.repository_id) FILTER (WHERE pr.association_status = 'CONFIRMED') AS confirmed_repos,
            COUNT(pr.repository_id) FILTER (WHERE pr.association_status = 'PROPOSED') AS proposed_repos
        FROM pub_neural.holding_projects hp
        LEFT JOIN pub_neural.project_repositories pr ON hp.id = pr.project_id
        WHERE 1=1
    """
    params: List[Any] = []
    if project_type:
        query += " AND hp.project_type = %s"
        params.append(project_type)
    if lifecycle_status:
        query += " AND hp.lifecycle_status = %s"
        params.append(lifecycle_status)
    if is_active is not None:
        query += " AND hp.is_active = %s"
        params.append(is_active)
    if ontology_status:
        query += " AND hp.ontology_status = %s"
        params.append(ontology_status)

    query += """
        GROUP BY hp.id, hp.slug, hp.display_name, hp.description, hp.project_type,
                 hp.lifecycle_status, hp.is_active, hp.is_archived, hp.strategic_priority,
                 hp.owner_scope, hp.ontology_status, hp.ontology_source, hp.ontology_confidence,
                 hp.ontology_reason, hp.ontology_verified_at, hp.ontology_verified_by,
                 hp.created_at, hp.updated_at
        ORDER BY hp.is_active DESC, hp.strategic_priority ASC, hp.display_name ASC;
    """
    cur.execute(query, tuple(params))
    hp_rows = cur.fetchall() or []

    # Get all repository associations
    cur.execute("""
        SELECT
            pr.project_id,
            pr.repository_id,
            reg.repository_name,
            reg.display_name,
            reg.category,
            pr.relationship_type,
            pr.is_primary,
            pr.association_status,
            pr.classification_source,
            pr.classification_confidence,
            pr.classification_reason,
            pr.classified_at,
            pr.classified_by,
            reg.github_url
        FROM pub_neural.project_repositories pr
        JOIN pub_neural.project_registry reg ON pr.repository_id = reg.id
        ORDER BY pr.is_primary DESC, pr.association_status ASC, reg.display_name ASC;
    """)
    assoc_rows = cur.fetchall() or []
    assoc_by_project: Dict[str, List[ProjectRepositoryAssociationDTO]] = {}
    for ar in assoc_rows:
        pid = ar["project_id"]
        dto = ProjectRepositoryAssociationDTO(
            project_id=pid,
            repository_id=ar["repository_id"],
            repository_name=ar["repository_name"],
            display_name=ar["display_name"],
            category=ar["category"],
            relationship_type=ar["relationship_type"],
            is_primary=bool(ar["is_primary"]),
            association_status=ar["association_status"],
            classification_source=ar["classification_source"],
            classification_confidence=float(ar["classification_confidence"]),
            classification_reason=ar.get("classification_reason"),
            github_url=ar.get("github_url"),
            classified_at=serialize_val(ar.get("classified_at")),
            classified_by=ar.get("classified_by"),
        )
        assoc_by_project.setdefault(pid, []).append(dto)

    # Node count by project
    cur.execute("""
        SELECT project_id, COUNT(*) AS node_count
        FROM pub_neural.neural_nodes
        WHERE is_active = TRUE AND project_id IS NOT NULL
        GROUP BY project_id;
    """)
    nodes_by_project = {r["project_id"]: int(r["node_count"]) for r in (cur.fetchall() or [])}

    # 7d observations by project
    cur.execute("""
        SELECT project_id, COUNT(*) AS obs_7d
        FROM pub_neural.neural_repository_observations
        WHERE observed_at >= (timezone('UTC', CURRENT_TIMESTAMP) - INTERVAL '7 days')
          AND project_id IS NOT NULL
        GROUP BY project_id;
    """)
    obs_7d_by_project = {r["project_id"]: int(r["obs_7d"]) for r in (cur.fetchall() or [])}

    projects: List[HoldingProjectItemDTO] = []
    for r in hp_rows:
        pid = r["id"]
        slug = r["slug"]
        obs_7d = obs_7d_by_project.get(pid, 0) + obs_7d_by_project.get(slug, 0)
        node_cnt = nodes_by_project.get(pid, 0) + nodes_by_project.get(slug, 0)

        # Check repository level observations
        p_assocs = assoc_by_project.get(pid, [])
        for assoc in p_assocs:
            repo_clean = assoc.repository_name
            obs_7d += obs_7d_by_project.get(repo_clean, 0)
            node_cnt += nodes_by_project.get(repo_clean, 0)

        projects.append(
            HoldingProjectItemDTO(
                id=pid,
                slug=r["slug"],
                display_name=r["display_name"],
                description=r.get("description"),
                project_type=r["project_type"],
                lifecycle_status=r["lifecycle_status"],
                is_active=bool(r["is_active"]),
                is_archived=bool(r["is_archived"]),
                strategic_priority=r["strategic_priority"],
                owner_scope=r["owner_scope"],
                repositories_count=int(r.get("repositories_count") or 0),
                confirmed_repositories_count=int(r.get("confirmed_repos") or 0),
                proposed_repositories_count=int(r.get("proposed_repos") or 0),
                active_knowledge_nodes_count=node_cnt,
                recent_observations_7d=obs_7d,
                repositories=p_assocs,
                created_at=serialize_val(r["created_at"]) or "",
                updated_at=serialize_val(r["updated_at"]) or "",
                ontology_status=r.get("ontology_status") or "CONFIRMED",
                ontology_source=r.get("ontology_source") or "DOCS",
                ontology_confidence=float(r.get("ontology_confidence") or 1.0),
                ontology_reason=r.get("ontology_reason"),
                ontology_verified_at=serialize_val(r.get("ontology_verified_at")),
                ontology_verified_by=r.get("ontology_verified_by"),
            )
        )

    return HoldingProjectListDTO(total_projects=len(projects), projects=projects)


def get_holding_project_detail(cur, project_id: str) -> Optional[HoldingProjectItemDTO]:
    """Returns single holding project detail with full repository associations and governance metadata."""
    cur.execute("""
        SELECT
            hp.id,
            hp.slug,
            hp.display_name,
            hp.description,
            hp.project_type,
            hp.lifecycle_status,
            hp.is_active,
            hp.is_archived,
            hp.strategic_priority,
            hp.owner_scope,
            hp.ontology_status,
            hp.ontology_source,
            hp.ontology_confidence,
            hp.ontology_reason,
            hp.ontology_verified_at,
            hp.ontology_verified_by,
            hp.created_at,
            hp.updated_at,
            COUNT(pr.repository_id) AS repositories_count,
            COUNT(pr.repository_id) FILTER (WHERE pr.association_status = 'CONFIRMED') AS confirmed_repos,
            COUNT(pr.repository_id) FILTER (WHERE pr.association_status = 'PROPOSED') AS proposed_repos
        FROM pub_neural.holding_projects hp
        LEFT JOIN pub_neural.project_repositories pr ON hp.id = pr.project_id
        WHERE hp.id = %s OR hp.slug = %s
        GROUP BY hp.id, hp.slug, hp.display_name, hp.description, hp.project_type,
                 hp.lifecycle_status, hp.is_active, hp.is_archived, hp.strategic_priority,
                 hp.owner_scope, hp.ontology_status, hp.ontology_source, hp.ontology_confidence,
                 hp.ontology_reason, hp.ontology_verified_at, hp.ontology_verified_by,
                 hp.created_at, hp.updated_at;
    """, (project_id, project_id))
    r = cur.fetchone()
    if not r:
        return None

    pid = r["id"]
    cur.execute("""
        SELECT
            pr.project_id,
            pr.repository_id,
            reg.repository_name,
            reg.display_name,
            reg.category,
            pr.relationship_type,
            pr.is_primary,
            pr.association_status,
            pr.classification_source,
            pr.classification_confidence,
            pr.classification_reason,
            pr.classified_at,
            pr.classified_by,
            reg.github_url
        FROM pub_neural.project_repositories pr
        JOIN pub_neural.project_registry reg ON pr.repository_id = reg.id
        WHERE pr.project_id = %s
        ORDER BY pr.is_primary DESC, pr.association_status ASC, reg.display_name ASC;
    """, (pid,))
    assoc_rows = cur.fetchall() or []
    repositories = [
        ProjectRepositoryAssociationDTO(
            project_id=pid,
            repository_id=ar["repository_id"],
            repository_name=ar["repository_name"],
            display_name=ar["display_name"],
            category=ar["category"],
            relationship_type=ar["relationship_type"],
            is_primary=bool(ar["is_primary"]),
            association_status=ar["association_status"],
            classification_source=ar["classification_source"],
            classification_confidence=float(ar["classification_confidence"]),
            classification_reason=ar.get("classification_reason"),
            github_url=ar.get("github_url"),
            classified_at=serialize_val(ar.get("classified_at")),
            classified_by=ar.get("classified_by"),
        )
        for ar in assoc_rows
    ]

    return HoldingProjectItemDTO(
        id=pid,
        slug=r["slug"],
        display_name=r["display_name"],
        description=r.get("description"),
        project_type=r["project_type"],
        lifecycle_status=r["lifecycle_status"],
        is_active=bool(r["is_active"]),
        is_archived=bool(r["is_archived"]),
        strategic_priority=r["strategic_priority"],
        owner_scope=r["owner_scope"],
        repositories_count=int(r.get("repositories_count") or 0),
        confirmed_repositories_count=int(r.get("confirmed_repos") or 0),
        proposed_repositories_count=int(r.get("proposed_repos") or 0),
        active_knowledge_nodes_count=0,
        recent_observations_7d=0,
        repositories=repositories,
        created_at=serialize_val(r["created_at"]) or "",
        updated_at=serialize_val(r["updated_at"]) or "",
        ontology_status=r.get("ontology_status") or "CONFIRMED",
        ontology_source=r.get("ontology_source") or "DOCS",
        ontology_confidence=float(r.get("ontology_confidence") or 1.0),
        ontology_reason=r.get("ontology_reason"),
        ontology_verified_at=serialize_val(r.get("ontology_verified_at")),
        ontology_verified_by=r.get("ontology_verified_by"),
    )


def get_project_repositories(cur, project_id: str) -> List[ProjectRepositoryAssociationDTO]:
    """Returns repository associations for a given holding project."""
    cur.execute("""
        SELECT
            pr.project_id,
            pr.repository_id,
            reg.repository_name,
            reg.display_name,
            reg.category,
            pr.relationship_type,
            pr.is_primary,
            pr.association_status,
            pr.classification_source,
            pr.classification_confidence,
            pr.classification_reason,
            pr.classified_at,
            pr.classified_by,
            reg.github_url
        FROM pub_neural.project_repositories pr
        JOIN pub_neural.project_registry reg ON pr.repository_id = reg.id
        WHERE pr.project_id = %s
           OR pr.project_id = (SELECT id FROM pub_neural.holding_projects WHERE slug = %s LIMIT 1)
        ORDER BY pr.is_primary DESC, pr.association_status ASC, reg.display_name ASC;
    """, (project_id, project_id))
    rows = cur.fetchall() or []
    return [
        ProjectRepositoryAssociationDTO(
            project_id=r["project_id"],
            repository_id=r["repository_id"],
            repository_name=r["repository_name"],
            display_name=r["display_name"],
            category=r["category"],
            relationship_type=r["relationship_type"],
            is_primary=bool(r["is_primary"]),
            association_status=r["association_status"],
            classification_source=r["classification_source"],
            classification_confidence=float(r["classification_confidence"]),
            classification_reason=r.get("classification_reason"),
            github_url=r.get("github_url"),
            classified_at=serialize_val(r.get("classified_at")),
            classified_by=r.get("classified_by"),
        )
        for r in rows
    ]


def get_all_repositories(cur) -> List[Dict[str, Any]]:
    """
    Returns all 57 registered repositories with associated project information (if any).
    Preserves exact epistemological status (CONFIRMED, PROPOSED, or UNCLASSIFIED).
    """
    cur.execute("""
        SELECT
            reg.id AS repository_id,
            reg.repository_full_name,
            reg.repository_name,
            reg.display_name AS repository_display_name,
            reg.description,
            reg.category,
            reg.lifecycle_status,
            reg.is_active,
            reg.is_archived,
            reg.is_private,
            reg.monitoring_enabled,
            reg.strategic_priority,
            reg.github_url,
            reg.created_at,
            reg.updated_at,
            reg.last_discovered_at,
            pr.project_id,
            hp.slug AS project_slug,
            hp.display_name AS project_display_name,
            hp.project_type,
            hp.ontology_status AS project_ontology_status,
            pr.relationship_type,
            pr.is_primary,
            COALESCE(pr.association_status, 'UNCLASSIFIED') AS association_status,
            pr.classification_source,
            pr.classification_confidence,
            pr.classification_reason,
            pr.classified_at,
            pr.classified_by
        FROM pub_neural.project_registry reg
        LEFT JOIN pub_neural.project_repositories pr ON reg.id = pr.repository_id
        LEFT JOIN pub_neural.holding_projects hp ON pr.project_id = hp.id
        ORDER BY reg.is_active DESC, reg.strategic_priority ASC, reg.display_name ASC;
    """)
    rows = cur.fetchall() or []
    results = []
    for r in rows:
        results.append({
            "id": r["repository_id"],
            "repository_full_name": r["repository_full_name"],
            "repository_name": r["repository_name"],
            "display_name": r["repository_display_name"],
            "description": r.get("description"),
            "category": r["category"],
            "lifecycle_status": r["lifecycle_status"],
            "is_active": bool(r["is_active"]),
            "is_archived": bool(r["is_archived"]),
            "is_private": bool(r["is_private"]),
            "monitoring_enabled": bool(r["monitoring_enabled"]),
            "strategic_priority": r["strategic_priority"],
            "github_url": r.get("github_url"),
            "created_at": serialize_val(r["created_at"]) or "",
            "updated_at": serialize_val(r["updated_at"]) or "",
            "last_discovered_at": serialize_val(r["last_discovered_at"]) or "",
            "project": {
                "project_id": r["project_id"],
                "project_slug": r["project_slug"],
                "project_display_name": r["project_display_name"],
                "project_type": r["project_type"],
                "project_ontology_status": r["project_ontology_status"],
                "relationship_type": r.get("relationship_type"),
                "is_primary": bool(r.get("is_primary", False)),
                "association_status": r["association_status"],
                "classification_source": r.get("classification_source"),
                "classification_confidence": float(r["classification_confidence"]) if r.get("classification_confidence") is not None else 0.0,
                "classification_reason": r.get("classification_reason"),
                "classified_at": serialize_val(r.get("classified_at")),
                "classified_by": r.get("classified_by"),
            } if r.get("project_id") else None,
        })
    return results


def get_unclassified_repositories(cur) -> List[ProjectRegistryItemDTO]:
    """
    Returns repositories that have NO association with any holding project.
    Factual: No forced associations.
    """
    cur.execute("""
        SELECT
            reg.id,
            reg.repository_full_name,
            reg.repository_name,
            reg.display_name,
            reg.description,
            reg.category,
            reg.lifecycle_status,
            reg.is_active,
            reg.is_archived,
            reg.is_private,
            reg.monitoring_enabled,
            reg.strategic_priority,
            reg.github_url,
            reg.created_at,
            reg.updated_at,
            reg.last_discovered_at
        FROM pub_neural.project_registry reg
        LEFT JOIN pub_neural.project_repositories pr ON reg.id = pr.repository_id
        WHERE pr.repository_id IS NULL
        ORDER BY reg.display_name ASC;
    """)
    rows = cur.fetchall() or []
    return [
        ProjectRegistryItemDTO(
            id=r["id"],
            repository_full_name=r["repository_full_name"],
            repository_name=r["repository_name"],
            display_name=r["display_name"],
            description=r.get("description"),
            category=r["category"],
            lifecycle_status=r["lifecycle_status"],
            is_active=bool(r["is_active"]),
            is_archived=bool(r["is_archived"]),
            is_private=bool(r["is_private"]),
            monitoring_enabled=bool(r["monitoring_enabled"]),
            strategic_priority=r["strategic_priority"],
            github_url=r.get("github_url"),
            created_at=serialize_val(r["created_at"]) or "",
            updated_at=serialize_val(r["updated_at"]) or "",
            last_discovered_at=serialize_val(r["last_discovered_at"]) or "",
        )
        for r in rows
    ]


def get_governance_queues(cur) -> Dict[str, Any]:
    """
    Provides the 3 official governance queues for Project Ontology Governance V0.3:
    1. pending_projects: Projects awaiting confirmation (ontology_status = 'PROPOSED')
    2. pending_associations: Repository associations awaiting confirmation (association_status = 'PROPOSED')
    3. unclassified_repositories: Repositories with no holding project association
    """
    # 1. Pending projects
    cur.execute("""
        SELECT
            hp.id,
            hp.slug,
            hp.display_name,
            hp.description,
            hp.project_type,
            hp.lifecycle_status,
            hp.strategic_priority,
            hp.ontology_status,
            hp.ontology_source,
            hp.ontology_confidence,
            hp.ontology_reason,
            COUNT(pr.repository_id) AS repositories_count
        FROM pub_neural.holding_projects hp
        LEFT JOIN pub_neural.project_repositories pr ON hp.id = pr.project_id
        WHERE hp.ontology_status = 'PROPOSED'
        GROUP BY hp.id, hp.slug, hp.display_name, hp.description, hp.project_type,
                 hp.lifecycle_status, hp.strategic_priority, hp.ontology_status,
                 hp.ontology_source, hp.ontology_confidence, hp.ontology_reason
        ORDER BY hp.strategic_priority ASC, hp.display_name ASC;
    """)
    pending_projects_rows = cur.fetchall() or []
    pending_projects = [
        {
            "id": r["id"],
            "slug": r["slug"],
            "display_name": r["display_name"],
            "description": r.get("description"),
            "project_type": r["project_type"],
            "lifecycle_status": r["lifecycle_status"],
            "strategic_priority": r["strategic_priority"],
            "ontology_status": r["ontology_status"],
            "ontology_source": r["ontology_source"],
            "ontology_confidence": float(r["ontology_confidence"]),
            "ontology_reason": r.get("ontology_reason"),
            "repositories_count": int(r.get("repositories_count") or 0),
        }
        for r in pending_projects_rows
    ]

    # 2. Pending associations
    cur.execute("""
        SELECT
            pr.project_id,
            hp.display_name AS project_display_name,
            pr.repository_id,
            reg.repository_name,
            reg.display_name AS repository_display_name,
            pr.relationship_type,
            pr.is_primary,
            pr.association_status,
            pr.classification_source,
            pr.classification_confidence,
            pr.classification_reason,
            pr.classified_at,
            pr.classified_by
        FROM pub_neural.project_repositories pr
        JOIN pub_neural.holding_projects hp ON pr.project_id = hp.id
        JOIN pub_neural.project_registry reg ON pr.repository_id = reg.id
        WHERE pr.association_status = 'PROPOSED'
        ORDER BY pr.classification_confidence DESC, reg.display_name ASC;
    """)
    pending_assoc_rows = cur.fetchall() or []
    pending_associations = [
        {
            "project_id": r["project_id"],
            "project_display_name": r["project_display_name"],
            "repository_id": r["repository_id"],
            "repository_name": r["repository_name"],
            "repository_display_name": r["repository_display_name"],
            "relationship_type": r["relationship_type"],
            "is_primary": bool(r["is_primary"]),
            "association_status": r["association_status"],
            "classification_source": r["classification_source"],
            "classification_confidence": float(r["classification_confidence"]),
            "classification_reason": r.get("classification_reason"),
            "classified_at": serialize_val(r.get("classified_at")),
            "classified_by": r.get("classified_by"),
        }
        for r in pending_assoc_rows
    ]

    # 3. Unclassified repositories
    unclassified = get_unclassified_repositories(cur)

    return {
        "pending_projects_count": len(pending_projects),
        "pending_projects": pending_projects,
        "pending_associations_count": len(pending_associations),
        "pending_associations": pending_associations,
        "unclassified_repositories_count": len(unclassified),
        "unclassified_repositories": [u.to_dict() for u in unclassified],
    }
