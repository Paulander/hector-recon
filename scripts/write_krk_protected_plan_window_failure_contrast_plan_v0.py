#!/usr/bin/env python3
"""Write a passive plan for protected plan-window failure contrasts.

This artifact scopes the evidence gap left by the non-causal sequence-policy
benchmark. It does not execute labels, train a selector, change runtime
behavior, promote Stage 7, or authorize Stage 8.
"""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
INPUTS = ROOT / "reports/strategy_arbitration/krk_sequence_policy_benchmark_inputs_v0.json"
BENCHMARK = ROOT / "reports/strategy_arbitration/krk_sequence_policy_benchmark_v0.json"
BENCHMARK_REVIEW = (
    ROOT / "reports/strategy_arbitration/krk_sequence_policy_benchmark_review_v0.json"
)
PROTECTED_WINDOWS = ROOT / "reports/strategy_arbitration/krk_protected_plan_window_frames_v0.json"
OUTPUT_JSON = (
    ROOT
    / "reports/strategy_arbitration/krk_protected_plan_window_failure_contrast_plan_v0.json"
)
OUTPUT_MD = (
    ROOT
    / "reports/strategy_arbitration/krk_protected_plan_window_failure_contrast_plan_v0.md"
)

SCHEMA_VERSION = "krk_protected_plan_window_failure_contrast_plan.v0"
MIN_FAILURE_CONTRASTS = 5

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

FORBIDDEN_INPUT_FLAGS = (
    "runtime_behavior_changed",
    "runtime_defaults_changed",
    "runtime_selector_implemented",
    "runtime_score_changes",
    "runtime_direct_routing",
    "runtime_dtm_or_tablebase_lookup",
    "gameplay_topology_mutation",
    "runtime_changes_allowed",
    "label_run_allowed",
    "selector_allowed",
    "selector_training_allowed",
    "usable_for_selector_training",
    "usable_for_runtime_authorization",
    "stage7_heldout_challenge",
    "stage7_promotion_allowed",
    "stage8_training_allowed",
)


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


def _plan_rows(inputs: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        row
        for row in inputs.get("rows") or []
        if row.get("input_group") == "protected_plan_window"
    ]


def _unique_key(row: dict[str, Any]) -> tuple[Any, ...]:
    return (
        row.get("state_id"),
        row.get("fen"),
        row.get("move_uci"),
        row.get("target_label"),
        row.get("outcome"),
    )


def _unique_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    deduped: list[dict[str, Any]] = []
    seen: set[tuple[Any, ...]] = set()
    for row in rows:
        key = _unique_key(row)
        if key in seen:
            continue
        seen.add(key)
        deduped.append(row)
    return deduped


def _count(rows: list[dict[str, Any]], key: str) -> dict[str, int]:
    return dict(Counter(str(row.get(key)) for row in rows))


def _counter_from_features(rows: list[dict[str, Any]], field: str) -> dict[str, int]:
    counts: Counter[str] = Counter()
    for row in rows:
        for value in (row.get("features") or {}).get(field) or []:
            counts[str(value)] += 1
    return dict(counts)


def _rows_with_truthy_flag(rows: list[dict[str, Any]], *flags: str) -> list[dict[str, Any]]:
    return [row for row in rows if any(row.get(flag) is True for flag in flags)]


def _forbidden_input_flag_counts(rows: list[dict[str, Any]]) -> dict[str, int]:
    return {
        flag: sum(1 for row in rows if row.get(flag) is True)
        for flag in FORBIDDEN_INPUT_FLAGS
    }


def _family_targets(unique_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    failure_rows = [row for row in unique_rows if row.get("target_label") == "conversion_failure"]
    failure_by_family = Counter(str(row.get("source_family")) for row in failure_rows)
    failure_by_stage = Counter(str(row.get("source_stage")) for row in failure_rows)
    families = sorted({str(row.get("source_family")) for row in unique_rows})
    targets = []
    for family in families:
        family_rows = [row for row in unique_rows if str(row.get("source_family")) == family]
        stage_counts = Counter(str(row.get("source_stage")) for row in family_rows)
        targets.append(
            {
                "source_family": family,
                "source_stage_counts": dict(stage_counts),
                "current_unique_failure_count": failure_by_family.get(family, 0),
                "recommended_min_new_failures": 1
                if failure_by_family.get(family, 0) == 0
                else 0,
                "priority": (
                    "high_no_current_failure_contrast"
                    if failure_by_family.get(family, 0) == 0
                    else "medium_existing_failure_contrast"
                ),
            }
        )
    for stage in sorted({str(row.get("source_stage")) for row in unique_rows}):
        if failure_by_stage.get(stage, 0):
            continue
        targets.append(
            {
                "source_family": f"{stage}_any_protected_plan_window",
                "source_stage_counts": {stage: sum(1 for row in unique_rows if row.get("source_stage") == stage)},
                "current_unique_failure_count": 0,
                "recommended_min_new_failures": 1,
                "priority": "high_no_current_stage_failure_contrast",
            }
        )
    return targets


def build_payload(
    *,
    inputs: dict[str, Any] | None = None,
    benchmark: dict[str, Any] | None = None,
    benchmark_review: dict[str, Any] | None = None,
    protected_windows: dict[str, Any] | None = None,
) -> dict[str, Any]:
    inputs = inputs or _load(INPUTS)
    benchmark = benchmark or _load(BENCHMARK)
    benchmark_review = benchmark_review or _load(BENCHMARK_REVIEW)
    protected_windows = protected_windows or _load(PROTECTED_WINDOWS)

    rows = _plan_rows(inputs)
    unique_rows = _unique_rows(rows)
    duplicate_row_count = len(rows) - len(unique_rows)
    failure_rows = [row for row in unique_rows if row.get("target_label") == "conversion_failure"]
    success_rows = [row for row in unique_rows if row.get("target_label") == "conversion_positive"]
    failure_gap = max(0, MIN_FAILURE_CONTRASTS - len(failure_rows))
    review_status = benchmark_review.get("decision", {}).get("status")
    plan_objective = _objective(benchmark, "protected_plan_window_entry_progress_exit_abort")
    blocker_present = "protected_plan_window_failure_evidence_sparse" in (
        benchmark_review.get("blockers") or []
    )
    forbidden_flag_counts = _forbidden_input_flag_counts(unique_rows)
    selector_training_rows = _rows_with_truthy_flag(
        unique_rows, "selector_training_allowed", "usable_for_selector_training"
    )
    runtime_authorization_rows = _rows_with_truthy_flag(
        unique_rows,
        "runtime_changes_allowed",
        "selector_allowed",
        "usable_for_runtime_authorization",
    )
    stage7_training_rows = _rows_with_truthy_flag(
        unique_rows, "stage7_heldout_challenge", "stage7_promotion_allowed"
    )
    forbidden_input_row_count = sum(
        1
        for row in unique_rows
        if any(row.get(flag) is True for flag in FORBIDDEN_INPUT_FLAGS)
    )

    collection_units = [
        {
            "unit_id": "protected_plan_window_failure_contrast_minimum",
            "purpose": "Raise unique protected plan-window failure contrasts to the non-causal benchmark minimum.",
            "current_unique_failures": len(failure_rows),
            "minimum_required_unique_failures": MIN_FAILURE_CONTRASTS,
            "minimum_new_unique_failures_needed": failure_gap,
            "approval_required_before_label_execution": True,
        },
        {
            "unit_id": "cross_stage_failure_balance",
            "purpose": "Avoid a Stage 4-only failure slice by adding Stage 5/6 protected-window failures if available.",
            "current_failure_stage_counts": _count(failure_rows, "source_stage"),
            "target_families": _family_targets(unique_rows),
            "approval_required_before_label_execution": True,
        },
    ]

    status = (
        "protected_plan_window_failure_contrast_plan_blocked_forbidden_training_or_runtime_rows"
        if forbidden_input_row_count
        else "protected_plan_window_failure_contrast_plan_ready_pending_explicit_collection_approval"
        if blocker_present and failure_gap
        else "protected_plan_window_failure_contrast_plan_not_needed"
        if not failure_gap
        else "protected_plan_window_failure_contrast_plan_waiting_on_benchmark_review"
    )

    return {
        "schema_version": SCHEMA_VERSION,
        "causal_status": "non_causal_failure_contrast_collection_plan",
        **COMMON_FALSE_FLAGS,
        "source_artifacts": [
            "reports/strategy_arbitration/krk_sequence_policy_benchmark_inputs_v0.json",
            "reports/strategy_arbitration/krk_sequence_policy_benchmark_v0.json",
            "reports/strategy_arbitration/krk_sequence_policy_benchmark_review_v0.json",
            "reports/strategy_arbitration/krk_protected_plan_window_frames_v0.json",
        ],
        "summary": {
            "benchmark_review_status": review_status,
            "benchmark_objective_row_count": plan_objective.get("row_count"),
            "benchmark_failure_evidence_sparse": plan_objective.get("failure_evidence_sparse"),
            "input_row_count": len(rows),
            "unique_row_count": len(unique_rows),
            "duplicate_row_count": duplicate_row_count,
            "unique_success_count": len(success_rows),
            "unique_failure_count": len(failure_rows),
            "minimum_required_unique_failures": MIN_FAILURE_CONTRASTS,
            "minimum_new_unique_failures_needed": failure_gap,
            "failure_source_stage_counts": _count(failure_rows, "source_stage"),
            "failure_source_family_counts": _count(failure_rows, "source_family"),
            "success_source_stage_counts": _count(success_rows, "source_stage"),
            "success_source_family_counts": _count(success_rows, "source_family"),
            "protected_window_frame_count": protected_windows.get("summary", {}).get("frame_count"),
            "selector_training_row_count": len(selector_training_rows),
            "runtime_authorization_row_count": len(runtime_authorization_rows),
            "stage7_training_row_count": len(stage7_training_rows),
            "forbidden_training_or_runtime_input_row_count": forbidden_input_row_count,
            "forbidden_input_flag_counts": forbidden_flag_counts,
        },
        "existing_failure_examples": [
            {
                "row_id": row.get("row_id"),
                "source_stage": row.get("source_stage"),
                "source_family": row.get("source_family"),
                "fen": row.get("fen"),
                "move_uci": row.get("move_uci"),
                "outcome": row.get("outcome"),
                "abort_terms": (row.get("features") or {}).get("abort_terms") or [],
            }
            for row in failure_rows
        ],
        "coverage_gaps": {
            "failure_abort_terms": _counter_from_features(failure_rows, "abort_terms"),
            "success_abort_terms": _counter_from_features(success_rows, "abort_terms"),
            "families_without_failure_contrast": [
                item["source_family"]
                for item in _family_targets(unique_rows)
                if item["current_unique_failure_count"] == 0
            ],
        },
        "collection_units": collection_units,
        "decision": {
            "status": status,
            "recommended_next_step": (
                "repair_sequence_policy_benchmark_inputs_before_failure_contrast_planning"
                if forbidden_input_row_count
                else
                "review_protected_plan_window_failure_contrast_plan_before_explicit_collection_approval"
                if failure_gap
                else "rerun_non_causal_sequence_policy_benchmark_review"
            ),
            "approval_required_before_label_execution": bool(failure_gap),
            "implementation_allowed_by_this_packet": False,
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
        "# KRK Protected Plan-Window Failure Contrast Plan v0",
        "",
        f"Status: `{decision['status']}`",
        "",
        "This is a non-causal collection plan only. It does not execute labels, change runtime behavior, train a selector, promote Stage 7, or train Stage 8.",
        "",
        "## Summary",
        "",
    ]
    for key, value in summary.items():
        lines.append(f"- {key}: `{value}`")
    lines.extend(["", "## Existing Failure Examples", ""])
    for row in payload["existing_failure_examples"]:
        lines.append(
            f"- `{row['row_id']}` stage=`{row['source_stage']}` family=`{row['source_family']}` move=`{row['move_uci']}` outcome=`{row['outcome']}` abort_terms=`{row['abort_terms']}`"
        )
    if not payload["existing_failure_examples"]:
        lines.append("- none")
    lines.extend(["", "## Collection Units", ""])
    for unit in payload["collection_units"]:
        lines.append(f"- `{unit['unit_id']}` purpose={unit['purpose']}")
    lines.extend(
        [
            "",
            "## Decision",
            "",
            f"- recommended_next_step: `{decision['recommended_next_step']}`",
            f"- approval_required_before_label_execution: `{decision['approval_required_before_label_execution']}`",
            "- implementation_allowed_by_this_packet: `false`",
            "- runtime_changes_allowed: `false`",
            "- label_run_allowed: `false`",
            "- selector_training_allowed: `false`",
            "- Stage 7 promotion and Stage 8 training remain blocked.",
        ]
    )
    return "\n".join(lines) + "\n"


def main() -> None:
    payload = build_payload()
    OUTPUT_JSON.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    OUTPUT_MD.write_text(write_markdown(payload), encoding="utf-8")
    print(f"wrote {OUTPUT_JSON.relative_to(ROOT)}")
    print(f"wrote {OUTPUT_MD.relative_to(ROOT)}")
    print(payload["decision"]["status"])


if __name__ == "__main__":
    main()
