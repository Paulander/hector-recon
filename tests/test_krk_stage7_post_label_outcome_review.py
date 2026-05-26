#!/usr/bin/env python3
"""Tests for KRK Stage 7 post-label outcome review."""

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


_review = _load_module(
    "review_krk_stage7_post_label_outcome_v0",
    "scripts/review_krk_stage7_post_label_outcome_v0.py",
)


def _read_report() -> dict:
    payload = json.loads((ROOT / "reports/krk_stage7_post_label_outcome_review_v0.json").read_text())
    assert isinstance(payload, dict)
    return payload


def test_stage7_post_label_outcome_current_artifact_reports_sequence_policy_gap():
    payload = _read_report()

    assert payload["schema_version"] == "krk_stage7_post_label_outcome_review.v0"
    assert payload["causal_status"] == "non_causal_post_label_outcome_review"
    assert payload["runtime_behavior_changed"] is False
    assert payload["runtime_selector_implemented"] is False
    assert payload["runtime_dtm_or_tablebase_lookup"] is False
    assert payload["gameplay_topology_mutation"] is False
    assert payload["stage7_promotion_allowed"] is False
    assert payload["stage8_training_allowed"] is False
    assert payload["summary"]["outputs_present_count"] == 8
    assert payload["summary"]["output_validation_status"] == (
        "stage7_diverse_clean_sampling_outputs_valid_ready_for_integration"
    )
    assert payload["summary"]["success_controls"] == 11
    assert payload["summary"]["success_controls_met"] is True
    assert payload["summary"]["stage7_training_row_count"] == 0
    assert payload["summary"]["selector_training_row_count"] == 0
    assert payload["summary"]["runtime_authorization_row_count"] == 0
    assert payload["summary"]["protected_failure_contrast_ready_for_explicit_approval"] is True
    assert payload["summary"]["protected_failure_contrast_integration_ready"] is False
    assert (
        payload["summary"]["protected_failure_contrast_runner_status"]
        == "protected_plan_window_failure_contrast_runner_dry_run_ready"
    )
    assert payload["summary"]["protected_failure_contrast_runner_processed_job_count"] == 0
    assert payload["summary"]["protected_failure_contrast_runner_executed_job_count"] == 0
    assert payload["summary"]["protected_failure_contrast_command_if_explicitly_approved"] == (
        "UV_CACHE_DIR=/tmp/uv-cache uv run python "
        "scripts/run_krk_protected_plan_window_failure_contrast_collection_v0.py "
        "--execute-reviewed-collection --refresh-after-run "
        "--approval-receipt "
        "reports/strategy_arbitration/"
        "krk_protected_plan_window_failure_contrast_collection_approval_v0.json"
    )
    assert (
        payload["decision"]["status"]
        == "post_label_outcome_waiting_on_explicit_protected_failure_contrast_collection"
    )
    assert (
        "protected_plan_window_failure_contrast_collection_pending_explicit_approval"
        in payload["blockers"]
    )
    assert "protected_plan_window_failure_contrast_gate_ready_for_approval" in payload["findings"]
    assert (
        payload["decision"]["recommended_next_step"]
        == "obtain_matching_approval_receipt_before_protected_failure_contrast_collection"
    )
    assert payload["decision"]["label_run_allowed"] is False
    assert payload["decision"]["runtime_changes_allowed"] is False
    assert payload["decision"]["stage7_promotion_allowed"] is False
    assert payload["decision"]["stage8_training_allowed"] is False


def test_stage7_post_label_outcome_blocks_invalid_outputs():
    payload = _review.build_payload(
        output_validation={
            "summary": {"output_exists_count": 1, "output_valid_count": 0},
            "decision": {
                "status": "stage7_diverse_clean_sampling_outputs_invalid_block_integration"
            },
        },
        integration={
            "summary": {
                "combined_success_controls": 2,
                "success_controls_required": 5,
                "success_controls_met": False,
                "combined_failure_controls": 8,
                "failure_controls_required": 5,
                "failure_controls_met": True,
            },
            "decision": {"status": "stage7_diverse_clean_sampling_integration_blocked_invalid_outputs"},
        },
        pipeline={"summary": {"sequence_policy_inputs_ready": False}, "decision": {"status": "blocked"}},
        benchmark_review={"decision": {"status": "sequence_policy_benchmark_review_blocked_pending_ready_inputs"}},
        readiness={"stage7_sampling_gate": {"invalid_existing_output_count": 1}, "decision": {"status": "blocked"}},
        stage8_review={
            "decision": {
                "status": "stage8_training_blocked_pending_protected_failure_contrast_collection"
            }
        },
    )

    assert payload["decision"]["status"] == "post_label_outcome_invalid_outputs_block_integration"
    assert "stage7_diverse_clean_outputs_invalid" in payload["blockers"]
    assert payload["summary"]["invalid_output_count"] == 1
    assert payload["decision"]["runtime_changes_allowed"] is False
    assert payload["decision"]["stage8_training_allowed"] is False


def test_stage7_post_label_outcome_detects_sequence_policy_review_ready():
    payload = _review.build_payload(
        output_validation={
            "summary": {"output_exists_count": 8, "output_valid_count": 8},
            "decision": {
                "status": "stage7_diverse_clean_sampling_outputs_valid_ready_for_integration"
            },
        },
        integration={
            "summary": {
                "combined_success_controls": 5,
                "success_controls_required": 5,
                "success_controls_met": True,
                "combined_failure_controls": 8,
                "failure_controls_required": 5,
                "failure_controls_met": True,
            },
            "decision": {
                "status": "stage7_diverse_clean_sampling_integration_success_controls_met"
            },
        },
        pipeline={
            "summary": {"sequence_policy_inputs_ready": True},
            "decision": {
                "status": "sequence_policy_pipeline_refreshed_ready_for_non_causal_benchmark_review"
            },
        },
        benchmark_review={
            "decision": {
                "status": "sequence_policy_benchmark_supports_non_causal_sequence_policy_review"
            }
        },
        readiness={
            "stage7_sampling_gate": {"invalid_existing_output_count": 0},
            "decision": {"status": "krk_suite_readiness_ready_for_next_runtime_or_training_review"},
            "protected_failure_contrast_gate": {
                "ready_for_explicit_approval": False,
                "integration_ready": False,
                "runner_status": "not_applicable",
                "runner_processed_job_count": 0,
                "runner_executed_job_count": 0,
            },
            "explicit_gate_blockers": [],
        },
        stage8_review={
            "decision": {
                "status": "stage8_training_blocked_pending_protected_failure_contrast_collection"
            }
        },
    )

    assert (
        payload["decision"]["status"]
        == "post_label_outcome_sequence_policy_review_ready_stage8_blocked"
    )
    assert "sequence_policy_benchmark_supportive" in payload["findings"]
    assert payload["decision"]["stage8_training_allowed"] is False


def test_stage7_post_label_outcome_routes_forbidden_rows_to_input_repair():
    payload = _review.build_payload(
        output_validation={
            "summary": {"output_exists_count": 8, "output_valid_count": 8},
            "decision": {
                "status": "stage7_diverse_clean_sampling_outputs_valid_ready_for_integration"
            },
        },
        integration={
            "summary": {
                "combined_success_controls": 5,
                "success_controls_required": 5,
                "success_controls_met": True,
                "combined_failure_controls": 8,
                "failure_controls_required": 5,
                "failure_controls_met": True,
            },
            "decision": {
                "status": "stage7_diverse_clean_sampling_integration_success_controls_met"
            },
        },
        pipeline={
            "summary": {"sequence_policy_inputs_ready": True},
            "decision": {
                "status": "sequence_policy_pipeline_refreshed_ready_for_non_causal_benchmark_review"
            },
        },
        benchmark_review={
            "decision": {
                "status": "sequence_policy_benchmark_review_blocked_forbidden_training_or_runtime_rows"
            },
            "blockers": ["selector_training_rows_forbidden"],
        },
        readiness={
            "stage7_sampling_gate": {"invalid_existing_output_count": 0},
            "sequence_policy": {
                "forbidden_training_or_runtime_input_blocked": True,
                "forbidden_training_or_runtime_input_blockers": [
                    "selector_training_rows_forbidden"
                ],
            },
            "protected_failure_contrast_gate": {
                "ready_for_explicit_approval": False,
                "integration_ready": False,
                "runner_status": "protected_plan_window_failure_contrast_runner_dry_run_ready",
                "runner_processed_job_count": 0,
                "runner_executed_job_count": 0,
            },
            "hard_blockers": ["sequence_policy_forbidden_training_or_runtime_rows"],
            "explicit_gate_blockers": [
                "protected_plan_window_failure_contrast_collection_pending_explicit_approval"
            ],
            "decision": {
                "status": "krk_suite_readiness_blocked_forbidden_training_or_runtime_rows"
            },
        },
        stage8_review={
            "decision": {
                "status": "stage8_training_blocked_forbidden_training_or_runtime_rows"
            }
        },
    )

    assert payload["summary"][
        "sequence_policy_forbidden_training_or_runtime_input_blocked"
    ] is True
    assert (
        payload["decision"]["status"]
        == "post_label_outcome_blocked_forbidden_training_or_runtime_rows"
    )
    assert (
        payload["decision"]["recommended_next_step"]
        == "repair_sequence_policy_inputs_remove_training_or_runtime_rows"
    )
    assert "sequence_policy_forbidden_training_or_runtime_rows" in payload["blockers"]
    assert (
        "protected_plan_window_failure_contrast_collection_pending_explicit_approval"
        not in payload["blockers"]
    )
    assert payload["decision"]["selector_training_allowed"] is False
