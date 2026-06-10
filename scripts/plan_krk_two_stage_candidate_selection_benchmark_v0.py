#!/usr/bin/env python3
"""Plan a non-causal two-stage candidate-generation/selection benchmark."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
TWO_STAGE_REVIEW = Path("reports/krk_two_stage_candidate_selection_review_v0.json")
OUT_JSON = Path("reports/krk_two_stage_candidate_selection_benchmark_plan_v0.json")
OUT_MD = Path("reports/krk_two_stage_candidate_selection_benchmark_plan_v0.md")


def _load(path: Path) -> dict[str, Any]:
    payload = json.loads((ROOT / path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"expected JSON object: {path}")
    return payload


def build_plan() -> dict[str, Any]:
    review = _load(TWO_STAGE_REVIEW)
    if review.get("causal_status") != "non_causal_architecture_review":
        raise ValueError("two-stage review must remain non-causal")
    payload = {
        "schema_version": "krk_two_stage_candidate_selection_benchmark_plan.v0",
        "causal_status": "non_causal_benchmark_plan",
        "runtime_behavior_changed": False,
        "runtime_defaults_changed": False,
        "runtime_selector_implemented": False,
        "runtime_candidate_generator_implemented": False,
        "runtime_terminals_added": False,
        "runtime_dtm_or_tablebase_lookup": False,
        "gameplay_topology_mutation": False,
        "stage7_promotion_allowed": False,
        "stage8_training_allowed": False,
        "source_artifacts": [str(TWO_STAGE_REVIEW)],
        "benchmark_tracks": {
            "candidate_generation": {
                "question": "Does the candidate set represent protected providers with conversion capacity?",
                "baselines": [
                    "current_runtime_proposal_frames",
                    "validated_provider_candidate_set_expansion",
                ],
                "metrics": [
                    "positive_capacity_recall",
                    "candidate_count_per_state",
                    "negative_capacity_inclusion_rate",
                    "stage7_leakage_count",
                ],
                "training_allowed": False,
            },
            "strategy_selection": {
                "question": "Given a candidate set, can a selector suppress negative-capacity candidates while preserving positives?",
                "label_channels": [
                    "selected_playout_success",
                    "runtime_proposal_label",
                    "forced_provider_capacity_label",
                ],
                "metrics": [
                    "leave_state_out_positive_hit_rate",
                    "negative_capacity_suppression",
                    "false_positive_on_forced_capacity",
                    "stage7_heldout_suppression",
                ],
                "training_allowed": False,
            },
        },
        "minimum_inputs": [
            "krk_ranked_strategy_proposal_frames_v1",
            "krk_protected_provider_coverage_frames_v0",
            "krk_state_local_contrast_labels_v2",
            "krk_candidate_generator_coverage_audit_v0",
            "krk_validated_provider_candidate_set_audit_v0",
        ],
        "acceptance": {
            "stage7_training_rows": 0,
            "runtime_work_allowed": False,
            "selector_training_allowed": False,
            "candidate_generator_runtime_allowed": False,
            "reports_candidate_generation_and_selection_separately": True,
            "explicitly_separates_label_semantics": True,
        },
        "stop_conditions": [
            "benchmark requires new runtime behavior",
            "benchmark mixes forced-capacity labels as direct selected-success labels",
            "Stage 7 rows become training rows",
            "DTM/tablebase enters runtime policy",
            "topology mutation is required",
        ],
        "decision": {
            "status": "two_stage_candidate_selection_benchmark_plan_ready",
            "recommended_next_step": "build_two_stage_candidate_selection_benchmark_v0",
            "runtime_work_allowed": False,
            "candidate_generator_runtime_allowed": False,
            "selector_training_allowed": False,
            "stage7_promotion_allowed": False,
            "stage8_training_allowed": False,
        },
    }
    validate_plan(payload)
    return payload


def validate_plan(payload: dict[str, Any]) -> None:
    for key in (
        "runtime_behavior_changed",
        "runtime_defaults_changed",
        "runtime_selector_implemented",
        "runtime_candidate_generator_implemented",
        "runtime_terminals_added",
        "runtime_dtm_or_tablebase_lookup",
        "gameplay_topology_mutation",
        "stage7_promotion_allowed",
        "stage8_training_allowed",
    ):
        if payload.get(key) is not False:
            raise ValueError(f"{key} must be false")
    if payload["acceptance"]["stage7_training_rows"] != 0:
        raise ValueError("Stage 7 rows must remain held out")
    if payload["decision"]["selector_training_allowed"] is not False:
        raise ValueError("selector training remains blocked")


def render_markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# KRK Two-Stage Candidate / Selection Benchmark Plan v0",
        "",
        "This non-causal plan defines a benchmark that separates candidate generation from strategy selection.",
        "",
        "## Tracks",
        "",
    ]
    for name, spec in payload["benchmark_tracks"].items():
        lines.append(f"- `{name}` question: {spec['question']}")
        lines.append(f"- `{name}` metrics: `{spec['metrics']}`")
    lines.extend(["", "## Minimum Inputs", ""])
    for item in payload["minimum_inputs"]:
        lines.append(f"- `{item}`")
    lines.extend(["", "## Acceptance", ""])
    for key, value in payload["acceptance"].items():
        lines.append(f"- `{key}`: `{value}`")
    lines.extend(["", "## Stop Conditions", ""])
    for item in payload["stop_conditions"]:
        lines.append(f"- `{item}`")
    lines.extend(["", "## Decision", ""])
    for key, value in payload["decision"].items():
        lines.append(f"- `{key}`: `{value}`")
    lines.append("")
    return "\n".join(lines)


def main() -> None:
    payload = build_plan()
    (ROOT / OUT_JSON).write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (ROOT / OUT_MD).write_text(render_markdown(payload), encoding="utf-8")
    print(json.dumps(payload["decision"], indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
