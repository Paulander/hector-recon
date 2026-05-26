#!/usr/bin/env python3
"""Tests for KRK sequence-control contrast dataset/probe artifacts."""

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


_dataset = _load_module(
    "build_krk_sequence_control_contrast_dataset_v0",
    "scripts/build_krk_sequence_control_contrast_dataset_v0.py",
)
_probe = _load_module(
    "probe_krk_sequence_control_contrast_v0",
    "scripts/probe_krk_sequence_control_contrast_v0.py",
)
_current_gate = _load_module(
    "write_krk_current_control_plane_gate_v0",
    "scripts/write_krk_current_control_plane_gate_v0.py",
)


def _read_report(path: str) -> dict:
    payload = json.loads((ROOT / path).read_text(encoding="utf-8"))
    assert isinstance(payload, dict)
    return payload


def test_sequence_control_contrast_dataset_is_non_causal_and_mixed_scope():
    payload = _read_report(
        "reports/strategy_arbitration/krk_sequence_control_contrast_dataset_v0.json"
    )

    assert payload["schema_version"] == "krk_sequence_control_contrast_dataset.v0"
    assert payload["causal_status"] == "non_causal_sequence_control_contrast_dataset"
    assert payload["runtime_behavior_changed"] is False
    assert payload["runtime_selector_implemented"] is False
    assert payload["runtime_score_changes"] is False
    assert payload["runtime_direct_routing"] is False
    assert payload["runtime_dtm_or_tablebase_lookup"] is False
    assert payload["gameplay_topology_mutation"] is False
    assert payload["stage7_promotion_allowed"] is False
    assert payload["stage8_training_allowed"] is False
    assert payload["summary"]["row_count"] == 76
    assert payload["summary"]["row_type_counts"]["forced_first_move_candidate"] == 48
    assert payload["summary"]["row_type_counts"]["ownership_seed_context"] == 18
    assert payload["summary"]["row_type_counts"]["stage7_clean_sequence_control"] == 10
    assert payload["summary"]["stage7_heldout_row_count"] == 10
    assert payload["summary"]["selector_training_row_count"] == 0
    assert payload["summary"]["runtime_authorization_row_count"] == 0
    assert payload["label_semantics"]["forced_first_move_capacity_is_not_runtime_ownership"] is True
    assert payload["label_semantics"]["stage7_rows_are_heldout_challenge_only"] is True
    assert payload["stage4_review_gate"]["runtime_review_ready"] is True
    assert payload["stage4_review_gate"]["implementation_authorized_by_packet"] is False
    assert payload["decision"]["runtime_changes_allowed"] is False


def test_sequence_control_contrast_probe_keeps_stage8_blocked():
    payload = _read_report(
        "reports/strategy_arbitration/krk_sequence_control_contrast_probe_v0.json"
    )

    assert payload["schema_version"] == "krk_sequence_control_contrast_probe.v0"
    assert payload["causal_status"] == "non_causal_sequence_control_contrast_probe"
    assert payload["runtime_behavior_changed"] is False
    assert payload["runtime_selector_implemented"] is False
    assert payload["runtime_score_changes"] is False
    assert payload["runtime_direct_routing"] is False
    assert payload["stage7_promotion_allowed"] is False
    assert payload["stage8_training_allowed"] is False
    assert (
        payload["decision"]["status"]
        == "sequence_control_dataset_ready_for_broader_sequence_policy_review"
    )
    assert (
        payload["decision"]["recommended_next_step"]
        == "review_current_sequence_policy_benchmark_and_protected_failure_contrast_gate"
    )
    assert payload["readiness"]["stage4_first_move_contrast_sandbox_review_ready"] is True
    assert payload["readiness"]["stage7_sequence_policy_benchmark_ready"] is True
    assert payload["readiness"]["broader_runtime_selector_ready"] is False
    assert payload["readiness"]["stage8_training_ready"] is False
    assert payload["summary"]["stage7_dataset_success_control_count"] == 2
    assert payload["summary"]["stage7_dataset_failure_control_count"] == 8
    assert payload["summary"]["stage7_success_control_count"] == 11
    assert payload["summary"]["stage7_success_controls_required"] == 5
    assert payload["summary"]["stage7_failure_control_count"] == 39
    assert payload["summary"]["stage7_failure_controls_required"] == 5
    assert payload["summary"]["stage7_success_controls_met"] is True
    assert payload["summary"]["stage7_rows_are_current_gate_evidence_not_promotion"] is True
    assert (
        "Stage 7 clean success controls are satisfied in the integrated current gate; "
        "Stage 7 remains held out and not promoted."
    ) in payload["blockers"]
    assert payload["decision"]["runtime_changes_allowed"] is False
    assert payload["decision"]["selector_training_allowed"] is False


def test_sequence_control_contrast_dataset_fixture_preserves_semantics():
    stage4 = {
        "variants": [
            {
                "variant_id": "identity",
                "rows": [
                    {
                        "fen": "1R6/1K6/8/k7/8/8/8/8 w - - 0 1",
                        "first_move": "b8h8",
                        "result": "max_plies",
                        "selected_analog": True,
                        "canonical_features": {"rook_far_rank8_drift_candidate": True},
                    }
                ],
            }
        ]
    }
    seed = {
        "seed_rows": [
            {
                "state_id": "state.safe",
                "source_stage": "stage5",
                "selected_provider_family": "stage0_basin",
                "objective_channel": "safe_preservation_contrast_seed",
            }
        ]
    }
    stage7 = {
        "controls": [
            {
                "state_id": "clean.fail",
                "fen": "8/8/8/8/8/8/8/8 w - - 0 1",
                "result": "max_plies",
                "control_role": "clean_sequence_hard_negative",
            }
        ]
    }
    packet = {
        "decision": {
            "status": "packet",
            "runtime_review_ready": True,
            "implementation_authorized_by_this_packet": False,
        }
    }

    payload = _dataset.build_payload(stage4=stage4, seed=seed, stage7=stage7, packet=packet)

    assert payload["summary"]["row_count"] == 3
    assert payload["summary"]["selector_training_row_count"] == 0
    assert payload["summary"]["runtime_authorization_row_count"] == 0
    assert payload["stage4_review_gate"]["runtime_review_ready"] is True
    assert payload["stage4_review_gate"]["implementation_authorized_by_packet"] is False
    assert payload["rows"][-1]["stage7_heldout_challenge"] is True


def test_sequence_control_contrast_probe_fixture_detects_stage7_success_gap():
    dataset = {
        "stage4_review_gate": {
            "runtime_review_ready": True,
            "implementation_authorized_by_packet": False,
        },
        "summary": {
            "selector_training_row_count": 0,
            "runtime_authorization_row_count": 0,
        },
        "rows": [
            {
                "row_type": "forced_first_move_candidate",
                "source_stage": "stage4",
                "target_label": "conversion_positive",
            },
            {
                "row_type": "ownership_seed_context",
                "source_stage": "stage5",
                "target_label": "candidate_switch_contrast_seed",
            },
            {
                "row_type": "ownership_seed_context",
                "source_stage": "stage5",
                "target_label": "safe_preservation_contrast_seed",
            },
            {
                "row_type": "stage7_clean_sequence_control",
                "source_stage": "stage7",
                "target_label": "conversion_failure",
            },
        ],
    }

    payload = _probe.build_payload(dataset=dataset, stage7_integration={"summary": {}})

    assert (
        payload["decision"]["status"]
        == "sequence_control_stage4_review_ready_stage7_success_controls_insufficient"
    )
    assert payload["readiness"]["stage8_training_ready"] is False
    assert payload["decision"]["runtime_changes_allowed"] is False


def test_current_control_plane_gate_requires_explicit_choice():
    payload = _read_report("reports/krk_current_control_plane_gate_v0.json")

    assert payload["schema_version"] == "krk_current_control_plane_gate.v0"
    assert payload["causal_status"] == "non_causal_current_gate_summary"
    assert payload["runtime_behavior_changed"] is False
    assert payload["runtime_selector_implemented"] is False
    assert payload["runtime_score_changes"] is False
    assert payload["runtime_direct_routing"] is False
    assert payload["runtime_dtm_or_tablebase_lookup"] is False
    assert payload["gameplay_topology_mutation"] is False
    assert payload["stage7_promotion_allowed"] is False
    assert payload["stage8_training_allowed"] is False
    assert payload["decision"]["status"] == "krk_control_plane_waiting_on_explicit_gate_choice"
    assert payload["decision"]["runtime_changes_allowed"] is False
    assert payload["decision"]["label_run_allowed"] is False
    assert payload["decision"]["stage7_promotion_allowed"] is False
    assert payload["decision"]["stage8_training_allowed"] is False
    assert payload["current_state"]["protected_stack_ready"] is True
    assert (
        payload["current_state"]["protected_stack_readiness_status"]
        == "retry1_protected_stage5_6_stack_adopted_manifest_only"
    )
    assert payload["current_state"]["protected_stack_rollback_paths_preserved"] is True
    assert payload["current_state"]["protected_stack_active_paths_safe"] is True
    assert payload["current_state"]["protected_stack_active_paths_exist"] is True
    assert payload["current_state"]["protected_stack_rollback_paths_safe"] is True
    assert payload["current_state"]["protected_stack_rollback_paths_exist"] is True
    assert (
        payload["current_state"]["protected_stack_rollback_common_paths_distinct"]
        is True
    )
    assert (
        payload["current_state"]["protected_stack_filesystem_snapshots_replaced"]
        is False
    )
    assert payload["current_state"]["protected_stack_hard_blockers"] == []
    option_ids = {option["option_id"] for option in payload["approval_options"]}
    assert option_ids == {
        "approve_stage4_first_move_contrast_sandbox",
        "approve_protected_plan_window_failure_contrast_collection",
    }
    stage4_option = [
        option
        for option in payload["approval_options"]
        if option["option_id"] == "approve_stage4_first_move_contrast_sandbox"
    ][0]
    assert stage4_option["approval_request_artifact"] == (
        "reports/krk_stage4_first_move_contrast_sandbox_approval_request_v0.md"
    )
    assert (
        stage4_option["approval_request_status"]
        == "stage4_first_move_contrast_sandbox_approval_request_ready"
    )
    assert stage4_option["approval_request_created"] is False
    assert (
        payload["current_state"]["sequence_policy"]
        == "sequence_policy_benchmark_mixed_plan_window_underpowered"
    )
    assert (
        payload["current_state"]["sequence_policy_passive_design_without_new_labels"]
        == "non_causal_sequence_policy_design_without_new_labels_ready"
    )
    assert (
        payload["current_state"]["sequence_policy_passive_design_current_evidence_limit"]
        == "protected_plan_window_failure_evidence_sparse"
    )
    assert (
        payload["current_state"][
            "sequence_policy_passive_design_depends_on_new_label_execution"
        ]
        is False
    )
    assert (
        payload["current_state"][
            "sequence_policy_passive_design_depends_on_protected_failure_contrast_collection"
        ]
        is False
    )
    assert (
        payload["current_state"]["sequence_policy_cross_stage_requirements"]
        == "cross_stage_plan_capsule_evidence_ready_for_non_causal_benchmark"
    )
    assert (
        payload["current_state"][
            "sequence_policy_replay_free_protected_cross_stage_evidence"
        ]
        is True
    )
    assert (
        payload["current_state"]["sequence_policy_cross_stage_sequence_evidence_met"]
        is True
    )
    assert (
        payload["current_state"]["sequence_policy_inputs"]
        == "sequence_policy_benchmark_inputs_ready_non_causal"
    )
    assert payload["current_state"]["stage7_success_controls_ready"] is True
    assert payload["current_state"]["stage7_success_controls"] == 11
    assert payload["current_state"]["stage7_success_controls_required"] == 5
    assert (
        payload["current_state"]["stage7_label_execution_readiness"]
        == "not_applicable_stage7_success_gate_closed"
    )
    assert (
        payload["current_state"]["stage7_label_historical_execution_readiness"]
        == "stage7_diverse_clean_sampling_execution_ready_pending_explicit_approval"
    )
    assert (
        payload["current_state"]["stage7_label_output_integration"]
        == "stage7_diverse_clean_sampling_integration_success_controls_met"
    )
    assert (
        payload["current_state"]["stage7_label_runner"]
        == "stage7_diverse_clean_sampling_runner_executed_success"
    )
    assert (
        payload["current_state"]["stage7_label_runner_output_validation_status"]
        == "stage7_diverse_clean_sampling_outputs_valid_ready_for_integration"
    )
    assert (
        payload["current_state"]["stage7_label_output_validation_status"]
        == "stage7_diverse_clean_sampling_outputs_valid_ready_for_integration"
    )
    assert payload["current_state"]["stage7_label_runner_invalid_existing_output_count"] == 0
    assert (
        payload["current_state"]["stage7_label_runner_execution_readiness_status"]
        == "not_applicable_stage7_success_gate_closed"
    )
    assert (
        payload["current_state"][
            "stage7_label_runner_historical_execution_readiness_status"
        ]
        == "stage7_diverse_clean_sampling_execution_ready_pending_explicit_approval"
    )
    assert payload["current_state"]["stage7_label_runner_processed_job_count"] == 0
    assert payload["current_state"]["stage7_label_runner_executed_job_count"] == 0
    assert payload["current_state"]["stage7_label_runner_historical_processed_job_count"] == 8
    assert payload["current_state"]["stage7_label_runner_historical_executed_job_count"] == 8
    assert payload["current_state"]["stage7_label_runner_skipped_existing_output_count"] == 0
    assert (
        payload["current_state"]["stage7_post_label_outcome"]
        == "post_label_outcome_waiting_on_explicit_protected_failure_contrast_collection"
    )
    assert (
        payload["current_state"]["stage7_label_distribution_review"]
        == "stage7_label_distribution_review_success_gate_closed"
    )
    assert (
        payload["current_state"]["stage7_additional_label_manifest"]
        == "stage7_additional_clean_sampling_manifest_not_applicable_success_gate_closed"
    )
    assert (
        payload["current_state"]["stage7_additional_label_runner"]
        == "stage7_additional_clean_sampling_runner_not_applicable_success_gate_closed"
    )
    assert payload["current_state"]["stage7_additional_label_runner_job_count"] == 0
    assert (
        payload["current_state"]["protected_plan_window_failure_contrast_plan"]
        == "protected_plan_window_failure_contrast_plan_ready_pending_explicit_collection_approval"
    )
    assert payload["current_state"]["protected_plan_window_unique_failure_count"] == 1
    assert payload["current_state"]["protected_plan_window_minimum_new_failures_needed"] == 4
    assert (
        payload["current_state"]["protected_plan_window_failure_contrast_manifest"]
        == "protected_plan_window_failure_contrast_manifest_ready_for_review"
    )
    assert payload["current_state"]["protected_plan_window_failure_contrast_manifest_job_count"] == 6
    assert (
        payload["current_state"]["protected_plan_window_failure_contrast_manifest_review"]
        == "protected_plan_window_failure_contrast_manifest_review_passed_pending_explicit_approval"
    )
    assert (
        payload["current_state"][
            "protected_plan_window_failure_contrast_execution_readiness"
        ]
        == "protected_plan_window_failure_contrast_execution_ready_pending_explicit_approval"
    )
    assert payload["current_state"]["protected_plan_window_failure_contrast_execution_jobs_passing"] == 6
    assert (
        payload["current_state"]["protected_plan_window_failure_contrast_runner"]
        == "protected_plan_window_failure_contrast_runner_dry_run_ready"
    )
    assert payload["current_state"]["protected_plan_window_failure_contrast_runner_processed_job_count"] == 0
    assert payload["current_state"]["protected_plan_window_failure_contrast_runner_executed_job_count"] == 0
    assert (
        payload["current_state"]["protected_plan_window_failure_contrast_approval_request"]
        == "protected_plan_window_failure_contrast_approval_request_ready"
    )
    assert (
        payload["current_state"][
            "protected_plan_window_failure_contrast_approval_receipt_created"
        ]
        is False
    )
    assert payload["current_state"][
        "protected_plan_window_failure_contrast_approval_receipt_blockers"
    ] == ["approval_receipt_missing"]
    assert (
        payload["current_state"]["protected_plan_window_failure_contrast_output_validation"]
        == "protected_plan_window_failure_contrast_outputs_validation_pending"
    )
    assert payload["current_state"]["protected_plan_window_failure_contrast_output_exists_count"] == 0
    assert payload["current_state"]["protected_plan_window_failure_contrast_output_valid_count"] == 0
    assert (
        payload["current_state"]["protected_plan_window_failure_contrast_integration"]
        == "protected_plan_window_failure_contrast_integration_pending_outputs"
    )
    assert (
        payload["current_state"][
            "protected_plan_window_failure_contrast_integrated_new_failure_count"
        ]
        == 0
    )
    assert payload["current_state"]["protected_plan_window_failure_contrast_integration_ready"] is False
    assert (
        payload["current_state"]["sequence_policy_after_protected_failure_contrast_refresh"]
        == "sequence_policy_after_protected_failure_contrast_refresh_waiting_on_integration_outputs"
    )
    assert payload["current_state"]["sequence_policy_after_protected_failure_contrast_rows"] == 0
    review_option = [
        option
        for option in payload["approval_options"]
        if option["option_id"] == "approve_protected_plan_window_failure_contrast_collection"
    ][0]
    assert (
        review_option["status"]
        == "protected_plan_window_failure_contrast_execution_ready_pending_explicit_approval"
    )
    assert review_option["command_if_explicitly_approved"] == (
        "UV_CACHE_DIR=/tmp/uv-cache uv run python "
        "scripts/run_krk_protected_plan_window_failure_contrast_collection_v0.py "
        "--execute-reviewed-collection --refresh-after-run "
        "--approval-receipt "
        "reports/strategy_arbitration/"
        "krk_protected_plan_window_failure_contrast_collection_approval_v0.json"
    )
    assert review_option["safety_scope"]["max_jobs"] == 6
    assert review_option["safety_scope"]["manifest_job_count"] == 6
    assert review_option["safety_scope"]["runner_max_jobs_option"] is None
    assert review_option["safety_scope"]["horizon"] == "h40"
    assert (
        review_option["safety_scope"]["stage"]
        == "protected_plan_window_failure_contrast_evidence_only"
    )
    assert (
        review_option["safety_scope"]["protected_stack_readiness_status"]
        == "retry1_protected_stage5_6_stack_adopted_manifest_only"
    )
    assert review_option["safety_scope"]["protected_stack_rollback_paths_preserved"] is True
    assert review_option["safety_scope"]["protected_stack_active_paths_safe"] is True
    assert review_option["safety_scope"]["protected_stack_active_paths_exist"] is True
    assert review_option["safety_scope"]["protected_stack_rollback_paths_safe"] is True
    assert review_option["safety_scope"]["protected_stack_rollback_paths_exist"] is True
    assert (
        review_option["safety_scope"]["protected_stack_rollback_common_paths_distinct"]
        is True
    )
    assert (
        review_option["safety_scope"]["protected_stack_filesystem_snapshots_replaced"]
        is False
    )
    assert review_option["safety_scope"]["source_stage_counts"] == {
        "stage4": 2,
        "stage5": 2,
        "stage6": 2,
    }
    assert review_option["safety_scope"]["stop_after_unique_failures"] == 4
    assert review_option["safety_scope"]["observation_only"] is True
    assert review_option["safety_scope"]["resume_safe"] is True
    assert review_option["safety_scope"]["skip_existing_outputs_by_default"] is True
    assert (
        review_option["safety_scope"]["invalid_existing_outputs_block_without_overwrite"]
        is True
    )
    assert review_option["safety_scope"]["execution_readiness_recomputed_live"] is True
    assert review_option["safety_scope"]["approval_receipt_required"] is True
    assert review_option["safety_scope"]["approval_receipt_path"] == (
        "reports/strategy_arbitration/"
        "krk_protected_plan_window_failure_contrast_collection_approval_v0.json"
    )
    assert review_option["safety_scope"]["approval_receipt_present"] is False
    assert review_option["safety_scope"]["approval_receipt_valid"] is False
    assert review_option["safety_scope"]["approval_receipt_blockers"] == [
        "approval_receipt_missing"
    ]
    assert review_option["approval_request_artifact"] == (
        "reports/strategy_arbitration/"
        "krk_protected_plan_window_failure_contrast_approval_request_v0.md"
    )
    assert (
        review_option["safety_scope"]["approval_request_status"]
        == "protected_plan_window_failure_contrast_approval_request_ready"
    )
    assert review_option["safety_scope"]["approval_receipt_created_by_request"] is False
    assert len(review_option["safety_scope"]["expected_manifest_fingerprint"]) == 64
    assert len(review_option["safety_scope"]["expected_readiness_fingerprint"]) == 64
    assert review_option["safety_scope"]["per_job_timeout_seconds"] == 900
    assert review_option["safety_scope"]["refresh_after_run"] is True
    assert review_option["safety_scope"]["processed_job_count"] == 0
    assert review_option["safety_scope"]["executed_job_count"] == 0
    assert review_option["safety_scope"]["output_valid_count"] == 0
    assert review_option["safety_scope"]["runtime_authorization_row_count"] == 0
    assert review_option["safety_scope"]["stage7_training_row_count"] == 0
    assert "runtime default changes" in review_option["what_it_does_not_allow"]
    assert "runtime DTM or tablebase lookup" in review_option["what_it_does_not_allow"]
    assert "gameplay-time topology mutation" in review_option["what_it_does_not_allow"]
    assert "selector training" in review_option["what_it_does_not_allow"]
    assert "unreviewed or unbounded label execution" in review_option["what_it_does_not_allow"]


def test_current_control_plane_gate_fixture_preserves_no_implicit_approval():
    payload = _current_gate.build_payload(
        stage4_packet={"decision": {"status": "s4"}},
        stage7_manifest={"decision": {"status": "s7"}},
        sequence_probe={"decision": {"status": "seq"}},
        sequence_policy_design={"decision": {"status": "design"}},
    )

    assert payload["decision"]["runtime_changes_allowed"] is False
    assert payload["decision"]["label_run_allowed"] is False
    assert (
        payload["recommendation"]["preferred_next_if_no_user_approval"]
        == "wait_for_explicit_protected_plan_window_failure_contrast_collection_approval"
    )
    assert (
        payload["recommendation"]["preferred_next_if_user_approves_collection"]
        == "create_matching_approval_receipt_then_execute_bounded_protected_plan_window_failure_contrast_collection_from_reviewed_manifest"
    )
    assert (
        payload["recommendation"]["preferred_next_if_user_approves_labels"]
        == "not_applicable_stage7_success_gate_closed"
    )
    assert (
        payload["recommendation"]["preferred_next_if_user_defers_both"]
        == "non_causal_sequence_policy_design_without_new_labels"
    )


def test_current_control_plane_gate_routes_forbidden_sequence_inputs_to_repair():
    payload = _current_gate.build_payload(
        sequence_policy_inputs={
            "decision": {"status": "sequence_policy_benchmark_inputs_ready_non_causal"},
            "summary": {
                "selector_training_row_count": 1,
                "runtime_authorization_row_count": 0,
            },
        },
        sequence_policy_benchmark_review={
            "decision": {
                "status": "sequence_policy_benchmark_review_blocked_forbidden_training_or_runtime_rows"
            },
            "blockers": ["selector_training_rows_forbidden"],
        },
    )

    option_ids = {option["option_id"] for option in payload["approval_options"]}
    assert "repair_sequence_policy_inputs_remove_training_or_runtime_rows" in option_ids
    assert "approve_protected_plan_window_failure_contrast_collection" not in option_ids
    repair_option = [
        option
        for option in payload["approval_options"]
        if option["option_id"] == "repair_sequence_policy_inputs_remove_training_or_runtime_rows"
    ][0]
    assert repair_option["command_if_explicitly_approved"] is None
    assert repair_option["safety_scope"]["selector_training_row_count"] == 1
    assert repair_option["safety_scope"]["runtime_authorization_row_count"] == 0
    assert "selector_training_rows_forbidden" in repair_option["safety_scope"]["blockers"]
    assert payload["current_state"][
        "sequence_policy_forbidden_training_or_runtime_input_blocked"
    ] is True
    assert (
        payload["recommendation"]["preferred_next_if_no_user_approval"]
        == "repair_sequence_policy_inputs_remove_training_or_runtime_rows"
    )
    assert (
        payload["recommendation"]["preferred_next_if_user_approves_collection"]
        == "not_applicable_pending_sequence_policy_input_repair"
    )
    assert payload["decision"]["selector_training_allowed"] is False


def test_current_control_plane_gate_blocks_collection_when_protected_stack_not_ready():
    payload = _current_gate.build_payload(
        full_suite_readiness={
            "decision": {"status": "krk_suite_readiness_blocked_pending_stack"},
            "protected_stack": {"ready": False},
            "hard_blockers": ["protected_retry1_stage5_6_stack_not_validated"],
        },
        sequence_policy_inputs={
            "decision": {"status": "sequence_policy_benchmark_inputs_ready_non_causal"},
            "summary": {
                "selector_training_row_count": 0,
                "runtime_authorization_row_count": 0,
            },
        },
        sequence_policy_benchmark_review={
            "decision": {"status": "sequence_policy_benchmark_mixed_plan_window_underpowered"},
            "blockers": ["protected_plan_window_failure_evidence_sparse"],
        },
    )

    option_ids = {option["option_id"] for option in payload["approval_options"]}
    assert "repair_protected_stack_validation" in option_ids
    assert "approve_protected_plan_window_failure_contrast_collection" not in option_ids
    repair_option = [
        option
        for option in payload["approval_options"]
        if option["option_id"] == "repair_protected_stack_validation"
    ][0]
    assert repair_option["command_if_explicitly_approved"] is None
    assert repair_option["safety_scope"]["protected_stack_ready"] is False
    assert (
        "protected_retry1_stage5_6_stack_not_validated"
        in repair_option["safety_scope"]["hard_blockers"]
    )
    assert payload["current_state"]["protected_stack"] == "protected_stack_validation_blocked"
    assert payload["current_state"]["protected_stack_ready"] is False
    assert (
        payload["recommendation"]["preferred_next_if_no_user_approval"]
        == "repair_protected_stack_validation"
    )
    assert (
        payload["recommendation"]["preferred_next_if_user_approves_collection"]
        == "not_applicable_pending_protected_stack_validation"
    )
    assert payload["decision"]["runtime_changes_allowed"] is False
