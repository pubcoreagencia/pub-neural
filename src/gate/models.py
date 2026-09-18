"""
Data Transfer Objects (DTOs) and contracts for the Bidirectional Neural Knowledge Gate.
Defines explicit, typed, and validatable contracts for:
  - Query Request (PDL -> Neural)
  - Query Response (Neural -> PDL)
  - Experience / Writeback (PDL -> Neural)
  - Provenance, Authority, Freshness, and Abstention metadata
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
import json
from typing import Any, Dict, List, Optional, Union

from .enums import (
    AgentRole,
    AuthorityLevel,
    ConflictState,
    ExperienceWritebackStatus,
    FreshnessState,
    GateStatus,
    KnowledgeClass,
    PromotionState,
    TaskExecutionStatus,
)
from .exceptions import GateValidationError


def _validate_non_empty_str(value: Any, field_name: str) -> str:
    """Validate that a field is a non-empty string."""
    if not isinstance(value, str) or not value.strip():
        raise GateValidationError(
            f"Field '{field_name}' must be a non-empty string, got {repr(value)}",
            field=field_name,
        )
    return value.strip()


def _validate_iso_timestamp(value: Any, field_name: str) -> str:
    """Validate that a field is a valid ISO timestamp."""
    text = _validate_non_empty_str(value, field_name)
    try:
        # Handle 'Z' suffix for Python < 3.11 compatibility
        iso_str = text.replace("Z", "+00:00")
        datetime.fromisoformat(iso_str)
    except Exception as e:
        raise GateValidationError(
            f"Field '{field_name}' must be a valid ISO 8601 timestamp: {e}",
            field=field_name,
        )
    return text


@dataclass
class ProvenanceMetadata:
    """
    Metadata recording the precise origin and evidence of a knowledge item.
    Enables full cryptographic and git lineage reconstruction without inventing provenance.
    """
    source_id: Optional[str] = None
    originating_event_id: Optional[str] = None
    evidence_id: Optional[str] = None
    repository: Optional[str] = None
    commit_sha: Optional[str] = None
    file_path: Optional[str] = None
    start_line: Optional[int] = None
    end_line: Optional[int] = None
    exact_quote: Optional[str] = None
    content_hash: Optional[str] = None
    captured_at: Optional[str] = None
    observed_at: Optional[str] = None
    storage_uri: Optional[str] = None
    last_transition_event_id: Optional[str] = None
    recorded_from: Optional[str] = None
    recorded_until: Optional[str] = None

    def __post_init__(self) -> None:
        if self.start_line is not None and self.start_line < 1:
            raise GateValidationError("start_line must be >= 1", field="start_line")
        if self.end_line is not None and self.end_line < 1:
            raise GateValidationError("end_line must be >= 1", field="end_line")
        if self.start_line is not None and self.end_line is not None:
            if self.start_line > self.end_line:
                raise GateValidationError(
                    f"start_line ({self.start_line}) cannot exceed end_line ({self.end_line})",
                    field="start_line",
                )

    def has_git_provenance(self) -> bool:
        """Check whether minimum Git provenance (repository + commit_sha) is present."""
        return bool(self.repository and self.commit_sha)

    def has_evidence_locator(self) -> bool:
        """Check whether direct locator (exact quote or file path with line numbers) is present."""
        return bool(self.exact_quote or (self.file_path and self.start_line is not None))

    def to_dict(self) -> Dict[str, Any]:
        return {
            "source_id": self.source_id,
            "originating_event_id": self.originating_event_id,
            "evidence_id": self.evidence_id,
            "repository": self.repository,
            "commit_sha": self.commit_sha,
            "file_path": self.file_path,
            "start_line": self.start_line,
            "end_line": self.end_line,
            "exact_quote": self.exact_quote,
            "content_hash": self.content_hash,
            "captured_at": self.captured_at,
            "observed_at": self.observed_at,
            "storage_uri": self.storage_uri,
            "last_transition_event_id": self.last_transition_event_id,
            "recorded_from": self.recorded_from,
            "recorded_until": self.recorded_until,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ProvenanceMetadata":
        if not isinstance(data, dict):
            raise GateValidationError("Provenance data must be a dictionary", field="provenance")
        return cls(
            source_id=data.get("source_id"),
            originating_event_id=data.get("originating_event_id"),
            evidence_id=data.get("evidence_id"),
            repository=data.get("repository"),
            commit_sha=data.get("commit_sha"),
            file_path=data.get("file_path"),
            start_line=data.get("start_line"),
            end_line=data.get("end_line"),
            exact_quote=data.get("exact_quote"),
            content_hash=data.get("content_hash"),
            captured_at=data.get("captured_at"),
            observed_at=data.get("observed_at"),
            storage_uri=data.get("storage_uri"),
            last_transition_event_id=data.get("last_transition_event_id"),
            recorded_from=data.get("recorded_from"),
            recorded_until=data.get("recorded_until"),
        )


@dataclass
class AuthorityMetadata:
    """
    Evidence hierarchy and authority classification for a knowledge item.
    CRITICAL: Neural knowledge is DATA. is_data_only is enforced as True.
    """
    level: AuthorityLevel = AuthorityLevel.VALIDATED_KNOWLEDGE
    is_data_only: bool = True
    description: Optional[str] = None

    def __post_init__(self) -> None:
        self.level = AuthorityLevel.from_str(self.level)
        # Neural knowledge is strictly data, never executable authority.
        if not self.is_data_only:
            raise GateValidationError(
                "Neural knowledge must always have is_data_only=True. It cannot override governance or runtime truth.",
                field="is_data_only",
            )

    @property
    def rank(self) -> int:
        return self.level.rank

    def is_authoritative_over(self, other: "AuthorityMetadata") -> bool:
        return self.level.is_authoritative_over(other.level)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "level": self.level.value,
            "rank": self.rank,
            "is_data_only": self.is_data_only,
            "description": self.description,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AuthorityMetadata":
        if not isinstance(data, dict):
            raise GateValidationError("Authority data must be a dictionary", field="authority")
        return cls(
            level=AuthorityLevel.from_str(data.get("level", AuthorityLevel.VALIDATED_KNOWLEDGE.value)),
            is_data_only=bool(data.get("is_data_only", True)),
            description=data.get("description"),
        )


@dataclass
class FreshnessMetadata:
    """
    Freshness, validity and branch alignment tracking for a knowledge item.
    """
    state: FreshnessState = FreshnessState.VALID
    is_stale: bool = False
    checked_at: Optional[str] = None
    diverged_commit_sha: Optional[str] = None
    valid_from: Optional[str] = None
    valid_until: Optional[str] = None
    reason: Optional[str] = None

    def __post_init__(self) -> None:
        self.state = FreshnessState.from_str(self.state)
        # Synchronize is_stale boolean with state enum
        if self.state in (FreshnessState.STALE, FreshnessState.EXPIRED):
            self.is_stale = True

    def to_dict(self) -> Dict[str, Any]:
        return {
            "state": self.state.value,
            "is_stale": self.is_stale,
            "checked_at": self.checked_at,
            "diverged_commit_sha": self.diverged_commit_sha,
            "valid_from": self.valid_from,
            "valid_until": self.valid_until,
            "reason": self.reason,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "FreshnessMetadata":
        if not isinstance(data, dict):
            raise GateValidationError("Freshness data must be a dictionary", field="freshness")
        return cls(
            state=FreshnessState.from_str(data.get("state", FreshnessState.VALID.value)),
            is_stale=bool(data.get("is_stale", False)),
            checked_at=data.get("checked_at"),
            diverged_commit_sha=data.get("diverged_commit_sha"),
            valid_from=data.get("valid_from"),
            valid_until=data.get("valid_until"),
            reason=data.get("reason"),
        )


@dataclass
class AbstentionMetadata:
    """
    Explicit decision record from the Retrieval Abstention Gate.
    Guarantees abstention is represented as an auditable domain decision, not merely results=[].
    """
    abstained: bool
    decision_reason: str
    top_dense_similarity: Optional[float] = None
    top_rrf_score: Optional[float] = None
    lexical_candidate_count: int = 0
    dense_candidate_count: int = 0
    threshold_applied: Optional[float] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "abstained": self.abstained,
            "decision_reason": self.decision_reason,
            "top_dense_similarity": self.top_dense_similarity,
            "top_rrf_score": self.top_rrf_score,
            "lexical_candidate_count": self.lexical_candidate_count,
            "dense_candidate_count": self.dense_candidate_count,
            "threshold_applied": self.threshold_applied,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AbstentionMetadata":
        if not isinstance(data, dict):
            raise GateValidationError("Abstention data must be a dictionary", field="abstention")
        return cls(
            abstained=bool(data.get("abstained", False)),
            decision_reason=_validate_non_empty_str(data.get("decision_reason", "NO_DECISION"), "decision_reason"),
            top_dense_similarity=data.get("top_dense_similarity"),
            top_rrf_score=data.get("top_rrf_score"),
            lexical_candidate_count=int(data.get("lexical_candidate_count", 0)),
            dense_candidate_count=int(data.get("dense_candidate_count", 0)),
            threshold_applied=data.get("threshold_applied"),
        )


@dataclass
class CallerIdentity:
    """
    Identifies the requesting actor or agent context making the query.
    """
    actor_id: str
    agent_role: Optional[AgentRole] = None
    trust_zone: str = "tz_internal_holding"

    def __post_init__(self) -> None:
        self.actor_id = _validate_non_empty_str(self.actor_id, "actor_id")
        self.trust_zone = _validate_non_empty_str(self.trust_zone, "trust_zone")
        if self.agent_role is not None:
            self.agent_role = AgentRole.from_str(self.agent_role)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "actor_id": self.actor_id,
            "agent_role": self.agent_role.value if self.agent_role else None,
            "trust_zone": self.trust_zone,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "CallerIdentity":
        if not isinstance(data, dict):
            raise GateValidationError("Caller identity must be a dictionary", field="caller")
        role = data.get("agent_role")
        return cls(
            actor_id=data.get("actor_id", ""),
            agent_role=AgentRole.from_str(role) if role else None,
            trust_zone=data.get("trust_zone", "tz_internal_holding"),
        )


@dataclass
class NeuralKnowledgeItem:
    """
    A discrete, retrieved unit of structured knowledge from PUB Neural.
    Carries complete provenance, authority ranking, and freshness metadata.
    """
    id: str
    knowledge_class: KnowledgeClass
    title: str
    content: str
    scope: str = "GLOBAL"  # 'GLOBAL' or 'PROJECT'
    project_id: Optional[str] = None
    relevance_score: float = 0.0
    confidence_score: float = 1.0
    promotion_state: Optional[PromotionState] = None
    conflict_state: Optional[ConflictState] = None
    authority: AuthorityMetadata = field(default_factory=lambda: AuthorityMetadata(level=AuthorityLevel.VALIDATED_KNOWLEDGE))
    provenance: ProvenanceMetadata = field(default_factory=ProvenanceMetadata)
    freshness: FreshnessMetadata = field(default_factory=lambda: FreshnessMetadata(state=FreshnessState.VALID, is_stale=False))

    def __post_init__(self) -> None:
        self.id = _validate_non_empty_str(self.id, "id")
        self.title = _validate_non_empty_str(self.title, "title")
        self.content = _validate_non_empty_str(self.content, "content")

        self.knowledge_class = KnowledgeClass.from_str(self.knowledge_class)
        if self.promotion_state is not None:
            self.promotion_state = PromotionState.from_str(self.promotion_state)
        if self.conflict_state is not None:
            self.conflict_state = ConflictState.from_str(self.conflict_state)

        norm_scope = str(self.scope).strip().upper()
        if norm_scope not in ("GLOBAL", "PROJECT"):
            raise GateValidationError(f"Scope must be 'GLOBAL' or 'PROJECT', got '{self.scope}'", field="scope")
        self.scope = norm_scope

        if not isinstance(self.authority, AuthorityMetadata):
            raise GateValidationError("authority must be an AuthorityMetadata instance", field="authority")
        if not isinstance(self.provenance, ProvenanceMetadata):
            raise GateValidationError("provenance must be a ProvenanceMetadata instance", field="provenance")
        if not isinstance(self.freshness, FreshnessMetadata):
            raise GateValidationError("freshness must be a FreshnessMetadata instance", field="freshness")

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "knowledge_class": self.knowledge_class.value,
            "title": self.title,
            "content": self.content,
            "scope": self.scope,
            "project_id": self.project_id,
            "relevance_score": self.relevance_score,
            "confidence_score": self.confidence_score,
            "promotion_state": self.promotion_state.value if self.promotion_state else None,
            "conflict_state": self.conflict_state.value if self.conflict_state else None,
            "authority": self.authority.to_dict(),
            "provenance": self.provenance.to_dict(),
            "freshness": self.freshness.to_dict(),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "NeuralKnowledgeItem":
        if not isinstance(data, dict):
            raise GateValidationError("Knowledge item must be a dictionary", field="results")

        raw_prom = data.get("promotion_state")
        prom_val = PromotionState.from_str(raw_prom) if raw_prom is not None else None

        raw_conf = data.get("conflict_state")
        conf_val = ConflictState.from_str(raw_conf) if raw_conf is not None else None

        return cls(
            id=data.get("id", ""),
            knowledge_class=KnowledgeClass.from_str(data.get("knowledge_class", "")),
            title=data.get("title", ""),
            content=data.get("content", ""),
            scope=data.get("scope", "GLOBAL"),
            project_id=data.get("project_id"),
            relevance_score=float(data.get("relevance_score", 0.0)),
            confidence_score=float(data.get("confidence_score", 1.0)),
            promotion_state=prom_val,
            conflict_state=conf_val,
            authority=AuthorityMetadata.from_dict(data.get("authority", {})),
            provenance=ProvenanceMetadata.from_dict(data.get("provenance", {})),
            freshness=FreshnessMetadata.from_dict(data.get("freshness", {})),
        )


@dataclass
class ContradictionItem:
    """
    Represents an observed conflict between two knowledge items.
    """
    item_a_id: str
    item_b_id: str
    reason: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "item_a_id": self.item_a_id,
            "item_b_id": self.item_b_id,
            "reason": self.reason,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ContradictionItem":
        return cls(
            item_a_id=_validate_non_empty_str(data.get("item_a_id"), "item_a_id"),
            item_b_id=_validate_non_empty_str(data.get("item_b_id"), "item_b_id"),
            reason=_validate_non_empty_str(data.get("reason"), "reason"),
        )


@dataclass
class NeuralQueryRequest:
    """
    Contract for a PDL -> PUB Neural knowledge consultation.
    Enforces validation of mandatory fields, explicit typing, closed knowledge classes,
    and deterministic serialization.
    """
    request_id: str
    task_id: str
    project_id: str
    repository: str
    objective: str
    requested_knowledge_classes: List[KnowledgeClass]
    caller: CallerIdentity
    timestamp: str
    branch: Optional[str] = None
    commit_sha: Optional[str] = None
    filters: Optional[Dict[str, Any]] = None
    limit: int = 5
    execution_id: Optional[str] = None
    correlation_id: Optional[str] = None

    def __post_init__(self) -> None:
        self.request_id = _validate_non_empty_str(self.request_id, "request_id")
        self.task_id = _validate_non_empty_str(self.task_id, "task_id")
        self.project_id = _validate_non_empty_str(self.project_id, "project_id")
        self.repository = _validate_non_empty_str(self.repository, "repository")
        self.objective = _validate_non_empty_str(self.objective, "objective")
        self.timestamp = _validate_iso_timestamp(self.timestamp, "timestamp")

        if self.execution_id is not None:
            self.execution_id = str(self.execution_id).strip()
        if self.correlation_id is not None:
            self.correlation_id = str(self.correlation_id).strip()

        if not isinstance(self.caller, CallerIdentity):
            raise GateValidationError("caller must be a CallerIdentity instance", field="caller")

        if not isinstance(self.requested_knowledge_classes, (list, tuple, set)):
            raise GateValidationError(
                "requested_knowledge_classes must be a non-empty list of KnowledgeClass",
                field="requested_knowledge_classes",
            )
        if len(self.requested_knowledge_classes) == 0:
            raise GateValidationError(
                "requested_knowledge_classes cannot be empty. Specify at least one KnowledgeClass.",
                field="requested_knowledge_classes",
            )

        # Normalize and validate knowledge classes
        normalized_classes = []
        for item in self.requested_knowledge_classes:
            if isinstance(item, KnowledgeClass):
                normalized_classes.append(item)
            elif isinstance(item, str):
                normalized_classes.append(KnowledgeClass.from_str(item))
            else:
                raise GateValidationError(
                    f"Invalid item in requested_knowledge_classes: {type(item).__name__}",
                    field="requested_knowledge_classes",
                )
        self.requested_knowledge_classes = normalized_classes

        if not isinstance(self.limit, int) or self.limit < 1 or self.limit > 50:
            raise GateValidationError(
                f"limit must be an integer between 1 and 50, got {self.limit}",
                field="limit",
            )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "request_id": self.request_id,
            "requestId": self.request_id,
            "task_id": self.task_id,
            "taskId": self.task_id,
            "execution_id": self.execution_id,
            "executionId": self.execution_id,
            "correlation_id": self.correlation_id,
            "correlationId": self.correlation_id,
            "project_id": self.project_id,
            "projectId": self.project_id,
            "repository": self.repository,
            "objective": self.objective,
            "requested_knowledge_classes": [k.value for k in self.requested_knowledge_classes],
            "requestedKnowledgeClasses": [k.value for k in self.requested_knowledge_classes],
            "caller": self.caller.to_dict(),
            "timestamp": self.timestamp,
            "branch": self.branch,
            "commit_sha": self.commit_sha,
            "commitSha": self.commit_sha,
            "filters": self.filters or {},
            "limit": self.limit,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "NeuralQueryRequest":
        if not isinstance(data, dict):
            raise GateValidationError("Query request payload must be a dictionary")
        classes_raw = data.get("requested_knowledge_classes", data.get("requestedKnowledgeClasses"))
        if classes_raw is None:
            raise GateValidationError("Field 'requested_knowledge_classes' is required", field="requested_knowledge_classes")

        return cls(
            request_id=data.get("request_id", data.get("requestId", "")),
            task_id=data.get("task_id", data.get("taskId", "")),
            project_id=data.get("project_id", data.get("projectId", "")),
            repository=data.get("repository", ""),
            objective=data.get("objective", ""),
            requested_knowledge_classes=classes_raw,
            caller=CallerIdentity.from_dict(data.get("caller", {})),
            timestamp=data.get("timestamp", ""),
            branch=data.get("branch"),
            commit_sha=data.get("commit_sha", data.get("commitSha")),
            filters=data.get("filters"),
            limit=data.get("limit", 5),
            execution_id=data.get("execution_id", data.get("executionId")),
            correlation_id=data.get("correlation_id", data.get("correlationId")),
        )

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2, ensure_ascii=False)

    @classmethod
    def from_json(cls, json_str: str) -> "NeuralQueryRequest":
        try:
            data = json.loads(json_str)
        except Exception as e:
            raise GateValidationError(f"Invalid JSON string for NeuralQueryRequest: {e}")
        return cls.from_dict(data)


@dataclass
class NeuralQueryResponse:
    """
    Contract for a PUB Neural -> PDL consultation response.
    Enforces auditable status separation (SUCCESS, NO_MATCH, ABSTAIN, CONFLICT, STALE, UNAVAILABLE, INTERNAL_ERROR).
    """
    request_id: str
    status: GateStatus
    results: List[NeuralKnowledgeItem] = field(default_factory=list)
    abstention: Optional[AbstentionMetadata] = None
    reason: Optional[str] = None
    contradictions: List[ContradictionItem] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    task_id: Optional[str] = None
    execution_id: Optional[str] = None
    correlation_id: Optional[str] = None

    def __post_init__(self) -> None:
        self.request_id = _validate_non_empty_str(self.request_id, "request_id")
        self.status = GateStatus.from_str(self.status)

        if self.task_id is not None:
            self.task_id = str(self.task_id).strip()
        if self.execution_id is not None:
            self.execution_id = str(self.execution_id).strip()
        if self.correlation_id is not None:
            self.correlation_id = str(self.correlation_id).strip()

        # Domain Invariants
        if self.status == GateStatus.NO_MATCH and len(self.results) > 0:
            raise GateValidationError("Status NO_MATCH must have empty results list", field="results")

        if self.status == GateStatus.ABSTAIN:
            if self.abstention is None:
                raise GateValidationError("Status ABSTAIN requires explicit abstention metadata", field="abstention")
            if not self.abstention.abstained:
                raise GateValidationError("Status ABSTAIN requires abstention.abstained == True", field="abstention")

        if self.status in (GateStatus.INVALID_REQUEST, GateStatus.UNAVAILABLE, GateStatus.INTERNAL_ERROR):
            if not self.reason or not str(self.reason).strip():
                raise GateValidationError(f"Status {self.status.value} requires an explicit failure reason", field="reason")

        if self.status == GateStatus.STALE and len(self.results) == 0:
            raise GateValidationError("Status STALE requires at least one stale knowledge item in results", field="results")

    @property
    def is_success(self) -> bool:
        return self.status == GateStatus.SUCCESS

    @property
    def is_abstention(self) -> bool:
        return self.status == GateStatus.ABSTAIN or (self.abstention is not None and self.abstention.abstained)

    @property
    def source_references(self) -> List[str]:
        """Extract unique source IDs referenced across results."""
        refs = {item.provenance.source_id for item in self.results if item.provenance.source_id}
        return sorted(list(refs))

    @property
    def event_references(self) -> List[str]:
        """Extract unique originating event IDs referenced across results."""
        refs = {item.provenance.originating_event_id for item in self.results if item.provenance.originating_event_id}
        return sorted(list(refs))

    @property
    def evidence_references(self) -> List[str]:
        """Extract unique evidence IDs referenced across results."""
        refs = {item.provenance.evidence_id for item in self.results if item.provenance.evidence_id}
        return sorted(list(refs))

    def to_dict(self) -> Dict[str, Any]:
        serialized_results = [item.to_dict() for item in self.results]
        return {
            "request_id": self.request_id,
            "requestId": self.request_id,
            "status": self.status.value,
            "results": serialized_results,
            "evidence": serialized_results,
            "abstention": self.abstention.to_dict() if self.abstention else None,
            "reason": self.reason,
            "contradictions": [c.to_dict() for c in self.contradictions],
            "metadata": self.metadata,
            "task_id": self.task_id,
            "taskId": self.task_id,
            "execution_id": self.execution_id,
            "executionId": self.execution_id,
            "correlation_id": self.correlation_id,
            "correlationId": self.correlation_id,
            "source_references": self.source_references,
            "event_references": self.event_references,
            "evidence_references": self.evidence_references,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "NeuralQueryResponse":
        if not isinstance(data, dict):
            raise GateValidationError("Query response payload must be a dictionary")

        results_data = data.get("results", data.get("evidence", []))
        items = [NeuralKnowledgeItem.from_dict(item) for item in results_data]

        abst_data = data.get("abstention")
        abstention = AbstentionMetadata.from_dict(abst_data) if abst_data else None

        contra_data = data.get("contradictions", [])
        contradictions = [ContradictionItem.from_dict(c) for c in contra_data]

        return cls(
            request_id=data.get("request_id", data.get("requestId", "")),
            status=GateStatus.from_str(data.get("status", GateStatus.INTERNAL_ERROR.value)),
            results=items,
            abstention=abstention,
            reason=data.get("reason"),
            contradictions=contradictions,
            metadata=data.get("metadata", {}),
            task_id=data.get("task_id", data.get("taskId")),
            execution_id=data.get("execution_id", data.get("executionId")),
            correlation_id=data.get("correlation_id", data.get("correlationId")),
        )

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2, ensure_ascii=False)

    @classmethod
    def from_json(cls, json_str: str) -> "NeuralQueryResponse":
        try:
            data = json.loads(json_str)
        except Exception as e:
            raise GateValidationError(f"Invalid JSON string for NeuralQueryResponse: {e}")
        return cls.from_dict(data)


@dataclass
class TaskEvidence:
    """
    Evidence record verifying the successful execution and governance checks of a PDL task.
    Directly compatible with PDL's NeuralTaskStatePayload evidence schema.
    """
    validation_passed: bool
    worktree_clean: bool
    push_succeeded: bool
    remote_verified: bool
    runtime_verified: Optional[bool] = None
    test_summary: Optional[Dict[str, int]] = None
    delivery_verified: Optional[bool] = None
    governance_verified: Optional[bool] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "validationPassed": self.validation_passed,
            "worktreeClean": self.worktree_clean,
            "pushSucceeded": self.push_succeeded,
            "remoteVerified": self.remote_verified,
            "runtimeVerified": self.runtime_verified,
            "testSummary": self.test_summary,
            "deliveryVerified": self.delivery_verified,
            "governanceVerified": self.governance_verified,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "TaskEvidence":
        if not isinstance(data, dict):
            raise GateValidationError("TaskEvidence must be a dictionary", field="evidence")
        return cls(
            validation_passed=bool(data.get("validationPassed", data.get("validation_passed", False))),
            worktree_clean=bool(data.get("worktreeClean", data.get("worktree_clean", False))),
            push_succeeded=bool(data.get("pushSucceeded", data.get("push_succeeded", False))),
            remote_verified=bool(data.get("remoteVerified", data.get("remote_verified", False))),
            runtime_verified=data.get("runtimeVerified", data.get("runtime_verified")),
            test_summary=data.get("testSummary", data.get("test_summary")),
            delivery_verified=data.get("deliveryVerified", data.get("delivery_verified")),
            governance_verified=data.get("governanceVerified", data.get("governance_verified")),
        )


@dataclass
class CandidateFinding:
    """
    Candidate lesson or pattern discovered during task execution, submitted for potential institutionalization.
    """
    finding_type: KnowledgeClass
    title: str
    statement: str
    scope: str = "PROJECT"  # 'PROJECT' or 'GLOBAL'
    confidence: float = 1.0

    def __post_init__(self) -> None:
        self.title = _validate_non_empty_str(self.title, "title")
        self.statement = _validate_non_empty_str(self.statement, "statement")
        self.finding_type = KnowledgeClass.from_str(self.finding_type)

        norm_scope = str(self.scope).strip().upper()
        if norm_scope not in ("PROJECT", "GLOBAL"):
            raise GateValidationError(f"Candidate finding scope must be 'PROJECT' or 'GLOBAL', got '{self.scope}'")
        self.scope = norm_scope

    def to_dict(self) -> Dict[str, Any]:
        return {
            "finding_type": self.finding_type.value,
            "title": self.title,
            "statement": self.statement,
            "scope": self.scope,
            "confidence": self.confidence,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "CandidateFinding":
        if not isinstance(data, dict):
            raise GateValidationError("Candidate finding must be a dictionary")
        return cls(
            finding_type=KnowledgeClass.from_str(data.get("finding_type", KnowledgeClass.LESSON.value)),
            title=data.get("title", ""),
            statement=data.get("statement", ""),
            scope=data.get("scope", "PROJECT"),
            confidence=float(data.get("confidence", 1.0)),
        )


@dataclass
class NeuralExperienceRecord:
    """
    Contract for a PDL -> PUB Neural post-task experience writeback.
    Fully compatible with PDL's NeuralTaskStatePayload while formalizing candidate findings,
    governance evidence, and deterministic serialization.
    """
    task_id: str
    project_id: str
    repository: str
    branch: str
    status: TaskExecutionStatus
    objective: str
    evidence: TaskEvidence
    completed_at: str
    occurred_at: Optional[str] = None
    ingested_at: Optional[str] = None
    commit_sha: Optional[str] = None
    remote_sha: Optional[str] = None
    agent_id: Optional[str] = None
    changed_files: List[str] = field(default_factory=list)
    candidate_findings: List[CandidateFinding] = field(default_factory=list)
    consumed_knowledge_ids: List[str] = field(default_factory=list)
    trace: Optional[Dict[str, Any]] = None
    ingestion_source: str = "pdl-bidirectional-gate"
    execution_id: Optional[str] = None
    correlation_id: Optional[str] = None

    def __post_init__(self) -> None:
        self.task_id = _validate_non_empty_str(self.task_id, "task_id")
        self.project_id = _validate_non_empty_str(self.project_id, "project_id")
        self.repository = _validate_non_empty_str(self.repository, "repository")
        self.branch = _validate_non_empty_str(self.branch, "branch")
        self.objective = _validate_non_empty_str(self.objective, "objective")
        self.completed_at = _validate_iso_timestamp(self.completed_at, "completed_at")
        if self.occurred_at is not None:
            self.occurred_at = _validate_iso_timestamp(self.occurred_at, "occurred_at")
        if self.ingested_at is not None:
            self.ingested_at = _validate_iso_timestamp(self.ingested_at, "ingested_at")
        self.ingestion_source = _validate_non_empty_str(self.ingestion_source, "ingestion_source")
        self.status = TaskExecutionStatus.from_str(self.status)

        if self.execution_id is not None:
            self.execution_id = str(self.execution_id).strip()
        if self.correlation_id is not None:
            self.correlation_id = str(self.correlation_id).strip()

        if not isinstance(self.evidence, TaskEvidence):
            raise GateValidationError("evidence must be a TaskEvidence instance", field="evidence")

        if not isinstance(self.changed_files, (list, tuple)):
            raise GateValidationError("changed_files must be a list of strings", field="changed_files")

        if not isinstance(self.consumed_knowledge_ids, (list, tuple)):
            raise GateValidationError("consumed_knowledge_ids must be a list of strings", field="consumed_knowledge_ids")
        self.consumed_knowledge_ids = [str(k).strip() for k in self.consumed_knowledge_ids if str(k).strip()]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "taskId": self.task_id,
            "task_id": self.task_id,
            "executionId": self.execution_id,
            "execution_id": self.execution_id,
            "correlationId": self.correlation_id,
            "correlation_id": self.correlation_id,
            "projectId": self.project_id,
            "project_id": self.project_id,
            "repository": self.repository,
            "branch": self.branch,
            "commitSha": self.commit_sha,
            "commit_sha": self.commit_sha,
            "remoteSha": self.remote_sha,
            "remote_sha": self.remote_sha,
            "status": self.status.value,
            "objective": self.objective,
            "agentId": self.agent_id,
            "agent_id": self.agent_id,
            "changedFiles": self.changed_files,
            "changed_files": self.changed_files,
            "evidence": self.evidence.to_dict(),
            "candidateFindings": [f.to_dict() for f in self.candidate_findings],
            "candidate_findings": [f.to_dict() for f in self.candidate_findings],
            "consumedKnowledgeIds": list(self.consumed_knowledge_ids),
            "consumed_knowledge_ids": list(self.consumed_knowledge_ids),
            "trace": self.trace,
            "completedAt": self.completed_at,
            "completed_at": self.completed_at,
            "occurredAt": self.occurred_at,
            "occurred_at": self.occurred_at,
            "ingestedAt": self.ingested_at,
            "ingested_at": self.ingested_at,
            "ingestionSource": self.ingestion_source,
            "ingestion_source": self.ingestion_source,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "NeuralExperienceRecord":
        if not isinstance(data, dict):
            raise GateValidationError("Experience payload must be a dictionary")

        evidence_raw = data.get("evidence")
        if evidence_raw is None:
            raise GateValidationError("Field 'evidence' is mandatory in experience payload", field="evidence")

        findings_raw = data.get("candidateFindings", data.get("candidate_findings", []))
        findings = [CandidateFinding.from_dict(f) for f in findings_raw]

        consumed_raw = data.get("consumedKnowledgeIds", data.get("consumed_knowledge_ids", []))
        if not isinstance(consumed_raw, (list, tuple)):
            consumed_raw = []

        return cls(
            task_id=data.get("taskId", data.get("task_id", "")),
            project_id=data.get("projectId", data.get("project_id", "")),
            repository=data.get("repository", ""),
            branch=data.get("branch", ""),
            commit_sha=data.get("commitSha", data.get("commit_sha")),
            remote_sha=data.get("remoteSha", data.get("remote_sha")),
            status=TaskExecutionStatus.from_str(data.get("status", "")),
            objective=data.get("objective", ""),
            agent_id=data.get("agentId", data.get("agent_id")),
            changed_files=data.get("changedFiles", data.get("changed_files", [])),
            evidence=TaskEvidence.from_dict(evidence_raw),
            candidate_findings=findings,
            consumed_knowledge_ids=list(consumed_raw),
            trace=data.get("trace"),
            completed_at=data.get("completedAt", data.get("completed_at", "")),
            occurred_at=data.get("occurredAt", data.get("occurred_at")),
            ingested_at=data.get("ingestedAt", data.get("ingested_at")),
            ingestion_source=data.get("ingestionSource", data.get("ingestion_source", "pdl-bidirectional-gate")),
            execution_id=data.get("executionId", data.get("execution_id")),
            correlation_id=data.get("correlationId", data.get("correlation_id")),
        )

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2, ensure_ascii=False)

    @classmethod
    def from_json(cls, json_str: str) -> "NeuralExperienceRecord":
        try:
            data = json.loads(json_str)
        except Exception as e:
            raise GateValidationError(f"Invalid JSON string for NeuralExperienceRecord: {e}")
        return cls.from_dict(data)


@dataclass
class GateFailure:
    """
    Explicit failure model representation for the Neural Knowledge Gate.
    Standardizes error reporting across transport boundaries.
    """
    status: GateStatus
    reason: str
    request_id: Optional[str] = None
    details: Optional[Dict[str, Any]] = None
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def __post_init__(self) -> None:
        self.status = GateStatus.from_str(self.status)
        self.reason = _validate_non_empty_str(self.reason, "reason")

    def to_dict(self) -> Dict[str, Any]:
        return {
            "status": self.status.value,
            "reason": self.reason,
            "request_id": self.request_id,
            "details": self.details or {},
            "timestamp": self.timestamp,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "GateFailure":
        if not isinstance(data, dict):
            raise GateValidationError("GateFailure data must be a dictionary")
        return cls(
            status=GateStatus.from_str(data.get("status", GateStatus.INTERNAL_ERROR.value)),
            reason=data.get("reason", "Unknown failure"),
            request_id=data.get("request_id"),
            details=data.get("details"),
            timestamp=data.get("timestamp", datetime.now(timezone.utc).isoformat()),
        )


@dataclass
class ExperienceIngestionResult:
    """
    Contract for the outcome of a post-task experience writeback into PUB Neural.
    Preserves explicit status separation (ACCEPTED, DUPLICATE, INVALID_REQUEST, UNAVAILABLE, INTERNAL_ERROR).
    """
    status: ExperienceWritebackStatus
    task_id: str
    event_id: Optional[str] = None
    idempotency_key: Optional[str] = None
    is_duplicate: bool = False
    candidate_findings_count: int = 0
    recorded_at: Optional[str] = None
    reason: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    execution_id: Optional[str] = None
    correlation_id: Optional[str] = None

    def __post_init__(self) -> None:
        self.status = ExperienceWritebackStatus.from_str(self.status)
        self.task_id = _validate_non_empty_str(self.task_id, "task_id") if self.task_id else "unknown"
        if self.execution_id is not None:
            self.execution_id = str(self.execution_id).strip()
        if self.correlation_id is not None:
            self.correlation_id = str(self.correlation_id).strip()

    @property
    def is_accepted(self) -> bool:
        return self.status == ExperienceWritebackStatus.ACCEPTED

    def to_dict(self) -> Dict[str, Any]:
        return {
            "status": self.status.value,
            "taskId": self.task_id,
            "task_id": self.task_id,
            "executionId": self.execution_id,
            "execution_id": self.execution_id,
            "correlationId": self.correlation_id,
            "correlation_id": self.correlation_id,
            "eventId": self.event_id,
            "event_id": self.event_id,
            "idempotencyKey": self.idempotency_key,
            "idempotency_key": self.idempotency_key,
            "isDuplicate": self.is_duplicate,
            "is_duplicate": self.is_duplicate,
            "candidateFindingsCount": self.candidate_findings_count,
            "candidate_findings_count": self.candidate_findings_count,
            "recordedAt": self.recorded_at,
            "recorded_at": self.recorded_at,
            "reason": self.reason,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ExperienceIngestionResult":
        if not isinstance(data, dict):
            raise GateValidationError("ExperienceIngestionResult data must be a dictionary")
        return cls(
            status=ExperienceWritebackStatus.from_str(data.get("status", ExperienceWritebackStatus.INTERNAL_ERROR.value)),
            task_id=data.get("taskId", data.get("task_id", "unknown")),
            event_id=data.get("eventId", data.get("event_id")),
            idempotency_key=data.get("idempotencyKey", data.get("idempotency_key")),
            is_duplicate=bool(data.get("isDuplicate", data.get("is_duplicate", False))),
            candidate_findings_count=int(data.get("candidateFindingsCount", data.get("candidate_findings_count", 0))),
            recorded_at=data.get("recordedAt", data.get("recorded_at")),
            reason=data.get("reason"),
            metadata=data.get("metadata", {}),
            execution_id=data.get("executionId", data.get("execution_id")),
            correlation_id=data.get("correlationId", data.get("correlation_id")),
        )

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2, ensure_ascii=False)

    @classmethod
    def from_json(cls, json_str: str) -> "ExperienceIngestionResult":
        try:
            data = json.loads(json_str)
        except Exception as e:
            raise GateValidationError(f"Invalid JSON string for ExperienceIngestionResult: {e}")
        return cls.from_dict(data)
