#!/usr/bin/env python3
"""Advance passive KRK-suite gates from the current artifact state.

This script is a safe continuation harness. It never runs Stage 7 labels,
implements runtime behavior, trains selectors, promotes Stage 7, or trains
Stage 8. It only reruns the passive integration/benchmark/readiness artifacts
that can become unblocked after separately approved outputs appear.
"""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
OUTPUT_JSON = ROOT / "reports/krk_suite_gate_advancement_v0.json"
OUTPUT_MD = ROOT / "reports/krk_suite_gate_advancement_v0.md"

SCHEMA_VERSION = "krk_suite_gate_advancement.v0"

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

FORBIDDEN_INPUT_BLOCKERS = {
    "selector_training_rows_forbidden",
    "runtime_authorization_rows_forbidden",
    "sequence_policy_forbidden_training_or_runtime_rows",
}

FORBIDDEN_INPUT_STATUSES = {
    "sequence_policy_benchmark_blocked_forbidden_training_or_runtime_rows",
    "sequence_policy_benchmark_review_blocked_forbidden_training_or_runtime_rows",
    "sequence_policy_pilot_blocked_forbidden_training_or_runtime_rows",
    "krk_suite_readiness_blocked_forbidden_training_or_runtime_rows",
    "krk_suite_unblocker_blocked_forbidden_training_or_runtime_rows",
}


def _approval_ready_with_status_fallback(
    *,
    explicit_value: Any,
    status: Any,
    ready_status: str,
    blockers: list[Any],
    summary_ready: Any = None,
) -> bool:
    if explicit_value is not None:
        return bool(explicit_value)
    return (
        status == ready_status
        and not blockers
        and summary_ready is not False
    )


PASSIVE_STEPS = [
    {
        "step_id": "stage7_diverse_clean_output_validation",
        "script": "scripts/validate_stage7_diverse_clean_sampling_outputs_v0.py",
        "output_json": "reports/structural_candidates/stage7_diverse_clean_sampling_output_validation_v0.json",
    },
    {
        "step_id": "stage4_first_move_contrast_sandbox_approval_request",
        "script": "scripts/write_krk_stage4_first_move_contrast_sandbox_approval_request_v0.py",
        "output_json": (
            "reports/krk_stage4_first_move_contrast_sandbox_approval_request_v0.json"
        ),
    },
    {
        "step_id": "stage4_caveat_unblocker_packet",
        "script": "scripts/write_krk_stage4_caveat_unblocker_packet_v0.py",
        "output_json": "reports/krk_stage4_caveat_unblocker_packet_v0.json",
    },
    {
        "step_id": "stage7_clean_artifact_manifest",
        "script": "scripts/build_stage7_clean_artifact_manifest.py",
        "output_json": "reports/structural_candidates/stage7_clean_artifact_manifest_v0.json",
    },
    {
        "step_id": "stage7_clean_sequence_control_recovery",
        "script": "scripts/recover_stage7_clean_sequence_controls.py",
        "output_json": "reports/structural_candidates/stage7_clean_sequence_control_recovery_v0.json",
    },
    {
        "step_id": "stage7_clean_success_backfill_audit",
        "script": "scripts/audit_stage7_clean_success_control_backfill_v0.py",
        "output_json": "reports/structural_candidates/stage7_clean_success_backfill_audit_v0.json",
    },
    {
        "step_id": "sequence_policy_pipeline_refresh",
        "script": "scripts/refresh_krk_sequence_policy_pipeline_v0.py",
        "output_json": "reports/strategy_arbitration/krk_sequence_policy_pipeline_refresh_v0.json",
    },
    {
        "step_id": "sequence_policy_benchmark_review",
        "script": "scripts/review_krk_sequence_policy_benchmark_v0.py",
        "output_json": "reports/strategy_arbitration/krk_sequence_policy_benchmark_review_v0.json",
    },
    {
        "step_id": "sequence_policy_benchmark_design",
        "script": "scripts/write_krk_sequence_policy_benchmark_design_v0.py",
        "output_json": "reports/strategy_arbitration/krk_sequence_policy_benchmark_design_v0.json",
    },
    {
        "step_id": "cross_stage_plan_capsule_requirements",
        "script": "scripts/write_krk_cross_stage_plan_capsule_evidence_requirements_v0.py",
        "output_json": (
            "reports/strategy_arbitration/"
            "krk_cross_stage_plan_capsule_evidence_requirements_v0.json"
        ),
    },
    {
        "step_id": "protected_plan_window_failure_contrast_plan",
        "script": "scripts/write_krk_protected_plan_window_failure_contrast_plan_v0.py",
        "output_json": (
            "reports/strategy_arbitration/"
            "krk_protected_plan_window_failure_contrast_plan_v0.json"
        ),
    },
    {
        "step_id": "protected_plan_window_failure_contrast_manifest",
        "script": "scripts/write_krk_protected_plan_window_failure_contrast_manifest_v0.py",
        "output_json": (
            "reports/strategy_arbitration/"
            "krk_protected_plan_window_failure_contrast_manifest_v0.json"
        ),
    },
    {
        "step_id": "protected_plan_window_failure_contrast_manifest_review",
        "script": "scripts/review_krk_protected_plan_window_failure_contrast_manifest_v0.py",
        "output_json": (
            "reports/strategy_arbitration/"
            "krk_protected_plan_window_failure_contrast_manifest_review_v0.json"
        ),
    },
    {
        "step_id": "protected_plan_window_failure_contrast_execution_readiness",
        "script": (
            "scripts/validate_krk_protected_plan_window_failure_contrast_execution_readiness_v0.py"
        ),
        "output_json": (
            "reports/strategy_arbitration/"
            "krk_protected_plan_window_failure_contrast_execution_readiness_v0.json"
        ),
    },
    {
        "step_id": "protected_plan_window_failure_contrast_runner",
        "script": "scripts/run_krk_protected_plan_window_failure_contrast_collection_v0.py",
        "args": ["--refresh-after-run"],
        "output_json": (
            "reports/strategy_arbitration/"
            "krk_protected_plan_window_failure_contrast_runner_v0.json"
        ),
    },
    {
        "step_id": "protected_plan_window_failure_contrast_approval_request",
        "script": (
            "scripts/write_krk_protected_plan_window_failure_contrast_approval_request_v0.py"
        ),
        "output_json": (
            "reports/strategy_arbitration/"
            "krk_protected_plan_window_failure_contrast_approval_request_v0.json"
        ),
    },
    {
        "step_id": "protected_plan_window_failure_contrast_output_validation",
        "script": "scripts/validate_krk_protected_plan_window_failure_contrast_outputs_v0.py",
        "output_json": (
            "reports/strategy_arbitration/"
            "krk_protected_plan_window_failure_contrast_output_validation_v0.json"
        ),
    },
    {
        "step_id": "protected_plan_window_failure_contrast_integration",
        "script": "scripts/integrate_krk_protected_plan_window_failure_contrasts_v0.py",
        "output_json": (
            "reports/strategy_arbitration/"
            "krk_protected_plan_window_failure_contrast_integration_v0.json"
        ),
    },
    {
        "step_id": "sequence_policy_after_protected_failure_contrast_refresh",
        "script": "scripts/refresh_krk_sequence_policy_after_protected_failure_contrasts_v0.py",
        "output_json": (
            "reports/strategy_arbitration/"
            "krk_sequence_policy_after_protected_failure_contrast_refresh_v0.json"
        ),
    },
    {
        "step_id": "full_suite_readiness_audit",
        "script": "scripts/write_krk_full_suite_readiness_audit_v0.py",
        "output_json": "reports/krk_full_suite_readiness_audit_v0.json",
    },
    {
        "step_id": "sequence_policy_underpowered_pilot_review",
        "script": "scripts/review_krk_sequence_policy_underpowered_pilot_v0.py",
        "output_json": "reports/strategy_arbitration/krk_sequence_policy_underpowered_pilot_v0.json",
    },
    {
        "step_id": "stage8_training_readiness_review",
        "script": "scripts/review_krk_stage8_training_readiness_v0.py",
        "output_json": "reports/krk_stage8_training_readiness_review_v0.json",
    },
    {
        "step_id": "stage7_post_label_outcome_review",
        "script": "scripts/review_krk_stage7_post_label_outcome_v0.py",
        "output_json": "reports/krk_stage7_post_label_outcome_review_v0.json",
    },
    {
        "step_id": "stage7_label_distribution_review",
        "script": "scripts/review_stage7_diverse_clean_label_distribution_v0.py",
        "output_json": (
            "reports/structural_candidates/"
            "stage7_diverse_clean_label_distribution_review_v0.json"
        ),
    },
    {
        "step_id": "stage7_additional_clean_sampling_manifest",
        "script": "scripts/write_stage7_additional_clean_sampling_manifest_v0.py",
        "output_json": (
            "reports/structural_candidates/stage7_additional_clean_sampling_manifest_v0.json"
        ),
    },
    {
        "step_id": "stage7_additional_clean_output_validation",
        "script": "scripts/validate_stage7_additional_clean_sampling_outputs_v0.py",
        "output_json": (
            "reports/structural_candidates/"
            "stage7_additional_clean_sampling_output_validation_v0.json"
        ),
    },
    {
        "step_id": "stage7_additional_clean_sampling_runner",
        "script": "scripts/run_stage7_additional_clean_sampling_jobs_v0.py",
        "output_json": (
            "reports/structural_candidates/stage7_additional_clean_sampling_runner_v0.json"
        ),
    },
    {
        "step_id": "current_control_plane_gate",
        "script": "scripts/write_krk_current_control_plane_gate_v0.py",
        "output_json": "reports/krk_current_control_plane_gate_v0.json",
    },
    {
        "step_id": "full_suite_unblocker_packet",
        "script": "scripts/write_krk_full_suite_unblocker_packet_v0.py",
        "output_json": "reports/krk_full_suite_unblocker_packet_v0.json",
    },
]


def _load_module(path: Path):
    spec = importlib.util.spec_from_file_location(path.stem, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load script module: {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _load_json(relative: str) -> dict[str, Any]:
    data = json.loads((ROOT / relative).read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise TypeError(f"{relative} must contain a JSON object")
    return data


def _run_script(script: str, args: list[str] | None = None) -> dict[str, Any]:
    module = _load_module(ROOT / script)
    if not hasattr(module, "main"):
        raise RuntimeError(f"script has no main(): {script}")
    original_argv = sys.argv
    try:
        # Passive refresh imports scripts in-process; never let caller CLI flags
        # such as --execute-reviewed-label-run leak into imported script parsers.
        sys.argv = [script, *(args or [])]
        module.main()
    finally:
        sys.argv = original_argv
    return {"script": script, "args": list(args or []), "ran": True}


def build_payload() -> dict[str, Any]:
    step_results: list[dict[str, Any]] = []
    for step in PASSIVE_STEPS:
        _run_script(step["script"], step.get("args") or [])
        output = _load_json(step["output_json"])
        step_results.append(
            {
                "step_id": step["step_id"],
                "script": step["script"],
                "script_args": list(step.get("args") or []),
                "output_json": step["output_json"],
                "decision_status": (output.get("decision") or {}).get("status"),
                "artifact_runtime_behavior_changed": bool(
                    output.get("runtime_behavior_changed", False)
                ),
                "artifact_runtime_defaults_changed": bool(
                    output.get("runtime_defaults_changed", False)
                ),
                "artifact_runtime_selector_implemented": bool(
                    output.get("runtime_selector_implemented", False)
                ),
                "artifact_runtime_score_changes": bool(
                    output.get("runtime_score_changes", False)
                ),
                "artifact_runtime_direct_routing": bool(
                    output.get("runtime_direct_routing", False)
                ),
                "artifact_runtime_dtm_or_tablebase_lookup": bool(
                    output.get("runtime_dtm_or_tablebase_lookup", False)
                ),
                "artifact_hidden_python_controller": bool(
                    output.get("hidden_python_controller", False)
                ),
                "artifact_gameplay_topology_mutation": bool(
                    output.get("gameplay_topology_mutation", False)
                ),
                "artifact_stage7_promotion_allowed": bool(
                    output.get("stage7_promotion_allowed", False)
                ),
                "artifact_stage8_training_allowed": bool(
                    output.get("stage8_training_allowed", False)
                ),
                "runtime_changes_allowed": bool(
                    (output.get("decision") or {}).get("runtime_changes_allowed", False)
                ),
                "label_run_allowed": bool(
                    (output.get("decision") or {}).get("label_run_allowed", False)
                ),
                "selector_training_allowed": bool(
                    (output.get("decision") or {}).get("selector_training_allowed", False)
                ),
                "stage7_promotion_allowed": bool(
                    (output.get("decision") or {}).get("stage7_promotion_allowed", False)
                ),
                "stage8_training_allowed": bool(
                    (output.get("decision") or {}).get("stage8_training_allowed", False)
                ),
            }
        )

    readiness = _load_json("reports/krk_full_suite_readiness_audit_v0.json")
    unblocker = _load_json("reports/krk_full_suite_unblocker_packet_v0.json")
    stage4_approval_request = _load_json(
        "reports/krk_stage4_first_move_contrast_sandbox_approval_request_v0.json"
    )
    stage4_unblocker = _load_json("reports/krk_stage4_caveat_unblocker_packet_v0.json")
    stage4_current = stage4_unblocker.get("current_stage4_status") or {}
    stage4_approval_scope = (
        stage4_unblocker.get("required_approval_scope_if_user_approves") or {}
    )
    output_validation = _load_json(
        "reports/structural_candidates/stage7_diverse_clean_sampling_output_validation_v0.json"
    )
    backfill_audit = _load_json(
        "reports/structural_candidates/stage7_clean_success_backfill_audit_v0.json"
    )
    pipeline = _load_json("reports/strategy_arbitration/krk_sequence_policy_pipeline_refresh_v0.json")
    benchmark = _load_json("reports/strategy_arbitration/krk_sequence_policy_benchmark_v0.json")
    benchmark_review = _load_json(
        "reports/strategy_arbitration/krk_sequence_policy_benchmark_review_v0.json"
    )
    benchmark_design = _load_json(
        "reports/strategy_arbitration/krk_sequence_policy_benchmark_design_v0.json"
    )
    cross_stage_requirements = _load_json(
        "reports/strategy_arbitration/krk_cross_stage_plan_capsule_evidence_requirements_v0.json"
    )
    failure_contrast_plan = _load_json(
        "reports/strategy_arbitration/krk_protected_plan_window_failure_contrast_plan_v0.json"
    )
    failure_contrast_manifest = _load_json(
        "reports/strategy_arbitration/krk_protected_plan_window_failure_contrast_manifest_v0.json"
    )
    failure_contrast_manifest_review = _load_json(
        "reports/strategy_arbitration/krk_protected_plan_window_failure_contrast_manifest_review_v0.json"
    )
    failure_contrast_execution_readiness = _load_json(
        "reports/strategy_arbitration/"
        "krk_protected_plan_window_failure_contrast_execution_readiness_v0.json"
    )
    failure_contrast_runner = _load_json(
        "reports/strategy_arbitration/krk_protected_plan_window_failure_contrast_runner_v0.json"
    )
    failure_contrast_approval_request = _load_json(
        "reports/strategy_arbitration/"
        "krk_protected_plan_window_failure_contrast_approval_request_v0.json"
    )
    failure_contrast_approval_request_summary = (
        failure_contrast_approval_request.get("summary") or {}
    )
    protected_failure_contrast_gate = readiness.get("protected_failure_contrast_gate") or {}
    stage4_approval_request_ready = _approval_ready_with_status_fallback(
        explicit_value=stage4_current.get(
            "approval_request_ready_for_runtime_approval"
        ),
        status=stage4_approval_request.get("decision", {}).get("status"),
        ready_status="stage4_first_move_contrast_sandbox_approval_request_ready",
        blockers=stage4_approval_request.get("blockers") or [],
    )
    failure_contrast_approval_request_ready = _approval_ready_with_status_fallback(
        explicit_value=protected_failure_contrast_gate.get(
            "approval_request_ready_for_collection"
        ),
        status=failure_contrast_approval_request.get("decision", {}).get("status"),
        ready_status="protected_plan_window_failure_contrast_approval_request_ready",
        blockers=failure_contrast_approval_request.get("blockers") or [],
        summary_ready=failure_contrast_approval_request_summary.get("request_ready"),
    )
    failure_contrast_output_validation = _load_json(
        "reports/strategy_arbitration/"
        "krk_protected_plan_window_failure_contrast_output_validation_v0.json"
    )
    failure_contrast_integration = _load_json(
        "reports/strategy_arbitration/"
        "krk_protected_plan_window_failure_contrast_integration_v0.json"
    )
    post_failure_refresh = _load_json(
        "reports/strategy_arbitration/"
        "krk_sequence_policy_after_protected_failure_contrast_refresh_v0.json"
    )
    underpowered_pilot = _load_json(
        "reports/strategy_arbitration/krk_sequence_policy_underpowered_pilot_v0.json"
    )
    stage8_review = _load_json("reports/krk_stage8_training_readiness_review_v0.json")
    post_label_review = _load_json("reports/krk_stage7_post_label_outcome_review_v0.json")
    label_distribution_review = _load_json(
        "reports/structural_candidates/stage7_diverse_clean_label_distribution_review_v0.json"
    )
    additional_manifest = _load_json(
        "reports/structural_candidates/stage7_additional_clean_sampling_manifest_v0.json"
    )
    additional_runner = _load_json(
        "reports/structural_candidates/stage7_additional_clean_sampling_runner_v0.json"
    )

    all_boundaries_preserved = all(
        not result["runtime_changes_allowed"]
        and not result["label_run_allowed"]
        and not result["selector_training_allowed"]
        and not result["stage7_promotion_allowed"]
        and not result["stage8_training_allowed"]
        and not result["artifact_runtime_behavior_changed"]
        and not result["artifact_runtime_defaults_changed"]
        and not result["artifact_runtime_selector_implemented"]
        and not result["artifact_runtime_score_changes"]
        and not result["artifact_runtime_direct_routing"]
        and not result["artifact_runtime_dtm_or_tablebase_lookup"]
        and not result["artifact_gameplay_topology_mutation"]
        and not result["artifact_stage7_promotion_allowed"]
        and not result["artifact_stage8_training_allowed"]
        for result in step_results
    )
    benchmark_ready = bool(benchmark.get("decision", {}).get("benchmark_executed_as_ready"))
    stage7_ready = bool(
        readiness.get("stage7_sampling_gate", {}).get("success_controls_ready")
    )
    stage7_outputs_valid = int(
        output_validation.get("summary", {}).get("output_valid_count") or 0
    ) > 0
    protected_stack = readiness.get("protected_stack") or {}
    readiness_boundaries = readiness.get("runtime_and_training_boundaries") or {}
    sequence_forbidden_blockers = sorted(
        FORBIDDEN_INPUT_BLOCKERS
        & (
            set(benchmark.get("preflight", {}).get("blockers") or [])
            | set(benchmark_review.get("blockers") or [])
            | set(underpowered_pilot.get("blockers") or [])
            | set(readiness.get("hard_blockers") or [])
        )
    )
    sequence_forbidden_training_or_runtime_inputs = (
        bool(sequence_forbidden_blockers)
        or benchmark.get("decision", {}).get("status") in FORBIDDEN_INPUT_STATUSES
        or benchmark_review.get("decision", {}).get("status") in FORBIDDEN_INPUT_STATUSES
        or underpowered_pilot.get("decision", {}).get("status") in FORBIDDEN_INPUT_STATUSES
        or readiness.get("decision", {}).get("status") in FORBIDDEN_INPUT_STATUSES
        or unblocker.get("decision", {}).get("status") in FORBIDDEN_INPUT_STATUSES
        or bool(
            underpowered_pilot.get("summary", {}).get(
                "forbidden_training_or_runtime_input_blocked"
            )
        )
        or bool(
            readiness.get("sequence_policy", {}).get(
                "forbidden_training_or_runtime_input_blocked"
            )
        )
        or bool(
            unblocker.get("current_state", {}).get(
                "sequence_policy_forbidden_training_or_runtime_input_blocked"
            )
        )
    )

    if sequence_forbidden_training_or_runtime_inputs:
        status = "krk_suite_passive_advancement_blocked_forbidden_training_or_runtime_rows"
        next_step = "repair_sequence_policy_inputs_remove_training_or_runtime_rows"
    elif benchmark_ready:
        status = (
            "krk_suite_passive_advancement_ready_for_protected_failure_contrast_collection"
        )
        next_step = (
            failure_contrast_integration.get("decision", {}).get("recommended_next_step")
            if failure_contrast_integration.get("summary", {}).get("integration_ready")
            else None
        ) or (
            failure_contrast_manifest_review.get("decision", {}).get("recommended_next_step")
            or failure_contrast_plan.get("decision", {}).get("recommended_next_step")
            if benchmark_review.get("decision", {}).get("status")
            == "sequence_policy_benchmark_mixed_plan_window_underpowered"
            else "review_non_causal_sequence_policy_benchmark_results"
        )
    elif (
        not stage7_ready
        and stage7_outputs_valid
        and additional_runner.get("decision", {}).get("status")
        == "stage7_additional_clean_sampling_runner_dry_run_ready"
    ):
        status = "krk_suite_passive_advancement_blocked_pending_explicit_additional_stage7_label_approval"
        next_step = "explicitly_approve_stage7_additional_clean_label_execution"
    elif not stage7_ready and stage7_outputs_valid:
        status = "krk_suite_passive_advancement_blocked_pending_additional_stage7_sampling_plan"
        next_step = (
            label_distribution_review.get("decision", {}).get("recommended_next_step")
            or post_label_review.get("decision", {}).get("recommended_next_step")
            or "write_additional_stage7_clean_sampling_manifest_for_remaining_success_gap"
        )
    elif not stage7_ready:
        status = "krk_suite_passive_advancement_blocked_pending_stage7_label_outputs"
        next_step = "explicitly_approve_stage7_diverse_clean_label_execution"
    else:
        status = "krk_suite_passive_advancement_blocked_pending_manual_review"
        next_step = "inspect_sequence_policy_pipeline_refresh"

    return {
        "schema_version": SCHEMA_VERSION,
        "causal_status": "non_causal_passive_gate_advancement",
        **COMMON_FALSE_FLAGS,
        "source_scripts": [step["script"] for step in PASSIVE_STEPS],
        "step_results": step_results,
        "summary": {
            "all_boundaries_preserved": all_boundaries_preserved,
            "protected_stack_status": protected_stack.get("status"),
            "protected_stack_ready": protected_stack.get("ready"),
            "protected_stack_rollback_paths_preserved": protected_stack.get(
                "rollback_paths_preserved"
            ),
            "protected_stack_active_paths_safe": (
                protected_stack.get("active_stack_path_status") or {}
            ).get("all_paths_safe"),
            "protected_stack_active_paths_exist": (
                protected_stack.get("active_stack_path_status") or {}
            ).get("all_paths_exist"),
            "protected_stack_rollback_paths_safe": (
                protected_stack.get("rollback_stack_path_status") or {}
            ).get("all_paths_safe"),
            "protected_stack_rollback_paths_exist": (
                protected_stack.get("rollback_stack_path_status") or {}
            ).get("all_paths_exist"),
            "protected_stack_rollback_common_paths_distinct": protected_stack.get(
                "rollback_common_paths_distinct"
            ),
            "protected_stack_filesystem_snapshots_replaced": protected_stack.get(
                "filesystem_snapshots_replaced"
            ),
            "stage7_output_validation_status": output_validation.get("decision", {}).get(
                "status"
            ),
            "stage7_output_valid_count": output_validation.get("summary", {}).get(
                "output_valid_count"
            ),
            "stage7_clean_success_backfill_status": backfill_audit.get("decision", {}).get(
                "status"
            ),
            "stage7_clean_success_backfill_available": backfill_audit.get(
                "summary", {}
            ).get("can_close_success_gate_replay_free"),
            "stage7_clean_success_backfill_eligible_new_success": backfill_audit.get(
                "summary", {}
            ).get("eligible_new_success_controls"),
            "stage4_caveat_unblocker_status": stage4_unblocker.get("decision", {}).get(
                "status"
            ),
            "stage4_first_move_contrast_sandbox_approval_request_status": stage4_approval_request.get(
                "decision", {}
            ).get("status"),
            "stage4_first_move_contrast_sandbox_approval_request_blockers": (
                stage4_approval_request.get("blockers") or []
            ),
            "stage4_first_move_contrast_sandbox_approval_request_ready_for_runtime_approval": (
                stage4_approval_request_ready
            ),
            "stage4_first_move_contrast_sandbox_approval_request_created": stage4_approval_request.get(
                "approval_request_created"
            ),
            "stage4_first_move_contrast_sandbox_implementation_authorized_by_request": stage4_approval_request.get(
                "implementation_authorized_by_request"
            ),
            "stage4_first_move_contrast_sandbox_scope_id": stage4_approval_scope.get(
                "sandbox_scope_id"
            ),
            "stage4_first_move_contrast_sandbox_default_off": stage4_approval_scope.get(
                "default_off"
            ),
            "stage4_first_move_contrast_sandbox_default_enabled": stage4_approval_scope.get(
                "default_enabled"
            ),
            "stage4_first_move_contrast_sandbox_runtime_change_class": stage4_approval_scope.get(
                "runtime_change_class"
            ),
            "stage4_first_move_contrast_sandbox_runtime_dtm_or_tablebase_lookup": stage4_approval_scope.get(
                "runtime_dtm_or_tablebase_lookup"
            ),
            "stage4_first_move_contrast_sandbox_hidden_python_controller": stage4_approval_scope.get(
                "hidden_python_controller"
            ),
            "stage4_first_move_contrast_sandbox_selector_training_allowed": stage4_approval_scope.get(
                "selector_training_allowed"
            ),
            "stage4_first_move_contrast_sandbox_stage7_promotion_allowed": stage4_approval_scope.get(
                "stage7_promotion_allowed"
            ),
            "stage4_first_move_contrast_sandbox_stage8_training_allowed": stage4_approval_scope.get(
                "stage8_training_allowed"
            ),
            "stage4_first_move_contrast_sandbox_readiness_checked_flag_count": stage4_approval_scope.get(
                "readiness_checked_flag_count"
            ),
            "stage4_first_move_contrast_sandbox_readiness_boundary_violation_count": stage4_approval_scope.get(
                "readiness_boundary_violation_count"
            ),
            "stage4_first_move_contrast_sandbox_readiness_source_artifact_count": stage4_approval_scope.get(
                "readiness_source_artifact_count"
            ),
            "stage7_success_controls": readiness.get("stage7_sampling_gate", {}).get(
                "combined_success_controls"
            ),
            "stage7_success_controls_required": readiness.get("stage7_sampling_gate", {}).get(
                "success_controls_required"
            ),
            "stage7_success_controls_ready": stage7_ready,
            "sequence_policy_inputs_ready": pipeline.get("summary", {}).get(
                "sequence_policy_inputs_ready"
            ),
            "sequence_policy_benchmark_ready": benchmark_ready,
            "sequence_policy_benchmark_review_status": benchmark_review.get("decision", {}).get(
                "status"
            ),
            "sequence_policy_benchmark_design_status": benchmark_design.get(
                "decision", {}
            ).get("status"),
            "sequence_policy_passive_design_without_new_labels_status": (
                benchmark_design.get("passive_design_without_new_labels") or {}
            ).get("status"),
            "cross_stage_plan_capsule_requirements_status": (
                cross_stage_requirements.get("decision", {}).get("status")
            ),
            "sequence_policy_forbidden_training_or_runtime_input_blocked": (
                sequence_forbidden_training_or_runtime_inputs
            ),
            "sequence_policy_forbidden_training_or_runtime_input_blockers": (
                sequence_forbidden_blockers
            ),
            "protected_plan_window_failure_contrast_plan_status": failure_contrast_plan.get(
                "decision", {}
            ).get("status"),
            "protected_plan_window_unique_failure_count": failure_contrast_plan.get(
                "summary", {}
            ).get("unique_failure_count"),
            "protected_plan_window_minimum_new_failures_needed": failure_contrast_plan.get(
                "summary", {}
            ).get("minimum_new_unique_failures_needed"),
            "protected_plan_window_failure_contrast_manifest_status": failure_contrast_manifest.get(
                "decision", {}
            ).get("status"),
            "protected_plan_window_failure_contrast_manifest_job_count": failure_contrast_manifest.get(
                "summary", {}
            ).get("job_count"),
            "protected_plan_window_failure_contrast_manifest_review_status": failure_contrast_manifest_review.get(
                "decision", {}
            ).get("status"),
            "protected_plan_window_failure_contrast_execution_readiness_status": failure_contrast_execution_readiness.get(
                "decision", {}
            ).get("status"),
            "protected_plan_window_failure_contrast_execution_jobs_passing": failure_contrast_execution_readiness.get(
                "summary", {}
            ).get("jobs_passing_readiness"),
            "protected_plan_window_failure_contrast_runner_status": failure_contrast_runner.get(
                "decision", {}
            ).get("status"),
            "protected_plan_window_failure_contrast_runner_processed_job_count": failure_contrast_runner.get(
                "summary", {}
            ).get("processed_job_count"),
            "protected_plan_window_failure_contrast_runner_executed_job_count": failure_contrast_runner.get(
                "summary", {}
            ).get("executed_job_count"),
            "protected_plan_window_failure_contrast_runner_refresh_after_run_requested": failure_contrast_runner.get(
                "summary", {}
            ).get("refresh_after_run_requested"),
            "protected_plan_window_failure_contrast_approval_request_status": failure_contrast_approval_request.get(
                "decision", {}
            ).get("status"),
            "protected_plan_window_failure_contrast_approval_request_blockers": (
                failure_contrast_approval_request.get("blockers") or []
            ),
            "protected_plan_window_failure_contrast_approval_request_ready_for_collection": (
                failure_contrast_approval_request_ready
            ),
            "protected_plan_window_failure_contrast_approval_receipt_created": failure_contrast_approval_request.get(
                "approval_receipt_created"
            ),
            "protected_plan_window_failure_contrast_approval_receipt_blockers": failure_contrast_approval_request.get(
                "approval_receipt_blockers"
            ),
            "protected_plan_window_failure_contrast_post_success_refresh_required": (
                failure_contrast_approval_request_summary.get(
                    "post_success_refresh_required"
                )
            ),
            "protected_plan_window_failure_contrast_post_success_refresh_script": (
                failure_contrast_approval_request_summary.get(
                    "post_success_refresh_script"
                )
            ),
            "protected_plan_window_failure_contrast_post_success_refresh_scope": (
                failure_contrast_approval_request_summary.get(
                    "post_success_refresh_scope"
                )
            ),
            "protected_plan_window_failure_contrast_runtime_direct_routing": readiness.get(
                "protected_failure_contrast_gate", {}
            ).get("runtime_direct_routing"),
            "protected_plan_window_failure_contrast_hidden_python_controller": readiness.get(
                "protected_failure_contrast_gate", {}
            ).get("hidden_python_controller"),
            "protected_plan_window_failure_contrast_output_validation_status": failure_contrast_output_validation.get(
                "decision", {}
            ).get("status"),
            "protected_plan_window_failure_contrast_output_exists_count": failure_contrast_output_validation.get(
                "summary", {}
            ).get("output_exists_count"),
            "protected_plan_window_failure_contrast_output_valid_count": failure_contrast_output_validation.get(
                "summary", {}
            ).get("output_valid_count"),
            "protected_plan_window_failure_contrast_integration_status": failure_contrast_integration.get(
                "decision", {}
            ).get("status"),
            "protected_plan_window_failure_contrast_integrated_new_failure_count": failure_contrast_integration.get(
                "summary", {}
            ).get("integrated_new_failure_count"),
            "protected_plan_window_failure_contrast_integration_ready": failure_contrast_integration.get(
                "summary", {}
            ).get("integration_ready"),
            "sequence_policy_after_protected_failure_contrast_refresh_status": post_failure_refresh.get(
                "decision", {}
            ).get("status"),
            "sequence_policy_after_protected_failure_contrast_rows": post_failure_refresh.get(
                "summary", {}
            ).get("protected_failure_contrast_row_count"),
            "sequence_policy_after_protected_failure_contrast_boundaries_preserved": post_failure_refresh.get(
                "summary", {}
            ).get("all_boundaries_preserved"),
            "sequence_policy_after_protected_failure_contrast_boundary_violation_count": post_failure_refresh.get(
                "summary", {}
            ).get("boundary_violation_count"),
            "sequence_policy_after_protected_failure_contrast_stage7_training_row_count": post_failure_refresh.get(
                "summary", {}
            ).get("stage7_training_row_count"),
            "sequence_policy_after_protected_failure_contrast_selector_training_row_count": post_failure_refresh.get(
                "summary", {}
            ).get("selector_training_row_count"),
            "sequence_policy_after_protected_failure_contrast_runtime_authorization_row_count": post_failure_refresh.get(
                "summary", {}
            ).get("runtime_authorization_row_count"),
            "sequence_policy_underpowered_pilot_status": underpowered_pilot.get(
                "decision", {}
            ).get("status"),
            "sequence_policy_underpowered_pilot_next_step": underpowered_pilot.get(
                "decision", {}
            ).get("recommended_next_step"),
            "sequence_policy_underpowered_pilot_stage4_topk_signal": underpowered_pilot.get(
                "summary", {}
            ).get("stage4_topk_signal"),
            "sequence_policy_underpowered_pilot_stage7_success_gap": underpowered_pilot.get(
                "summary", {}
            ).get("stage7_success_gap"),
            "sequence_policy_underpowered_pilot_readiness_checked_flag_count": underpowered_pilot.get(
                "summary", {}
            ).get("readiness_checked_flag_count"),
            "sequence_policy_underpowered_pilot_readiness_boundary_violation_count": underpowered_pilot.get(
                "summary", {}
            ).get("readiness_boundary_violation_count"),
            "sequence_policy_underpowered_pilot_readiness_source_artifact_count": underpowered_pilot.get(
                "summary", {}
            ).get("readiness_source_artifact_count"),
            "sequence_policy_underpowered_pilot_protected_failure_contrast_runner_processed_job_count": underpowered_pilot.get(
                "summary", {}
            ).get("protected_failure_contrast_runner_processed_job_count"),
            "sequence_policy_underpowered_pilot_protected_failure_contrast_runner_executed_job_count": underpowered_pilot.get(
                "summary", {}
            ).get("protected_failure_contrast_runner_executed_job_count"),
            "sequence_policy_underpowered_pilot_protected_failure_contrast_post_success_refresh_required": underpowered_pilot.get(
                "summary", {}
            ).get("protected_failure_contrast_post_success_refresh_required"),
            "sequence_policy_underpowered_pilot_protected_failure_contrast_post_success_refresh_script": underpowered_pilot.get(
                "summary", {}
            ).get("protected_failure_contrast_post_success_refresh_script"),
            "sequence_policy_underpowered_pilot_protected_failure_contrast_runtime_behavior_changed": underpowered_pilot.get(
                "summary", {}
            ).get("protected_failure_contrast_runtime_behavior_changed"),
            "sequence_policy_underpowered_pilot_protected_failure_contrast_runtime_defaults_changed": underpowered_pilot.get(
                "summary", {}
            ).get("protected_failure_contrast_runtime_defaults_changed"),
            "sequence_policy_underpowered_pilot_protected_failure_contrast_runtime_selector_implemented": underpowered_pilot.get(
                "summary", {}
            ).get("protected_failure_contrast_runtime_selector_implemented"),
            "sequence_policy_underpowered_pilot_protected_failure_contrast_runtime_score_changes": underpowered_pilot.get(
                "summary", {}
            ).get("protected_failure_contrast_runtime_score_changes"),
            "sequence_policy_underpowered_pilot_protected_failure_contrast_runtime_direct_routing": underpowered_pilot.get(
                "summary", {}
            ).get("protected_failure_contrast_runtime_direct_routing"),
            "sequence_policy_underpowered_pilot_protected_failure_contrast_runtime_dtm_or_tablebase_lookup": underpowered_pilot.get(
                "summary", {}
            ).get("protected_failure_contrast_runtime_dtm_or_tablebase_lookup"),
            "sequence_policy_underpowered_pilot_protected_failure_contrast_hidden_python_controller": underpowered_pilot.get(
                "summary", {}
            ).get("protected_failure_contrast_hidden_python_controller"),
            "sequence_policy_underpowered_pilot_protected_failure_contrast_gameplay_topology_mutation": underpowered_pilot.get(
                "summary", {}
            ).get("protected_failure_contrast_gameplay_topology_mutation"),
            "sequence_policy_underpowered_pilot_protected_failure_contrast_selector_training_allowed": underpowered_pilot.get(
                "summary", {}
            ).get("protected_failure_contrast_selector_training_allowed"),
            "sequence_policy_underpowered_pilot_protected_failure_contrast_stage7_promotion_allowed": underpowered_pilot.get(
                "summary", {}
            ).get("protected_failure_contrast_stage7_promotion_allowed"),
            "sequence_policy_underpowered_pilot_protected_failure_contrast_stage8_training_allowed": underpowered_pilot.get(
                "summary", {}
            ).get("protected_failure_contrast_stage8_training_allowed"),
            "readiness_status": readiness.get("decision", {}).get("status"),
            "readiness_checked_flag_count": readiness_boundaries.get(
                "checked_flag_count"
            ),
            "readiness_boundary_violation_count": readiness_boundaries.get(
                "violation_count"
            ),
            "readiness_source_artifact_count": len(
                readiness.get("source_artifacts") or {}
            ),
            "unblocker_status": unblocker.get("decision", {}).get("status"),
            "stage8_training_readiness_status": stage8_review.get("decision", {}).get(
                "status"
            ),
            "stage8_training_readiness_checked_flag_count": stage8_review.get(
                "requirements", {}
            ).get("readiness_checked_flag_count"),
            "stage8_training_readiness_boundary_violation_count": stage8_review.get(
                "requirements", {}
            ).get("readiness_boundary_violation_count"),
            "stage8_training_readiness_source_artifact_count": stage8_review.get(
                "requirements", {}
            ).get("readiness_source_artifact_count"),
            "stage8_training_readiness_protected_failure_contrast_post_success_refresh_required": stage8_review.get(
                "requirements", {}
            ).get("protected_failure_contrast_post_success_refresh_required"),
            "stage8_training_readiness_protected_failure_contrast_runtime_direct_routing": stage8_review.get(
                "requirements", {}
            ).get("protected_failure_contrast_runtime_direct_routing"),
            "stage8_training_readiness_protected_failure_contrast_hidden_python_controller": stage8_review.get(
                "requirements", {}
            ).get("protected_failure_contrast_hidden_python_controller"),
            "stage7_post_label_outcome_status": post_label_review.get("decision", {}).get(
                "status"
            ),
            "stage7_post_label_outcome_readiness_checked_flag_count": post_label_review.get(
                "summary", {}
            ).get("readiness_checked_flag_count"),
            "stage7_post_label_outcome_readiness_boundary_violation_count": post_label_review.get(
                "summary", {}
            ).get("readiness_boundary_violation_count"),
            "stage7_post_label_outcome_readiness_source_artifact_count": post_label_review.get(
                "summary", {}
            ).get("readiness_source_artifact_count"),
            "stage7_post_label_outcome_next_step": post_label_review.get("decision", {}).get(
                "recommended_next_step"
            ),
            "stage7_post_label_outcome_protected_failure_contrast_runner_processed_job_count": post_label_review.get(
                "summary", {}
            ).get("protected_failure_contrast_runner_processed_job_count"),
            "stage7_post_label_outcome_protected_failure_contrast_runner_executed_job_count": post_label_review.get(
                "summary", {}
            ).get("protected_failure_contrast_runner_executed_job_count"),
            "stage7_post_label_outcome_protected_failure_contrast_post_success_refresh_required": post_label_review.get(
                "summary", {}
            ).get("protected_failure_contrast_post_success_refresh_required"),
            "stage7_post_label_outcome_protected_failure_contrast_post_success_refresh_script": post_label_review.get(
                "summary", {}
            ).get("protected_failure_contrast_post_success_refresh_script"),
            "stage7_post_label_outcome_protected_failure_contrast_runtime_direct_routing": post_label_review.get(
                "summary", {}
            ).get("protected_failure_contrast_runtime_direct_routing"),
            "stage7_post_label_outcome_protected_failure_contrast_hidden_python_controller": post_label_review.get(
                "summary", {}
            ).get("protected_failure_contrast_hidden_python_controller"),
            "stage7_label_distribution_review_status": label_distribution_review.get(
                "decision", {}
            ).get("status"),
            "stage7_label_distribution_review_next_step": label_distribution_review.get(
                "decision", {}
            ).get("recommended_next_step"),
            "stage7_label_distribution_unique_new_success": label_distribution_review.get(
                "summary", {}
            ).get("unique_new_success_key_count_vs_pre_run"),
            "stage7_label_distribution_duplicate_playouts": label_distribution_review.get(
                "summary", {}
            ).get("duplicate_playout_count"),
            "stage7_additional_clean_sampling_manifest_status": additional_manifest.get(
                "decision", {}
            ).get("status"),
            "stage7_additional_clean_sampling_runner_status": additional_runner.get(
                "decision", {}
            ).get("status"),
            "stage7_additional_clean_sampling_job_count": additional_runner.get(
                "summary", {}
            ).get("job_count"),
            "stage7_additional_clean_sampling_max_samples": additional_manifest.get(
                "summary", {}
            ).get("max_total_samples"),
        },
        "decision": {
            "status": status,
            "recommended_next_step": next_step,
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
    summary = payload["summary"]
    lines = [
        "# KRK Suite Gate Advancement v0",
        "",
        f"Status: `{decision['status']}`",
        "",
        "This passive advancement reruns the safe post-label integration, sequence-policy, readiness, and unblocker artifacts. It never executes labels, changes runtime behavior, trains selectors, promotes Stage 7, or trains Stage 8.",
        "",
        "## Summary",
        "",
    ]
    for key, value in summary.items():
        lines.append(f"- {key}: `{value}`")
    lines.extend(["", "## Steps", ""])
    for result in payload["step_results"]:
        lines.append(
            f"- `{result['step_id']}` status=`{result['decision_status']}` labels=`{result['label_run_allowed']}` runtime=`{result['runtime_changes_allowed']}` artifact_runtime=`{result['artifact_runtime_behavior_changed']}`"
        )
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
