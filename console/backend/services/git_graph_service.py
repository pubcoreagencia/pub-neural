"""
Git Graph Service for PUB Neural Console V0.
Provides canonical Git topology views, directory tree expansion, and object details
anchored in pubcoreagencia/pubcore@main.

Enforces:
- pubcoreagencia/pubcore@main as the sovereign source of truth for versioned code topology.
- Exclusion of secrets (.env, tokens, private keys) while preserving .env.example.
- Incremental Level of Detail (LOD) expansion (Repository -> Commits/Roots -> Dirs -> Files).
- Deterministic node and edge IDs.
- Strict mapping to canonical Postgres ENUMs:
    - REPOSITORY -> REPOSITORY
    - Directory -> CONCEPT
    - Documentation -> DOCUMENT
    - Source/Code -> SOURCE
    - Commit -> EVENT
"""

import json
import os
import re
import subprocess
import time
import urllib.request
import urllib.error
from typing import Any, Dict, List, Optional, Set, Tuple

from console.backend.models import (
    GraphEdgeDTO,
    GraphNodeDTO,
    GraphResponseDTO,
)

CANONICAL_REPO = "pubcoreagencia/pubcore"
DEFAULT_BRANCH = "main"

# Secret patterns to strictly exclude from graph ingestion and exploration
SECRET_PATTERNS = [
    re.compile(r"^\.env(\..+)?$", re.IGNORECASE),  # .env, .env.local, etc.
    re.compile(r".*\.pem$", re.IGNORECASE),
    re.compile(r".*\.key$", re.IGNORECASE),
    re.compile(r".*id_rsa.*", re.IGNORECASE),
    re.compile(r".*credentials.*", re.IGNORECASE),
]

DOC_EXTENSIONS = {".md", ".txt", ".rst", ".adoc"}

# In-memory tree cache with TTL (15 minutes)
_TREE_CACHE: Dict[str, Tuple[float, List[Dict[str, Any]], str]] = {}
CACHE_TTL_SECONDS = 900.0


def is_secret_file(path: str) -> bool:
    """Fail-closed secret detection: strictly block secrets, preserve .env.example."""
    basename = path.split("/")[-1]
    if basename == ".env.example":
        return False
    for pat in SECRET_PATTERNS:
        if pat.match(basename) or pat.match(path):
            return True
    return False


def get_github_token() -> Optional[str]:
    """Retrieve GitHub token from env or gh CLI."""
    token = os.getenv("GITHUB_TOKEN") or os.getenv("GH_TOKEN")
    if token and token.strip():
        return token.strip()
    try:
        proc = subprocess.run(
            ["gh", "auth", "token"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=5,
        )
        if proc.returncode == 0 and proc.stdout.strip():
            return proc.stdout.strip()
    except Exception:
        pass
    return None


def fetch_git_tree_remote(
    repo: str = CANONICAL_REPO,
    branch: str = DEFAULT_BRANCH,
) -> Tuple[List[Dict[str, Any]], str]:
    """
    Fetch recursive git tree for repo@branch from GitHub API.
    Returns (tree_items, root_commit_sha).
    """
    cache_key = f"{repo}@{branch}"
    now = time.time()
    if cache_key in _TREE_CACHE:
        cached_time, cached_tree, cached_sha = _TREE_CACHE[cache_key]
        if now - cached_time < CACHE_TTL_SECONDS:
            return cached_tree, cached_sha

    # 1. Try gh CLI first if available
    try:
        proc = subprocess.run(
            ["gh", "api", f"repos/{repo}/git/trees/{branch}?recursive=1"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=15,
        )
        if proc.returncode == 0:
            payload = json.loads(proc.stdout)
            tree = payload.get("tree", [])
            sha = payload.get("sha", "")
            _TREE_CACHE[cache_key] = (now, tree, sha)
            return tree, sha
    except Exception:
        pass

    # 2. Fallback to urllib with or without token
    url = f"https://api.github.com/repos/{repo}/git/trees/{branch}?recursive=1"
    headers = {
        "User-Agent": "PUB-Neural-GitGraph/1.0",
        "Accept": "application/vnd.github.v3+json",
    }
    token = get_github_token()
    if token:
        headers["Authorization"] = f"token {token}"

    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            tree = data.get("tree", [])
            sha = data.get("sha", "")
            _TREE_CACHE[cache_key] = (now, tree, sha)
            return tree, sha
    except Exception as e:
        # If cache exists even if expired, use as stale-while-revalidate fallback
        if cache_key in _TREE_CACHE:
            return _TREE_CACHE[cache_key][1], _TREE_CACHE[cache_key][2]
        raise RuntimeError(f"Failed to fetch Git tree for {repo}@{branch}: {e}") from e


def get_git_topology(
    repo: str = CANONICAL_REPO,
    branch: str = DEFAULT_BRANCH,
    base_path: str = "",
    depth: int = 1,
    limit: int = 100,
) -> GraphResponseDTO:
    """
    Build a bounded Git topology graph starting from base_path up to depth hops.
    LOD Principle:
    - Root of repo: `repo:{repo}`
    - Base path == "": Shows Root, Root Commit, and immediate children (depth=1: top-level dirs & files).
    - Expanding a directory expands only its immediate children.
    """
    tree, root_sha = fetch_git_tree_remote(repo, branch)

    # Clean base_path
    base_path = base_path.strip().strip("/")
    bounded_depth = max(1, min(depth, 3))
    bounded_limit = max(10, min(limit, 200))

    nodes: List[GraphNodeDTO] = []
    edges: List[GraphEdgeDTO] = []
    seen_nodes: Set[str] = set()
    seen_edges: Set[str] = set()

    # Determine center node ID
    if not base_path:
        center_node_id = f"repo:{repo}"
    else:
        center_node_id = f"dir:{repo}@{branch}:{base_path}"

    # Always include the Repository Root Node
    repo_node_id = f"repo:{repo}"
    short_repo = repo.split("/")[-1]
    if repo_node_id not in seen_nodes:
        seen_nodes.add(repo_node_id)
        nodes.append(
            GraphNodeDTO(
                id=repo_node_id,
                entity_type="REPOSITORY",
                title=f"Repository: {repo}",
                slug=short_repo,
                summary=f"Canonical Git repository {repo} (branch: {branch})",
                promotion_state="VALIDATED",
                conflict_state="RESOLVED",
                confidence_score=1.0,
                valid_from="2026-01-01T00:00:00Z",
                valid_until=None,
                trust_zone="tz_internal_holding",
                project_id="pub-core",
                evidence_count=len(tree),
            )
        )

    # Commit snapshot node
    if root_sha:
        commit_node_id = f"commit:{repo}@{root_sha[:8]}"
        if commit_node_id not in seen_nodes:
            seen_nodes.add(commit_node_id)
            nodes.append(
                GraphNodeDTO(
                    id=commit_node_id,
                    entity_type="EVENT",
                    title=f"Commit: {root_sha[:8]}",
                    slug=root_sha[:8],
                    summary=f"Latest tree commit on {branch} ({root_sha})",
                    promotion_state="VALIDATED",
                    conflict_state="RESOLVED",
                    confidence_score=1.0,
                    valid_from="2026-01-01T00:00:00Z",
                    valid_until=None,
                    trust_zone="tz_internal_holding",
                    project_id="pub-core",
                    evidence_count=0,
                )
            )
            # Edge: REPOSITORY -[CREATED_BY]-> COMMIT
            edge_id = f"edge:{repo_node_id}:{commit_node_id}"
            if edge_id not in seen_edges:
                seen_edges.add(edge_id)
                edges.append(
                    GraphEdgeDTO(
                        id=edge_id,
                        source_id=repo_node_id,
                        target_id=commit_node_id,
                        relation_type="CREATED_BY",
                        weight=1.0,
                        is_bidirectional=False,
                        trust_zone="tz_internal_holding",
                        is_active=True,
                        association_status="CONFIRMED",
                        classification_source="git",
                        classification_confidence=1.0,
                        classification_reason="Latest HEAD commit snapshot",
                    )
                )

    # If exploring a subpath, ensure the base directory node itself is present
    if base_path:
        base_dir_name = base_path.split("/")[-1]
        if center_node_id not in seen_nodes:
            seen_nodes.add(center_node_id)
            nodes.append(
                GraphNodeDTO(
                    id=center_node_id,
                    entity_type="CONCEPT",
                    title=f"📁 {base_dir_name}",
                    slug=base_path,
                    summary=f"Directory '{base_dir_name}' in {repo}",
                    promotion_state="VALIDATED",
                    conflict_state="RESOLVED",
                    confidence_score=1.0,
                    valid_from="2026-01-01T00:00:00Z",
                    valid_until=None,
                    trust_zone="tz_internal_holding",
                    project_id="pub-core",
                    evidence_count=0,
                )
            )

    # Index items by relative depth from base_path
    base_prefix = f"{base_path}/" if base_path else ""

    eligible_items = []
    for item in tree:
        item_path = item.get("path", "")
        # Exclude secrets
        if is_secret_file(item_path):
            continue

        if base_prefix:
            if not item_path.startswith(base_prefix):
                continue
            relative_sub = item_path[len(base_prefix):]
        else:
            relative_sub = item_path

        parts = [p for p in relative_sub.split("/") if p]
        item_depth = len(parts)

        if 1 <= item_depth <= bounded_depth:
            eligible_items.append((item_depth, parts, item))

    # Sort eligible items: directories first, then alphabetically
    eligible_items.sort(key=lambda x: (x[0], 0 if x[2].get("type") == "tree" else 1, x[2].get("path", "")))

    # Add items up to bounded_limit
    for item_depth, parts, item in eligible_items:
        if len(nodes) >= bounded_limit:
            break

        item_path = item.get("path", "")
        item_type = item.get("type")
        item_name = parts[-1]
        item_sha = item.get("sha", "")
        item_size = item.get("size", 0)

        # Parent ID calculation
        if item_depth == 1:
            parent_id = center_node_id
        else:
            parent_path = base_prefix + "/".join(parts[:-1]) if base_prefix else "/".join(parts[:-1])
            parent_id = f"dir:{repo}@{branch}:{parent_path}"

        if item_type == "tree":
            node_id = f"dir:{repo}@{branch}:{item_path}"
            entity_type = "CONCEPT"
            title = f"📁 {item_name}"
            summary = f"Git Directory: {item_path}"
        else:
            ext = os.path.splitext(item_name)[1].lower()
            if ext in DOC_EXTENSIONS:
                entity_type = "DOCUMENT"
                title = f"📄 {item_name}"
            else:
                entity_type = "SOURCE"
                title = f"⚡ {item_name}"
            node_id = f"file:{repo}@{branch}:{item_path}"
            summary = f"Git File: {item_path} ({item_size} bytes)"

        if node_id not in seen_nodes:
            seen_nodes.add(node_id)
            nodes.append(
                GraphNodeDTO(
                    id=node_id,
                    entity_type=entity_type,
                    title=title,
                    slug=item_path,
                    summary=summary,
                    promotion_state="VALIDATED",
                    conflict_state="RESOLVED",
                    confidence_score=1.0,
                    valid_from="2026-01-01T00:00:00Z",
                    valid_until=None,
                    trust_zone="tz_internal_holding",
                    project_id="pub-core",
                    evidence_count=1 if item_type == "blob" else 0,
                )
            )

        # Connect to parent
        edge_id = f"edge:{parent_id}:{node_id}"
        if edge_id not in seen_edges and parent_id in seen_nodes:
            seen_edges.add(edge_id)
            edges.append(
                GraphEdgeDTO(
                    id=edge_id,
                    source_id=parent_id,
                    target_id=node_id,
                    relation_type="DEPENDS_ON" if item_type == "tree" else "USES",
                    weight=1.0,
                    is_bidirectional=False,
                    trust_zone="tz_internal_holding",
                    is_active=True,
                    association_status="CONFIRMED",
                    classification_source="git",
                    classification_confidence=1.0,
                    classification_reason=f"Git path containment under {parent_id}",
                )
            )

    return GraphResponseDTO(
        nodes=nodes,
        edges=edges,
        center_node_id=center_node_id,
        hop_depth=bounded_depth,
        total_nodes=len(nodes),
        total_edges=len(edges),
    )


def get_git_node_detail(node_id: str) -> Optional[Dict[str, Any]]:
    """
    Provide deep inspection details for a Git node (Repo, Commit, Directory, or File).
    """
    if node_id.startswith("repo:"):
        repo = node_id.replace("repo:", "")
        return {
            "id": node_id,
            "entity_type": "REPOSITORY",
            "title": f"Repository: {repo}",
            "slug": repo.split("/")[-1],
            "summary": f"Canonical versioned source of truth repository: {repo}",
            "content": f"Repository URL: https://github.com/{repo}\nCanonical Branch: {DEFAULT_BRANCH}\nRole: Sovereign Codebase Truth",
            "promotion_state": "VALIDATED",
            "promotion_reason": "Canonical Source of Truth",
            "conflict_state": "RESOLVED",
            "confidence_score": 1.0,
            "valid_from": "2026-01-01T00:00:00Z",
            "valid_until": None,
            "trust_zone": "tz_internal_holding",
            "project_id": "pub-core",
            "is_active": True,
            "originating_event_id": "00000000-0000-0000-0000-000000000001",
            "evidence": [],
            "git_metadata": {
                "repository": repo,
                "branch": DEFAULT_BRANCH,
                "github_url": f"https://github.com/{repo}",
            },
        }

    if node_id.startswith("commit:"):
        # Format: commit:repo@sha
        match = re.match(r"^commit:([^@]+)@(.+)$", node_id)
        if not match:
            return None
        repo, sha = match.groups()
        return {
            "id": node_id,
            "entity_type": "EVENT",
            "title": f"Commit: {sha}",
            "slug": sha,
            "summary": f"Git Commit Snapshot on {repo}",
            "content": f"Commit SHA: {sha}\nRepository: https://github.com/{repo}/commit/{sha}",
            "promotion_state": "VALIDATED",
            "promotion_reason": "Git Commit Verified",
            "conflict_state": "RESOLVED",
            "confidence_score": 1.0,
            "valid_from": "2026-01-01T00:00:00Z",
            "valid_until": None,
            "trust_zone": "tz_internal_holding",
            "project_id": "pub-core",
            "is_active": True,
            "originating_event_id": "00000000-0000-0000-0000-000000000001",
            "evidence": [],
            "git_metadata": {
                "repository": repo,
                "sha": sha,
                "github_url": f"https://github.com/{repo}/commit/{sha}",
            },
        }

    if node_id.startswith("dir:"):
        # Format: dir:repo@branch:path
        match = re.match(r"^dir:([^@]+)@([^:]+):(.+)$", node_id)
        if not match:
            return None
        repo, branch, path = match.groups()
        return {
            "id": node_id,
            "entity_type": "CONCEPT",
            "title": f"Directory: {path}",
            "slug": path,
            "summary": f"Versioned directory in {repo}@{branch}",
            "content": f"Git Tree Path: {path}\nRepository: {repo}\nBranch: {branch}\nGitHub Link: https://github.com/{repo}/tree/{branch}/{path}",
            "promotion_state": "VALIDATED",
            "promotion_reason": "Git Object Hierarchy",
            "conflict_state": "RESOLVED",
            "confidence_score": 1.0,
            "valid_from": "2026-01-01T00:00:00Z",
            "valid_until": None,
            "trust_zone": "tz_internal_holding",
            "project_id": "pub-core",
            "is_active": True,
            "originating_event_id": "00000000-0000-0000-0000-000000000001",
            "evidence": [],
            "git_metadata": {
                "repository": repo,
                "branch": branch,
                "path": path,
                "type": "tree",
                "github_url": f"https://github.com/{repo}/tree/{branch}/{path}",
            },
        }

    if node_id.startswith("file:"):
        # Format: file:repo@branch:path
        match = re.match(r"^file:([^@]+)@([^:]+):(.+)$", node_id)
        if not match:
            return None
        repo, branch, path = match.groups()
        tree, root_sha = fetch_git_tree_remote(repo, branch)
        item = next((it for it in tree if it.get("path") == path), None)
        item_sha = item.get("sha") if item else "unknown"
        item_size = item.get("size") if item else 0

        ext = os.path.splitext(path)[1].lower()
        entity_type = "DOCUMENT" if ext in DOC_EXTENSIONS else "SOURCE"

        return {
            "id": node_id,
            "entity_type": entity_type,
            "title": f"File: {path}",
            "slug": path,
            "summary": f"Git Blob {item_sha[:8]} ({item_size} bytes)",
            "content": f"File Path: {path}\nGit Blob SHA: {item_sha}\nSize: {item_size} bytes\nGitHub: https://github.com/{repo}/blob/{branch}/{path}",
            "promotion_state": "VALIDATED",
            "promotion_reason": "Git Blob Verified",
            "conflict_state": "RESOLVED",
            "confidence_score": 1.0,
            "valid_from": "2026-01-01T00:00:00Z",
            "valid_until": None,
            "trust_zone": "tz_internal_holding",
            "project_id": "pub-core",
            "is_active": True,
            "originating_event_id": "00000000-0000-0000-0000-000000000001",
            "evidence": [],
            "git_metadata": {
                "repository": repo,
                "branch": branch,
                "path": path,
                "type": "blob",
                "sha": item_sha,
                "size": item_size,
                "raw_url": f"https://raw.githubusercontent.com/{repo}/{branch}/{path}",
                "github_url": f"https://github.com/{repo}/blob/{branch}/{path}",
            },
        }

    return None
