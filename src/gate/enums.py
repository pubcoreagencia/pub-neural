"""
Canonical enums and types for the Bidirectional Neural Knowledge Gate.
Defines closed sets for knowledge classes, gate statuses, authority levels,
freshness states, conflict states, and execution statuses.
"""

from enum import Enum
from typing import Any


class KnowledgeClass(str, Enum):
    """
    Canonical knowledge classes recognized by PUB Neural and PDL.
    Closed enum: arbitrary string values are strictly rejected.
    """
    DECISION = "DECISION"
    RULE = "RULE"
    GOVERNANCE = "GOVERNANCE"
    PATTERN = "PATTERN"
    LESSON = "LESSON"
    SKILL = "SKILL"
    PROJECT = "PROJECT"
    REPOSITORY = "REPOSITORY"

    @classmethod
    def from_str(cls, value: Any) -> "KnowledgeClass":
        if isinstance(value, cls):
            return value
        if hasattr(value, "value") and isinstance(value.value, str):
            value = value.value
        if not isinstance(value, str):
            raise TypeError(f"KnowledgeClass must be a string, got {type(value).__name__}")
        normalized = value.strip().upper()
        try:
            return cls(normalized)
        except ValueError:
            valid = ", ".join(k.value for k in cls)
            raise ValueError(f"Invalid knowledge class '{value}'. Must be one of: {valid}")


class GateStatus(str, Enum):
    """
    Auditable status of a Neural Knowledge Gate interaction.
    Distinguishes successful retrieval from explicit abstention, conflicts,
    staleness, and the complete failure model.
    """
    SUCCESS = "SUCCESS"                  # Valid knowledge matched and returned
    NO_MATCH = "NO_MATCH"                # Query executed; zero relevant matches found
    ABSTAIN = "ABSTAIN"                  # Confidence/abstention gate declined to return low-relevance results
    CONFLICT = "CONFLICT"                # Contradictory or blocked knowledge detected
    STALE = "STALE"                      # Retrieved knowledge is stale/divergent from active commit/branch
    UNAVAILABLE = "UNAVAILABLE"          # Neural backend/database unconfigured or unreachable
    INVALID_REQUEST = "INVALID_REQUEST"  # Malformed request payload or validation failure
    INTERNAL_ERROR = "INTERNAL_ERROR"    # Unexpected internal gate processing error

    @classmethod
    def from_str(cls, value: Any) -> "GateStatus":
        if isinstance(value, cls):
            return value
        if hasattr(value, "value") and isinstance(value.value, str):
            value = value.value
        if not isinstance(value, str):
            raise TypeError(f"GateStatus must be a string, got {type(value).__name__}")
        normalized = value.strip().upper()
        try:
            return cls(normalized)
        except ValueError:
            valid = ", ".join(s.value for s in cls)
            raise ValueError(f"Invalid gate status '{value}'. Must be one of: {valid}")


class AuthorityLevel(str, Enum):
    """
    Strict authority hierarchy for PUB Neural knowledge:
    RUNTIME_DIRECT_EVIDENCE (5) > REAL_EXECUTION (4) > TEST_EVIDENCE (3) > VALIDATED_KNOWLEDGE (2) > HISTORICAL_MEMORY (1).

    CRITICAL ARCHITECTURAL PRINCIPLE:
    Neural knowledge is strictly DATA. Retrieved knowledge never substitutes
    for human authority, governance mandates, runtime truth, or direct evidence.
    """
    RUNTIME_DIRECT_EVIDENCE = "RUNTIME_DIRECT_EVIDENCE"
    REAL_EXECUTION = "REAL_EXECUTION"
    TEST_EVIDENCE = "TEST_EVIDENCE"
    VALIDATED_KNOWLEDGE = "VALIDATED_KNOWLEDGE"
    HISTORICAL_MEMORY = "HISTORICAL_MEMORY"

    @property
    def rank(self) -> int:
        ranks = {
            AuthorityLevel.HISTORICAL_MEMORY: 1,
            AuthorityLevel.VALIDATED_KNOWLEDGE: 2,
            AuthorityLevel.TEST_EVIDENCE: 3,
            AuthorityLevel.REAL_EXECUTION: 4,
            AuthorityLevel.RUNTIME_DIRECT_EVIDENCE: 5,
        }
        return ranks[self]

    def is_authoritative_over(self, other: "AuthorityLevel") -> bool:
        """Evaluate if this authority level strictly outranks another."""
        return self.rank > other.rank

    @classmethod
    def from_str(cls, value: Any) -> "AuthorityLevel":
        if isinstance(value, cls):
            return value
        if hasattr(value, "value") and isinstance(value.value, str):
            value = value.value
        if not isinstance(value, str):
            raise TypeError(f"AuthorityLevel must be a string, got {type(value).__name__}")
        normalized = value.strip().upper()
        try:
            return cls(normalized)
        except ValueError:
            valid = ", ".join(a.value for a in cls)
            raise ValueError(f"Invalid authority level '{value}'. Must be one of: {valid}")


class FreshnessState(str, Enum):
    """
    Auditable freshness state of a knowledge item.
    Enforces clear separation between 'not found', 'found but stale', and 'unavailable'.
    """
    VALID = "VALID"
    STALE = "STALE"
    UNKNOWN = "UNKNOWN"
    EXPIRED = "EXPIRED"

    @classmethod
    def from_str(cls, value: Any) -> "FreshnessState":
        if isinstance(value, cls):
            return value
        if hasattr(value, "value") and isinstance(value.value, str):
            value = value.value
        if not isinstance(value, str):
            raise TypeError(f"FreshnessState must be a string, got {type(value).__name__}")
        normalized = value.strip().upper()
        try:
            return cls(normalized)
        except ValueError:
            valid = ", ".join(f.value for f in cls)
            raise ValueError(f"Invalid freshness state '{value}'. Must be one of: {valid}")


class ConflictState(str, Enum):
    """
    Conflict state aligning with pub_neural.neural_conflict_state.
    """
    RESOLVED = "RESOLVED"
    CONTRADICTORY = "CONTRADICTORY"
    BLOCKED = "BLOCKED"
    SUPERSEDED = "SUPERSEDED"
    DEPRECATED = "DEPRECATED"
    REJECTED = "REJECTED"

    @classmethod
    def from_str(cls, value: Any) -> "ConflictState":
        if isinstance(value, cls):
            return value
        if hasattr(value, "value") and isinstance(value.value, str):
            value = value.value
        if not isinstance(value, str):
            raise TypeError(f"ConflictState must be a string, got {type(value).__name__}")
        normalized = value.strip().upper()
        try:
            return cls(normalized)
        except ValueError:
            valid = ", ".join(c.value for c in cls)
            raise ValueError(f"Invalid conflict state '{value}'. Must be one of: {valid}")


class PromotionState(str, Enum):
    """
    Promotion lifecycle aligning with pub_neural.neural_promotion_state.
    """
    CAPTURED = "CAPTURED"
    OBSERVED = "OBSERVED"
    EXTRACTED = "EXTRACTED"
    CANDIDATE = "CANDIDATE"
    VALIDATED = "VALIDATED"
    ADOPTED = "ADOPTED"
    INSTITUTIONAL_CANDIDATE = "INSTITUTIONAL_CANDIDATE"
    INSTITUTIONAL = "INSTITUTIONAL"

    @classmethod
    def from_str(cls, value: Any) -> "PromotionState":
        if isinstance(value, cls):
            return value
        if hasattr(value, "value") and isinstance(value.value, str):
            value = value.value
        if not isinstance(value, str):
            raise TypeError(f"PromotionState must be a string, got {type(value).__name__}")
        normalized = value.strip().upper()
        try:
            return cls(normalized)
        except ValueError:
            valid = ", ".join(p.value for p in cls)
            raise ValueError(f"Invalid promotion state '{value}'. Must be one of: {valid}")


class TaskExecutionStatus(str, Enum):
    """
    Execution outcome status reported by PDL persistence gate.
    """
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"
    TIMED_OUT = "TIMED_OUT"

    @classmethod
    def from_str(cls, value: Any) -> "TaskExecutionStatus":
        if isinstance(value, cls):
            return value
        if hasattr(value, "value") and isinstance(value.value, str):
            value = value.value
        if not isinstance(value, str):
            raise TypeError(f"TaskExecutionStatus must be a string, got {type(value).__name__}")
        normalized = value.strip().upper()
        try:
            return cls(normalized)
        except ValueError:
            valid = ", ".join(t.value for t in cls)
            raise ValueError(f"Invalid task status '{value}'. Must be one of: {valid}")


class AgentRole(str, Enum):
    """
    Operating persona / role within the PDL and Neural ecosystem.
    """
    CHIEF_OF_STAFF = "chief-of-staff"
    ARCHITECT = "architect"
    DEVELOPER = "developer"
    REVIEWER = "reviewer"
    QA_ENGINEER = "qa-engineer"
    RESEARCHER = "researcher"

    @classmethod
    def from_str(cls, value: Any) -> "AgentRole":
        if isinstance(value, cls):
            return value
        if hasattr(value, "value") and isinstance(value.value, str):
            value = value.value
        if not isinstance(value, str):
            raise TypeError(f"AgentRole must be a string, got {type(value).__name__}")
        normalized = value.strip().lower().replace("_", "-")
        for role in cls:
            if role.value == normalized:
                return role
        valid = ", ".join(r.value for r in cls)
        raise ValueError(f"Invalid agent role '{value}'. Must be one of: {valid}")
