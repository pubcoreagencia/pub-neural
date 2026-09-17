"""
Unified Graph Service for PUB Neural Console V0.
Provides a unified projection of Physical Source-of-Truth (Git / 55 repositories)
and Cognitive Institutional Graph (Nodes, Edges, Policies, Decisions, Rules, Lessons).

Guarantees:
1. No duplicate canonical ontology or persistence layer.
2. Evidence-First Policy:
   - Factual links (EXTRACTED) have verified source and evidence locators.
   - Heuristic / inferred links (INFERRED) carry clear confidence and reasoning.
   - Candidates (PROPOSED) remain distinct and never promoted silently.
3. Level-of-Detail (LOD):
   - Level 0: Organization -> 55 Repositories + Institutional Backbone Nodes + Bridges.
   - Lazy expansion for subtrees.
"""

from typing import Any, Dict, List, Optional, Set

from console.backend.models import (
    EdgeDetailDTO,
    EvidenceLocatorDTO,
    GraphEdgeDTO,
    GraphNodeDTO,
    GraphResponseDTO,
)
from console.backend.services.git_graph_service import (
    CANONICAL_ORG,
    get_organization_graph,
    get_git_topology,
    get_git_node_detail,
    get_git_edge_detail,
)
from console.backend.services.graph_service import (
    get_graph_backbone,
    get_entity_detail,
    get_edge_detail,
)


def get_unified_graph(
    cur,
    source: str = "all",  # "git", "cognitive", or "all"
    trust_zone: Optional[str] = None,
    project_id: Optional[str] = None,
    limit: int = 120,
    repository_filter: Optional[str] = None,
    entity_type_filter: Optional[str] = None,
    relation_type_filter: Optional[str] = None,
    epistemic_filter: Optional[str] = None,  # "EXTRACTED", "INFERRED", "PROPOSED", or None
) -> GraphResponseDTO:
    """Return a unified GraphResponseDTO connecting physical Git topology and cognitive knowledge.

    Orchestrates:
    1. Physical Git Graph (Organization + 55 Repositories).
    2. Cognitive Graph Backbone (Projects, Decisions, Rules, Lessons, Patterns, Agents).
    3. Factual Evidence Bridges:
       - REPOSITORY <-> PROJECT (evidenced in pub_neural.project_repositories).
       - REPOSITORY / SOURCE <-> COGNITIVE NODES (evidenced in pub_neural.neural_evidence and project context).
    """
    nodes: List[GraphNodeDTO] = []
    edges: List[GraphEdgeDTO] = []
    seen_node_ids: Set[str] = set()
    seen_edge_ids: Set[str] = set()

    # 1. Physical Git Topology
    if source in ("git", "all"):
        if repository_filter:
            # Subtree projection for specific repository
            git_graph = get_git_topology(
                repo=repository_filter,
                branch="main",
                base_path="",
                depth=1,
                limit=limit,
            )
        else:
            # Full holding topology (Root + 55 repositories + cross-repo consolidation)
            git_graph = get_organization_graph(
                org=CANONICAL_ORG,
                include_archived=True,
                limit=limit,
            )

        for n in git_graph.nodes:
            if n.id not in seen_node_ids:
                seen_node_ids.add(n.id)
                nodes.append(n)

        for e in git_graph.edges:
            if e.id not in seen_edge_ids:
                seen_edge_ids.add(e.id)
                edges.append(e)

    # 2. Cognitive Institutional Backbone
    if source in ("cognitive", "all"):
        cog_graph = get_graph_backbone(
            cur=cur,
            trust_zone=trust_zone,
            limit=limit,
            project_id=project_id,
        )

        for n in cog_graph.nodes:
            if n.id not in seen_node_ids:
                seen_node_ids.add(n.id)
                nodes.append(n)

        for e in cog_graph.edges:
            if e.id not in seen_edge_ids:
                seen_edge_ids.add(e.id)
                edges.append(e)

    # 3. Evidence Bridges between Physical Repositories, Projects, and Cognitive Entities
    if source == "all" and cur is not None:
        _attach_project_and_evidence_bridges(
            cur=cur,
            nodes=nodes,
            edges=edges,
            seen_node_ids=seen_node_ids,
            seen_edge_ids=seen_edge_ids,
        )

    # 4. Apply Dynamic Filters if requested
    if entity_type_filter:
        allowed_types = {t.strip().upper() for t in entity_type_filter.split(",")}
        nodes = [n for n in nodes if n.entity_type.upper() in allowed_types]
        surviving_ids = {n.id for n in nodes}
        edges = [e for e in edges if e.source_id in surviving_ids and e.target_id in surviving_ids]

    if relation_type_filter:
        allowed_rels = {r.strip().upper() for r in relation_type_filter.split(",")}
        edges = [e for e in edges if e.relation_type.upper() in allowed_rels]

    if epistemic_filter:
        allowed_epistemic = {epistemic_filter.strip().upper()}
        edges = [
            e for e in edges
            if getattr(e, "epistemic_classification", None) in allowed_epistemic
            or (getattr(e, "association_status", None) == "CONFIRMED" and "EXTRACTED" in allowed_epistemic)
            or (getattr(e, "association_status", None) == "PROPOSED" and "PROPOSED" in allowed_epistemic)
        ]

    return GraphResponseDTO(
        nodes=nodes,
        edges=edges,
        center_node_id=f"org:{CANONICAL_ORG}" if f"org:{CANONICAL_ORG}" in seen_node_ids else None,
        hop_depth=1,
        total_nodes=len(nodes),
        total_edges=len(edges),
    )


def _attach_project_and_evidence_bridges(
    cur,
    nodes: List[GraphNodeDTO],
    edges: List[GraphEdgeDTO],
    seen_node_ids: Set[str],
    seen_edge_ids: Set[str],
) -> None:
    """Project canonical PROJECT entities and wire ORG -> PROJECT -> REPOSITORY hierarchy."""
    try:
        org_node_id = f"org:{CANONICAL_ORG}"

        # A. Query holding_projects to create canonical PROJECT nodes
        projects_sql = """
            SELECT
                id, slug, display_name, description, project_type,
                lifecycle_status, is_active, is_archived, strategic_priority,
                owner_scope, ontology_status, ontology_source, ontology_confidence,
                ontology_reason
            FROM pub_neural.holding_projects;
        """
        cur.execute(projects_sql)
        project_rows = cur.fetchall() or []

        for proj in project_rows:
            proj_id = proj["id"]  # e.g. "proj:pub-neural"
            slug = proj["slug"]
            disp_name = proj["display_name"]
            desc = proj.get("description") or f"Holding Project {disp_name}"
            p_type = proj.get("project_type", "PLATFORM")
            ont_status = proj.get("ontology_status", "CONFIRMED")
            ont_conf = float(proj.get("ontology_confidence") or 1.0)
            ont_source = proj.get("ontology_source", "DOCUMENTATION")
            is_active = bool(proj.get("is_active", True))

            if proj_id not in seen_node_ids:
                seen_node_ids.add(proj_id)
                nodes.append(
                    GraphNodeDTO(
                        id=proj_id,
                        entity_type="PROJECT",
                        title=f"🏛️ {disp_name}",
                        slug=slug,
                        summary=f"{desc} (type: {p_type}, status: {proj.get('lifecycle_status', 'ACTIVE')})",
                        promotion_state="INSTITUTIONAL" if ont_status == "CONFIRMED" else "PROPOSED",
                        conflict_state="RESOLVED",
                        confidence_score=ont_conf,
                        valid_from="2026-01-01T00:00:00Z",
                        valid_until=None,
                        trust_zone="tz_internal_holding",
                        project_id=slug,
                        evidence_count=1,
                    )
                )

            # Wire ORG -> PROJECT (CONTAINS)
            org_proj_edge_id = f"edge:{org_node_id}:{proj_id}"
            if org_node_id in seen_node_ids and org_proj_edge_id not in seen_edge_ids:
                seen_edge_ids.add(org_proj_edge_id)
                edges.append(
                    GraphEdgeDTO(
                        id=org_proj_edge_id,
                        source_id=org_node_id,
                        target_id=proj_id,
                        relation_type="CONTAINS",
                        weight=ont_conf,
                        is_bidirectional=False,
                        trust_zone="tz_internal_holding",
                        is_active=is_active,
                        association_status=ont_status,
                        classification_source=ont_source,
                        classification_confidence=ont_conf,
                        classification_reason=f"Organization {CANONICAL_ORG} contains project {disp_name}",
                        epistemic_classification="EXTRACTED" if ont_status == "CONFIRMED" else "PROPOSED",
                        evidence_locator={
                            "source": "pub_neural.holding_projects",
                            "project_id": proj_id,
                            "slug": slug,
                            "ontology_status": ont_status,
                        },
                    )
                )

        # B. Query project_repositories to wire PROJECT -> REPOSITORY
        repo_assoc_sql = """
            SELECT
                project_id, repository_id, relationship_type, is_primary,
                association_status, classification_source, classification_confidence,
                classification_reason
            FROM pub_neural.project_repositories;
        """
        cur.execute(repo_assoc_sql)
        assocs = cur.fetchall() or []

        # Track mapped repository node IDs to rewire edges from ORG -> REPO to PROJECT -> REPO
        mapped_repo_node_ids: Set[str] = set()

        for assoc in assocs:
            proj_id_raw = assoc["project_id"]  # e.g. "proj:pub-core"
            repo_name = assoc["repository_id"]  # e.g. "pubcore"
            is_primary = bool(assoc.get("is_primary", False))
            rel_type = assoc.get("relationship_type", "PRIMARY")
            assoc_status = assoc.get("association_status", "CONFIRMED")
            reason = assoc.get("classification_reason", "Evidenced project repository association")
            confidence = float(assoc.get("classification_confidence") or 1.0)
            class_source = assoc.get("classification_source", "DOCUMENTATION")

            # Determine epistemic state
            if assoc_status == "CONFIRMED" and confidence >= 0.9:
                epistemic_state = "EXTRACTED"
            elif assoc_status == "PROPOSED":
                epistemic_state = "PROPOSED"
            else:
                epistemic_state = "INFERRED"

            proj_node_id = proj_id_raw if proj_id_raw.startswith("proj:") else f"proj:{proj_id_raw}"
            repo_node_id = f"repo:{CANONICAL_ORG}/{repo_name}"

            # If repo node exists in graph
            if repo_node_id in seen_node_ids and proj_node_id in seen_node_ids:
                mapped_repo_node_ids.add(repo_node_id)
                proj_repo_edge_id = f"edge:{proj_node_id}:{repo_node_id}"
                if proj_repo_edge_id not in seen_edge_ids:
                    seen_edge_ids.add(proj_repo_edge_id)
                    edges.append(
                        GraphEdgeDTO(
                            id=proj_repo_edge_id,
                            source_id=proj_node_id,
                            target_id=repo_node_id,
                            relation_type="CONTAINS",
                            weight=1.0 if is_primary else 0.8,
                            is_bidirectional=False,
                            trust_zone="tz_internal_holding",
                            is_active=True,
                            association_status=assoc_status,
                            classification_source=class_source,
                            classification_confidence=confidence,
                            classification_reason=f"Project {proj_node_id} contains repository {repo_name} ({rel_type}, primary={is_primary}): {reason}",
                            epistemic_classification=epistemic_state,
                            evidence_locator={
                                "source": class_source,
                                "repository": repo_name,
                                "project_id": proj_node_id,
                                "relationship_type": rel_type,
                                "is_primary": is_primary,
                                "reason": reason,
                                "confidence": confidence,
                                "epistemic_state": epistemic_state,
                            },
                        )
                    )

            # Bridge to Cognitive Nodes that share this project_id
            clean_proj_key = proj_node_id.replace("proj:", "")

            for n in nodes:
                # If node is a cognitive entity and belongs to this project
                if not (n.id.startswith("org:") or n.id.startswith("proj:") or n.id.startswith("repo:") or n.id.startswith("dir:") or n.id.startswith("file:") or n.id.startswith("commit:")) and n.project_id == clean_proj_key:
                    # Bridge Repo -> Cognitive Entity
                    bridge_edge_id = f"edge:{repo_node_id}:{n.id}"
                    if repo_node_id in seen_node_ids and bridge_edge_id not in seen_edge_ids:
                        seen_edge_ids.add(bridge_edge_id)
                        edges.append(
                            GraphEdgeDTO(
                                id=bridge_edge_id,
                                source_id=repo_node_id,
                                target_id=n.id,
                                relation_type="IMPLEMENTS" if n.entity_type in ("DECISION", "GOVERNANCE", "RULE") else "APPLIES_TO",
                                weight=confidence,
                                is_bidirectional=False,
                                trust_zone=n.trust_zone,
                                is_active=True,
                                association_status=assoc_status,
                                classification_source=class_source,
                                classification_confidence=confidence,
                                classification_reason=f"Repository {repo_name} binds to cognitive node {n.id} via project {clean_proj_key}: {reason}",
                                epistemic_classification=epistemic_state,
                                evidence_locator={
                                    "source": class_source,
                                    "repository": repo_name,
                                    "project": clean_proj_key,
                                    "reason": reason,
                                    "confidence": confidence,
                                    "epistemic_state": epistemic_state,
                                },
                            )
                        )

                    # Bridge Project -> Cognitive Entity
                    proj_cog_edge_id = f"edge:{proj_node_id}:{n.id}"
                    if proj_node_id in seen_node_ids and proj_cog_edge_id not in seen_edge_ids:
                        seen_edge_ids.add(proj_cog_edge_id)
                        edges.append(
                            GraphEdgeDTO(
                                id=proj_cog_edge_id,
                                source_id=proj_node_id,
                                target_id=n.id,
                                relation_type="IMPLEMENTS" if n.entity_type in ("DECISION", "GOVERNANCE", "RULE") else "APPLIES_TO",
                                weight=1.0,
                                is_bidirectional=False,
                                trust_zone=n.trust_zone,
                                is_active=True,
                                association_status="CONFIRMED",
                                classification_source="pub_neural.neural_nodes",
                                classification_confidence=1.0,
                                classification_reason=f"Project {proj_node_id} governs cognitive node {n.id}",
                                epistemic_classification="EXTRACTED",
                                evidence_locator={
                                    "source": "pub_neural.neural_nodes",
                                    "project_id": proj_node_id,
                                    "node_id": n.id,
                                },
                            )
                        )

        # C. Rewire direct ORG -> REPO edges:
        # Repositories that now have a Project parent should NOT have a duplicate direct ORG -> REPO edge.
        # Only unmapped repositories (e.g. pub-github-mcp) retain direct edge org:pubcoreagencia -> repo:pubcoreagencia/...
        if mapped_repo_node_ids:
            edges[:] = [
                e for e in edges
                if not (e.source_id == org_node_id and e.target_id in mapped_repo_node_ids)
            ]

        # D. Query neural_evidence for direct file / commit evidence attachments
        ev_query_sql = """
            SELECT 
                e.id AS evidence_id, e.node_id, e.edge_id, e.confidence,
                e.start_line, e.end_line, e.exact_quote,
                s.repository, s.commit_sha, s.file_path
            FROM pub_neural.neural_evidence e
            JOIN pub_neural.neural_sources s ON e.source_id = s.id
            WHERE s.repository IS NOT NULL;
        """
        cur.execute(ev_query_sql)
        ev_rows = cur.fetchall() or []

        for ev in ev_rows:
            node_id = ev.get("node_id")
            repo = ev.get("repository")
            file_path = ev.get("file_path")
            conf = float(ev.get("confidence") or 1.0)
            if not repo or not node_id:
                continue

            repo_node_id = f"repo:{CANONICAL_ORG}/{repo}" if "/" not in repo else f"repo:{repo}"
            bridge_edge_id = f"edge:{repo_node_id}:{node_id}"

            if repo_node_id in seen_node_ids and node_id in seen_node_ids and bridge_edge_id not in seen_edge_ids:
                seen_edge_ids.add(bridge_edge_id)
                edges.append(
                    GraphEdgeDTO(
                        id=bridge_edge_id,
                        source_id=repo_node_id,
                        target_id=node_id,
                        relation_type="VALIDATED_BY",
                        weight=conf,
                        is_bidirectional=False,
                        trust_zone="tz_internal_holding",
                        is_active=True,
                        association_status="CONFIRMED",
                        classification_source="neural_evidence",
                        classification_confidence=conf,
                        classification_reason=f"Grounded code slice evidence in {file_path}",
                        epistemic_classification="EXTRACTED",
                        evidence_locator={
                            "evidence_id": str(ev.get("evidence_id")),
                            "repository": repo,
                            "file_path": file_path,
                            "commit_sha": ev.get("commit_sha"),
                            "start_line": ev.get("start_line"),
                            "end_line": ev.get("end_line"),
                            "exact_quote": ev.get("exact_quote"),
                            "confidence": conf,
                            "epistemic_state": "EXTRACTED",
                        },
                    )
                )
    except Exception as e:
        # Fail-soft: project and bridge enhancement must not break base graph projection
        import logging
        logging.getLogger(__name__).warning("Error attaching project and evidence bridges in unified graph: %s", e)

