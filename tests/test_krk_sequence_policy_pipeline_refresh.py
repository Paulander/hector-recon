#!/usr/bin/env python3
"""Tests for passive KRK sequence-policy pipeline refresh."""

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


_refresh = _load_module(
    "refresh_krk_sequence_policy_pipeline_v0",
    "scripts/refresh_krk_sequence_policy_pipeline_v0.py",
)


def _read_report(path: str) -> dict:
    payload = json.loads((ROOT / path).read_text(encoding="utf-8"))
    assert isinstance(payload, dict)
    return payload


def test_sequence_policy_pipeline_refresh_preserves_boundaries():
    payload = _read_report(
        "reports/strategy_arbitration/krk_sequence_policy_pipeline_refresh_v0.json"
    )

    assert payload["schema_version"] == "krk_sequence_policy_pipeline_refresh.v0"
    assert payload["causal_status"] == "non_causal_passive_pipeline_refresh"
    assert payload["runtime_behavior_changed"] is False
    assert payload["runtime_selector_implemented"] is False
    assert payload["runtime_score_changes"] is False
    assert payload["runtime_direct_routing"] is False
    assert payload["runtime_dtm_or_tablebase_lookup"] is False
    assert payload["gameplay_topology_mutation"] is False
    assert payload["stage7_promotion_allowed"] is False
    assert payload["stage8_training_allowed"] is False
    assert payload["summary"]["all_boundaries_preserved"] is True
    assert payload["summary"]["stage7_success_controls"] == 11
    assert payload["summary"]["sequence_policy_inputs_ready"] is True
    assert (
        payload["summary"]["sequence_policy_benchmark_review_status"]
        == "sequence_policy_benchmark_mixed_plan_window_underpowered"
    )
    assert (
        payload["summary"]["sequence_policy_benchmark_design_status"]
        == "sequence_policy_benchmark_design_ready_non_causal"
    )
    assert (
        payload["summary"]["sequence_policy_passive_design_without_new_labels_status"]
        == "non_causal_sequence_policy_design_without_new_labels_ready"
    )
    assert (
        payload["summary"]["cross_stage_plan_capsule_requirements_status"]
        == "cross_stage_plan_capsule_evidence_ready_for_non_causal_benchmark"
    )
    assert (
        payload["summary"]["sequence_policy_benchmark_review_next_step"]
        == "obtain_matching_approval_receipt_before_protected_failure_contrast_collection"
    )
    assert (
        payload["decision"]["status"]
        == "sequence_policy_pipeline_refreshed_ready_for_non_causal_benchmark_review"
    )
    assert (
        payload["decision"]["recommended_next_step"]
        == "obtain_matching_approval_receipt_before_protected_failure_contrast_collection"
    )
    assert payload["decision"]["runtime_changes_allowed"] is False
    assert payload["decision"]["label_run_allowed"] is False
    assert payload["decision"]["selector_training_allowed"] is False
    assert payload["decision"]["stage7_promotion_allowed"] is False
    assert payload["decision"]["stage8_training_allowed"] is False
    for step in payload["step_results"]:
        assert step["runtime_changes_allowed"] is False
        assert step["label_run_allowed"] is False
        assert step["stage7_promotion_allowed"] is False
        assert step["stage8_training_allowed"] is False


def test_sequence_policy_pipeline_refresh_ready_status_logic():
    payload = {
        "schema_version": "krk_sequence_policy_pipeline_refresh.v0",
        "causal_status": "non_causal_passive_pipeline_refresh",
        "runtime_behavior_changed": False,
        "runtime_defaults_changed": False,
        "runtime_selector_implemented": False,
        "runtime_score_changes": False,
        "runtime_direct_routing": False,
        "runtime_dtm_or_tablebase_lookup": False,
        "gameplay_topology_mutation": False,
        "stage7_promotion_allowed": False,
        "stage8_training_allowed": False,
        "step_results": [],
        "summary": {
            "step_count": 5,
            "all_boundaries_preserved": True,
            "stage7_outputs_present_count": 1,
            "stage7_success_controls": 5,
            "stage7_success_controls_required": 5,
            "sequence_policy_inputs_ready": True,
            "sequence_policy_benchmark_status": "sequence_policy_benchmark_ready_non_causal_results_available",
            "sequence_policy_benchmark_review_status": "sequence_policy_benchmark_mixed_plan_window_underpowered",
            "sequence_policy_benchmark_review_next_step": "obtain_matching_approval_receipt_before_protected_failure_contrast_collection",
            "current_gate_status": "krk_control_plane_waiting_on_explicit_gate_choice",
        },
        "decision": {
            "status": "sequence_policy_pipeline_refreshed_ready_for_non_causal_benchmark_review",
            "recommended_next_step": "obtain_matching_approval_receipt_before_protected_failure_contrast_collection",
            "runtime_changes_allowed": False,
            "label_run_allowed": False,
            "selector_training_allowed": False,
            "stage7_promotion_allowed": False,
            "stage8_training_allowed": False,
        },
    }

    rendered = _refresh.write_markdown(payload)

    assert "sequence_policy_pipeline_refreshed_ready_for_non_causal_benchmark_review" in rendered
    assert "runtime_changes_allowed: `false`" in rendered


def test_sequence_policy_pipeline_refresh_reports_protected_plan_window_input_gap(
    monkeypatch,
):
    mapping = {
        "reports/structural_candidates/stage7_diverse_clean_sampling_integration_v0.json": {
            "summary": {"outputs_present_count": 8}
        },
        "reports/strategy_arbitration/krk_sequence_policy_benchmark_inputs_v0.json": {
            "summary": {
                "benchmark_input_ready": False,
                "stage7_clean_success_controls": 5,
                "stage7_clean_success_controls_required": 5,
                "stage7_clean_success_controls_met": True,
                "stage7_clean_failure_controls": 5,
                "stage7_clean_failure_controls_required": 5,
                "stage7_clean_failure_controls_met": True,
                "protected_plan_window_evidence_met": False,
            }
        },
        "reports/strategy_arbitration/krk_sequence_policy_benchmark_v0.json": {
            "decision": {
                "status": "sequence_policy_benchmark_blocked_pending_protected_plan_window_evidence"
            }
        },
        "reports/strategy_arbitration/krk_sequence_policy_benchmark_review_v0.json": {
            "decision": {"status": "sequence_policy_benchmark_review_blocked_pending_ready_inputs"}
        },
        "reports/strategy_arbitration/krk_sequence_policy_benchmark_design_v0.json": {
            "decision": {"status": "sequence_policy_benchmark_design_ready_non_causal"},
            "passive_design_without_new_labels": {"status": "fixture_passive"},
        },
        "reports/strategy_arbitration/krk_cross_stage_plan_capsule_evidence_requirements_v0.json": {
            "decision": {"status": "fixture_cross_stage"}
        },
        "reports/krk_current_control_plane_gate_v0.json": {
            "decision": {"status": "krk_control_plane_waiting_on_explicit_gate_choice"}
        },
    }

    monkeypatch.setattr(_refresh, "STEPS", [])
    monkeypatch.setattr(_refresh, "_load_json", lambda path: mapping[str(path)])

    payload = _refresh.run_refresh()

    assert (
        payload["decision"]["status"]
        == "sequence_policy_pipeline_refreshed_blocked_pending_protected_plan_window_inputs"
    )
    assert payload["decision"]["recommended_next_step"] == "repair_protected_plan_window_input_gap"
    assert payload["summary"]["stage7_success_controls"] == 5
    assert payload["summary"]["stage7_failure_controls"] == 5
    assert payload["summary"]["protected_plan_window_evidence_met"] is False
    assert payload["decision"]["label_run_allowed"] is False
    assert payload["decision"]["runtime_changes_allowed"] is False


def test_sequence_policy_pipeline_refresh_routes_forbidden_rows_to_repair(monkeypatch):
    mapping = {
        "reports/structural_candidates/stage7_diverse_clean_sampling_integration_v0.json": {
            "summary": {"outputs_present_count": 8}
        },
        "reports/strategy_arbitration/krk_sequence_policy_benchmark_inputs_v0.json": {
            "summary": {
                "benchmark_input_ready": True,
                "stage7_clean_success_controls": 5,
                "stage7_clean_success_controls_required": 5,
                "stage7_clean_success_controls_met": True,
                "stage7_clean_failure_controls": 5,
                "stage7_clean_failure_controls_required": 5,
                "stage7_clean_failure_controls_met": True,
                "protected_plan_window_evidence_met": True,
                "selector_training_row_count": 1,
                "runtime_authorization_row_count": 0,
            }
        },
        "reports/strategy_arbitration/krk_sequence_policy_benchmark_v0.json": {
            "preflight": {"blockers": ["selector_training_rows_forbidden"]},
            "decision": {
                "status": "sequence_policy_benchmark_blocked_forbidden_training_or_runtime_rows"
            },
        },
        "reports/strategy_arbitration/krk_sequence_policy_benchmark_review_v0.json": {
            "blockers": ["selector_training_rows_forbidden"],
            "decision": {
                "status": "sequence_policy_benchmark_review_blocked_forbidden_training_or_runtime_rows",
                "recommended_next_step": "repair_sequence_policy_inputs_remove_training_or_runtime_rows",
            },
        },
        "reports/strategy_arbitration/krk_sequence_policy_benchmark_design_v0.json": {
            "decision": {"status": "sequence_policy_benchmark_design_ready_non_causal"},
            "passive_design_without_new_labels": {"status": "fixture_passive"},
        },
        "reports/strategy_arbitration/krk_cross_stage_plan_capsule_evidence_requirements_v0.json": {
            "decision": {"status": "fixture_cross_stage"}
        },
        "reports/krk_current_control_plane_gate_v0.json": {
            "decision": {"status": "krk_control_plane_waiting_on_explicit_gate_choice"}
        },
    }

    monkeypatch.setattr(_refresh, "STEPS", [])
    monkeypatch.setattr(_refresh, "_load_json", lambda path: mapping[str(path)])

    payload = _refresh.run_refresh()

    assert (
        payload["decision"]["status"]
        == "sequence_policy_pipeline_refreshed_blocked_forbidden_training_or_runtime_rows"
    )
    assert (
        payload["decision"]["recommended_next_step"]
        == "repair_sequence_policy_inputs_remove_training_or_runtime_rows"
    )
    assert payload["summary"]["forbidden_training_or_runtime_input_blocked"] is True
    assert "selector_training_rows_forbidden" in payload["summary"][
        "forbidden_training_or_runtime_input_blockers"
    ]
    assert payload["decision"]["selector_training_allowed"] is False
