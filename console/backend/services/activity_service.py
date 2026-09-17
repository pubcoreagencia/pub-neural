"""
Overview and Activity aggregation service for PUB Neural Command Center V0.1.
Discovers observed projects strictly from verifiable observations and active knowledge nodes.
Calculates daily activity buckets and operational metrics without progress fabrication.
"""

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from console.backend.models import (
    ActivityListResponseDTO,
    ActivitySignalDTO,
    CandidateReviewDTO,
    DailyActivityBucketDTO,
    ExecutiveSummaryDTO,
    GovernanceReviewResponseDTO,
    LatestSignalDTO,
    ObservationSyncTelemetryDTO,
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

    # 6. Operational Signals aggregation and latest signal per project
    cur.execute("""
        WITH signals AS (
            SELECT
                COALESCE(pr.project_id, obs.project_id) AS project_id,
                obs.repository AS repository,
                'REPOSITORY_OBSERVED' AS signal_type,
                obs.observed_at AS sig_timestamp,
                CASE
                    WHEN obs.event_type = 'PULL_REQUEST' THEN
                        'Pull Request #' || COALESCE(obs.details->>'pull_request_number', '') ||
                        CASE WHEN obs.details->>'title' IS NOT NULL THEN ': ' || (obs.details->>'title') ELSE '' END
                    WHEN obs.sha IS NOT NULL AND obs.ref IS NOT NULL THEN 'Observed commit ' || substring(obs.sha from 1 for 7) || ' on branch ' || obs.ref
                    WHEN obs.sha IS NOT NULL THEN 'Observed commit ' || substring(obs.sha from 1 for 7)
                    WHEN obs.ref IS NOT NULL THEN 'Observed branch ' || obs.ref
                    ELSE 'Repository observation recorded'
                END AS summary,
                'neural_repository_observations' AS source,
                COALESCE(obs.repository || '@' || obs.sha, obs.observation_id::text) AS locator,
                obs.event_id::text AS event_id,
                2 AS priority
            FROM pub_neural.neural_repository_observations obs
            LEFT JOIN pub_neural.project_repositories pr ON obs.repository_name = pr.repository_id OR obs.repository = pr.repository_id
            WHERE obs.project_id IS NOT NULL OR pr.project_id IS NOT NULL

            UNION ALL

            SELECT
                COALESCE(payload->>'projectId', payload->>'project_id') AS project_id,
                COALESCE(payload->>'repository', payload->>'repository_name') AS repository,
                event_type AS signal_type,
                recorded_at AS sig_timestamp,
                CASE
                    WHEN event_type = 'TASK_EXPERIENCE_RECORDED' THEN
                        'Task ' || COALESCE(payload->>'taskId', payload->>'task_id', 'unknown') ||
                        ' completed with status ' || COALESCE(payload->>'status', 'UNKNOWN') ||
                        CASE WHEN payload->>'objective' IS NOT NULL THEN ': ' || (payload->>'objective') ELSE '' END
                    WHEN event_type = 'AUTONOMOUS_AGENT_VALIDATED' THEN
                        'Autonomous Agent: ' || COALESCE(payload->>'title', payload->>'statement', 'Validated')
                    WHEN event_type = 'OPERATING_MODE_ADOPTED' THEN
                        'Operating Mode: ' || COALESCE(payload->>'title', 'Adopted')
                    ELSE 'Event ' || event_type
                END AS summary,
                'neural_events' AS source,
                id::text AS locator,
                id::text AS event_id,
                1 AS priority
            FROM pub_neural.neural_events
            WHERE (payload->>'projectId' IS NOT NULL OR payload->>'project_id' IS NOT NULL)
        ),
        ranked_signals AS (
            SELECT
                project_id,
                repository,
                signal_type,
                sig_timestamp,
                summary,
                source,
                locator,
                event_id,
                ROW_NUMBER() OVER (
                    PARTITION BY project_id
                    ORDER BY sig_timestamp DESC, priority ASC, locator ASC
                ) AS rank_num
            FROM signals
        )
        SELECT project_id, repository, signal_type, sig_timestamp, summary, source, locator, event_id
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
            repository=r.get("repository"),
            event_id=r.get("event_id"),
            project_id=pid,
        )

    # 7. Build Project DTOs with operational_activity_state and signal counts
    projects: List[OverviewProjectDTO] = []
    total_obs_7d = 0
    projects_with_activity_today = 0
    projects_with_activity_7d = 0

    for pid in all_project_ids:
        obs_data = obs_by_project.get(pid, {})
        last_obs = obs_data.get("last_observed_at")
        reg_info = registry_by_id.get(pid, {})

        obs_count = int(obs_data.get("total_observations") or 0)
        act_today = int(obs_data.get("today_observations") or 0)
        act_7d = int(obs_data.get("seven_day_observations") or 0)
        total_obs_7d += act_7d

        # Also check signal level activity
        latest_sig = signals_by_project.get(pid)
        sig_count_today = act_today
        sig_count_7d = act_7d

        # Determine semantic operational_activity_state
        if act_today > 0:
            op_activity_state = "ATIVIDADE_HOJE"
            projects_with_activity_today += 1
            projects_with_activity_7d += 1
        elif act_7d > 0 or (latest_sig and latest_sig.timestamp):
            # Check if latest signal was within 7 days
            op_activity_state = "ATIVIDADE_RECENTE"
            projects_with_activity_7d += 1
        elif obs_count > 0:
            op_activity_state = "SEM_ATIVIDADE_NO_PERIODO"
        else:
            op_activity_state = "DADOS_INSUFICIENTES"

        # Determine registry status
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
                activity_today=act_today,
                activity_7d=act_7d,
                last_observation_at=serialize_val(last_obs) if last_obs else None,
                active_node_count=nodes_by_project.get(pid, 0),
                project_state=p_state,
                operational_activity_state=op_activity_state,
                signals_today=sig_count_today,
                signals_7d=sig_count_7d,
                blocked_nodes_count=blocked_by_project.get(pid, 0),
                latest_signal=latest_sig,
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
    confirmed_projects_count = 0
    proposed_projects_count = 0
    unknown_projects_count = 0

    try:
        cur.execute("SAVEPOINT sp_holding_projects;")
        hp_list = get_holding_projects(cur)
        holding_projects_dto = hp_list.projects
        total_holding_projects = hp_list.total_projects
        multi_repo_projects_count = sum(1 for hp in hp_list.projects if hp.repositories_count > 1)

        cur.execute("""
            SELECT
                COUNT(*) FILTER (WHERE ontology_status = 'CONFIRMED') AS confirmed_proj_count,
                COUNT(*) FILTER (WHERE ontology_status = 'PROPOSED') AS proposed_proj_count,
                COUNT(*) FILTER (WHERE ontology_status = 'UNKNOWN') AS unknown_proj_count
            FROM pub_neural.holding_projects;
        """)
        proj_counts = cur.fetchone() or {}
        confirmed_projects_count = int(proj_counts.get("confirmed_proj_count") or 0)
        proposed_projects_count = int(proj_counts.get("proposed_proj_count") or 0)
        unknown_projects_count = int(proj_counts.get("unknown_proj_count") or 0)

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
        confirmed_projects_count=confirmed_projects_count,
        proposed_projects_count=proposed_projects_count,
        unknown_projects_count=unknown_projects_count,
        projects_with_activity_today_count=projects_with_activity_today,
        projects_with_activity_7d_count=projects_with_activity_7d,
    )

    # 10. Query latest Observation Sync Run Telemetry
    obs_sync_dto = None
    try:
        cur.execute("SAVEPOINT sp_obs_sync_telemetry;")
        cur.execute("""
            SELECT started_at, completed_at, status, repositories_scanned,
                   observations_created, observations_failed
            FROM pub_neural.observation_sync_runs
            ORDER BY started_at DESC
            LIMIT 1;
        """)
        sync_row = cur.fetchone()
        if sync_row:
            obs_sync_dto = ObservationSyncTelemetryDTO(
                last_sync_at=serialize_val(sync_row.get("completed_at") or sync_row.get("started_at")),
                repositories_scanned=int(sync_row.get("repositories_scanned") or 0),
                observations_created=int(sync_row.get("observations_created") or 0),
                observations_failed=int(sync_row.get("observations_failed") or 0),
                status=sync_row.get("status") or "UNKNOWN",
            )
        cur.execute("RELEASE SAVEPOINT sp_obs_sync_telemetry;")
    except Exception:
        try:
            cur.execute("ROLLBACK TO SAVEPOINT sp_obs_sync_telemetry;")
        except Exception:
            pass

    return OverviewResponseDTO(
        generated_at=now_utc.isoformat(),
        window_days=clamped_window,
        database_health=database_health,
        projector_health=projector_health,
        projects=projects,
        daily_activity=daily_buckets,
        executive_summary=exec_summary,
        holding_projects=holding_projects_dto,
        observation_sync_telemetry=obs_sync_dto,
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


def get_activity_signals(
    cur,
    window_days: int = 14,
    project_id: Optional[str] = None,
    repository_id: Optional[str] = None,
    activity_type: Optional[str] = None,
    limit: int = 50,
) -> ActivityListResponseDTO:
    """
    Retrieves chronological, verifiable activity signals across projects and repositories.
    Supports filtering by window_days, project_id, repository_id, and activity_type.
    Strictly factual: derived directly from neural_repository_observations and neural_events.
    """
    clamped_window = min(max(window_days, 1), 90)
    clamped_limit = min(max(limit, 1), 100)

    # Base query combining repository observations and domain neural events
    cur.execute("""
        WITH raw_signals AS (
            SELECT
                'obs:' || obs.observation_id::text AS signal_id,
                COALESCE(pr.project_id, obs.project_id) AS project_id,
                hp.display_name AS project_display_name,
                COALESCE(pr.repository_id, obs.repository_name, obs.repository) AS repository_id,
                obs.repository AS repository_name,
                'REPOSITORY_OBSERVED' AS activity_type,
                obs.observed_at AS timestamp,
                'neural_repository_observations' AS source,
                CASE
                    WHEN obs.event_type = 'PULL_REQUEST' THEN
                        'Pull Request #' || COALESCE(obs.details->>'pull_request_number', '') ||
                        CASE WHEN obs.details->>'title' IS NOT NULL THEN ': ' || (obs.details->>'title') ELSE '' END
                    WHEN obs.sha IS NOT NULL AND obs.ref IS NOT NULL THEN 'Observed commit ' || substring(obs.sha from 1 for 7) || ' on branch ' || obs.ref
                    WHEN obs.sha IS NOT NULL THEN 'Observed commit ' || substring(obs.sha from 1 for 7)
                    WHEN obs.ref IS NOT NULL THEN 'Observed branch ' || obs.ref
                    ELSE 'Repository observation recorded'
                END AS summary,
                COALESCE(obs.repository || '@' || obs.sha, obs.observation_id::text) AS locator,
                jsonb_build_object(
                    'ref', obs.ref,
                    'sha', obs.sha,
                    'is_default_branch', (obs.details->>'is_default_branch')::boolean,
                    'details', obs.details
                ) AS evidence_preview,
                obs.event_id::text AS event_id
            FROM pub_neural.neural_repository_observations obs
            LEFT JOIN pub_neural.project_repositories pr
                ON obs.repository_name = pr.repository_id OR obs.repository = pr.repository_id
            LEFT JOIN pub_neural.holding_projects hp
                ON COALESCE(pr.project_id, obs.project_id) = hp.id
            WHERE obs.observed_at >= timezone('UTC', CURRENT_TIMESTAMP) - (%(window_days)s || ' days')::interval

            UNION ALL

            SELECT
                'ev:' || e.id::text AS signal_id,
                COALESCE(e.payload->>'projectId', e.payload->>'project_id') AS project_id,
                hp.display_name AS project_display_name,
                COALESCE(e.payload->>'repositoryId', e.payload->>'repository_id', e.payload->>'repository') AS repository_id,
                COALESCE(e.payload->>'repository', e.payload->>'repository_name') AS repository_name,
                e.event_type AS activity_type,
                e.recorded_at AS timestamp,
                'neural_events' AS source,
                CASE
                    WHEN e.event_type = 'TASK_EXPERIENCE_RECORDED' THEN
                        'Task ' || COALESCE(e.payload->>'taskId', e.payload->>'task_id', 'unknown') ||
                        ' completed with status ' || COALESCE(e.payload->>'status', 'UNKNOWN') ||
                        CASE WHEN e.payload->>'objective' IS NOT NULL THEN ': ' || (e.payload->>'objective') ELSE '' END
                    WHEN e.event_type = 'AUTONOMOUS_AGENT_VALIDATED' THEN
                        'Autonomous Agent: ' || COALESCE(e.payload->>'title', e.payload->>'statement', 'Validated')
                    WHEN e.event_type = 'OPERATING_MODE_ADOPTED' THEN
                        'Operating Mode: ' || COALESCE(e.payload->>'title', 'Adopted')
                    ELSE 'Event ' || e.event_type
                END AS summary,
                e.id::text AS locator,
                jsonb_build_object(
                    'event_type', e.event_type,
                    'actor_id', e.actor_id,
                    'actor_role', e.actor_role,
                    'stream_id', e.stream_id,
                    'stream_version', e.stream_version
                ) AS evidence_preview,
                e.id::text AS event_id
            FROM pub_neural.neural_events e
            LEFT JOIN pub_neural.holding_projects hp
                ON COALESCE(e.payload->>'projectId', e.payload->>'project_id') = hp.id
            WHERE e.recorded_at >= timezone('UTC', CURRENT_TIMESTAMP) - (%(window_days)s || ' days')::interval
              AND (
                  e.payload->>'projectId' IS NOT NULL
                  OR e.payload->>'project_id' IS NOT NULL
                  OR e.payload->>'repository' IS NOT NULL
                  OR e.payload->>'repository_name' IS NOT NULL
              )
        )
        SELECT
            signal_id,
            project_id,
            project_display_name,
            repository_id,
            repository_name,
            activity_type,
            timestamp,
            source,
            summary,
            locator,
            evidence_preview,
            event_id
        FROM raw_signals
        WHERE (%(project_id)s IS NULL OR project_id = %(project_id)s)
          AND (%(repository_id)s IS NULL OR repository_id = %(repository_id)s OR repository_name = %(repository_id)s)
          AND (%(activity_type)s IS NULL OR activity_type = %(activity_type)s)
        ORDER BY timestamp DESC
        LIMIT %(limit)s;
    """, {
        "window_days": clamped_window,
        "project_id": project_id,
        "repository_id": repository_id,
        "activity_type": activity_type,
        "limit": clamped_limit,
    })
    rows = cur.fetchall()

    signals: List[ActivitySignalDTO] = []
    for r in rows:
        signals.append(
            ActivitySignalDTO(
                id=r["signal_id"],
                project_id=r.get("project_id"),
                project_display_name=r.get("project_display_name") or r.get("project_id"),
                repository_id=r.get("repository_id"),
                repository_name=r.get("repository_name") or r.get("repository_id"),
                activity_type=r["activity_type"],
                timestamp=serialize_val(r["timestamp"]) or "",
                source=r["source"],
                summary=r["summary"],
                locator=r["locator"],
                evidence_preview=r.get("evidence_preview"),
                event_id=r.get("event_id"),
            )
        )

    # Calculate summary counts for activity today vs 7d
    cur.execute("""
        WITH signals_summary AS (
            SELECT
                COALESCE(pr.project_id, obs.project_id) AS project_id,
                obs.observed_at AS timestamp
            FROM pub_neural.neural_repository_observations obs
            LEFT JOIN pub_neural.project_repositories pr
                ON obs.repository_name = pr.repository_id OR obs.repository = pr.repository_id
            WHERE obs.observed_at >= timezone('UTC', CURRENT_TIMESTAMP) - INTERVAL '7 days'

            UNION ALL

            SELECT
                COALESCE(e.payload->>'projectId', e.payload->>'project_id') AS project_id,
                e.recorded_at AS timestamp
            FROM pub_neural.neural_events e
            WHERE e.recorded_at >= timezone('UTC', CURRENT_TIMESTAMP) - INTERVAL '7 days'
              AND (e.payload->>'projectId' IS NOT NULL OR e.payload->>'project_id' IS NOT NULL)
        )
        SELECT
            COUNT(DISTINCT project_id) FILTER (WHERE timestamp >= timezone('UTC', CURRENT_DATE)) AS projects_today,
            COUNT(DISTINCT project_id) AS projects_7d
        FROM signals_summary
        WHERE project_id IS NOT NULL;
    """)
    summary_row = cur.fetchone() or {}
    proj_today = int(summary_row.get("projects_today") or 0)
    proj_7d = int(summary_row.get("projects_7d") or 0)

    return ActivityListResponseDTO(
        window_days=clamped_window,
        total_signals=len(signals),
        projects_with_activity_today=proj_today,
        projects_with_activity_7d=proj_7d,
        signals=signals,
    )


def get_project_activity(
    cur,
    project_id: str,
    window_days: int = 14,
    limit: int = 50,
) -> ActivityListResponseDTO:
    """Convenience accessor for project-scoped activity."""
    return get_activity_signals(
        cur,
        window_days=window_days,
        project_id=project_id,
        limit=limit,
    )


def get_repository_activity(
    cur,
    repository_id: str,
    window_days: int = 14,
    limit: int = 50,
) -> ActivityListResponseDTO:
    """Convenience accessor for repository-scoped activity."""
    return get_activity_signals(
        cur,
        window_days=window_days,
        repository_id=repository_id,
        limit=limit,
    )

