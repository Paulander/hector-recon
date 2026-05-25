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
INPUTS = ROOT / "reports/strategy_arbitration/krk_sequence_policy_benchmark_inputs_v0.json"
BACKFILL_AUDIT = ROOT / "reports/structural_candidates/stage7_clean_success_backfill_audit_v0.json"
OUTPUT_JSON = ROOT / "reports/strategy_arbitration/krk_sequence_policy_underpowered_pilot_v0.json"
OUTPUT_MD = ROOT / "reports/strategy_arbitration/krk_sequence_policy_underpowered_pilot_v0.md"

SCHEMA_VERSION = "krk_sequence_policy_underpowered_pilot.v0"

COMMON_FALSE_FLAGS = {
    "runtime_behavior_changed": False,
    "runtime_defaults_changed": False,
    "runtime_selector_implemented": False,
    "runtime_score_changes": False,
    "runtime_direct_routing": False,
    "runtime_dtm_or_tablebase_lookup": False,
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
    inputs: dict[str, Any] | None = None,
    backfill_audit: dict[str, Any] | None = None,
) -> dict[str, Any]:
    benchmark = benchmark or _load(BENCHMARK)
    inputs = inputs or _load(INPUTS)
    backfill_audit = backfill_audit or _load(BACKFILL_AUDIT)

    stage4 = _objective(benchmark, "stage4_state_local_first_move_contrast")
    plan_window = _objective(benchmark, "protected_plan_window_entry_progress_exit_abort")
    stage7 = _objective(benchmark, "stage7_heldout_sequence_success_vs_hard_negative")
    stage4_metrics = stage4.get("metrics") or {}
    stage7_counts = stage7.get("target_label_counts") or {}
    plan_counts = plan_window.get("target_label_counts") or {}
    input_summary = inputs.get("summary") or {}
    backfill_summary = backfill_audit.get("summary") or {}

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

    findings: list[str] = []
    blockers: list[str] = []
    if stage4_topk_signal:
        findings.append("stage4_state_local_topk_signal_present")
    if stage4_binary_insufficient:
        findings.append("stage4_one_term_binary_rule_insufficient")
    if protected_plan_window_underpowered:
        blockers.append("protected_plan_window_failure_evidence_sparse")
    if stage7_success_gap:
        blockers.append("stage7_clean_success_controls_missing")
    if replay_free_backfill_exhausted:
        blockers.append("stage7_replay_free_backfill_exhausted")

    decision_status = (
        "sequence_policy_pilot_ready_for_full_benchmark_after_label_gate"
        if stage4_topk_signal and stage7_success_gap and replay_free_backfill_exhausted
        else "sequence_policy_pilot_underpowered_needs_review"
    )

    return {
        "schema_version": SCHEMA_VERSION,
        "causal_status": "non_causal_underpowered_pilot_review",
        **COMMON_FALSE_FLAGS,
        "source_artifacts": [
            "reports/strategy_arbitration/krk_sequence_policy_benchmark_v0.json",
            "reports/strategy_arbitration/krk_sequence_policy_benchmark_inputs_v0.json",
            "reports/structural_candidates/stage7_clean_success_backfill_audit_v0.json",
        ],
        "summary": {
            "benchmark_executed_as_ready": bool(
                benchmark.get("decision", {}).get("benchmark_executed_as_ready")
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
            "recommended_next_step": (
                "explicitly_approve_stage7_diverse_clean_label_execution_before_full_sequence_policy_benchmark"
                if stage7_success_gap and replay_free_backfill_exhausted
                else "review_underpowered_sequence_policy_pilot"
            ),
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
