#!/usr/bin/env python3
"""Review blockers after bounded candidate-move capacity labeling."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
GAP_REVIEW = Path(
    "reports/strategy_arbitration/krk_candidate_generation_observation_gap_review_v1.json"
)
ANNOTATION_V2 = Path("reports/strategy_arbitration/krk_candidate_move_capacity_annotation_v2.json")
LABELS_V1 = Path("reports/strategy_arbitration/krk_candidate_move_capacity_labels_v1.json")
MANIFEST_V1 = Path("reports/strategy_arbitration/krk_candidate_move_capacity_label_manifest_v1.json")
OUT_JSON = Path("reports/strategy_arbitration/krk_candidate_generation_label_blocker_review_v1.json")
OUT_MD = Path("reports/strategy_arbitration/krk_candidate_generation_label_blocker_review_v1.md")


def _load(path: Path) -> dict[str, Any]:
    payload = json.loads((ROOT / path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"expected JSON object: {path}")
    return payload


def build_payload(
    gap_review: dict[str, Any] | None = None,
    annotation_v2: dict[str, Any] | None = None,
    labels_v1: dict[str, Any] | None = None,
    manifest_v1: dict[str, Any] | None = None,
) -> dict[str, Any]:
    gap_review = gap_review or _load(GAP_REVIEW)
    annotation_v2 = annotation_v2 or _load(ANNOTATION_V2)
    labels_v1 = labels_v1 or _load(LABELS_V1)
    manifest_v1 = manifest_v1 or _load(MANIFEST_V1)
    annotation_summary = annotation_v2.get("summary") or {}
    label_summary = labels_v1.get("summary") or {}
    gap_summary = gap_review.get("summary") or {}
    manifest_summary = manifest_v1.get("summary") or {}
    recall = float(annotation_summary.get("protected_annotation_recall") or 0.0)
    label_count = int(label_summary.get("label_count") or 0)
    positive_count = int((label_summary.get("capacity_label_counts") or {}).get("positive_capacity") or 0)
    negative_count = int((label_summary.get("capacity_label_counts") or {}).get("negative_capacity") or 0)
    blockers = list(gap_review.get("selector_blockers") or [])
    blockers.extend(
        [
            "candidate_move_annotation_coverage_too_sparse"
            if recall < 0.5
            else "candidate_move_annotation_coverage_sufficient",
            "blind_label_expansion_risk"
            if recall < 0.15 and label_count > 0
            else "bounded_labeling_may_continue",
        ]
    )
    status = (
        "candidate_generation_label_coverage_underpowered_selector_blocked"
        if recall < 0.5
        else "candidate_generation_label_coverage_review_ready"
    )
    return {
        "schema_version": "krk_candidate_generation_label_blocker_review.v1",
        "causal_status": "non_causal_architecture_review",
        "runtime_behavior_changed": False,
        "runtime_defaults_changed": False,
        "runtime_selector_implemented": False,
        "runtime_score_changes": False,
        "runtime_direct_routing": False,
        "runtime_dtm_or_tablebase_lookup": False,
        "gameplay_topology_mutation": False,
        "stage7_promotion_allowed": False,
        "stage8_training_allowed": False,
        "source_artifacts": [
            str(GAP_REVIEW),
            str(MANIFEST_V1),
            str(LABELS_V1),
            str(ANNOTATION_V2),
        ],
        "evidence": {
            "broadened_frame_count": gap_summary.get("frame_count"),
            "candidate_move_frame_count": annotation_summary.get("candidate_move_frame_count"),
            "protected_candidate_move_count": annotation_summary.get("protected_candidate_move_count"),
            "protected_annotated_candidate_move_count": annotation_summary.get(
                "protected_annotated_candidate_move_count"
            ),
            "protected_annotation_recall": recall,
            "bounded_label_count": label_count,
            "bounded_label_positive_capacity_count": positive_count,
            "bounded_label_negative_capacity_count": negative_count,
            "manifest_job_count": manifest_summary.get("job_count"),
            "stage7_label_count": label_summary.get("stage7_label_count"),
            "stage7_training_label_count": label_summary.get("stage7_training_label_count"),
            "missing_expected_sources": gap_summary.get("missing_expected_sources"),
        },
        "blockers": blockers,
        "interpretation": {
            "candidate_generation_observation_is_safe": True,
            "candidate_move_capacity_annotation_path_exists": True,
            "candidate_move_annotation_is_too_sparse_for_selector_review": recall < 0.5,
            "bounded_labels_found_positive_capacity": positive_count > 0,
            "bounded_labels_found_negative_capacity": negative_count > 0,
            "more_blind_label_farming_not_recommended": recall < 0.15,
            "capacity_labels_are_not_ownership_labels": True,
        },
        "decision": {
            "status": status,
            "selector_allowed": False,
            "guardrails_allowed": False,
            "runtime_changes_allowed": False,
            "recommended_next_step": "design_candidate_proposal_quality_prioritization_review"
            if recall < 0.5
            else "candidate_move_capacity_quality_review",
        },
    }


def write_markdown(payload: dict[str, Any]) -> None:
    evidence = payload["evidence"]
    lines = [
        "# KRK Candidate-Generation Label Blocker Review v1",
        "",
        "This review closes the bounded candidate-move capacity-label slice. It remains non-causal.",
        "",
        "## Decision",
        "",
        f"- status: `{payload['decision']['status']}`",
        f"- selector_allowed: `{payload['decision']['selector_allowed']}`",
        f"- guardrails_allowed: `{payload['decision']['guardrails_allowed']}`",
        f"- recommended_next_step: `{payload['decision']['recommended_next_step']}`",
        "",
        "## Evidence",
        "",
        f"- broadened_frame_count: {evidence['broadened_frame_count']}",
        f"- candidate_move_frame_count: {evidence['candidate_move_frame_count']}",
        f"- protected_candidate_move_count: {evidence['protected_candidate_move_count']}",
        f"- protected_annotated_candidate_move_count: {evidence['protected_annotated_candidate_move_count']}",
        f"- protected_annotation_recall: `{evidence['protected_annotation_recall']:.3f}`",
        f"- bounded_label_count: {evidence['bounded_label_count']}",
        f"- bounded_label_positive_capacity_count: {evidence['bounded_label_positive_capacity_count']}",
        f"- bounded_label_negative_capacity_count: {evidence['bounded_label_negative_capacity_count']}",
        f"- missing_expected_sources: `{evidence['missing_expected_sources']}`",
        "",
        "## Blockers",
        "",
    ]
    lines.extend(f"- `{blocker}`" for blocker in payload["blockers"])
    lines.extend(
        [
            "",
            "## Interpretation",
            "",
        ]
    )
    lines.extend(
        f"- {key}: `{value}`" for key, value in payload["interpretation"].items()
    )
    lines.extend(
        [
            "",
            "## Boundary",
            "",
            "The next step should improve candidate proposal quality/prioritization before further labels or selector review. Do not implement a selector, route, score change, guardrail campaign, Stage 7 promotion, or Stage 8 training.",
        ]
    )
    (ROOT / OUT_MD).write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    payload = build_payload()
    (ROOT / OUT_JSON).write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    write_markdown(payload)
    print(json.dumps(payload["decision"], indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
