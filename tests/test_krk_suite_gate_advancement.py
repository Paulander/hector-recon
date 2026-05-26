#!/usr/bin/env python3
"""Tests for passive KRK suite gate advancement."""

import importlib.util
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def _load_module(name: str, relative: str):
    spec = importlib.util.spec_from_file_location(name, ROOT / relative)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


_advance = _load_module(
    "advance_krk_suite_from_current_gates_v0",
    "scripts/advance_krk_suite_from_current_gates_v0.py",
)


def _read_report() -> dict:
    payload = json.loads((ROOT / "reports/krk_suite_gate_advancement_v0.json").read_text())
    assert isinstance(payload, dict)
    return payload


def test_gate_advancement_artifact_is_passive_and_boundary_clean():
    payload = _read_report()

    assert payload["schema_version"] == "krk_suite_gate_advancement.v0"
    assert payload["causal_status"] == "non_causal_passive_gate_advancement"
    assert payload["runtime_behavior_changed"] is False
    assert payload["runtime_defaults_changed"] is False
    assert payload["runtime_selector_implemented"] is False
    assert payload["runtime_score_changes"] is False
    assert payload["runtime_direct_routing"] is False
    assert payload["runtime_dtm_or_tablebase_lookup"] is False
    assert payload["gameplay_topology_mutation"] is False
    assert payload["stage7_promotion_allowed"] is False
    assert payload["stage8_training_allowed"] is False
    assert payload["summary"]["all_boundaries_preserved"] is True

    decision = payload["decision"]
    assert decision["runtime_changes_allowed"] is False
    assert decision["label_run_allowed"] is False
    assert decision["selector_allowed"] is False
    assert decision["selector_training_allowed"] is False
    assert decision["stage7_promotion_allowed"] is False
    assert decision["stage8_training_allowed"] is False


def test_gate_advancement_reports_current_stage7_blocker():
    payload = _read_report()

    assert (
        payload["decision"]["status"]
        == "krk_suite_passive_advancement_ready_for_protected_failure_contrast_collection"
    )
    assert (
        payload["decision"]["recommended_next_step"]
        == "obtain_matching_approval_receipt_before_protected_failure_contrast_collection"
    )
    assert payload["summary"]["stage7_success_controls"] == 11
    assert (
        payload["summary"]["protected_stack_status"]
        == "retry1_protected_stage5_6_stack_adopted_manifest_only"
    )
    assert payload["summary"]["protected_stack_ready"] is True
    assert payload["summary"]["protected_stack_rollback_paths_preserved"] is True
    assert payload["summary"]["protected_stack_active_paths_safe"] is True
    assert payload["summary"]["protected_stack_active_paths_exist"] is True
    assert payload["summary"]["protected_stack_rollback_paths_safe"] is True
    assert payload["summary"]["protected_stack_rollback_paths_exist"] is True
    assert payload["summary"]["protected_stack_rollback_common_paths_distinct"] is True
    assert payload["summary"]["protected_stack_filesystem_snapshots_replaced"] is False
    assert payload["summary"]["stage7_success_controls_required"] == 5
    assert payload["summary"]["stage7_success_controls_ready"] is True
    assert (
        payload["summary"]["stage7_clean_success_backfill_status"]
        == "stage7_clean_success_backfill_available"
    )
    assert payload["summary"]["stage7_clean_success_backfill_available"] is True
    assert payload["summary"]["stage7_clean_success_backfill_eligible_new_success"] == 0
    assert payload["summary"]["sequence_policy_inputs_ready"] is True
    assert payload["summary"]["sequence_policy_benchmark_ready"] is True


def test_gate_advancement_writer_includes_all_passive_steps():
    payload = _advance.build_payload()
    rendered = _advance.write_markdown(payload)

    step_ids = {step["step_id"] for step in payload["step_results"]}
    assert step_ids == {
        "stage7_diverse_clean_output_validation",
        "stage4_first_move_contrast_sandbox_approval_request",
        "stage4_caveat_unblocker_packet",
        "stage7_clean_artifact_manifest",
        "stage7_clean_sequence_control_recovery",
        "stage7_clean_success_backfill_audit",
        "sequence_policy_pipeline_refresh",
        "sequence_policy_benchmark_review",
        "protected_plan_window_failure_contrast_plan",
        "protected_plan_window_failure_contrast_manifest",
        "protected_plan_window_failure_contrast_manifest_review",
        "protected_plan_window_failure_contrast_execution_readiness",
        "protected_plan_window_failure_contrast_runner",
        "protected_plan_window_failure_contrast_approval_request",
        "protected_plan_window_failure_contrast_output_validation",
        "protected_plan_window_failure_contrast_integration",
        "sequence_policy_after_protected_failure_contrast_refresh",
        "sequence_policy_underpowered_pilot_review",
        "full_suite_readiness_audit",
        "full_suite_unblocker_packet",
        "stage8_training_readiness_review",
        "stage7_post_label_outcome_review",
        "stage7_label_distribution_review",
        "stage7_additional_clean_sampling_manifest",
        "stage7_additional_clean_output_validation",
        "stage7_additional_clean_sampling_runner",
        "current_control_plane_gate",
    }
    assert (
        "krk_suite_passive_advancement_ready_for_protected_failure_contrast_collection"
        in rendered
    )
    assert (
        payload["summary"]["sequence_policy_benchmark_review_status"]
        == "sequence_policy_benchmark_mixed_plan_window_underpowered"
    )
    assert (
        payload["summary"]["protected_plan_window_failure_contrast_plan_status"]
        == "protected_plan_window_failure_contrast_plan_ready_pending_explicit_collection_approval"
    )
    assert payload["summary"]["protected_plan_window_unique_failure_count"] == 1
    assert payload["summary"]["protected_plan_window_minimum_new_failures_needed"] == 4
    assert (
        payload["summary"]["protected_plan_window_failure_contrast_manifest_status"]
        == "protected_plan_window_failure_contrast_manifest_ready_for_review"
    )
    assert payload["summary"]["protected_plan_window_failure_contrast_manifest_job_count"] == 6
    assert (
        payload["summary"]["protected_plan_window_failure_contrast_manifest_review_status"]
        == "protected_plan_window_failure_contrast_manifest_review_passed_pending_explicit_approval"
    )
    assert (
        payload["summary"][
            "protected_plan_window_failure_contrast_execution_readiness_status"
        ]
        == "protected_plan_window_failure_contrast_execution_ready_pending_explicit_approval"
    )
    assert payload["summary"]["protected_plan_window_failure_contrast_execution_jobs_passing"] == 6
    assert (
        payload["summary"]["protected_plan_window_failure_contrast_runner_status"]
        == "protected_plan_window_failure_contrast_runner_dry_run_ready"
    )
    assert payload["summary"]["protected_plan_window_failure_contrast_runner_processed_job_count"] == 0
    assert payload["summary"]["protected_plan_window_failure_contrast_runner_executed_job_count"] == 0
    assert (
        payload["summary"]["protected_plan_window_failure_contrast_approval_request_status"]
        == "protected_plan_window_failure_contrast_approval_request_ready"
    )
    assert (
        payload["summary"]["protected_plan_window_failure_contrast_approval_receipt_created"]
        is False
    )
    assert payload["summary"][
        "protected_plan_window_failure_contrast_approval_receipt_blockers"
    ] == ["approval_receipt_missing"]
    assert (
        payload["summary"]["protected_plan_window_failure_contrast_output_validation_status"]
        == "protected_plan_window_failure_contrast_outputs_validation_pending"
    )
    assert payload["summary"]["protected_plan_window_failure_contrast_output_exists_count"] == 0
    assert payload["summary"]["protected_plan_window_failure_contrast_output_valid_count"] == 0
    assert (
        payload["summary"]["protected_plan_window_failure_contrast_integration_status"]
        == "protected_plan_window_failure_contrast_integration_pending_outputs"
    )
    assert payload["summary"]["protected_plan_window_failure_contrast_integrated_new_failure_count"] == 0
    assert payload["summary"]["protected_plan_window_failure_contrast_integration_ready"] is False
    assert (
        payload["summary"]["sequence_policy_after_protected_failure_contrast_refresh_status"]
        == "sequence_policy_after_protected_failure_contrast_refresh_waiting_on_integration_outputs"
    )
    assert payload["summary"]["sequence_policy_after_protected_failure_contrast_rows"] == 0
    assert (
        payload["summary"]["sequence_policy_underpowered_pilot_status"]
        == "sequence_policy_pilot_underpowered_pending_protected_failure_contrast_collection"
    )
    assert (
        payload["summary"]["sequence_policy_underpowered_pilot_next_step"]
        == "obtain_matching_approval_receipt_before_protected_failure_contrast_collection"
    )
    assert payload["summary"]["sequence_policy_underpowered_pilot_stage4_topk_signal"] is True
    assert payload["summary"]["sequence_policy_underpowered_pilot_stage7_success_gap"] == 0
    assert (
        payload["summary"][
            "sequence_policy_underpowered_pilot_protected_failure_contrast_runner_processed_job_count"
        ]
        == 0
    )
    assert (
        payload["summary"][
            "sequence_policy_underpowered_pilot_protected_failure_contrast_runner_executed_job_count"
        ]
        == 0
    )
    assert (
        payload["summary"]["stage7_output_validation_status"]
        == "stage7_diverse_clean_sampling_outputs_valid_ready_for_integration"
    )
    assert payload["summary"]["stage7_output_valid_count"] == 8
    assert (
        payload["summary"]["stage8_training_readiness_status"]
        == "stage8_training_blocked_pending_protected_failure_contrast_collection"
    )
    assert (
        payload["summary"]["stage7_post_label_outcome_status"]
        == "post_label_outcome_waiting_on_explicit_protected_failure_contrast_collection"
    )
    assert (
        payload["summary"]["stage7_post_label_outcome_next_step"]
        == "obtain_matching_approval_receipt_before_protected_failure_contrast_collection"
    )
    assert (
        payload["summary"][
            "stage7_post_label_outcome_protected_failure_contrast_runner_processed_job_count"
        ]
        == 0
    )
    assert (
        payload["summary"][
            "stage7_post_label_outcome_protected_failure_contrast_runner_executed_job_count"
        ]
        == 0
    )
    assert (
        payload["summary"]["stage7_label_distribution_review_status"]
        == "stage7_label_distribution_review_success_gate_closed"
    )
    assert (
        payload["summary"]["stage7_label_distribution_review_next_step"]
        == "rerun_passive_sequence_policy_gate_stack"
    )
    assert payload["summary"]["stage7_label_distribution_unique_new_success"] == 2
    assert payload["summary"]["stage7_label_distribution_duplicate_playouts"] == 50
    assert (
        payload["summary"]["stage7_additional_clean_sampling_manifest_status"]
        == "stage7_additional_clean_sampling_manifest_not_applicable_success_gate_closed"
    )
    assert (
        payload["summary"]["stage7_additional_clean_sampling_runner_status"]
        == "stage7_additional_clean_sampling_runner_not_applicable_success_gate_closed"
    )
    assert payload["summary"]["stage7_additional_clean_sampling_job_count"] == 0
    assert payload["summary"]["stage7_additional_clean_sampling_max_samples"] == 0
    assert (
        payload["summary"]["stage4_caveat_unblocker_status"]
        == "stage4_caveat_unblocker_ready_pending_explicit_runtime_approval"
    )
    assert (
        payload["summary"][
            "stage4_first_move_contrast_sandbox_approval_request_status"
        ]
        == "stage4_first_move_contrast_sandbox_approval_request_ready"
    )
    assert (
        payload["summary"][
            "stage4_first_move_contrast_sandbox_approval_request_created"
        ]
        is False
    )
    assert (
        payload["summary"][
            "stage4_first_move_contrast_sandbox_implementation_authorized_by_request"
        ]
        is False
    )
    for step in payload["step_results"]:
        assert step["label_run_allowed"] is False
        assert step["runtime_changes_allowed"] is False
        assert step["stage7_promotion_allowed"] is False
        assert step["stage8_training_allowed"] is False
        assert step["artifact_runtime_behavior_changed"] is False
        assert step["artifact_runtime_defaults_changed"] is False
        assert step["artifact_runtime_selector_implemented"] is False
        assert step["artifact_runtime_score_changes"] is False
        assert step["artifact_runtime_direct_routing"] is False
        assert step["artifact_runtime_dtm_or_tablebase_lookup"] is False
        assert step["artifact_gameplay_topology_mutation"] is False
        assert step["artifact_stage7_promotion_allowed"] is False
        assert step["artifact_stage8_training_allowed"] is False


def test_gate_advancement_does_not_inherit_caller_label_execution_flags():
    original_argv = sys.argv
    try:
        sys.argv = [
            "scripts/run_stage7_additional_clean_sampling_jobs_v0.py",
            "--execute-reviewed-label-run",
            "--refresh-after-run",
        ]
        payload = _advance.build_payload()
    finally:
        sys.argv = original_argv

    assert payload["decision"]["label_run_allowed"] is False
    runner_step = [
        step
        for step in payload["step_results"]
        if step["step_id"] == "stage7_additional_clean_sampling_runner"
    ][0]
    assert runner_step["label_run_allowed"] is False
    assert (
        runner_step["decision_status"]
        == "stage7_additional_clean_sampling_runner_not_applicable_success_gate_closed"
    )


def test_gate_advancement_boundary_check_includes_artifact_level_flags(monkeypatch):
    real_load_json = _advance._load_json

    def tainted_load_json(relative: str):
        payload = real_load_json(relative)
        if relative == "reports/strategy_arbitration/krk_sequence_policy_benchmark_review_v0.json":
            payload = dict(payload)
            payload["runtime_behavior_changed"] = True
        return payload

    monkeypatch.setattr(_advance, "_load_json", tainted_load_json)

    payload = _advance.build_payload()

    assert payload["summary"]["all_boundaries_preserved"] is False
    tainted_step = [
        step
        for step in payload["step_results"]
        if step["step_id"] == "sequence_policy_benchmark_review"
    ][0]
    assert tainted_step["runtime_changes_allowed"] is False
    assert tainted_step["artifact_runtime_behavior_changed"] is True


def test_gate_advancement_routes_forbidden_training_rows_to_input_repair(monkeypatch):
    real_load_json = _advance._load_json

    def no_op_run_script(script: str):
        return {"script": script, "ran": False}

    def tainted_load_json(relative: str):
        payload = json.loads(json.dumps(real_load_json(relative)))
        if relative == "reports/strategy_arbitration/krk_sequence_policy_benchmark_v0.json":
            payload.setdefault("preflight", {})["selector_training_row_count"] = 1
            payload.setdefault("preflight", {})["blockers"] = [
                "selector_training_rows_forbidden"
            ]
            payload.setdefault("decision", {})["status"] = (
                "sequence_policy_benchmark_blocked_forbidden_training_or_runtime_rows"
            )
        if (
            relative
            == "reports/strategy_arbitration/krk_sequence_policy_benchmark_review_v0.json"
        ):
            payload["blockers"] = ["selector_training_rows_forbidden"]
            payload.setdefault("decision", {})["status"] = (
                "sequence_policy_benchmark_review_blocked_forbidden_training_or_runtime_rows"
            )
        if (
            relative
            == "reports/strategy_arbitration/krk_sequence_policy_underpowered_pilot_v0.json"
        ):
            payload.setdefault("summary", {})[
                "forbidden_training_or_runtime_input_blocked"
            ] = True
            payload["blockers"] = ["selector_training_rows_forbidden"]
            payload.setdefault("decision", {})["status"] = (
                "sequence_policy_pilot_blocked_forbidden_training_or_runtime_rows"
            )
            payload["decision"]["recommended_next_step"] = (
                "repair_sequence_policy_inputs_remove_training_or_runtime_rows"
            )
        if relative == "reports/krk_full_suite_readiness_audit_v0.json":
            payload.setdefault("sequence_policy", {})[
                "forbidden_training_or_runtime_input_blocked"
            ] = True
            payload.setdefault("hard_blockers", []).append(
                "sequence_policy_forbidden_training_or_runtime_rows"
            )
            payload.setdefault("decision", {})["status"] = (
                "krk_suite_readiness_blocked_forbidden_training_or_runtime_rows"
            )
        if relative == "reports/krk_full_suite_unblocker_packet_v0.json":
            payload.setdefault("current_state", {})[
                "sequence_policy_forbidden_training_or_runtime_input_blocked"
            ] = True
            payload.setdefault("decision", {})["status"] = (
                "krk_suite_unblocker_blocked_forbidden_training_or_runtime_rows"
            )
        return payload

    monkeypatch.setattr(_advance, "_run_script", no_op_run_script)
    monkeypatch.setattr(_advance, "_load_json", tainted_load_json)

    payload = _advance.build_payload()

    assert (
        payload["decision"]["status"]
        == "krk_suite_passive_advancement_blocked_forbidden_training_or_runtime_rows"
    )
    assert (
        payload["decision"]["recommended_next_step"]
        == "repair_sequence_policy_inputs_remove_training_or_runtime_rows"
    )
    assert payload["summary"][
        "sequence_policy_forbidden_training_or_runtime_input_blocked"
    ] is True
    assert (
        "selector_training_rows_forbidden"
        in payload["summary"]["sequence_policy_forbidden_training_or_runtime_input_blockers"]
    )
    assert payload["decision"]["selector_training_allowed"] is False
