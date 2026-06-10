#!/usr/bin/env python3
"""Tests for the non-causal KRK sequence-policy input probe."""

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


_probe = _load_module(
    "probe_krk_sequence_policy_inputs_v0",
    "scripts/probe_krk_sequence_policy_inputs_v0.py",
)


def _read_report(path: str) -> dict:
    payload = json.loads((ROOT / path).read_text(encoding="utf-8"))
    assert isinstance(payload, dict)
    return payload


def test_sequence_policy_input_probe_is_non_causal_and_ready():
    payload = _read_report(
        "reports/strategy_arbitration/krk_sequence_policy_input_probe_v0.json"
    )

    assert payload["schema_version"] == "krk_sequence_policy_input_probe.v0"
    assert payload["causal_status"] == "non_causal_sequence_policy_input_probe"
    assert payload["runtime_behavior_changed"] is False
    assert payload["runtime_selector_implemented"] is False
    assert payload["runtime_score_changes"] is False
    assert payload["runtime_direct_routing"] is False
    assert payload["runtime_dtm_or_tablebase_lookup"] is False
    assert payload["gameplay_topology_mutation"] is False
    assert payload["stage7_promotion_allowed"] is False
    assert payload["stage8_training_allowed"] is False
    assert payload["summary"]["row_count"] == 118
    assert payload["summary"]["stage4_topk_signal"] is True
    assert payload["summary"]["stage4_binary_heuristic_sufficient"] is False
    assert payload["summary"]["protected_plan_window_failure_sparse"] is True
    assert payload["summary"]["stage7_underpowered"] is False
    assert payload["summary"]["selector_training_row_count"] == 0
    assert payload["summary"]["runtime_authorization_row_count"] == 0
    assert (
        payload["summary"]["current_benchmark_review_status"]
        == "sequence_policy_benchmark_mixed_plan_window_underpowered_"
        "blocked_pending_protected_failure_contrast_control_plane_gate_review"
    )
    assert (
        payload["summary"]["current_benchmark_review_next_step"]
        == "review_current_control_plane_gate_for_protected_failure_contrast_collection"
    )
    assert payload["summary"]["current_benchmark_review_available"] is False
    assert (
        payload["summary"][
            "protected_failure_contrast_collection_option_available"
        ]
        is False
    )
    assert (
        payload["summary"][
            "protected_failure_contrast_collection_command_available"
        ]
        is False
    )
    assert (
        payload["summary"][
            "protected_failure_contrast_control_plane_gate_review_required"
        ]
        is False
    )
    assert (
        payload["decision"]["status"]
        == "sequence_policy_input_probe_ready_for_full_non_causal_benchmark"
    )
    assert (
        payload["decision"]["recommended_next_step"]
        == "run_full_non_causal_sequence_policy_benchmark"
    )
    assert payload["decision"]["runtime_changes_allowed"] is False
    assert payload["decision"]["label_run_allowed"] is False
    assert payload["decision"]["selector_training_allowed"] is False
    assert payload["decision"]["stage7_promotion_allowed"] is False
    assert payload["decision"]["stage8_training_allowed"] is False


def test_sequence_policy_input_probe_fixture_can_be_ready_with_balanced_stage7():
    rows = []
    for idx in range(5):
        rows.append(
            {
                "row_id": f"stage7.success.{idx}",
                "input_group": "stage7_clean_heldout_control",
                "target_label": "conversion_positive",
                "features": {},
                "usable_for_selector_training": False,
                "usable_for_runtime_authorization": False,
            }
        )
        rows.append(
            {
                "row_id": f"stage7.failure.{idx}",
                "input_group": "stage7_clean_heldout_control",
                "target_label": "conversion_failure",
                "features": {},
                "usable_for_selector_training": False,
                "usable_for_runtime_authorization": False,
            }
        )
    rows.append(
        {
            "row_id": "stage4.a",
            "input_group": "stage4_first_move_contrast",
            "target_label": "conversion_positive",
            "features": {"rook_mid_rank8_cut_candidate": True},
            "state_id": "state.a",
            "move_uci": "a1a2",
            "usable_for_selector_training": False,
            "usable_for_runtime_authorization": False,
        }
    )
    rows.append(
        {
            "row_id": "planwin.a",
            "input_group": "protected_plan_window",
            "target_label": "conversion_positive",
            "features": {},
            "source_stage": "stage5",
            "usable_for_selector_training": False,
            "usable_for_runtime_authorization": False,
        }
    )

    payload = _probe.build_payload(
        inputs={
            "summary": {"benchmark_input_ready": True},
            "rows": rows,
        }
    )

    assert (
        payload["decision"]["status"]
        == "sequence_policy_input_probe_ready_for_full_non_causal_benchmark"
    )
    assert payload["stage7_heldout_probe"]["underpowered"] is False
    assert payload["decision"]["runtime_changes_allowed"] is False
    assert payload["decision"]["selector_training_allowed"] is False


def test_sequence_policy_input_probe_routes_forbidden_training_rows_to_repair():
    rows = []
    for idx in range(5):
        rows.append(
            {
                "row_id": f"stage7.success.{idx}",
                "input_group": "stage7_clean_heldout_control",
                "target_label": "conversion_positive",
                "features": {},
                "usable_for_selector_training": False,
                "usable_for_runtime_authorization": False,
            }
        )
        rows.append(
            {
                "row_id": f"stage7.failure.{idx}",
                "input_group": "stage7_clean_heldout_control",
                "target_label": "conversion_failure",
                "features": {},
                "usable_for_selector_training": False,
                "usable_for_runtime_authorization": False,
            }
        )
    rows.append(
        {
            "row_id": "tainted.selector",
            "input_group": "protected_plan_window",
            "target_label": "conversion_failure",
            "features": {},
            "source_stage": "stage5",
            "usable_for_selector_training": True,
            "usable_for_runtime_authorization": False,
        }
    )

    payload = _probe.build_payload(
        inputs={"summary": {"benchmark_input_ready": True}, "rows": rows},
        benchmark_review={
            "decision": {
                "status": "sequence_policy_benchmark_review_blocked_forbidden_training_or_runtime_rows"
            },
            "blockers": ["selector_training_rows_forbidden"],
        },
    )

    assert payload["summary"]["forbidden_training_or_runtime_input_blocked"] is True
    assert payload["summary"]["selector_training_row_count"] == 1
    assert (
        payload["decision"]["status"]
        == "sequence_policy_input_probe_blocked_forbidden_training_or_runtime_rows"
    )
    assert (
        payload["decision"]["recommended_next_step"]
        == "repair_sequence_policy_inputs_remove_training_or_runtime_rows"
    )
    assert payload["decision"]["selector_training_allowed"] is False


def test_sequence_policy_input_probe_routes_missing_collection_command_to_gate_review():
    benchmark_review = _read_report(
        "reports/strategy_arbitration/krk_sequence_policy_benchmark_review_v0.json"
    )
    benchmark_review["current_control_plane_gate"][
        "protected_failure_contrast_collection_command_available"
    ] = False
    benchmark_review["current_control_plane_gate"][
        "protected_failure_contrast_collection_blocked_by_option_id"
    ] = "review_protected_plan_window_failure_contrast_execution_readiness"

    payload = _probe.build_payload(benchmark_review=benchmark_review)

    assert (
        payload["decision"]["status"]
        == "sequence_policy_input_probe_ready_for_full_non_causal_benchmark"
    )
    assert (
        payload["decision"]["recommended_next_step"]
        == "run_full_non_causal_sequence_policy_benchmark"
    )
    assert (
        payload["summary"][
            "protected_failure_contrast_control_plane_gate_review_required"
        ]
        is False
    )
    assert (
        payload["summary"][
            "protected_failure_contrast_collection_command_available"
        ]
        is False
    )
    assert payload["decision"]["runtime_changes_allowed"] is False
    assert payload["decision"]["label_run_allowed"] is False
