#!/usr/bin/env python3
"""Tests for the KRK sequence-policy benchmark review gate."""

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
    "review_krk_sequence_policy_benchmark_v0",
    "scripts/review_krk_sequence_policy_benchmark_v0.py",
)


def _read_report() -> dict:
    payload = json.loads(
        (
            ROOT
            / "reports/strategy_arbitration/krk_sequence_policy_benchmark_review_v0.json"
        ).read_text()
    )
    assert isinstance(payload, dict)
    return payload


def test_sequence_policy_benchmark_review_reports_current_mixed_result():
    payload = _read_report()

    assert payload["schema_version"] == "krk_sequence_policy_benchmark_review.v0"
    assert payload["causal_status"] == "non_causal_benchmark_review"
    assert payload["runtime_behavior_changed"] is False
    assert payload["runtime_selector_implemented"] is False
    assert payload["runtime_score_changes"] is False
    assert payload["runtime_direct_routing"] is False
    assert payload["runtime_dtm_or_tablebase_lookup"] is False
    assert payload["gameplay_topology_mutation"] is False
    assert payload["stage7_promotion_allowed"] is False
    assert payload["stage8_training_allowed"] is False
    assert (
        payload["decision"]["status"]
        == "sequence_policy_benchmark_mixed_plan_window_underpowered"
    )
    assert payload["decision"]["runtime_changes_allowed"] is False
    assert payload["decision"]["label_run_allowed"] is False
    assert payload["decision"]["selector_training_allowed"] is False
    assert payload["decision"]["stage7_promotion_allowed"] is False
    assert payload["decision"]["stage8_training_allowed"] is False
    assert "protected_plan_window_failure_evidence_sparse" in payload["blockers"]
    assert (
        payload["decision"]["recommended_next_step"]
        == "explicitly_approve_protected_plan_window_failure_contrast_collection"
    )
    assert "stage4_topk_sequence_signal_present" in payload["findings"]
    assert "stage4_binary_rule_insufficient" in payload["findings"]
    assert "stage7_heldout_controls_balanced" in payload["findings"]


def test_sequence_policy_benchmark_review_ready_fixture_supports_review_packet():
    benchmark = {
        "preflight": {
            "benchmark_input_ready": True,
            "blockers": [],
            "row_count": 40,
            "selector_training_row_count": 0,
            "runtime_authorization_row_count": 0,
            "stage7_heldout_row_count": 10,
        },
        "decision": {
            "benchmark_executed_as_ready": True,
            "runtime_changes_allowed": False,
            "label_run_allowed": False,
            "selector_training_allowed": False,
            "stage7_promotion_allowed": False,
            "stage8_training_allowed": False,
        },
        "objectives": [
            {
                "objective_id": "stage4_state_local_first_move_contrast",
                "row_count": 20,
                "state_count": 4,
                "metrics": {
                    "top1_conversion_positive_by_state": 0.75,
                    "top3_conversion_positive_by_state": 1.0,
                    "recall": 0.5,
                    "negative_suppression": 0.9,
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

    payload = _review.build_payload(benchmark=benchmark)

    assert (
        payload["decision"]["status"]
        == "sequence_policy_benchmark_supports_non_causal_sequence_policy_review"
    )
    assert (
        payload["decision"]["recommended_next_step"]
        == "write_sequence_policy_runtime_or_training_review_packet"
    )
    assert payload["decision"]["runtime_changes_allowed"] is False
    assert payload["decision"]["selector_training_allowed"] is False
    assert payload["decision"]["stage8_training_allowed"] is False
    assert payload["blockers"] == []


def test_sequence_policy_benchmark_review_ready_fixture_can_still_be_underpowered():
    benchmark = {
        "preflight": {
            "benchmark_input_ready": True,
            "blockers": [],
            "row_count": 35,
            "selector_training_row_count": 0,
            "runtime_authorization_row_count": 0,
            "stage7_heldout_row_count": 10,
        },
        "decision": {"benchmark_executed_as_ready": True},
        "objectives": [
            {
                "objective_id": "stage4_state_local_first_move_contrast",
                "row_count": 20,
                "state_count": 4,
                "metrics": {
                    "top1_conversion_positive_by_state": 0.75,
                    "top3_conversion_positive_by_state": 1.0,
                    "recall": 0.5,
                    "negative_suppression": 0.9,
                },
            },
            {
                "objective_id": "protected_plan_window_entry_progress_exit_abort",
                "row_count": 5,
                "target_label_counts": {"conversion_positive": 4, "conversion_failure": 1},
                "failure_evidence_sparse": True,
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

    payload = _review.build_payload(benchmark=benchmark)

    assert payload["decision"]["status"] == "sequence_policy_benchmark_mixed_plan_window_underpowered"
    assert (
        payload["decision"]["recommended_next_step"]
        == "explicitly_approve_protected_plan_window_failure_contrast_collection"
    )
    assert "protected_plan_window_failure_evidence_sparse" in payload["blockers"]
    assert payload["decision"]["runtime_changes_allowed"] is False


def test_sequence_policy_benchmark_review_not_ready_routes_by_preflight_blocker():
    payload = _review.build_payload(
        benchmark={
            "preflight": {
                "benchmark_input_ready": False,
                "blockers": ["protected_plan_window_evidence_missing"],
                "row_count": 10,
                "selector_training_row_count": 0,
                "runtime_authorization_row_count": 0,
                "stage7_heldout_row_count": 10,
            },
            "decision": {"benchmark_executed_as_ready": False},
            "objectives": [],
        }
    )

    assert (
        payload["decision"]["status"]
        == "sequence_policy_benchmark_review_blocked_pending_ready_inputs"
    )
    assert payload["blockers"] == ["protected_plan_window_evidence_missing"]
    assert payload["decision"]["recommended_next_step"] == "repair_protected_plan_window_input_gap"
    assert payload["decision"]["runtime_changes_allowed"] is False
    assert payload["decision"]["label_run_allowed"] is False


def test_sequence_policy_benchmark_review_blocks_forbidden_training_or_runtime_rows():
    payload = _review.build_payload(
        benchmark={
            "preflight": {
                "benchmark_input_ready": True,
                "blockers": ["selector_training_rows_forbidden"],
                "row_count": 10,
                "selector_training_row_count": 1,
                "runtime_authorization_row_count": 0,
                "stage7_heldout_row_count": 0,
            },
            "decision": {
                "benchmark_executed_as_ready": False,
                "runtime_changes_allowed": False,
                "label_run_allowed": False,
                "selector_training_allowed": False,
                "stage7_promotion_allowed": False,
                "stage8_training_allowed": False,
            },
            "objectives": [],
        }
    )

    assert (
        payload["decision"]["status"]
        == "sequence_policy_benchmark_review_blocked_forbidden_training_or_runtime_rows"
    )
    assert payload["decision"]["recommended_next_step"] == (
        "repair_sequence_policy_inputs_remove_training_or_runtime_rows"
    )
    assert payload["blockers"] == ["selector_training_rows_forbidden"]
    assert payload["benchmark_preflight"]["selector_training_row_count"] == 1
    assert payload["decision"]["selector_training_allowed"] is False
    assert payload["decision"]["runtime_changes_allowed"] is False
    assert payload["decision"]["stage8_training_allowed"] is False
