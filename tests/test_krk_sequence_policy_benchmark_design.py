#!/usr/bin/env python3
"""Tests for KRK sequence-policy benchmark design/readiness artifact."""

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


_design = _load_module(
    "write_krk_sequence_policy_benchmark_design_v0",
    "scripts/write_krk_sequence_policy_benchmark_design_v0.py",
)


def _read_report(path: str) -> dict:
    payload = json.loads((ROOT / path).read_text(encoding="utf-8"))
    assert isinstance(payload, dict)
    return payload


def test_sequence_policy_benchmark_design_is_ready_but_blocks_training_and_runtime():
    payload = _read_report(
        "reports/strategy_arbitration/krk_sequence_policy_benchmark_design_v0.json"
    )

    assert payload["schema_version"] == "krk_sequence_policy_benchmark_design.v0"
    assert payload["causal_status"] == "non_causal_sequence_policy_design"
    assert payload["runtime_behavior_changed"] is False
    assert payload["runtime_selector_implemented"] is False
    assert payload["runtime_score_changes"] is False
    assert payload["runtime_direct_routing"] is False
    assert payload["runtime_dtm_or_tablebase_lookup"] is False
    assert payload["hidden_python_controller"] is False
    assert payload["gameplay_topology_mutation"] is False
    assert payload["stage7_promotion_allowed"] is False
    assert payload["stage8_training_allowed"] is False
    assert (
        payload["decision"]["status"]
        == "sequence_policy_benchmark_design_ready_non_causal"
    )
    assert payload["readiness"]["stage4_first_move_contrast_sandbox_review_ready"] is True
    assert (
        payload["readiness"][
            "stage4_first_move_contrast_sandbox_approval_request_status"
        ]
        == "stage4_first_move_contrast_sandbox_approval_request_ready"
    )
    assert (
        payload["readiness"][
            "stage4_first_move_contrast_sandbox_approval_request_blockers"
        ]
        == []
    )
    assert (
        payload["readiness"][
            "stage4_first_move_contrast_sandbox_approval_request_ready"
        ]
        is True
    )
    assert (
        payload["readiness"][
            "stage4_first_move_contrast_sandbox_approval_request_ready_for_runtime_approval"
        ]
        is True
    )
    assert payload["readiness"]["stage7_clean_success_controls"] == 11
    assert payload["readiness"]["stage7_clean_failure_controls"] == 39
    assert payload["readiness"]["stage7_clean_success_controls_met"] is True
    assert payload["readiness"]["stage7_clean_failure_controls_met"] is True
    assert payload["readiness"]["post_box_controls_runtime_authorization_eligible"] is False
    assert payload["readiness"]["protected_plan_window_frame_count"] >= 20
    assert payload["readiness"]["protected_plan_window_evidence_met"] is True
    assert payload["readiness"]["cross_stage_sequence_evidence_met"] is True
    assert payload["readiness"]["benchmark_ready"] is True
    assert (
        payload["readiness"]["current_benchmark_review_status"]
        == "sequence_policy_benchmark_mixed_plan_window_underpowered"
    )
    assert (
        payload["readiness"]["current_benchmark_review_next_step"]
        == "obtain_matching_approval_receipt_before_protected_failure_contrast_collection"
    )
    assert payload["readiness"]["current_benchmark_review_available"] is True
    assert (
        payload["decision"]["recommended_next_step"]
        == "obtain_matching_approval_receipt_before_protected_failure_contrast_collection"
    )
    passive = payload["passive_design_without_new_labels"]
    assert passive["status"] == "non_causal_sequence_policy_design_without_new_labels_ready"
    assert passive["depends_on_new_label_execution"] is False
    assert passive["depends_on_protected_failure_contrast_collection"] is False
    assert passive["current_evidence_limit"] == "protected_plan_window_failure_evidence_sparse"
    assert "protected plan-window failure-contrast collection" in passive[
        "blocked_work_without_explicit_approval"
    ]
    assert "selector training" in passive["blocked_work_without_explicit_approval"]
    assert "new Stage 7 label execution" in passive["blocked_work_without_explicit_approval"]
    assert payload["decision"]["runtime_changes_allowed"] is False
    assert payload["decision"]["selector_training_allowed"] is False
    assert payload["decision"]["stage7_promotion_allowed"] is False
    assert payload["decision"]["stage8_training_allowed"] is False
    stage4_pending = [
        item
        for item in payload["blocked_or_pending"]
        if item["item"] == "stage4_first_move_contrast_sandbox"
    ][0]
    assert stage4_pending["status"] == "review_ready_pending_explicit_approval"
    assert (
        stage4_pending["approval_request_status"]
        == "stage4_first_move_contrast_sandbox_approval_request_ready"
    )
    assert stage4_pending["approval_request_blockers"] == []
    assert stage4_pending["approval_request_ready_for_runtime_approval"] is True


def test_sequence_policy_benchmark_design_fixture_requires_clean_success_controls():
    payload = _design.build_payload(
        contrast_probe={
            "readiness": {"stage4_first_move_contrast_sandbox_review_ready": True}
        },
        contrast_dataset={},
        plan_capsule_review={
            "readiness": {
                "stage7_only_evidence": True,
                "policy_succeeded": False,
            }
        },
        post_box_controls={"summary": {"control_count": 14}},
        clean_controls={
            "summary": {
                "role_counts": {
                    "clean_sequence_success_control": 2,
                    "clean_sequence_hard_negative": 8,
                }
            }
        },
        sampling_manifest={"decision": {"status": "review_ready"}},
        protected_plan_windows={
            "summary": {
                "frame_count": 21,
                "protected_cross_stage_evidence_met": True,
            }
        },
    )

    assert (
        payload["decision"]["status"]
        == "sequence_policy_benchmark_blocked_pending_clean_stage7_controls"
    )
    assert (
        payload["passive_design_without_new_labels"]["status"]
        == "non_causal_sequence_policy_design_blocked_pending_ready_inputs"
    )
    assert payload["readiness"]["benchmark_ready"] is False
    assert payload["decision"]["stage8_training_allowed"] is False


def test_sequence_policy_benchmark_design_fixture_can_become_ready_non_causally():
    payload = _design.build_payload(
        contrast_probe={
            "readiness": {"stage4_first_move_contrast_sandbox_review_ready": True}
        },
        contrast_dataset={},
        plan_capsule_review={
            "readiness": {
                "stage7_only_evidence": False,
                "policy_succeeded": False,
            }
        },
        post_box_controls={"summary": {"control_count": 14}},
        clean_controls={
            "summary": {
                "role_counts": {
                    "clean_sequence_success_control": 5,
                    "clean_sequence_hard_negative": 5,
                }
            }
        },
        sampling_manifest={"decision": {"status": "review_ready"}},
        protected_plan_windows={
            "summary": {
                "frame_count": 21,
                "protected_cross_stage_evidence_met": True,
            }
        },
    )

    assert payload["decision"]["status"] == "sequence_policy_benchmark_design_ready_non_causal"
    assert (
        payload["passive_design_without_new_labels"]["status"]
        == "non_causal_sequence_policy_design_review_needed"
    )
    assert payload["readiness"]["benchmark_ready"] is True
    assert payload["decision"]["runtime_changes_allowed"] is False
    assert payload["decision"]["selector_training_allowed"] is False


def test_sequence_policy_benchmark_design_routes_forbidden_rows_to_repair():
    payload = _design.build_payload(
        contrast_probe={
            "readiness": {"stage4_first_move_contrast_sandbox_review_ready": True}
        },
        contrast_dataset={},
        plan_capsule_review={
            "readiness": {
                "stage7_only_evidence": False,
                "policy_succeeded": False,
            }
        },
        post_box_controls={"summary": {"control_count": 14}},
        clean_controls={
            "summary": {
                "role_counts": {
                    "clean_sequence_success_control": 5,
                    "clean_sequence_hard_negative": 5,
                }
            }
        },
        sampling_manifest={"decision": {"status": "review_ready"}},
        protected_plan_windows={
            "summary": {
                "frame_count": 21,
                "protected_cross_stage_evidence_met": True,
            }
        },
        benchmark_review={
            "decision": {
                "status": "sequence_policy_benchmark_review_blocked_forbidden_training_or_runtime_rows",
                "recommended_next_step": "repair_sequence_policy_inputs_remove_training_or_runtime_rows",
            },
            "blockers": ["selector_training_rows_forbidden"],
        },
    )

    assert payload["readiness"]["forbidden_training_or_runtime_input_blocked"] is True
    assert (
        payload["decision"]["status"]
        == "sequence_policy_benchmark_design_blocked_forbidden_training_or_runtime_rows"
    )
    assert (
        payload["decision"]["recommended_next_step"]
        == "repair_sequence_policy_inputs_remove_training_or_runtime_rows"
    )
    assert (
        payload["passive_design_without_new_labels"]["status"]
        == "non_causal_sequence_policy_design_blocked_forbidden_training_or_runtime_rows"
    )
    assert "selector_training_rows_forbidden" in payload["readiness"][
        "forbidden_training_or_runtime_input_blockers"
    ]
    assert payload["decision"]["selector_training_allowed"] is False


def test_sequence_policy_benchmark_design_propagates_stage4_approval_request_not_ready():
    payload = _design.build_payload(
        contrast_probe={
            "readiness": {"stage4_first_move_contrast_sandbox_review_ready": True}
        },
        contrast_dataset={},
        plan_capsule_review={
            "readiness": {
                "stage7_only_evidence": False,
                "policy_succeeded": False,
            }
        },
        post_box_controls={"summary": {"control_count": 14}},
        clean_controls={
            "summary": {
                "role_counts": {
                    "clean_sequence_success_control": 5,
                    "clean_sequence_hard_negative": 5,
                }
            }
        },
        sampling_manifest={"decision": {"status": "review_ready"}},
        protected_plan_windows={
            "summary": {
                "frame_count": 21,
                "protected_cross_stage_evidence_met": True,
            }
        },
        stage4_approval_request={
            "decision": {
                "status": (
                    "stage4_first_move_contrast_sandbox_approval_request_ready"
                )
            },
            "blockers": [],
            "approval_request_ready_for_runtime_approval": False,
        },
    )

    assert (
        payload["decision"]["status"]
        == "sequence_policy_benchmark_design_ready_non_causal"
    )
    assert (
        payload["readiness"][
            "stage4_first_move_contrast_sandbox_approval_request_status"
        ]
        == "stage4_first_move_contrast_sandbox_approval_request_ready"
    )
    assert (
        payload["readiness"][
            "stage4_first_move_contrast_sandbox_approval_request_blockers"
        ]
        == []
    )
    assert (
        payload["readiness"][
            "stage4_first_move_contrast_sandbox_approval_request_ready"
        ]
        is False
    )
    assert (
        payload["readiness"][
            "stage4_first_move_contrast_sandbox_approval_request_ready_for_runtime_approval"
        ]
        is False
    )
    stage4_pending = [
        item
        for item in payload["blocked_or_pending"]
        if item["item"] == "stage4_first_move_contrast_sandbox"
    ][0]
    assert stage4_pending["status"] == "approval_request_blocked_pending_repair"
    assert stage4_pending["approval_request_blockers"] == []
    assert stage4_pending["approval_request_ready_for_runtime_approval"] is False
    assert payload["decision"]["runtime_changes_allowed"] is False
