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

PROTECTED_FAILURE_CONTRAST_APPROVAL_REQUEST_REPAIR_STATUSES = {
    "sequence_policy_pilot_blocked_pending_protected_failure_contrast_approval_request_repair",
    "stage8_training_blocked_pending_protected_failure_contrast_approval_request_repair",
    "post_label_outcome_blocked_pending_protected_failure_contrast_approval_request_repair",
    "krk_suite_readiness_blocked_pending_protected_failure_contrast_approval_request_repair",
}

PROTECTED_FAILURE_CONTRAST_EXECUTION_READINESS_STATUSES = {
    "sequence_policy_pilot_blocked_pending_protected_failure_contrast_execution_readiness",
    "stage8_training_blocked_pending_protected_failure_contrast_execution_readiness",
    "post_label_outcome_blocked_pending_protected_failure_contrast_execution_readiness",
    "krk_suite_protected_failure_contrast_unblocker_blocked_pending_execution_readiness",
}

PROTECTED_FAILURE_CONTRAST_CONTROL_PLANE_GATE_REVIEW_STATUSES = {
    "krk_suite_protected_failure_contrast_unblocker_blocked_pending_control_plane_gate_review",
    "krk_suite_readiness_blocked_pending_protected_failure_contrast_control_plane_gate_review",
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
        "step_id": "candidate_generator_coverage_audit",
        "script": "scripts/audit_krk_candidate_generator_coverage_v0.py",
        "output_json": "reports/krk_candidate_generator_coverage_audit_v0.json",
    },
    {
        "step_id": "validated_provider_candidate_set_audit",
        "script": "scripts/audit_krk_validated_provider_candidate_set_v0.py",
        "output_json": "reports/krk_validated_provider_candidate_set_audit_v0.json",
    },
    {
        "step_id": "two_stage_candidate_selection_review",
        "script": "scripts/summarize_krk_two_stage_candidate_selection_review_v0.py",
        "output_json": "reports/krk_two_stage_candidate_selection_review_v0.json",
    },
    {
        "step_id": "two_stage_candidate_selection_benchmark_plan",
        "script": "scripts/plan_krk_two_stage_candidate_selection_benchmark_v0.py",
        "output_json": "reports/krk_two_stage_candidate_selection_benchmark_plan_v0.json",
    },
    {
        "step_id": "two_stage_candidate_selection_benchmark",
        "script": "scripts/build_krk_two_stage_candidate_selection_benchmark_v0.py",
        "output_json": "reports/krk_two_stage_candidate_selection_benchmark_v0.json",
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


def _find_approval_option(gate: dict[str, Any], option_id: str) -> dict[str, Any]:
    for option in gate.get("approval_options") or []:
        if option.get("option_id") == option_id:
            return option
    return {}


def _find_first_approval_option(
    gate: dict[str, Any], option_ids: tuple[str, ...]
) -> dict[str, Any]:
    for option_id in option_ids:
        option = _find_approval_option(gate, option_id)
        if option:
            return option
    return {}


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
    current_control_plane_gate = _load_json("reports/krk_current_control_plane_gate_v0.json")
    current_gate_collection_option = _find_approval_option(
        current_control_plane_gate,
        "approve_protected_plan_window_failure_contrast_collection",
    )
    current_gate_blocking_option = _find_first_approval_option(
        current_control_plane_gate,
        (
            "repair_protected_stack_validation",
            "repair_protected_failure_contrast_approval_request_scope",
            "review_protected_plan_window_failure_contrast_execution_readiness",
            "review_protected_plan_window_failure_contrast_manifest",
            "review_protected_plan_window_failure_contrast_plan",
        ),
    )
    current_gate_approval_option_ids = [
        option.get("option_id")
        for option in current_control_plane_gate.get("approval_options") or []
    ]
    current_gate_collection_option_available = bool(current_gate_collection_option)
    current_gate_collection_command_available = bool(
        current_gate_collection_option.get("command_if_explicitly_approved")
    )
    readiness_control_plane_gate_review_blockers = (
        readiness.get("control_plane_gate_review_blockers") or []
    )
    readiness_explicit_gate_blockers = readiness.get("explicit_gate_blockers") or []
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
    failure_contrast_approval_request_decision = (
        failure_contrast_approval_request.get("decision") or {}
    )
    failure_contrast_approval_request_status = (
        failure_contrast_approval_request_decision.get("status")
    )
    failure_contrast_approval_request_blockers = (
        failure_contrast_approval_request.get("blockers") or []
    )
    failure_contrast_approval_request_summary = (
        failure_contrast_approval_request.get("summary") or {}
    )
    protected_failure_contrast_gate = readiness.get("protected_failure_contrast_gate") or {}
    protected_failure_contrast_gate_approval_request_status = (
        protected_failure_contrast_gate.get("approval_request_status")
    )
    protected_failure_contrast_gate_approval_request_blockers = (
        protected_failure_contrast_gate.get("approval_request_blockers") or []
    )
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
        status=failure_contrast_approval_request_status,
        ready_status="protected_plan_window_failure_contrast_approval_request_ready",
        blockers=failure_contrast_approval_request_blockers,
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
    clean_curriculum_run_lineage_gate = (
        readiness.get("clean_curriculum_run_lineage_gate") or {}
    )
    strategy_sequence_architecture_gate = (
        readiness.get("strategy_sequence_architecture_gate") or {}
    )
    strategy_owner_contrast_gate = readiness.get("strategy_owner_contrast_gate") or {}
    selector_objective_normalization_gate = (
        readiness.get("selector_objective_normalization_gate") or {}
    )
    selector_label_balance_gate = readiness.get("selector_label_balance_gate") or {}
    ownership_selection_context_gate = (
        readiness.get("ownership_selection_context_gate") or {}
    )
    selector_negative_suppression_gate = (
        readiness.get("selector_negative_suppression_blocker_gate") or {}
    )
    abstention_selector_safety_gate = (
        readiness.get("abstention_selector_safety_gate") or {}
    )
    targeted_ownership_recovery_gate = (
        readiness.get("targeted_ownership_recovery_gate") or {}
    )
    balanced_hard_negative_gate = readiness.get("balanced_hard_negative_gate") or {}
    stronger_selector_feature_gate = (
        readiness.get("stronger_selector_feature_gate") or {}
    )
    selected_provider_diversity_gate = (
        readiness.get("selected_provider_diversity_gate") or {}
    )
    state_local_contrast_gate = readiness.get("state_local_contrast_gate") or {}
    state_local_paired_ownership_gate = (
        readiness.get("state_local_paired_ownership_gate") or {}
    )
    selected_owner_failure_risk_proxy_gate = (
        readiness.get("selected_owner_failure_risk_proxy_gate") or {}
    )
    progress_window_reconsideration_gate = (
        readiness.get("progress_window_reconsideration_gate") or {}
    )
    clean_replacement_review_gate = readiness.get("clean_replacement_review_gate") or {}
    active_stack_path_status = protected_stack.get("active_stack_path_status") or {}
    rollback_stack_path_status = protected_stack.get("rollback_stack_path_status") or {}
    readiness_boundaries = readiness.get("runtime_and_training_boundaries") or {}
    protected_missing_provider_gate = (
        readiness.get("protected_missing_provider_gate") or {}
    )
    strategy_sequence_candidate_source_gate = (
        readiness.get("strategy_sequence_candidate_source_gate") or {}
    )
    repair_monitor_trace_feature_gate = (
        readiness.get("repair_monitor_trace_feature_gate") or {}
    )
    stage5_6_candidate_generation_refresh_gate = (
        readiness.get("stage5_6_candidate_generation_refresh_gate") or {}
    )
    cross_stage_candidate_generation_scope_gate = (
        readiness.get("cross_stage_candidate_generation_scope_gate") or {}
    )
    selector_objective_lineage_gate = (
        readiness.get("selector_objective_lineage_gate") or {}
    )
    selector_objective_gate = readiness.get("selector_objective_gate") or {}
    stage4_first_move_diagnostic_gate = (
        readiness.get("stage4_first_move_diagnostic_gate") or {}
    )
    candidate_generation_training_refresh_gate = (
        readiness.get("candidate_generation_training_refresh_gate") or {}
    )
    candidate_generation_trace_context_gate = (
        readiness.get("candidate_generation_trace_context_gate") or {}
    )
    strategy_arbitration_gate = readiness.get("strategy_arbitration_gate") or {}
    strategy_monitor_maturity_gate = (
        readiness.get("strategy_monitor_maturity_gate") or {}
    )
    internal_terminal_readiness_gate = (
        readiness.get("internal_terminal_readiness_gate") or {}
    )
    protected_stack_repair_statuses = {
        "sequence_policy_pilot_blocked_pending_protected_stack_repair",
        "stage8_training_blocked_pending_protected_stack_repair",
        "post_label_outcome_blocked_pending_protected_stack_repair",
    }
    protected_stack_repair_required = (
        protected_stack.get("ready") is False
        or protected_stack.get("rollback_paths_preserved") is False
        or active_stack_path_status.get("all_paths_safe") is False
        or active_stack_path_status.get("all_paths_exist") is False
        or rollback_stack_path_status.get("all_paths_safe") is False
        or rollback_stack_path_status.get("all_paths_exist") is False
        or protected_stack.get("rollback_common_paths_distinct") is False
        or protected_stack.get("filesystem_snapshots_replaced") is True
        or underpowered_pilot.get("decision", {}).get("status")
        in protected_stack_repair_statuses
        or stage8_review.get("decision", {}).get("status")
        in protected_stack_repair_statuses
        or post_label_review.get("decision", {}).get("status")
        in protected_stack_repair_statuses
    )
    protected_failure_contrast_approval_request_repair_required = (
        benchmark_ready
        and (
            failure_contrast_approval_request_status
            == "protected_plan_window_failure_contrast_approval_request_blocked"
            or protected_failure_contrast_gate_approval_request_status
            == "protected_plan_window_failure_contrast_approval_request_blocked"
            or bool(failure_contrast_approval_request_blockers)
            or bool(protected_failure_contrast_gate_approval_request_blockers)
            or protected_failure_contrast_gate.get("approval_request_ready_for_collection")
            is False
            or failure_contrast_approval_request_summary.get("request_ready") is False
            or readiness.get("decision", {}).get("status")
            in PROTECTED_FAILURE_CONTRAST_APPROVAL_REQUEST_REPAIR_STATUSES
            or underpowered_pilot.get("decision", {}).get("status")
            in PROTECTED_FAILURE_CONTRAST_APPROVAL_REQUEST_REPAIR_STATUSES
            or stage8_review.get("decision", {}).get("status")
            in PROTECTED_FAILURE_CONTRAST_APPROVAL_REQUEST_REPAIR_STATUSES
            or post_label_review.get("decision", {}).get("status")
            in PROTECTED_FAILURE_CONTRAST_APPROVAL_REQUEST_REPAIR_STATUSES
        )
    )
    protected_failure_contrast_execution_readiness_required = (
        benchmark_ready
        and (
            failure_contrast_execution_readiness.get("decision", {}).get("status")
            != "protected_plan_window_failure_contrast_execution_ready_pending_explicit_approval"
            or failure_contrast_runner.get("decision", {}).get("status")
            != "protected_plan_window_failure_contrast_runner_dry_run_ready"
            or protected_failure_contrast_gate.get("status")
            == "protected_plan_window_failure_contrast_execution_blocked"
            or underpowered_pilot.get("decision", {}).get("status")
            in PROTECTED_FAILURE_CONTRAST_EXECUTION_READINESS_STATUSES
            or stage8_review.get("decision", {}).get("status")
            in PROTECTED_FAILURE_CONTRAST_EXECUTION_READINESS_STATUSES
            or post_label_review.get("decision", {}).get("status")
            in PROTECTED_FAILURE_CONTRAST_EXECUTION_READINESS_STATUSES
            or unblocker.get("decision", {}).get("status")
            in PROTECTED_FAILURE_CONTRAST_EXECUTION_READINESS_STATUSES
        )
    )
    protected_failure_contrast_control_plane_gate_review_required = (
        benchmark_ready
        and not protected_failure_contrast_approval_request_repair_required
        and not protected_failure_contrast_execution_readiness_required
        and not current_gate_collection_command_available
        and (
            current_gate_collection_option_available is False
            or bool(readiness_control_plane_gate_review_blockers)
            or readiness.get("decision", {}).get("status")
            in PROTECTED_FAILURE_CONTRAST_CONTROL_PLANE_GATE_REVIEW_STATUSES
            or unblocker.get("decision", {}).get("status")
            in PROTECTED_FAILURE_CONTRAST_CONTROL_PLANE_GATE_REVIEW_STATUSES
        )
    )
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
    elif protected_stack_repair_required:
        status = "krk_suite_passive_advancement_blocked_pending_protected_stack_repair"
        next_step = "repair_protected_stack_validation"
    elif protected_failure_contrast_approval_request_repair_required:
        status = (
            "krk_suite_passive_advancement_blocked_pending_"
            "protected_failure_contrast_approval_request_repair"
        )
        next_step = "repair_protected_failure_contrast_approval_request_scope"
    elif protected_failure_contrast_execution_readiness_required:
        status = (
            "krk_suite_passive_advancement_blocked_pending_"
            "protected_failure_contrast_execution_readiness"
        )
        next_step = "review_protected_plan_window_failure_contrast_execution_readiness"
    elif protected_failure_contrast_control_plane_gate_review_required:
        status = (
            "krk_suite_passive_advancement_blocked_pending_"
            "protected_failure_contrast_control_plane_gate_review"
        )
        next_step = (
            "review_current_control_plane_gate_for_protected_failure_contrast_collection"
        )
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
            "protected_stack_active_paths_safe": active_stack_path_status.get(
                "all_paths_safe"
            ),
            "protected_stack_active_paths_exist": active_stack_path_status.get(
                "all_paths_exist"
            ),
            "protected_stack_rollback_paths_safe": rollback_stack_path_status.get(
                "all_paths_safe"
            ),
            "protected_stack_rollback_paths_exist": rollback_stack_path_status.get(
                "all_paths_exist"
            ),
            "protected_stack_rollback_common_paths_distinct": protected_stack.get(
                "rollback_common_paths_distinct"
            ),
            "protected_stack_filesystem_snapshots_replaced": protected_stack.get(
                "filesystem_snapshots_replaced"
            ),
            "clean_curriculum_run_lineage_passive_ready": (
                clean_curriculum_run_lineage_gate.get("passive_lineage_ready")
            ),
            "clean_curriculum_checkpoint_plan_status": (
                clean_curriculum_run_lineage_gate.get("checkpoint_plan_status")
            ),
            "clean_curriculum_execution_manifest_status": (
                clean_curriculum_run_lineage_gate.get("execution_manifest_status")
            ),
            "clean_curriculum_execution_manifest_full_run_authorized": (
                clean_curriculum_run_lineage_gate.get(
                    "execution_manifest_full_run_authorized"
                )
            ),
            "clean_curriculum_preflight_status": (
                clean_curriculum_run_lineage_gate.get("preflight_status")
            ),
            "clean_curriculum_preflight_blocker_count": (
                clean_curriculum_run_lineage_gate.get("preflight_blocker_count")
            ),
            "clean_curriculum_smoke_result_status": (
                clean_curriculum_run_lineage_gate.get("smoke_result_status")
            ),
            "clean_curriculum_initial_run_status": (
                clean_curriculum_run_lineage_gate.get("initial_run_status")
            ),
            "clean_curriculum_initial_run_complete": (
                clean_curriculum_run_lineage_gate.get(
                    "initial_run_full_clean_retrain_complete"
                )
            ),
            "clean_curriculum_retry1_status": (
                clean_curriculum_run_lineage_gate.get("retry1_status")
            ),
            "clean_curriculum_retry1_complete_through_stage6": (
                clean_curriculum_run_lineage_gate.get("retry1_complete_through_stage6")
            ),
            "clean_curriculum_retry1_promoted_by_this_artifact": (
                clean_curriculum_run_lineage_gate.get("retry1_promoted_by_this_artifact")
            ),
            "clean_curriculum_guardrail_status": (
                clean_curriculum_run_lineage_gate.get("guardrail_status")
            ),
            "clean_curriculum_stage6_gap_status": (
                clean_curriculum_run_lineage_gate.get("stage6_gap_status")
            ),
            "clean_curriculum_stage5_control_debt_status": (
                clean_curriculum_run_lineage_gate.get("stage5_control_debt_status")
            ),
            "clean_curriculum_stage4_caveat_control_status": (
                clean_curriculum_run_lineage_gate.get("stage4_caveat_control_status")
            ),
            "clean_curriculum_stage7_promotion_allowed": (
                clean_curriculum_run_lineage_gate.get("stage7_promotion_allowed")
            ),
            "clean_curriculum_stage8_training_allowed": (
                clean_curriculum_run_lineage_gate.get("stage8_training_allowed")
            ),
            "strategy_sequence_architecture_passive_ready": (
                strategy_sequence_architecture_gate.get("passive_architecture_ready")
            ),
            "strategy_sequence_architecture_review_status": (
                strategy_sequence_architecture_gate.get("architecture_review_status")
            ),
            "strategy_sequence_architecture_runtime_work_allowed": (
                strategy_sequence_architecture_gate.get("architecture_runtime_work_allowed")
            ),
            "strategy_sequence_architecture_next_objective_ids": (
                strategy_sequence_architecture_gate.get("architecture_next_objective_ids")
            ),
            "strategy_sequence_evidence_plan_status": (
                strategy_sequence_architecture_gate.get("evidence_plan_status")
            ),
            "strategy_sequence_evidence_plan_runtime_work_allowed": (
                strategy_sequence_architecture_gate.get("evidence_plan_runtime_work_allowed")
            ),
            "strategy_sequence_inventory_status": (
                strategy_sequence_architecture_gate.get("inventory_status")
            ),
            "strategy_sequence_inventory_runtime_work_allowed": (
                strategy_sequence_architecture_gate.get("inventory_runtime_work_allowed")
            ),
            "strategy_sequence_inventory_clean_gate_closed": (
                strategy_sequence_architecture_gate.get(
                    "inventory_sequence_policy_clean_gate_closed"
                )
            ),
            "strategy_sequence_inventory_state_holdout_gap_blocks_runtime": (
                strategy_sequence_architecture_gate.get(
                    "inventory_state_holdout_gap_blocks_runtime"
                )
            ),
            "strategy_sequence_inventory_stage7_is_held_out": (
                strategy_sequence_architecture_gate.get("inventory_stage7_is_held_out")
            ),
            "strategy_sequence_runtime_selector_implemented": (
                strategy_sequence_architecture_gate.get("runtime_selector_implemented")
            ),
            "strategy_sequence_stage7_promotion_allowed": (
                strategy_sequence_architecture_gate.get("stage7_promotion_allowed")
            ),
            "strategy_sequence_stage8_training_allowed": (
                strategy_sequence_architecture_gate.get("stage8_training_allowed")
            ),
            "strategy_owner_contrast_passive_probe_ready": (
                strategy_owner_contrast_gate.get("passive_probe_ready")
            ),
            "strategy_owner_contrast_label_plan_status": (
                strategy_owner_contrast_gate.get("label_plan_status")
            ),
            "strategy_owner_contrast_label_plan_job_count": (
                strategy_owner_contrast_gate.get("label_plan_job_count")
            ),
            "strategy_owner_contrast_label_plan_stage7_job_count": (
                strategy_owner_contrast_gate.get("label_plan_stage7_job_count")
            ),
            "strategy_owner_contrast_execution_manifest_status": (
                strategy_owner_contrast_gate.get("execution_manifest_status")
            ),
            "strategy_owner_contrast_execution_manifest_stage7_jobs": (
                strategy_owner_contrast_gate.get("execution_manifest_stage7_jobs")
            ),
            "strategy_owner_contrast_control_label_count": (
                strategy_owner_contrast_gate.get("control_label_count")
            ),
            "strategy_owner_contrast_control_label_stage7_count": (
                strategy_owner_contrast_gate.get("control_label_stage7_count")
            ),
            "strategy_owner_contrast_dataset_status": (
                strategy_owner_contrast_gate.get("dataset_status")
            ),
            "strategy_owner_contrast_dataset_row_count": (
                strategy_owner_contrast_gate.get("dataset_row_count")
            ),
            "strategy_owner_contrast_dataset_stage7_training_rows": (
                strategy_owner_contrast_gate.get("dataset_stage7_training_rows")
            ),
            "strategy_owner_contrast_readiness_selector_sandbox_ready": (
                strategy_owner_contrast_gate.get("readiness_selector_sandbox_ready")
            ),
            "strategy_owner_contrast_probe_status": (
                strategy_owner_contrast_gate.get("probe_status")
            ),
            "strategy_owner_contrast_probe_readiness_blockers": (
                strategy_owner_contrast_gate.get("probe_readiness_blockers")
            ),
            "strategy_owner_contrast_runtime_arbiter_implemented": (
                strategy_owner_contrast_gate.get("runtime_arbiter_implemented")
            ),
            "strategy_owner_contrast_runtime_terminals_added": (
                strategy_owner_contrast_gate.get("runtime_terminals_added")
            ),
            "strategy_owner_contrast_stage7_promotion_allowed": (
                strategy_owner_contrast_gate.get("stage7_promotion_allowed")
            ),
            "strategy_owner_contrast_stage8_training_allowed": (
                strategy_owner_contrast_gate.get("stage8_training_allowed")
            ),
            "selector_objective_normalization_passive_ready": (
                selector_objective_normalization_gate.get("passive_objective_ready")
            ),
            "selector_objective_arbitration_status": (
                selector_objective_normalization_gate.get("arbitration_objective_status")
            ),
            "selector_objective_normalized_status": (
                selector_objective_normalization_gate.get("normalized_objective_status")
            ),
            "selector_objective_normalized_probe_status": (
                selector_objective_normalization_gate.get("normalized_probe_status")
            ),
            "selector_objective_normalized_probe_underpowered": (
                selector_objective_normalization_gate.get(
                    "normalized_probe_benchmark_underpowered"
                )
            ),
            "selector_objective_architecture_status": (
                selector_objective_normalization_gate.get("selector_architecture_status")
            ),
            "selector_objective_architecture_sandbox_ready": (
                selector_objective_normalization_gate.get(
                    "selector_architecture_sandbox_ready"
                )
            ),
            "selector_objective_split_dataset_status": (
                selector_objective_normalization_gate.get("split_dataset_status")
            ),
            "selector_objective_split_dataset_row_count": (
                selector_objective_normalization_gate.get(
                    "split_dataset_objective_row_count"
                )
            ),
            "selector_objective_split_dataset_selector_training_row_count": (
                selector_objective_normalization_gate.get(
                    "split_dataset_selector_training_row_count"
                )
            ),
            "selector_objective_split_dataset_stage7_row_count": (
                selector_objective_normalization_gate.get("split_dataset_stage7_row_count")
            ),
            "selector_objective_split_readiness_status": (
                selector_objective_normalization_gate.get("split_readiness_status")
            ),
            "selector_objective_split_readiness_selector_training_allowed": (
                selector_objective_normalization_gate.get(
                    "split_readiness_selector_training_allowed"
                )
            ),
            "selector_objective_split_readiness_ownership_underpowered": (
                selector_objective_normalization_gate.get(
                    "split_readiness_ownership_probe_underpowered"
                )
            ),
            "selector_objective_runtime_selector_implemented": (
                selector_objective_normalization_gate.get("runtime_selector_implemented")
            ),
            "selector_objective_runtime_terminals_added": (
                selector_objective_normalization_gate.get("runtime_terminals_added")
            ),
            "selector_objective_stage7_promotion_allowed": (
                selector_objective_normalization_gate.get("stage7_promotion_allowed")
            ),
            "selector_objective_stage8_training_allowed": (
                selector_objective_normalization_gate.get("stage8_training_allowed")
            ),
            "selector_label_balance_passive_ready": (
                selector_label_balance_gate.get("passive_label_balance_ready")
            ),
            "selector_label_balance_stratified_dataset_status": (
                selector_label_balance_gate.get("stratified_dataset_status")
            ),
            "selector_label_balance_stratified_dataset_row_count": (
                selector_label_balance_gate.get("stratified_dataset_row_count")
            ),
            "selector_label_balance_stratified_dataset_stage7_training_rows": (
                selector_label_balance_gate.get(
                    "stratified_dataset_stage7_training_rows"
                )
            ),
            "selector_label_balance_stratified_probe_status": (
                selector_label_balance_gate.get("stratified_probe_status")
            ),
            "selector_label_balance_stratified_probe_underbalanced": (
                selector_label_balance_gate.get("stratified_probe_underbalanced")
            ),
            "selector_label_balance_balanced_dataset_status": (
                selector_label_balance_gate.get("balanced_dataset_status")
            ),
            "selector_label_balance_balanced_dataset_row_count": (
                selector_label_balance_gate.get("balanced_dataset_row_count")
            ),
            "selector_label_balance_balanced_dataset_stage7_training_rows": (
                selector_label_balance_gate.get("balanced_dataset_stage7_training_rows")
            ),
            "selector_label_balance_balanced_probe_status": (
                selector_label_balance_gate.get("balanced_probe_status")
            ),
            "selector_label_balance_balanced_probe_best_accuracy": (
                selector_label_balance_gate.get("balanced_probe_best_accuracy")
            ),
            "selector_label_balance_architecture_status": (
                selector_label_balance_gate.get("architecture_status")
            ),
            "selector_label_balance_architecture_runtime_arbiter_allowed": (
                selector_label_balance_gate.get("architecture_runtime_arbiter_allowed")
            ),
            "selector_label_balance_architecture_selector_sandbox_ready": (
                selector_label_balance_gate.get("architecture_selector_sandbox_ready")
            ),
            "selector_label_balance_runtime_selector_implemented": (
                selector_label_balance_gate.get("runtime_selector_implemented")
            ),
            "selector_label_balance_runtime_dtm_or_tablebase_lookup": (
                selector_label_balance_gate.get("runtime_dtm_or_tablebase_lookup")
            ),
            "selector_label_balance_stage7_promotion_allowed": (
                selector_label_balance_gate.get("stage7_promotion_allowed")
            ),
            "selector_label_balance_stage8_training_allowed": (
                selector_label_balance_gate.get("stage8_training_allowed")
            ),
            "ownership_selection_context_passive_ready": (
                ownership_selection_context_gate.get("passive_context_ready")
            ),
            "ownership_selection_context_label_dataset_status": (
                ownership_selection_context_gate.get("label_dataset_status")
            ),
            "ownership_selection_context_label_dataset_merged_row_count": (
                ownership_selection_context_gate.get("label_dataset_merged_row_count")
            ),
            "ownership_selection_context_label_dataset_selector_training_row_count": (
                ownership_selection_context_gate.get(
                    "label_dataset_selector_training_row_count"
                )
            ),
            "ownership_selection_context_label_dataset_stage7_row_count": (
                ownership_selection_context_gate.get("label_dataset_stage7_row_count")
            ),
            "ownership_selection_context_dataset_status": (
                ownership_selection_context_gate.get("context_dataset_status")
            ),
            "ownership_selection_context_dataset_row_count": (
                ownership_selection_context_gate.get("context_dataset_row_count")
            ),
            "ownership_selection_context_dataset_selector_training_row_count": (
                ownership_selection_context_gate.get(
                    "context_dataset_selector_training_row_count"
                )
            ),
            "ownership_selection_context_dataset_stage7_row_count": (
                ownership_selection_context_gate.get("context_dataset_stage7_row_count")
            ),
            "ownership_selection_context_probe_status": (
                ownership_selection_context_gate.get("context_probe_status")
            ),
            "ownership_selection_context_probe_underpowered": (
                ownership_selection_context_gate.get("context_probe_underpowered")
            ),
            "ownership_selection_source_diversity_status": (
                ownership_selection_context_gate.get("source_diversity_status")
            ),
            "ownership_selection_source_diversity_non_stage0_ownership_row_count": (
                ownership_selection_context_gate.get(
                    "source_diversity_non_stage0_ownership_row_count"
                )
            ),
            "ownership_selection_context_runtime_selector_implemented": (
                ownership_selection_context_gate.get("runtime_selector_implemented")
            ),
            "ownership_selection_context_runtime_dtm_or_tablebase_lookup": (
                ownership_selection_context_gate.get("runtime_dtm_or_tablebase_lookup")
            ),
            "ownership_selection_context_stage7_promotion_allowed": (
                ownership_selection_context_gate.get("stage7_promotion_allowed")
            ),
            "ownership_selection_context_stage8_training_allowed": (
                ownership_selection_context_gate.get("stage8_training_allowed")
            ),
            "selector_negative_suppression_blocker_passive_ready": (
                selector_negative_suppression_gate.get("passive_blocker_ready")
            ),
            "selector_negative_suppression_protected_max_only_status": (
                selector_negative_suppression_gate.get("protected_max_only_status")
            ),
            "selector_negative_suppression_protected_max_only_frame_count": (
                selector_negative_suppression_gate.get(
                    "protected_max_only_frame_count"
                )
            ),
            "selector_negative_suppression_status": (
                selector_negative_suppression_gate.get("negative_suppression_status")
            ),
            "selector_negative_suppression_runtime_work_allowed": (
                selector_negative_suppression_gate.get(
                    "negative_suppression_runtime_work_allowed"
                )
            ),
            "selector_negative_suppression_selector_training_allowed": (
                selector_negative_suppression_gate.get(
                    "negative_suppression_selector_training_allowed"
                )
            ),
            "selector_negative_suppression_candidate_generator_runtime_allowed": (
                selector_negative_suppression_gate.get(
                    "negative_suppression_candidate_generator_runtime_allowed"
                )
            ),
            "selector_negative_suppression_runtime_selector_readiness_status": (
                selector_negative_suppression_gate.get(
                    "runtime_selector_readiness_status"
                )
            ),
            "selector_negative_suppression_runtime_test_allowed_next": (
                selector_negative_suppression_gate.get(
                    "runtime_selector_readiness_runtime_test_allowed_next"
                )
            ),
            "selector_negative_suppression_runtime_selector_implemented": (
                selector_negative_suppression_gate.get("runtime_selector_implemented")
            ),
            "selector_negative_suppression_runtime_dtm_or_tablebase_lookup": (
                selector_negative_suppression_gate.get(
                    "runtime_dtm_or_tablebase_lookup"
                )
            ),
            "selector_negative_suppression_stage7_promotion_allowed": (
                selector_negative_suppression_gate.get("stage7_promotion_allowed")
            ),
            "selector_negative_suppression_stage8_training_allowed": (
                selector_negative_suppression_gate.get("stage8_training_allowed")
            ),
            "abstention_selector_safety_passive_ready": (
                abstention_selector_safety_gate.get("passive_safety_ready")
            ),
            "abstention_selector_first_objective_status": (
                abstention_selector_safety_gate.get("first_objective_status")
            ),
            "abstention_safe_preservation_review_status": (
                abstention_selector_safety_gate.get("safe_preservation_review_status")
            ),
            "abstention_training_dataset_status": (
                abstention_selector_safety_gate.get("training_dataset_status")
            ),
            "abstention_training_dataset_row_count": (
                abstention_selector_safety_gate.get("training_dataset_row_count")
            ),
            "abstention_training_dataset_stage7_training_rows": (
                abstention_selector_safety_gate.get(
                    "training_dataset_stage7_training_rows"
                )
            ),
            "abstention_training_probe_status": (
                abstention_selector_safety_gate.get("training_probe_status")
            ),
            "abstention_context_dataset_status": (
                abstention_selector_safety_gate.get("context_dataset_status")
            ),
            "abstention_context_probe_status": (
                abstention_selector_safety_gate.get("context_probe_status")
            ),
            "abstention_context_probe_improved_negative_suppression": (
                abstention_selector_safety_gate.get(
                    "context_probe_improved_negative_suppression"
                )
            ),
            "abstention_context_error_audit_status": (
                abstention_selector_safety_gate.get("context_error_audit_status")
            ),
            "abstention_context_error_false_positive_count": (
                abstention_selector_safety_gate.get(
                    "context_error_false_positive_count"
                )
            ),
            "abstention_feature_gap_next_step_status": (
                abstention_selector_safety_gate.get("feature_gap_next_step_status")
            ),
            "abstention_feature_gap_implementation_allowed": (
                abstention_selector_safety_gate.get("feature_gap_implementation_allowed")
            ),
            "abstention_feature_gap_runtime_ready": (
                abstention_selector_safety_gate.get("feature_gap_runtime_ready")
            ),
            "abstention_runtime_selector_implemented": (
                abstention_selector_safety_gate.get("runtime_selector_implemented")
            ),
            "abstention_runtime_dtm_or_tablebase_lookup": (
                abstention_selector_safety_gate.get("runtime_dtm_or_tablebase_lookup")
            ),
            "abstention_stage7_promotion_allowed": (
                abstention_selector_safety_gate.get("stage7_promotion_allowed")
            ),
            "abstention_stage8_training_allowed": (
                abstention_selector_safety_gate.get("stage8_training_allowed")
            ),
            "targeted_ownership_recovery_passive_ready": (
                targeted_ownership_recovery_gate.get("passive_recovery_ready")
            ),
            "targeted_ownership_non_stage0_manifest_status": (
                targeted_ownership_recovery_gate.get("non_stage0_manifest_status")
            ),
            "targeted_ownership_non_stage0_manifest_job_count": (
                targeted_ownership_recovery_gate.get("non_stage0_manifest_job_count")
            ),
            "targeted_ownership_non_stage0_manifest_stage7_job_count": (
                targeted_ownership_recovery_gate.get(
                    "non_stage0_manifest_stage7_job_count"
                )
            ),
            "targeted_ownership_non_stage0_labels_status": (
                targeted_ownership_recovery_gate.get("non_stage0_labels_status")
            ),
            "targeted_ownership_non_stage0_label_count": (
                targeted_ownership_recovery_gate.get("non_stage0_label_count")
            ),
            "targeted_ownership_non_stage0_preserved_count": (
                targeted_ownership_recovery_gate.get("non_stage0_preserved_count")
            ),
            "targeted_ownership_non_stage0_stage7_training_rows": (
                targeted_ownership_recovery_gate.get("non_stage0_stage7_training_rows")
            ),
            "targeted_ownership_negative_manifest_status": (
                targeted_ownership_recovery_gate.get("negative_manifest_status")
            ),
            "targeted_ownership_negative_manifest_job_count": (
                targeted_ownership_recovery_gate.get("negative_manifest_job_count")
            ),
            "targeted_ownership_negative_manifest_stage7_job_count": (
                targeted_ownership_recovery_gate.get(
                    "negative_manifest_stage7_job_count"
                )
            ),
            "targeted_ownership_negative_labels_status": (
                targeted_ownership_recovery_gate.get("negative_labels_status")
            ),
            "targeted_ownership_negative_label_count": (
                targeted_ownership_recovery_gate.get("negative_label_count")
            ),
            "targeted_ownership_negative_targeted_owner_failed_count": (
                targeted_ownership_recovery_gate.get(
                    "negative_targeted_owner_failed_count"
                )
            ),
            "targeted_ownership_negative_stage7_training_rows": (
                targeted_ownership_recovery_gate.get("negative_stage7_training_rows")
            ),
            "targeted_ownership_runtime_selector_implemented": (
                targeted_ownership_recovery_gate.get("runtime_selector_implemented")
            ),
            "targeted_ownership_runtime_dtm_or_tablebase_lookup": (
                targeted_ownership_recovery_gate.get("runtime_dtm_or_tablebase_lookup")
            ),
            "targeted_ownership_runtime_terminals_added": (
                targeted_ownership_recovery_gate.get("runtime_terminals_added")
            ),
            "targeted_ownership_stage7_promotion_allowed": (
                targeted_ownership_recovery_gate.get("stage7_promotion_allowed")
            ),
            "targeted_ownership_stage8_training_allowed": (
                targeted_ownership_recovery_gate.get("stage8_training_allowed")
            ),
            "balanced_hard_negative_passive_ready": (
                balanced_hard_negative_gate.get("passive_evidence_ready")
            ),
            "balanced_hard_negative_label_plan_status": (
                balanced_hard_negative_gate.get("label_plan_status")
            ),
            "balanced_hard_negative_label_plan_job_count": (
                balanced_hard_negative_gate.get("label_plan_job_count")
            ),
            "balanced_hard_negative_label_plan_stage7_jobs": (
                balanced_hard_negative_gate.get("label_plan_stage7_jobs")
            ),
            "balanced_hard_negative_execution_manifest_status": (
                balanced_hard_negative_gate.get("execution_manifest_status")
            ),
            "balanced_hard_negative_execution_manifest_labels_allowed_now": (
                balanced_hard_negative_gate.get(
                    "execution_manifest_labels_allowed_now"
                )
            ),
            "balanced_hard_negative_execution_manifest_stage7_jobs": (
                balanced_hard_negative_gate.get("execution_manifest_stage7_jobs")
            ),
            "balanced_hard_negative_labels_status": (
                balanced_hard_negative_gate.get("labels_status")
            ),
            "balanced_hard_negative_label_count": (
                balanced_hard_negative_gate.get("label_count")
            ),
            "balanced_hard_negative_positive_capacity_count": (
                balanced_hard_negative_gate.get("positive_capacity_count")
            ),
            "balanced_hard_negative_negative_capacity_count": (
                balanced_hard_negative_gate.get("negative_capacity_count")
            ),
            "balanced_hard_negative_stage7_labels": (
                balanced_hard_negative_gate.get("stage7_labels")
            ),
            "balanced_hard_negative_stage7_training_labels": (
                balanced_hard_negative_gate.get("stage7_training_labels")
            ),
            "balanced_hard_negative_evidence_review_status": (
                balanced_hard_negative_gate.get("evidence_review_status")
            ),
            "balanced_hard_negative_evidence_underpowered": (
                balanced_hard_negative_gate.get("evidence_underpowered")
            ),
            "balanced_hard_negative_evidence_expanded_row_count": (
                balanced_hard_negative_gate.get("evidence_expanded_row_count")
            ),
            "balanced_hard_negative_evidence_expanded_hard_negative_count": (
                balanced_hard_negative_gate.get("evidence_expanded_hard_negative_count")
            ),
            "balanced_hard_negative_runtime_selector_implemented": (
                balanced_hard_negative_gate.get("runtime_selector_implemented")
            ),
            "balanced_hard_negative_runtime_dtm_or_tablebase_lookup": (
                balanced_hard_negative_gate.get("runtime_dtm_or_tablebase_lookup")
            ),
            "balanced_hard_negative_runtime_terminals_added": (
                balanced_hard_negative_gate.get("runtime_terminals_added")
            ),
            "balanced_hard_negative_stage7_promotion_allowed": (
                balanced_hard_negative_gate.get("stage7_promotion_allowed")
            ),
            "balanced_hard_negative_stage8_training_allowed": (
                balanced_hard_negative_gate.get("stage8_training_allowed")
            ),
            "stronger_selector_feature_passive_ready": (
                stronger_selector_feature_gate.get("passive_feature_review_ready")
            ),
            "stronger_selector_feature_ablation_status": (
                stronger_selector_feature_gate.get("feature_ablation_status")
            ),
            "stronger_selector_feature_ablation_underpowered": (
                stronger_selector_feature_gate.get("feature_ablation_underpowered")
            ),
            "stronger_selector_feature_ablation_row_count": (
                stronger_selector_feature_gate.get("feature_ablation_row_count")
            ),
            "stronger_selector_feature_ablation_stage7_row_count": (
                stronger_selector_feature_gate.get("feature_ablation_stage7_row_count")
            ),
            "stronger_selector_feature_review_status": (
                stronger_selector_feature_gate.get("feature_review_status")
            ),
            "stronger_selector_feature_improved_over_v2_ablation": (
                stronger_selector_feature_gate.get(
                    "feature_review_improved_over_v2_ablation"
                )
            ),
            "stronger_selector_feature_previous_best_negative_suppression": (
                stronger_selector_feature_gate.get(
                    "feature_review_previous_best_negative_suppression"
                )
            ),
            "stronger_selector_feature_best_negative_suppression": (
                stronger_selector_feature_gate.get(
                    "feature_review_best_negative_suppression"
                )
            ),
            "stronger_selector_feature_best_positive_recall": (
                stronger_selector_feature_gate.get("feature_review_best_positive_recall")
            ),
            "stronger_selector_feature_review_stage7_row_count": (
                stronger_selector_feature_gate.get("feature_review_stage7_row_count")
            ),
            "stronger_selector_feature_runtime_selector_implemented": (
                stronger_selector_feature_gate.get("runtime_selector_implemented")
            ),
            "stronger_selector_feature_runtime_candidate_generator_implemented": (
                stronger_selector_feature_gate.get(
                    "runtime_candidate_generator_implemented"
                )
            ),
            "stronger_selector_feature_runtime_dtm_or_tablebase_lookup": (
                stronger_selector_feature_gate.get("runtime_dtm_or_tablebase_lookup")
            ),
            "stronger_selector_feature_stage7_promotion_allowed": (
                stronger_selector_feature_gate.get("stage7_promotion_allowed")
            ),
            "stronger_selector_feature_stage8_training_allowed": (
                stronger_selector_feature_gate.get("stage8_training_allowed")
            ),
            "selected_provider_diversity_passive_ready": (
                selected_provider_diversity_gate.get("passive_diversity_review_ready")
            ),
            "selected_provider_diversity_evidence_plan_status": (
                selected_provider_diversity_gate.get("evidence_plan_status")
            ),
            "selected_provider_diversity_manifest_status": (
                selected_provider_diversity_gate.get("manifest_status")
            ),
            "selected_provider_diversity_manifest_observations_allowed_now": (
                selected_provider_diversity_gate.get("manifest_observations_allowed_now")
            ),
            "selected_provider_diversity_manifest_job_count": (
                selected_provider_diversity_gate.get("manifest_job_count")
            ),
            "selected_provider_diversity_manifest_stage7_jobs": (
                selected_provider_diversity_gate.get("manifest_stage7_jobs")
            ),
            "selected_provider_diversity_labels_status": (
                selected_provider_diversity_gate.get("labels_status")
            ),
            "selected_provider_diversity_label_count": (
                selected_provider_diversity_gate.get("label_count")
            ),
            "selected_provider_diversity_stage7_training_rows": (
                selected_provider_diversity_gate.get("stage7_training_rows")
            ),
            "selected_provider_diversity_architecture_status": (
                selected_provider_diversity_gate.get("architecture_status")
            ),
            "selected_provider_diversity_architecture_runtime_arbiter_allowed": (
                selected_provider_diversity_gate.get(
                    "architecture_runtime_arbiter_allowed"
                )
            ),
            "selected_provider_diversity_runtime_selector_implemented": (
                selected_provider_diversity_gate.get("runtime_selector_implemented")
            ),
            "selected_provider_diversity_runtime_candidate_generator_implemented": (
                selected_provider_diversity_gate.get(
                    "runtime_candidate_generator_implemented"
                )
            ),
            "selected_provider_diversity_runtime_arbiter_implemented": (
                selected_provider_diversity_gate.get("runtime_arbiter_implemented")
            ),
            "selected_provider_diversity_runtime_dtm_or_tablebase_lookup": (
                selected_provider_diversity_gate.get("runtime_dtm_or_tablebase_lookup")
            ),
            "selected_provider_diversity_stage7_promotion_allowed": (
                selected_provider_diversity_gate.get("stage7_promotion_allowed")
            ),
            "selected_provider_diversity_stage8_training_allowed": (
                selected_provider_diversity_gate.get("stage8_training_allowed")
            ),
            "state_local_contrast_passive_ready": (
                state_local_contrast_gate.get("passive_contrast_ready")
            ),
            "state_local_contrast_labels_status": (
                state_local_contrast_gate.get("labels_status")
            ),
            "state_local_contrast_labels_row_count": (
                state_local_contrast_gate.get("labels_row_count")
            ),
            "state_local_contrast_labels_stage7_challenge_row_count": (
                state_local_contrast_gate.get("labels_stage7_challenge_row_count")
            ),
            "state_local_contrast_labels_usable_training_row_count": (
                state_local_contrast_gate.get("labels_usable_training_row_count")
            ),
            "state_local_contrast_probe_status": (
                state_local_contrast_gate.get("probe_status")
            ),
            "state_local_contrast_probe_training_row_count": (
                state_local_contrast_gate.get("probe_training_row_count")
            ),
            "state_local_contrast_probe_stage7_eval_row_count": (
                state_local_contrast_gate.get("probe_stage7_eval_row_count")
            ),
            "state_local_contrast_probe_stage7_training_leakage": (
                state_local_contrast_gate.get("probe_stage7_training_leakage")
            ),
            "state_local_contrast_readiness_status": (
                state_local_contrast_gate.get("readiness_status")
            ),
            "state_local_contrast_readiness_runtime_test_allowed_next": (
                state_local_contrast_gate.get("readiness_runtime_test_allowed_next")
            ),
            "state_local_contrast_runtime_selector_implemented": (
                state_local_contrast_gate.get("runtime_selector_implemented")
            ),
            "state_local_contrast_runtime_dtm_or_tablebase_lookup": (
                state_local_contrast_gate.get("runtime_dtm_or_tablebase_lookup")
            ),
            "state_local_contrast_stage7_promotion_allowed": (
                state_local_contrast_gate.get("stage7_promotion_allowed")
            ),
            "state_local_contrast_stage8_training_allowed": (
                state_local_contrast_gate.get("stage8_training_allowed")
            ),
            "state_local_paired_ownership_passive_ready": (
                state_local_paired_ownership_gate.get("passive_semantic_gate_ready")
            ),
            "state_local_paired_hard_negative_target_status": (
                state_local_paired_ownership_gate.get(
                    "hard_negative_target_dataset_status"
                )
            ),
            "state_local_paired_hard_negative_target_row_count": (
                state_local_paired_ownership_gate.get("hard_negative_target_row_count")
            ),
            "state_local_paired_hard_negative_training_row_count": (
                state_local_paired_ownership_gate.get("hard_negative_training_row_count")
            ),
            "state_local_paired_hard_negative_stage7_row_count": (
                state_local_paired_ownership_gate.get("hard_negative_stage7_row_count")
            ),
            "state_local_paired_ownership_context_status": (
                state_local_paired_ownership_gate.get("ownership_context_status")
            ),
            "state_local_paired_ownership_context_runtime_threshold_passed": (
                state_local_paired_ownership_gate.get(
                    "ownership_context_runtime_threshold_passed"
                )
            ),
            "state_local_paired_ownership_architecture_status": (
                state_local_paired_ownership_gate.get("ownership_architecture_status")
            ),
            "state_local_paired_inventory_status": (
                state_local_paired_ownership_gate.get("inventory_status")
            ),
            "state_local_paired_inventory_pair_count": (
                state_local_paired_ownership_gate.get("inventory_pair_count")
            ),
            "state_local_paired_inventory_same_state_conflict_pair_count": (
                state_local_paired_ownership_gate.get(
                    "inventory_same_state_conflict_pair_count"
                )
            ),
            "state_local_paired_inventory_selector_training_row_count": (
                state_local_paired_ownership_gate.get(
                    "inventory_selector_training_row_count"
                )
            ),
            "state_local_paired_inventory_stage7_row_count": (
                state_local_paired_ownership_gate.get("inventory_stage7_row_count")
            ),
            "state_local_paired_probe_status": (
                state_local_paired_ownership_gate.get("probe_status")
            ),
            "state_local_paired_probe_threshold_passing_model_count": (
                state_local_paired_ownership_gate.get(
                    "probe_threshold_passing_model_count"
                )
            ),
            "state_local_paired_probe_runtime_feature_passing_model_count": (
                state_local_paired_ownership_gate.get(
                    "probe_runtime_feature_passing_model_count"
                )
            ),
            "state_local_paired_error_audit_status": (
                state_local_paired_ownership_gate.get("error_audit_status")
            ),
            "state_local_paired_review_status": (
                state_local_paired_ownership_gate.get("review_status")
            ),
            "state_local_paired_review_best_objective": (
                state_local_paired_ownership_gate.get("review_best_objective")
            ),
            "state_local_paired_review_runtime_feature_passing_model_count": (
                state_local_paired_ownership_gate.get(
                    "review_runtime_feature_passing_model_count"
                )
            ),
            "state_local_paired_review_stage7_row_count": (
                state_local_paired_ownership_gate.get("review_stage7_row_count")
            ),
            "state_local_paired_runtime_selector_implemented": (
                state_local_paired_ownership_gate.get("runtime_selector_implemented")
            ),
            "state_local_paired_runtime_dtm_or_tablebase_lookup": (
                state_local_paired_ownership_gate.get("runtime_dtm_or_tablebase_lookup")
            ),
            "state_local_paired_runtime_terminals_added": (
                state_local_paired_ownership_gate.get("runtime_terminals_added")
            ),
            "state_local_paired_stage7_promotion_allowed": (
                state_local_paired_ownership_gate.get("stage7_promotion_allowed")
            ),
            "state_local_paired_stage8_training_allowed": (
                state_local_paired_ownership_gate.get("stage8_training_allowed")
            ),
            "selected_owner_failure_risk_proxy_passive_ready": (
                selected_owner_failure_risk_proxy_gate.get("passive_proxy_review_ready")
            ),
            "selected_owner_failure_risk_runtime_proxy_design_status": (
                selected_owner_failure_risk_proxy_gate.get("runtime_proxy_design_status")
            ),
            "selected_owner_failure_risk_runtime_proxy_dataset_row_count": (
                selected_owner_failure_risk_proxy_gate.get(
                    "runtime_proxy_dataset_row_count"
                )
            ),
            "selected_owner_failure_risk_runtime_proxy_dataset_stage7_row_count": (
                selected_owner_failure_risk_proxy_gate.get(
                    "runtime_proxy_dataset_stage7_row_count"
                )
            ),
            "selected_owner_failure_risk_runtime_proxy_review_status": (
                selected_owner_failure_risk_proxy_gate.get("runtime_proxy_review_status")
            ),
            "selected_owner_failure_risk_runtime_review_packet_v0_translation_blocker": (
                selected_owner_failure_risk_proxy_gate.get(
                    "runtime_review_packet_v0_translation_blocker"
                )
            ),
            "selected_owner_failure_risk_evidence_status": (
                selected_owner_failure_risk_proxy_gate.get("failure_risk_evidence_status")
            ),
            "selected_owner_failure_risk_evidence_row_count": (
                selected_owner_failure_risk_proxy_gate.get(
                    "failure_risk_evidence_row_count"
                )
            ),
            "selected_owner_failure_risk_visible_proxy_precision": (
                selected_owner_failure_risk_proxy_gate.get("visible_proxy_precision")
            ),
            "selected_owner_failure_risk_visible_proxy_recall": (
                selected_owner_failure_risk_proxy_gate.get("visible_proxy_recall")
            ),
            "selected_owner_failure_risk_visible_proxy_probe_v0_status": (
                selected_owner_failure_risk_proxy_gate.get(
                    "visible_proxy_probe_v0_status"
                )
            ),
            "selected_owner_failure_risk_independent_validation_v0_status": (
                selected_owner_failure_risk_proxy_gate.get(
                    "independent_validation_v0_status"
                )
            ),
            "selected_owner_failure_risk_independent_validation_v0_threshold_met": (
                selected_owner_failure_risk_proxy_gate.get(
                    "independent_validation_v0_threshold_met"
                )
            ),
            "selected_owner_failure_risk_blocker_review_v0_status": (
                selected_owner_failure_risk_proxy_gate.get("blocker_review_v0_status")
            ),
            "selected_owner_failure_risk_blocker_review_v0_threshold_met": (
                selected_owner_failure_risk_proxy_gate.get(
                    "blocker_review_v0_threshold_met"
                )
            ),
            "selected_owner_failure_risk_proxy_v1_probe_status": (
                selected_owner_failure_risk_proxy_gate.get("proxy_v1_probe_status")
            ),
            "selected_owner_failure_risk_proxy_v1_independent_passing_proxy_count": (
                selected_owner_failure_risk_proxy_gate.get(
                    "proxy_v1_independent_passing_proxy_count"
                )
            ),
            "selected_owner_failure_risk_independent_label_count": (
                selected_owner_failure_risk_proxy_gate.get("independent_label_count")
            ),
            "selected_owner_failure_risk_independent_label_stage7_training_rows": (
                selected_owner_failure_risk_proxy_gate.get(
                    "independent_label_stage7_training_rows"
                )
            ),
            "selected_owner_failure_risk_independent_validation_status": (
                selected_owner_failure_risk_proxy_gate.get(
                    "independent_validation_status"
                )
            ),
            "selected_owner_failure_risk_independent_validation_threshold_met": (
                selected_owner_failure_risk_proxy_gate.get(
                    "independent_validation_threshold_met"
                )
            ),
            "selected_owner_failure_risk_runtime_proxy_review_packet_v1_status": (
                selected_owner_failure_risk_proxy_gate.get(
                    "runtime_proxy_review_packet_v1_status"
                )
            ),
            "selected_owner_failure_risk_runtime_proxy_review_packet_v1_implementation_allowed": (
                selected_owner_failure_risk_proxy_gate.get(
                    "runtime_proxy_review_packet_v1_implementation_allowed"
                )
            ),
            "selected_owner_failure_risk_runtime_selector_implemented": (
                selected_owner_failure_risk_proxy_gate.get("runtime_selector_implemented")
            ),
            "selected_owner_failure_risk_runtime_dtm_or_tablebase_lookup": (
                selected_owner_failure_risk_proxy_gate.get(
                    "runtime_dtm_or_tablebase_lookup"
                )
            ),
            "selected_owner_failure_risk_runtime_terminals_added": (
                selected_owner_failure_risk_proxy_gate.get("runtime_terminals_added")
            ),
            "selected_owner_failure_risk_stage7_promotion_allowed": (
                selected_owner_failure_risk_proxy_gate.get("stage7_promotion_allowed")
            ),
            "selected_owner_failure_risk_stage8_training_allowed": (
                selected_owner_failure_risk_proxy_gate.get("stage8_training_allowed")
            ),
            "progress_window_reconsideration_passive_ready": (
                progress_window_reconsideration_gate.get("passive_review_ready")
            ),
            "progress_window_reconsideration_runtime_test_status": (
                progress_window_reconsideration_gate.get("runtime_test_review_status")
            ),
            "progress_window_reconsideration_runtime_test_guardrails_allowed_now": (
                progress_window_reconsideration_gate.get(
                    "runtime_test_guardrails_allowed_now"
                )
            ),
            "progress_window_reconsideration_runtime_test_promotion_allowed_now": (
                progress_window_reconsideration_gate.get(
                    "runtime_test_promotion_allowed_now"
                )
            ),
            "progress_window_reconsideration_smoke_status": (
                progress_window_reconsideration_gate.get("smoke_status")
            ),
            "progress_window_reconsideration_default_off_equivalence_passed": (
                progress_window_reconsideration_gate.get(
                    "smoke_default_off_equivalence_passed"
                )
            ),
            "progress_window_reconsideration_improved_target_failure_count": (
                progress_window_reconsideration_gate.get(
                    "smoke_improved_target_failure_count"
                )
            ),
            "progress_window_reconsideration_safe_regression_count": (
                progress_window_reconsideration_gate.get("smoke_safe_regression_count")
            ),
            "progress_window_reconsideration_target_failure_row_count": (
                progress_window_reconsideration_gate.get("smoke_target_failure_row_count")
            ),
            "progress_window_reconsideration_post_activation_status": (
                progress_window_reconsideration_gate.get("post_activation_status")
            ),
            "progress_window_reconsideration_implement_next_fix_now": (
                progress_window_reconsideration_gate.get(
                    "post_activation_implement_next_fix_now"
                )
            ),
            "progress_window_reconsideration_promotion_status": (
                progress_window_reconsideration_gate.get("promotion_status")
            ),
            "progress_window_reconsideration_sandbox_status": (
                progress_window_reconsideration_gate.get("sandbox_status")
            ),
            "progress_window_reconsideration_runtime_defaults_changed": (
                progress_window_reconsideration_gate.get("runtime_defaults_changed")
            ),
            "progress_window_reconsideration_runtime_dtm_or_tablebase_lookup": (
                progress_window_reconsideration_gate.get(
                    "runtime_dtm_or_tablebase_lookup"
                )
            ),
            "progress_window_reconsideration_stage7_promotion_allowed": (
                progress_window_reconsideration_gate.get("stage7_promotion_allowed")
            ),
            "progress_window_reconsideration_stage8_training_allowed": (
                progress_window_reconsideration_gate.get("stage8_training_allowed")
            ),
            "clean_replacement_review_passive_ready": clean_replacement_review_gate.get(
                "passive_review_ready"
            ),
            "clean_replacement_review_packet_status": clean_replacement_review_gate.get(
                "review_packet_status"
            ),
            "clean_replacement_review_packet_implementation_allowed": (
                clean_replacement_review_gate.get("review_packet_implementation_allowed")
            ),
            "clean_replacement_deferred_review_status": clean_replacement_review_gate.get(
                "deferred_review_status"
            ),
            "clean_replacement_deferred_review_explicit_approval_detected": (
                clean_replacement_review_gate.get(
                    "deferred_review_explicit_approval_detected"
                )
            ),
            "clean_replacement_deferred_review_implementation_allowed": (
                clean_replacement_review_gate.get(
                    "deferred_review_implementation_allowed"
                )
            ),
            "clean_replacement_protected_stage_reference_mode": (
                clean_replacement_review_gate.get("protected_stage_reference_mode")
            ),
            "clean_replacement_protected_stage_active_stack_status": (
                clean_replacement_review_gate.get("protected_stage_active_stack_status")
            ),
            "clean_replacement_stage7_promotion_allowed": (
                clean_replacement_review_gate.get("stage7_promotion_allowed")
            ),
            "clean_replacement_stage8_training_allowed": (
                clean_replacement_review_gate.get("stage8_training_allowed")
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
            "sequence_policy_input_probe_status": readiness.get(
                "sequence_policy", {}
            ).get("input_probe_status"),
            "sequence_policy_input_probe_row_count": readiness.get(
                "sequence_policy", {}
            ).get("input_probe_row_count"),
            "sequence_policy_input_probe_benchmark_input_ready": readiness.get(
                "sequence_policy", {}
            ).get("input_probe_benchmark_input_ready"),
            "sequence_policy_input_probe_stage4_topk_signal": readiness.get(
                "sequence_policy", {}
            ).get("input_probe_stage4_topk_signal"),
            "sequence_policy_input_probe_protected_plan_window_failure_sparse": readiness.get(
                "sequence_policy", {}
            ).get("input_probe_protected_plan_window_failure_sparse"),
            "sequence_policy_input_probe_protected_failure_contrast_collection_option_available": readiness.get(
                "sequence_policy", {}
            ).get(
                "input_probe_protected_failure_contrast_collection_option_available"
            ),
            "sequence_policy_input_probe_protected_failure_contrast_collection_command_available": readiness.get(
                "sequence_policy", {}
            ).get(
                "input_probe_protected_failure_contrast_collection_command_available"
            ),
            "sequence_policy_input_probe_selector_training_row_count": readiness.get(
                "sequence_policy", {}
            ).get("input_probe_selector_training_row_count"),
            "sequence_policy_input_probe_runtime_authorization_row_count": readiness.get(
                "sequence_policy", {}
            ).get("input_probe_runtime_authorization_row_count"),
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
            "readiness_control_plane_gate_review_blockers": (
                readiness_control_plane_gate_review_blockers
            ),
            "readiness_explicit_gate_blockers": readiness_explicit_gate_blockers,
            "current_control_plane_gate_status": current_control_plane_gate.get(
                "decision", {}
            ).get("status"),
            "current_control_plane_approval_option_ids": (
                current_gate_approval_option_ids
            ),
            "protected_plan_window_failure_contrast_collection_option_available": (
                current_gate_collection_option_available
            ),
            "protected_plan_window_failure_contrast_collection_command_available": (
                current_gate_collection_command_available
            ),
            "protected_plan_window_failure_contrast_collection_option_id": (
                current_gate_collection_option.get("option_id")
            ),
            "protected_plan_window_failure_contrast_collection_blocked_by_option_id": (
                current_gate_blocking_option.get("option_id")
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
            "protected_plan_window_failure_contrast_runner_manifest_status": failure_contrast_runner.get(
                "summary", {}
            ).get("manifest_status"),
            "protected_plan_window_failure_contrast_runner_manifest_declared_job_count": failure_contrast_runner.get(
                "summary", {}
            ).get("manifest_declared_job_count"),
            "protected_plan_window_failure_contrast_runner_manifest_fingerprint": failure_contrast_runner.get(
                "summary", {}
            ).get("manifest_fingerprint"),
            "protected_plan_window_failure_contrast_runner_collection_run_allowed": failure_contrast_runner.get(
                "decision", {}
            ).get("collection_run_allowed"),
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
                failure_contrast_approval_request_blockers
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
            "protected_missing_provider_labels_status": protected_missing_provider_gate.get(
                "labels_status"
            ),
            "protected_missing_provider_label_count": protected_missing_provider_gate.get(
                "label_count"
            ),
            "protected_missing_provider_stage7_label_count": protected_missing_provider_gate.get(
                "stage7_label_count"
            ),
            "protected_missing_provider_stage7_training_label_count": protected_missing_provider_gate.get(
                "stage7_training_label_count"
            ),
            "protected_missing_provider_merge_status": protected_missing_provider_gate.get(
                "merge_status"
            ),
            "protected_missing_provider_unmatched_label_count": protected_missing_provider_gate.get(
                "unmatched_label_count"
            ),
            "protected_missing_provider_coverage_status": protected_missing_provider_gate.get(
                "coverage_status"
            ),
            "protected_missing_provider_missing_from_frame_count": protected_missing_provider_gate.get(
                "provider_missing_from_frame_count"
            ),
            "protected_missing_provider_mate_label_count": protected_missing_provider_gate.get(
                "missing_provider_mate_label_count"
            ),
            "protected_missing_provider_gap_blocks_selector_training": protected_missing_provider_gate.get(
                "current_gap_blocks_selector_training"
            ),
            "protected_missing_provider_coverage_expansion_plan_status": protected_missing_provider_gate.get(
                "coverage_expansion_plan_status"
            ),
            "protected_missing_provider_coverage_expansion_rows_to_create": protected_missing_provider_gate.get(
                "coverage_expansion_rows_to_create"
            ),
            "protected_missing_provider_coverage_expansion_training_allowed_initially": protected_missing_provider_gate.get(
                "coverage_expansion_training_allowed_initially"
            ),
            "protected_missing_provider_coverage_expansion_requires_followup_review_before_training_use": protected_missing_provider_gate.get(
                "coverage_expansion_requires_followup_review_before_training_use"
            ),
            "protected_missing_provider_coverage_frames_status": protected_missing_provider_gate.get(
                "coverage_frames_status"
            ),
            "protected_missing_provider_coverage_frame_row_count": protected_missing_provider_gate.get(
                "coverage_frame_row_count"
            ),
            "protected_missing_provider_coverage_frame_positive_capacity_count": protected_missing_provider_gate.get(
                "coverage_frame_positive_capacity_count"
            ),
            "protected_missing_provider_coverage_frame_negative_capacity_count": protected_missing_provider_gate.get(
                "coverage_frame_negative_capacity_count"
            ),
            "protected_missing_provider_coverage_frame_stage7_row_count": protected_missing_provider_gate.get(
                "coverage_frame_stage7_row_count"
            ),
            "protected_missing_provider_coverage_frame_training_row_count": protected_missing_provider_gate.get(
                "coverage_frame_training_row_count"
            ),
            "protected_missing_provider_coverage_frame_runtime_proposal_row_count": protected_missing_provider_gate.get(
                "coverage_frame_runtime_proposal_row_count"
            ),
            "protected_missing_provider_training_semantics_review_status": protected_missing_provider_gate.get(
                "training_semantics_review_status"
            ),
            "protected_missing_provider_training_semantics_selector_training_allowed": protected_missing_provider_gate.get(
                "training_semantics_selector_training_allowed"
            ),
            "protected_missing_provider_training_semantics_runtime_work_allowed": protected_missing_provider_gate.get(
                "training_semantics_runtime_work_allowed"
            ),
            "protected_missing_provider_training_semantics_training_row_count": protected_missing_provider_gate.get(
                "training_semantics_training_row_count"
            ),
            "protected_missing_provider_training_semantics_runtime_proposal_row_count": protected_missing_provider_gate.get(
                "training_semantics_runtime_proposal_row_count"
            ),
            "protected_missing_provider_candidate_generator_coverage_status": protected_missing_provider_gate.get(
                "candidate_generator_coverage_status"
            ),
            "protected_missing_provider_candidate_generator_positive_recall_rate": protected_missing_provider_gate.get(
                "candidate_generator_positive_recall_rate"
            ),
            "protected_missing_provider_candidate_generator_missing_positive_capacity_count": protected_missing_provider_gate.get(
                "candidate_generator_missing_positive_capacity_count"
            ),
            "protected_missing_provider_validated_candidate_set_status": protected_missing_provider_gate.get(
                "validated_candidate_set_status"
            ),
            "protected_missing_provider_validated_candidate_set_added_positive_capacity_count": protected_missing_provider_gate.get(
                "validated_candidate_set_added_positive_capacity_count"
            ),
            "protected_missing_provider_validated_candidate_set_added_negative_capacity_count": protected_missing_provider_gate.get(
                "validated_candidate_set_added_negative_capacity_count"
            ),
            "protected_missing_provider_validated_candidate_set_candidate_generator_runtime_allowed": protected_missing_provider_gate.get(
                "validated_candidate_set_candidate_generator_runtime_allowed"
            ),
            "protected_missing_provider_two_stage_review_status": protected_missing_provider_gate.get(
                "two_stage_review_status"
            ),
            "protected_missing_provider_two_stage_review_candidate_generator_runtime_allowed": protected_missing_provider_gate.get(
                "two_stage_review_candidate_generator_runtime_allowed"
            ),
            "protected_missing_provider_two_stage_benchmark_plan_status": protected_missing_provider_gate.get(
                "two_stage_benchmark_plan_status"
            ),
            "protected_missing_provider_two_stage_benchmark_status": protected_missing_provider_gate.get(
                "two_stage_benchmark_status"
            ),
            "protected_missing_provider_two_stage_benchmark_current_positive_recall_rate": protected_missing_provider_gate.get(
                "two_stage_benchmark_current_positive_recall_rate"
            ),
            "protected_missing_provider_two_stage_benchmark_expanded_positive_recall_rate": protected_missing_provider_gate.get(
                "two_stage_benchmark_expanded_positive_recall_rate"
            ),
            "protected_missing_provider_two_stage_benchmark_expanded_negative_inclusion_rate": protected_missing_provider_gate.get(
                "two_stage_benchmark_expanded_negative_inclusion_rate"
            ),
            "protected_missing_provider_two_stage_benchmark_selector_ready": protected_missing_provider_gate.get(
                "two_stage_benchmark_selector_ready"
            ),
            "protected_missing_provider_two_stage_benchmark_best_negative_suppression": protected_missing_provider_gate.get(
                "two_stage_benchmark_best_negative_suppression"
            ),
            "protected_missing_provider_two_stage_benchmark_stage7_training_leakage": protected_missing_provider_gate.get(
                "two_stage_benchmark_stage7_training_leakage"
            ),
            "protected_missing_provider_two_stage_benchmark_candidate_generator_runtime_allowed": protected_missing_provider_gate.get(
                "two_stage_benchmark_candidate_generator_runtime_allowed"
            ),
            "protected_missing_provider_two_stage_benchmark_selector_training_allowed": protected_missing_provider_gate.get(
                "two_stage_benchmark_selector_training_allowed"
            ),
            "protected_missing_provider_runtime_work_allowed": protected_missing_provider_gate.get(
                "runtime_work_allowed"
            ),
            "strategy_sequence_candidate_source_candidate_proposal_coverage_status": strategy_sequence_candidate_source_gate.get(
                "candidate_proposal_coverage_status"
            ),
            "strategy_sequence_candidate_source_candidate_proposal_coverage_positive_capacity_recall": strategy_sequence_candidate_source_gate.get(
                "candidate_proposal_coverage_positive_capacity_recall"
            ),
            "strategy_sequence_candidate_source_candidate_proposal_coverage_missing_positive_capacity_count": strategy_sequence_candidate_source_gate.get(
                "candidate_proposal_coverage_missing_positive_capacity_count"
            ),
            "strategy_sequence_candidate_source_candidate_proposal_coverage_stage7_row_count": strategy_sequence_candidate_source_gate.get(
                "candidate_proposal_coverage_stage7_row_count"
            ),
            "strategy_sequence_candidate_source_candidate_proposal_coverage_selector_training_allowed": strategy_sequence_candidate_source_gate.get(
                "candidate_proposal_coverage_selector_training_allowed"
            ),
            "strategy_sequence_candidate_source_candidate_generation_strategy_review_status": strategy_sequence_candidate_source_gate.get(
                "candidate_generation_strategy_review_status"
            ),
            "strategy_sequence_candidate_source_candidate_generation_strategy_review_runtime_sandbox_allowed": strategy_sequence_candidate_source_gate.get(
                "candidate_generation_strategy_review_runtime_sandbox_allowed"
            ),
            "strategy_sequence_candidate_source_candidate_generation_strategy_review_recommended_next_step": strategy_sequence_candidate_source_gate.get(
                "candidate_generation_strategy_review_recommended_next_step"
            ),
            "strategy_sequence_candidate_source_schema_status": strategy_sequence_candidate_source_gate.get(
                "schema_status"
            ),
            "strategy_sequence_candidate_source_schema_runtime_sandbox_allowed": strategy_sequence_candidate_source_gate.get(
                "schema_runtime_sandbox_allowed"
            ),
            "strategy_sequence_candidate_source_frames_status": strategy_sequence_candidate_source_gate.get(
                "frames_status"
            ),
            "strategy_sequence_candidate_source_frames_frame_count": strategy_sequence_candidate_source_gate.get(
                "frames_frame_count"
            ),
            "strategy_sequence_candidate_source_frames_stage7_challenge_row_count": strategy_sequence_candidate_source_gate.get(
                "frames_stage7_challenge_row_count"
            ),
            "strategy_sequence_candidate_source_frames_stage7_readiness_training_row_count": strategy_sequence_candidate_source_gate.get(
                "frames_stage7_readiness_training_row_count"
            ),
            "strategy_sequence_candidate_source_quality_status": strategy_sequence_candidate_source_gate.get(
                "quality_status"
            ),
            "strategy_sequence_candidate_source_quality_capacity_not_selector_label": strategy_sequence_candidate_source_gate.get(
                "quality_capacity_not_selector_label"
            ),
            "strategy_sequence_candidate_source_quality_sequence_candidate_mate_count": strategy_sequence_candidate_source_gate.get(
                "quality_sequence_candidate_mate_count"
            ),
            "strategy_sequence_candidate_source_benchmark_status": strategy_sequence_candidate_source_gate.get(
                "source_benchmark_status"
            ),
            "strategy_sequence_candidate_source_benchmark_protected_positive_capacity_ratio": strategy_sequence_candidate_source_gate.get(
                "source_benchmark_protected_positive_capacity_ratio"
            ),
            "strategy_sequence_candidate_source_benchmark_protected_negative_capacity_ratio": strategy_sequence_candidate_source_gate.get(
                "source_benchmark_protected_negative_capacity_ratio"
            ),
            "strategy_sequence_candidate_source_benchmark_progress_window_sequence_candidate_mate_count": strategy_sequence_candidate_source_gate.get(
                "source_benchmark_progress_window_sequence_candidate_mate_count"
            ),
            "strategy_sequence_candidate_source_control_plane_status": strategy_sequence_candidate_source_gate.get(
                "control_plane_status"
            ),
            "strategy_sequence_candidate_source_control_plane_runtime_sandbox_allowed": strategy_sequence_candidate_source_gate.get(
                "control_plane_runtime_sandbox_allowed"
            ),
            "strategy_sequence_candidate_source_sandbox_review_status": strategy_sequence_candidate_source_gate.get(
                "sandbox_review_status"
            ),
            "strategy_sequence_candidate_source_sandbox_review_implementation_authorized": strategy_sequence_candidate_source_gate.get(
                "sandbox_review_implementation_authorized"
            ),
            "strategy_sequence_candidate_source_observation_sandbox_status": strategy_sequence_candidate_source_gate.get(
                "observation_sandbox_status"
            ),
            "strategy_sequence_candidate_source_observation_sandbox_generated_candidate_count": strategy_sequence_candidate_source_gate.get(
                "observation_sandbox_generated_candidate_count"
            ),
            "strategy_sequence_candidate_source_observation_sandbox_selected_move_or_provider_changed": strategy_sequence_candidate_source_gate.get(
                "observation_sandbox_selected_move_or_provider_changed"
            ),
            "strategy_sequence_candidate_source_observation_coverage_status": strategy_sequence_candidate_source_gate.get(
                "observation_coverage_status"
            ),
            "strategy_sequence_candidate_source_observation_coverage_sampled_frame_count": strategy_sequence_candidate_source_gate.get(
                "observation_coverage_sampled_frame_count"
            ),
            "strategy_sequence_candidate_source_observation_coverage_invariant_failure_count": strategy_sequence_candidate_source_gate.get(
                "observation_coverage_invariant_failure_count"
            ),
            "strategy_sequence_candidate_source_observation_broadened_status": strategy_sequence_candidate_source_gate.get(
                "observation_broadened_status"
            ),
            "strategy_sequence_candidate_source_observation_broadened_case_count": strategy_sequence_candidate_source_gate.get(
                "observation_broadened_case_count"
            ),
            "strategy_sequence_candidate_source_observation_broadened_emitted_frame_count": strategy_sequence_candidate_source_gate.get(
                "observation_broadened_emitted_frame_count"
            ),
            "strategy_sequence_candidate_source_observation_broadened_selected_move_or_provider_delta_count": strategy_sequence_candidate_source_gate.get(
                "observation_broadened_selected_move_or_provider_delta_count"
            ),
            "strategy_sequence_candidate_source_observation_gap_review_status": strategy_sequence_candidate_source_gate.get(
                "observation_gap_review_status"
            ),
            "strategy_sequence_candidate_source_observation_gap_review_unknown_capacity_ratio": strategy_sequence_candidate_source_gate.get(
                "observation_gap_review_unknown_capacity_ratio"
            ),
            "strategy_sequence_candidate_source_observation_gap_review_missing_expected_sources": strategy_sequence_candidate_source_gate.get(
                "observation_gap_review_missing_expected_sources"
            ),
            "strategy_sequence_candidate_source_capacity_annotation_v1_status": strategy_sequence_candidate_source_gate.get(
                "capacity_annotation_v1_status"
            ),
            "strategy_sequence_candidate_source_capacity_annotation_v1_protected_annotation_recall": strategy_sequence_candidate_source_gate.get(
                "capacity_annotation_v1_protected_annotation_recall"
            ),
            "strategy_sequence_candidate_source_capacity_label_manifest_status": strategy_sequence_candidate_source_gate.get(
                "capacity_label_manifest_status"
            ),
            "strategy_sequence_candidate_source_capacity_label_manifest_labels_run_by_this_artifact": strategy_sequence_candidate_source_gate.get(
                "capacity_label_manifest_labels_run_by_this_artifact"
            ),
            "strategy_sequence_candidate_source_capacity_label_manifest_job_count": strategy_sequence_candidate_source_gate.get(
                "capacity_label_manifest_job_count"
            ),
            "strategy_sequence_candidate_source_capacity_label_manifest_stage7_job_count": strategy_sequence_candidate_source_gate.get(
                "capacity_label_manifest_stage7_job_count"
            ),
            "strategy_sequence_candidate_source_capacity_labels_status": strategy_sequence_candidate_source_gate.get(
                "capacity_labels_status"
            ),
            "strategy_sequence_candidate_source_capacity_labels_label_count": strategy_sequence_candidate_source_gate.get(
                "capacity_labels_label_count"
            ),
            "strategy_sequence_candidate_source_capacity_labels_stage7_training_label_count": strategy_sequence_candidate_source_gate.get(
                "capacity_labels_stage7_training_label_count"
            ),
            "strategy_sequence_candidate_source_capacity_annotation_v2_status": strategy_sequence_candidate_source_gate.get(
                "capacity_annotation_v2_status"
            ),
            "strategy_sequence_candidate_source_capacity_annotation_v2_annotated_candidate_move_count": strategy_sequence_candidate_source_gate.get(
                "capacity_annotation_v2_annotated_candidate_move_count"
            ),
            "strategy_sequence_candidate_source_capacity_annotation_v2_protected_annotation_recall": strategy_sequence_candidate_source_gate.get(
                "capacity_annotation_v2_protected_annotation_recall"
            ),
            "strategy_sequence_candidate_source_capacity_annotation_v2_stage7_readiness_training_row_count": strategy_sequence_candidate_source_gate.get(
                "capacity_annotation_v2_stage7_readiness_training_row_count"
            ),
            "strategy_sequence_candidate_source_label_blocker_status": strategy_sequence_candidate_source_gate.get(
                "label_blocker_status"
            ),
            "strategy_sequence_candidate_source_label_blocker_more_blind_label_farming_not_recommended": strategy_sequence_candidate_source_gate.get(
                "label_blocker_more_blind_label_farming_not_recommended"
            ),
            "strategy_sequence_candidate_source_label_blocker_protected_annotation_recall": strategy_sequence_candidate_source_gate.get(
                "label_blocker_protected_annotation_recall"
            ),
            "strategy_sequence_candidate_source_quality_prioritization_review_status": strategy_sequence_candidate_source_gate.get(
                "quality_prioritization_review_status"
            ),
            "strategy_sequence_candidate_source_quality_dataset_status": strategy_sequence_candidate_source_gate.get(
                "quality_dataset_status"
            ),
            "strategy_sequence_candidate_source_quality_dataset_row_count": strategy_sequence_candidate_source_gate.get(
                "quality_dataset_row_count"
            ),
            "strategy_sequence_candidate_source_quality_dataset_quality_probe_row_count": strategy_sequence_candidate_source_gate.get(
                "quality_dataset_quality_probe_row_count"
            ),
            "strategy_sequence_candidate_source_quality_dataset_stage7_readiness_training_row_count": strategy_sequence_candidate_source_gate.get(
                "quality_dataset_stage7_readiness_training_row_count"
            ),
            "strategy_sequence_candidate_source_quality_probe_status": strategy_sequence_candidate_source_gate.get(
                "quality_probe_status"
            ),
            "strategy_sequence_candidate_source_quality_probe_best_probe": strategy_sequence_candidate_source_gate.get(
                "quality_probe_best_probe"
            ),
            "strategy_sequence_candidate_source_quality_probe_best_positive_recall": strategy_sequence_candidate_source_gate.get(
                "quality_probe_best_positive_recall"
            ),
            "strategy_sequence_candidate_source_quality_probe_best_negative_suppression": strategy_sequence_candidate_source_gate.get(
                "quality_probe_best_negative_suppression"
            ),
            "strategy_sequence_candidate_source_quality_probe_ready_for_selector_review": strategy_sequence_candidate_source_gate.get(
                "quality_probe_ready_for_selector_review"
            ),
            "strategy_sequence_candidate_source_quality_decision_status": strategy_sequence_candidate_source_gate.get(
                "quality_decision_status"
            ),
            "strategy_sequence_candidate_source_quality_decision_more_blind_label_farming_allowed": strategy_sequence_candidate_source_gate.get(
                "quality_decision_more_blind_label_farming_allowed"
            ),
            "strategy_sequence_candidate_source_quality_decision_recommended_next_step": strategy_sequence_candidate_source_gate.get(
                "quality_decision_recommended_next_step"
            ),
            "strategy_sequence_candidate_source_design_status": strategy_sequence_candidate_source_gate.get(
                "source_design_status"
            ),
            "strategy_sequence_candidate_source_design_implementation_allowed": strategy_sequence_candidate_source_gate.get(
                "source_design_implementation_allowed"
            ),
            "strategy_sequence_candidate_source_plan_capsule_status": strategy_sequence_candidate_source_gate.get(
                "plan_capsule_source_status"
            ),
            "strategy_sequence_candidate_source_broader_strategy_status": strategy_sequence_candidate_source_gate.get(
                "broader_strategy_source_status"
            ),
            "strategy_sequence_candidate_source_review_status": strategy_sequence_candidate_source_gate.get(
                "source_review_status"
            ),
            "strategy_sequence_candidate_source_review_implementation_allowed": strategy_sequence_candidate_source_gate.get(
                "source_review_implementation_allowed"
            ),
            "strategy_sequence_candidate_source_protected_monitor_expansion_status": strategy_sequence_candidate_source_gate.get(
                "protected_monitor_expansion_status"
            ),
            "strategy_sequence_candidate_source_protected_monitor_expansion_frame_count": strategy_sequence_candidate_source_gate.get(
                "protected_monitor_expansion_frame_count"
            ),
            "strategy_sequence_candidate_source_protected_monitor_expansion_stage7_challenge_row_count": strategy_sequence_candidate_source_gate.get(
                "protected_monitor_expansion_stage7_challenge_row_count"
            ),
            "strategy_sequence_candidate_source_protected_monitor_quality_status": strategy_sequence_candidate_source_gate.get(
                "protected_monitor_quality_status"
            ),
            "strategy_sequence_candidate_source_protected_monitor_quality_strong_failure_family_count": strategy_sequence_candidate_source_gate.get(
                "protected_monitor_quality_strong_failure_family_count"
            ),
            "strategy_sequence_candidate_source_repair_monitor_review_status": strategy_sequence_candidate_source_gate.get(
                "repair_monitor_review_status"
            ),
            "strategy_sequence_candidate_source_repair_monitor_review_implementation_authorized": strategy_sequence_candidate_source_gate.get(
                "repair_monitor_review_implementation_authorized"
            ),
            "strategy_sequence_candidate_source_runtime_work_allowed": strategy_sequence_candidate_source_gate.get(
                "runtime_work_allowed"
            ),
            "strategy_sequence_candidate_source_selector_training_allowed": strategy_sequence_candidate_source_gate.get(
                "selector_training_allowed"
            ),
            "strategy_sequence_candidate_source_stage7_promotion_allowed": strategy_sequence_candidate_source_gate.get(
                "stage7_promotion_allowed"
            ),
            "strategy_sequence_candidate_source_stage8_training_allowed": strategy_sequence_candidate_source_gate.get(
                "stage8_training_allowed"
            ),
            "repair_monitor_trace_feature_smoke_status": repair_monitor_trace_feature_gate.get(
                "smoke_status"
            ),
            "repair_monitor_trace_feature_smoke_case_count": repair_monitor_trace_feature_gate.get(
                "smoke_case_count"
            ),
            "repair_monitor_trace_feature_smoke_repair_monitor_frame_count": repair_monitor_trace_feature_gate.get(
                "smoke_repair_monitor_frame_count"
            ),
            "repair_monitor_trace_feature_smoke_selected_move_provider_delta_count": repair_monitor_trace_feature_gate.get(
                "smoke_selected_move_provider_delta_count"
            ),
            "repair_monitor_trace_feature_smoke_stage7_case_count": repair_monitor_trace_feature_gate.get(
                "smoke_stage7_case_count"
            ),
            "repair_monitor_trace_feature_broadened_status": repair_monitor_trace_feature_gate.get(
                "broadened_status"
            ),
            "repair_monitor_trace_feature_broadened_case_count": repair_monitor_trace_feature_gate.get(
                "broadened_case_count"
            ),
            "repair_monitor_trace_feature_broadened_stage7_case_count": repair_monitor_trace_feature_gate.get(
                "broadened_stage7_case_count"
            ),
            "repair_monitor_trace_feature_quality_status": repair_monitor_trace_feature_gate.get(
                "quality_status"
            ),
            "repair_monitor_trace_feature_quality_source_stable": repair_monitor_trace_feature_gate.get(
                "quality_source_stable"
            ),
            "repair_monitor_trace_feature_trace_features_status": repair_monitor_trace_feature_gate.get(
                "trace_features_status"
            ),
            "repair_monitor_trace_feature_trace_frame_count": repair_monitor_trace_feature_gate.get(
                "trace_features_trace_frame_count"
            ),
            "repair_monitor_trace_feature_stage7_trace_frame_count": repair_monitor_trace_feature_gate.get(
                "trace_features_stage7_trace_frame_count"
            ),
            "repair_monitor_trace_feature_selector_training_row_count": repair_monitor_trace_feature_gate.get(
                "trace_features_selector_training_row_count"
            ),
            "repair_monitor_trace_feature_integration_review_status": repair_monitor_trace_feature_gate.get(
                "integration_review_status"
            ),
            "repair_monitor_trace_feature_integration_safe": repair_monitor_trace_feature_gate.get(
                "integration_review_trace_integration_safe"
            ),
            "repair_monitor_trace_feature_dataset_design_status": repair_monitor_trace_feature_gate.get(
                "dataset_design_status"
            ),
            "repair_monitor_trace_feature_dataset_design_implementation_allowed": repair_monitor_trace_feature_gate.get(
                "dataset_design_implementation_allowed"
            ),
            "repair_monitor_trace_feature_dataset_v2_status": repair_monitor_trace_feature_gate.get(
                "dataset_v2_status"
            ),
            "repair_monitor_trace_feature_dataset_v2_row_count": repair_monitor_trace_feature_gate.get(
                "dataset_v2_row_count"
            ),
            "repair_monitor_trace_feature_dataset_v2_runtime_trace_feature_row_count": repair_monitor_trace_feature_gate.get(
                "dataset_v2_runtime_trace_feature_row_count"
            ),
            "repair_monitor_trace_feature_dataset_v2_selector_training_row_count": repair_monitor_trace_feature_gate.get(
                "dataset_v2_selector_training_row_count"
            ),
            "repair_monitor_trace_feature_dataset_v2_stage7_readiness_training_row_count": repair_monitor_trace_feature_gate.get(
                "dataset_v2_stage7_readiness_training_row_count"
            ),
            "repair_monitor_trace_feature_dataset_v2_quality_status": repair_monitor_trace_feature_gate.get(
                "dataset_v2_quality_status"
            ),
            "repair_monitor_trace_feature_dataset_v2_quality_runtime_flags_false": repair_monitor_trace_feature_gate.get(
                "dataset_v2_quality_runtime_flags_false"
            ),
            "repair_monitor_trace_feature_dataset_v2_quality_selector_rows_absent": repair_monitor_trace_feature_gate.get(
                "dataset_v2_quality_selector_rows_absent"
            ),
            "repair_monitor_trace_feature_refresh_probe_status": repair_monitor_trace_feature_gate.get(
                "refresh_probe_status"
            ),
            "repair_monitor_trace_feature_refresh_probe_positive_recall": repair_monitor_trace_feature_gate.get(
                "refresh_probe_positive_recall"
            ),
            "repair_monitor_trace_feature_refresh_probe_negative_suppression": repair_monitor_trace_feature_gate.get(
                "refresh_probe_negative_suppression"
            ),
            "repair_monitor_trace_feature_capacity_manifest_status": repair_monitor_trace_feature_gate.get(
                "capacity_manifest_status"
            ),
            "repair_monitor_trace_feature_capacity_manifest_labels_run_by_this_artifact": repair_monitor_trace_feature_gate.get(
                "capacity_manifest_labels_run_by_this_artifact"
            ),
            "repair_monitor_trace_feature_capacity_manifest_stage7_job_count": repair_monitor_trace_feature_gate.get(
                "capacity_manifest_stage7_job_count"
            ),
            "repair_monitor_trace_feature_capacity_labels_status": repair_monitor_trace_feature_gate.get(
                "capacity_labels_status"
            ),
            "repair_monitor_trace_feature_capacity_labels_stage7_label_count": repair_monitor_trace_feature_gate.get(
                "capacity_labels_stage7_label_count"
            ),
            "repair_monitor_trace_feature_capacity_labels_stage7_training_label_count": repair_monitor_trace_feature_gate.get(
                "capacity_labels_stage7_training_label_count"
            ),
            "repair_monitor_trace_feature_dataset_v2_capacity_merged_status": repair_monitor_trace_feature_gate.get(
                "dataset_v2_capacity_merged_status"
            ),
            "repair_monitor_trace_feature_dataset_v2_capacity_merged_row_count": repair_monitor_trace_feature_gate.get(
                "dataset_v2_capacity_merged_row_count"
            ),
            "repair_monitor_trace_feature_dataset_v2_capacity_merged_selector_training_row_count": repair_monitor_trace_feature_gate.get(
                "dataset_v2_capacity_merged_selector_training_row_count"
            ),
            "repair_monitor_trace_feature_dataset_v2_capacity_merged_stage7_readiness_training_row_count": repair_monitor_trace_feature_gate.get(
                "dataset_v2_capacity_merged_stage7_readiness_training_row_count"
            ),
            "repair_monitor_trace_feature_refresh_after_labels_status": repair_monitor_trace_feature_gate.get(
                "refresh_after_labels_status"
            ),
            "repair_monitor_trace_feature_refresh_after_labels_positive_recall": repair_monitor_trace_feature_gate.get(
                "refresh_after_labels_positive_recall"
            ),
            "repair_monitor_trace_feature_refresh_after_labels_negative_suppression": repair_monitor_trace_feature_gate.get(
                "refresh_after_labels_negative_suppression"
            ),
            "repair_monitor_trace_feature_runtime_work_allowed": repair_monitor_trace_feature_gate.get(
                "runtime_work_allowed"
            ),
            "repair_monitor_trace_feature_selector_training_allowed": repair_monitor_trace_feature_gate.get(
                "selector_training_allowed"
            ),
            "repair_monitor_trace_feature_stage7_promotion_allowed": repair_monitor_trace_feature_gate.get(
                "stage7_promotion_allowed"
            ),
            "repair_monitor_trace_feature_stage8_training_allowed": repair_monitor_trace_feature_gate.get(
                "stage8_training_allowed"
            ),
            "stage5_6_candidate_generation_refresh_review_status": stage5_6_candidate_generation_refresh_gate.get(
                "review_status"
            ),
            "stage5_6_candidate_generation_refresh_review_runtime_review_ready": stage5_6_candidate_generation_refresh_gate.get(
                "review_runtime_review_ready"
            ),
            "stage5_6_candidate_generation_refresh_review_implementation_authorized": stage5_6_candidate_generation_refresh_gate.get(
                "review_implementation_authorized"
            ),
            "stage5_6_candidate_generation_refresh_review_runtime_candidate_generator_refresh_allowed": stage5_6_candidate_generation_refresh_gate.get(
                "review_runtime_candidate_generator_refresh_allowed"
            ),
            "stage5_6_candidate_generation_refresh_smoke_status": stage5_6_candidate_generation_refresh_gate.get(
                "smoke_status"
            ),
            "stage5_6_candidate_generation_refresh_smoke_case_count": stage5_6_candidate_generation_refresh_gate.get(
                "smoke_case_count"
            ),
            "stage5_6_candidate_generation_refresh_smoke_refresh_frame_count": stage5_6_candidate_generation_refresh_gate.get(
                "smoke_refresh_frame_count"
            ),
            "stage5_6_candidate_generation_refresh_smoke_selected_move_provider_delta_count": stage5_6_candidate_generation_refresh_gate.get(
                "smoke_selected_move_provider_delta_count"
            ),
            "stage5_6_candidate_generation_refresh_smoke_invariant_failure_count": stage5_6_candidate_generation_refresh_gate.get(
                "smoke_invariant_failure_count"
            ),
            "stage5_6_candidate_generation_refresh_smoke_stage7_case_count": stage5_6_candidate_generation_refresh_gate.get(
                "smoke_stage7_case_count"
            ),
            "stage5_6_candidate_generation_refresh_coverage_status": stage5_6_candidate_generation_refresh_gate.get(
                "coverage_status"
            ),
            "stage5_6_candidate_generation_refresh_coverage_refresh_frame_count": stage5_6_candidate_generation_refresh_gate.get(
                "coverage_refresh_frame_count"
            ),
            "stage5_6_candidate_generation_refresh_coverage_stage7_case_count": stage5_6_candidate_generation_refresh_gate.get(
                "coverage_stage7_case_count"
            ),
            "stage5_6_candidate_generation_refresh_broadened_status": stage5_6_candidate_generation_refresh_gate.get(
                "broadened_status"
            ),
            "stage5_6_candidate_generation_refresh_broadened_case_count": stage5_6_candidate_generation_refresh_gate.get(
                "broadened_case_count"
            ),
            "stage5_6_candidate_generation_refresh_broadened_refresh_frame_count": stage5_6_candidate_generation_refresh_gate.get(
                "broadened_refresh_frame_count"
            ),
            "stage5_6_candidate_generation_refresh_broadened_selected_move_provider_delta_count": stage5_6_candidate_generation_refresh_gate.get(
                "broadened_selected_move_provider_delta_count"
            ),
            "stage5_6_candidate_generation_refresh_broadened_stage7_case_count": stage5_6_candidate_generation_refresh_gate.get(
                "broadened_stage7_case_count"
            ),
            "stage5_6_candidate_generation_refresh_quality_status": stage5_6_candidate_generation_refresh_gate.get(
                "quality_status"
            ),
            "stage5_6_candidate_generation_refresh_quality_trace_usable_for_candidate_generation_context": stage5_6_candidate_generation_refresh_gate.get(
                "quality_trace_usable_for_candidate_generation_context"
            ),
            "stage5_6_candidate_generation_refresh_quality_stage7_case_count": stage5_6_candidate_generation_refresh_gate.get(
                "quality_stage7_case_count"
            ),
            "stage5_6_candidate_generation_refresh_trace_features_status": stage5_6_candidate_generation_refresh_gate.get(
                "trace_features_status"
            ),
            "stage5_6_candidate_generation_refresh_trace_features_trace_frame_count": stage5_6_candidate_generation_refresh_gate.get(
                "trace_features_trace_frame_count"
            ),
            "stage5_6_candidate_generation_refresh_trace_features_stage7_trace_frame_count": stage5_6_candidate_generation_refresh_gate.get(
                "trace_features_stage7_trace_frame_count"
            ),
            "stage5_6_candidate_generation_refresh_trace_features_selector_training_row_count": stage5_6_candidate_generation_refresh_gate.get(
                "trace_features_selector_training_row_count"
            ),
            "stage5_6_candidate_generation_refresh_trace_features_candidate_generation_training_row_count": stage5_6_candidate_generation_refresh_gate.get(
                "trace_features_candidate_generation_training_row_count"
            ),
            "stage5_6_candidate_generation_refresh_dataset_design_v3_status": stage5_6_candidate_generation_refresh_gate.get(
                "dataset_design_v3_status"
            ),
            "stage5_6_candidate_generation_refresh_dataset_design_v3_implementation_allowed": stage5_6_candidate_generation_refresh_gate.get(
                "dataset_design_v3_implementation_allowed"
            ),
            "stage5_6_candidate_generation_refresh_runtime_work_allowed": stage5_6_candidate_generation_refresh_gate.get(
                "runtime_work_allowed"
            ),
            "stage5_6_candidate_generation_refresh_selector_training_allowed": stage5_6_candidate_generation_refresh_gate.get(
                "selector_training_allowed"
            ),
            "stage5_6_candidate_generation_refresh_stage7_promotion_allowed": stage5_6_candidate_generation_refresh_gate.get(
                "stage7_promotion_allowed"
            ),
            "stage5_6_candidate_generation_refresh_stage8_training_allowed": stage5_6_candidate_generation_refresh_gate.get(
                "stage8_training_allowed"
            ),
            "cross_stage_candidate_generation_scope_capacity_review_status": cross_stage_candidate_generation_scope_gate.get(
                "capacity_review_status"
            ),
            "cross_stage_candidate_generation_scope_cross_stage_label_probe_status": cross_stage_candidate_generation_scope_gate.get(
                "cross_stage_label_probe_status"
            ),
            "cross_stage_candidate_generation_scope_cross_stage_label_probe_positive_recall": cross_stage_candidate_generation_scope_gate.get(
                "cross_stage_label_probe_positive_recall"
            ),
            "cross_stage_candidate_generation_scope_cross_stage_label_probe_negative_suppression": cross_stage_candidate_generation_scope_gate.get(
                "cross_stage_label_probe_negative_suppression"
            ),
            "cross_stage_candidate_generation_scope_cross_stage_label_probe_guardrails_allowed": cross_stage_candidate_generation_scope_gate.get(
                "cross_stage_label_probe_guardrails_allowed"
            ),
            "cross_stage_candidate_generation_scope_cross_stage_label_probe_selector_allowed": cross_stage_candidate_generation_scope_gate.get(
                "cross_stage_label_probe_selector_allowed"
            ),
            "cross_stage_candidate_generation_scope_cross_stage_label_probe_promotion_allowed": cross_stage_candidate_generation_scope_gate.get(
                "cross_stage_label_probe_promotion_allowed"
            ),
            "cross_stage_candidate_generation_scope_capacity_review_capacity_row_count": cross_stage_candidate_generation_scope_gate.get(
                "capacity_review_capacity_row_count"
            ),
            "cross_stage_candidate_generation_scope_capacity_manifest_status": cross_stage_candidate_generation_scope_gate.get(
                "capacity_manifest_status"
            ),
            "cross_stage_candidate_generation_scope_capacity_manifest_labels_run_by_this_artifact": cross_stage_candidate_generation_scope_gate.get(
                "capacity_manifest_labels_run_by_this_artifact"
            ),
            "cross_stage_candidate_generation_scope_capacity_manifest_stage7_job_count": cross_stage_candidate_generation_scope_gate.get(
                "capacity_manifest_stage7_job_count"
            ),
            "cross_stage_candidate_generation_scope_capacity_labels_status": cross_stage_candidate_generation_scope_gate.get(
                "capacity_labels_status"
            ),
            "cross_stage_candidate_generation_scope_capacity_labels_label_count": cross_stage_candidate_generation_scope_gate.get(
                "capacity_labels_label_count"
            ),
            "cross_stage_candidate_generation_scope_capacity_labels_stage7_label_count": cross_stage_candidate_generation_scope_gate.get(
                "capacity_labels_stage7_label_count"
            ),
            "cross_stage_candidate_generation_scope_dataset_cross_stage_merged_status": cross_stage_candidate_generation_scope_gate.get(
                "dataset_cross_stage_merged_status"
            ),
            "cross_stage_candidate_generation_scope_dataset_cross_stage_merged_row_count": cross_stage_candidate_generation_scope_gate.get(
                "dataset_cross_stage_merged_row_count"
            ),
            "cross_stage_candidate_generation_scope_dataset_cross_stage_merged_selector_training_row_count": cross_stage_candidate_generation_scope_gate.get(
                "dataset_cross_stage_merged_selector_training_row_count"
            ),
            "cross_stage_candidate_generation_scope_dataset_cross_stage_merged_stage7_readiness_training_row_count": cross_stage_candidate_generation_scope_gate.get(
                "dataset_cross_stage_merged_stage7_readiness_training_row_count"
            ),
            "cross_stage_candidate_generation_scope_label_outcome_review_status": cross_stage_candidate_generation_scope_gate.get(
                "label_outcome_review_status"
            ),
            "cross_stage_candidate_generation_scope_scope_review_status": cross_stage_candidate_generation_scope_gate.get(
                "scope_review_status"
            ),
            "cross_stage_candidate_generation_scope_stage_conditioned_benchmark_status": cross_stage_candidate_generation_scope_gate.get(
                "stage_conditioned_benchmark_status"
            ),
            "cross_stage_candidate_generation_scope_stage_conditioned_benchmark_positive_recall": cross_stage_candidate_generation_scope_gate.get(
                "stage_conditioned_benchmark_positive_recall"
            ),
            "cross_stage_candidate_generation_scope_stage_conditioned_benchmark_negative_suppression": cross_stage_candidate_generation_scope_gate.get(
                "stage_conditioned_benchmark_negative_suppression"
            ),
            "cross_stage_candidate_generation_scope_stage_conditioned_benchmark_stage4_positive_recall": cross_stage_candidate_generation_scope_gate.get(
                "stage_conditioned_benchmark_stage4_positive_recall"
            ),
            "cross_stage_candidate_generation_scope_stage_conditioned_benchmark_stage5_6_positive_recall": cross_stage_candidate_generation_scope_gate.get(
                "stage_conditioned_benchmark_stage5_6_positive_recall"
            ),
            "cross_stage_candidate_generation_scope_runtime_work_allowed": cross_stage_candidate_generation_scope_gate.get(
                "runtime_work_allowed"
            ),
            "cross_stage_candidate_generation_scope_selector_training_allowed": cross_stage_candidate_generation_scope_gate.get(
                "selector_training_allowed"
            ),
            "cross_stage_candidate_generation_scope_stage7_promotion_allowed": cross_stage_candidate_generation_scope_gate.get(
                "stage7_promotion_allowed"
            ),
            "cross_stage_candidate_generation_scope_stage8_training_allowed": cross_stage_candidate_generation_scope_gate.get(
                "stage8_training_allowed"
            ),
            "selector_objective_lineage_ownership_recovery_status": selector_objective_lineage_gate.get(
                "ownership_recovery_status"
            ),
            "selector_objective_lineage_ownership_recovery_joined_state_count": selector_objective_lineage_gate.get(
                "ownership_recovery_joined_state_count"
            ),
            "selector_objective_lineage_ownership_recovery_selected_failure_with_visible_positive_count": selector_objective_lineage_gate.get(
                "ownership_recovery_selected_failure_with_visible_positive_count"
            ),
            "selector_objective_lineage_seed_manifest_v0_status": selector_objective_lineage_gate.get(
                "seed_manifest_v0_status"
            ),
            "selector_objective_lineage_seed_manifest_v0_seed_row_count": selector_objective_lineage_gate.get(
                "seed_manifest_v0_seed_row_count"
            ),
            "selector_objective_lineage_seed_probe_v0_status": selector_objective_lineage_gate.get(
                "seed_probe_v0_status"
            ),
            "selector_objective_lineage_seed_probe_v0_runtime_feature_eligible_prediction_count": selector_objective_lineage_gate.get(
                "seed_probe_v0_runtime_feature_eligible_prediction_count"
            ),
            "selector_objective_lineage_collection_manifest_status": selector_objective_lineage_gate.get(
                "collection_manifest_status"
            ),
            "selector_objective_lineage_collection_manifest_runtime_collection_allowed_row_count": selector_objective_lineage_gate.get(
                "collection_manifest_runtime_collection_allowed_row_count"
            ),
            "selector_objective_lineage_collection_review_status": selector_objective_lineage_gate.get(
                "collection_review_status"
            ),
            "selector_objective_lineage_collection_review_implementation_authorized": selector_objective_lineage_gate.get(
                "collection_review_implementation_authorized"
            ),
            "selector_objective_lineage_joined_collection_status": selector_objective_lineage_gate.get(
                "joined_collection_status"
            ),
            "selector_objective_lineage_joined_collection_collected_row_count": selector_objective_lineage_gate.get(
                "joined_collection_collected_row_count"
            ),
            "selector_objective_lineage_joined_collection_generated_frame_count": selector_objective_lineage_gate.get(
                "joined_collection_generated_frame_count"
            ),
            "selector_objective_lineage_joined_collection_selected_move_delta_count": selector_objective_lineage_gate.get(
                "joined_collection_selected_move_delta_count"
            ),
            "selector_objective_lineage_joined_collection_selected_provider_delta_count": selector_objective_lineage_gate.get(
                "joined_collection_selected_provider_delta_count"
            ),
            "selector_objective_lineage_joined_collection_score_delta_count": selector_objective_lineage_gate.get(
                "joined_collection_score_delta_count"
            ),
            "selector_objective_lineage_joined_collection_routing_delta_count": selector_objective_lineage_gate.get(
                "joined_collection_routing_delta_count"
            ),
            "selector_objective_lineage_seed_manifest_v1_status": selector_objective_lineage_gate.get(
                "seed_manifest_v1_status"
            ),
            "selector_objective_lineage_seed_manifest_v1_seed_row_count": selector_objective_lineage_gate.get(
                "seed_manifest_v1_seed_row_count"
            ),
            "selector_objective_lineage_seed_manifest_v1_selector_training_row_count": selector_objective_lineage_gate.get(
                "seed_manifest_v1_selector_training_row_count"
            ),
            "selector_objective_lineage_seed_manifest_v1_stage7_training_row_count": selector_objective_lineage_gate.get(
                "seed_manifest_v1_stage7_training_row_count"
            ),
            "selector_objective_lineage_seed_probe_v1_status": selector_objective_lineage_gate.get(
                "seed_probe_v1_status"
            ),
            "selector_objective_lineage_feature_probe_status": selector_objective_lineage_gate.get(
                "feature_probe_status"
            ),
            "selector_objective_lineage_feature_probe_runtime_threshold_passing_model_count": selector_objective_lineage_gate.get(
                "feature_probe_runtime_threshold_passing_model_count"
            ),
            "selector_objective_lineage_feature_probe_review_status": selector_objective_lineage_gate.get(
                "feature_probe_review_status"
            ),
            "selector_objective_lineage_feature_probe_review_best_switch_recall": selector_objective_lineage_gate.get(
                "feature_probe_review_best_switch_recall"
            ),
            "selector_objective_lineage_feature_probe_review_best_preserve_recall": selector_objective_lineage_gate.get(
                "feature_probe_review_best_preserve_recall"
            ),
            "selector_objective_lineage_diversity_gap_status": selector_objective_lineage_gate.get(
                "diversity_gap_status"
            ),
            "selector_objective_lineage_diversity_gap_remaining_stage4_selected_failure_count": selector_objective_lineage_gate.get(
                "diversity_gap_remaining_stage4_selected_failure_count"
            ),
            "selector_objective_lineage_diversity_gap_remaining_stage5_6_selected_failure_count": selector_objective_lineage_gate.get(
                "diversity_gap_remaining_stage5_6_selected_failure_count"
            ),
            "selector_objective_lineage_stage4_scope_review_status": selector_objective_lineage_gate.get(
                "stage4_scope_review_status"
            ),
            "selector_objective_lineage_stage4_scope_review_implementation_authorized": selector_objective_lineage_gate.get(
                "stage4_scope_review_implementation_authorized"
            ),
            "selector_objective_lineage_selector_training_allowed": selector_objective_lineage_gate.get(
                "selector_training_allowed"
            ),
            "selector_objective_lineage_stage7_promotion_allowed": selector_objective_lineage_gate.get(
                "stage7_promotion_allowed"
            ),
            "selector_objective_lineage_stage8_training_allowed": selector_objective_lineage_gate.get(
                "stage8_training_allowed"
            ),
            "selector_objective_stage4_collection_status": selector_objective_gate.get(
                "stage4_collection_status"
            ),
            "selector_objective_stage4_collection_collected_row_count": selector_objective_gate.get(
                "stage4_collection_collected_row_count"
            ),
            "selector_objective_stage4_collection_generated_frame_count": selector_objective_gate.get(
                "stage4_collection_generated_frame_count"
            ),
            "selector_objective_stage4_collection_switch_contrast_with_positive_capacity_count": selector_objective_gate.get(
                "stage4_collection_switch_contrast_with_positive_capacity_count"
            ),
            "selector_objective_stage4_collection_default_off_equivalence_passed": selector_objective_gate.get(
                "stage4_collection_default_off_equivalence_passed"
            ),
            "selector_objective_stage4_collection_selected_move_delta_count": selector_objective_gate.get(
                "stage4_collection_selected_move_delta_count"
            ),
            "selector_objective_stage4_collection_selected_provider_delta_count": selector_objective_gate.get(
                "stage4_collection_selected_provider_delta_count"
            ),
            "selector_objective_stage4_collection_score_delta_count": selector_objective_gate.get(
                "stage4_collection_score_delta_count"
            ),
            "selector_objective_stage4_collection_routing_delta_count": selector_objective_gate.get(
                "stage4_collection_routing_delta_count"
            ),
            "selector_objective_seed_manifest_v2_status": selector_objective_gate.get(
                "seed_manifest_v2_status"
            ),
            "selector_objective_seed_manifest_v2_seed_row_count": selector_objective_gate.get(
                "seed_manifest_v2_seed_row_count"
            ),
            "selector_objective_seed_manifest_v2_objective_channel_counts": selector_objective_gate.get(
                "seed_manifest_v2_objective_channel_counts"
            ),
            "selector_objective_seed_probe_v2_status": selector_objective_gate.get(
                "seed_probe_v2_status"
            ),
            "selector_objective_seed_probe_v2_runtime_feature_eligible_prediction_count": selector_objective_gate.get(
                "seed_probe_v2_runtime_feature_eligible_prediction_count"
            ),
            "selector_objective_benchmark_v2_status": selector_objective_gate.get(
                "selector_benchmark_v2_status"
            ),
            "selector_objective_benchmark_v2_best_runtime_model": selector_objective_gate.get(
                "selector_benchmark_v2_best_runtime_model"
            ),
            "selector_objective_benchmark_v2_best_runtime_accuracy": selector_objective_gate.get(
                "selector_benchmark_v2_best_runtime_accuracy"
            ),
            "selector_objective_benchmark_v2_best_runtime_switch_recall": selector_objective_gate.get(
                "selector_benchmark_v2_best_runtime_switch_recall"
            ),
            "selector_objective_benchmark_v2_runtime_threshold_passing_model_count": selector_objective_gate.get(
                "selector_benchmark_v2_runtime_threshold_passing_model_count"
            ),
            "selector_objective_benchmark_review_status": selector_objective_gate.get(
                "selector_benchmark_review_status"
            ),
            "selector_objective_benchmark_review_runtime_review_ready": selector_objective_gate.get(
                "selector_benchmark_review_runtime_review_ready"
            ),
            "selector_objective_benchmark_review_independent_validation_ready": selector_objective_gate.get(
                "selector_benchmark_review_independent_validation_ready"
            ),
            "selector_objective_independent_validation_manifest_status": selector_objective_gate.get(
                "independent_validation_manifest_status"
            ),
            "selector_objective_independent_validation_manifest_job_count": selector_objective_gate.get(
                "independent_validation_manifest_job_count"
            ),
            "selector_objective_independent_validation_manifest_stage7_training_rows": selector_objective_gate.get(
                "independent_validation_manifest_stage7_training_rows"
            ),
            "selector_objective_independent_validation_manifest_job_labels_generated_count": selector_objective_gate.get(
                "independent_validation_manifest_job_labels_generated_count"
            ),
            "selector_objective_independent_validation_labels_status": selector_objective_gate.get(
                "independent_validation_labels_status"
            ),
            "selector_objective_independent_validation_labels_label_count": selector_objective_gate.get(
                "independent_validation_labels_label_count"
            ),
            "selector_objective_independent_validation_labels_selector_training_row_count": selector_objective_gate.get(
                "independent_validation_labels_selector_training_row_count"
            ),
            "selector_objective_independent_validation_labels_stage7_training_row_count": selector_objective_gate.get(
                "independent_validation_labels_stage7_training_row_count"
            ),
            "selector_objective_independent_validation_status": selector_objective_gate.get(
                "independent_validation_status"
            ),
            "selector_objective_independent_validation_row_count": selector_objective_gate.get(
                "independent_validation_row_count"
            ),
            "selector_objective_independent_validation_target_counts": selector_objective_gate.get(
                "independent_validation_target_counts"
            ),
            "selector_objective_independent_validation_switch_recall": selector_objective_gate.get(
                "independent_validation_switch_recall"
            ),
            "selector_objective_independent_validation_preserve_recall": selector_objective_gate.get(
                "independent_validation_preserve_recall"
            ),
            "selector_objective_independent_validation_blocker_status": selector_objective_gate.get(
                "independent_validation_blocker_status"
            ),
            "selector_objective_independent_validation_blocker_class": selector_objective_gate.get(
                "independent_validation_blocker_class"
            ),
            "selector_objective_independent_validation_runtime_selector_blocked": selector_objective_gate.get(
                "independent_validation_runtime_selector_blocked"
            ),
            "selector_objective_selector_training_allowed": selector_objective_gate.get(
                "selector_training_allowed"
            ),
            "selector_objective_stage7_promotion_allowed": selector_objective_gate.get(
                "stage7_promotion_allowed"
            ),
            "selector_objective_stage8_training_allowed": selector_objective_gate.get(
                "stage8_training_allowed"
            ),
            "stage4_first_move_diagnostic_failure_discovery_status": stage4_first_move_diagnostic_gate.get(
                "failure_discovery_status"
            ),
            "stage4_first_move_diagnostic_failure_packet_count": stage4_first_move_diagnostic_gate.get(
                "failure_packet_count"
            ),
            "stage4_first_move_diagnostic_unique_failure_state_move_count": stage4_first_move_diagnostic_gate.get(
                "unique_failure_state_move_count"
            ),
            "stage4_first_move_diagnostic_sequence_review_status": stage4_first_move_diagnostic_gate.get(
                "sequence_review_status"
            ),
            "stage4_first_move_diagnostic_sequence_review_primary_diagnosis": stage4_first_move_diagnostic_gate.get(
                "sequence_review_primary_diagnosis"
            ),
            "stage4_first_move_diagnostic_sequence_candidate_status": stage4_first_move_diagnostic_gate.get(
                "sequence_candidate_status"
            ),
            "stage4_first_move_diagnostic_converting_first_move_count": stage4_first_move_diagnostic_gate.get(
                "sequence_candidate_converting_first_move_count"
            ),
            "stage4_first_move_diagnostic_feature_review_status": stage4_first_move_diagnostic_gate.get(
                "feature_review_status"
            ),
            "stage4_first_move_diagnostic_feature_review_positive_terms": stage4_first_move_diagnostic_gate.get(
                "feature_review_positive_terms"
            ),
            "stage4_first_move_diagnostic_feature_review_failure_terms": stage4_first_move_diagnostic_gate.get(
                "feature_review_failure_terms"
            ),
            "stage4_first_move_diagnostic_stratified_validation_status": stage4_first_move_diagnostic_gate.get(
                "stratified_validation_status"
            ),
            "stage4_first_move_diagnostic_stratified_gap_variant_count": stage4_first_move_diagnostic_gate.get(
                "stratified_validation_gap_variant_count"
            ),
            "stage4_first_move_diagnostic_runtime_review_status": stage4_first_move_diagnostic_gate.get(
                "runtime_review_status"
            ),
            "stage4_first_move_diagnostic_runtime_review_implementation_authorized": stage4_first_move_diagnostic_gate.get(
                "runtime_review_implementation_authorized"
            ),
            "stage4_first_move_diagnostic_sequence_control_dataset_row_count": stage4_first_move_diagnostic_gate.get(
                "sequence_control_dataset_row_count"
            ),
            "stage4_first_move_diagnostic_sequence_control_dataset_runtime_authorization_row_count": stage4_first_move_diagnostic_gate.get(
                "sequence_control_dataset_runtime_authorization_row_count"
            ),
            "stage4_first_move_diagnostic_sequence_control_probe_status": stage4_first_move_diagnostic_gate.get(
                "sequence_control_probe_status"
            ),
            "stage4_first_move_diagnostic_selector_training_allowed": stage4_first_move_diagnostic_gate.get(
                "selector_training_allowed"
            ),
            "stage4_first_move_diagnostic_stage7_promotion_allowed": stage4_first_move_diagnostic_gate.get(
                "stage7_promotion_allowed"
            ),
            "stage4_first_move_diagnostic_stage8_training_allowed": stage4_first_move_diagnostic_gate.get(
                "stage8_training_allowed"
            ),
            "candidate_generation_training_refresh_dataset_v3_status": candidate_generation_training_refresh_gate.get(
                "dataset_v3_status"
            ),
            "candidate_generation_training_refresh_dataset_v3_row_count": candidate_generation_training_refresh_gate.get(
                "dataset_v3_row_count"
            ),
            "candidate_generation_training_refresh_dataset_v3_candidate_generation_training_row_count": candidate_generation_training_refresh_gate.get(
                "dataset_v3_candidate_generation_training_row_count"
            ),
            "candidate_generation_training_refresh_dataset_v3_selector_training_row_count": candidate_generation_training_refresh_gate.get(
                "dataset_v3_selector_training_row_count"
            ),
            "candidate_generation_training_refresh_context_benchmark_status": candidate_generation_training_refresh_gate.get(
                "context_benchmark_status"
            ),
            "candidate_generation_training_refresh_context_benchmark_stage_family_positive_capacity_recall_from_trace": candidate_generation_training_refresh_gate.get(
                "context_benchmark_stage_family_positive_capacity_recall_from_trace"
            ),
            "candidate_generation_training_refresh_runtime_boundary_status": candidate_generation_training_refresh_gate.get(
                "runtime_boundary_status"
            ),
            "candidate_generation_training_refresh_runtime_boundary_new_runtime_behavior_allowed": candidate_generation_training_refresh_gate.get(
                "runtime_boundary_new_runtime_behavior_allowed"
            ),
            "candidate_generation_training_refresh_design_v2_status": candidate_generation_training_refresh_gate.get(
                "training_refresh_design_v2_status"
            ),
            "candidate_generation_training_refresh_design_v2_runtime_candidate_generator_refresh_allowed": candidate_generation_training_refresh_gate.get(
                "training_refresh_design_v2_runtime_candidate_generator_refresh_allowed"
            ),
            "candidate_generation_training_refresh_design_v2_selector_allowed": candidate_generation_training_refresh_gate.get(
                "training_refresh_design_v2_selector_allowed"
            ),
            "candidate_generation_training_refresh_design_v2_guardrails_allowed": candidate_generation_training_refresh_gate.get(
                "training_refresh_design_v2_guardrails_allowed"
            ),
            "candidate_generation_training_refresh_design_v2_promotion_allowed": candidate_generation_training_refresh_gate.get(
                "training_refresh_design_v2_promotion_allowed"
            ),
            "candidate_generation_training_refresh_design_status": candidate_generation_training_refresh_gate.get(
                "training_refresh_design_status"
            ),
            "candidate_generation_training_refresh_design_implementation_allowed": candidate_generation_training_refresh_gate.get(
                "training_refresh_design_implementation_allowed"
            ),
            "candidate_generation_training_refresh_benchmark_status": candidate_generation_training_refresh_gate.get(
                "benchmark_status"
            ),
            "candidate_generation_training_refresh_benchmark_best_policy": candidate_generation_training_refresh_gate.get(
                "benchmark_best_policy"
            ),
            "candidate_generation_training_refresh_benchmark_positive_capacity_recall": candidate_generation_training_refresh_gate.get(
                "benchmark_positive_capacity_recall"
            ),
            "candidate_generation_training_refresh_benchmark_negative_capacity_suppression": candidate_generation_training_refresh_gate.get(
                "benchmark_negative_capacity_suppression"
            ),
            "candidate_generation_training_refresh_benchmark_thresholds_met": candidate_generation_training_refresh_gate.get(
                "benchmark_thresholds_met"
            ),
            "candidate_generation_training_refresh_runtime_review_status": candidate_generation_training_refresh_gate.get(
                "runtime_review_status"
            ),
            "candidate_generation_training_refresh_runtime_review_ready": candidate_generation_training_refresh_gate.get(
                "runtime_review_ready"
            ),
            "candidate_generation_training_refresh_runtime_review_candidate_generation_allowed_by_packet": candidate_generation_training_refresh_gate.get(
                "runtime_review_candidate_generation_allowed_by_packet"
            ),
            "candidate_generation_training_refresh_runtime_review_implementation_authorized": candidate_generation_training_refresh_gate.get(
                "runtime_review_implementation_authorized"
            ),
            "candidate_generation_training_refresh_runtime_work_allowed": candidate_generation_training_refresh_gate.get(
                "runtime_work_allowed"
            ),
            "candidate_generation_training_refresh_selector_training_allowed": candidate_generation_training_refresh_gate.get(
                "selector_training_allowed"
            ),
            "candidate_generation_training_refresh_stage7_promotion_allowed": candidate_generation_training_refresh_gate.get(
                "stage7_promotion_allowed"
            ),
            "candidate_generation_training_refresh_stage8_training_allowed": candidate_generation_training_refresh_gate.get(
                "stage8_training_allowed"
            ),
            "candidate_generation_trace_refresh_sandbox_status": candidate_generation_trace_context_gate.get(
                "refresh_sandbox_status"
            ),
            "candidate_generation_trace_refresh_sandbox_generated_frame_count": candidate_generation_trace_context_gate.get(
                "refresh_sandbox_generated_frame_count"
            ),
            "candidate_generation_trace_refresh_sandbox_default_off_equivalence_passed": candidate_generation_trace_context_gate.get(
                "refresh_sandbox_default_off_equivalence_passed"
            ),
            "candidate_generation_trace_refresh_coverage_status": candidate_generation_trace_context_gate.get(
                "refresh_coverage_status"
            ),
            "candidate_generation_trace_refresh_coverage_exact_positive_capacity_recall": candidate_generation_trace_context_gate.get(
                "refresh_coverage_exact_positive_capacity_recall"
            ),
            "candidate_generation_trace_refresh_trace_features_status": candidate_generation_trace_context_gate.get(
                "refresh_trace_features_status"
            ),
            "candidate_generation_trace_refresh_trace_features_trace_frame_count": candidate_generation_trace_context_gate.get(
                "refresh_trace_features_trace_frame_count"
            ),
            "candidate_generation_trace_refresh_trace_features_stage7_trace_frame_count": candidate_generation_trace_context_gate.get(
                "refresh_trace_features_stage7_trace_frame_count"
            ),
            "candidate_generation_trace_refresh_trace_features_selector_training_row_count": candidate_generation_trace_context_gate.get(
                "refresh_trace_features_selector_training_row_count"
            ),
            "candidate_generation_trace_refresh_trace_features_candidate_generation_training_row_count": candidate_generation_trace_context_gate.get(
                "refresh_trace_features_candidate_generation_training_row_count"
            ),
            "candidate_generation_trace_dataset_v4_status": candidate_generation_trace_context_gate.get(
                "dataset_v4_status"
            ),
            "candidate_generation_trace_dataset_v4_row_count": candidate_generation_trace_context_gate.get(
                "dataset_v4_row_count"
            ),
            "candidate_generation_trace_v4_boundary_status": candidate_generation_trace_context_gate.get(
                "v4_boundary_status"
            ),
            "candidate_generation_trace_source_gap_manifest_status": candidate_generation_trace_context_gate.get(
                "source_gap_manifest_status"
            ),
            "candidate_generation_trace_source_gap_exact_missing_positive_capacity_count": candidate_generation_trace_context_gate.get(
                "source_gap_exact_missing_positive_capacity_count"
            ),
            "candidate_generation_trace_exact_trace_runtime_review_status": candidate_generation_trace_context_gate.get(
                "exact_trace_runtime_review_status"
            ),
            "candidate_generation_trace_exact_trace_runtime_review_implementation_authorized": candidate_generation_trace_context_gate.get(
                "exact_trace_runtime_review_implementation_authorized"
            ),
            "candidate_generation_trace_exact_trace_sandbox_status": candidate_generation_trace_context_gate.get(
                "exact_trace_sandbox_status"
            ),
            "candidate_generation_trace_exact_trace_sandbox_generated_frame_count": candidate_generation_trace_context_gate.get(
                "exact_trace_sandbox_generated_frame_count"
            ),
            "candidate_generation_trace_exact_trace_coverage_exact_gap_recall": candidate_generation_trace_context_gate.get(
                "exact_trace_coverage_exact_gap_recall"
            ),
            "candidate_generation_trace_dataset_v5_status": candidate_generation_trace_context_gate.get(
                "dataset_v5_status"
            ),
            "candidate_generation_trace_dataset_v5_row_count": candidate_generation_trace_context_gate.get(
                "dataset_v5_row_count"
            ),
            "candidate_generation_trace_dataset_v5_selector_training_row_count": candidate_generation_trace_context_gate.get(
                "dataset_v5_selector_training_row_count"
            ),
            "candidate_generation_trace_v5_context_benchmark_status": candidate_generation_trace_context_gate.get(
                "v5_context_benchmark_status"
            ),
            "candidate_generation_trace_v5_exact_positive_capacity_recall_from_candidate_generation_trace": candidate_generation_trace_context_gate.get(
                "v5_exact_positive_capacity_recall_from_candidate_generation_trace"
            ),
            "candidate_generation_trace_v5_boundary_status": candidate_generation_trace_context_gate.get(
                "v5_boundary_status"
            ),
            "candidate_generation_trace_v5_boundary_implement_new_runtime_sandbox": candidate_generation_trace_context_gate.get(
                "v5_boundary_implement_new_runtime_sandbox"
            ),
            "candidate_generation_trace_runtime_work_allowed": candidate_generation_trace_context_gate.get(
                "runtime_work_allowed"
            ),
            "candidate_generation_trace_selector_training_allowed": candidate_generation_trace_context_gate.get(
                "selector_training_allowed"
            ),
            "candidate_generation_trace_stage7_promotion_allowed": candidate_generation_trace_context_gate.get(
                "stage7_promotion_allowed"
            ),
            "candidate_generation_trace_stage8_training_allowed": candidate_generation_trace_context_gate.get(
                "stage8_training_allowed"
            ),
            "strategy_arbitration_decision_status": strategy_arbitration_gate.get(
                "decision_status"
            ),
            "strategy_arbitration_decision_next_class": strategy_arbitration_gate.get(
                "decision_next_class"
            ),
            "strategy_arbitration_dataset_record_count": strategy_arbitration_gate.get(
                "dataset_record_count"
            ),
            "strategy_arbitration_dataset_proposal_count": strategy_arbitration_gate.get(
                "dataset_proposal_count"
            ),
            "strategy_arbitration_probe_stage7_record_count": strategy_arbitration_gate.get(
                "probe_stage7_record_count"
            ),
            "strategy_arbitration_probe_raw_global_provider_hit_rate": strategy_arbitration_gate.get(
                "probe_raw_global_provider_hit_rate"
            ),
            "strategy_arbitration_probe_visible_heuristic_hit_rate": strategy_arbitration_gate.get(
                "probe_visible_heuristic_hit_rate"
            ),
            "strategy_arbitration_missing_feature_candidate_count": strategy_arbitration_gate.get(
                "missing_feature_candidate_count"
            ),
            "strategy_arbitration_missing_feature_recommended_next_step": strategy_arbitration_gate.get(
                "missing_feature_recommended_next_step"
            ),
            "strategy_arbitration_runtime_work_allowed": strategy_arbitration_gate.get(
                "runtime_work_allowed"
            ),
            "strategy_arbitration_runtime_arbiter_allowed": strategy_arbitration_gate.get(
                "runtime_arbiter_allowed"
            ),
            "strategy_arbitration_selector_training_allowed": strategy_arbitration_gate.get(
                "selector_training_allowed"
            ),
            "strategy_arbitration_stage7_promotion_allowed": strategy_arbitration_gate.get(
                "stage7_promotion_allowed"
            ),
            "strategy_arbitration_stage8_training_allowed": strategy_arbitration_gate.get(
                "stage8_training_allowed"
            ),
            "strategy_monitor_plan_do_not_implement_as_causal_affordances": strategy_monitor_maturity_gate.get(
                "plan_do_not_implement_as_causal_affordances"
            ),
            "strategy_monitor_records_monitor_record_count": strategy_monitor_maturity_gate.get(
                "records_monitor_record_count"
            ),
            "strategy_monitor_companion_audit_v1_visible_term_count": strategy_monitor_maturity_gate.get(
                "companion_audit_v1_visible_term_count"
            ),
            "strategy_monitor_companion_audit_v1_still_missing_term_count": strategy_monitor_maturity_gate.get(
                "companion_audit_v1_still_missing_term_count"
            ),
            "strategy_monitor_maturity_term_count": strategy_monitor_maturity_gate.get(
                "maturity_term_count"
            ),
            "strategy_monitor_maturity_causal_ready_terms": strategy_monitor_maturity_gate.get(
                "maturity_causal_ready_terms"
            ),
            "strategy_monitor_maturity_strongest_internal_terminal_candidates": strategy_monitor_maturity_gate.get(
                "maturity_strongest_internal_terminal_candidates"
            ),
            "strategy_monitor_maturity_recommended_next_step": strategy_monitor_maturity_gate.get(
                "maturity_recommended_next_step"
            ),
            "strategy_monitor_runtime_work_allowed": strategy_monitor_maturity_gate.get(
                "runtime_work_allowed"
            ),
            "strategy_monitor_runtime_terminals_allowed": strategy_monitor_maturity_gate.get(
                "runtime_terminals_allowed"
            ),
            "strategy_monitor_runtime_arbiter_allowed": strategy_monitor_maturity_gate.get(
                "runtime_arbiter_allowed"
            ),
            "strategy_monitor_monitor_to_provider_routing_allowed": strategy_monitor_maturity_gate.get(
                "monitor_to_provider_routing_allowed"
            ),
            "strategy_monitor_selector_training_allowed": strategy_monitor_maturity_gate.get(
                "selector_training_allowed"
            ),
            "strategy_monitor_stage7_promotion_allowed": strategy_monitor_maturity_gate.get(
                "stage7_promotion_allowed"
            ),
            "strategy_monitor_stage8_training_allowed": strategy_monitor_maturity_gate.get(
                "stage8_training_allowed"
            ),
            "internal_terminal_feature_candidate_all_non_causal": internal_terminal_readiness_gate.get(
                "feature_candidate_all_non_causal"
            ),
            "internal_terminal_candidate_spec_count": internal_terminal_readiness_gate.get(
                "candidate_spec_count"
            ),
            "internal_terminal_validation_causal_ready_terminals": internal_terminal_readiness_gate.get(
                "validation_causal_ready_terminals"
            ),
            "internal_terminal_validation_all_causal_use_blocked": internal_terminal_readiness_gate.get(
                "validation_all_causal_use_blocked"
            ),
            "internal_terminal_evidence_causal_ready_terminals": internal_terminal_readiness_gate.get(
                "evidence_causal_ready_terminals"
            ),
            "internal_terminal_evidence_all_causal_ready_false": internal_terminal_readiness_gate.get(
                "evidence_all_causal_ready_false"
            ),
            "internal_terminal_design_review_causal_ready_terminals": internal_terminal_readiness_gate.get(
                "design_review_causal_ready_terminals"
            ),
            "internal_terminal_design_review_all_causal_ready_false": internal_terminal_readiness_gate.get(
                "design_review_all_causal_ready_false"
            ),
            "internal_terminal_design_review_recommended_next_step": internal_terminal_readiness_gate.get(
                "design_review_recommended_next_step"
            ),
            "internal_terminal_runtime_work_allowed": internal_terminal_readiness_gate.get(
                "runtime_work_allowed"
            ),
            "internal_terminal_runtime_terminals_allowed": internal_terminal_readiness_gate.get(
                "runtime_terminals_allowed"
            ),
            "internal_terminal_causal_affordances_allowed": internal_terminal_readiness_gate.get(
                "causal_affordances_allowed"
            ),
            "internal_terminal_runtime_arbiter_allowed": internal_terminal_readiness_gate.get(
                "runtime_arbiter_allowed"
            ),
            "internal_terminal_monitor_to_provider_routing_allowed": internal_terminal_readiness_gate.get(
                "monitor_to_provider_routing_allowed"
            ),
            "internal_terminal_selector_training_allowed": internal_terminal_readiness_gate.get(
                "selector_training_allowed"
            ),
            "internal_terminal_stage7_promotion_allowed": internal_terminal_readiness_gate.get(
                "stage7_promotion_allowed"
            ),
            "internal_terminal_stage8_training_allowed": internal_terminal_readiness_gate.get(
                "stage8_training_allowed"
            ),
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
            "sequence_policy_underpowered_pilot_protected_failure_contrast_runner_collection_run_allowed": underpowered_pilot.get(
                "summary", {}
            ).get("protected_failure_contrast_runner_collection_run_allowed"),
            "sequence_policy_underpowered_pilot_protected_failure_contrast_approval_receipt_present": underpowered_pilot.get(
                "summary", {}
            ).get("protected_failure_contrast_approval_receipt_present"),
            "sequence_policy_underpowered_pilot_protected_failure_contrast_approval_receipt_valid": underpowered_pilot.get(
                "summary", {}
            ).get("protected_failure_contrast_approval_receipt_valid"),
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
            "stage8_training_readiness_protected_failure_contrast_approval_receipt_present": stage8_review.get(
                "requirements", {}
            ).get("protected_failure_contrast_approval_receipt_present"),
            "stage8_training_readiness_protected_failure_contrast_approval_receipt_valid": stage8_review.get(
                "requirements", {}
            ).get("protected_failure_contrast_approval_receipt_valid"),
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
            "stage7_post_label_outcome_protected_failure_contrast_runner_collection_run_allowed": post_label_review.get(
                "summary", {}
            ).get("protected_failure_contrast_runner_collection_run_allowed"),
            "stage7_post_label_outcome_protected_failure_contrast_approval_receipt_present": post_label_review.get(
                "summary", {}
            ).get("protected_failure_contrast_approval_receipt_present"),
            "stage7_post_label_outcome_protected_failure_contrast_approval_receipt_valid": post_label_review.get(
                "summary", {}
            ).get("protected_failure_contrast_approval_receipt_valid"),
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
