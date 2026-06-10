#!/usr/bin/env python3
"""Write KRK candidate proposal quality/prioritization review v1."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
BLOCKER_REVIEW = Path(
    "reports/strategy_arbitration/krk_candidate_generation_label_blocker_review_v1.json"
)
ANNOTATION_V2 = Path("reports/strategy_arbitration/krk_candidate_move_capacity_annotation_v2.json")
GAP_REVIEW = Path("reports/strategy_arbitration/krk_candidate_generation_observation_gap_review_v1.json")
OUT_JSON = Path(
    "reports/strategy_arbitration/"
    "krk_candidate_proposal_quality_prioritization_review_v1.json"
)
OUT_MD = Path(
    "reports/strategy_arbitration/"
    "krk_candidate_proposal_quality_prioritization_review_v1.md"
)


def _load(path: Path) -> dict[str, Any]:
    payload = json.loads((ROOT / path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"expected JSON object: {path}")
    return payload


def build_payload(
    blocker_review: dict[str, Any] | None = None,
    annotation_v2: dict[str, Any] | None = None,
    gap_review: dict[str, Any] | None = None,
) -> dict[str, Any]:
    blocker_review = blocker_review or _load(BLOCKER_REVIEW)
    annotation_v2 = annotation_v2 or _load(ANNOTATION_V2)
    gap_review = gap_review or _load(GAP_REVIEW)
    blocker_evidence = blocker_review.get("evidence") or {}
    annotation_summary = annotation_v2.get("summary") or {}
    gap_summary = gap_review.get("summary") or {}
    return {
        "schema_version": "krk_candidate_proposal_quality_prioritization_review.v1",
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
            str(ANNOTATION_V2),
            str(BLOCKER_REVIEW),
        ],
        "evidence_summary": {
            "observation_frame_count": gap_summary.get("frame_count"),
            "candidate_move_frame_count": annotation_summary.get("candidate_move_frame_count"),
            "protected_candidate_move_count": annotation_summary.get("protected_candidate_move_count"),
            "protected_annotated_candidate_move_count": annotation_summary.get(
                "protected_annotated_candidate_move_count"
            ),
            "protected_annotation_recall": annotation_summary.get(
                "protected_annotation_recall"
            ),
            "bounded_label_count": blocker_evidence.get("bounded_label_count"),
            "bounded_label_positive_capacity_count": blocker_evidence.get(
                "bounded_label_positive_capacity_count"
            ),
            "bounded_label_negative_capacity_count": blocker_evidence.get(
                "bounded_label_negative_capacity_count"
            ),
            "missing_expected_sources": gap_summary.get("missing_expected_sources"),
        },
        "proposal_quality_problem": {
            "diagnosis": "candidate_generator_is_visible_but_too_broad_and_underannotated",
            "why_not_more_blind_labels": [
                "bounded labels found many positives but only raised protected annotation recall to 0.075",
                "observation emits hundreds of candidate moves, so unprioritized labeling scales poorly",
                "capacity labels remain candidate-generation evidence, not ownership labels",
                "negative-capacity provider-pack candidates remain present",
            ],
            "why_not_selector_review_yet": [
                "candidate capacity is mostly unknown",
                "candidate proposal quality is not ranked or filtered",
                "PlanCapsule and broader strategy candidates are not visible in observation frames",
                "capacity labels are not direct selector labels",
            ],
        },
        "recommended_quality_axes": [
            {
                "axis": "source_channel",
                "use": "separate validated_provider_pack, candidate_move_frame, plan_capsule_sequence_candidate, and broader_strategy_candidate before ranking",
                "causal_status": "non_causal",
            },
            {
                "axis": "visible_term_density",
                "use": "prioritize candidates with meaningful move_shape/post_move/safety/source terms over low-information legal moves",
                "causal_status": "non_causal",
            },
            {
                "axis": "safety_floor",
                "use": "separate legal-safe candidate generation from conversion-capacity evidence",
                "causal_status": "non_causal",
            },
            {
                "axis": "known_capacity_contrast",
                "use": "use existing positive/negative capacity labels as offline quality calibration only",
                "causal_status": "non_causal",
            },
            {
                "axis": "duplicate_or_selected_move_relation",
                "use": "distinguish current selected move, same-move provider alternatives, and distinct alternatives",
                "causal_status": "non_causal",
            },
            {
                "axis": "stage_and_protection_scope",
                "use": "Stage 4/5/6 protected candidates may train coverage diagnostics; Stage 7 remains held-out challenge",
                "causal_status": "non_causal",
            },
        ],
        "proposed_next_artifacts": [
            "reports/strategy_arbitration/krk_candidate_proposal_quality_dataset_v1.json",
            "reports/strategy_arbitration/krk_candidate_proposal_quality_probe_v1.json",
            "reports/strategy_arbitration/krk_candidate_proposal_quality_decision_v1.json",
        ],
        "acceptance_before_selector_review": [
            "candidate proposal quality model improves positive/negative capacity separation on protected rows",
            "candidate count is bounded by a visible quality gate in offline analysis",
            "Stage 7 readiness/training rows remain zero",
            "capacity labels remain separate from ownership labels",
            "PlanCapsule/broader strategy visibility gap is explicitly handled or deferred",
            "focused tests pass and runtime defaults remain unchanged",
        ],
        "forbidden_next_steps": [
            "runtime_selector",
            "score_changes",
            "provider_routing",
            "guardrail_campaign",
            "stage7_promotion",
            "stage8_training",
            "runtime_dtm_or_tablebase",
            "hidden_python_controller",
            "more_blind_label_farming_without_quality_prioritization",
        ],
        "decision": {
            "status": "proposal_quality_prioritization_review_ready",
            "selector_allowed": False,
            "guardrails_allowed": False,
            "runtime_changes_allowed": False,
            "recommended_next_step": "build_non_causal_candidate_proposal_quality_dataset",
        },
    }


def write_markdown(payload: dict[str, Any]) -> None:
    evidence = payload["evidence_summary"]
    lines = [
        "# KRK Candidate Proposal Quality / Prioritization Review v1",
        "",
        "This review follows the observation sandbox and bounded candidate-move labels. It is non-causal and does not authorize selection.",
        "",
        "## Decision",
        "",
        f"- status: `{payload['decision']['status']}`",
        f"- selector_allowed: `{payload['decision']['selector_allowed']}`",
        f"- recommended_next_step: `{payload['decision']['recommended_next_step']}`",
        "",
        "## Evidence Summary",
        "",
        f"- observation_frame_count: {evidence['observation_frame_count']}",
        f"- candidate_move_frame_count: {evidence['candidate_move_frame_count']}",
        f"- protected_annotated_candidate_move_count: {evidence['protected_annotated_candidate_move_count']}",
        f"- protected_annotation_recall: `{float(evidence['protected_annotation_recall'] or 0.0):.3f}`",
        f"- bounded_label_count: {evidence['bounded_label_count']}",
        f"- bounded_label_positive_capacity_count: {evidence['bounded_label_positive_capacity_count']}",
        f"- bounded_label_negative_capacity_count: {evidence['bounded_label_negative_capacity_count']}",
        f"- missing_expected_sources: `{evidence['missing_expected_sources']}`",
        "",
        "## Diagnosis",
        "",
        f"- `{payload['proposal_quality_problem']['diagnosis']}`",
        "",
        "## Why Not More Blind Labels",
        "",
    ]
    lines.extend(
        f"- {item}" for item in payload["proposal_quality_problem"]["why_not_more_blind_labels"]
    )
    lines.extend(["", "## Quality Axes", ""])
    lines.extend(
        f"- `{axis['axis']}`: {axis['use']}" for axis in payload["recommended_quality_axes"]
    )
    lines.extend(["", "## Forbidden Next Steps", ""])
    lines.extend(f"- `{step}`" for step in payload["forbidden_next_steps"])
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
