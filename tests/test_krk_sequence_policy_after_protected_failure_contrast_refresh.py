#!/usr/bin/env python3
"""Tests for post protected-failure sequence-policy refresh."""

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
    "refresh_krk_sequence_policy_after_protected_failure_contrasts_v0",
    "scripts/refresh_krk_sequence_policy_after_protected_failure_contrasts_v0.py",
)


def _read_report() -> dict:
    payload = json.loads(
        (
            ROOT
            / "reports/strategy_arbitration/"
            "krk_sequence_policy_after_protected_failure_contrast_refresh_v0.json"
        ).read_text(encoding="utf-8")
    )
    assert isinstance(payload, dict)
    return payload


def test_after_protected_failure_contrast_refresh_waits_on_outputs():
    payload = _read_report()

    assert (
        payload["schema_version"]
        == "krk_sequence_policy_after_protected_failure_contrast_refresh.v0"
    )
    assert payload["causal_status"] == "non_causal_post_failure_contrast_sequence_policy_refresh"
    assert payload["runtime_behavior_changed"] is False
    assert payload["runtime_selector_implemented"] is False
    assert payload["runtime_score_changes"] is False
    assert payload["runtime_direct_routing"] is False
    assert payload["runtime_dtm_or_tablebase_lookup"] is False
    assert payload["hidden_python_controller"] is False
    assert payload["gameplay_topology_mutation"] is False
    assert payload["stage7_promotion_allowed"] is False
    assert payload["stage8_training_allowed"] is False
    assert payload["summary"]["all_boundaries_preserved"] is True
    assert payload["summary"]["boundary_violation_count"] == 0
    assert payload["summary"]["boundary_violations"] == []
    assert (
        payload["summary"]["integration_status"]
        == "protected_plan_window_failure_contrast_integration_underpowered_needs_more_valid_failures"
    )
    assert payload["summary"]["integration_ready"] is False
    assert payload["summary"]["integrated_new_failure_count"] == 0
    assert payload["summary"]["protected_failure_contrast_row_count"] == 0
    assert (
        "approve_protected_plan_window_failure_contrast_collection"
        not in payload["summary"]["current_control_plane_approval_option_ids"]
    )
    assert (
        payload["summary"]["protected_failure_contrast_collection_option_available"]
        is False
    )
    assert (
        payload["summary"]["protected_failure_contrast_collection_command_available"]
        is False
    )
    assert (
        payload["summary"]["protected_failure_contrast_collection_option_id"]
        is None
    )
    assert (
        payload["summary"]["protected_failure_contrast_collection_blocked_by_option_id"]
        == "review_protected_plan_window_failure_contrast_manifest"
    )
    assert (
        payload["decision"]["status"]
        == "sequence_policy_after_protected_failure_contrast_refresh_blocked_pending_"
        "protected_failure_contrast_control_plane_gate_review"
    )
    assert (
        payload["decision"]["recommended_next_step"]
        == "review_current_control_plane_gate_for_protected_failure_contrast_collection"
    )
    assert payload["decision"]["runtime_changes_allowed"] is False
    assert payload["decision"]["label_run_allowed"] is False
    assert payload["decision"]["selector_training_allowed"] is False
    assert payload["decision"]["stage7_promotion_allowed"] is False
    assert payload["decision"]["stage8_training_allowed"] is False
    for step in payload["step_results"]:
        assert step["runtime_changes_allowed"] is False
        assert step["label_run_allowed"] is False
        assert step["selector_training_allowed"] is False
        assert step["stage7_promotion_allowed"] is False
        assert step["stage8_training_allowed"] is False


def test_after_protected_failure_contrast_refresh_markdown_boundary_summary():
    payload = _read_report()
    rendered = _refresh.write_markdown(payload)

    assert "runtime_changes_allowed: `false`" in rendered
    assert "label_run_allowed: `false`" in rendered
    assert "Stage 7 promotion and Stage 8 training remain blocked." in rendered


def test_after_protected_failure_contrast_refresh_blocks_boundary_violation(monkeypatch):
    class FakeModule:
        @staticmethod
        def main():
            return None

    outputs = {
        "reports/strategy_arbitration/krk_sequence_policy_benchmark_inputs_v0.json": {
            "summary": {
                "protected_failure_contrast_row_count": 4,
                "row_count": 122,
                "selector_training_row_count": 0,
                "runtime_authorization_row_count": 0,
            },
            "decision": {
                "status": "sequence_policy_benchmark_inputs_ready_non_causal",
                "runtime_changes_allowed": False,
                "label_run_allowed": False,
                "selector_training_allowed": False,
                "stage7_promotion_allowed": False,
                "stage8_training_allowed": False,
            },
        },
        "reports/strategy_arbitration/krk_sequence_policy_input_probe_v0.json": {
            "decision": {
                "status": "sequence_policy_input_probe_ready_for_full_non_causal_benchmark",
                "runtime_changes_allowed": False,
                "label_run_allowed": False,
                "selector_training_allowed": False,
                "stage7_promotion_allowed": False,
                "stage8_training_allowed": False,
            }
        },
        "reports/strategy_arbitration/krk_sequence_policy_benchmark_v0.json": {
            "decision": {
                "status": "sequence_policy_benchmark_ready_non_causal_results_available",
                "runtime_changes_allowed": True,
                "label_run_allowed": False,
                "selector_training_allowed": False,
                "stage7_promotion_allowed": False,
                "stage8_training_allowed": False,
            }
        },
        "reports/strategy_arbitration/krk_sequence_policy_benchmark_review_v0.json": {
            "decision": {
                "status": "sequence_policy_benchmark_mixed_plan_window_underpowered",
                "runtime_changes_allowed": False,
                "label_run_allowed": False,
                "selector_training_allowed": False,
                "stage7_promotion_allowed": False,
                "stage8_training_allowed": False,
            }
        },
    }

    monkeypatch.setattr(_refresh, "_load_module", lambda _path: FakeModule)
    def fake_load(path):
        if path == _refresh.CONTROL_PLANE_GATE:
            return {
                "decision": {"status": "krk_control_plane_waiting_on_explicit_gate_choice"},
                "approval_options": [
                    {
                        "option_id": (
                            "approve_protected_plan_window_failure_contrast_collection"
                        ),
                        "command_if_explicitly_approved": (
                            "uv run python scripts/run_krk_protected_plan_window_"
                            "failure_contrast_collection_v0.py --execute-reviewed-collection"
                        ),
                    }
                ],
            }
        return {
            "decision": {
                "status": (
                    "protected_plan_window_failure_contrast_integration_ready_for_passive_benchmark_refresh"
                )
            },
            "summary": {"integration_ready": True, "integrated_new_failure_count": 4},
        }

    monkeypatch.setattr(_refresh, "_load", fake_load)
    monkeypatch.setattr(_refresh, "_load_relative", lambda path: outputs[path])

    payload = _refresh.build_payload()

    assert (
        payload["decision"]["status"]
        == "sequence_policy_after_protected_failure_contrast_refresh_blocked_boundary_violation"
    )
    assert payload["decision"]["recommended_next_step"] == (
        "inspect_post_protected_failure_contrast_refresh_boundary_violation"
    )
    assert payload["summary"]["all_boundaries_preserved"] is False
    assert payload["summary"]["boundary_violation_count"] == 1
    assert payload["summary"]["boundary_violations"] == [
        {
            "step_id": "sequence_policy_benchmark",
            "field": "runtime_changes_allowed",
            "script": "scripts/run_krk_sequence_policy_benchmark_v0.py",
        }
    ]
    assert payload["decision"]["runtime_changes_allowed"] is False
    assert payload["decision"]["stage8_training_allowed"] is False


def test_after_protected_failure_contrast_refresh_routes_missing_collection_option_to_gate_review(
    monkeypatch,
):
    class FakeModule:
        @staticmethod
        def main():
            return None

    outputs = {
        "reports/strategy_arbitration/krk_sequence_policy_benchmark_inputs_v0.json": {
            "summary": {
                "protected_failure_contrast_row_count": 0,
                "row_count": 118,
                "selector_training_row_count": 0,
                "runtime_authorization_row_count": 0,
            },
            "decision": {
                "status": "sequence_policy_benchmark_inputs_ready_non_causal",
                "runtime_changes_allowed": False,
                "label_run_allowed": False,
                "selector_training_allowed": False,
                "stage7_promotion_allowed": False,
                "stage8_training_allowed": False,
            },
        },
        "reports/strategy_arbitration/krk_sequence_policy_input_probe_v0.json": {
            "decision": {
                "status": "sequence_policy_input_probe_ready_for_full_non_causal_benchmark",
                "runtime_changes_allowed": False,
                "label_run_allowed": False,
                "selector_training_allowed": False,
                "stage7_promotion_allowed": False,
                "stage8_training_allowed": False,
            }
        },
        "reports/strategy_arbitration/krk_sequence_policy_benchmark_v0.json": {
            "decision": {
                "status": "sequence_policy_benchmark_ready_non_causal_results_available",
                "runtime_changes_allowed": False,
                "label_run_allowed": False,
                "selector_training_allowed": False,
                "stage7_promotion_allowed": False,
                "stage8_training_allowed": False,
            }
        },
        "reports/strategy_arbitration/krk_sequence_policy_benchmark_review_v0.json": {
            "decision": {
                "status": "sequence_policy_benchmark_mixed_plan_window_underpowered",
                "runtime_changes_allowed": False,
                "label_run_allowed": False,
                "selector_training_allowed": False,
                "stage7_promotion_allowed": False,
                "stage8_training_allowed": False,
            }
        },
    }

    def fake_load(path):
        if path == _refresh.CONTROL_PLANE_GATE:
            return {
                "decision": {"status": "krk_control_plane_waiting_on_explicit_gate_choice"},
                "approval_options": [
                    {
                        "option_id": (
                            "review_protected_plan_window_failure_contrast_execution_readiness"
                        ),
                        "command_if_explicitly_approved": None,
                    }
                ],
            }
        return {
            "decision": {
                "status": "protected_plan_window_failure_contrast_integration_pending_outputs"
            },
            "summary": {"integration_ready": False, "integrated_new_failure_count": 0},
        }

    monkeypatch.setattr(_refresh, "_load_module", lambda _path: FakeModule)
    monkeypatch.setattr(_refresh, "_load", fake_load)
    monkeypatch.setattr(_refresh, "_load_relative", lambda path: outputs[path])

    payload = _refresh.build_payload()

    assert (
        payload["decision"]["status"]
        == "sequence_policy_after_protected_failure_contrast_refresh_blocked_pending_"
        "protected_failure_contrast_control_plane_gate_review"
    )
    assert (
        payload["decision"]["recommended_next_step"]
        == "review_current_control_plane_gate_for_protected_failure_contrast_collection"
    )
    assert (
        payload["summary"]["protected_failure_contrast_collection_option_available"]
        is False
    )
    assert (
        payload["summary"]["protected_failure_contrast_collection_command_available"]
        is False
    )
    assert (
        payload["summary"][
            "protected_failure_contrast_collection_blocked_by_option_id"
        ]
        == "review_protected_plan_window_failure_contrast_execution_readiness"
    )
    assert payload["decision"]["runtime_changes_allowed"] is False
    assert payload["decision"]["label_run_allowed"] is False
    assert payload["decision"]["stage8_training_allowed"] is False
