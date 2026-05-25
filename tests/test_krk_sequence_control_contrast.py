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
        == "sequence_control_stage4_review_ready_stage7_success_controls_insufficient"
    )
    assert payload["readiness"]["stage4_first_move_contrast_sandbox_review_ready"] is True
    assert payload["readiness"]["stage7_sequence_policy_benchmark_ready"] is False
    assert payload["readiness"]["broader_runtime_selector_ready"] is False
    assert payload["readiness"]["stage8_training_ready"] is False
    assert payload["summary"]["stage7_success_control_count"] == 2
    assert payload["summary"]["stage7_failure_control_count"] == 8
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

    payload = _probe.build_payload(dataset=dataset)

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
    option_ids = {option["option_id"] for option in payload["approval_options"]}
    assert option_ids == {
        "approve_stage4_first_move_contrast_sandbox",
        "approve_stage7_diverse_clean_label_run",
        "defer_runtime_and_labels_review_cross_stage_plan_capsule_evidence",
    }
    assert (
        payload["current_state"]["sequence_policy"]
        == "sequence_policy_benchmark_blocked_pending_clean_stage7_controls"
    )


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
        == "stop_at_gate_or_design_non_causal_sequence_policy_only"
    )
    assert (
        payload["recommendation"]["preferred_next_if_user_defers_both"]
        == "non_causal_sequence_policy_design_without_new_labels"
    )
