"""Experimental evidence-aware decision primitives for STEP 2E.2.

This module is intentionally policy-driven and does not alter HybridSearchEngine.
It separates structural evidence checks from calibrated answerability decisions.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional


class EvidenceDecision(str, Enum):
    ANSWER = "ANSWER"
    ABSTAIN = "ABSTAIN"
    ESCALATE = "ESCALATE"


class ReasonCode(str, Enum):
    SUFFICIENT_EVIDENCE = "SUFFICIENT_EVIDENCE"
    INSUFFICIENT_EVIDENCE = "INSUFFICIENT_EVIDENCE"
    OUT_OF_SCOPE = "OUT_OF_SCOPE"
    CONTRADICTORY_EVIDENCE = "CONTRADICTORY_EVIDENCE"
    LOW_VERIFIER_SUPPORT = "LOW_VERIFIER_SUPPORT"
    LOW_PROVENANCE_QUALITY = "LOW_PROVENANCE_QUALITY"
    INSUFFICIENT_COVERAGE = "INSUFFICIENT_COVERAGE"
    ESCALATION_REQUIRED = "ESCALATION_REQUIRED"


@dataclass(frozen=True)
class EvidenceSignals:
    """Signals supplied by retrieval and/or an external verifier.

    Scores are observations, not probabilities. No threshold is defined here.
    """

    evidence_coverage: Optional[float]
    verifier_score: Optional[float]
    scope_compatible: bool
    contradiction: bool
    provenance_quality: Optional[float]


@dataclass(frozen=True)
class EvidencePolicy:
    """Explicit experimental policy. Values must be calibrated externally."""

    min_coverage: float
    min_verifier_score: float
    min_provenance_quality: float = 0.0
    allow_missing_verifier: bool = False

    def __post_init__(self) -> None:
        for name, value in (
            ("min_coverage", self.min_coverage),
            ("min_verifier_score", self.min_verifier_score),
            ("min_provenance_quality", self.min_provenance_quality),
        ):
            if not 0.0 <= value <= 1.0:
                raise ValueError(f"{name} must be between 0 and 1")


@dataclass(frozen=True)
class EvidenceAssessment:
    decision: EvidenceDecision
    reason_codes: List[ReasonCode] = field(default_factory=list)
    policy_version: str = "step2e2-experimental-v0"


def assess_evidence(
    signals: EvidenceSignals,
    policy: EvidencePolicy,
    *,
    policy_version: str = "step2e2-experimental-v0",
) -> EvidenceAssessment:
    """Apply an explicitly supplied experimental policy to evidence signals.

    Precedence is deliberately conservative:
      1. contradiction -> ESCALATE;
      2. scope failure -> ABSTAIN;
      3. missing/low provenance -> ABSTAIN;
      4. missing/low coverage -> ABSTAIN;
      5. missing verifier -> ESCALATE unless explicitly allowed;
      6. low verifier score -> ABSTAIN;
      7. all gates pass -> ANSWER.

    The function never consumes dense similarity or RRF as answerability scores.
    """
    if signals.contradiction:
        return EvidenceAssessment(
            EvidenceDecision.ESCALATE,
            [ReasonCode.CONTRADICTORY_EVIDENCE, ReasonCode.ESCALATION_REQUIRED],
            policy_version,
        )

    if not signals.scope_compatible:
        return EvidenceAssessment(
            EvidenceDecision.ABSTAIN,
            [ReasonCode.OUT_OF_SCOPE],
            policy_version,
        )

    if (
        signals.provenance_quality is None
        or signals.provenance_quality < policy.min_provenance_quality
    ):
        return EvidenceAssessment(
            EvidenceDecision.ABSTAIN,
            [ReasonCode.LOW_PROVENANCE_QUALITY],
            policy_version,
        )

    if (
        signals.evidence_coverage is None
        or signals.evidence_coverage < policy.min_coverage
    ):
        return EvidenceAssessment(
            EvidenceDecision.ABSTAIN,
            [ReasonCode.INSUFFICIENT_COVERAGE, ReasonCode.INSUFFICIENT_EVIDENCE],
            policy_version,
        )

    if signals.verifier_score is None:
        if policy.allow_missing_verifier:
            return EvidenceAssessment(
                EvidenceDecision.ESCALATE,
                [ReasonCode.ESCALATION_REQUIRED],
                policy_version,
            )
        return EvidenceAssessment(
            EvidenceDecision.ESCALATE,
            [ReasonCode.LOW_VERIFIER_SUPPORT, ReasonCode.ESCALATION_REQUIRED],
            policy_version,
        )

    if signals.verifier_score < policy.min_verifier_score:
        return EvidenceAssessment(
            EvidenceDecision.ABSTAIN,
            [ReasonCode.LOW_VERIFIER_SUPPORT],
            policy_version,
        )

    return EvidenceAssessment(
        EvidenceDecision.ANSWER,
        [ReasonCode.SUFFICIENT_EVIDENCE],
        policy_version,
    )
