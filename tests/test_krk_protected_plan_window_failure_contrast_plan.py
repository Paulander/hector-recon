#!/usr/bin/env python3
"""Tests for the protected plan-window failure contrast plan."""

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


_plan = _load_module(
    "write_krk_protected_plan_window_failure_contrast_plan_v0",
    "scripts/write_krk_protected_plan_window_failure_contrast_plan_v0.py",
)


def _read_report() -> dict:
    payload = json.loads(
        (
            ROOT
            / "reports/strategy_arbitration/krk_protected_plan_window_failure_contrast_plan_v0.json"
        ).read_text(encoding="utf-8")
    )
    assert isinstance(payload, dict)
    return payload


def test_failure_contrast_plan_reports_unique_protected_failure_gap():
    payload = _read_report()

    assert payload["schema_version"] == "krk_protected_plan_window_failure_contrast_plan.v0"
    assert payload["causal_status"] == "non_causal_failure_contrast_collection_plan"
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
    assert (
        payload["decision"]["status"]
        == "protected_plan_window_failure_contrast_plan_ready_pending_explicit_collection_approval"
    )
    assert payload["summary"]["input_row_count"] == 20
    assert payload["summary"]["unique_row_count"] == 20
    assert payload["summary"]["duplicate_row_count"] == 0
    assert payload["summary"]["unique_success_count"] == 19
    assert payload["summary"]["unique_failure_count"] == 1
    assert payload["summary"]["minimum_required_unique_failures"] == 5
    assert payload["summary"]["minimum_new_unique_failures_needed"] == 4
    assert payload["summary"]["selector_training_row_count"] == 0
    assert payload["summary"]["runtime_authorization_row_count"] == 0
    assert payload["summary"]["stage7_training_row_count"] == 0
    assert payload["decision"]["approval_required_before_label_execution"] is True
    assert payload["decision"]["implementation_allowed_by_this_packet"] is False
    assert payload["decision"]["label_run_allowed"] is False
    assert payload["decision"]["runtime_changes_allowed"] is False
    assert payload["decision"]["selector_training_allowed"] is False
    assert payload["decision"]["stage7_promotion_allowed"] is False
    assert payload["decision"]["stage8_training_allowed"] is False


def test_failure_contrast_plan_fixture_closes_when_unique_failures_met():
    rows = []
    for idx in range(5):
        rows.append(
            {
                "row_id": f"planwin.failure.{idx}",
                "input_group": "protected_plan_window",
                "source_stage": "stage5",
                "source_family": "fence_handoff_plan_window",
                "state_id": f"state.{idx}",
                "fen": f"8/8/8/8/8/8/8/{idx} w - - 0 1",
                "move_uci": "a1a2",
                "target_label": "conversion_failure",
                "outcome": "max_plies",
                "features": {"abort_terms": ["max_plies"]},
            }
        )
    payload = _plan.build_payload(
        inputs={"rows": rows},
        benchmark={
            "objectives": [
                {
                    "objective_id": "protected_plan_window_entry_progress_exit_abort",
                    "row_count": 5,
                    "failure_evidence_sparse": False,
                }
            ]
        },
        benchmark_review={"decision": {"status": "reviewed"}, "blockers": []},
        protected_windows={"summary": {"frame_count": 5}},
    )

    assert payload["decision"]["status"] == "protected_plan_window_failure_contrast_plan_not_needed"
    assert payload["summary"]["minimum_new_unique_failures_needed"] == 0
    assert payload["decision"]["label_run_allowed"] is False
    assert payload["decision"]["runtime_changes_allowed"] is False


def test_failure_contrast_plan_fixture_blocks_forbidden_sequence_input_rows():
    rows = [
        {
            "row_id": "tainted",
            "input_group": "protected_plan_window",
            "source_stage": "stage5",
            "source_family": "fence_handoff_plan_window",
            "state_id": "state.tainted",
            "fen": "8/8/8/8/8/8/8/K7 w - - 0 1",
            "move_uci": "a1a2",
            "target_label": "conversion_positive",
            "outcome": "mate",
            "usable_for_selector_training": True,
        }
    ]

    payload = _plan.build_payload(
        inputs={"rows": rows},
        benchmark={
            "objectives": [
                {
                    "objective_id": "protected_plan_window_entry_progress_exit_abort",
                    "row_count": 1,
                    "failure_evidence_sparse": True,
                }
            ]
        },
        benchmark_review={
            "decision": {"status": "sequence_policy_benchmark_mixed_plan_window_underpowered"},
            "blockers": ["protected_plan_window_failure_evidence_sparse"],
        },
        protected_windows={"summary": {"frame_count": 1}},
    )

    assert (
        payload["decision"]["status"]
        == "protected_plan_window_failure_contrast_plan_blocked_forbidden_training_or_runtime_rows"
    )
    assert payload["summary"]["forbidden_training_or_runtime_input_row_count"] == 1
    assert payload["summary"]["selector_training_row_count"] == 1
    assert payload["decision"]["label_run_allowed"] is False
    assert payload["decision"]["runtime_changes_allowed"] is False
