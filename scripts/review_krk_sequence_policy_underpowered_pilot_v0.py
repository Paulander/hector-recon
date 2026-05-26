#!/usr/bin/env python3
"""Review the current underpowered KRK sequence-policy pilot.

This is a non-causal diagnostic over the already assembled benchmark and
backfill-audit artifacts. It deliberately does not relax the full benchmark
gate. Its purpose is to preserve useful signal from current data while making
the remaining evidence gap explicit.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
BENCHMARK = ROOT / "reports/strategy_arbitration/krk_sequence_policy_benchmark_v0.json"
BENCHMARK_REVIEW = (
    ROOT / "reports/strategy_arbitration/krk_sequence_policy_benchmark_review_v0.json"
)
INPUTS = ROOT / "reports/strategy_arbitration/krk_sequence_policy_benchmark_inputs_v0.json"
BACKFILL_AUDIT = ROOT / "reports/structural_candidates/stage7_clean_success_backfill_audit_v0.json"
READINESS = ROOT / "reports/krk_full_suite_readiness_audit_v0.json"
OUTPUT_JSON = ROOT / "reports/strategy_arbitration/krk_sequence_policy_underpowered_pilot_v0.json"
OUTPUT_MD = ROOT / "reports/strategy_arbitration/krk_sequence_policy_underpowered_pilot_v0.md"

SCHEMA_VERSION = "krk_sequence_policy_underpowered_pilot.v0"

FORBIDDEN_INPUT_BLOCKERS = {
    "selector_training_rows_forbidden",
    "runtime_authorization_rows_forbidden",
}

FORBIDDEN_INPUT_STATUSES = {
    "sequence_policy_benchmark_blocked_forbidden_training_or_runtime_rows",
    "sequence_policy_benchmark_review_blocked_forbidden_training_or_runtime_rows",
}

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


def _objective(benchmark: dict[str, Any], objective_id: str) -> dict[str, Any]:
    for objective in benchmark.get("objectives") or []:
        if objective.get("objective_id") == objective_id:
            return objective
    return {}


def build_payload(
    *,
    benchmark: dict[str, Any] | None = None,
    benchmark_review: dict[str, Any] | None = None,
    inputs: dict[str, Any] | None = None,
    backfill_audit: dict[str, Any] | None = None,
    readiness: dict[str, Any] | None = None,
) -> dict[str, Any]:
    benchmark = benchmark or _load(BENCHMARK)
    benchmark_review = benchmark_review or _load(BENCHMARK_REVIEW)
    inputs = inputs or _load(INPUTS)
    backfill_audit = backfill_audit or _load(BACKFILL_AUDIT)
    readiness = readiness or _load(READINESS)

    stage4 = _objective(benchmark, "stage4_state_local_first_move_contrast")
    plan_window = _objective(benchmark, "protected_plan_window_entry_progress_exit_abort")
    stage7 = _objective(benchmark, "stage7_heldout_sequence_success_vs_hard_negative")
    stage4_metrics = stage4.get("metrics") or {}
    stage7_counts = stage7.get("target_label_counts") or {}
    plan_counts = plan_window.get("target_label_counts") or {}
    input_summary = inputs.get("summary") or {}
    benchmark_preflight = benchmark.get("preflight") or {}
    benchmark_decision = benchmark.get("decision") or {}
    benchmark_review_decision = benchmark_review.get("decision") or {}
    backfill_summary = backfill_audit.get("summary") or {}
    protected_failure_contrast = readiness.get("protected_failure_contrast_gate") or {}
    sequence_policy = readiness.get("sequence_policy") or {}
    readiness_boundaries = readiness.get("runtime_and_training_boundaries") or {}
    explicit_gate_blockers = set(readiness.get("explicit_gate_blockers") or [])
    protected_failure_contrast_request_status = protected_failure_contrast.get(
        "approval_request_status"
    )
    protected_failure_contrast_request_blockers = (
        protected_failure_contrast.get("approval_request_blockers") or []
    )
    protected_failure_contrast_request_ready_value = protected_failure_contrast.get(
        "approval_request_ready_for_collection"
    )
    protected_failure_contrast_request_ready = (
        bool(protected_failure_contrast_request_ready_value)
        if protected_failure_contrast_request_ready_value is not None
        else (
            not protected_failure_contrast_request_blockers
            and protected_failure_contrast_request_status
            in (None, "protected_plan_window_failure_contrast_approval_request_ready")
        )
    )
    protected_failure_contrast_pending_approval = (
        "protected_plan_window_failure_contrast_collection_pending_explicit_approval"
        in explicit_gate_blockers
        and protected_failure_contrast_request_ready
    )
    protected_failure_contrast_ready_value = protected_failure_contrast.get(
        "ready_for_explicit_approval"
    )
    protected_failure_contrast_gate_ready = (
        bool(protected_failure_contrast_ready_value)
        if protected_failure_contrast_ready_value is not None
        else (
            protected_failure_contrast.get("status")
            == "protected_plan_window_failure_contrast_execution_ready_pending_explicit_approval"
            or protected_failure_contrast_pending_approval
        )
    )
    protected_failure_contrast_ready_for_explicit_approval = (
        protected_failure_contrast_gate_ready
        and protected_failure_contrast_request_ready
    )

    stage4_topk_signal = (
        (stage4_metrics.get("top1_conversion_positive_by_state") or 0) >= 0.7
        and (stage4_metrics.get("top3_conversion_positive_by_state") or 0) >= 0.8
    )
    stage4_binary_insufficient = not (
        (stage4_metrics.get("precision") or 0) >= 0.7
        and (stage4_metrics.get("recall") or 0) >= 0.7
        and (stage4_metrics.get("negative_suppression") or 0) >= 0.8
    )
    protected_plan_window_underpowered = bool(plan_window.get("failure_evidence_sparse"))
    stage7_success_gap = max(
        0,
        int(input_summary.get("stage7_clean_success_controls_required") or 5)
        - int(stage7_counts.get("conversion_positive") or 0),
    )
    replay_free_backfill_exhausted = (
        backfill_audit.get("decision", {}).get("status")
        == "stage7_clean_success_backfill_exhausted_pending_label_execution"
    )
    forbidden_input_blockers_set = FORBIDDEN_INPUT_BLOCKERS & (
        set(benchmark_preflight.get("blockers") or [])
        | set(benchmark_review.get("blockers") or [])
    )
    if int(input_summary.get("selector_training_row_count") or 0) > 0:
        forbidden_input_blockers_set.add("selector_training_rows_forbidden")
    if int(input_summary.get("runtime_authorization_row_count") or 0) > 0:
        forbidden_input_blockers_set.add("runtime_authorization_rows_forbidden")
    forbidden_input_blockers = sorted(forbidden_input_blockers_set)
    forbidden_training_or_runtime_inputs = bool(forbidden_input_blockers) or (
        benchmark_decision.get("status") in FORBIDDEN_INPUT_STATUSES
        or benchmark_review_decision.get("status") in FORBIDDEN_INPUT_STATUSES
    )

    findings: list[str] = []
    blockers: list[str] = []
    if stage4_topk_signal:
        findings.append("stage4_state_local_topk_signal_present")
    if stage4_binary_insufficient:
        findings.append("stage4_one_term_binary_rule_insufficient")
    if protected_plan_window_underpowered:
        if not protected_failure_contrast_request_ready:
            blockers.append(
                "protected_plan_window_failure_contrast_approval_request_blocked"
            )
        elif protected_failure_contrast_pending_approval:
            blockers.append(
                "protected_plan_window_failure_contrast_collection_pending_explicit_approval"
            )
        else:
            blockers.append("protected_plan_window_failure_evidence_sparse")
    if stage7_success_gap:
        blockers.append("stage7_clean_success_controls_missing")
    if replay_free_backfill_exhausted:
        blockers.append("stage7_replay_free_backfill_exhausted")
    if forbidden_training_or_runtime_inputs:
        blockers.extend(forbidden_input_blockers or ["forbidden_training_or_runtime_rows"])

    if forbidden_training_or_runtime_inputs:
        decision_status = "sequence_policy_pilot_blocked_forbidden_training_or_runtime_rows"
        recommended_next_step = "repair_sequence_policy_inputs_remove_training_or_runtime_rows"
    elif stage4_topk_signal and stage7_success_gap and replay_free_backfill_exhausted:
        decision_status = "sequence_policy_pilot_ready_for_full_benchmark_after_label_gate"
        recommended_next_step = (
            "explicitly_approve_stage7_diverse_clean_label_execution_before_full_sequence_policy_benchmark"
        )
    elif protected_plan_window_underpowered and not protected_failure_contrast_request_ready:
        decision_status = (
            "sequence_policy_pilot_blocked_pending_protected_failure_contrast_approval_request_repair"
        )
        recommended_next_step = "repair_protected_failure_contrast_approval_request_scope"
    elif protected_plan_window_underpowered and protected_failure_contrast_pending_approval:
        decision_status = (
            "sequence_policy_pilot_underpowered_pending_protected_failure_contrast_collection"
        )
        recommended_next_step = (
            "obtain_matching_approval_receipt_before_protected_failure_contrast_collection"
        )
    else:
        decision_status = "sequence_policy_pilot_underpowered_needs_review"
        recommended_next_step = "review_underpowered_sequence_policy_pilot"

    if (
        not forbidden_training_or_runtime_inputs
        and stage7_success_gap
        and replay_free_backfill_exhausted
    ):
        recommended_next_step = (
            "explicitly_approve_stage7_diverse_clean_label_execution_before_full_sequence_policy_benchmark"
        )

    return {
        "schema_version": SCHEMA_VERSION,
        "causal_status": "non_causal_underpowered_pilot_review",
        **COMMON_FALSE_FLAGS,
        "source_artifacts": [
            "reports/strategy_arbitration/krk_sequence_policy_benchmark_v0.json",
            "reports/strategy_arbitration/krk_sequence_policy_benchmark_review_v0.json",
            "reports/strategy_arbitration/krk_sequence_policy_benchmark_inputs_v0.json",
            "reports/structural_candidates/stage7_clean_success_backfill_audit_v0.json",
            "reports/krk_full_suite_readiness_audit_v0.json",
        ],
        "summary": {
            "benchmark_executed_as_ready": bool(
                benchmark_decision.get("benchmark_executed_as_ready")
            ),
            "benchmark_status": benchmark_decision.get("status"),
            "benchmark_preflight_blockers": benchmark_preflight.get("blockers") or [],
            "benchmark_review_status": benchmark_review_decision.get("status"),
            "benchmark_review_blockers": benchmark_review.get("blockers") or [],
            "readiness_checked_flag_count": readiness_boundaries.get(
                "checked_flag_count"
            ),
            "readiness_boundary_violation_count": readiness_boundaries.get(
                "violation_count"
            ),
            "readiness_source_artifact_count": len(
                readiness.get("source_artifacts") or {}
            ),
            "forbidden_training_or_runtime_input_blocked": (
                forbidden_training_or_runtime_inputs
            ),
            "input_row_count": input_summary.get("row_count"),
            "stage4_topk_signal": stage4_topk_signal,
            "stage4_binary_rule_insufficient": stage4_binary_insufficient,
            "protected_plan_window_failure_evidence_sparse": protected_plan_window_underpowered,
            "stage7_success_controls": stage7_counts.get("conversion_positive", 0),
            "stage7_failure_controls": stage7_counts.get("conversion_failure", 0),
            "stage7_success_gap": stage7_success_gap,
            "stage7_replay_free_backfill_exhausted": replay_free_backfill_exhausted,
            "stage7_backfillable_success_controls": backfill_summary.get(
                "eligible_new_success_controls"
            ),
            "protected_failure_contrast_ready_for_explicit_approval": (
                protected_failure_contrast_ready_for_explicit_approval
            ),
            "protected_failure_contrast_integration_ready": (
                protected_failure_contrast.get("integration_ready")
            ),
            "protected_failure_contrast_runner_status": protected_failure_contrast.get(
                "runner_status"
            ),
            "protected_failure_contrast_runner_manifest_status": (
                protected_failure_contrast.get("runner_manifest_status")
            ),
            "protected_failure_contrast_runner_manifest_declared_job_count": (
                protected_failure_contrast.get("runner_manifest_declared_job_count")
            ),
            "protected_failure_contrast_runner_manifest_fingerprint": (
                protected_failure_contrast.get("runner_manifest_fingerprint")
            ),
            "protected_failure_contrast_runner_collection_run_allowed": (
                protected_failure_contrast.get("runner_collection_run_allowed")
            ),
            "protected_failure_contrast_runner_processed_job_count": (
                protected_failure_contrast.get("runner_processed_job_count")
            ),
            "protected_failure_contrast_runner_executed_job_count": (
                protected_failure_contrast.get("runner_executed_job_count")
            ),
            "protected_failure_contrast_command_if_explicitly_approved": (
                protected_failure_contrast.get("command_if_explicitly_approved")
            ),
            "protected_failure_contrast_approval_request_artifact": (
                protected_failure_contrast.get("approval_request_artifact")
            ),
            "protected_failure_contrast_approval_request_status": (
                protected_failure_contrast_request_status
            ),
            "protected_failure_contrast_approval_request_blockers": (
                protected_failure_contrast_request_blockers
            ),
            "protected_failure_contrast_approval_request_ready_for_collection": (
                protected_failure_contrast_request_ready
            ),
            "protected_failure_contrast_approval_receipt_created_by_request": (
                protected_failure_contrast.get("approval_receipt_created_by_request")
            ),
            "protected_failure_contrast_approval_receipt_blockers": (
                protected_failure_contrast.get("approval_receipt_blockers") or []
            ),
            "protected_failure_contrast_post_success_refresh_required": (
                protected_failure_contrast.get("post_success_refresh_required")
            ),
            "protected_failure_contrast_post_success_refresh_script": (
                protected_failure_contrast.get("post_success_refresh_script")
            ),
            "protected_failure_contrast_post_success_refresh_scope": (
                protected_failure_contrast.get("post_success_refresh_scope")
            ),
            "protected_failure_contrast_runtime_behavior_changed": (
                protected_failure_contrast.get("runtime_behavior_changed", False)
            ),
            "protected_failure_contrast_runtime_defaults_changed": (
                protected_failure_contrast.get("runtime_defaults_changed", False)
            ),
            "protected_failure_contrast_runtime_selector_implemented": (
                protected_failure_contrast.get("runtime_selector_implemented", False)
            ),
            "protected_failure_contrast_runtime_score_changes": (
                protected_failure_contrast.get("runtime_score_changes", False)
            ),
            "protected_failure_contrast_runtime_direct_routing": (
                protected_failure_contrast.get("runtime_direct_routing", False)
            ),
            "protected_failure_contrast_runtime_dtm_or_tablebase_lookup": (
                protected_failure_contrast.get("runtime_dtm_or_tablebase_lookup", False)
            ),
            "protected_failure_contrast_hidden_python_controller": (
                protected_failure_contrast.get("hidden_python_controller", False)
            ),
            "protected_failure_contrast_gameplay_topology_mutation": (
                protected_failure_contrast.get("gameplay_topology_mutation", False)
            ),
            "protected_failure_contrast_selector_training_allowed": (
                protected_failure_contrast.get("selector_training_allowed", False)
            ),
            "protected_failure_contrast_stage7_promotion_allowed": (
                protected_failure_contrast.get("stage7_promotion_allowed", False)
            ),
            "protected_failure_contrast_stage8_training_allowed": (
                protected_failure_contrast.get("stage8_training_allowed", False)
            ),
            "sequence_policy_after_protected_failure_contrast_refresh_status": (
                sequence_policy.get("post_failure_contrast_refresh_status")
            ),
            "sequence_policy_after_protected_failure_contrast_boundaries_preserved": (
                sequence_policy.get("post_failure_contrast_refresh_boundaries_preserved")
            ),
            "sequence_policy_after_protected_failure_contrast_boundary_violation_count": (
                sequence_policy.get(
                    "post_failure_contrast_refresh_boundary_violation_count"
                )
            ),
            "sequence_policy_after_protected_failure_contrast_rows": (
                sequence_policy.get("post_failure_contrast_refresh_row_count")
            ),
            "sequence_policy_after_protected_failure_contrast_stage7_training_row_count": (
                sequence_policy.get(
                    "post_failure_contrast_refresh_stage7_training_row_count"
                )
            ),
            "selector_training_row_count": input_summary.get("selector_training_row_count"),
            "runtime_authorization_row_count": input_summary.get(
                "runtime_authorization_row_count"
            ),
            "stage7_training_row_count": 0,
        },
        "pilot_findings": findings,
        "blockers": blockers,
        "stage4_signal": {
            "row_count": stage4.get("row_count"),
            "state_count": stage4.get("state_count"),
            "top1_conversion_positive_by_state": stage4_metrics.get(
                "top1_conversion_positive_by_state"
            ),
            "top3_conversion_positive_by_state": stage4_metrics.get(
                "top3_conversion_positive_by_state"
            ),
            "precision": stage4_metrics.get("precision"),
            "recall": stage4_metrics.get("recall"),
            "negative_suppression": stage4_metrics.get("negative_suppression"),
            "interpretation": (
                "state_local_ranking_signal_present_but_one_term_binary_rule_insufficient"
                if stage4_topk_signal and stage4_binary_insufficient
                else "stage4_signal_not_established"
            ),
        },
        "protected_plan_window_signal": {
            "row_count": plan_window.get("row_count"),
            "target_label_counts": plan_counts,
            "failure_evidence_sparse": protected_plan_window_underpowered,
        },
        "stage7_heldout_signal": {
            "row_count": stage7.get("row_count"),
            "target_label_counts": stage7_counts,
            "success_controls_met": stage7.get("success_controls_met"),
            "failure_controls_met": stage7.get("failure_controls_met"),
            "replay_free_backfill_exhausted": replay_free_backfill_exhausted,
        },
        "decision": {
            "status": decision_status,
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
    summary = payload["summary"]
    decision = payload["decision"]
    lines = [
        "# KRK Sequence-Policy Underpowered Pilot v0",
        "",
        f"Status: `{decision['status']}`",
        "",
        "This is a non-causal pilot review over underpowered inputs. It preserves diagnostic signal but does not relax the full benchmark gate, authorize labels, train a selector, change runtime behavior, promote Stage 7, or train Stage 8.",
        "",
        "## Summary",
        "",
    ]
    for key, value in summary.items():
        lines.append(f"- {key}: `{value}`")
    lines.extend(["", "## Findings", ""])
    for finding in payload["pilot_findings"]:
        lines.append(f"- `{finding}`")
    lines.extend(["", "## Blockers", ""])
    for blocker in payload["blockers"]:
        lines.append(f"- `{blocker}`")
    stage4 = payload["stage4_signal"]
    lines.extend(
        [
            "",
            "## Stage 4 Signal",
            "",
            f"- interpretation: `{stage4['interpretation']}`",
            f"- top1_conversion_positive_by_state: `{stage4['top1_conversion_positive_by_state']}`",
            f"- top3_conversion_positive_by_state: `{stage4['top3_conversion_positive_by_state']}`",
            f"- precision: `{stage4['precision']}`",
            f"- recall: `{stage4['recall']}`",
            f"- negative_suppression: `{stage4['negative_suppression']}`",
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
    print(
        json.dumps(
            {
                "decision": payload["decision"]["status"],
                "stage4_topk_signal": payload["summary"]["stage4_topk_signal"],
                "stage7_success_gap": payload["summary"]["stage7_success_gap"],
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
