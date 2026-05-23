#!/usr/bin/env python3
"""Write offline candidate-generation training refresh design v3."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
REVIEW = Path("reports/strategy_arbitration/krk_candidate_generation_v3_training_refresh_review.json")
DATASET = Path("reports/strategy_arbitration/krk_strategy_sequence_dataset_v3.json")
OUT_JSON = Path("reports/strategy_arbitration/krk_candidate_generation_training_refresh_design_v3.json")
OUT_MD = Path("reports/strategy_arbitration/krk_candidate_generation_training_refresh_design_v3.md")


def _load(path: Path) -> dict[str, Any]:
    payload = json.loads((ROOT / path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"expected JSON object: {path}")
    return payload


def build_payload(
    review: dict[str, Any] | None = None,
    dataset: dict[str, Any] | None = None,
) -> dict[str, Any]:
    review = review or _load(REVIEW)
    dataset = dataset or _load(DATASET)
    summary = dataset.get("summary") or {}
    design_allowed = (
        (review.get("decision") or {}).get("status")
        == "candidate_generation_v3_training_refresh_design_ready_non_causal"
    )
    return {
        "schema_version": "krk_candidate_generation_training_refresh_design.v3",
        "causal_status": "non_causal_design",
        "runtime_behavior_changed": False,
        "runtime_defaults_changed": False,
        "runtime_selector_implemented": False,
        "runtime_score_changes": False,
        "runtime_direct_routing": False,
        "runtime_dtm_or_tablebase_lookup": False,
        "gameplay_topology_mutation": False,
        "stage7_promotion_allowed": False,
        "stage8_training_allowed": False,
        "source_artifacts": [str(REVIEW), str(DATASET)],
        "design_goal": (
            "Define an offline candidate-generation refresh benchmark that learns "
            "which provider families should be visible as candidates in protected "
            "Stage 4/5/6 contexts. This is candidate generation only, not ownership "
            "selection."
        ),
        "input_channels": [
            {
                "channel": "validated_provider_capacity",
                "use": "positive/negative candidate-generation labels",
                "selector_use": False,
            },
            {
                "channel": "runtime_observation_trace_feature",
                "use": "context/proposal-source features only",
                "selector_use": False,
            },
            {
                "channel": "visible_provider_proposal",
                "use": "normal-routing proposal context",
                "selector_use": False,
            },
        ],
        "training_target": {
            "positive": "protected positive forced-provider capacity rows",
            "negative": "protected negative forced-provider capacity rows",
            "objective": "candidate_generation_recall_with_negative_capacity_suppression",
            "not_objective": "runtime_ownership_or_move_selection",
        },
        "feature_groups": [
            "source_stage",
            "active_landmark_label",
            "candidate_strategy_family",
            "provider_id",
            "trace_feature_source",
            "stage_family_context",
            "visible_source_terms",
            "selected_provider_before_observation_context",
        ],
        "evaluation_protocol": {
            "protected_stages": ["stage4", "stage5", "stage6"],
            "heldout_challenge_stages": ["stage7"],
            "splits": ["leave_stage_out", "leave_family_out", "leave_state_out_if_enough_rows"],
            "metrics": [
                "positive_capacity_recall",
                "negative_capacity_suppression",
                "precision",
                "stage_family_coverage",
                "stage7_heldout_candidate_visibility_only",
            ],
        },
        "readiness_thresholds_for_future_runtime_review": {
            "positive_capacity_recall": 0.75,
            "negative_capacity_suppression": 0.80,
            "leave_stage_out_positive_capacity_recall": 0.65,
            "stage7_training_rows": 0,
            "selector_training_rows": 0,
        },
        "current_dataset_summary": {
            "row_count": summary.get("row_count"),
            "candidate_generation_training_row_count": summary.get(
                "candidate_generation_training_row_count"
            ),
            "selector_training_row_count": summary.get("selector_training_row_count"),
            "runtime_trace_feature_row_count": summary.get("runtime_trace_feature_row_count"),
            "stage7_readiness_training_row_count": summary.get(
                "stage7_readiness_training_row_count"
            ),
        },
        "forbidden_uses": [
            "runtime_selector",
            "score_changes",
            "provider_routing",
            "provider_suppression",
            "guardrail_campaign",
            "stage7_promotion",
            "stage8_training",
        ],
        "decision": {
            "status": (
                "candidate_generation_training_refresh_v3_design_ready"
                if design_allowed
                else "candidate_generation_training_refresh_v3_design_blocked"
            ),
            "implementation_allowed_by_this_artifact": False,
            "selector_allowed": False,
            "guardrails_allowed": False,
            "promotion_allowed": False,
            "recommended_next_step": (
                "implement_offline_candidate_generation_training_refresh_v3_benchmark"
                if design_allowed
                else "fix_training_refresh_review_gate"
            ),
        },
    }


def write_markdown(payload: dict[str, Any]) -> None:
    lines = [
        "# KRK Candidate-Generation Training Refresh Design v3",
        "",
        payload["design_goal"],
        "",
        "## Decision",
        "",
        f"- status: `{payload['decision']['status']}`",
        f"- implementation_allowed_by_this_artifact: `{payload['decision']['implementation_allowed_by_this_artifact']}`",
        f"- selector_allowed: `{payload['decision']['selector_allowed']}`",
        f"- recommended_next_step: `{payload['decision']['recommended_next_step']}`",
        "",
        "## Training Target",
        "",
    ]
    for key, value in payload["training_target"].items():
        lines.append(f"- {key}: `{value}`")
    lines.extend(["", "## Feature Groups", ""])
    lines.extend(f"- `{item}`" for item in payload["feature_groups"])
    lines.extend(["", "## Evaluation Protocol", ""])
    for key, value in payload["evaluation_protocol"].items():
        lines.append(f"- {key}: `{value}`")
    lines.extend(["", "## Forbidden Uses", ""])
    lines.extend(f"- `{item}`" for item in payload["forbidden_uses"])
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
