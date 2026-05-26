#!/usr/bin/env python3
"""Tests for the non-causal underpowered KRK sequence-policy pilot review."""

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


_pilot = _load_module(
    "review_krk_sequence_policy_underpowered_pilot_v0",
    "scripts/review_krk_sequence_policy_underpowered_pilot_v0.py",
)


def _read_report() -> dict:
    payload = json.loads(
        (
            ROOT
            / "reports/strategy_arbitration/krk_sequence_policy_underpowered_pilot_v0.json"
        ).read_text(encoding="utf-8")
    )
    assert isinstance(payload, dict)
    return payload


def test_underpowered_pilot_preserves_all_boundaries():
    payload = _read_report()

    assert payload["schema_version"] == "krk_sequence_policy_underpowered_pilot.v0"
    assert payload["causal_status"] == "non_causal_underpowered_pilot_review"
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
    assert payload["decision"]["selector_training_allowed"] is False
    assert payload["decision"]["stage7_promotion_allowed"] is False
    assert payload["decision"]["stage8_training_allowed"] is False


def test_underpowered_pilot_keeps_ready_gate_blocked_but_preserves_signal():
    payload = _read_report()

    assert (
        payload["decision"]["status"]
        == "sequence_policy_pilot_underpowered_pending_protected_failure_contrast_collection"
    )
    assert (
        payload["decision"]["recommended_next_step"]
        == "obtain_matching_approval_receipt_before_protected_failure_contrast_collection"
    )
    assert payload["summary"]["benchmark_executed_as_ready"] is True
    assert (
        payload["summary"]["benchmark_review_status"]
        == "sequence_policy_benchmark_mixed_plan_window_underpowered"
    )
    assert payload["summary"]["readiness_checked_flag_count"] >= 430
    assert payload["summary"]["readiness_boundary_violation_count"] == 0
    assert payload["summary"]["readiness_source_artifact_count"] >= 44
    assert payload["summary"]["forbidden_training_or_runtime_input_blocked"] is False
    assert payload["summary"]["stage4_topk_signal"] is True
    assert payload["summary"]["stage4_binary_rule_insufficient"] is True
    assert payload["summary"]["stage7_success_gap"] == 0
    assert payload["summary"]["stage7_replay_free_backfill_exhausted"] is False
    assert payload["summary"]["protected_failure_contrast_ready_for_explicit_approval"] is True
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
    assert payload["summary"]["protected_failure_contrast_integration_ready"] is False
    assert (
        payload["summary"]["protected_failure_contrast_runner_status"]
        == "protected_plan_window_failure_contrast_runner_dry_run_ready"
    )
    assert (
        payload["summary"]["protected_failure_contrast_runner_manifest_status"]
        == "protected_plan_window_failure_contrast_manifest_ready_for_review"
    )
    assert (
        payload["summary"][
            "protected_failure_contrast_runner_manifest_declared_job_count"
        ]
        == 6
    )
    assert (
        len(
            payload["summary"][
                "protected_failure_contrast_runner_manifest_fingerprint"
            ]
        )
        == 64
    )
    assert (
        payload["summary"]["protected_failure_contrast_runner_collection_run_allowed"]
        is False
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
    assert payload["summary"]["protected_failure_contrast_approval_request_artifact"] == (
        "reports/strategy_arbitration/"
        "krk_protected_plan_window_failure_contrast_approval_request_v0.json"
    )
    assert (
        payload["summary"]["protected_failure_contrast_approval_request_status"]
        == "protected_plan_window_failure_contrast_approval_request_ready"
    )
    assert (
        payload["summary"]["protected_failure_contrast_approval_request_blockers"]
        == []
    )
    assert (
        payload["summary"][
            "protected_failure_contrast_approval_request_ready_for_collection"
        ]
        is True
    )
    assert (
        payload["summary"][
            "sequence_policy_after_protected_failure_contrast_refresh_status"
        ]
        == "sequence_policy_after_protected_failure_contrast_refresh_waiting_on_integration_outputs"
    )
    assert (
        payload["summary"][
            "sequence_policy_after_protected_failure_contrast_boundaries_preserved"
        ]
        is True
    )
    assert (
        payload["summary"][
            "sequence_policy_after_protected_failure_contrast_boundary_violation_count"
        ]
        == 0
    )
    assert payload["summary"]["sequence_policy_after_protected_failure_contrast_rows"] == 0
    assert (
        payload["summary"][
            "sequence_policy_after_protected_failure_contrast_stage7_training_row_count"
        ]
        == 0
    )
    assert (
        payload["summary"][
            "protected_failure_contrast_approval_receipt_created_by_request"
        ]
        is False
    )
    assert (
        payload["summary"]["protected_failure_contrast_approval_receipt_present"]
        is False
    )
    assert (
        payload["summary"]["protected_failure_contrast_approval_receipt_valid"]
        is False
    )
    assert payload["summary"][
        "protected_failure_contrast_approval_receipt_blockers"
    ] == ["approval_receipt_missing"]
    assert (
        payload["summary"][
            "protected_failure_contrast_post_success_refresh_required"
        ]
        is True
    )
    assert (
        payload["summary"]["protected_failure_contrast_post_success_refresh_script"]
        == "scripts/advance_krk_suite_from_current_gates_v0.py"
    )
    assert (
        payload["summary"]["protected_failure_contrast_post_success_refresh_scope"]
        == "full_passive_krk_suite_gate_stack"
    )
    assert (
        payload["summary"]["protected_failure_contrast_runtime_behavior_changed"]
        is False
    )
    assert (
        payload["summary"]["protected_failure_contrast_runtime_defaults_changed"]
        is False
    )
    assert (
        payload["summary"]["protected_failure_contrast_runtime_selector_implemented"]
        is False
    )
    assert payload["summary"]["protected_failure_contrast_runtime_score_changes"] is False
    assert payload["summary"]["protected_failure_contrast_runtime_direct_routing"] is False
    assert (
        payload["summary"][
            "protected_failure_contrast_runtime_dtm_or_tablebase_lookup"
        ]
        is False
    )
    assert (
        payload["summary"]["protected_failure_contrast_hidden_python_controller"]
        is False
    )
    assert (
        payload["summary"]["protected_failure_contrast_gameplay_topology_mutation"]
        is False
    )
    assert (
        payload["summary"]["protected_failure_contrast_selector_training_allowed"]
        is False
    )
    assert (
        payload["summary"]["protected_failure_contrast_stage7_promotion_allowed"]
        is False
    )
    assert (
        payload["summary"]["protected_failure_contrast_stage8_training_allowed"]
        is False
    )
    assert "stage4_state_local_topk_signal_present" in payload["pilot_findings"]
    assert "stage7_clean_success_controls_missing" not in payload["blockers"]
    assert (
        "protected_plan_window_failure_contrast_collection_pending_explicit_approval"
        in payload["blockers"]
    )


def test_underpowered_pilot_fixture_without_stage7_gap_needs_review():
    benchmark = {
        "decision": {"benchmark_executed_as_ready": False},
        "objectives": [
            {
                "objective_id": "stage4_state_local_first_move_contrast",
                "row_count": 1,
                "state_count": 1,
                "metrics": {
                    "top1_conversion_positive_by_state": 1.0,
                    "top3_conversion_positive_by_state": 1.0,
                    "precision": 1.0,
                    "recall": 1.0,
                    "negative_suppression": 1.0,
                },
            },
            {
                "objective_id": "protected_plan_window_entry_progress_exit_abort",
                "row_count": 10,
                "target_label_counts": {"conversion_positive": 5, "conversion_failure": 5},
                "failure_evidence_sparse": False,
            },
            {
                "objective_id": "stage7_heldout_sequence_success_vs_hard_negative",
                "row_count": 10,
                "target_label_counts": {"conversion_positive": 5, "conversion_failure": 5},
                "success_controls_met": True,
                "failure_controls_met": True,
            },
        ],
    }
    inputs = {
        "summary": {
            "row_count": 21,
            "stage7_clean_success_controls_required": 5,
            "selector_training_row_count": 0,
            "runtime_authorization_row_count": 0,
        }
    }
    backfill = {"decision": {"status": "not_needed"}, "summary": {}}
    benchmark_review = {
        "decision": {"status": "sequence_policy_benchmark_mixed_or_insufficient"},
        "blockers": [],
    }
    readiness = {"protected_failure_contrast_gate": {}, "explicit_gate_blockers": []}

    payload = _pilot.build_payload(
        benchmark=benchmark,
        benchmark_review=benchmark_review,
        inputs=inputs,
        backfill_audit=backfill,
        readiness=readiness,
    )

    assert payload["summary"]["stage7_success_gap"] == 0
    assert payload["decision"]["status"] == "sequence_policy_pilot_underpowered_needs_review"
    assert payload["decision"]["runtime_changes_allowed"] is False


def test_underpowered_pilot_routes_forbidden_training_rows_to_input_repair():
    benchmark = {
        "decision": {
            "benchmark_executed_as_ready": False,
            "status": "sequence_policy_benchmark_blocked_forbidden_training_or_runtime_rows",
        },
        "preflight": {"blockers": ["selector_training_rows_forbidden"]},
        "objectives": [
            {
                "objective_id": "stage4_state_local_first_move_contrast",
                "metrics": {
                    "top1_conversion_positive_by_state": 1.0,
                    "top3_conversion_positive_by_state": 1.0,
                    "precision": 0.8,
                    "recall": 0.4,
                    "negative_suppression": 0.9,
                },
            },
            {
                "objective_id": "protected_plan_window_entry_progress_exit_abort",
                "failure_evidence_sparse": True,
            },
            {
                "objective_id": "stage7_heldout_sequence_success_vs_hard_negative",
                "target_label_counts": {"conversion_positive": 5, "conversion_failure": 5},
            },
        ],
    }
    benchmark_review = {
        "decision": {
            "status": "sequence_policy_benchmark_review_blocked_forbidden_training_or_runtime_rows"
        },
        "blockers": ["selector_training_rows_forbidden"],
    }
    inputs = {
        "summary": {
            "row_count": 21,
            "stage7_clean_success_controls_required": 5,
            "selector_training_row_count": 1,
            "runtime_authorization_row_count": 0,
        }
    }
    backfill = {"decision": {"status": "not_needed"}, "summary": {}}
    readiness = {
        "protected_failure_contrast_gate": {"ready_for_explicit_approval": True},
        "explicit_gate_blockers": [
            "protected_plan_window_failure_contrast_collection_pending_explicit_approval"
        ],
    }

    payload = _pilot.build_payload(
        benchmark=benchmark,
        benchmark_review=benchmark_review,
        inputs=inputs,
        backfill_audit=backfill,
        readiness=readiness,
    )

    assert payload["summary"]["forbidden_training_or_runtime_input_blocked"] is True
    assert payload["decision"]["status"] == (
        "sequence_policy_pilot_blocked_forbidden_training_or_runtime_rows"
    )
    assert (
        payload["decision"]["recommended_next_step"]
        == "repair_sequence_policy_inputs_remove_training_or_runtime_rows"
    )
    assert "selector_training_rows_forbidden" in payload["blockers"]
    assert payload["decision"]["selector_training_allowed"] is False


def test_underpowered_pilot_routes_blocked_collection_request_to_repair():
    benchmark = {
        "decision": {"benchmark_executed_as_ready": True},
        "preflight": {"blockers": []},
        "objectives": [
            {
                "objective_id": "stage4_state_local_first_move_contrast",
                "metrics": {
                    "top1_conversion_positive_by_state": 1.0,
                    "top3_conversion_positive_by_state": 1.0,
                    "precision": 0.8,
                    "recall": 0.4,
                    "negative_suppression": 0.9,
                },
            },
            {
                "objective_id": "protected_plan_window_entry_progress_exit_abort",
                "failure_evidence_sparse": True,
            },
            {
                "objective_id": "stage7_heldout_sequence_success_vs_hard_negative",
                "target_label_counts": {
                    "conversion_positive": 5,
                    "conversion_failure": 5,
                },
            },
        ],
    }
    benchmark_review = {
        "decision": {"status": "sequence_policy_benchmark_mixed_plan_window_underpowered"},
        "blockers": [],
    }
    inputs = {
        "summary": {
            "row_count": 21,
            "stage7_clean_success_controls_required": 5,
            "selector_training_row_count": 0,
            "runtime_authorization_row_count": 0,
        }
    }
    backfill = {"decision": {"status": "not_needed"}, "summary": {}}
    readiness = {
        "protected_failure_contrast_gate": {
            "ready_for_explicit_approval": True,
            "approval_request_status": (
                "protected_plan_window_failure_contrast_approval_request_ready"
            ),
            "approval_request_blockers": [],
            "approval_request_ready_for_collection": False,
        },
        "explicit_gate_blockers": [
            "protected_plan_window_failure_contrast_collection_pending_explicit_approval"
        ],
    }

    payload = _pilot.build_payload(
        benchmark=benchmark,
        benchmark_review=benchmark_review,
        inputs=inputs,
        backfill_audit=backfill,
        readiness=readiness,
    )

    assert payload["summary"]["protected_failure_contrast_ready_for_explicit_approval"] is False
    assert (
        payload["summary"][
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
        == "sequence_policy_pilot_blocked_pending_protected_failure_contrast_approval_request_repair"
    )
    assert (
        payload["decision"]["recommended_next_step"]
        == "repair_protected_failure_contrast_approval_request_scope"
    )
    assert payload["decision"]["runtime_changes_allowed"] is False


def test_underpowered_pilot_routes_unsafe_protected_stack_to_repair():
    benchmark = {
        "decision": {"benchmark_executed_as_ready": True},
        "preflight": {"blockers": []},
        "objectives": [
            {
                "objective_id": "stage4_state_local_first_move_contrast",
                "metrics": {
                    "top1_conversion_positive_by_state": 1.0,
                    "top3_conversion_positive_by_state": 1.0,
                    "precision": 0.8,
                    "recall": 0.4,
                    "negative_suppression": 0.9,
                },
            },
            {
                "objective_id": "protected_plan_window_entry_progress_exit_abort",
                "failure_evidence_sparse": True,
            },
            {
                "objective_id": "stage7_heldout_sequence_success_vs_hard_negative",
                "target_label_counts": {
                    "conversion_positive": 5,
                    "conversion_failure": 5,
                },
            },
        ],
    }
    benchmark_review = {
        "decision": {"status": "sequence_policy_benchmark_mixed_plan_window_underpowered"},
        "blockers": [],
    }
    inputs = {
        "summary": {
            "row_count": 21,
            "stage7_clean_success_controls_required": 5,
            "selector_training_row_count": 0,
            "runtime_authorization_row_count": 0,
        }
    }
    readiness = {
        "protected_stack": {
            "ready": False,
            "rollback_paths_preserved": False,
            "active_stack_path_status": {"all_paths_safe": False},
        },
        "protected_failure_contrast_gate": {
            "ready_for_explicit_approval": True,
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

    payload = _pilot.build_payload(
        benchmark=benchmark,
        benchmark_review=benchmark_review,
        inputs=inputs,
        backfill_audit={"decision": {"status": "not_needed"}, "summary": {}},
        readiness=readiness,
    )

    assert "protected_stage5_6_stack_not_ready" in payload["blockers"]
    assert "protected_stack_rollback_paths_not_preserved" in payload["blockers"]
    assert "protected_stack_active_paths_unsafe" in payload["blockers"]
    assert (
        "protected_plan_window_failure_contrast_collection_pending_explicit_approval"
        not in payload["blockers"]
    )
    assert (
        payload["decision"]["status"]
        == "sequence_policy_pilot_blocked_pending_protected_stack_repair"
    )
    assert payload["decision"]["recommended_next_step"] == "repair_protected_stack_validation"
    assert payload["decision"]["runtime_changes_allowed"] is False


def test_underpowered_pilot_falls_back_when_collection_ready_is_null():
    benchmark = {
        "decision": {"benchmark_executed_as_ready": True},
        "preflight": {"blockers": []},
        "objectives": [
            {
                "objective_id": "stage4_state_local_first_move_contrast",
                "metrics": {
                    "top1_conversion_positive_by_state": 1.0,
                    "top3_conversion_positive_by_state": 1.0,
                    "precision": 0.8,
                    "recall": 0.4,
                    "negative_suppression": 0.9,
                },
            },
            {
                "objective_id": "protected_plan_window_entry_progress_exit_abort",
                "failure_evidence_sparse": True,
            },
            {
                "objective_id": "stage7_heldout_sequence_success_vs_hard_negative",
                "target_label_counts": {
                    "conversion_positive": 5,
                    "conversion_failure": 5,
                },
            },
        ],
    }
    benchmark_review = {
        "decision": {"status": "sequence_policy_benchmark_mixed_plan_window_underpowered"},
        "blockers": [],
    }
    inputs = {
        "summary": {
            "row_count": 21,
            "stage7_clean_success_controls_required": 5,
            "selector_training_row_count": 0,
            "runtime_authorization_row_count": 0,
        }
    }
    backfill = {"decision": {"status": "not_needed"}, "summary": {}}
    readiness = {
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
        },
        "explicit_gate_blockers": [
            "protected_plan_window_failure_contrast_collection_pending_explicit_approval"
        ],
    }

    payload = _pilot.build_payload(
        benchmark=benchmark,
        benchmark_review=benchmark_review,
        inputs=inputs,
        backfill_audit=backfill,
        readiness=readiness,
    )

    assert payload["summary"]["protected_failure_contrast_ready_for_explicit_approval"] is True
    assert (
        payload["summary"][
            "protected_failure_contrast_approval_request_ready_for_collection"
        ]
        is True
    )
    assert (
        "protected_plan_window_failure_contrast_collection_pending_explicit_approval"
        in payload["blockers"]
    )
    assert (
        payload["decision"]["status"]
        == "sequence_policy_pilot_underpowered_pending_protected_failure_contrast_collection"
    )
    assert payload["decision"]["runtime_changes_allowed"] is False
