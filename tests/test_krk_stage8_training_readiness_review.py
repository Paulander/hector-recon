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
    assert payload["requirements"]["sequence_policy_benchmark_review_ready"] is False
    assert (
        payload["requirements"]["sequence_policy_benchmark_design_status"]
        == "sequence_policy_benchmark_design_ready_non_causal"
    )
    assert (
        payload["requirements"][
            "sequence_policy_passive_design_without_new_labels_status"
        ]
        == "non_causal_sequence_policy_design_review_needed"
    )
    assert (
        payload["requirements"]["sequence_policy_passive_design_current_evidence_limit"]
        is None
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
        == "sequence_policy_after_protected_failure_contrast_refresh_blocked_pending_"
        "protected_failure_contrast_control_plane_gate_review"
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
        is False
    )
    assert (
        payload["requirements"]["protected_stack_status"]
        == "retry1_protected_stage5_6_stack_adopted_manifest_only"
    )
    assert payload["requirements"]["protected_stack_ready"] is True
    assert payload["requirements"]["protected_stack_rollback_paths_preserved"] is True
    assert payload["requirements"]["protected_stack_active_paths_safe"] is True
    assert payload["requirements"]["protected_stack_active_paths_exist"] is True
    assert payload["requirements"]["protected_stack_rollback_paths_safe"] is True
    assert payload["requirements"]["protected_stack_rollback_paths_exist"] is True
    assert payload["requirements"]["protected_stack_rollback_common_paths_distinct"] is True
    assert payload["requirements"]["protected_stack_filesystem_snapshots_replaced"] is False
    assert payload["requirements"]["protected_failure_contrast_integration_ready"] is False
    assert (
        payload["requirements"]["protected_failure_contrast_runner_status"]
        == "protected_plan_window_failure_contrast_runner_blocked"
    )
    assert (
        payload["requirements"]["protected_failure_contrast_runner_manifest_status"]
        == "protected_plan_window_failure_contrast_manifest_ready_for_review"
    )
    assert (
        payload["requirements"][
            "protected_failure_contrast_runner_manifest_declared_job_count"
        ]
        == 6
    )
    assert (
        len(
            payload["requirements"][
                "protected_failure_contrast_runner_manifest_fingerprint"
            ]
        )
        == 64
    )
    assert (
        payload["requirements"][
            "protected_failure_contrast_runner_collection_run_allowed"
        ]
        is False
    )
    assert payload["requirements"]["protected_failure_contrast_runner_processed_job_count"] == 0
    assert payload["requirements"]["protected_failure_contrast_runner_executed_job_count"] == 0
    assert (
        payload["requirements"][
            "protected_failure_contrast_command_if_explicitly_approved"
        ]
        is None
    )
    assert (
        payload["requirements"][
            "protected_failure_contrast_collection_option_available"
        ]
        is False
    )
    assert (
        payload["requirements"][
            "protected_failure_contrast_collection_command_available"
        ]
        is False
    )
    assert (
        payload["requirements"]["protected_failure_contrast_collection_option_id"]
        is None
    )
    assert (
        payload["requirements"][
            "protected_failure_contrast_collection_blocked_by_option_id"
        ]
        == "review_protected_plan_window_failure_contrast_manifest"
    )
    assert payload["requirements"]["protected_failure_contrast_approval_request_artifact"] == (
        "reports/strategy_arbitration/"
        "krk_protected_plan_window_failure_contrast_approval_request_v0.json"
    )
    assert (
        payload["requirements"]["protected_failure_contrast_approval_request_status"]
        == "protected_plan_window_failure_contrast_approval_request_blocked"
    )
    assert (
        payload["requirements"][
            "protected_failure_contrast_approval_request_blockers"
        ]
        == ["protected_failure_contrast_execution_scope_not_ready"]
    )
    assert (
        payload["requirements"][
            "protected_failure_contrast_approval_request_ready_for_collection"
        ]
        is False
    )
    assert (
        payload["requirements"][
            "protected_failure_contrast_approval_receipt_created_by_request"
        ]
        is False
    )
    assert (
        payload["requirements"]["protected_failure_contrast_approval_receipt_present"]
        is True
    )
    assert (
        payload["requirements"]["protected_failure_contrast_approval_receipt_valid"]
        is False
    )
    assert payload["requirements"][
        "protected_failure_contrast_approval_receipt_blockers"
    ] == [
        "approval_receipt_readiness_fingerprint_mismatch",
        "approval_receipt_readiness_status_mismatch",
        "approval_receipt_current_control_plane_approval_option_ids_mismatch",
        "approval_receipt_protected_failure_contrast_collection_option_available_mismatch",
        "approval_receipt_protected_failure_contrast_collection_command_available_mismatch",
        "approval_receipt_protected_failure_contrast_collection_option_id_mismatch",
        "approval_receipt_protected_failure_contrast_collection_blocked_by_option_id_mismatch",
    ]
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
        "sequence_policy_benchmark_review_not_ready"
        in payload["blockers"]
    )
    assert (
        payload["decision"]["status"]
        == "stage8_training_blocked_pending_sequence_policy_gate"
    )
    assert (
        payload["decision"]["recommended_next_step"]
        == "rerun_passive_gate_advancement_or_inspect_sequence_policy_benchmark_review"
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
            "command_if_explicitly_approved": "SHOULD_NOT_SURFACE",
        },
        "current_control_plane_gate": {
            "protected_failure_contrast_collection_option_available": False,
            "protected_failure_contrast_collection_command_available": False,
            "protected_failure_contrast_collection_option_id": None,
            "protected_failure_contrast_collection_blocked_by_option_id": (
                "review_protected_plan_window_failure_contrast_execution_readiness"
            ),
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
            "command_if_explicitly_approved": "SHOULD_NOT_SURFACE",
        },
        "current_control_plane_gate": {
            "protected_failure_contrast_collection_option_available": False,
            "protected_failure_contrast_collection_command_available": False,
            "protected_failure_contrast_collection_option_id": None,
            "protected_failure_contrast_collection_blocked_by_option_id": (
                "review_protected_plan_window_failure_contrast_execution_readiness"
            ),
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
        == "stage8_training_blocked_pending_protected_failure_contrast_control_plane_gate_review"
    )
    assert (
        "protected_plan_window_failure_contrast_control_plane_gate_review_required"
        in payload["blockers"]
    )
    assert (
        payload["decision"]["recommended_next_step"]
        == "review_current_control_plane_gate_for_protected_failure_contrast_collection"
    )
    assert "stage7_not_promoted_and_must_remain_held_out_without_explicit_gate" in payload["warnings"]
    assert payload["decision"]["stage8_training_allowed"] is False


def test_stage8_training_readiness_review_routes_blocked_collection_request_to_repair():
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
            "command_if_explicitly_approved": "SHOULD_NOT_SURFACE",
            "approval_request_status": (
                "protected_plan_window_failure_contrast_approval_request_ready"
            ),
            "approval_request_blockers": [],
            "approval_request_ready_for_collection": False,
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
        payload["requirements"][
            "protected_failure_contrast_collection_ready_for_explicit_approval"
        ]
        is False
    )
    assert (
        payload["requirements"][
            "protected_failure_contrast_approval_request_ready_for_collection"
        ]
        is False
    )
    assert (
        "protected_plan_window_failure_contrast_approval_request_blocked"
        in payload["blockers"]
    )
    assert (
        payload["decision"]["status"]
        == "stage8_training_blocked_pending_protected_failure_contrast_approval_request_repair"
    )
    assert (
        payload["decision"]["recommended_next_step"]
        == "repair_protected_failure_contrast_approval_request_scope"
    )
    assert (
        payload["requirements"][
            "protected_failure_contrast_command_if_explicitly_approved"
        ]
        is None
    )
    assert payload["decision"]["stage8_training_allowed"] is False


def test_stage8_training_readiness_review_blocks_collection_when_execution_not_ready():
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
            "status": "protected_plan_window_failure_contrast_execution_blocked",
            "ready_for_explicit_approval": True,
            "command_if_explicitly_approved": "SHOULD_NOT_SURFACE",
            "approval_request_status": (
                "protected_plan_window_failure_contrast_approval_request_ready"
            ),
            "approval_request_blockers": [],
            "approval_request_ready_for_collection": True,
            "integration_ready": False,
            "runner_status": "protected_plan_window_failure_contrast_runner_blocked",
            "runner_processed_job_count": 0,
            "runner_executed_job_count": 0,
        },
        "explicit_gate_blockers": [
            "protected_plan_window_failure_contrast_collection_pending_explicit_approval"
        ],
    }

    payload = _review.build_payload(
        readiness=readiness,
        benchmark_review={
            "decision": {
                "status": "sequence_policy_benchmark_mixed_plan_window_underpowered"
            }
        },
    )

    assert (
        payload["requirements"][
            "protected_failure_contrast_collection_ready_for_explicit_approval"
        ]
        is False
    )
    assert (
        "protected_plan_window_failure_contrast_execution_readiness_blocked"
        in payload["blockers"]
    )
    assert (
        "protected_plan_window_failure_contrast_collection_pending_explicit_approval"
        not in payload["blockers"]
    )
    assert (
        payload["decision"]["status"]
        == "stage8_training_blocked_pending_protected_failure_contrast_execution_readiness"
    )
    assert (
        payload["decision"]["recommended_next_step"]
        == "review_protected_plan_window_failure_contrast_execution_readiness"
    )
    assert (
        payload["requirements"][
            "protected_failure_contrast_command_if_explicitly_approved"
        ]
        is None
    )
    assert payload["decision"]["stage8_training_allowed"] is False


def test_stage8_training_readiness_review_prioritizes_protected_stack_repair():
    readiness = {
        "protected_stack": {
            "ready": False,
            "rollback_paths_preserved": False,
            "active_stack_path_status": {"all_paths_safe": False},
            "rollback_common_paths_distinct": False,
            "filesystem_snapshots_replaced": True,
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
            "command_if_explicitly_approved": "SHOULD_NOT_SURFACE",
            "approval_request_status": (
                "protected_plan_window_failure_contrast_approval_request_ready"
            ),
            "approval_request_blockers": [],
            "approval_request_ready_for_collection": True,
        },
        "explicit_gate_blockers": [
            "protected_plan_window_failure_contrast_collection_pending_explicit_approval"
        ],
    }
    benchmark_review = {
        "decision": {"status": "sequence_policy_benchmark_mixed_plan_window_underpowered"}
    }

    payload = _review.build_payload(readiness=readiness, benchmark_review=benchmark_review)

    assert "protected_stage5_6_stack_not_ready" in payload["blockers"]
    assert "protected_stack_rollback_paths_not_preserved" in payload["blockers"]
    assert "protected_stack_active_paths_unsafe" in payload["blockers"]
    assert "protected_stack_rollback_common_paths_not_distinct" in payload["blockers"]
    assert (
        "protected_stack_filesystem_snapshot_replacement_detected"
        in payload["blockers"]
    )
    assert (
        payload["decision"]["status"]
        == "stage8_training_blocked_pending_protected_stack_repair"
    )
    assert payload["decision"]["recommended_next_step"] == "repair_protected_stack_validation"
    assert (
        payload["requirements"][
            "protected_failure_contrast_command_if_explicitly_approved"
        ]
        is None
    )
    assert payload["decision"]["stage8_training_allowed"] is False


def test_stage8_training_readiness_review_falls_back_when_collection_ready_is_null():
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
            "status": (
                "protected_plan_window_failure_contrast_execution_ready_pending_explicit_approval"
            ),
            "ready_for_explicit_approval": None,
            "approval_request_status": (
                "protected_plan_window_failure_contrast_approval_request_ready"
            ),
            "approval_request_blockers": [],
            "approval_request_ready_for_collection": True,
            "integration_ready": False,
            "runner_status": "protected_plan_window_failure_contrast_runner_dry_run_ready",
            "runner_processed_job_count": 0,
            "runner_executed_job_count": 0,
            "command_if_explicitly_approved": "SHOULD_NOT_SURFACE",
        },
        "current_control_plane_gate": {
            "protected_failure_contrast_collection_option_available": False,
            "protected_failure_contrast_collection_command_available": False,
            "protected_failure_contrast_collection_option_id": None,
            "protected_failure_contrast_collection_blocked_by_option_id": (
                "review_protected_plan_window_failure_contrast_execution_readiness"
            ),
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
        payload["requirements"][
            "protected_failure_contrast_collection_ready_for_explicit_approval"
        ]
        is True
    )
    assert (
        payload["requirements"][
            "protected_failure_contrast_approval_request_ready_for_collection"
        ]
        is True
    )
    assert (
        "protected_plan_window_failure_contrast_control_plane_gate_review_required"
        in payload["blockers"]
    )
    assert (
        payload["requirements"][
            "protected_failure_contrast_command_if_explicitly_approved"
        ]
        is None
    )
    assert (
        payload["requirements"][
            "protected_failure_contrast_collection_command_available"
        ]
        is False
    )
    assert (
        payload["requirements"][
            "protected_failure_contrast_collection_blocked_by_option_id"
        ]
        == "review_protected_plan_window_failure_contrast_execution_readiness"
    )
    assert (
        payload["decision"]["status"]
        == "stage8_training_blocked_pending_protected_failure_contrast_control_plane_gate_review"
    )
    assert (
        payload["decision"]["recommended_next_step"]
        == "review_current_control_plane_gate_for_protected_failure_contrast_collection"
    )
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
