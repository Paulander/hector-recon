#!/usr/bin/env python3
"""Review targeted non-stage0 ownership label results."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
LABELS = Path("reports/krk_targeted_non_stage0_ownership_labels_v0.json")
SOURCE_DIVERSITY = Path("reports/krk_ownership_source_diversity_review_v0.json")
OUT_JSON = Path("reports/krk_targeted_non_stage0_ownership_review_v0.json")
OUT_MD = Path("reports/krk_targeted_non_stage0_ownership_review_v0.md")


def _load_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"expected JSON object: {path}")
    return payload


def build_review(repo_root: Path) -> dict[str, Any]:
    labels_payload = _load_json(repo_root / LABELS)
    source_review = _load_json(repo_root / SOURCE_DIVERSITY)
    if labels_payload.get("causal_status") != "non_causal_label_run":
        raise ValueError("labels must remain non-causal")

    labels = labels_payload.get("labels") or []
    preserved = [
        label for label in labels if label.get("historical_selection_preserved") is True
    ]
    collapsed = [
        label for label in labels if label.get("current_profile_collapsed_to_stage0") is True
    ]
    shifted = [
        label
        for label in labels
        if label.get("historical_selection_preserved") is not True
        and label.get("current_profile_collapsed_to_stage0") is not True
    ]
    failed = [
        label
        for label in labels
        if (label.get("selected_playout_success") or {}).get("result") != "mate"
    ]

    if preserved:
        status = "non_stage0_current_profile_evidence_recovered"
        next_step = "merge_preserved_non_stage0_labels_into_v4_then_reprobe_selector_features"
    elif collapsed and len(collapsed) == len(labels):
        status = "routing_profile_stage0_dominance_blocks_source_diversity"
        next_step = "review_current_profile_stage0_dominance_before_more_label_farming"
    elif shifted:
        status = "historical_non_stage0_states_shift_to_other_current_owners"
        next_step = "review_owner_shift_semantics_before_selector_training"
    else:
        status = "targeted_non_stage0_review_inconclusive"
        next_step = "stop_for_review_before_more_label_collection"

    review = {
        "schema_version": "krk_targeted_non_stage0_ownership_review.v0",
        "causal_status": "non_causal_review",
        "runtime_behavior_changed": False,
        "runtime_defaults_changed": False,
        "runtime_arbiter_implemented": False,
        "runtime_terminals_added": False,
        "runtime_dtm_or_tablebase_lookup": False,
        "gameplay_topology_mutation": False,
        "stage7_promotion_allowed": False,
        "stage8_training_allowed": False,
        "selector_training_allowed": False,
        "source_artifacts": [str(LABELS), str(SOURCE_DIVERSITY)],
        "summary": {
            "targeted_label_count": len(labels),
            "preserved_historical_non_stage0_count": len(preserved),
            "stage0_collapse_count": len(collapsed),
            "shifted_to_other_owner_count": len(shifted),
            "selected_owner_failed_count": len(failed),
            "previous_ownership_source_status": source_review.get("decision", {}).get("status"),
            "labeling_semantics": (
                "offline_observation_of_current_graph_choices_not_hand_authored_policy"
            ),
        },
        "evidence": {
            "preserved_state_ids": [label.get("state_id") for label in preserved],
            "stage0_collapse_state_ids": [label.get("state_id") for label in collapsed],
            "shifted_state_ids": [label.get("state_id") for label in shifted],
            "failed_state_ids": [label.get("state_id") for label in failed],
        },
        "decision": {
            "status": status,
            "selector_training_allowed": False,
            "runtime_arbiter_allowed": False,
            "recommended_next_step": next_step,
        },
        "blocked_next_steps": [
            "runtime_arbiter",
            "selector_sandbox",
            "stage7_repair",
            "stage7_promotion",
            "stage8_training",
            "runtime_dtm_or_tablebase",
            "gameplay_topology_mutation",
        ],
    }
    validate_review(review)
    return review


def validate_review(review: dict[str, Any]) -> None:
    if review.get("causal_status") != "non_causal_review":
        raise ValueError("review must remain non-causal")
    for key in (
        "runtime_behavior_changed",
        "runtime_defaults_changed",
        "runtime_arbiter_implemented",
        "runtime_terminals_added",
        "runtime_dtm_or_tablebase_lookup",
        "gameplay_topology_mutation",
        "stage7_promotion_allowed",
        "stage8_training_allowed",
        "selector_training_allowed",
    ):
        if review.get(key) is not False:
            raise ValueError(f"{key} must be false")


def render_markdown(review: dict[str, Any]) -> str:
    summary = review["summary"]
    lines = [
        "# KRK Targeted Non-Stage0 Ownership Review v0",
        "",
        "This review distinguishes label scarcity from current-profile owner collapse. "
        "The labels are offline observations of the current graph, not hand-authored "
        "policy targets.",
        "",
        "## Summary",
        "",
        f"- Targeted label count: `{summary['targeted_label_count']}`",
        f"- Preserved historical non-stage0 count: `{summary['preserved_historical_non_stage0_count']}`",
        f"- Stage0 collapse count: `{summary['stage0_collapse_count']}`",
        f"- Shifted to other owner count: `{summary['shifted_to_other_owner_count']}`",
        f"- Selected owner failed count: `{summary['selected_owner_failed_count']}`",
        f"- Previous source-diversity status: `{summary['previous_ownership_source_status']}`",
        "",
        "## Decision",
        "",
        f"- Status: `{review['decision']['status']}`",
        f"- Recommended next step: `{review['decision']['recommended_next_step']}`",
        f"- Selector training allowed: `{review['decision']['selector_training_allowed']}`",
        "",
    ]
    return "\n".join(lines)


def write_outputs(repo_root: Path, review: dict[str, Any]) -> None:
    (repo_root / OUT_JSON).write_text(
        json.dumps(review, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (repo_root / OUT_MD).write_text(render_markdown(review), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=ROOT)
    args = parser.parse_args()
    repo_root = args.repo_root.resolve()
    review = build_review(repo_root)
    write_outputs(repo_root, review)
    print(json.dumps(review["summary"], indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
