"""
Overview and Activity aggregation service for PUB Neural Command Center V0.1.
Discovers observed projects strictly from verifiable observations and active knowledge nodes.
Calculates daily activity buckets and operational metrics without progress fabrication.
"""

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from console.backend.models import (
    CandidateReviewDTO,
    DailyActivityBucketDTO,
    ExecutiveSummaryDTO,
    GovernanceReviewResponseDTO,
    LatestSignalDTO,
    OverviewProjectDTO,
    OverviewResponseDTO,
    ProjectRegistryItemDTO,
    ProjectRegistryListDTO,
    serialize_val,
)
from console.backend.services.ontology_service import get_holding_projects


def get_projects_registry(
    cur,
    category: Optional[str] = None,
    lifecycle_status: Optional[str] = None,
    is_active: Optional[bool] = None,
) -> ProjectRegistryListDTO:
    """Returns all registered projects from pub_neural.project_registry."""
    query = """
        SELECT
            id, repository_full_name, repository_name, display_name,
            description, category, lifecycle_status, is_active,
            is_archived, is_private, monitoring_enabled, strategic_priority,
            github_url, created_at, updated_at, last_discovered_at
        FROM pub_neural.project_registry
        WHERE 1=1
    """
    params: List[Any] = []
    if category:
        query += " AND category = %s"
        params.append(category)
    if lifecycle_status:
        query += " AND lifecycle_status = %s"
        params.append(lifecycle_status)
    if is_active is not None:
        query += " AND is_active = %s"
        params.append(is_active)

    query += " ORDER BY is_active DESC, strategic_priority ASC, display_name ASC;"

    cur.execute(query, tuple(params))
    rows = cur.fetchall()

    projects = [
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
    return ProjectRegistryListDTO(total_count=len(projects), projects=projects)


def get_project_detail(cur, project_id: str) -> Optional[Dict[str, Any]]:
    """Returns single project registry metadata along with observations and knowledge summary."""
    cur.execute("""
        SELECT
            id, repository_full_name, repository_name, display_name,
            description, category, lifecycle_status, is_active,
            is_archived, is_private, monitoring_enabled, strategic_priority,
            github_url, created_at, updated_at, last_discovered_at
        FROM pub_neural.project_registry
        WHERE id = %s OR repository_name = %s;
    """, (project_id, project_id))
    row = cur.fetchone()
    if not row:
        return None

    pid = row["id"]
    # Observation stats
    cur.execute("""
        SELECT
            COUNT(DISTINCT repository) AS observed_repos,
            COUNT(*) AS total_observations,
            COUNT(*) FILTER (
                WHERE observed_at >= (timezone('UTC', CURRENT_DATE))
                  AND observed_at < (timezone('UTC', CURRENT_TIMESTAMP))
            ) AS today_observations,
            COUNT(*) FILTER (
                WHERE observed_at >= (timezone('UTC', CURRENT_TIMESTAMP) - INTERVAL '7 days')
                  AND observed_at < (timezone('UTC', CURRENT_TIMESTAMP))
            ) AS seven_day_observations,
            MAX(observed_at) AS last_observed_at
        FROM pub_neural.neural_repository_observations
        WHERE project_id = %s;
    """, (pid,))
    obs_row = cur.fetchone() or {}

    # Knowledge nodes stats
    cur.execute("""
        SELECT
            COUNT(*) AS total_nodes,
            COUNT(*) FILTER (WHERE promotion_state = 'CANDIDATE') AS candidate_nodes,
            COUNT(*) FILTER (WHERE promotion_state = 'ADOPTED') AS adopted_nodes,
            COUNT(*) FILTER (WHERE conflict_state = 'BLOCKED') AS blocked_nodes
        FROM pub_neural.neural_nodes
        WHERE project_id = %s AND is_active = TRUE;
    """, (pid,))
    node_row = cur.fetchone() or {}

    return {
        "registry": {
            "id": row["id"],
            "repository_full_name": row["repository_full_name"],
            "repository_name": row["repository_name"],
            "display_name": row["display_name"],
            "description": row.get("description"),
            "category": row["category"],
            "lifecycle_status": row["lifecycle_status"],
            "is_active": bool(row["is_active"]),
            "is_archived": bool(row["is_archived"]),
            "is_private": bool(row["is_private"]),
            "monitoring_enabled": bool(row["monitoring_enabled"]),
            "strategic_priority": row["strategic_priority"],
            "github_url": row.get("github_url"),
            "created_at": serialize_val(row["created_at"]),
            "updated_at": serialize_val(row["updated_at"]),
            "last_discovered_at": serialize_val(row["last_discovered_at"]),
        },
        "observations": {
            "observed_repositories": int(obs_row.get("observed_repos") or 0),
            "total_observations": int(obs_row.get("total_observations") or 0),
            "today_observations": int(obs_row.get("today_observations") or 0),
            "seven_day_observations": int(obs_row.get("seven_day_observations") or 0),
            "last_observed_at": serialize_val(obs_row.get("last_observed_at")),
        },
        "knowledge": {
            "active_nodes": int(node_row.get("total_nodes") or 0),
            "candidate_nodes": int(node_row.get("candidate_nodes") or 0),
            "adopted_nodes": int(node_row.get("adopted_nodes") or 0),
            "blocked_nodes": int(node_row.get("blocked_nodes") or 0),
        },
    }


def get_overview_data(cur, window_days: int = 14) -> OverviewResponseDTO:
    """
    Produces deterministic operational summary:
    - Database health: derived from PostgreSQL engine connectivity and execution responsiveness.
    - Projector health: derived strictly from `pub_neural.neural_projection_checkpoints`.
    - Discovers all projects primarily from `pub_neural.project_registry` with fallback to observations/nodes.
    - Preserves distinction between existence, activity, and knowledge without synthetic fabrication.
    """
    now_utc = datetime.now(timezone.utc)
    clamped_window = min(max(window_days, 1), 60)

    # 1. Evaluate Database Health (PostgreSQL engine connectivity and responsiveness)
    database_health = "UNKNOWN"
    try:
        cur.execute("SELECT version();")
        res = cur.fetchone()
        if res and res.get("version"):
            database_health = "HEALTHY"
    except Exception:
        database_health = "UNAVAILABLE"

    # 2. Evaluate Projector Health (Pipeline checkpoints)
    projector_health = "UNKNOWN"
    try:
        cur.execute("SAVEPOINT sp_overview_checkpoints;")
        cur.execute("""
            SELECT projector_name, status, error_detail
            FROM pub_neural.neural_projection_checkpoints;
        """)
        cp_rows = cur.fetchall()
        if cp_rows:
            has_error = any(r.get("status") == "ERROR" or r.get("error_detail") for r in cp_rows)
            has_degraded = any(r.get("status") == "DEGRADED" for r in cp_rows)
            if has_error:
                projector_health = "ERROR"
            elif has_degraded:
                projector_health = "DEGRADED"
            else:
                projector_health = "HEALTHY"
        cur.execute("RELEASE SAVEPOINT sp_overview_checkpoints;")
    except Exception:
        try:
            cur.execute("ROLLBACK TO SAVEPOINT sp_overview_checkpoints;")
        except Exception:
            pass

    # 3. Discover all projects: primarily from project_registry, complemented with observed/node projects
    registry_by_id: Dict[str, Dict[str, Any]] = {}
    try:
        cur.execute("SAVEPOINT sp_registry_lookup;")
        cur.execute("""
            SELECT
                id, repository_full_name, repository_name, display_name,
                description, category, lifecycle_status, is_active,
                is_archived, is_private, monitoring_enabled, strategic_priority,
                github_url
            FROM pub_neural.project_registry
            ORDER BY is_active DESC, strategic_priority ASC, display_name ASC;
        """)
        for r in (cur.fetchall() or []):
            if isinstance(r, dict) and "id" in r:
                registry_by_id[r["id"]] = r
        cur.execute("RELEASE SAVEPOINT sp_registry_lookup;")
    except Exception:
        try:
            cur.execute("ROLLBACK TO SAVEPOINT sp_registry_lookup;")
        except Exception:
            pass

    # Also discover observed projects that may not be in registry yet
    cur.execute("""
        SELECT DISTINCT project_id FROM pub_neural.neural_repository_observations WHERE project_id IS NOT NULL
        UNION
        SELECT DISTINCT project_id FROM pub_neural.neural_nodes WHERE project_id IS NOT NULL AND is_active = TRUE
        ORDER BY project_id ASC;
    """)
    extra_projects = [r.get("project_id") for r in (cur.fetchall() or []) if isinstance(r, dict) and r.get("project_id")]

    all_project_ids: List[str] = list(registry_by_id.keys())
    for pid in extra_projects:
        if pid not in registry_by_id and pid:
            all_project_ids.append(pid)

    # 4. Per-project observation statistics with strict UTC boundaries
    cur.execute("""
        SELECT
            project_id,
            COUNT(DISTINCT repository) AS observed_repos,
            COUNT(*) AS total_observations,
            COUNT(*) FILTER (
                WHERE observed_at >= (timezone('UTC', CURRENT_DATE))
                  AND observed_at < (timezone('UTC', CURRENT_TIMESTAMP))
            ) AS today_observations,
            COUNT(*) FILTER (
                WHERE observed_at >= (timezone('UTC', CURRENT_TIMESTAMP) - INTERVAL '7 days')
                  AND observed_at < (timezone('UTC', CURRENT_TIMESTAMP))
            ) AS seven_day_observations,
            MAX(observed_at) AS last_observed_at
        FROM pub_neural.neural_repository_observations
        WHERE project_id IS NOT NULL
        GROUP BY project_id;
    """)
    obs_rows = cur.fetchall()
    obs_by_project: Dict[str, Dict[str, Any]] = {
        r["project_id"]: r for r in obs_rows
    }

    # 5. Per-project active knowledge nodes and blocked nodes statistics
    cur.execute("""
        SELECT
            project_id,
            COUNT(*) AS total_active_nodes,
            COUNT(*) FILTER (WHERE conflict_state = 'BLOCKED') AS total_blocked_nodes
        FROM pub_neural.neural_nodes
        WHERE project_id IS NOT NULL AND is_active = TRUE
        GROUP BY project_id;
    """)
    node_rows = cur.fetchall() or []
    nodes_by_project: Dict[str, int] = {
        r["project_id"]: int(r.get("total_active_nodes", 0))
        for r in node_rows
        if isinstance(r, dict) and "project_id" in r
    }
    blocked_by_project: Dict[str, int] = {
        r["project_id"]: int(r.get("total_blocked_nodes") or 0)
        for r in node_rows
        if isinstance(r, dict) and "project_id" in r
    }

    # 6. Latest Operational Signal per project
    cur.execute("""
        WITH signals AS (
            SELECT
                project_id,
                'REPOSITORY_OBSERVED' AS signal_type,
                observed_at AS sig_timestamp,
                CASE
                    WHEN sha IS NOT NULL AND ref IS NOT NULL THEN 'Observed commit ' || substring(sha from 1 for 7) || ' on branch ' || ref
                    WHEN sha IS NOT NULL THEN 'Observed commit ' || substring(sha from 1 for 7)
                    WHEN ref IS NOT NULL THEN 'Observed branch ' || ref
                    ELSE 'Repository observation recorded'
                END AS summary,
                'neural_repository_observations' AS source,
                COALESCE(repository || '@' || sha, observation_id::text) AS locator,
                2 AS priority
            FROM pub_neural.neural_repository_observations
            WHERE project_id IS NOT NULL

            UNION ALL

            SELECT
                COALESCE(payload->>'projectId', payload->>'project_id') AS project_id,
                'TASK_EXPERIENCE_RECORDED' AS signal_type,
                recorded_at AS sig_timestamp,
                'Task ' || COALESCE(payload->>'taskId', payload->>'task_id', 'unknown') ||
                ' completed with status ' || COALESCE(payload->>'status', 'UNKNOWN') ||
                CASE
                    WHEN payload->>'objective' IS NOT NULL THEN ': ' || (payload->>'objective')
                    ELSE ''
                END AS summary,
                'neural_events' AS source,
                id::text AS locator,
                1 AS priority
            FROM pub_neural.neural_events
            WHERE event_type = 'TASK_EXPERIENCE_RECORDED'
              AND (payload->>'projectId' IS NOT NULL OR payload->>'project_id' IS NOT NULL)
        ),
        ranked_signals AS (
            SELECT
                project_id,
                signal_type,
                sig_timestamp,
                summary,
                source,
                locator,
                ROW_NUMBER() OVER (
                    PARTITION BY project_id
                    ORDER BY sig_timestamp DESC, priority ASC, locator ASC
                ) AS rank_num
            FROM signals
        )
        SELECT project_id, signal_type, sig_timestamp, summary, source, locator
        FROM ranked_signals
        WHERE rank_num = 1;
    """)
    signal_rows = cur.fetchall()
    signals_by_project: Dict[str, LatestSignalDTO] = {}
    for r in signal_rows:
        pid = r["project_id"]
        ts_val = serialize_val(r["sig_timestamp"])
        signals_by_project[pid] = LatestSignalDTO(
            type=r["signal_type"],
            timestamp=ts_val if ts_val else "",
            summary=r["summary"],
            source=r["source"],
            locator=r["locator"],
        )

    # 7. Build Project DTOs
    projects: List[OverviewProjectDTO] = []
    total_obs_7d = 0

    for pid in all_project_ids:
        obs_data = obs_by_project.get(pid, {})
        last_obs = obs_data.get("last_observed_at")
        reg_info = registry_by_id.get(pid, {})

        obs_count = int(obs_data.get("total_observations") or 0)
        act_7d = int(obs_data.get("seven_day_observations") or 0)
        total_obs_7d += act_7d

        # Determine friendly project_state
        if reg_info.get("is_archived"):
            p_state = "ARQUIVADO"
        elif obs_count > 0:
            p_state = "ATIVO_OBSERVADO"
        else:
            p_state = "SEM_OBSERVACOES"

        projects.append(
            OverviewProjectDTO(
                project_id=pid,
                observed_repository_count=int(obs_data.get("observed_repos") or 0),
                observation_count=obs_count,
                activity_today=int(obs_data.get("today_observations") or 0),
                activity_7d=act_7d,
                last_observation_at=serialize_val(last_obs) if last_obs else None,
                active_node_count=nodes_by_project.get(pid, 0),
                project_state=p_state,
                blocked_nodes_count=blocked_by_project.get(pid, 0),
                latest_signal=signals_by_project.get(pid),
                display_name=reg_info.get("display_name") or pid,
                description=reg_info.get("description") or "",
                category=reg_info.get("category") or "OPERACIONAL",
                lifecycle_status=reg_info.get("lifecycle_status") or ("ARQUIVADO" if reg_info.get("is_archived") else "ATIVO"),
                is_active=bool(reg_info.get("is_active", True)),
                is_archived=bool(reg_info.get("is_archived", False)),
                monitoring_enabled=bool(reg_info.get("monitoring_enabled", True)),
                github_url=reg_info.get("github_url"),
            )
        )

    # Sort projects: active first, then highest 7d activity, then by display_name
    projects.sort(key=lambda p: (not p.is_active, p.is_archived, -p.activity_7d, p.display_name or p.project_id))

    # 8. Calendar activity window for observed projects
    # We only include projects with observations in the daily heatmap table to avoid empty rows of 60 items
    observed_pids = [p.project_id for p in projects if p.observation_count > 0]
    daily_buckets: List[DailyActivityBucketDTO] = []

    if observed_pids:
        cur.execute("""
            SELECT
                TO_CHAR(d.day, 'YYYY-MM-DD') AS day,
                p.project_id,
                COALESCE(COUNT(o.observation_id), 0) AS observed_count
            FROM generate_series(
                timezone('UTC', CURRENT_DATE) - ((%s - 1) * INTERVAL '1 day'),
                timezone('UTC', CURRENT_DATE),
                INTERVAL '1 day'
            ) AS d(day)
            CROSS JOIN (
                SELECT DISTINCT project_id FROM pub_neural.neural_repository_observations WHERE project_id IS NOT NULL
            ) AS p(project_id)
            LEFT JOIN pub_neural.neural_repository_observations o
                ON o.project_id = p.project_id
               AND o.observed_at >= d.day
               AND o.observed_at < d.day + INTERVAL '1 day'
            GROUP BY d.day, p.project_id
            ORDER BY day ASC, p.project_id ASC;
        """, (clamped_window,))
        daily_rows = cur.fetchall()
        daily_buckets = [
            DailyActivityBucketDTO(
                day=r["day"],
                project_id=r["project_id"],
                observed_count=int(r["observed_count"]),
            )
            for r in daily_rows
        ]

    # 9. Aggregate Holding Projects & Executive Summary
    holding_projects_dto = None
    total_holding_projects = 0
    total_repositories = 0
    multi_repo_projects_count = 0
    unclassified_repositories_count = 0
    confirmed_associations_count = 0
    proposed_associations_count = 0

    try:
        cur.execute("SAVEPOINT sp_holding_projects;")
        hp_list = get_holding_projects(cur)
        holding_projects_dto = hp_list.projects
        total_holding_projects = hp_list.total_projects
        multi_repo_projects_count = sum(1 for hp in hp_list.projects if hp.repositories_count > 1)

        cur.execute("SELECT COUNT(*) AS total_repos FROM pub_neural.project_registry;")
        total_repositories = int((cur.fetchone() or {}).get("total_repos", 0))

        cur.execute("""
            SELECT
                COUNT(*) FILTER (WHERE association_status = 'CONFIRMED') AS confirmed_count,
                COUNT(*) FILTER (WHERE association_status = 'PROPOSED') AS proposed_count
            FROM pub_neural.project_repositories;
        """)
        assoc_counts = cur.fetchone() or {}
        confirmed_associations_count = int(assoc_counts.get("confirmed_count") or 0)
        proposed_associations_count = int(assoc_counts.get("proposed_count") or 0)

        cur.execute("""
            SELECT COUNT(*) AS unclassified_count
            FROM pub_neural.project_registry reg
            LEFT JOIN pub_neural.project_repositories pr ON reg.id = pr.repository_id
            WHERE pr.repository_id IS NULL;
        """)
        unclassified_repositories_count = int((cur.fetchone() or {}).get("unclassified_count", 0))
        cur.execute("RELEASE SAVEPOINT sp_holding_projects;")
    except Exception:
        try:
            cur.execute("ROLLBACK TO SAVEPOINT sp_holding_projects;")
        except Exception:
            pass

    if total_holding_projects == 0 and len(projects) > 0:
        total_holding_projects = len(projects)
    if total_repositories == 0 and len(projects) > 0:
        total_repositories = len(projects)

    cur.execute("""
        SELECT
            COUNT(*) FILTER (WHERE promotion_state = 'CANDIDATE' AND is_active = TRUE) AS candidate_count,
            COUNT(*) FILTER (WHERE promotion_state = 'ADOPTED' AND is_active = TRUE) AS adopted_count
        FROM pub_neural.neural_nodes;
    """)
    gov_stats = cur.fetchone() or {}

    cur.execute("""
        SELECT COUNT(*) AS today_events
        FROM pub_neural.neural_events
        WHERE recorded_at >= timezone('UTC', CURRENT_DATE)
          AND recorded_at < timezone('UTC', CURRENT_TIMESTAMP);
    """)
    ev_today = (cur.fetchone() or {}).get("today_events", 0)

    active_projects = sum(1 for p in projects if p.is_active and not p.is_archived)
    monitored_repos = sum(1 for p in projects if p.monitoring_enabled)

    exec_summary = ExecutiveSummaryDTO(
        total_holding_projects=total_holding_projects,
        total_repositories=total_repositories,
        multi_repo_projects_count=multi_repo_projects_count,
        unclassified_repositories_count=unclassified_repositories_count,
        confirmed_associations_count=confirmed_associations_count,
        proposed_associations_count=proposed_associations_count,
        active_projects=active_projects,
        monitored_repositories=monitored_repos,
        recent_observations_7d=total_obs_7d,
        events_today=int(ev_today),
        candidate_knowledge_count=int(gov_stats.get("candidate_count") or 0),
        adopted_knowledge_count=int(gov_stats.get("adopted_count") or 0),
        neural_health="SAUDAVEL" if database_health == "HEALTHY" and projector_health in ("HEALTHY", "UNKNOWN") else "DEGRADADO",
    )

    return OverviewResponseDTO(
        generated_at=now_utc.isoformat(),
        window_days=clamped_window,
        database_health=database_health,
        projector_health=projector_health,
        projects=projects,
        daily_activity=daily_buckets,
        executive_summary=exec_summary,
        holding_projects=holding_projects_dto,
    )


def get_governance_review_data(cur) -> GovernanceReviewResponseDTO:
    """
    Retrieves candidate knowledge awaiting formal governance review.
    Factual and non-evaluative:
    - Lists active nodes with promotion_state = 'CANDIDATE'.
    - Links to originating event, proposing actor, and provenance evidence.
    - Zero synthetic scoring or progress rankings.
    """
    now_utc = datetime.now(timezone.utc)
    cur.execute("""
        SELECT
            n.id,
            n.entity_type,
            n.title,
            n.summary,
            n.content,
            n.promotion_state,
            n.promotion_reason,
            n.conflict_state,
            n.scope,
            n.project_id,
            n.trust_zone,
            n.originating_event_id,
            n.created_at,
            e.actor_id AS proposed_by_actor_id,
            e.actor_role AS proposed_by_actor_role,
            e.event_type AS originating_event_type,
            parent_exp.target_id AS derived_from_experience_id,
            (SELECT COUNT(*) FROM pub_neural.neural_evidence ev WHERE ev.node_id = n.id) AS evidence_count
        FROM pub_neural.neural_nodes n
        LEFT JOIN pub_neural.neural_events e ON n.originating_event_id = e.id
        LEFT JOIN pub_neural.neural_edges parent_exp
            ON n.id = parent_exp.source_id AND parent_exp.relation_type = 'DERIVED_FROM'
        WHERE n.promotion_state = 'CANDIDATE' AND n.is_active = TRUE
        ORDER BY n.created_at ASC;
    """)
    rows = cur.fetchall()

    candidates: List[CandidateReviewDTO] = []
    for r in rows:
        created_val = serialize_val(r["created_at"])
        candidates.append(
            CandidateReviewDTO(
                id=r["id"],
                entity_type=r["entity_type"],
                title=r["title"],
                summary=r.get("summary"),
                content=r.get("content"),
                promotion_state=r["promotion_state"],
                promotion_reason=r.get("promotion_reason"),
                conflict_state=r["conflict_state"],
                scope=r["scope"],
                project_id=r.get("project_id"),
                trust_zone=r["trust_zone"],
                originating_event_id=str(r["originating_event_id"]),
                originating_event_type=r.get("originating_event_type"),
                proposed_by_actor_id=r.get("proposed_by_actor_id"),
                proposed_by_actor_role=r.get("proposed_by_actor_role"),
                derived_from_experience_id=r.get("derived_from_experience_id"),
                created_at=created_val if created_val else "",
                evidence_count=int(r.get("evidence_count") or 0),
            )
        )

    return GovernanceReviewResponseDTO(
        generated_at=now_utc.isoformat(),
        candidates_count=len(candidates),
        candidates=candidates,
    )
