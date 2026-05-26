#!/usr/bin/env python3
"""Tests for passive KRK Stage 8 training-readiness review."""

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
    "review_krk_stage8_training_readiness_v0",
    "scripts/review_krk_stage8_training_readiness_v0.py",
)


def _read_report() -> dict:
    payload = json.loads((ROOT / "reports/krk_stage8_training_readiness_review_v0.json").read_text())
    assert isinstance(payload, dict)
    return payload


def test_stage8_training_readiness_review_blocks_current_state():
    payload = _read_report()

    assert payload["schema_version"] == "krk_stage8_training_readiness_review.v0"
    assert payload["causal_status"] == "non_causal_stage8_training_readiness_review"
    assert payload["runtime_behavior_changed"] is False
    assert payload["runtime_selector_implemented"] is False
    assert payload["runtime_score_changes"] is False
    assert payload["runtime_direct_routing"] is False
    assert payload["runtime_dtm_or_tablebase_lookup"] is False
    assert payload["hidden_python_controller"] is False
    assert payload["gameplay_topology_mutation"] is False
    assert payload["stage7_promotion_allowed"] is False
    assert payload["stage8_training_allowed"] is False
    assert payload["requirements"]["readiness_checked_flag_count"] >= 430
    assert payload["requirements"]["readiness_boundary_violation_count"] == 0
    assert payload["requirements"]["readiness_source_artifact_count"] >= 44
    assert payload["requirements"]["protected_stage5_6_stack_ready"] is True
    assert payload["requirements"]["stage7_clean_success_controls_ready"] is True
    assert payload["requirements"]["sequence_policy_benchmark_review_ready"] is True
    assert (
        payload["requirements"]["sequence_policy_benchmark_design_status"]
        == "sequence_policy_benchmark_design_ready_non_causal"
    )
    assert (
        payload["requirements"][
            "sequence_policy_passive_design_without_new_labels_status"
        ]
        == "non_causal_sequence_policy_design_without_new_labels_ready"
    )
    assert (
        payload["requirements"]["sequence_policy_passive_design_current_evidence_limit"]
        == "protected_plan_window_failure_evidence_sparse"
    )
    assert (
        payload["requirements"]["sequence_policy_cross_stage_requirements_status"]
        == "cross_stage_plan_capsule_evidence_ready_for_non_causal_benchmark"
    )
    assert (
        payload["requirements"][
            "sequence_policy_replay_free_protected_cross_stage_evidence"
        ]
        is True
    )
    assert (
        payload["requirements"]["sequence_policy_cross_stage_sequence_evidence_met"]
        is True
    )
    assert (
        payload["requirements"][
            "sequence_policy_after_protected_failure_contrast_refresh_status"
        ]
        == "sequence_policy_after_protected_failure_contrast_refresh_waiting_on_integration_outputs"
    )
    assert (
        payload["requirements"][
            "sequence_policy_after_protected_failure_contrast_boundaries_preserved"
        ]
        is True
    )
    assert (
        payload["requirements"][
            "sequence_policy_after_protected_failure_contrast_boundary_violation_count"
        ]
        == 0
    )
    assert (
        payload["requirements"]["sequence_policy_after_protected_failure_contrast_rows"]
        == 0
    )
    assert (
        payload["requirements"][
            "sequence_policy_after_protected_failure_contrast_stage7_training_row_count"
        ]
        == 0
    )
    assert (
        payload["requirements"][
            "protected_failure_contrast_collection_ready_for_explicit_approval"
        ]
        is True
    )
    assert payload["requirements"]["protected_failure_contrast_integration_ready"] is False
    assert (
        payload["requirements"]["protected_failure_contrast_runner_status"]
        == "protected_plan_window_failure_contrast_runner_dry_run_ready"
    )
    assert payload["requirements"]["protected_failure_contrast_runner_processed_job_count"] == 0
    assert payload["requirements"]["protected_failure_contrast_runner_executed_job_count"] == 0
    assert payload["requirements"]["protected_failure_contrast_command_if_explicitly_approved"] == (
        "UV_CACHE_DIR=/tmp/uv-cache uv run python "
        "scripts/run_krk_protected_plan_window_failure_contrast_collection_v0.py "
        "--execute-reviewed-collection --refresh-after-run "
        "--approval-receipt "
        "reports/strategy_arbitration/"
        "krk_protected_plan_window_failure_contrast_collection_approval_v0.json"
    )
    assert payload["requirements"]["protected_failure_contrast_approval_request_artifact"] == (
        "reports/strategy_arbitration/"
        "krk_protected_plan_window_failure_contrast_approval_request_v0.json"
    )
    assert (
        payload["requirements"]["protected_failure_contrast_approval_request_status"]
        == "protected_plan_window_failure_contrast_approval_request_ready"
    )
    assert (
        payload["requirements"][
            "protected_failure_contrast_approval_request_blockers"
        ]
        == []
    )
    assert (
        payload["requirements"][
            "protected_failure_contrast_approval_receipt_created_by_request"
        ]
        is False
    )
    assert payload["requirements"][
        "protected_failure_contrast_approval_receipt_blockers"
    ] == ["approval_receipt_missing"]
    assert (
        payload["requirements"][
            "protected_failure_contrast_post_success_refresh_required"
        ]
        is True
    )
    assert (
        payload["requirements"]["protected_failure_contrast_post_success_refresh_script"]
        == "scripts/advance_krk_suite_from_current_gates_v0.py"
    )
    assert (
        payload["requirements"]["protected_failure_contrast_post_success_refresh_scope"]
        == "full_passive_krk_suite_gate_stack"
    )
    assert (
        payload["requirements"]["protected_failure_contrast_runtime_behavior_changed"]
        is False
    )
    assert (
        payload["requirements"]["protected_failure_contrast_runtime_defaults_changed"]
        is False
    )
    assert (
        payload["requirements"]["protected_failure_contrast_runtime_selector_implemented"]
        is False
    )
    assert (
        payload["requirements"]["protected_failure_contrast_runtime_score_changes"]
        is False
    )
    assert (
        payload["requirements"]["protected_failure_contrast_runtime_direct_routing"]
        is False
    )
    assert (
        payload["requirements"][
            "protected_failure_contrast_runtime_dtm_or_tablebase_lookup"
        ]
        is False
    )
    assert (
        payload["requirements"]["protected_failure_contrast_hidden_python_controller"]
        is False
    )
    assert (
        payload["requirements"]["protected_failure_contrast_gameplay_topology_mutation"]
        is False
    )
    assert (
        payload["requirements"]["protected_failure_contrast_selector_training_allowed"]
        is False
    )
    assert (
        payload["requirements"]["protected_failure_contrast_stage7_promotion_allowed"]
        is False
    )
    assert (
        payload["requirements"]["protected_failure_contrast_stage8_training_allowed"]
        is False
    )
    assert "stage7_clean_success_controls_missing" not in payload["blockers"]
    assert (
        "protected_plan_window_failure_contrast_collection_pending_explicit_approval"
        in payload["blockers"]
    )
    assert (
        payload["decision"]["status"]
        == "stage8_training_blocked_pending_protected_failure_contrast_collection"
    )
    assert (
        payload["decision"]["recommended_next_step"]
        == "obtain_matching_approval_receipt_before_protected_failure_contrast_collection"
    )
    assert payload["decision"]["implementation_allowed_by_this_review"] is False
    assert payload["decision"]["stage8_training_allowed"] is False


def test_stage8_training_readiness_review_fixture_can_be_review_ready():
    readiness = {
        "protected_stack": {
            "ready": True,
            "m1_m4_preservation_passed": True,
            "kpk_kqk_bridge_preservation_passed": True,
        },
        "stage_status": {
            "stage4": {"ready_for_current_suite": True},
            "stage7": {
                "success_controls_ready": True,
                "success_controls": 5,
                "success_controls_required": 5,
                "ready_for_promotion": True,
            },
        },
        "protected_failure_contrast_gate": {
            "ready_for_explicit_approval": True,
            "integration_ready": False,
            "runner_status": "protected_plan_window_failure_contrast_runner_dry_run_ready",
            "runner_processed_job_count": 0,
            "runner_executed_job_count": 0,
        },
        "explicit_gate_blockers": [
            "protected_plan_window_failure_contrast_collection_pending_explicit_approval"
        ],
    }
    benchmark_review = {
        "decision": {
            "status": "sequence_policy_benchmark_supports_non_causal_sequence_policy_review"
        }
    }

    payload = _review.build_payload(readiness=readiness, benchmark_review=benchmark_review)

    assert (
        payload["decision"]["status"]
        == "stage8_training_review_ready_pending_explicit_approval"
    )
    assert payload["blockers"] == []
    assert payload["warnings"] == []
    assert payload["decision"]["implementation_allowed_by_this_review"] is False
    assert payload["decision"]["stage8_training_allowed"] is False


def test_stage8_training_readiness_review_fixture_blocks_mixed_sequence_result():
    readiness = {
        "protected_stack": {
            "ready": True,
            "m1_m4_preservation_passed": True,
            "kpk_kqk_bridge_preservation_passed": True,
        },
        "stage_status": {
            "stage4": {"ready_for_current_suite": True},
            "stage7": {
                "success_controls_ready": True,
                "success_controls": 5,
                "success_controls_required": 5,
                "ready_for_promotion": False,
            },
        },
        "protected_failure_contrast_gate": {
            "ready_for_explicit_approval": True,
            "integration_ready": False,
            "runner_status": "protected_plan_window_failure_contrast_runner_dry_run_ready",
            "runner_processed_job_count": 0,
            "runner_executed_job_count": 0,
        },
        "explicit_gate_blockers": [
            "protected_plan_window_failure_contrast_collection_pending_explicit_approval"
        ],
    }
    benchmark_review = {
        "decision": {"status": "sequence_policy_benchmark_mixed_plan_window_underpowered"}
    }

    payload = _review.build_payload(readiness=readiness, benchmark_review=benchmark_review)

    assert (
        payload["decision"]["status"]
        == "stage8_training_blocked_pending_protected_failure_contrast_collection"
    )
    assert (
        "protected_plan_window_failure_contrast_collection_pending_explicit_approval"
        in payload["blockers"]
    )
    assert (
        payload["decision"]["recommended_next_step"]
        == "obtain_matching_approval_receipt_before_protected_failure_contrast_collection"
    )
    assert "stage7_not_promoted_and_must_remain_held_out_without_explicit_gate" in payload["warnings"]
    assert payload["decision"]["stage8_training_allowed"] is False


def test_stage8_training_readiness_review_keeps_stage7_status_for_stage7_gap():
    payload = _review.build_payload(
        readiness={
            "protected_stack": {"ready": True},
            "stage_status": {
                "stage4": {"ready_for_current_suite": True},
                "stage7": {
                    "success_controls_ready": False,
                    "success_controls": 2,
                    "success_controls_required": 5,
                    "ready_for_promotion": False,
                },
            },
            "protected_failure_contrast_gate": {},
            "explicit_gate_blockers": [],
        },
        benchmark_review={
            "decision": {"status": "sequence_policy_benchmark_review_blocked_pending_ready_inputs"}
        },
    )

    assert "stage7_clean_success_controls_missing" in payload["blockers"]
    assert (
        payload["decision"]["status"]
        == "stage8_training_blocked_pending_stage7_sequence_gate"
    )
    assert (
        payload["decision"]["recommended_next_step"]
        == "fill_stage7_success_controls_and_rerun_passive_gate_advancement"
    )
    assert payload["decision"]["stage8_training_allowed"] is False


def test_stage8_training_readiness_review_routes_forbidden_rows_to_input_repair():
    readiness = {
        "protected_stack": {"ready": True},
        "stage_status": {
            "stage4": {"ready_for_current_suite": True},
            "stage7": {
                "success_controls_ready": True,
                "success_controls": 5,
                "success_controls_required": 5,
                "ready_for_promotion": False,
            },
        },
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
        "explicit_gate_blockers": [],
        "decision": {
            "status": "krk_suite_readiness_blocked_forbidden_training_or_runtime_rows"
        },
    }
    benchmark_review = {
        "decision": {
            "status": "sequence_policy_benchmark_review_blocked_forbidden_training_or_runtime_rows"
        },
        "blockers": ["selector_training_rows_forbidden"],
    }

    payload = _review.build_payload(readiness=readiness, benchmark_review=benchmark_review)

    assert payload["requirements"][
        "sequence_policy_forbidden_training_or_runtime_input_blocked"
    ] is True
    assert (
        payload["decision"]["status"]
        == "stage8_training_blocked_forbidden_training_or_runtime_rows"
    )
    assert (
        payload["decision"]["recommended_next_step"]
        == "repair_sequence_policy_inputs_remove_training_or_runtime_rows"
    )
    assert "sequence_policy_forbidden_training_or_runtime_rows" in payload["blockers"]
    assert payload["decision"]["selector_training_allowed"] is False
    assert payload["decision"]["stage8_training_allowed"] is False
