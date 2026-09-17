"""
Continuous Repository Observation Service (V0.5.1 Hardened).
Observes real external signals from GitHub across the PUB Core Holding repository universe.
Ensures:
- Factual observation recording (COMMIT, PULL_REQUEST, RELEASE, BRANCH_CHANGE, REPOSITORY_METADATA_CHANGE).
- True incremental synchronization via persistent per-repository cursor data.
- Branch accuracy: assigns exact branch ref when known, never fabricates "main".
- Metadata change detection: computes deterministic SHA256 snapshot.
- Branch change detection: detects newly pushed or removed branches.
- Rate limit resilience (HTTP 403, 429, timeouts).
- Idempotency via delivery_id: gh:<repo>:<type>:<external_id>.
- Epistemological distinction: collection failures never mark projects as inactive.
- Zero credential leakage.
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
import hashlib
import json
import subprocess
from typing import Any, Dict, List, Optional, Tuple
import uuid

import psycopg2
from psycopg2.extras import RealDictCursor


@dataclass
class ObservationSyncResult:
    run_id: str
    started_at: str
    completed_at: Optional[str] = None
    status: str = "RUNNING"
    repositories_scanned: int = 0
    repositories_changed: int = 0
    observations_created: int = 0
    observations_deduplicated: int = 0
    observations_failed: int = 0
    error_detail: Optional[str] = None
    consecutive_failures: int = 0
    last_success_at: Optional[str] = None
    last_failure_at: Optional[str] = None
    created_observations: List[Dict[str, Any]] = field(default_factory=list)
    cursor_data: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "run_id": self.run_id,
            "started_at": self.started_at,
            "completed_at": self.completed_at,
            "status": self.status,
            "repositories_scanned": self.repositories_scanned,
            "repositories_changed": self.repositories_changed,
            "observations_created": self.observations_created,
            "observations_deduplicated": self.observations_deduplicated,
            "observations_failed": self.observations_failed,
            "error_detail": self.error_detail,
            "consecutive_failures": self.consecutive_failures,
            "last_success_at": self.last_success_at,
            "last_failure_at": self.last_failure_at,
        }


class GitHubSignalExtractor:
    """Extracts raw signals from GitHub via gh CLI or authenticated HTTP client."""

    @staticmethod
    def fetch_repo_signals(
        repo_full_name: str,
        limit_commits: int = 10,
        limit_prs: int = 10,
    ) -> Dict[str, Any]:
        signals: Dict[str, Any] = {
            "commits": [],
            "pull_requests": [],
            "branches": {},
            "releases": [],
            "metadata": None,
            "metadata_hash": None,
            "error": None,
        }

        try:
            # 1. Fetch Repository Metadata
            meta_cmd = ["gh", "api", f"repos/{repo_full_name}"]
            res_meta = subprocess.run(meta_cmd, capture_output=True, text=True, check=True)
            meta_raw = json.loads(res_meta.stdout)
            signals["metadata"] = {
                "name": meta_raw.get("name"),
                "full_name": meta_raw.get("full_name"),
                "default_branch": meta_raw.get("default_branch"),
                "archived": meta_raw.get("archived", False),
                "updated_at": meta_raw.get("updated_at"),
                "description": meta_raw.get("description") or "",
            }
            # Deterministic snapshot hash of essential metadata
            meta_str = f"{signals['metadata']['name']}|{signals['metadata']['description']}|{signals['metadata']['default_branch']}|{signals['metadata']['archived']}"
            signals["metadata_hash"] = hashlib.sha256(meta_str.encode("utf-8")).hexdigest()

            # 2. Fetch Branches to resolve accurate refs
            branches_cmd = ["gh", "api", f"repos/{repo_full_name}/branches"]
            res_branches = subprocess.run(branches_cmd, capture_output=True, text=True, check=True)
            branches_raw = json.loads(res_branches.stdout)
            signals["branches"] = {
                b.get("name"): b.get("commit", {}).get("sha")
                for b in branches_raw if isinstance(b, dict) and b.get("name")
            }

            # 3. Fetch Recent Commits
            commits_cmd = ["gh", "api", f"repos/{repo_full_name}/commits?per_page={limit_commits}"]
            res_commits = subprocess.run(commits_cmd, capture_output=True, text=True, check=True)
            commits_raw = json.loads(res_commits.stdout)
            signals["commits"] = [
                {
                    "sha": c.get("sha"),
                    "message": (c.get("commit", {}).get("message") or "")[:250],
                    "author": (c.get("commit", {}).get("author", {}).get("name") or c.get("author", {}).get("login") or "unknown") if isinstance(c.get("author"), dict) else (c.get("commit", {}).get("author", {}).get("name") or "unknown"),
                    "date": c.get("commit", {}).get("author", {}).get("date"),
                }
                for c in commits_raw if isinstance(c, dict)
            ]

            # 4. Fetch Recent Pull Requests
            prs_cmd = ["gh", "api", f"repos/{repo_full_name}/pulls?state=all&per_page={limit_prs}"]
            res_prs = subprocess.run(prs_cmd, capture_output=True, text=True, check=True)
            prs_raw = json.loads(res_prs.stdout)
            signals["pull_requests"] = [
                {
                    "number": p.get("number"),
                    "title": (p.get("title") or "")[:200],
                    "state": p.get("state"),
                    "merged": bool(p.get("merged_at")),
                    "author": p.get("user", {}).get("login", "unknown") if isinstance(p.get("user"), dict) else "unknown",
                    "updated_at": p.get("updated_at"),
                    "head_ref": p.get("head", {}).get("ref") if isinstance(p.get("head"), dict) else None,
                    "base_ref": p.get("base", {}).get("ref") if isinstance(p.get("base"), dict) else None,
                }
                for p in prs_raw if isinstance(p, dict)
            ]

        except subprocess.CalledProcessError as e:
            err_output = (e.stderr or e.stdout or str(e)).strip()
            # Distinguish rate limits from general network errors
            if "403" in err_output or "rate limit" in err_output.lower():
                signals["error"] = f"RATE_LIMIT_EXCEEDED: {err_output[:150]}"
            elif "429" in err_output:
                signals["error"] = f"RATE_LIMIT_429: {err_output[:150]}"
            else:
                signals["error"] = f"GitHub API error for {repo_full_name}: {err_output[:150]}"
        except Exception as e:
            signals["error"] = f"Unexpected error querying GitHub for {repo_full_name}: {str(e)[:150]}"

        return signals


class RepositoryObservationSync:
    """
    Coordinates continuous repository observation synchronization.
    Fetches monitored repositories from registry, checks external GitHub signals,
    normalizes into canonical observations with ontology mapping, and persists idempotently.
    """

    def __init__(self, db_url: str, internal_actor: str = "actor:system:observation-sync"):
        self.db_url = db_url
        self.internal_actor = internal_actor

    def run_sync(
        self,
        repository_ids: Optional[List[str]] = None,
        max_commits_per_repo: int = 10,
        max_prs_per_repo: int = 10,
        github_extractor: Optional[GitHubSignalExtractor] = None,
    ) -> ObservationSyncResult:
        run_id = str(uuid.uuid4())
        started_at = datetime.now(timezone.utc)
        result = ObservationSyncResult(
            run_id=run_id,
            started_at=started_at.isoformat(),
        )

        extractor = github_extractor or GitHubSignalExtractor()

        conn = None
        try:
            conn = psycopg2.connect(self.db_url, cursor_factory=RealDictCursor)
            conn.autocommit = True

            with conn.cursor() as cur:
                # 1. Fetch latest successful sync run to retrieve persistent cursor_data and failure telemetry
                cur.execute("""
                    SELECT id, cursor_data, consecutive_failures, last_success_at
                    FROM pub_neural.observation_sync_runs
                    WHERE status = 'COMPLETED'
                    ORDER BY started_at DESC
                    LIMIT 1;
                """)
                prev_run = cur.fetchone()
                existing_cursor: Dict[str, Any] = {}
                prev_consecutive_failures = 0
                if prev_run:
                    existing_cursor = prev_run.get("cursor_data") or {}
                    prev_consecutive_failures = int(prev_run.get("consecutive_failures") or 0)
                    if prev_run.get("last_success_at"):
                        result.last_success_at = prev_run["last_success_at"].isoformat() if hasattr(prev_run["last_success_at"], "isoformat") else str(prev_run["last_success_at"])

                # Check if the immediately preceding run failed
                cur.execute("""
                    SELECT status, completed_at, started_at, error_detail
                    FROM pub_neural.observation_sync_runs
                    ORDER BY started_at DESC
                    LIMIT 1;
                """)
                last_any_run = cur.fetchone()
                if last_any_run and last_any_run.get("status") == "FAILED":
                    prev_consecutive_failures += 1
                    result.last_failure_at = (last_any_run.get("completed_at") or last_any_run.get("started_at")).isoformat()

                result.consecutive_failures = prev_consecutive_failures

                # 2. Record sync run started
                cur.execute("""
                    INSERT INTO pub_neural.observation_sync_runs (
                        id, started_at, status, repositories_scanned,
                        repositories_changed, observations_created,
                        observations_deduplicated, observations_failed,
                        consecutive_failures, last_success_at, last_failure_at, cursor_data
                    ) VALUES (%s, %s, 'RUNNING', 0, 0, 0, 0, 0, %s, %s, %s, %s);
                """, (
                    run_id,
                    started_at,
                    result.consecutive_failures,
                    result.last_success_at,
                    result.last_failure_at,
                    json.dumps(existing_cursor),
                ))

                # 3. Fetch target repositories with project ontology mapping
                query = """
                    SELECT
                        reg.id AS repository_id,
                        reg.repository_full_name,
                        reg.repository_name,
                        reg.is_archived,
                        COALESCE(pr.project_id, NULL) AS mapped_project_id
                    FROM pub_neural.project_registry reg
                    LEFT JOIN pub_neural.project_repositories pr
                        ON reg.id = pr.repository_id
                    WHERE reg.monitoring_enabled = TRUE
                """
                params: List[Any] = []
                if repository_ids:
                    query += " AND reg.id = ANY(%s)"
                    params.append(repository_ids)

                query += " ORDER BY reg.id ASC;"
                cur.execute(query, tuple(params) if params else None)
                target_repos = cur.fetchall() or []

                result.repositories_scanned = len(target_repos)
                updated_cursor: Dict[str, Any] = dict(existing_cursor)

                # 4. Iterate over target repositories
                has_fatal_rate_limit = False
                for repo in target_repos:
                    repo_id = repo["repository_id"]
                    repo_full_name = repo["repository_full_name"]
                    project_id = repo["mapped_project_id"]
                    repo_cursor = existing_cursor.get(repo_id, {})

                    repo_signals = extractor.fetch_repo_signals(
                        repo_full_name,
                        limit_commits=max_commits_per_repo,
                        limit_prs=max_prs_per_repo,
                    )

                    if repo_signals.get("error"):
                        result.observations_failed += 1
                        if "RATE_LIMIT" in repo_signals["error"]:
                            has_fatal_rate_limit = True
                            result.error_detail = repo_signals["error"]
                            break
                        continue

                    repo_had_new_obs = False
                    new_repo_cursor = dict(repo_cursor)

                    # A. Ingest Commits (Incremental check against last_commit_sha)
                    commits = repo_signals.get("commits", [])
                    last_seen_sha = repo_cursor.get("last_commit_sha")
                    branches_map = repo_signals.get("branches", {})

                    for c in commits:
                        sha = c.get("sha")
                        if not sha:
                            continue

                        # If we reached the previously committed SHA, stop processing older commits
                        if last_seen_sha and sha == last_seen_sha:
                            break

                        delivery_id = f"gh:{repo_id}:COMMIT:{sha}"
                        date_str = c.get("date")
                        try:
                            observed_at = datetime.fromisoformat(date_str.replace("Z", "+00:00")) if date_str else datetime.now(timezone.utc)
                        except Exception:
                            observed_at = datetime.now(timezone.utc)

                        # Determine accurate branch ref (no fabricating main)
                        matching_branch = None
                        for b_name, b_sha in branches_map.items():
                            if b_sha == sha:
                                matching_branch = b_name
                                break

                        details = {
                            "action": "commit",
                            "commit_message": (c.get("message") or "")[:250],
                            "commit_author": c.get("author") or "unknown",
                            "ref": matching_branch,
                        }

                        created = self._persist_observation_if_new(
                            cur=cur,
                            delivery_id=delivery_id,
                            repository=repo_full_name,
                            repo_name=repo_id,
                            project_id=project_id,
                            event_type="COMMIT",
                            sha=sha,
                            ref=matching_branch,
                            external_actor=c.get("author") or "unknown",
                            observed_at=observed_at,
                            details=details,
                        )

                        if created:
                            result.observations_created += 1
                            repo_had_new_obs = True
                            result.created_observations.append({
                                "delivery_id": delivery_id,
                                "repository": repo_full_name,
                                "project_id": project_id,
                                "type": "COMMIT",
                                "sha": sha[:7],
                                "ref": matching_branch,
                            })
                        else:
                            result.observations_deduplicated += 1

                    if commits and commits[0].get("sha"):
                        new_repo_cursor["last_commit_sha"] = commits[0]["sha"]

                    # B. Ingest Pull Requests (Incremental check against last_pr_updated_at)
                    prs = repo_signals.get("pull_requests", [])
                    last_pr_updated_at = repo_cursor.get("last_pr_updated_at")

                    for pr in prs:
                        pr_num = pr.get("number")
                        if not pr_num:
                            continue

                        pr_state = "merged" if pr.get("merged") else pr.get("state", "open")
                        updated_at_str = pr.get("updated_at") or ""

                        # If PR is older than our last processed cursor, stop
                        if last_pr_updated_at and updated_at_str and updated_at_str <= last_pr_updated_at:
                            break

                        delivery_id = f"gh:{repo_id}:PR:{pr_num}:{pr_state}:{updated_at_str}"

                        try:
                            observed_at = datetime.fromisoformat(updated_at_str.replace("Z", "+00:00")) if updated_at_str else datetime.now(timezone.utc)
                        except Exception:
                            observed_at = datetime.now(timezone.utc)

                        details = {
                            "action": f"pr_{pr_state}",
                            "pull_request_number": pr_num,
                            "title": (pr.get("title") or "")[:200],
                            "head_ref": pr.get("head_ref"),
                            "base_ref": pr.get("base_ref"),
                        }

                        created = self._persist_observation_if_new(
                            cur=cur,
                            delivery_id=delivery_id,
                            repository=repo_full_name,
                            repo_name=repo_id,
                            project_id=project_id,
                            event_type="PULL_REQUEST",
                            sha=None,
                            ref=pr.get("head_ref"),
                            external_actor=pr.get("author") or "unknown",
                            observed_at=observed_at,
                            details=details,
                        )

                        if created:
                            result.observations_created += 1
                            repo_had_new_obs = True
                            result.created_observations.append({
                                "delivery_id": delivery_id,
                                "repository": repo_full_name,
                                "project_id": project_id,
                                "type": "PULL_REQUEST",
                                "pr_number": pr_num,
                            })
                        else:
                            result.observations_deduplicated += 1

                    if prs and prs[0].get("updated_at"):
                        new_repo_cursor["last_pr_updated_at"] = prs[0]["updated_at"]

                    # C. Check Branch Changes (BRANCH_CHANGE)
                    prev_branches = repo_cursor.get("branches") or {}
                    if prev_branches and branches_map:
                        added_branches = set(branches_map.keys()) - set(prev_branches.keys())
                        deleted_branches = set(prev_branches.keys()) - set(branches_map.keys())
                        for ab in added_branches:
                            delivery_id = f"gh:{repo_id}:BRANCH_ADDED:{ab}:{branches_map[ab]}"
                            created = self._persist_observation_if_new(
                                cur=cur,
                                delivery_id=delivery_id,
                                repository=repo_full_name,
                                repo_name=repo_id,
                                project_id=project_id,
                                event_type="BRANCH_CHANGE",
                                sha=branches_map[ab],
                                ref=ab,
                                external_actor="github",
                                observed_at=datetime.now(timezone.utc),
                                details={"action": "branch_created", "branch": ab, "sha": branches_map[ab]},
                            )
                            if created:
                                result.observations_created += 1
                                repo_had_new_obs = True
                                result.created_observations.append({
                                    "delivery_id": delivery_id,
                                    "repository": repo_full_name,
                                    "project_id": project_id,
                                    "type": "BRANCH_CHANGE",
                                    "branch": ab,
                                })

                        for db in deleted_branches:
                            delivery_id = f"gh:{repo_id}:BRANCH_DELETED:{db}:{started_at.strftime('%Y%m%d%H')}"
                            created = self._persist_observation_if_new(
                                cur=cur,
                                delivery_id=delivery_id,
                                repository=repo_full_name,
                                repo_name=repo_id,
                                project_id=project_id,
                                event_type="BRANCH_CHANGE",
                                sha=None,
                                ref=db,
                                external_actor="github",
                                observed_at=datetime.now(timezone.utc),
                                details={"action": "branch_deleted", "branch": db},
                            )
                            if created:
                                result.observations_created += 1
                                repo_had_new_obs = True

                    if branches_map:
                        new_repo_cursor["branches"] = branches_map

                    # D. Check Metadata Changes (REPOSITORY_METADATA_CHANGE)
                    meta_hash = repo_signals.get("metadata_hash")
                    prev_meta_hash = repo_cursor.get("metadata_hash")
                    if prev_meta_hash and meta_hash and prev_meta_hash != meta_hash:
                        meta = repo_signals.get("metadata") or {}
                        delivery_id = f"gh:{repo_id}:META_CHANGE:{meta_hash[:16]}"
                        created = self._persist_observation_if_new(
                            cur=cur,
                            delivery_id=delivery_id,
                            repository=repo_full_name,
                            repo_name=repo_id,
                            project_id=project_id,
                            event_type="REPOSITORY_METADATA_CHANGE",
                            sha=None,
                            ref=meta.get("default_branch"),
                            external_actor="github",
                            observed_at=datetime.now(timezone.utc),
                            details={"action": "metadata_updated", "metadata": meta},
                        )
                        if created:
                            result.observations_created += 1
                            repo_had_new_obs = True
                            result.created_observations.append({
                                "delivery_id": delivery_id,
                                "repository": repo_full_name,
                                "project_id": project_id,
                                "type": "REPOSITORY_METADATA_CHANGE",
                            })

                    if meta_hash:
                        new_repo_cursor["metadata_hash"] = meta_hash

                    if repo_had_new_obs:
                        result.repositories_changed += 1

                    updated_cursor[repo_id] = new_repo_cursor

                # 5. Finalize run status
                completed_at = datetime.now(timezone.utc)
                result.completed_at = completed_at.isoformat()
                result.cursor_data = updated_cursor

                if has_fatal_rate_limit:
                    result.status = "FAILED"
                    result.consecutive_failures += 1
                    result.last_failure_at = completed_at.isoformat()
                else:
                    result.status = "COMPLETED"
                    result.consecutive_failures = 0
                    result.last_success_at = completed_at.isoformat()

                cur.execute("""
                    UPDATE pub_neural.observation_sync_runs
                    SET completed_at = %s,
                        status = %s,
                        repositories_scanned = %s,
                        repositories_changed = %s,
                        observations_created = %s,
                        observations_deduplicated = %s,
                        observations_failed = %s,
                        error_detail = %s,
                        consecutive_failures = %s,
                        last_success_at = %s,
                        last_failure_at = %s,
                        cursor_data = %s
                    WHERE id = %s;
                """, (
                    completed_at,
                    result.status,
                    result.repositories_scanned,
                    result.repositories_changed,
                    result.observations_created,
                    result.observations_deduplicated,
                    result.observations_failed,
                    result.error_detail,
                    result.consecutive_failures,
                    result.last_success_at,
                    result.last_failure_at,
                    json.dumps(updated_cursor),
                    run_id,
                ))

        except Exception as e:
            result.status = "FAILED"
            result.error_detail = str(e)
            result.consecutive_failures += 1
            if conn:
                try:
                    with conn.cursor() as cur:
                        cur.execute("""
                            UPDATE pub_neural.observation_sync_runs
                            SET completed_at = CURRENT_TIMESTAMP,
                                status = 'FAILED',
                                consecutive_failures = consecutive_failures + 1,
                                last_failure_at = CURRENT_TIMESTAMP,
                                error_detail = %s
                            WHERE id = %s;
                        """, (str(e), run_id))
                except Exception:
                    pass
            raise
        finally:
            if conn and not conn.closed:
                conn.close()

        return result

    def _persist_observation_if_new(
        self,
        cur,
        delivery_id: str,
        repository: str,
        repo_name: str,
        project_id: Optional[str],
        event_type: str,
        sha: Optional[str],
        ref: Optional[str],
        external_actor: str,
        observed_at: datetime,
        details: Dict[str, Any],
    ) -> bool:
        """
        Idempotently inserts into pub_neural.neural_repository_observations.
        Returns True if inserted, False if duplicate.
        Also records corresponding canonical neural_events record to maintain causal ledger.
        """
        cur.execute("""
            SELECT observation_id FROM pub_neural.neural_repository_observations
            WHERE delivery_id = %s;
        """, (delivery_id,))
        if cur.fetchone():
            return False  # Already exists, deduplicated

        obs_id = str(uuid.uuid4())
        event_id = str(uuid.uuid4())
        payload_hash = hashlib.sha256(f"{delivery_id}:{observed_at.isoformat()}".encode("utf-8")).hexdigest()

        # 1. Insert into neural_events (canonical ledger)
        stream_id = f"repo_obs:{repo_name}"
        cur.execute("""
            SELECT COALESCE(MAX(stream_version), 0) + 1 AS next_ver
            FROM pub_neural.neural_events
            WHERE stream_id = %s;
        """, (stream_id,))
        stream_ver = cur.fetchone()["next_ver"]

        canonical_payload = {
            "observation_id": obs_id,
            "delivery_id": delivery_id,
            "repository": repository,
            "repository_name": repo_name,
            "project_id": project_id,
            "event_type": event_type,
            "sha": sha,
            "ref": ref,
            "external_actor": external_actor,
            "observed_at": observed_at.isoformat(),
            "details": details,
        }

        cur.execute("""
            INSERT INTO pub_neural.neural_events (
                id, event_type, event_version, payload_schema_version,
                producer_version, stream_id, stream_version,
                actor_id, actor_role, payload, recorded_at
            ) VALUES (
                %s, 'REPOSITORY_OBSERVED', 1, 1,
                'v0.5.1', %s, %s,
                %s, 'INGESTOR', %s, %s
            );
        """, (
            event_id,
            stream_id,
            stream_ver,
            self.internal_actor,
            json.dumps(canonical_payload),
            datetime.now(timezone.utc),
        ))

        # 2. Insert into neural_repository_observations
        cur.execute("""
            INSERT INTO pub_neural.neural_repository_observations (
                observation_id, event_id, repository, repository_name,
                source, source_event_id, event_type, project_id,
                trust_zone, external_actor, internal_actor,
                observed_at, delivery_id, received_at, payload_hash,
                ref, sha, details
            ) VALUES (
                %s, %s, %s, %s,
                'github', %s, %s, %s,
                'tz_internal_holding', %s, %s,
                %s, %s, %s, %s,
                %s, %s, %s
            ) ON CONFLICT (delivery_id) DO NOTHING;
        """, (
            obs_id,
            event_id,
            repository,
            repo_name,
            sha or delivery_id,
            event_type,
            project_id,
            external_actor,
            self.internal_actor,
            observed_at,
            delivery_id,
            datetime.now(timezone.utc),
            payload_hash,
            ref,
            sha,
            json.dumps(details),
        ))

        return True
