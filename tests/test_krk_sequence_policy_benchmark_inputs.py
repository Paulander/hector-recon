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


def test_sequence_policy_benchmark_inputs_are_non_causal_and_blocked_by_stage7_success():
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
    assert payload["gameplay_topology_mutation"] is False
    assert payload["stage7_promotion_allowed"] is False
    assert payload["stage8_training_allowed"] is False
    assert payload["summary"]["row_count"] == 79
    assert payload["summary"]["input_group_counts"]["stage4_first_move_contrast"] == 48
    assert payload["summary"]["input_group_counts"]["protected_plan_window"] == 21
    assert payload["summary"]["input_group_counts"]["stage7_clean_heldout_control"] == 10
    assert payload["summary"]["protected_plan_window_evidence_met"] is True
    assert payload["summary"]["stage7_clean_success_controls"] == 2
    assert payload["summary"]["stage7_clean_success_controls_met"] is False
    assert payload["summary"]["stage7_clean_failure_controls_met"] is True
    assert payload["summary"]["stage7_diverse_outputs_present"] is False
    assert payload["summary"]["stage7_diverse_new_controls"] == 0
    assert payload["summary"]["selector_training_row_count"] == 0
    assert payload["summary"]["runtime_authorization_row_count"] == 0
    assert (
        payload["decision"]["status"]
        == "sequence_policy_benchmark_inputs_blocked_pending_stage7_success_controls"
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
