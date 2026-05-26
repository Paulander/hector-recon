#!/usr/bin/env python3
"""Tests for the KRK full-suite unblocker packet."""

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


_packet = _load_module(
    "write_krk_full_suite_unblocker_packet_v0",
    "scripts/write_krk_full_suite_unblocker_packet_v0.py",
)


def _read_report() -> dict:
    payload = json.loads((ROOT / "reports/krk_full_suite_unblocker_packet_v0.json").read_text())
    assert isinstance(payload, dict)
    return payload


def test_unblocker_packet_identifies_primary_gate_without_authorizing_it():
    payload = _read_report()

    assert payload["schema_version"] == "krk_full_suite_unblocker_packet.v0"
    assert payload["causal_status"] == "non_causal_approval_packet"
    assert (
        payload["decision"]["status"]
        == "krk_suite_protected_failure_contrast_unblocker_ready_pending_explicit_collection_approval"
    )
    assert payload["decision"]["label_run_allowed"] is False
    assert payload["decision"]["runtime_changes_allowed"] is False
    assert payload["decision"]["stage7_promotion_allowed"] is False
    assert payload["decision"]["stage8_training_allowed"] is False
    assert (
        payload["decision"]["recommended_next_step"]
        == "obtain_matching_approval_receipt_before_protected_failure_contrast_collection"
    )

    primary = payload["primary_unblocker"]
    assert primary["id"] == "protected_plan_window_failure_contrast_collection"
    assert primary["approval_required"] is True
    assert primary["implementation_allowed_by_this_packet"] is False
    assert (
        primary["status"]
        == "protected_plan_window_failure_contrast_manifest_review_passed_pending_explicit_approval"
    )
    assert primary["command_if_explicitly_approved"] == (
        "UV_CACHE_DIR=/tmp/uv-cache uv run python "
        "scripts/run_krk_protected_plan_window_failure_contrast_collection_v0.py "
        "--execute-reviewed-collection --refresh-after-run "
        "--approval-receipt "
        "reports/strategy_arbitration/"
        "krk_protected_plan_window_failure_contrast_collection_approval_v0.json"
    )
    assert primary["scope"]["resume_safe"] is True
    assert primary["scope"]["max_jobs"] == 6
    assert primary["scope"]["horizon"] == "h40"
    assert primary["scope"]["stage"] == "protected_plan_window_failure_contrast_evidence_only"
    assert primary["scope"]["protected_stack_readiness_required"] is True
    assert (
        primary["scope"]["protected_stack_status"]
        == "retry1_protected_stage5_6_stack_adopted_manifest_only"
    )
    assert primary["scope"]["protected_stack_ready"] is True
    assert primary["scope"]["protected_stack_rollback_paths_preserved"] is True
    assert primary["scope"]["protected_stack_active_paths_safe"] is True
    assert primary["scope"]["protected_stack_active_paths_exist"] is True
    assert primary["scope"]["protected_stack_rollback_paths_safe"] is True
    assert primary["scope"]["protected_stack_rollback_paths_exist"] is True
    assert primary["scope"]["protected_stack_rollback_common_paths_distinct"] is True
    assert primary["scope"]["protected_stack_filesystem_snapshots_replaced"] is False
    assert primary["scope"]["source_stage_counts"] == {
        "stage4": 2,
        "stage5": 2,
        "stage6": 2,
    }
    assert primary["scope"]["stop_after_unique_failures"] == 4
    assert primary["scope"]["observation_only"] is True
    assert primary["scope"]["skip_existing_outputs_by_default"] is True
    assert primary["scope"]["invalid_existing_outputs_block_without_overwrite"] is True
    assert primary["scope"]["execution_readiness_recomputed_live"] is True
    assert primary["scope"]["per_job_timeout_seconds"] == 900
    assert primary["scope"]["refresh_after_run"] is True
    assert primary["scope"]["approval_receipt_required"] is True
    assert primary["scope"]["approval_receipt_path"] == (
        "reports/strategy_arbitration/"
        "krk_protected_plan_window_failure_contrast_collection_approval_v0.json"
    )
    assert primary["scope"]["approval_receipt_present"] is False
    assert primary["scope"]["approval_receipt_valid"] is False
    assert primary["scope"]["approval_receipt_blockers"] == ["approval_receipt_missing"]
    assert primary["scope"]["approval_request_artifact"] == (
        "reports/strategy_arbitration/"
        "krk_protected_plan_window_failure_contrast_approval_request_v0.json"
    )
    assert (
        primary["scope"]["approval_request_status"]
        == "protected_plan_window_failure_contrast_approval_request_ready"
    )
    assert primary["scope"]["approval_receipt_created_by_request"] is False
    assert len(primary["scope"]["expected_manifest_fingerprint"]) == 64
    assert len(primary["scope"]["expected_readiness_fingerprint"]) == 64
    assert primary["scope"]["timed_out_job_count"] == 0
    assert primary["scope"]["post_success_refresh"] == "full_passive_krk_suite_gate_stack"
    assert primary["scope"]["stage7_training_rows"] == 0
    assert primary["scope"]["stage7_promotion_allowed"] is False
    assert primary["scope"]["stage8_training_allowed"] is False
    assert (
        payload["current_state"]["protected_stack_status"]
        == "retry1_protected_stage5_6_stack_adopted_manifest_only"
    )
    assert payload["current_state"]["protected_stack_ready"] is True
    assert payload["current_state"]["protected_stack_rollback_paths_preserved"] is True
    assert payload["current_state"]["protected_stack_active_paths_safe"] is True
    assert payload["current_state"]["protected_stack_active_paths_exist"] is True
    assert payload["current_state"]["protected_stack_rollback_paths_safe"] is True
    assert payload["current_state"]["protected_stack_rollback_paths_exist"] is True
    assert payload["current_state"]["protected_stack_rollback_common_paths_distinct"] is True
    assert payload["current_state"]["protected_stack_filesystem_snapshots_replaced"] is False
    assert (
        payload["current_state"]["stage7_output_validation_status"]
        == "stage7_diverse_clean_sampling_outputs_valid_ready_for_integration"
    )
    assert payload["current_state"]["stage7_execution_readiness_source"] == "live_recomputed"
    assert (
        payload["current_state"]["stage7_execution_readiness_status"]
        == "not_applicable_stage7_success_gate_closed"
    )
    assert (
        payload["current_state"]["stage7_historical_execution_readiness_status"]
        == "stage7_diverse_clean_sampling_execution_ready_pending_explicit_approval"
    )
    assert payload["current_state"]["stage7_execution_readiness_jobs_passing"] == 8
    assert payload["current_state"]["stage7_invalid_existing_output_count"] == 0
    assert payload["current_state"]["stage7_job_timeout_seconds"] == 900
    assert payload["current_state"]["stage7_timed_out_job_count"] == 0
    assert payload["current_state"]["stage7_overwrite_existing_outputs"] is False
    assert payload["current_state"]["stage7_processed_job_count"] == 0
    assert payload["current_state"]["stage7_executed_job_count"] == 0
    assert payload["current_state"]["stage7_historical_processed_job_count"] == 8
    assert payload["current_state"]["stage7_historical_executed_job_count"] == 8
    assert payload["current_state"]["stage7_skipped_existing_output_count"] == 0
    assert (
        payload["current_state"]["stage7_label_distribution_review_status"]
        == "stage7_label_distribution_review_success_gate_closed"
    )
    assert payload["current_state"]["stage7_label_distribution_unique_new_success"] == 2
    assert payload["current_state"]["stage7_label_distribution_duplicate_playouts"] == 50
    assert (
        payload["current_state"]["stage7_additional_clean_sampling_manifest_status"]
        == "stage7_additional_clean_sampling_manifest_not_applicable_success_gate_closed"
    )
    assert (
        payload["current_state"]["stage7_additional_clean_sampling_runner_status"]
        == "stage7_additional_clean_sampling_runner_not_applicable_success_gate_closed"
    )
    assert payload["current_state"]["stage7_additional_clean_sampling_job_count"] == 0
    assert (
        payload["current_state"]["protected_plan_window_failure_contrast_plan_status"]
        == "protected_plan_window_failure_contrast_plan_ready_pending_explicit_collection_approval"
    )
    assert payload["current_state"]["protected_plan_window_unique_failure_count"] == 1
    assert payload["current_state"]["protected_plan_window_minimum_new_failures_needed"] == 4
    assert (
        payload["current_state"]["protected_plan_window_failure_contrast_manifest_status"]
        == "protected_plan_window_failure_contrast_manifest_ready_for_review"
    )
    assert payload["current_state"]["protected_plan_window_failure_contrast_manifest_job_count"] == 6
    assert (
        payload["current_state"][
            "protected_plan_window_failure_contrast_manifest_review_status"
        ]
        == "protected_plan_window_failure_contrast_manifest_review_passed_pending_explicit_approval"
    )
    assert (
        payload["current_state"][
            "protected_plan_window_failure_contrast_execution_readiness_status"
        ]
        == "protected_plan_window_failure_contrast_execution_ready_pending_explicit_approval"
    )
    assert payload["current_state"]["protected_plan_window_failure_contrast_execution_jobs_passing"] == 6
    assert (
        payload["current_state"]["protected_plan_window_failure_contrast_runner_status"]
        == "protected_plan_window_failure_contrast_runner_dry_run_ready"
    )
    assert payload["current_state"]["protected_plan_window_failure_contrast_runner_processed_job_count"] == 0
    assert payload["current_state"]["protected_plan_window_failure_contrast_runner_executed_job_count"] == 0
    assert (
        payload["current_state"][
            "protected_plan_window_failure_contrast_approval_request_status"
        ]
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
        payload["current_state"]["protected_plan_window_failure_contrast_output_validation_status"]
        == "protected_plan_window_failure_contrast_outputs_validation_pending"
    )
    assert payload["current_state"]["protected_plan_window_failure_contrast_output_exists_count"] == 0
    assert payload["current_state"]["protected_plan_window_failure_contrast_output_valid_count"] == 0
    assert (
        payload["current_state"]["protected_plan_window_failure_contrast_integration_status"]
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
        payload["current_state"][
            "sequence_policy_after_protected_failure_contrast_refresh_status"
        ]
        == "sequence_policy_after_protected_failure_contrast_refresh_waiting_on_integration_outputs"
    )
    assert payload["current_state"]["sequence_policy_after_protected_failure_contrast_rows"] == 0


def test_unblocker_packet_keeps_stage4_as_secondary_gate():
    payload = _read_report()
    secondary = payload["secondary_unblocker"]

    assert secondary["id"] == "stage4_first_move_contrast_sandbox"
    assert secondary["status"] == "stage4_caveat_unblocker_ready_pending_explicit_runtime_approval"
    assert secondary["approval_request_artifact"] == (
        "reports/krk_stage4_first_move_contrast_sandbox_approval_request_v0.md"
    )
    assert (
        secondary["approval_request_status"]
        == "stage4_first_move_contrast_sandbox_approval_request_ready"
    )
    assert secondary["approval_request_created"] is False
    assert secondary["implementation_authorized_by_approval_request"] is False
    assert secondary["approval_required"] is True
    assert secondary["implementation_allowed_by_this_packet"] is False


def test_unblocker_packet_writer_mentions_exact_command_but_still_blocks_execution():
    payload = _packet.build_payload()
    rendered = _packet.write_markdown(payload)

    assert "protected_plan_window_failure_contrast_collection" in rendered
    assert (
        "command_if_explicitly_approved: `UV_CACHE_DIR=/tmp/uv-cache uv run python "
        "scripts/run_krk_protected_plan_window_failure_contrast_collection_v0.py "
        "--execute-reviewed-collection --refresh-after-run "
        "--approval-receipt reports/strategy_arbitration/"
        "krk_protected_plan_window_failure_contrast_collection_approval_v0.json`"
        in rendered
    )
    assert "max_jobs: `6`" in rendered
    assert "stage: `protected_plan_window_failure_contrast_evidence_only`" in rendered
    assert "stop_after_unique_failures: `4`" in rendered
    assert "observation_only: `True`" in rendered
    assert "resume_safe: `True`" in rendered
    assert "invalid_existing_outputs_block_without_overwrite: `True`" in rendered
    assert "per_job_timeout_seconds: `900`" in rendered
    assert "approval_receipt_required: `True`" in rendered
    assert "approval_receipt_blockers: `['approval_receipt_missing']`" in rendered
    assert (
        "approval_request_status: "
        "`protected_plan_window_failure_contrast_approval_request_ready`"
        in rendered
    )
    assert "approval_receipt_created_by_request: `False`" in rendered
    assert "protected_stack_readiness_required: `True`" in rendered
    assert (
        "protected_stack_status: "
        "`retry1_protected_stage5_6_stack_adopted_manifest_only`" in rendered
    )
    assert "protected_stack_rollback_paths_preserved: `True`" in rendered
    assert "protected_stack_filesystem_snapshots_replaced: `False`" in rendered
    assert (
        "approval_request_status: "
        "`stage4_first_move_contrast_sandbox_approval_request_ready`"
        in rendered
    )
    assert "implementation_authorized_by_approval_request: `False`" in rendered
    assert (
        "protected_plan_window_failure_contrast_approval_request_status: "
        "`protected_plan_window_failure_contrast_approval_request_ready`"
        in rendered
    )
    assert (
        "protected_plan_window_failure_contrast_approval_receipt_created: `False`"
        in rendered
    )
    assert (
        "approval_receipt_path: `reports/strategy_arbitration/"
        "krk_protected_plan_window_failure_contrast_collection_approval_v0.json`"
        in rendered
    )
    assert "post_success_refresh: `full_passive_krk_suite_gate_stack`" in rendered
    assert "approval_required: `True`" in rendered
    assert "implementation_allowed_by_this_packet: `False`" in rendered
    assert payload["primary_unblocker"]["implementation_allowed_by_this_packet"] is False


def test_unblocker_packet_routes_forbidden_training_rows_to_input_repair(monkeypatch):
    real_load = _packet._load

    def tainted_load(path: Path):
        payload = json.loads(json.dumps(real_load(path)))
        if path == _packet.READINESS:
            payload.setdefault("sequence_policy", {})[
                "forbidden_training_or_runtime_input_blocked"
            ] = True
            payload.setdefault("sequence_policy", {})[
                "forbidden_training_or_runtime_input_blockers"
            ] = ["selector_training_rows_forbidden"]
            payload.setdefault("hard_blockers", []).append(
                "sequence_policy_forbidden_training_or_runtime_rows"
            )
            payload.setdefault("decision", {})["status"] = (
                "krk_suite_readiness_blocked_forbidden_training_or_runtime_rows"
            )
        return payload

    monkeypatch.setattr(_packet, "_load", tainted_load)

    payload = _packet.build_payload()

    assert (
        payload["decision"]["status"]
        == "krk_suite_unblocker_blocked_forbidden_training_or_runtime_rows"
    )
    assert (
        payload["decision"]["recommended_next_step"]
        == "repair_sequence_policy_inputs_remove_training_or_runtime_rows"
    )
    assert payload["primary_unblocker"]["id"] == "sequence_policy_input_repair"
    assert payload["primary_unblocker"]["command_if_explicitly_approved"] is None
    assert payload["primary_unblocker"]["scope"]["max_jobs"] == 0
    assert payload["primary_unblocker"]["scope"]["stage"] == "sequence_policy_input_repair_only"
    assert payload["current_state"][
        "sequence_policy_forbidden_training_or_runtime_input_blocked"
    ] is True
    assert payload["decision"]["selector_training_allowed"] is False
