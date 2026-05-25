#!/usr/bin/env python3
"""Tests for the gate-aware KRK sequence-policy benchmark harness."""

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


_benchmark = _load_module(
    "run_krk_sequence_policy_benchmark_v0",
    "scripts/run_krk_sequence_policy_benchmark_v0.py",
)


def _read_report(path: str) -> dict:
    payload = json.loads((ROOT / path).read_text(encoding="utf-8"))
    assert isinstance(payload, dict)
    return payload


def test_sequence_policy_benchmark_blocks_current_underpowered_inputs():
    payload = _read_report(
        "reports/strategy_arbitration/krk_sequence_policy_benchmark_v0.json"
    )

    assert payload["schema_version"] == "krk_sequence_policy_benchmark.v0"
    assert payload["causal_status"] == "non_causal_sequence_policy_benchmark"
    assert payload["runtime_behavior_changed"] is False
    assert payload["runtime_selector_implemented"] is False
    assert payload["runtime_score_changes"] is False
    assert payload["runtime_direct_routing"] is False
    assert payload["runtime_dtm_or_tablebase_lookup"] is False
    assert payload["gameplay_topology_mutation"] is False
    assert payload["stage7_promotion_allowed"] is False
    assert payload["stage8_training_allowed"] is False
    assert payload["preflight"]["benchmark_input_ready"] is False
    assert payload["preflight"]["blockers"] == ["stage7_clean_success_controls_missing"]
    assert payload["preflight"]["selector_training_row_count"] == 0
    assert payload["preflight"]["runtime_authorization_row_count"] == 0
    assert (
        payload["decision"]["status"]
        == "sequence_policy_benchmark_blocked_pending_stage7_success_controls"
    )
    assert payload["decision"]["benchmark_executed_as_ready"] is False
    assert payload["decision"]["runtime_changes_allowed"] is False
    assert payload["decision"]["label_run_allowed"] is False
    assert payload["decision"]["selector_training_allowed"] is False
    assert payload["decision"]["stage8_training_allowed"] is False


def test_sequence_policy_benchmark_fixture_runs_when_inputs_ready():
    rows = [
        {
            "row_id": "stage4.good",
            "input_group": "stage4_first_move_contrast",
            "state_id": "s4",
            "move_uci": "a1a2",
            "target_label": "conversion_positive",
            "features": {"rook_mid_rank8_cut_candidate": True},
            "stage7_heldout_challenge": False,
            "usable_for_selector_training": False,
            "usable_for_runtime_authorization": False,
        },
        {
            "row_id": "stage4.bad",
            "input_group": "stage4_first_move_contrast",
            "state_id": "s4",
            "move_uci": "a1a8",
            "target_label": "conversion_failure",
            "features": {"rook_mid_rank8_cut_candidate": False},
            "stage7_heldout_challenge": False,
            "usable_for_selector_training": False,
            "usable_for_runtime_authorization": False,
        },
        {
            "row_id": "plan.1",
            "input_group": "protected_plan_window",
            "target_label": "conversion_positive",
            "features": {
                "entry_terms_confirmed": ["reward_confirmed"],
                "progress_terms_after_first_reply": ["handoff_gap_absent"],
                "abort_terms": [],
            },
            "stage7_heldout_challenge": False,
            "usable_for_selector_training": False,
            "usable_for_runtime_authorization": False,
        },
    ]
    for idx in range(5):
        rows.append(
            {
                "row_id": f"stage7.success.{idx}",
                "input_group": "stage7_clean_heldout_control",
                "target_label": "conversion_positive",
                "features": {"selected_provider": "krk.edge_trap_close"},
                "stage7_heldout_challenge": True,
                "usable_for_selector_training": False,
                "usable_for_runtime_authorization": False,
            }
        )
        rows.append(
            {
                "row_id": f"stage7.failure.{idx}",
                "input_group": "stage7_clean_heldout_control",
                "target_label": "conversion_failure",
                "features": {"selected_provider": "krk.stage0_basin"},
                "stage7_heldout_challenge": True,
                "usable_for_selector_training": False,
                "usable_for_runtime_authorization": False,
            }
        )

    payload = _benchmark.build_payload(
        inputs={
            "summary": {
                "benchmark_input_ready": True,
                "protected_plan_window_evidence_met": True,
                "stage7_clean_success_controls_met": True,
                "stage7_clean_failure_controls_met": True,
            },
            "rows": rows,
        }
    )

    assert (
        payload["decision"]["status"]
        == "sequence_policy_benchmark_ready_non_causal_results_available"
    )
    assert payload["decision"]["benchmark_executed_as_ready"] is True
    assert payload["preflight"]["blockers"] == []
    assert payload["preflight"]["selector_training_row_count"] == 0
    assert payload["preflight"]["runtime_authorization_row_count"] == 0
    assert payload["decision"]["runtime_changes_allowed"] is False
    assert payload["decision"]["selector_training_allowed"] is False
