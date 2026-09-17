"""
Data Transfer Objects (DTOs) for PUB Neural Console V0 Read-Only API.
Enforces typed presentation boundaries and prevents database row / secret leakage.
"""

from dataclasses import asdict, dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional
import uuid


def serialize_val(val: Any) -> Any:
    """Helper to serialize datetime, UUID, or dataclass objects."""
    if isinstance(val, (datetime,)):
        return val.isoformat()
    if isinstance(val, (uuid.UUID,)):
        return str(val)
    if hasattr(val, "to_dict"):
        return val.to_dict()
    if isinstance(val, list):
        return [serialize_val(item) for item in val]
    if isinstance(val, dict):
        return {k: serialize_val(v) for k, v in val.items()}
    return val


@dataclass(frozen=True)
class GraphNodeDTO:
    id: str
    entity_type: str
    title: str
    slug: str
    summary: Optional[str]
    promotion_state: str
    conflict_state: str
    confidence_score: float
    valid_from: str
    valid_until: Optional[str]
    trust_zone: str
    project_id: Optional[str]
    evidence_count: int

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class GraphEdgeDTO:
    id: str
    source_id: str
    target_id: str
    relation_type: str
    weight: float
    is_bidirectional: bool
    trust_zone: str
    is_active: bool

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class GraphResponseDTO:
    nodes: List[GraphNodeDTO]
    edges: List[GraphEdgeDTO]
    center_node_id: Optional[str]
    hop_depth: int
    total_nodes: int
    total_edges: int

    def to_dict(self) -> Dict[str, Any]:
        return {
            "nodes": [n.to_dict() for n in self.nodes],
            "edges": [e.to_dict() for e in self.edges],
            "center_node_id": self.center_node_id,
            "hop_depth": self.hop_depth,
            "total_nodes": self.total_nodes,
            "total_edges": self.total_edges,
        }


@dataclass(frozen=True)
class EvidenceLocatorDTO:
    id: str
    source_id: str
    repository: Optional[str]
    commit_sha: Optional[str]
    file_path: Optional[str]
    start_line: int
    end_line: int
    exact_quote: str
    confidence: float

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class EntityDetailDTO:
    id: str
    entity_type: str
    title: str
    slug: str
    summary: Optional[str]
    content: Optional[str]
    promotion_state: str
    promotion_reason: Optional[str]
    conflict_state: str
    confidence_score: float
    superseded_by: Optional[str]
    valid_from: str
    valid_until: Optional[str]
    recorded_from: str
    recorded_until: Optional[str]
    is_active: bool
    originating_event_id: str
    last_transition_event_id: Optional[str]
    project_id: Optional[str]
    trust_zone: str
    created_at: str
    updated_at: str
    evidence: List[EvidenceLocatorDTO]
    incoming_relations_count: int
    outgoing_relations_count: int

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d["evidence"] = [e.to_dict() for e in self.evidence]
        return d


@dataclass(frozen=True)
class SearchResultItemDTO:
    target_id: str
    target_type: str
    title: str
    snippet: str
    lexical_rank: Optional[int]
    dense_rank: Optional[int]
    rrf_score: float
    trust_zone: str
    project_id: Optional[str]
    originating_event_id: str

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class AbstentionDecisionDTO:
    accepted: bool
    reason: Optional[str]
    top_dense_similarity: Optional[float]
    top_rrf_score: Optional[float]
    lexical_candidate_count: int
    dense_candidate_count: int

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class SearchResponseDTO:
    query: str
    status: str  # "SUCCESS", "ABSTAINED", "NO_MATCH"
    results: List[SearchResultItemDTO]
    abstention_decision: AbstentionDecisionDTO
    lexical_count: int
    dense_count: int

    def to_dict(self) -> Dict[str, Any]:
        return {
            "query": self.query,
            "status": self.status,
            "results": [r.to_dict() for r in self.results],
            "abstention_decision": self.abstention_decision.to_dict(),
            "lexical_count": self.lexical_count,
            "dense_count": self.dense_count,
        }


@dataclass(frozen=True)
class EventItemDTO:
    id: str
    global_sequence: int
    event_type: str
    event_version: int
    producer_version: str
    stream_id: str
    stream_version: int
    actor_id: str
    actor_role: str
    recorded_at: str

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class EventDetailDTO:
    id: str
    global_sequence: int
    event_type: str
    event_version: int
    payload_schema_version: int
    producer_version: str
    stream_id: str
    stream_version: int
    actor_id: str
    actor_role: str
    payload: Dict[str, Any]
    signature: Optional[str]
    recorded_at: str
    parent_event_ids: List[str]

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class EventListResponseDTO:
    events: List[EventItemDTO]
    total_returned: int
    limit: int
    offset: int

    def to_dict(self) -> Dict[str, Any]:
        return {
            "events": [e.to_dict() for e in self.events],
            "total_returned": self.total_returned,
            "limit": self.limit,
            "offset": self.offset,
        }


@dataclass(frozen=True)
class SystemStatusDTO:
    status: str
    database_connected: bool
    postgresql_version: Optional[str]
    active_trust_zone: Optional[str]
    active_actor_role: Optional[str]
    projector_checkpoints: List[Dict[str, Any]]
    capabilities: Dict[str, str]
    server_time: str

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class CandidateReviewDTO:
    id: str
    entity_type: str
    title: str
    summary: Optional[str]
    content: Optional[str]
    promotion_state: str
    promotion_reason: Optional[str]
    conflict_state: str
    scope: str
    project_id: Optional[str]
    trust_zone: str
    originating_event_id: str
    originating_event_type: Optional[str]
    proposed_by_actor_id: Optional[str]
    proposed_by_actor_role: Optional[str]
    derived_from_experience_id: Optional[str]
    created_at: str
    evidence_count: int

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class GovernanceReviewResponseDTO:
    generated_at: str
    candidates_count: int
    candidates: List[CandidateReviewDTO]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "generated_at": self.generated_at,
            "candidates_count": self.candidates_count,
            "candidates": [c.to_dict() for c in self.candidates],
        }


@dataclass(frozen=True)
class ErrorResponseDTO:
    error: str
    detail: Optional[str] = None
    status_code: int = 400

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class LatestSignalDTO:
    type: str
    timestamp: str
    summary: str
    source: str
    locator: str

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class ProjectRegistryItemDTO:
    id: str
    repository_full_name: str
    repository_name: str
    display_name: str
    description: Optional[str]
    category: str
    lifecycle_status: str
    is_active: bool
    is_archived: bool
    is_private: bool
    monitoring_enabled: bool
    strategic_priority: str
    github_url: Optional[str]
    created_at: str
    updated_at: str
    last_discovered_at: str

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class ProjectRegistryListDTO:
    total_count: int
    projects: List[ProjectRegistryItemDTO]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "total_count": self.total_count,
            "projects": [p.to_dict() for p in self.projects],
        }


@dataclass(frozen=True)
class ProjectRepositoryAssociationDTO:
    project_id: str
    repository_id: str
    repository_name: str
    display_name: str
    category: str
    relationship_type: str
    is_primary: bool
    association_status: str
    classification_source: str
    classification_confidence: float
    classification_reason: Optional[str]
    github_url: Optional[str]
    observation_count: int = 0
    last_observation_at: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class HoldingProjectItemDTO:
    id: str
    slug: str
    display_name: str
    description: Optional[str]
    project_type: str
    lifecycle_status: str
    is_active: bool
    is_archived: bool
    strategic_priority: str
    owner_scope: str
    repositories_count: int
    confirmed_repositories_count: int
    proposed_repositories_count: int
    active_knowledge_nodes_count: int
    recent_observations_7d: int
    repositories: List[ProjectRepositoryAssociationDTO]
    created_at: str
    updated_at: str

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d["repositories"] = [r.to_dict() for r in self.repositories]
        return d


@dataclass(frozen=True)
class HoldingProjectListDTO:
    total_projects: int
    projects: List[HoldingProjectItemDTO]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "total_projects": self.total_projects,
            "projects": [p.to_dict() for p in self.projects],
        }


@dataclass(frozen=True)
class ExecutiveSummaryDTO:
    total_holding_projects: int
    total_repositories: int
    multi_repo_projects_count: int
    unclassified_repositories_count: int
    confirmed_associations_count: int
    proposed_associations_count: int
    active_projects: int
    monitored_repositories: int
    recent_observations_7d: int
    events_today: int
    candidate_knowledge_count: int
    adopted_knowledge_count: int
    neural_health: str

    @property
    def total_projects(self) -> int:
        return self.total_holding_projects

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d["total_projects"] = self.total_holding_projects
        return d


@dataclass(frozen=True)
class OverviewProjectDTO:
    project_id: str
    observed_repository_count: int
    observation_count: int
    activity_today: int
    activity_7d: int
    last_observation_at: Optional[str]
    active_node_count: int
    project_state: str = "SEM_OBSERVACOES"
    blocked_nodes_count: int = 0
    latest_signal: Optional[LatestSignalDTO] = None
    display_name: Optional[str] = None
    description: Optional[str] = None
    category: Optional[str] = None
    lifecycle_status: Optional[str] = None
    is_active: bool = True
    is_archived: bool = False
    monitoring_enabled: bool = True
    github_url: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "project_id": self.project_id,
            "observed_repository_count": self.observed_repository_count,
            "observation_count": self.observation_count,
            "activity_today": self.activity_today,
            "activity_7d": self.activity_7d,
            "last_observation_at": self.last_observation_at,
            "active_node_count": self.active_node_count,
            "project_state": self.project_state,
            "blocked_nodes_count": self.blocked_nodes_count,
            "latest_signal": self.latest_signal.to_dict() if self.latest_signal else None,
            "display_name": self.display_name or self.project_id,
            "description": self.description or "",
            "category": self.category or "OPERACIONAL",
            "lifecycle_status": self.lifecycle_status or ("ARQUIVADO" if self.is_archived else "ATIVO"),
            "is_active": self.is_active,
            "is_archived": self.is_archived,
            "monitoring_enabled": self.monitoring_enabled,
            "github_url": self.github_url,
        }


@dataclass(frozen=True)
class DailyActivityBucketDTO:
    day: str
    project_id: str
    observed_count: int

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class OverviewResponseDTO:
    generated_at: str
    window_days: int
    database_health: str
    projector_health: str
    projects: List[OverviewProjectDTO]
    daily_activity: List[DailyActivityBucketDTO]
    executive_summary: Optional[ExecutiveSummaryDTO] = None
    holding_projects: Optional[List[HoldingProjectItemDTO]] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "generated_at": self.generated_at,
            "window_days": self.window_days,
            "database_health": self.database_health,
            "projector_health": self.projector_health,
            "projects": [p.to_dict() for p in self.projects],
            "daily_activity": [b.to_dict() for b in self.daily_activity],
            "executive_summary": self.executive_summary.to_dict() if self.executive_summary else None,
            "holding_projects": [hp.to_dict() for hp in self.holding_projects] if self.holding_projects else None,
        }
