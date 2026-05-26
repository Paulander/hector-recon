#!/usr/bin/env python3
"""Tests for assembled KRK sequence-policy benchmark inputs."""

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


_inputs = _load_module(
    "assemble_krk_sequence_policy_benchmark_inputs_v0",
    "scripts/assemble_krk_sequence_policy_benchmark_inputs_v0.py",
)


def _read_report(path: str) -> dict:
    payload = json.loads((ROOT / path).read_text(encoding="utf-8"))
    assert isinstance(payload, dict)
    return payload


def test_sequence_policy_benchmark_inputs_are_non_causal_and_ready_after_stage7_success():
    payload = _read_report(
        "reports/strategy_arbitration/krk_sequence_policy_benchmark_inputs_v0.json"
    )

    assert payload["schema_version"] == "krk_sequence_policy_benchmark_inputs.v0"
    assert payload["causal_status"] == "non_causal_sequence_policy_input_assembly"
    assert payload["runtime_behavior_changed"] is False
    assert payload["runtime_selector_implemented"] is False
    assert payload["runtime_score_changes"] is False
    assert payload["runtime_direct_routing"] is False
    assert payload["runtime_dtm_or_tablebase_lookup"] is False
    assert payload["hidden_python_controller"] is False
    assert payload["gameplay_topology_mutation"] is False
    assert payload["stage7_promotion_allowed"] is False
    assert payload["stage8_training_allowed"] is False
    assert payload["summary"]["row_count"] == 118
    assert payload["summary"]["input_group_counts"]["stage4_first_move_contrast"] == 48
    assert payload["summary"]["input_group_counts"]["protected_plan_window"] == 20
    assert payload["summary"]["input_group_counts"]["stage7_clean_heldout_control"] == 50
    assert payload["summary"]["protected_plan_window_evidence_met"] is True
    assert payload["summary"]["stage7_clean_success_controls"] == 11
    assert payload["summary"]["stage7_clean_success_controls_met"] is True
    assert payload["summary"]["stage7_clean_failure_controls_met"] is True
    assert payload["summary"]["stage7_diverse_outputs_present"] is True
    assert payload["summary"]["stage7_diverse_new_controls"] == 0
    assert (
        payload["summary"]["protected_failure_contrast_integration_status"]
        == "protected_plan_window_failure_contrast_integration_pending_outputs"
    )
    assert payload["summary"]["protected_failure_contrast_integration_ready"] is False
    assert payload["summary"]["protected_failure_contrast_row_count"] == 0
    assert payload["summary"]["protected_failure_contrast_skipped_counts"] == {}
    assert (
        payload["summary"]["current_benchmark_review_status"]
        == "sequence_policy_benchmark_mixed_plan_window_underpowered"
    )
    assert (
        payload["summary"]["current_benchmark_review_next_step"]
        == "obtain_matching_approval_receipt_before_protected_failure_contrast_collection"
    )
    assert payload["summary"]["current_benchmark_review_available"] is True
    assert payload["summary"]["selector_training_row_count"] == 0
    assert payload["summary"]["runtime_authorization_row_count"] == 0
    assert (
        payload["decision"]["status"]
        == "sequence_policy_benchmark_inputs_ready_non_causal"
    )
    assert (
        payload["decision"]["recommended_next_step"]
        == "obtain_matching_approval_receipt_before_protected_failure_contrast_collection"
    )
    assert payload["decision"]["runtime_changes_allowed"] is False
    assert payload["decision"]["label_run_allowed"] is False
    assert payload["decision"]["selector_training_allowed"] is False
    assert payload["decision"]["stage8_training_allowed"] is False


def test_sequence_policy_benchmark_inputs_preserve_label_semantics():
    payload = _read_report(
        "reports/strategy_arbitration/krk_sequence_policy_benchmark_inputs_v0.json"
    )

    assert payload["label_semantics"]["stage4_forced_first_move_rows_are_capacity_contrast"]
    assert payload["label_semantics"]["protected_plan_window_rows_are_replay_free_context"]
    assert payload["label_semantics"]["stage7_rows_are_heldout_challenge_only"]
    assert payload["label_semantics"]["capacity_labels_are_not_runtime_ownership_labels"]
    for row in payload["rows"]:
        assert row["causal_status"] == "non_causal_sequence_policy_input"
        assert row["usable_for_selector_training"] is False
        assert row["usable_for_runtime_authorization"] is False
        if row["input_group"] == "stage7_clean_heldout_control":
            assert row["stage7_heldout_challenge"] is True
        else:
            assert row["stage7_heldout_challenge"] is False


def test_sequence_policy_benchmark_inputs_fixture_can_be_ready_non_causally():
    payload = _inputs.build_payload(
        contrast_dataset={
            "rows": [
                {
                    "row_type": "forced_first_move_candidate",
                    "row_id": "s4.a",
                    "source_stage": "stage4",
                    "source_family": "edge_trap_wrong_tempo",
                    "state_id": "state.a",
                    "fen": "8/8/8/8/8/8/8/8 w - - 0 1",
                    "move_uci": "a1a2",
                    "target_label": "conversion_positive",
                    "result": "mate",
                    "features": {},
                }
            ]
        },
        protected_plan_windows={
            "summary": {"protected_cross_stage_evidence_met": True},
            "frames": [
                {
                    "frame_id": "planwin.a",
                    "source_stage": "stage5",
                    "source_family": "fence_handoff_plan_window",
                    "fen": "8/8/8/8/8/8/8/8 w - - 0 1",
                    "move_uci": "a1a2",
                    "h40_outcome_label": "conversion_positive",
                    "result": "mate",
                }
            ],
        },
        stage7_clean_controls={
            "controls": [
                {
                    "state_id": f"success.{idx}",
                    "fen": f"8/8/8/8/{idx}/8/8/8 w - - 0 1",
                    "move_uci": "a1a2",
                    "control_role": "clean_sequence_success_control",
                    "result": "mate",
                }
                for idx in range(5)
            ]
            + [
                {
                    "state_id": f"failure.{idx}",
                    "fen": f"8/8/8/8/8/{idx}/8/8 w - - 0 1",
                    "move_uci": "a1a2",
                    "control_role": "clean_sequence_hard_negative",
                    "result": "max_plies",
                }
                for idx in range(5)
            ]
        },
        stage7_diverse_integration={"summary": {}, "new_controls": []},
        protected_failure_contrast_integration={"summary": {}, "integrated_failure_contrasts": []},
        sequence_policy_design={
            "readiness": {"stage7_clean_success_controls_required": 5}
        },
    )

    assert payload["summary"]["benchmark_input_ready"] is True
    assert payload["decision"]["status"] == "sequence_policy_benchmark_inputs_ready_non_causal"
    assert payload["decision"]["runtime_changes_allowed"] is False
    assert payload["decision"]["selector_training_allowed"] is False


def test_sequence_policy_benchmark_inputs_fixture_consumes_diverse_integration():
    payload = _inputs.build_payload(
        contrast_dataset={"rows": []},
        protected_plan_windows={
            "summary": {"protected_cross_stage_evidence_met": True},
            "frames": [],
        },
        stage7_clean_controls={
            "controls": [
                {
                    "state_id": f"base.success.{idx}",
                    "fen": f"8/8/8/8/8/8/8/{idx} w - - 0 1",
                    "move_uci": "a1a2",
                    "control_role": "clean_sequence_success_control",
                    "result": "mate",
                }
                for idx in range(2)
            ]
            + [
                {
                    "state_id": f"base.failure.{idx}",
                    "fen": f"8/8/8/8/8/8/7{idx}/8 w - - 0 1",
                    "move_uci": "a1a2",
                    "control_role": "clean_sequence_hard_negative",
                    "result": "max_plies",
                }
                for idx in range(5)
            ]
        },
        stage7_diverse_integration={
            "summary": {"outputs_present_count": 1, "new_control_count": 3},
            "new_controls": [
                {
                    "state_id": f"diverse.success.{idx}",
                    "fen": f"8/8/8/8/8/{idx}/8/8 w - - 0 1",
                    "move_uci": "a1a2",
                    "control_role": "clean_sequence_success_control",
                    "result": "mate",
                    "source_job_id": "fixture.job",
                    "source_stage_names": ["Box_Small"],
                }
                for idx in range(3)
            ],
        },
        protected_failure_contrast_integration={"summary": {}, "integrated_failure_contrasts": []},
        sequence_policy_design={
            "readiness": {"stage7_clean_success_controls_required": 5}
        },
    )

    assert payload["summary"]["stage7_clean_success_controls"] == 5
    assert payload["summary"]["stage7_clean_success_controls_met"] is True
    assert payload["summary"]["stage7_clean_failure_controls_met"] is True
    assert payload["summary"]["stage7_diverse_outputs_present"] is True
    assert payload["summary"]["stage7_diverse_new_controls"] == 3
    assert payload["summary"]["benchmark_input_ready"] is True
    assert payload["decision"]["status"] == "sequence_policy_benchmark_inputs_ready_non_causal"
    assert payload["decision"]["runtime_changes_allowed"] is False
    assert payload["decision"]["selector_training_allowed"] is False


def test_sequence_policy_benchmark_inputs_fixture_consumes_ready_protected_failure_contrasts():
    payload = _inputs.build_payload(
        contrast_dataset={"rows": []},
        protected_plan_windows={
            "summary": {"protected_cross_stage_evidence_met": True},
            "frames": [],
        },
        stage7_clean_controls={
            "controls": [
                {
                    "state_id": f"success.{idx}",
                    "fen": f"8/8/8/8/8/8/8/{idx} w - - 0 1",
                    "move_uci": "a1a2",
                    "control_role": "clean_sequence_success_control",
                    "result": "mate",
                }
                for idx in range(5)
            ]
            + [
                {
                    "state_id": f"failure.{idx}",
                    "fen": f"8/8/8/8/8/8/7{idx}/8 w - - 0 1",
                    "move_uci": "a1a2",
                    "control_role": "clean_sequence_hard_negative",
                    "result": "max_plies",
                }
                for idx in range(5)
            ]
        },
        stage7_diverse_integration={"summary": {}, "new_controls": []},
        protected_failure_contrast_integration={
            "decision": {
                "status": "protected_plan_window_failure_contrast_integration_ready_for_passive_benchmark_refresh"
            },
            "summary": {"integration_ready": True},
            "integrated_failure_contrasts": [
                {
                    "row_id": "protected_failure_contrast.fixture",
                    "job_id": "job.fixture",
                    "source_stage": "stage5",
                    "source_family": "fence_handoff_plan_window",
                    "seed_frame_id": "frame.fixture",
                    "fen": "8/8/8/8/8/8/8/R3K2k w - - 0 1",
                    "anchor_move_uci": "a1a8",
                    "result": "max_plies",
                    "h40_outcome_label": "conversion_failure",
                    "control_role": "protected_plan_window_failure_contrast",
                    "stage7_training_row": False,
                    "usable_for_selector_training": False,
                    "usable_for_runtime_authorization": False,
                    "stage7_heldout_challenge": False,
                }
            ],
        },
        sequence_policy_design={
            "readiness": {"stage7_clean_success_controls_required": 5}
        },
    )

    assert payload["summary"]["protected_failure_contrast_integration_ready"] is True
    assert payload["summary"]["protected_failure_contrast_row_count"] == 1
    row = [
        row
        for row in payload["rows"]
        if row["input_group"] == "protected_plan_window_failure_contrast"
    ][0]
    assert row["target_label"] == "conversion_failure"
    assert row["usable_for_selector_training"] is False
    assert row["usable_for_runtime_authorization"] is False
    assert payload["decision"]["runtime_changes_allowed"] is False


def test_sequence_policy_benchmark_inputs_rejects_unready_protected_failure_rows():
    payload = _inputs.build_payload(
        contrast_dataset={"rows": []},
        protected_plan_windows={"summary": {"protected_cross_stage_evidence_met": True}, "frames": []},
        stage7_clean_controls={
            "controls": [
                {
                    "state_id": f"success.{idx}",
                    "fen": f"8/8/8/8/8/8/8/{idx} w - - 0 1",
                    "move_uci": "a1a2",
                    "control_role": "clean_sequence_success_control",
                    "result": "mate",
                }
                for idx in range(5)
            ]
            + [
                {
                    "state_id": f"failure.{idx}",
                    "fen": f"8/8/8/8/8/8/7{idx}/8 w - - 0 1",
                    "move_uci": "a1a2",
                    "control_role": "clean_sequence_hard_negative",
                    "result": "max_plies",
                }
                for idx in range(5)
            ]
        },
        stage7_diverse_integration={"summary": {}, "new_controls": []},
        protected_failure_contrast_integration={
            "decision": {"status": "protected_plan_window_failure_contrast_integration_pending_outputs"},
            "summary": {"integration_ready": True},
            "integrated_failure_contrasts": [
                {
                    "row_id": "protected_failure_contrast.fixture",
                    "job_id": "job.fixture",
                    "source_stage": "stage5",
                    "source_family": "fence_handoff_plan_window",
                    "seed_frame_id": "frame.fixture",
                    "fen": "8/8/8/8/8/8/8/R3K2k w - - 0 1",
                    "anchor_move_uci": "a1a8",
                    "result": "max_plies",
                    "h40_outcome_label": "conversion_failure",
                    "control_role": "protected_plan_window_failure_contrast",
                    "stage7_training_row": False,
                    "usable_for_selector_training": False,
                    "usable_for_runtime_authorization": False,
                    "stage7_heldout_challenge": False,
                }
            ],
        },
        sequence_policy_design={"readiness": {"stage7_clean_success_controls_required": 5}},
    )

    assert payload["summary"]["protected_failure_contrast_row_count"] == 0
    assert payload["summary"]["protected_failure_contrast_skipped_counts"] == {
        "integration_status_not_ready": 1
    }
    assert all(
        row["input_group"] != "protected_plan_window_failure_contrast"
        for row in payload["rows"]
    )
    assert payload["decision"]["selector_training_allowed"] is False


def test_sequence_policy_benchmark_inputs_rejects_tainted_protected_failure_rows():
    payload = _inputs.build_payload(
        contrast_dataset={"rows": []},
        protected_plan_windows={"summary": {"protected_cross_stage_evidence_met": True}, "frames": []},
        stage7_clean_controls={
            "controls": [
                {
                    "state_id": f"success.{idx}",
                    "fen": f"8/8/8/8/8/8/8/{idx} w - - 0 1",
                    "move_uci": "a1a2",
                    "control_role": "clean_sequence_success_control",
                    "result": "mate",
                }
                for idx in range(5)
            ]
            + [
                {
                    "state_id": f"failure.{idx}",
                    "fen": f"8/8/8/8/8/8/7{idx}/8 w - - 0 1",
                    "move_uci": "a1a2",
                    "control_role": "clean_sequence_hard_negative",
                    "result": "max_plies",
                }
                for idx in range(5)
            ]
        },
        stage7_diverse_integration={"summary": {}, "new_controls": []},
        protected_failure_contrast_integration={
            "decision": {
                "status": "protected_plan_window_failure_contrast_integration_ready_for_passive_benchmark_refresh"
            },
            "summary": {"integration_ready": True},
            "integrated_failure_contrasts": [
                {
                    "row_id": "protected_failure_contrast.tainted",
                    "job_id": "job.tainted",
                    "source_stage": "stage5",
                    "source_family": "fence_handoff_plan_window",
                    "seed_frame_id": "frame.tainted",
                    "fen": "8/8/8/8/8/8/8/R3K2k w - - 0 1",
                    "anchor_move_uci": "a1a8",
                    "result": "max_plies",
                    "h40_outcome_label": "conversion_failure",
                    "control_role": "protected_plan_window_failure_contrast",
                    "stage7_training_row": False,
                    "usable_for_selector_training": True,
                    "usable_for_runtime_authorization": False,
                    "stage7_heldout_challenge": False,
                }
            ],
        },
        sequence_policy_design={"readiness": {"stage7_clean_success_controls_required": 5}},
    )

    assert payload["summary"]["protected_failure_contrast_row_count"] == 0
    assert payload["summary"]["protected_failure_contrast_skipped_counts"] == {
        "selector_training_must_be_false": 1
    }
    assert payload["summary"]["selector_training_row_count"] == 0
    assert payload["decision"]["runtime_changes_allowed"] is False


def test_sequence_policy_benchmark_inputs_reports_stage7_failure_gap_separately():
    payload = _inputs.build_payload(
        contrast_dataset={"rows": []},
        protected_plan_windows={
            "summary": {"protected_cross_stage_evidence_met": True},
            "frames": [],
        },
        stage7_clean_controls={
            "controls": [
                {
                    "state_id": f"success.{idx}",
                    "fen": f"8/8/8/8/8/8/8/{idx} w - - 0 1",
                    "move_uci": "a1a2",
                    "control_role": "clean_sequence_success_control",
                    "result": "mate",
                }
                for idx in range(5)
            ]
        },
        stage7_diverse_integration={"summary": {}, "new_controls": []},
        protected_failure_contrast_integration={"summary": {}, "integrated_failure_contrasts": []},
        sequence_policy_design={
            "readiness": {"stage7_clean_success_controls_required": 5}
        },
    )

    assert payload["summary"]["stage7_clean_success_controls_met"] is True
    assert payload["summary"]["stage7_clean_failure_controls_met"] is False
    assert (
        payload["decision"]["status"]
        == "sequence_policy_benchmark_inputs_blocked_pending_stage7_failure_controls"
    )
    assert (
        payload["decision"]["recommended_next_step"]
        == "approve_stage7_clean_failure_control_collection_or_repair_inputs"
    )
    assert payload["decision"]["label_run_allowed"] is False
    assert payload["decision"]["runtime_changes_allowed"] is False
