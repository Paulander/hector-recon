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
    assert payload["summary"]["stage7_success_controls"] == 2
    assert payload["summary"]["sequence_policy_inputs_ready"] is False
    assert (
        payload["decision"]["status"]
        == "sequence_policy_pipeline_refreshed_still_blocked_by_stage7_success_controls"
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
            "current_gate_status": "krk_control_plane_waiting_on_explicit_gate_choice",
        },
        "decision": {
            "status": "sequence_policy_pipeline_refreshed_ready_for_non_causal_benchmark_review",
            "recommended_next_step": "review_non_causal_sequence_policy_benchmark",
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
