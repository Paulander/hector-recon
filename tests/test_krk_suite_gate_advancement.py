#!/usr/bin/env python3
"""Tests for passive KRK suite gate advancement."""

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


_advance = _load_module(
    "advance_krk_suite_from_current_gates_v0",
    "scripts/advance_krk_suite_from_current_gates_v0.py",
)


def _read_report() -> dict:
    payload = json.loads((ROOT / "reports/krk_suite_gate_advancement_v0.json").read_text())
    assert isinstance(payload, dict)
    return payload


def test_gate_advancement_artifact_is_passive_and_boundary_clean():
    payload = _read_report()

    assert payload["schema_version"] == "krk_suite_gate_advancement.v0"
    assert payload["causal_status"] == "non_causal_passive_gate_advancement"
    assert payload["runtime_behavior_changed"] is False
    assert payload["runtime_defaults_changed"] is False
    assert payload["runtime_selector_implemented"] is False
    assert payload["runtime_score_changes"] is False
    assert payload["runtime_direct_routing"] is False
    assert payload["runtime_dtm_or_tablebase_lookup"] is False
    assert payload["gameplay_topology_mutation"] is False
    assert payload["stage7_promotion_allowed"] is False
    assert payload["stage8_training_allowed"] is False
    assert payload["summary"]["all_boundaries_preserved"] is True

    decision = payload["decision"]
    assert decision["runtime_changes_allowed"] is False
    assert decision["label_run_allowed"] is False
    assert decision["selector_allowed"] is False
    assert decision["selector_training_allowed"] is False
    assert decision["stage7_promotion_allowed"] is False
    assert decision["stage8_training_allowed"] is False


def test_gate_advancement_reports_current_stage7_blocker():
    payload = _read_report()

    assert (
        payload["decision"]["status"]
        == "krk_suite_passive_advancement_blocked_pending_stage7_label_outputs"
    )
    assert (
        payload["decision"]["recommended_next_step"]
        == "explicitly_approve_stage7_diverse_clean_label_execution"
    )
    assert payload["summary"]["stage7_success_controls"] == 2
    assert payload["summary"]["stage7_success_controls_required"] == 5
    assert payload["summary"]["stage7_success_controls_ready"] is False
    assert (
        payload["summary"]["stage7_clean_success_backfill_status"]
        == "stage7_clean_success_backfill_exhausted_pending_label_execution"
    )
    assert payload["summary"]["stage7_clean_success_backfill_available"] is False
    assert payload["summary"]["stage7_clean_success_backfill_eligible_new_success"] == 0
    assert payload["summary"]["sequence_policy_inputs_ready"] is False
    assert payload["summary"]["sequence_policy_benchmark_ready"] is False


def test_gate_advancement_writer_includes_all_passive_steps():
    payload = _advance.build_payload()
    rendered = _advance.write_markdown(payload)

    step_ids = {step["step_id"] for step in payload["step_results"]}
    assert step_ids == {
        "stage7_diverse_clean_output_validation",
        "stage4_caveat_unblocker_packet",
        "stage7_clean_success_backfill_audit",
        "sequence_policy_pipeline_refresh",
        "sequence_policy_benchmark_review",
        "sequence_policy_underpowered_pilot_review",
        "full_suite_readiness_audit",
        "full_suite_unblocker_packet",
        "stage8_training_readiness_review",
        "stage7_post_label_outcome_review",
    }
    assert "krk_suite_passive_advancement_blocked_pending_stage7_label_outputs" in rendered
    assert (
        payload["summary"]["sequence_policy_benchmark_review_status"]
        == "sequence_policy_benchmark_review_blocked_pending_ready_inputs"
    )
    assert (
        payload["summary"]["sequence_policy_underpowered_pilot_status"]
        == "sequence_policy_pilot_ready_for_full_benchmark_after_label_gate"
    )
    assert payload["summary"]["sequence_policy_underpowered_pilot_stage4_topk_signal"] is True
    assert payload["summary"]["sequence_policy_underpowered_pilot_stage7_success_gap"] == 3
    assert (
        payload["summary"]["stage7_output_validation_status"]
        == "stage7_diverse_clean_sampling_outputs_validation_pending"
    )
    assert payload["summary"]["stage7_output_valid_count"] == 0
    assert (
        payload["summary"]["stage8_training_readiness_status"]
        == "stage8_training_blocked_pending_stage7_sequence_gate"
    )
    assert (
        payload["summary"]["stage7_post_label_outcome_status"]
        == "post_label_outcome_pending_explicit_label_outputs"
    )
    assert (
        payload["summary"]["stage7_post_label_outcome_next_step"]
        == "explicitly_approve_stage7_diverse_clean_label_execution"
    )
    assert (
        payload["summary"]["stage4_caveat_unblocker_status"]
        == "stage4_caveat_unblocker_ready_pending_explicit_runtime_approval"
    )
    for step in payload["step_results"]:
        assert step["label_run_allowed"] is False
        assert step["runtime_changes_allowed"] is False
        assert step["stage7_promotion_allowed"] is False
        assert step["stage8_training_allowed"] is False
