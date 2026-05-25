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
        == "sequence_policy_pilot_ready_for_full_benchmark_after_label_gate"
    )
    assert payload["summary"]["benchmark_executed_as_ready"] is False
    assert payload["summary"]["stage4_topk_signal"] is True
    assert payload["summary"]["stage4_binary_rule_insufficient"] is True
    assert payload["summary"]["stage7_success_gap"] == 3
    assert payload["summary"]["stage7_replay_free_backfill_exhausted"] is True
    assert "stage4_state_local_topk_signal_present" in payload["pilot_findings"]
    assert "stage7_clean_success_controls_missing" in payload["blockers"]
    assert "stage7_replay_free_backfill_exhausted" in payload["blockers"]


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

    payload = _pilot.build_payload(
        benchmark=benchmark,
        inputs=inputs,
        backfill_audit=backfill,
    )

    assert payload["summary"]["stage7_success_gap"] == 0
    assert payload["decision"]["status"] == "sequence_policy_pilot_underpowered_needs_review"
    assert payload["decision"]["runtime_changes_allowed"] is False
