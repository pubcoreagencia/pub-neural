"""
Bidirectional Neural Knowledge Gate — Contracts and Boundaries Module.
Provides canonical DTOs, Enums, Validators, and the NeuralQueryService
for the PDL <-> PUB Neural interaction.
"""

from .enums import (
    AgentRole,
    AuthorityLevel,
    ConflictState,
    FreshnessState,
    GateStatus,
    KnowledgeClass,
    PromotionState,
    TaskExecutionStatus,
)
from .exceptions import (
    GateContractError,
    GateTransportError,
    GateValidationError,
)
from .models import (
    AbstentionMetadata,
    AuthorityMetadata,
    CallerIdentity,
    CandidateFinding,
    ContradictionItem,
    FreshnessMetadata,
    GateFailure,
    NeuralExperienceRecord,
    NeuralKnowledgeItem,
    NeuralQueryRequest,
    NeuralQueryResponse,
    ProvenanceMetadata,
    TaskEvidence,
)
from .retrieval_adapter import (
    HybridSearchAdapter,
    NeuralResultMapper,
    NeuralRetrievalEngine,
    RetrievalBatch,
)
from .service import NeuralQueryService

__all__ = [
    # Enums
    "AgentRole",
    "AuthorityLevel",
    "ConflictState",
    "FreshnessState",
    "GateStatus",
    "KnowledgeClass",
    "PromotionState",
    "TaskExecutionStatus",
    # Exceptions
    "GateContractError",
    "GateTransportError",
    "GateValidationError",
    # Models / Contracts
    "AbstentionMetadata",
    "AuthorityMetadata",
    "CallerIdentity",
    "CandidateFinding",
    "ContradictionItem",
    "FreshnessMetadata",
    "GateFailure",
    "NeuralExperienceRecord",
    "NeuralKnowledgeItem",
    "NeuralQueryRequest",
    "NeuralQueryResponse",
    "ProvenanceMetadata",
    "TaskEvidence",
    # Retrieval Adapter & Service Boundary
    "HybridSearchAdapter",
    "NeuralQueryService",
    "NeuralResultMapper",
    "NeuralRetrievalEngine",
    "RetrievalBatch",
]
