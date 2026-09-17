from dataclasses import dataclass
from os import getenv
from typing import Any, List, Optional


@dataclass(frozen=True)
class AbstentionDecision:
    """Auditable outcome of the retrieval confidence gate."""

    accepted: bool
    reason: str
    top_dense_similarity: Optional[float]
    top_rrf_score: Optional[float]
    lexical_candidate_count: int
    dense_candidate_count: int
    graph_candidate_count: int = 0
    top_graph_score: Optional[float] = None


@dataclass(frozen=True)
class RetrievalAbstentionPolicy:
    """
    Optional confidence gate for hybrid retrieval.

    The policy is intentionally disabled by default so V0.1 callers preserve
    backwards compatibility. When enabled, a minimum dense cosine similarity
    threshold is mandatory. Exact lexical evidence may be accepted without a
    dense threshold because lexical identifiers are a legitimate retrieval
    signal for this corpus.

    Thresholds MUST be calibrated from an independent calibration split before
    being enabled for production use. Holdout queries must remain untouched.
    """

    enabled: bool = False
    min_dense_similarity: Optional[float] = None
    accept_on_lexical_candidate: bool = True

    def __post_init__(self) -> None:
        if self.min_dense_similarity is not None and not 0.0 <= self.min_dense_similarity <= 1.0:
            raise ValueError("min_dense_similarity must be between 0.0 and 1.0")
        if self.enabled and self.min_dense_similarity is None:
            raise ValueError(
                "Enabled abstention requires min_dense_similarity. "
                "Calibrate a threshold before enabling the gate."
            )

    @classmethod
    def disabled(cls) -> "RetrievalAbstentionPolicy":
        return cls(enabled=False)

    @classmethod
    def from_environment(cls) -> "RetrievalAbstentionPolicy":
        """Build a policy from explicit deployment environment variables."""
        enabled = getenv("PUB_NEURAL_ABSTENTION_ENABLED", "0").strip().lower() in {
            "1",
            "true",
            "yes",
            "on",
        }
        raw_threshold = getenv("PUB_NEURAL_MIN_DENSE_SIMILARITY")
        threshold = float(raw_threshold) if raw_threshold is not None and raw_threshold.strip() else None

        accept_lexical = getenv("PUB_NEURAL_ABSTENTION_ACCEPT_LEXICAL", "1").strip().lower() in {
            "1",
            "true",
            "yes",
            "on",
        }
        return cls(
            enabled=enabled,
            min_dense_similarity=threshold,
            accept_on_lexical_candidate=accept_lexical,
        )

    def evaluate(
        self,
        lexical_results: List[dict[str, Any]],
        dense_results: List[dict[str, Any]],
        fused_results: List[Any],
        graph_results: Optional[List[Any]] = None,
    ) -> AbstentionDecision:
        """Evaluate whether hybrid retrieval has sufficient evidence to answer."""
        lexical_count = len(lexical_results)
        dense_count = len(dense_results)
        graph_count = len(graph_results) if graph_results else 0

        top_dense_similarity: Optional[float] = None
        if dense_results:
            distance = float(dense_results[0]["cosine_distance"])
            top_dense_similarity = 1.0 - distance

        top_rrf_score: Optional[float] = None
        if fused_results:
            top_rrf_score = float(fused_results[0].rrf_score)

        top_graph_score: Optional[float] = None
        if graph_results:
            top_graph_score = float(getattr(graph_results[0], "graph_score", graph_results[0].get("graph_score", 0.0)))

        if not self.enabled:
            return AbstentionDecision(
                accepted=True,
                reason="POLICY_DISABLED",
                top_dense_similarity=top_dense_similarity,
                top_rrf_score=top_rrf_score,
                lexical_candidate_count=lexical_count,
                dense_candidate_count=dense_count,
                graph_candidate_count=graph_count,
                top_graph_score=top_graph_score,
            )

        if self.accept_on_lexical_candidate and lexical_count > 0:
            return AbstentionDecision(
                accepted=True,
                reason="LEXICAL_EVIDENCE_PRESENT",
                top_dense_similarity=top_dense_similarity,
                top_rrf_score=top_rrf_score,
                lexical_candidate_count=lexical_count,
                dense_candidate_count=dense_count,
                graph_candidate_count=graph_count,
                top_graph_score=top_graph_score,
            )

        if top_dense_similarity is None:
            return AbstentionDecision(
                accepted=False,
                reason="NO_DENSE_CANDIDATE",
                top_dense_similarity=None,
                top_rrf_score=top_rrf_score,
                lexical_candidate_count=lexical_count,
                dense_candidate_count=dense_count,
                graph_candidate_count=graph_count,
                top_graph_score=top_graph_score,
            )

        assert self.min_dense_similarity is not None
        if top_dense_similarity < self.min_dense_similarity:
            return AbstentionDecision(
                accepted=False,
                reason="DENSE_SIMILARITY_BELOW_THRESHOLD",
                top_dense_similarity=top_dense_similarity,
                top_rrf_score=top_rrf_score,
                lexical_candidate_count=lexical_count,
                dense_candidate_count=dense_count,
                graph_candidate_count=graph_count,
                top_graph_score=top_graph_score,
            )

        return AbstentionDecision(
            accepted=True,
            reason="DENSE_SIMILARITY_ABOVE_THRESHOLD",
            top_dense_similarity=top_dense_similarity,
            top_rrf_score=top_rrf_score,
            lexical_candidate_count=lexical_count,
            dense_candidate_count=dense_count,
            graph_candidate_count=graph_count,
            top_graph_score=top_graph_score,
        )
