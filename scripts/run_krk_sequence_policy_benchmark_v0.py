#!/usr/bin/env python3
"""Run the non-causal KRK sequence-policy benchmark when inputs are ready.

The benchmark is deliberately gate-aware. It reports the specific missing input
class rather than defaulting every not-ready state to Stage 7 label work, and it
never adds runtime behavior or trains a selector.
"""

from __future__ import annotations

import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
INPUTS = ROOT / "reports/strategy_arbitration/krk_sequence_policy_benchmark_inputs_v0.json"
OUTPUT_JSON = ROOT / "reports/strategy_arbitration/krk_sequence_policy_benchmark_v0.json"
OUTPUT_MD = ROOT / "reports/strategy_arbitration/krk_sequence_policy_benchmark_v0.md"

SCHEMA_VERSION = "krk_sequence_policy_benchmark.v0"

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
    return json.loads(path.read_text(encoding="utf-8"))


def _binary_metrics(rows: list[dict[str, Any]], predictions: dict[str, bool]) -> dict[str, Any]:
    tp = fp = tn = fn = 0
    for row in rows:
        predicted = bool(predictions.get(row["row_id"], False))
        positive = row.get("target_label") == "conversion_positive"
        if predicted and positive:
            tp += 1
        elif predicted and not positive:
            fp += 1
        elif not predicted and positive:
            fn += 1
        else:
            tn += 1
    total = tp + fp + tn + fn
    return {
        "true_positive": tp,
        "false_positive": fp,
        "true_negative": tn,
        "false_negative": fn,
        "accuracy": (tp + tn) / total if total else None,
        "precision": tp / (tp + fp) if tp + fp else None,
        "recall": tp / (tp + fn) if tp + fn else None,
        "negative_suppression": tn / (tn + fp) if tn + fp else None,
    }


def _stage4_objective(rows: list[dict[str, Any]]) -> dict[str, Any]:
    stage4 = [row for row in rows if row.get("input_group") == "stage4_first_move_contrast"]
    predictions = {
        row["row_id"]: bool((row.get("features") or {}).get("rook_mid_rank8_cut_candidate"))
        for row in stage4
    }
    by_state: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in stage4:
        by_state[str(row.get("state_id"))].append(row)
    top1_hits = 0
    top3_hits = 0
    state_count = 0
    for state_rows in by_state.values():
        if not state_rows:
            continue
        state_count += 1
        ranked = sorted(
            state_rows,
            key=lambda row: (
                1 if predictions.get(row["row_id"]) else 0,
                -int((row.get("features") or {}).get("target_distance_to_black_king") or 99),
                str(row.get("move_uci")),
            ),
            reverse=True,
        )
        top1_hits += int(ranked[0].get("target_label") == "conversion_positive")
        top3_hits += int(any(row.get("target_label") == "conversion_positive" for row in ranked[:3]))
    metrics = _binary_metrics(stage4, predictions)
    return {
        "objective_id": "stage4_state_local_first_move_contrast",
        "row_count": len(stage4),
        "state_count": state_count,
        "model": "visible_rook_mid_rank8_cut_candidate_topk",
        "metrics": {
            **metrics,
            "top1_conversion_positive_by_state": top1_hits / state_count if state_count else None,
            "top3_conversion_positive_by_state": top3_hits / state_count if state_count else None,
        },
        "runtime_ready": False,
    }


def _plan_window_objective(rows: list[dict[str, Any]]) -> dict[str, Any]:
    plan_rows = [
        row
        for row in rows
        if row.get("input_group")
        in {"protected_plan_window", "protected_plan_window_failure_contrast"}
    ]
    outcome_counts = Counter(row.get("target_label") for row in plan_rows)
    term_counts: dict[str, Counter] = defaultdict(Counter)
    for row in plan_rows:
        label = str(row.get("target_label"))
        features = row.get("features") or {}
        for field in ("entry_terms_confirmed", "progress_terms_after_first_reply", "abort_terms"):
            for term in features.get(field) or []:
                term_counts[f"{field}:{term}"][label] += 1
        if features.get("selected_successor"):
            term_counts[f"selected_successor:{features['selected_successor']}"][label] += 1
    top_terms = []
    for term, counts in term_counts.items():
        total = sum(counts.values())
        top_terms.append(
            {
                "term": term,
                "support": total,
                "success_precision": counts.get("conversion_positive", 0) / total if total else None,
                "failure_precision": counts.get("conversion_failure", 0) / total if total else None,
            }
        )
    top_terms.sort(key=lambda item: (-item["support"], item["term"]))
    return {
        "objective_id": "protected_plan_window_entry_progress_exit_abort",
        "row_count": len(plan_rows),
        "input_group_counts": dict(Counter(row.get("input_group") for row in plan_rows)),
        "target_label_counts": dict(outcome_counts),
        "failure_evidence_sparse": outcome_counts.get("conversion_failure", 0) < 5,
        "top_terms": top_terms[:10],
        "runtime_ready": False,
    }


def _stage7_holdout_objective(rows: list[dict[str, Any]]) -> dict[str, Any]:
    stage7 = [row for row in rows if row.get("input_group") == "stage7_clean_heldout_control"]
    provider_counts = Counter((row.get("features") or {}).get("selected_provider") for row in stage7)
    outcome_counts = Counter(row.get("target_label") for row in stage7)
    alignment_counts = Counter((row.get("features") or {}).get("semantic_alignment_status") for row in stage7)
    return {
        "objective_id": "stage7_heldout_sequence_success_vs_hard_negative",
        "row_count": len(stage7),
        "target_label_counts": dict(outcome_counts),
        "selected_provider_counts": {str(key): value for key, value in provider_counts.items()},
        "semantic_alignment_counts": {str(key): value for key, value in alignment_counts.items()},
        "success_controls_met": outcome_counts.get("conversion_positive", 0) >= 5,
        "failure_controls_met": outcome_counts.get("conversion_failure", 0) >= 5,
        "runtime_ready": False,
    }


def build_payload(*, inputs: dict[str, Any] | None = None) -> dict[str, Any]:
    inputs = inputs or _load(INPUTS)
    rows = inputs.get("rows") or []
    summary = inputs.get("summary") or {}
    input_ready = bool(summary.get("benchmark_input_ready"))
    blockers = []
    if not summary.get("protected_plan_window_evidence_met"):
        blockers.append("protected_plan_window_evidence_missing")
    if not summary.get("stage7_clean_success_controls_met"):
        blockers.append("stage7_clean_success_controls_missing")
    if not summary.get("stage7_clean_failure_controls_met"):
        blockers.append("stage7_clean_failure_controls_missing")
    selector_training_row_count = sum(
        1 for row in rows if row.get("usable_for_selector_training")
    )
    runtime_authorization_row_count = sum(
        1 for row in rows if row.get("usable_for_runtime_authorization")
    )
    if selector_training_row_count:
        blockers.append("selector_training_rows_forbidden")
    if runtime_authorization_row_count:
        blockers.append("runtime_authorization_rows_forbidden")
    benchmark_can_execute = input_ready and not blockers

    objectives = [
        _stage4_objective(rows),
        _plan_window_objective(rows),
        _stage7_holdout_objective(rows),
    ]
    status = (
        "sequence_policy_benchmark_ready_non_causal_results_available"
        if benchmark_can_execute
        else "sequence_policy_benchmark_blocked_forbidden_training_or_runtime_rows"
        if (
            "selector_training_rows_forbidden" in blockers
            or "runtime_authorization_rows_forbidden" in blockers
        )
        else "sequence_policy_benchmark_blocked_pending_stage7_success_controls"
        if "stage7_clean_success_controls_missing" in blockers
        else "sequence_policy_benchmark_blocked_pending_stage7_failure_controls"
        if "stage7_clean_failure_controls_missing" in blockers
        else "sequence_policy_benchmark_blocked_pending_protected_plan_window_evidence"
        if "protected_plan_window_evidence_missing" in blockers
        else "sequence_policy_benchmark_blocked_pending_inputs"
    )
    recommended_next_step = (
        "review_non_causal_sequence_policy_results"
        if benchmark_can_execute
        else "repair_sequence_policy_inputs_remove_training_or_runtime_rows"
        if (
            "selector_training_rows_forbidden" in blockers
            or "runtime_authorization_rows_forbidden" in blockers
        )
        else "fill_stage7_clean_success_controls_before_treating_benchmark_as_ready"
        if "stage7_clean_success_controls_missing" in blockers
        else "fill_stage7_clean_failure_controls_before_treating_benchmark_as_ready"
        if "stage7_clean_failure_controls_missing" in blockers
        else "repair_protected_plan_window_input_gap_before_treating_benchmark_as_ready"
        if "protected_plan_window_evidence_missing" in blockers
        else "repair_sequence_policy_input_gap_before_treating_benchmark_as_ready"
    )
    return {
        "schema_version": SCHEMA_VERSION,
        "causal_status": "non_causal_sequence_policy_benchmark",
        **COMMON_FALSE_FLAGS,
        "source_artifacts": [
            "reports/strategy_arbitration/krk_sequence_policy_benchmark_inputs_v0.json"
        ],
        "preflight": {
            "benchmark_input_ready": input_ready,
            "blockers": blockers,
            "row_count": len(rows),
            "selector_training_row_count": selector_training_row_count,
            "runtime_authorization_row_count": runtime_authorization_row_count,
            "stage7_heldout_row_count": sum(
                1 for row in rows if row.get("stage7_heldout_challenge")
            ),
        },
        "objectives": objectives,
        "decision": {
            "status": status,
            "benchmark_executed_as_ready": benchmark_can_execute,
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
    preflight = payload["preflight"]
    lines = [
        "# KRK Sequence-Policy Benchmark v0",
        "",
        f"Status: `{decision['status']}`",
        "",
        "This is a non-causal benchmark harness. It does not train a model, select moves, change runtime behavior, promote Stage 7, or train Stage 8.",
        "",
        "## Preflight",
        "",
    ]
    for key, value in preflight.items():
        lines.append(f"- {key}: `{value}`")
    lines.extend(["", "## Objectives", ""])
    for objective in payload["objectives"]:
        lines.append(
            f"- `{objective['objective_id']}` rows=`{objective['row_count']}` runtime_ready=`{objective['runtime_ready']}`"
        )
    lines.extend(
        [
            "",
            "## Decision",
            "",
            f"- benchmark_executed_as_ready: `{decision['benchmark_executed_as_ready']}`",
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
                "benchmark_executed_as_ready": payload["decision"][
                    "benchmark_executed_as_ready"
                ],
                "blockers": payload["preflight"]["blockers"],
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
