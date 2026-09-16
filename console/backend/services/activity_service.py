"""
Overview and Activity aggregation service for PUB Neural Command Center V0.1.
Discovers observed projects strictly from verifiable observations and active knowledge nodes.
Calculates daily activity buckets and operational metrics without progress fabrication.
"""

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from console.backend.models import (
    DailyActivityBucketDTO,
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

    # 5. Per-project active knowledge nodes statistics (is_active = TRUE)
    cur.execute("""
        SELECT
            project_id,
            COUNT(*) AS total_active_nodes
        FROM pub_neural.neural_nodes
        WHERE project_id IS NOT NULL AND is_active = TRUE
        GROUP BY project_id;
    """)
    node_rows = cur.fetchall()
    nodes_by_project: Dict[str, int] = {
        r["project_id"]: int(r["total_active_nodes"]) for r in node_rows
    }

    # 6. Build Project DTOs
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
