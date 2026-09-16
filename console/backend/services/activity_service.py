"""
Overview and Activity aggregation service for PUB Neural Command Center V0.1.
Discovers observed projects strictly from verifiable observations and active knowledge nodes.
Calculates daily activity buckets and operational metrics without progress fabrication.
"""

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from console.backend.models import (
    DailyActivityBucketDTO,
    LatestSignalDTO,
    OverviewProjectDTO,
    OverviewResponseDTO,
    serialize_val,
)


def get_overview_data(cur, window_days: int = 14) -> OverviewResponseDTO:
    """
    Produces deterministic operational summary:
    - Database health: derived from PostgreSQL engine connectivity and execution responsiveness.
    - Projector health: derived strictly from `pub_neural.neural_projection_checkpoints`.
    - Observed projects discovered via `pub_neural.neural_repository_observations`
      and active `pub_neural.neural_nodes`.
    - Distinct semantic metrics:
        * observed_repository_count: count of distinct repositories observed
        * observation_count: total repository observations recorded
        * activity_today: observations recorded today in UTC [today_utc_start, current_timestamp_utc)
        * activity_7d: observations recorded in the last 7 completed/running 24h UTC intervals [now - 7d, now)
        * active_node_count: count of active knowledge nodes (is_active = TRUE)
        * blocked_nodes_count: count of active knowledge nodes with conflict_state = 'BLOCKED'
        * project_state: promotion_state if authoritative PROJECT node with originating_event by CEO/ADMIN exists, else 'UNKNOWN'
        * latest_signal: deterministic latest operational signal (REPOSITORY_OBSERVED vs TASK_EXPERIENCE_RECORDED)
    - Full calendar window for daily activity: exactly N UTC days guaranteed for every project.
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

    # 3. Discover all observed projects across repository observations and active knowledge nodes
    cur.execute("""
        SELECT DISTINCT project_id FROM pub_neural.neural_repository_observations WHERE project_id IS NOT NULL
        UNION
        SELECT DISTINCT project_id FROM pub_neural.neural_nodes WHERE project_id IS NOT NULL AND is_active = TRUE
        ORDER BY project_id ASC;
    """)
    project_rows = cur.fetchall()
    observed_project_ids: List[str] = [r["project_id"] for r in project_rows if r.get("project_id")]

    # 4. Per-project observation statistics with strict UTC boundaries
    # today_observations: [today_utc_start, current_timestamp_utc)
    # seven_day_observations: [current_timestamp_utc - 7 days, current_timestamp_utc)
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
    node_rows = cur.fetchall()
    nodes_by_project: Dict[str, int] = {
        r["project_id"]: int(r["total_active_nodes"]) for r in node_rows
    }
    blocked_by_project: Dict[str, int] = {
        r["project_id"]: int(r.get("total_blocked_nodes") or 0) for r in node_rows
    }

    # 6. Project State: strictly 'UNKNOWN'
    # Semantic audit: No authoritative project lifecycle state or dedicated PROJECT node ID convention exists in the schema.
    # We strictly adhere to zero synthetic progress/state generation.
    project_states: Dict[str, str] = {}

    # 7. Latest Operational Signal per project (deterministic rank: REPOSITORY_OBSERVED vs TASK_EXPERIENCE_RECORDED)
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

    # 8. Build Project DTOs
    projects: List[OverviewProjectDTO] = []
    for pid in observed_project_ids:
        obs_data = obs_by_project.get(pid, {})
        last_obs = obs_data.get("last_observed_at")
        projects.append(
            OverviewProjectDTO(
                project_id=pid,
                observed_repository_count=int(obs_data.get("observed_repos") or 0),
                observation_count=int(obs_data.get("total_observations") or 0),
                activity_today=int(obs_data.get("today_observations") or 0),
                activity_7d=int(obs_data.get("seven_day_observations") or 0),
                last_observation_at=serialize_val(last_obs) if last_obs else None,
                active_node_count=nodes_by_project.get(pid, 0),
                project_state=project_states.get(pid, "UNKNOWN"),
                blocked_nodes_count=blocked_by_project.get(pid, 0),
                latest_signal=signals_by_project.get(pid),
            )
        )

    # 7. Generate strict calendar window of exactly N UTC days
    # Range: from (CURRENT_DATE - (window_days - 1)) to CURRENT_DATE (inclusive)
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
            UNION
            SELECT DISTINCT project_id FROM pub_neural.neural_nodes WHERE project_id IS NOT NULL AND is_active = TRUE
        ) AS p(project_id)
        LEFT JOIN pub_neural.neural_repository_observations o
            ON o.project_id = p.project_id
           AND o.observed_at >= d.day
           AND o.observed_at < d.day + INTERVAL '1 day'
        GROUP BY d.day, p.project_id
        ORDER BY day ASC, p.project_id ASC;
    """, (clamped_window,))
    daily_rows = cur.fetchall()

    daily_buckets: List[DailyActivityBucketDTO] = [
        DailyActivityBucketDTO(
            day=r["day"],
            project_id=r["project_id"],
            observed_count=int(r["observed_count"]),
        )
        for r in daily_rows
    ]

    return OverviewResponseDTO(
        generated_at=now_utc.isoformat(),
        window_days=clamped_window,
        database_health=database_health,
        projector_health=projector_health,
        projects=projects,
        daily_activity=daily_buckets,
    )
