#!/usr/bin/env python3
"""Calibrate the V0.3 dense-similarity abstention threshold.

Input JSON must contain a list of records with:
  - query_id
  - evaluation_split: CALIBRATION or HOLDOUT
  - query_type
  - dense_top1_similarity

Threshold selection is strictly calibration-only. HOLDOUT records are rejected
for threshold selection so the script cannot silently tune on the locked split.
"""

from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path
from typing import Any


def _load_records(path: Path) -> list[dict[str, Any]]:
    with path.open("r", encoding="utf-8") as handle:
        payload = json.load(handle)
    if not isinstance(payload, list):
        raise ValueError("Input must be a JSON list of query measurement records.")
    return payload


def _validate_records(records: list[dict[str, Any]]) -> None:
    required = {"query_id", "evaluation_split", "query_type", "dense_top1_similarity"}
    for record in records:
        missing = required.difference(record)
        if missing:
            raise ValueError(
                f"Record {record.get('query_id', '<unknown>')} is missing: {sorted(missing)}"
            )
        similarity = float(record["dense_top1_similarity"])
        if not math.isfinite(similarity) or not 0.0 <= similarity <= 1.0:
            raise ValueError(
                f"Invalid dense_top1_similarity for {record['query_id']}: {similarity}"
            )
        split = str(record["evaluation_split"]).upper()
        if split not in {"CALIBRATION", "HOLDOUT"}:
            raise ValueError(
                f"Unsupported evaluation_split for {record['query_id']}: {split}"
            )


def _candidate_thresholds(values: list[float]) -> list[float]:
    unique = sorted(set(values))
    if not unique:
        return []

    candidates = {0.0, 1.0}
    candidates.update(unique)
    for left, right in zip(unique, unique[1:]):
        midpoint = (left + right) / 2.0
        candidates.add(midpoint)
    return sorted(candidates)


def _evaluate_threshold(records: list[dict[str, Any]], threshold: float) -> dict[str, float]:
    supported = [
        r for r in records if str(r["query_type"]).upper() != "Q13_UNSUPPORTED"
    ]
    unsupported = [
        r for r in records if str(r["query_type"]).upper() == "Q13_UNSUPPORTED"
    ]

    def accepts(record: dict[str, Any]) -> bool:
        return float(record["dense_top1_similarity"]) >= threshold

    supported_acceptance = (
        sum(accepts(r) for r in supported) / len(supported) if supported else 0.0
    )
    unsupported_rejection = (
        sum(not accepts(r) for r in unsupported) / len(unsupported)
        if unsupported
        else 0.0
    )
    balanced_accuracy = (supported_acceptance + unsupported_rejection) / 2.0

    return {
        "threshold": threshold,
        "supported_acceptance_rate": supported_acceptance,
        "unsupported_rejection_rate": unsupported_rejection,
        "balanced_accuracy": balanced_accuracy,
    }


def calibrate(records: list[dict[str, Any]]) -> dict[str, Any]:
    _validate_records(records)

    calibration = [
        r for r in records if str(r["evaluation_split"]).upper() == "CALIBRATION"
    ]
    holdout = [
        r for r in records if str(r["evaluation_split"]).upper() == "HOLDOUT"
    ]
    if not calibration:
        raise ValueError("No CALIBRATION records were supplied.")

    # Refuse to let HOLDOUT participate in optimization, even accidentally.
    calibration_ids = {r["query_id"] for r in calibration}
    holdout_ids = {r["query_id"] for r in holdout}
    overlap = calibration_ids.intersection(holdout_ids)
    if overlap:
        raise ValueError(f"Query IDs appear in both splits: {sorted(overlap)}")

    candidates = _candidate_thresholds(
        [float(r["dense_top1_similarity"]) for r in calibration]
    )
    scored = [_evaluate_threshold(calibration, threshold) for threshold in candidates]

    # Deterministic selection: maximize balanced accuracy, then supported
    # acceptance, then unsupported rejection, then choose the highest threshold.
    best = max(
        scored,
        key=lambda row: (
            row["balanced_accuracy"],
            row["supported_acceptance_rate"],
            row["unsupported_rejection_rate"],
            row["threshold"],
        ),
    )

    return {
        "selection_split": "CALIBRATION",
        "selection_objective": "balanced_accuracy",
        "calibration_query_count": len(calibration),
        "calibration_supported_count": sum(
            r["query_type"] != "Q13_UNSUPPORTED" for r in calibration
        ),
        "calibration_unsupported_count": sum(
            r["query_type"] == "Q13_UNSUPPORTED" for r in calibration
        ),
        "holdout_query_count_seen_but_not_used": len(holdout),
        "selected_threshold": best["threshold"],
        "selected_metrics": best,
        "candidate_count": len(scored),
        "candidates": scored,
        "holdout_used_for_selection": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path, help="JSON measurements file")
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help="Optional JSON output path",
    )
    args = parser.parse_args()

    try:
        result = calibrate(_load_records(args.input))
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"CALIBRATION_ERROR: {exc}", file=sys.stderr)
        return 2

    payload = json.dumps(result, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.write_text(payload, encoding="utf-8")
    else:
        print(payload, end="")

    print(
        f"SELECTED_THRESHOLD={result['selected_threshold']:.6f}",
        file=sys.stderr,
    )
    print("HOLDOUT_USED_FOR_SELECTION=NO", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
