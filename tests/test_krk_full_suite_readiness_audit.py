#!/usr/bin/env python3
"""Tests for the KRK full-suite readiness audit."""

import importlib.util
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def _load_module(name: str, relative: str):
    spec = importlib.util.spec_from_file_location(name, ROOT / relative)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


_audit = _load_module(
    "write_krk_full_suite_readiness_audit_v0",
    "scripts/write_krk_full_suite_readiness_audit_v0.py",
)


def _read_report() -> dict:
    payload = json.loads((ROOT / "reports/krk_full_suite_readiness_audit_v0.json").read_text())
    assert isinstance(payload, dict)
    return payload


def test_full_suite_readiness_artifact_preserves_boundaries():
    payload = _read_report()

    assert payload["schema_version"] == "krk_full_suite_readiness_audit.v0"
    assert payload["causal_status"] == "non_causal_readiness_audit"
    assert payload["runtime_behavior_changed"] is False
    assert payload["runtime_defaults_changed"] is False
    assert payload["runtime_selector_implemented"] is False
    assert payload["runtime_score_changes"] is False
    assert payload["runtime_direct_routing"] is False
    assert payload["runtime_dtm_or_tablebase_lookup"] is False
    assert payload["hidden_python_controller"] is False
    assert payload["gameplay_topology_mutation"] is False
    assert payload["stage7_promotion_allowed"] is False
    assert payload["stage8_training_allowed"] is False
    assert payload["decision"]["runtime_changes_allowed"] is False
    assert payload["decision"]["label_run_allowed"] is False
    assert payload["decision"]["selector_allowed"] is False
    assert payload["decision"]["selector_training_allowed"] is False
    assert payload["decision"]["stage7_promotion_allowed"] is False
    assert payload["decision"]["stage8_training_allowed"] is False

    boundaries = payload["runtime_and_training_boundaries"]
    assert boundaries["checked_flag_count"] >= 430
    assert boundaries["violation_count"] == 0
    assert boundaries["runtime_behavior_changed"] is False
    assert boundaries["runtime_selector_implemented"] is False
    assert boundaries["runtime_score_changes"] is False
    assert boundaries["runtime_direct_routing"] is False
    assert boundaries["runtime_dtm_or_tablebase_lookup"] is False
    assert boundaries["hidden_python_controller"] is False
    assert boundaries["gameplay_topology_mutation"] is False
    assert (
        payload["source_artifacts"]["control_plane_filtered_frames"]
        == "reports/krk_control_plane_filtered_frames_v0.json"
    )
    assert (
        payload["source_artifacts"]["control_plane_forced_controls"]
        == "reports/krk_control_plane_filtered_frames_with_forced_controls_v0.json"
    )
    assert (
        payload["source_artifacts"]["sequence_benchmark_inputs"]
        == "reports/strategy_arbitration/krk_sequence_policy_benchmark_inputs_v0.json"
    )
    assert (
        payload["source_artifacts"]["stage7_sampling_manifest"]
        == "reports/structural_candidates/stage7_diverse_clean_sampling_manifest_v0.json"
    )


def test_full_suite_readiness_identifies_current_gate():
    payload = _read_report()

    assert payload["protected_stack"]["ready"] is True
    assert payload["protected_stack"]["clean_stack_adopted"] is True
    assert payload["protected_stack"]["clean_stack_adopted_and_validated"] is True
    assert payload["protected_stack"]["post_adoption_validation_required"] is True
    assert payload["protected_stack"]["rollback_paths_preserved"] is True
    assert payload["protected_stack"]["active_stack_path_status"]["all_paths_safe"] is True
    assert payload["protected_stack"]["active_stack_path_status"]["all_paths_exist"] is True
    assert payload["protected_stack"]["rollback_stack_path_status"]["all_paths_safe"] is True
    assert payload["protected_stack"]["rollback_stack_path_status"]["all_paths_exist"] is True
    assert payload["protected_stack"]["rollback_common_paths_distinct"] is True
    assert payload["protected_stack"]["m1_m4_preservation_passed"] is True
    assert payload["protected_stack"]["kpk_kqk_bridge_preservation_passed"] is True

    stage7 = payload["stage7_sampling_gate"]
    assert stage7["runner_status"] == "stage7_diverse_clean_sampling_runner_executed_success"
    assert stage7["processed_job_count"] == 0
    assert stage7["executed_job_count"] == 0
    assert stage7["historical_processed_job_count"] == 8
    assert stage7["historical_executed_job_count"] == 8
    assert stage7["output_validation_status"] == (
        "stage7_diverse_clean_sampling_outputs_valid_ready_for_integration"
    )
    assert stage7["runner_output_validation_status"] == (
        "stage7_diverse_clean_sampling_outputs_valid_ready_for_integration"
    )
    assert stage7["output_valid_count"] == 8
    assert stage7["execution_readiness_source"] == "live_recomputed"
    assert (
        stage7["execution_readiness_status"]
        == "not_applicable_stage7_success_gate_closed"
    )
    assert (
        stage7["historical_execution_readiness_status"]
        == "stage7_diverse_clean_sampling_execution_ready_pending_explicit_approval"
    )
    assert stage7["execution_readiness_jobs_passing"] == 8
    assert stage7["invalid_existing_output_count"] == 0
    assert stage7["job_timeout_seconds"] == 900
    assert stage7["timed_out_job_count"] == 0
    assert stage7["overwrite_existing_outputs"] is False
    assert stage7["success_controls_ready"] is True
    assert stage7["label_gate_status"] == "stage7_success_gate_closed_no_current_label_approval"
    assert stage7["label_run_allowed_by_artifact"] is False
    assert stage7["historical_label_run_allowed_by_runner"] is True
    assert stage7["combined_success_controls"] == 11
    assert stage7["combined_success_controls"] >= stage7["success_controls_required"]

    stage4 = payload["stage_status"]["stage4"]
    assert (
        stage4["status"]
        == "stage4_caveat_unblocker_ready_pending_explicit_runtime_approval"
    )
    assert stage4["ready_for_explicit_runtime_approval"] is True
    assert stage4["implementation_allowed_by_current_artifact"] is False
    assert stage4["approval_request_artifact"] == (
        "reports/krk_stage4_first_move_contrast_sandbox_approval_request_v0.json"
    )
    assert (
        stage4["approval_request_status"]
        == "stage4_first_move_contrast_sandbox_approval_request_ready"
    )
    assert stage4["approval_request_blockers"] == []
    assert stage4["approval_request_ready_for_runtime_approval"] is True
    assert stage4["approval_request_created"] is False
    assert stage4["implementation_authorized_by_approval_request"] is False

    assert (
        payload["decision"]["status"]
        == "krk_suite_readiness_waiting_on_explicit_protected_failure_contrast_collection"
    )
    assert payload["hard_blockers"] == []
    assert payload["explicit_gate_blockers"] == [
        "protected_plan_window_failure_contrast_collection_pending_explicit_approval"
    ]
    assert payload["blockers"] == payload["explicit_gate_blockers"]
    assert payload["stage_status"]["stage8"]["blocker"] == (
        "Protected plan-window failure-contrast evidence is not integrated; "
        "Stage 8 remains blocked pending explicit protected failure-contrast "
        "collection and passive integration."
    )
    assert payload["approval_gates"]["stage8_training"]["why"] == (
        "Protected plan-window failure-contrast evidence is not integrated; "
        "Stage 8 training remains blocked even though Stage 7 held-out controls "
        "are balanced."
    )
    assert payload["current_control_plane_gate"]["selector_allowed"] is False
    assert payload["current_control_plane_gate"]["runtime_direct_routing"] is False
    assert payload["current_control_plane_gate"]["hidden_python_controller"] is False

    sequence = payload["sequence_policy"]
    assert (
        sequence["benchmark_design_status"]
        == "sequence_policy_benchmark_design_ready_non_causal"
    )
    assert (
        sequence["post_failure_contrast_refresh_status"]
        == "sequence_policy_after_protected_failure_contrast_refresh_waiting_on_integration_outputs"
    )
    assert (
        sequence["post_failure_contrast_refresh_next_step"]
        == "obtain_matching_approval_receipt_before_protected_failure_contrast_collection"
    )
    assert sequence["post_failure_contrast_refresh_boundaries_preserved"] is True
    assert sequence["post_failure_contrast_refresh_boundary_violation_count"] == 0
    assert (
        sequence["post_failure_contrast_refresh_integration_status"]
        == "protected_plan_window_failure_contrast_integration_pending_outputs"
    )
    assert sequence["post_failure_contrast_refresh_integration_ready"] is False
    assert sequence["post_failure_contrast_refresh_integrated_new_failure_count"] == 0
    assert sequence["post_failure_contrast_refresh_row_count"] == 0
    assert sequence["post_failure_contrast_refresh_stage7_training_row_count"] == 0
    assert (
        sequence["passive_design_without_new_labels_status"]
        == "non_causal_sequence_policy_design_without_new_labels_ready"
    )
    assert (
        sequence["passive_design_current_evidence_limit"]
        == "protected_plan_window_failure_evidence_sparse"
    )
    assert sequence["passive_design_depends_on_new_label_execution"] is False
    assert (
        sequence["passive_design_depends_on_protected_failure_contrast_collection"]
        is False
    )
    assert (
        sequence["cross_stage_requirements_status"]
        == "cross_stage_plan_capsule_evidence_ready_for_non_causal_benchmark"
    )
    assert sequence["replay_free_protected_cross_stage_evidence"] is True
    assert sequence["cross_stage_sequence_evidence_met"] is True

    protected_failure_contrast = payload["protected_failure_contrast_gate"]
    assert (
        protected_failure_contrast["plan_status"]
        == "protected_plan_window_failure_contrast_plan_ready_pending_explicit_collection_approval"
    )
    assert protected_failure_contrast["unique_failure_count"] == 1
    assert protected_failure_contrast["minimum_new_failures_needed"] == 4
    assert (
        protected_failure_contrast["manifest_status"]
        == "protected_plan_window_failure_contrast_manifest_ready_for_review"
    )
    assert protected_failure_contrast["manifest_job_count"] == 6
    assert (
        protected_failure_contrast["manifest_review_status"]
        == "protected_plan_window_failure_contrast_manifest_review_passed_pending_explicit_approval"
    )
    assert (
        protected_failure_contrast["execution_readiness_status"]
        == "protected_plan_window_failure_contrast_execution_ready_pending_explicit_approval"
    )
    assert protected_failure_contrast["execution_jobs_passing"] == 6
    assert (
        protected_failure_contrast["runner_status"]
        == "protected_plan_window_failure_contrast_runner_dry_run_ready"
    )
    assert (
        protected_failure_contrast["runner_manifest_status"]
        == "protected_plan_window_failure_contrast_manifest_ready_for_review"
    )
    assert protected_failure_contrast["runner_manifest_declared_job_count"] == 6
    assert len(protected_failure_contrast["runner_manifest_fingerprint"]) == 64
    assert protected_failure_contrast["runner_collection_run_allowed"] is False
    assert protected_failure_contrast["runner_processed_job_count"] == 0
    assert protected_failure_contrast["runner_executed_job_count"] == 0
    assert (
        protected_failure_contrast["output_validation_status"]
        == "protected_plan_window_failure_contrast_outputs_validation_pending"
    )
    assert protected_failure_contrast["output_exists_count"] == 0
    assert protected_failure_contrast["output_valid_count"] == 0
    assert (
        protected_failure_contrast["integration_status"]
        == "protected_plan_window_failure_contrast_integration_pending_outputs"
    )
    assert protected_failure_contrast["integrated_new_failure_count"] == 0
    assert protected_failure_contrast["integration_ready"] is False
    assert protected_failure_contrast["ready_for_explicit_approval"] is True
    assert protected_failure_contrast["approval_request_ready_for_collection"] is True
    assert protected_failure_contrast["current_artifact_allows_collection"] is False
    assert protected_failure_contrast["approval_receipt_required"] is True
    assert protected_failure_contrast["approval_receipt_path"] == (
        "reports/strategy_arbitration/"
        "krk_protected_plan_window_failure_contrast_collection_approval_v0.json"
    )
    assert protected_failure_contrast["approval_receipt_present"] is False
    assert protected_failure_contrast["approval_receipt_valid"] is False
    assert protected_failure_contrast["approval_receipt_blockers"] == [
        "approval_receipt_missing"
    ]
    assert protected_failure_contrast["approval_request_artifact"] == (
        "reports/strategy_arbitration/"
        "krk_protected_plan_window_failure_contrast_approval_request_v0.json"
    )
    assert (
        protected_failure_contrast["approval_request_status"]
        == "protected_plan_window_failure_contrast_approval_request_ready"
    )
    assert protected_failure_contrast["approval_request_blockers"] == []
    assert protected_failure_contrast["approval_receipt_created_by_request"] is False
    assert protected_failure_contrast["post_success_refresh_required"] is True
    assert protected_failure_contrast["post_success_refresh_script"] == (
        "scripts/advance_krk_suite_from_current_gates_v0.py"
    )
    assert protected_failure_contrast["post_success_refresh_scope"] == (
        "full_passive_krk_suite_gate_stack"
    )
    assert len(protected_failure_contrast["expected_manifest_fingerprint"]) == 64
    assert len(protected_failure_contrast["expected_readiness_fingerprint"]) == 64
    assert protected_failure_contrast["command_if_explicitly_approved"] == (
        "UV_CACHE_DIR=/tmp/uv-cache uv run python "
        "scripts/run_krk_protected_plan_window_failure_contrast_collection_v0.py "
        "--execute-reviewed-collection --refresh-after-run "
        "--approval-receipt "
        "reports/strategy_arbitration/"
        "krk_protected_plan_window_failure_contrast_collection_approval_v0.json"
    )
    assert protected_failure_contrast["runtime_behavior_changed"] is False
    assert protected_failure_contrast["runtime_defaults_changed"] is False
    assert protected_failure_contrast["runtime_selector_implemented"] is False
    assert protected_failure_contrast["runtime_score_changes"] is False
    assert protected_failure_contrast["runtime_direct_routing"] is False
    assert protected_failure_contrast["runtime_dtm_or_tablebase_lookup"] is False
    assert protected_failure_contrast["hidden_python_controller"] is False
    assert protected_failure_contrast["gameplay_topology_mutation"] is False
    assert protected_failure_contrast["selector_training_allowed"] is False
    assert protected_failure_contrast["stage7_promotion_allowed"] is False
    assert protected_failure_contrast["stage8_training_allowed"] is False


def test_full_suite_readiness_writer_helpers_are_deterministic():
    payload = _audit.build_payload()
    rendered = _audit.write_markdown(payload)

    assert payload["decision"]["runtime_changes_allowed"] is False
    assert payload["stage_status"]["stage7"]["ready_for_promotion"] is False
    assert payload["stage_status"]["stage7"]["sampling_runner_invalid_existing_output_count"] == 0
    assert payload["stage_status"]["stage7"]["sampling_runner_timed_out_job_count"] == 0
    assert (
        payload["stage_status"]["stage7"]["sampling_runner_execution_readiness_source"]
        == "live_recomputed"
    )
    assert payload["stage_status"]["stage8"]["ready_for_training"] is False
    assert (
        payload["approval_gates"]["stage4_first_move_contrast_sandbox"]["status"]
        == "stage4_caveat_unblocker_ready_pending_explicit_runtime_approval"
    )
    assert (
        payload["approval_gates"]["stage4_first_move_contrast_sandbox"][
            "approval_request_status"
        ]
        == "stage4_first_move_contrast_sandbox_approval_request_ready"
    )
    assert (
        payload["approval_gates"]["stage4_first_move_contrast_sandbox"][
            "approval_request_blockers"
        ]
        == []
    )
    assert (
        payload["approval_gates"]["stage4_first_move_contrast_sandbox"][
            "approval_request_ready_for_runtime_approval"
        ]
        is True
    )
    assert (
        payload["approval_gates"]["stage4_first_move_contrast_sandbox"][
            "implementation_authorized_by_approval_request"
        ]
        is False
    )
    stage4_scope = payload["approval_gates"]["stage4_first_move_contrast_sandbox"][
        "safety_scope"
    ]
    assert (
        stage4_scope["sandbox_scope_id"]
        == "default_off_stage4_candidate_move_first_move_contrast_sandbox_only"
    )
    assert stage4_scope["approval_request_blockers"] == []
    assert stage4_scope["approval_request_ready_for_runtime_approval"] is True
    assert stage4_scope["default_off"] is True
    assert stage4_scope["default_enabled"] is False
    assert stage4_scope["implementation_authorized_by_request"] is False
    assert stage4_scope["runtime_change_class"] == "default_off_candidate_move_frame_sandbox_only"
    assert stage4_scope["exact_state_or_exact_move_exception"] is False
    assert stage4_scope["runtime_dtm_or_tablebase_lookup"] is False
    assert stage4_scope["hidden_python_controller"] is False
    assert stage4_scope["selector_training_allowed"] is False
    assert stage4_scope["gameplay_topology_mutation"] is False
    assert stage4_scope["stage7_promotion_allowed"] is False
    assert stage4_scope["stage8_training_allowed"] is False
    assert (
        stage4_scope["readiness_audit"]
        == "reports/krk_full_suite_readiness_audit_v0.json"
    )
    assert stage4_scope["readiness_checked_flag_count"] >= 430
    assert stage4_scope["readiness_boundary_violation_count"] == 0
    assert stage4_scope["readiness_source_artifact_count"] >= 44
    assert (
        payload["approval_gates"]["protected_plan_window_failure_contrast_collection"][
            "ready_for_explicit_approval"
        ]
        is True
    )
    assert (
        payload["approval_gates"]["protected_plan_window_failure_contrast_collection"][
            "approval_request_ready_for_collection"
        ]
        is True
    )
    assert (
        payload["approval_gates"]["protected_plan_window_failure_contrast_collection"][
            "post_success_refresh_required"
        ]
        is True
    )
    assert (
        payload["approval_gates"]["protected_plan_window_failure_contrast_collection"][
            "post_success_refresh_script"
        ]
        == "scripts/advance_krk_suite_from_current_gates_v0.py"
    )
    assert "krk_suite_readiness_waiting_on_explicit_protected_failure_contrast_collection" in rendered
    assert "protected_plan_window_failure_contrast_runner_dry_run_ready" in rendered
    assert "approval_receipt_blockers: `['approval_receipt_missing']`" in rendered
    assert (
        "approval_request_status: "
        "`protected_plan_window_failure_contrast_approval_request_ready`"
        in rendered
    )
    assert "approval_receipt_created_by_request: `False`" in rendered
    assert "post_success_refresh_required: `True`" in rendered
    assert (
        "post_success_refresh_script: "
        "`scripts/advance_krk_suite_from_current_gates_v0.py`"
        in rendered
    )
    assert "post_success_refresh_scope: `full_passive_krk_suite_gate_stack`" in rendered
    assert "runtime_behavior_changed: `False`" in rendered
    assert "runtime_defaults_changed: `False`" in rendered
    assert "runtime_selector_implemented: `False`" in rendered
    assert "runtime_score_changes: `False`" in rendered
    assert "runtime_direct_routing: `False`" in rendered
    assert "runtime_dtm_or_tablebase_lookup: `False`" in rendered
    assert "hidden_python_controller: `False`" in rendered
    assert "gameplay_topology_mutation: `False`" in rendered
    assert "selector_training_allowed: `False`" in rendered
    assert "stage7_promotion_allowed: `False`" in rendered
    assert "stage8_training_allowed: `False`" in rendered
    assert (
        "passive_design_without_new_labels_status: "
        "`non_causal_sequence_policy_design_without_new_labels_ready`"
        in rendered
    )
    assert (
        "post_failure_contrast_refresh_status: "
        "`sequence_policy_after_protected_failure_contrast_refresh_waiting_on_integration_outputs`"
        in rendered
    )
    assert "post_failure_contrast_refresh_boundaries_preserved: `True`" in rendered
    assert "post_failure_contrast_refresh_row_count: `0`" in rendered
    assert (
        "approval_request_status: "
        "`stage4_first_move_contrast_sandbox_approval_request_ready`"
        in rendered
    )
    assert "approval_request_created: `False`" in rendered
    assert "label_run_allowed: `false`" in rendered


def test_full_suite_readiness_routes_forbidden_training_rows_to_input_repair(monkeypatch):
    real_load_json = _audit.load_json

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
        return payload

    monkeypatch.setattr(_audit, "load_json", tainted_load_json)

    payload = _audit.build_payload()

    assert (
        payload["decision"]["status"]
        == "krk_suite_readiness_blocked_forbidden_training_or_runtime_rows"
    )
    assert (
        payload["decision"]["recommended_next_step"]
        == "repair_sequence_policy_inputs_remove_training_or_runtime_rows"
    )
    assert "sequence_policy_forbidden_training_or_runtime_rows" in payload["hard_blockers"]
    assert payload["sequence_policy"]["forbidden_training_or_runtime_input_blocked"] is True
    assert payload["protected_failure_contrast_gate"]["ready_for_explicit_approval"] is False
    assert payload["protected_failure_contrast_gate"]["command_if_explicitly_approved"] is None
    assert (
        payload["approval_gates"]["protected_plan_window_failure_contrast_collection"][
            "ready_for_explicit_approval"
        ]
        is False
    )
    assert payload["decision"]["selector_training_allowed"] is False


def test_full_suite_readiness_routes_blocked_protected_collection_request_to_repair(monkeypatch):
    real_load_json = _audit.load_json

    def tainted_load_json(relative: str):
        payload = json.loads(json.dumps(real_load_json(relative)))
        if (
            relative
            == "reports/strategy_arbitration/"
            "krk_protected_plan_window_failure_contrast_approval_request_v0.json"
        ):
            payload.setdefault("decision", {})["status"] = (
                "protected_plan_window_failure_contrast_approval_request_blocked"
            )
            payload["blockers"] = ["full_suite_readiness_audit_not_clean"]
            payload["approval_request_ready_for_collection"] = False
        return payload

    monkeypatch.setattr(_audit, "load_json", tainted_load_json)

    payload = _audit.build_payload()
    gate = payload["protected_failure_contrast_gate"]

    assert gate["approval_request_status"] == (
        "protected_plan_window_failure_contrast_approval_request_blocked"
    )
    assert gate["approval_request_blockers"] == [
        "full_suite_readiness_audit_not_clean"
    ]
    assert gate["approval_request_ready_for_collection"] is False
    assert gate["ready_for_explicit_approval"] is False
    assert gate["command_if_explicitly_approved"] is None
    assert (
        "protected_plan_window_failure_contrast_approval_request_blocked"
        in payload["hard_blockers"]
    )
    assert payload["explicit_gate_blockers"] == []
    assert (
        payload["decision"]["status"]
        == "krk_suite_readiness_blocked_pending_protected_failure_contrast_approval_request_repair"
    )
    assert (
        payload["decision"]["recommended_next_step"]
        == "repair_protected_failure_contrast_approval_request_scope"
    )
    assert (
        payload["approval_gates"]["protected_plan_window_failure_contrast_collection"][
            "ready_for_explicit_approval"
        ]
        is False
    )
    assert (
        payload["approval_gates"]["protected_plan_window_failure_contrast_collection"][
            "approval_request_ready_for_collection"
        ]
        is False
    )
    assert payload["decision"]["runtime_changes_allowed"] is False


def test_full_suite_readiness_gates_stage4_runtime_on_approval_request_not_ready(monkeypatch):
    real_load_json = _audit.load_json

    def tainted_load_json(relative: str):
        payload = json.loads(json.dumps(real_load_json(relative)))
        if relative == "reports/krk_stage4_first_move_contrast_sandbox_approval_request_v0.json":
            payload.setdefault("decision", {})["status"] = (
                "stage4_first_move_contrast_sandbox_approval_request_ready"
            )
            payload["blockers"] = []
            payload["approval_request_ready_for_runtime_approval"] = False
        return payload

    monkeypatch.setattr(_audit, "load_json", tainted_load_json)

    payload = _audit.build_payload()
    stage4 = payload["stage_status"]["stage4"]
    stage4_gate = payload["approval_gates"]["stage4_first_move_contrast_sandbox"]

    assert stage4["ready_for_explicit_runtime_approval"] is False
    assert stage4["approval_request_ready_for_runtime_approval"] is False
    assert stage4["approval_request_blockers"] == []
    assert stage4_gate["ready_for_explicit_approval"] is False
    assert stage4_gate["approval_request_ready_for_runtime_approval"] is False
    assert (
        stage4_gate["safety_scope"]["approval_request_ready_for_runtime_approval"]
        is False
    )
    assert payload["decision"]["runtime_changes_allowed"] is False


def test_full_suite_readiness_blocks_post_failure_refresh_boundary_violation(monkeypatch):
    real_load_json = _audit.load_json

    def tainted_load_json(relative: str):
        payload = json.loads(json.dumps(real_load_json(relative)))
        if (
            relative
            == "reports/strategy_arbitration/"
            "krk_sequence_policy_after_protected_failure_contrast_refresh_v0.json"
        ):
            payload.setdefault("summary", {})["all_boundaries_preserved"] = False
            payload.setdefault("summary", {})["boundary_violation_count"] = 1
            payload.setdefault("summary", {})["boundary_violations"] = [
                {
                    "step_id": "sequence_policy_benchmark",
                    "field": "runtime_changes_allowed",
                    "script": "scripts/run_krk_sequence_policy_benchmark_v0.py",
                }
            ]
            payload.setdefault("decision", {})["status"] = (
                "sequence_policy_after_protected_failure_contrast_refresh_blocked_boundary_violation"
            )
        return payload

    monkeypatch.setattr(_audit, "load_json", tainted_load_json)

    payload = _audit.build_payload()

    assert payload["sequence_policy"][
        "post_failure_contrast_refresh_boundaries_preserved"
    ] is False
    assert (
        payload["sequence_policy"][
            "post_failure_contrast_refresh_boundary_violation_count"
        ]
        == 1
    )
    assert (
        "post_failure_contrast_sequence_refresh_boundary_violation"
        in payload["hard_blockers"]
    )
    assert payload["decision"]["status"].startswith("krk_suite_readiness_blocked")
    assert payload["decision"]["runtime_changes_allowed"] is False
    assert payload["decision"]["stage8_training_allowed"] is False


def test_full_suite_readiness_blocks_unsafe_protected_stack_paths(monkeypatch):
    real_load_json = _audit.load_json

    def tainted_load_json(relative: str):
        payload = json.loads(json.dumps(real_load_json(relative)))
        if relative == "reports/krk_active_protected_stack_v0.json":
            payload["active_protected_stack"]["stage6_drive_overlay"][
                "topology"
            ] = "../unsafe_topology.json"
        if (
            relative
            == "reports/strategy_arbitration/"
            "krk_protected_plan_window_failure_contrast_approval_request_v0.json"
        ):
            payload.setdefault("decision", {})["status"] = (
                "protected_plan_window_failure_contrast_approval_request_blocked"
            )
            payload["blockers"] = ["full_suite_readiness_audit_not_clean"]
            payload["approval_request_ready_for_collection"] = False
        return payload

    monkeypatch.setattr(_audit, "load_json", tainted_load_json)

    payload = _audit.build_payload()

    assert payload["protected_stack"]["ready"] is False
    assert payload["protected_stack"]["active_stack_path_status"]["all_paths_safe"] is False
    assert "stage6_drive_overlay.topology" in payload["protected_stack"][
        "active_stack_path_status"
    ]["unsafe_paths"]
    assert "protected_retry1_stage5_6_stack_not_validated" in payload["hard_blockers"]
    assert (
        "protected_plan_window_failure_contrast_approval_request_blocked"
        not in payload["hard_blockers"]
    )
    assert payload["explicit_gate_blockers"] == []
    assert payload["protected_failure_contrast_gate"]["ready_for_explicit_approval"] is False
    assert (
        payload["protected_failure_contrast_gate"]["command_if_explicitly_approved"]
        is None
    )
    assert (
        payload["decision"]["status"]
        == "krk_suite_readiness_blocked_pending_protected_stack_repair"
    )
    assert (
        payload["decision"]["recommended_next_step"]
        == "repair_protected_stack_validation"
    )
    assert payload["decision"]["runtime_changes_allowed"] is False
