#!/usr/bin/env python3
"""Assemble current non-causal KRK sequence-policy benchmark inputs.

This script normalizes the available Stage 4 contrast rows, protected Stage
4/5/6 plan-window frames, and clean held-out Stage 7 controls into a single
readiness artifact. It does not train a model, run labels, implement runtime
behavior, or authorize Stage 7/8 changes.
"""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
CONTRAST_DATASET = ROOT / "reports/strategy_arbitration/krk_sequence_control_contrast_dataset_v0.json"
PROTECTED_PLAN_WINDOWS = ROOT / "reports/strategy_arbitration/krk_protected_plan_window_frames_v0.json"
STAGE7_CLEAN_CONTROLS = ROOT / "reports/structural_candidates/stage7_clean_sequence_control_recovery_v0.json"
STAGE7_DIVERSE_INTEGRATION = ROOT / "reports/structural_candidates/stage7_diverse_clean_sampling_integration_v0.json"
PROTECTED_FAILURE_CONTRAST_INTEGRATION = (
    ROOT
    / "reports/strategy_arbitration/"
    "krk_protected_plan_window_failure_contrast_integration_v0.json"
)
SEQUENCE_POLICY_DESIGN = ROOT / "reports/strategy_arbitration/krk_sequence_policy_benchmark_design_v0.json"
SEQUENCE_POLICY_BENCHMARK_REVIEW = (
    ROOT / "reports/strategy_arbitration/krk_sequence_policy_benchmark_review_v0.json"
)
OUTPUT_JSON = ROOT / "reports/strategy_arbitration/krk_sequence_policy_benchmark_inputs_v0.json"
OUTPUT_MD = ROOT / "reports/strategy_arbitration/krk_sequence_policy_benchmark_inputs_v0.md"

SCHEMA_VERSION = "krk_sequence_policy_benchmark_inputs.v0"

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

PROTECTED_FAILURE_INTEGRATION_READY_STATUS = (
    "protected_plan_window_failure_contrast_integration_ready_for_passive_benchmark_refresh"
)


def _load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _load_optional(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return _load(path)


def _stage4_rows(contrast_dataset: dict[str, Any]) -> list[dict[str, Any]]:
    rows = []
    for row in contrast_dataset.get("rows") or []:
        if row.get("row_type") != "forced_first_move_candidate":
            continue
        rows.append(
            {
                "schema_version": "krk_sequence_policy_benchmark_input_row.v0",
                "row_id": f"seq_input.{row.get('row_id')}",
                "input_group": "stage4_first_move_contrast",
                "source_stage": row.get("source_stage"),
                "source_family": row.get("source_family"),
                "state_id": row.get("state_id"),
                "fen": row.get("fen"),
                "move_uci": row.get("move_uci"),
                "target_label": row.get("target_label"),
                "outcome": row.get("result"),
                "features": row.get("features") or {},
                "stage7_heldout_challenge": False,
                "usable_for_selector_training": False,
                "usable_for_runtime_authorization": False,
                "causal_status": "non_causal_sequence_policy_input",
            }
        )
    return rows


def _protected_plan_window_rows(protected_plan_windows: dict[str, Any]) -> list[dict[str, Any]]:
    rows = []
    for frame in protected_plan_windows.get("frames") or []:
        rows.append(
            {
                "schema_version": "krk_sequence_policy_benchmark_input_row.v0",
                "row_id": f"seq_input.{frame.get('frame_id')}",
                "input_group": "protected_plan_window",
                "source_stage": frame.get("source_stage"),
                "source_family": frame.get("source_family"),
                "state_id": frame.get("frame_id"),
                "fen": frame.get("fen"),
                "move_uci": frame.get("move_uci"),
                "target_label": frame.get("h40_outcome_label"),
                "outcome": frame.get("result"),
                "features": {
                    "entry_terms_confirmed": frame.get("entry_terms_confirmed") or [],
                    "progress_terms_after_first_reply": frame.get("progress_terms_after_first_reply") or [],
                    "abort_terms": frame.get("abort_terms") or [],
                    "handoff_targets": frame.get("handoff_targets") or [],
                    "selected_successor": frame.get("selected_successor"),
                    "selected_successor_contract_met": frame.get("selected_successor_contract_met"),
                    "semantic_alignment_status": frame.get("semantic_alignment_status"),
                },
                "stage7_heldout_challenge": False,
                "usable_for_selector_training": False,
                "usable_for_runtime_authorization": False,
                "causal_status": "non_causal_sequence_policy_input",
            }
        )
    return rows


def _protected_failure_contrast_rows(
    integration: dict[str, Any],
) -> tuple[list[dict[str, Any]], Counter[str]]:
    skipped: Counter[str] = Counter()
    if not integration.get("summary", {}).get("integration_ready"):
        skipped_count = len(integration.get("integrated_failure_contrasts") or [])
        if skipped_count:
            skipped["integration_not_ready"] += skipped_count
        return [], skipped
    if integration.get("decision", {}).get("status") != PROTECTED_FAILURE_INTEGRATION_READY_STATUS:
        skipped_count = len(integration.get("integrated_failure_contrasts") or [])
        if skipped_count:
            skipped["integration_status_not_ready"] += skipped_count
        return [], skipped
    rows = []
    for row in integration.get("integrated_failure_contrasts") or []:
        row_blockers = []
        if row.get("h40_outcome_label") != "conversion_failure":
            row_blockers.append("not_conversion_failure")
        if row.get("control_role") != "protected_plan_window_failure_contrast":
            row_blockers.append("unexpected_control_role")
        if row.get("stage7_training_row") is not False:
            row_blockers.append("stage7_training_row_must_be_false")
        if row.get("usable_for_selector_training") is not False:
            row_blockers.append("selector_training_must_be_false")
        if row.get("usable_for_runtime_authorization") is not False:
            row_blockers.append("runtime_authorization_must_be_false")
        if row.get("stage7_heldout_challenge") is not False:
            row_blockers.append("stage7_heldout_challenge_must_be_false")
        if row_blockers:
            skipped.update(row_blockers)
            continue
        rows.append(
            {
                "schema_version": "krk_sequence_policy_benchmark_input_row.v0",
                "row_id": f"seq_input.{row.get('row_id')}",
                "input_group": "protected_plan_window_failure_contrast",
                "source_stage": row.get("source_stage"),
                "source_family": row.get("source_family"),
                "state_id": row.get("seed_frame_id"),
                "fen": row.get("fen"),
                "move_uci": row.get("anchor_move_uci"),
                "target_label": "conversion_failure",
                "outcome": row.get("result"),
                "features": {
                    "control_role": row.get("control_role"),
                    "source_job_id": row.get("job_id"),
                    "source_track": "protected_failure_contrast_integration",
                    "validated_failure_contrast": True,
                },
                "stage7_heldout_challenge": False,
                "usable_for_selector_training": False,
                "usable_for_runtime_authorization": False,
                "causal_status": "non_causal_sequence_policy_input",
            }
        )
    return rows, skipped


def _stage7_clean_rows(
    stage7_clean_controls: dict[str, Any],
    *,
    controls_key: str = "controls",
    source_track: str = "replay_free_recovery",
) -> list[dict[str, Any]]:
    rows = []
    for control in stage7_clean_controls.get(controls_key) or []:
        rows.append(
            {
                "schema_version": "krk_sequence_policy_benchmark_input_row.v0",
                "row_id": f"seq_input.{control.get('state_id')}",
                "input_group": "stage7_clean_heldout_control",
                "source_stage": "stage7",
                "source_family": "stage7_heldout_post_box",
                "state_id": control.get("state_id"),
                "fen": control.get("fen"),
                "move_uci": control.get("move_uci"),
                "target_label": (
                    "conversion_positive"
                    if control.get("control_role") == "clean_sequence_success_control"
                    else "conversion_failure"
                ),
                "outcome": control.get("result"),
                "features": {
                    "control_role": control.get("control_role"),
                    "selected_provider": control.get("selected_provider"),
                    "selected_provider_move": control.get("selected_provider_move"),
                    "selected_provider_score": control.get("selected_provider_score"),
                    "selected_provider_second_score": control.get("selected_provider_second_score"),
                    "selected_skill_source": control.get("selected_skill_source"),
                    "semantic_alignment_status": control.get("semantic_alignment_status"),
                    "source_classification": control.get("source_classification"),
                    "source_track": source_track,
                    "source_job_id": control.get("source_job_id"),
                    "source_stage_names": control.get("source_stage_names") or [],
                },
                "stage7_heldout_challenge": True,
                "usable_for_selector_training": False,
                "usable_for_runtime_authorization": False,
                "causal_status": "non_causal_sequence_policy_input",
            }
        )
    return rows


def build_payload(
    *,
    contrast_dataset: dict[str, Any] | None = None,
    protected_plan_windows: dict[str, Any] | None = None,
    stage7_clean_controls: dict[str, Any] | None = None,
    stage7_diverse_integration: dict[str, Any] | None = None,
    protected_failure_contrast_integration: dict[str, Any] | None = None,
    sequence_policy_design: dict[str, Any] | None = None,
    sequence_policy_benchmark_review: dict[str, Any] | None = None,
) -> dict[str, Any]:
    loading_repo_defaults = all(
        item is None
        for item in (
            contrast_dataset,
            protected_plan_windows,
            stage7_clean_controls,
            stage7_diverse_integration,
            protected_failure_contrast_integration,
            sequence_policy_design,
        )
    )
    contrast_dataset = contrast_dataset or _load(CONTRAST_DATASET)
    protected_plan_windows = protected_plan_windows or _load(PROTECTED_PLAN_WINDOWS)
    stage7_clean_controls = stage7_clean_controls or _load(STAGE7_CLEAN_CONTROLS)
    stage7_diverse_integration = stage7_diverse_integration or _load_optional(STAGE7_DIVERSE_INTEGRATION)
    protected_failure_contrast_integration = (
        protected_failure_contrast_integration
        or _load_optional(PROTECTED_FAILURE_CONTRAST_INTEGRATION)
    )
    sequence_policy_design = sequence_policy_design or _load(SEQUENCE_POLICY_DESIGN)
    if sequence_policy_benchmark_review is None:
        sequence_policy_benchmark_review = (
            _load_optional(SEQUENCE_POLICY_BENCHMARK_REVIEW) if loading_repo_defaults else {}
        )

    stage7_rows = [
        *_stage7_clean_rows(stage7_clean_controls),
        *_stage7_clean_rows(
            stage7_diverse_integration,
            controls_key="new_controls",
            source_track="diverse_clean_sampling_integration",
        ),
    ]
    deduped_stage7_rows = []
    seen_stage7_keys: set[tuple[Any, Any, Any]] = set()
    for row in stage7_rows:
        key = (row.get("fen"), row.get("move_uci"), row.get("outcome"))
        if key in seen_stage7_keys:
            continue
        seen_stage7_keys.add(key)
        deduped_stage7_rows.append(row)

    protected_failure_rows, protected_failure_skipped = _protected_failure_contrast_rows(
        protected_failure_contrast_integration
    )
    rows = [
        *_stage4_rows(contrast_dataset),
        *_protected_plan_window_rows(protected_plan_windows),
        *protected_failure_rows,
        *deduped_stage7_rows,
    ]
    input_counts = Counter(row["input_group"] for row in rows)
    stage_counts = Counter(row["source_stage"] for row in rows)
    label_counts = Counter(row["target_label"] for row in rows)
    stage7_success = sum(
        1
        for row in rows
        if row["input_group"] == "stage7_clean_heldout_control"
        and row["target_label"] == "conversion_positive"
    )
    stage7_fail = sum(
        1
        for row in rows
        if row["input_group"] == "stage7_clean_heldout_control"
        and row["target_label"] == "conversion_failure"
    )
    stage7_success_required = int(
        sequence_policy_design.get("readiness", {}).get("stage7_clean_success_controls_required", 5)
    )
    stage7_failure_required = 5
    stage7_success_met = stage7_success >= stage7_success_required
    stage7_failure_met = stage7_fail >= stage7_failure_required
    protected_plan_window_met = bool(
        protected_plan_windows.get("summary", {}).get("protected_cross_stage_evidence_met")
    )
    benchmark_input_ready = protected_plan_window_met and stage7_success_met and stage7_failure_met
    benchmark_review_status = sequence_policy_benchmark_review.get("decision", {}).get("status")
    benchmark_review_next_step = sequence_policy_benchmark_review.get("decision", {}).get(
        "recommended_next_step"
    )
    benchmark_review_current = benchmark_review_status in {
        "sequence_policy_benchmark_supports_non_causal_sequence_policy_review",
        "sequence_policy_benchmark_mixed_plan_window_underpowered",
        "sequence_policy_benchmark_mixed_or_insufficient",
    }
    status = (
        "sequence_policy_benchmark_inputs_ready_non_causal"
        if benchmark_input_ready
        else "sequence_policy_benchmark_inputs_blocked_pending_stage7_success_controls"
        if not stage7_success_met
        else "sequence_policy_benchmark_inputs_blocked_pending_stage7_failure_controls"
        if not stage7_failure_met
        else "sequence_policy_benchmark_inputs_blocked_pending_protected_plan_windows"
    )

    return {
        "schema_version": SCHEMA_VERSION,
        "causal_status": "non_causal_sequence_policy_input_assembly",
        **COMMON_FALSE_FLAGS,
        "source_artifacts": [
            "reports/strategy_arbitration/krk_sequence_control_contrast_dataset_v0.json",
            "reports/strategy_arbitration/krk_protected_plan_window_frames_v0.json",
            "reports/structural_candidates/stage7_clean_sequence_control_recovery_v0.json",
            "reports/structural_candidates/stage7_diverse_clean_sampling_integration_v0.json",
            "reports/strategy_arbitration/krk_protected_plan_window_failure_contrast_integration_v0.json",
            "reports/strategy_arbitration/krk_sequence_policy_benchmark_design_v0.json",
            "reports/strategy_arbitration/krk_sequence_policy_benchmark_review_v0.json",
        ],
        "summary": {
            "row_count": len(rows),
            "input_group_counts": dict(input_counts),
            "source_stage_counts": dict(stage_counts),
            "target_label_counts": dict(label_counts),
            "protected_plan_window_evidence_met": protected_plan_window_met,
            "stage7_clean_success_controls": stage7_success,
            "stage7_clean_success_controls_required": stage7_success_required,
            "stage7_clean_success_controls_met": stage7_success_met,
            "stage7_clean_failure_controls": stage7_fail,
            "stage7_clean_failure_controls_required": stage7_failure_required,
            "stage7_clean_failure_controls_met": stage7_failure_met,
            "stage7_diverse_outputs_present": bool(
                stage7_diverse_integration.get("summary", {}).get("outputs_present_count", 0)
            ),
            "stage7_diverse_new_controls": int(
                stage7_diverse_integration.get("summary", {}).get("new_control_count", 0) or 0
            ),
            "protected_failure_contrast_integration_status": protected_failure_contrast_integration.get(
                "decision", {}
            ).get("status"),
            "protected_failure_contrast_integration_ready": bool(
                protected_failure_contrast_integration.get("summary", {}).get("integration_ready")
            ),
            "protected_failure_contrast_row_count": input_counts.get(
                "protected_plan_window_failure_contrast", 0
            ),
            "protected_failure_contrast_skipped_counts": dict(protected_failure_skipped),
            "current_benchmark_review_status": benchmark_review_status,
            "current_benchmark_review_next_step": benchmark_review_next_step,
            "current_benchmark_review_available": benchmark_review_current,
            "stage7_heldout_row_count": sum(1 for row in rows if row["stage7_heldout_challenge"]),
            "selector_training_row_count": sum(1 for row in rows if row["usable_for_selector_training"]),
            "runtime_authorization_row_count": sum(
                1 for row in rows if row["usable_for_runtime_authorization"]
            ),
            "benchmark_input_ready": benchmark_input_ready,
        },
        "label_semantics": {
            "stage4_forced_first_move_rows_are_capacity_contrast": True,
            "protected_plan_window_rows_are_replay_free_context": True,
            "stage7_rows_are_heldout_challenge_only": True,
            "capacity_labels_are_not_runtime_ownership_labels": True,
            "benchmark_inputs_do_not_authorize_runtime_or_training": True,
        },
        "rows": rows,
        "decision": {
            "status": status,
            "recommended_next_step": (
                "approve_stage7_diverse_clean_label_run_to_fill_success_controls"
                if not stage7_success_met
                else "approve_stage7_clean_failure_control_collection_or_repair_inputs"
                if not stage7_failure_met
                else benchmark_review_next_step
                if benchmark_input_ready and benchmark_review_current and benchmark_review_next_step
                else "implement_non_causal_sequence_policy_benchmark"
                if benchmark_input_ready
                else "repair_protected_plan_window_input_gap"
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
        "# KRK Sequence-Policy Benchmark Inputs v0",
        "",
        f"Status: `{decision['status']}`",
        "",
        "This artifact assembles currently available non-causal inputs for a future sequence-policy benchmark. It does not run labels, train a model, implement runtime behavior, promote Stage 7, or train Stage 8.",
        "",
        "## Summary",
        "",
    ]
    for key, value in summary.items():
        lines.append(f"- {key}: `{value}`")
    lines.extend(
        [
            "",
            "## Label Semantics",
            "",
        ]
    )
    for key, value in payload["label_semantics"].items():
        lines.append(f"- {key}: `{value}`")
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
    print(
        json.dumps(
            {
                "decision": payload["decision"]["status"],
                "row_count": payload["summary"]["row_count"],
                "stage7_success": payload["summary"]["stage7_clean_success_controls"],
                "stage7_success_required": payload["summary"][
                    "stage7_clean_success_controls_required"
                ],
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
