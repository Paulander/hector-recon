#!/usr/bin/env python3
"""Review the non-causal KRK sequence-policy benchmark.

This gate is deliberately passive. It can classify benchmark results once the
benchmark preflight is ready, but it never trains, routes, promotes Stage 7, or
authorizes Stage 8 by itself.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
BENCHMARK = ROOT / "reports/strategy_arbitration/krk_sequence_policy_benchmark_v0.json"
OUTPUT_JSON = ROOT / "reports/strategy_arbitration/krk_sequence_policy_benchmark_review_v0.json"
OUTPUT_MD = ROOT / "reports/strategy_arbitration/krk_sequence_policy_benchmark_review_v0.md"

SCHEMA_VERSION = "krk_sequence_policy_benchmark_review.v0"

COMMON_FALSE_FLAGS = {
    "runtime_behavior_changed": False,
    "runtime_defaults_changed": False,
    "runtime_selector_implemented": False,
    "runtime_score_changes": False,
    "runtime_direct_routing": False,
    "runtime_dtm_or_tablebase_lookup": False,
    "hidden_python_controller": False,
    "gameplay_topology_mutation": False,
    "stage7_promotion_allowed": False,
    "stage8_training_allowed": False,
}


def _load(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise TypeError(f"{path} must contain a JSON object")
    return data


def _objective(payload: dict[str, Any], objective_id: str) -> dict[str, Any]:
    for objective in payload.get("objectives") or []:
        if objective.get("objective_id") == objective_id:
            return objective
    return {}


def _numeric(value: Any, default: float = 0.0) -> float:
    if value is None:
        return default
    return float(value)


def build_payload(*, benchmark: dict[str, Any] | None = None) -> dict[str, Any]:
    benchmark = benchmark or _load(BENCHMARK)
    preflight = benchmark.get("preflight") or {}
    benchmark_decision = benchmark.get("decision") or {}
    ready = bool(benchmark_decision.get("benchmark_executed_as_ready"))

    stage4 = _objective(benchmark, "stage4_state_local_first_move_contrast")
    plan = _objective(benchmark, "protected_plan_window_entry_progress_exit_abort")
    stage7 = _objective(benchmark, "stage7_heldout_sequence_success_vs_hard_negative")

    stage4_metrics = stage4.get("metrics") or {}
    stage4_top3 = _numeric(stage4_metrics.get("top3_conversion_positive_by_state"))
    stage4_top1 = _numeric(stage4_metrics.get("top1_conversion_positive_by_state"))
    stage4_recall = _numeric(stage4_metrics.get("recall"))
    stage4_negative_suppression = _numeric(stage4_metrics.get("negative_suppression"))

    plan_failure_sparse = bool(plan.get("failure_evidence_sparse"))
    stage7_success_met = bool(stage7.get("success_controls_met"))
    stage7_failure_met = bool(stage7.get("failure_controls_met"))

    findings: list[str] = []
    if stage4_top3 >= 0.9:
        findings.append("stage4_topk_sequence_signal_present")
    if stage4_recall < 0.7:
        findings.append("stage4_binary_rule_insufficient")
    if stage4_negative_suppression >= 0.8:
        findings.append("stage4_negative_suppression_reasonable")
    if plan_failure_sparse:
        findings.append("protected_plan_window_failure_evidence_sparse")
    if stage7_success_met and stage7_failure_met:
        findings.append("stage7_heldout_controls_balanced")
    elif not stage7_success_met:
        findings.append("stage7_success_controls_missing")

    blockers: list[str] = []
    if not ready:
        blockers.extend(preflight.get("blockers") or ["benchmark_preflight_not_ready"])
    if ready and plan_failure_sparse:
        blockers.append("protected_plan_window_failure_evidence_sparse")

    if not ready:
        if (
            "selector_training_rows_forbidden" in blockers
            or "runtime_authorization_rows_forbidden" in blockers
        ):
            status = "sequence_policy_benchmark_review_blocked_forbidden_training_or_runtime_rows"
            recommended_next_step = (
                "repair_sequence_policy_inputs_remove_training_or_runtime_rows"
            )
        elif "stage7_clean_success_controls_missing" in blockers:
            status = "sequence_policy_benchmark_review_blocked_pending_ready_inputs"
            recommended_next_step = (
                "fill_stage7_clean_success_controls_and_rerun_passive_gate_advancement"
            )
        elif "stage7_clean_failure_controls_missing" in blockers:
            status = "sequence_policy_benchmark_review_blocked_pending_ready_inputs"
            recommended_next_step = "review_stage7_clean_failure_control_inputs"
        elif "protected_plan_window_evidence_missing" in blockers:
            status = "sequence_policy_benchmark_review_blocked_pending_ready_inputs"
            recommended_next_step = "repair_protected_plan_window_input_gap"
        else:
            status = "sequence_policy_benchmark_review_blocked_pending_ready_inputs"
            recommended_next_step = (
                "repair_sequence_policy_benchmark_inputs_and_rerun_passive_gate_advancement"
            )
    elif stage4_top3 >= 0.9 and stage7_success_met and stage7_failure_met and not plan_failure_sparse:
        status = "sequence_policy_benchmark_supports_non_causal_sequence_policy_review"
        recommended_next_step = "write_sequence_policy_runtime_or_training_review_packet"
    elif stage4_top3 >= 0.9 and stage7_success_met and stage7_failure_met:
        status = "sequence_policy_benchmark_mixed_plan_window_underpowered"
        recommended_next_step = (
            "obtain_matching_approval_receipt_before_protected_failure_contrast_collection"
        )
    else:
        status = "sequence_policy_benchmark_mixed_or_insufficient"
        recommended_next_step = "review_sequence_policy_objective_or_collect_more_balanced_controls"

    return {
        "schema_version": SCHEMA_VERSION,
        "causal_status": "non_causal_benchmark_review",
        **COMMON_FALSE_FLAGS,
        "source_artifacts": [
            "reports/strategy_arbitration/krk_sequence_policy_benchmark_v0.json"
        ],
        "benchmark_preflight": {
            "benchmark_input_ready": preflight.get("benchmark_input_ready"),
            "blockers": preflight.get("blockers") or [],
            "row_count": preflight.get("row_count"),
            "selector_training_row_count": preflight.get("selector_training_row_count"),
            "runtime_authorization_row_count": preflight.get("runtime_authorization_row_count"),
            "stage7_heldout_row_count": preflight.get("stage7_heldout_row_count"),
        },
        "objective_review": {
            "stage4": {
                "row_count": stage4.get("row_count"),
                "state_count": stage4.get("state_count"),
                "top1_conversion_positive_by_state": stage4_top1,
                "top3_conversion_positive_by_state": stage4_top3,
                "recall": stage4_recall,
                "negative_suppression": stage4_negative_suppression,
                "interpretation": (
                    "topk_signal_present_binary_rule_insufficient"
                    if stage4_top3 >= 0.9 and stage4_recall < 0.7
                    else "stage4_signal_inconclusive"
                ),
            },
            "protected_plan_window": {
                "row_count": plan.get("row_count"),
                "target_label_counts": plan.get("target_label_counts") or {},
                "failure_evidence_sparse": plan_failure_sparse,
                "interpretation": (
                    "needs_more_failure_contrasts"
                    if plan_failure_sparse
                    else "enough_for_initial_review"
                ),
            },
            "stage7_heldout": {
                "row_count": stage7.get("row_count"),
                "target_label_counts": stage7.get("target_label_counts") or {},
                "success_controls_met": stage7_success_met,
                "failure_controls_met": stage7_failure_met,
                "interpretation": (
                    "balanced_heldout_controls"
                    if stage7_success_met and stage7_failure_met
                    else "success_controls_missing"
                    if not stage7_success_met
                    else "failure_controls_missing"
                ),
            },
        },
        "findings": findings,
        "blockers": blockers,
        "decision": {
            "status": status,
            "recommended_next_step": recommended_next_step,
            "runtime_changes_allowed": False,
            "label_run_allowed": False,
            "selector_allowed": False,
            "selector_training_allowed": False,
            "stage7_promotion_allowed": False,
            "stage8_training_allowed": False,
        },
    }


def write_markdown(payload: dict[str, Any]) -> str:
    decision = payload["decision"]
    preflight = payload["benchmark_preflight"]
    review = payload["objective_review"]
    lines = [
        "# KRK Sequence-Policy Benchmark Review v0",
        "",
        f"Status: `{decision['status']}`",
        "",
        "This review is non-causal. It does not train a sequence policy, implement a selector, change runtime behavior, promote Stage 7, or train Stage 8.",
        "",
        "## Preflight",
        "",
    ]
    for key, value in preflight.items():
        lines.append(f"- {key}: `{value}`")
    lines.extend(["", "## Objective Review", ""])
    for name, values in review.items():
        lines.append(f"### {name}")
        for key, value in values.items():
            lines.append(f"- {key}: `{value}`")
        lines.append("")
    lines.extend(["## Findings", ""])
    for finding in payload["findings"]:
        lines.append(f"- `{finding}`")
    if not payload["findings"]:
        lines.append("- none")
    lines.extend(["", "## Blockers", ""])
    for blocker in payload["blockers"]:
        lines.append(f"- `{blocker}`")
    if not payload["blockers"]:
        lines.append("- none")
    lines.extend(
        [
            "",
            "## Decision",
            "",
            f"- recommended_next_step: `{decision['recommended_next_step']}`",
            "- runtime_changes_allowed: `false`",
            "- label_run_allowed: `false`",
            "- selector_training_allowed: `false`",
            "- Stage 7 promotion and Stage 8 training remain blocked.",
        ]
    )
    return "\n".join(lines) + "\n"


def main() -> None:
    payload = build_payload()
    OUTPUT_JSON.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    OUTPUT_MD.write_text(write_markdown(payload), encoding="utf-8")
    print(f"wrote {OUTPUT_JSON.relative_to(ROOT)}")
    print(f"wrote {OUTPUT_MD.relative_to(ROOT)}")
    print(payload["decision"]["status"])


if __name__ == "__main__":
    main()
