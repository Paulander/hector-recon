#!/usr/bin/env python3
"""Tests for protected plan-window failure-contrast collection result packet."""

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


_result = _load_module(
    "summarize_krk_protected_plan_window_failure_contrast_collection_result_v0",
    "scripts/summarize_krk_protected_plan_window_failure_contrast_collection_result_v0.py",
)


def _read(relative: str) -> dict:
    payload = json.loads((ROOT / relative).read_text(encoding="utf-8"))
    assert isinstance(payload, dict)
    return payload


def test_collection_result_records_underpowered_collection_and_zero_deltas():
    payload = _read(
        "reports/strategy_arbitration/"
        "krk_protected_plan_window_failure_contrast_collection_result_v0.json"
    )

    assert (
        payload["schema_version"]
        == "krk_protected_plan_window_failure_contrast_collection_result.v0"
    )
    assert payload["causal_status"] == (
        "non_causal_protected_plan_window_collection_result"
    )
    assert payload["decision"]["status"] == "collection_complete_underpowered"
    assert payload["decision"]["collection_run_allowed"] is False
    assert payload["decision"]["runtime_changes_allowed"] is False
    assert payload["decision"]["selector_training_allowed"] is False
    assert payload["decision"]["stage7_promotion_allowed"] is False
    assert payload["decision"]["stage8_training_allowed"] is False
    assert payload["runtime_behavior_changed"] is False
    assert payload["runtime_defaults_changed"] is False
    assert payload["runtime_selector_implemented"] is False
    assert payload["runtime_score_changes"] is False
    assert payload["runtime_direct_routing"] is False
    assert payload["runtime_dtm_or_tablebase_lookup"] is False
    assert payload["hidden_python_controller"] is False
    assert payload["gameplay_topology_mutation"] is False

    summary = payload["summary"]
    assert summary["manifest_job_count"] == 6
    assert summary["collection_output_count"] == 6
    assert summary["output_valid_count"] == 6
    assert summary["h40_outcome_label_counts"] == {"conversion_positive": 6}
    assert summary["conversion_failure_count"] == 0
    assert summary["integrated_new_failure_count"] == 0
    assert summary["integration_ready"] is False
    assert summary["sequence_policy_replay_free_recovery_row_count"] == 0
    assert summary["selected_move_delta_count"] == 0
    assert summary["selected_provider_delta_count"] == 0
    assert summary["score_delta_count"] == 0
    assert summary["routing_delta_count"] == 0
    assert summary["runtime_behavior_unchanged"] is True
    assert summary["selector_training_row_count"] == 0
    assert summary["stage7_training_row_count"] == 0
    assert summary["runtime_authorization_row_count"] == 0
    assert summary["runtime_dtm_or_tablebase_lookup"] is False
    assert summary["gameplay_topology_mutation"] is False
    assert summary["output_load_issue_counts"] == {}
    assert summary["output_forbidden_issue_counts"] == {}
    assert summary["next_step_requires_new_explicit_approval"] is True


def test_followup_review_packet_blocks_additional_collection_without_new_approval():
    payload = _read(
        "reports/strategy_arbitration/"
        "krk_protected_plan_window_failure_contrast_followup_review_packet_v0.json"
    )

    assert (
        payload["schema_version"]
        == "krk_protected_plan_window_failure_contrast_followup_review_packet.v0"
    )
    assert payload["causal_status"] == "non_causal_future_collection_review_packet_only"
    assert payload["decision"]["status"] == "blocked_needs_human_approval"
    assert payload["decision"]["collection_run_allowed"] is False
    assert payload["decision"]["runtime_changes_allowed"] is False
    assert payload["decision"]["selector_training_allowed"] is False
    assert payload["decision"]["stage7_promotion_allowed"] is False
    assert payload["decision"]["stage8_training_allowed"] is False

    summary = payload["summary"]
    assert summary["prior_collection_status"] == "collection_complete_underpowered"
    assert summary["prior_collection_output_count"] == 6
    assert summary["prior_collection_conversion_failure_count"] == 0
    assert summary["integrated_new_failure_count"] == 0
    assert summary["review_packet_only"] is True
    assert summary["execute_now"] is False
    assert summary["new_collection_approved_by_this_packet"] is False
    assert summary["requires_fresh_manifest_or_scope_review"] is True
    assert summary["requires_new_explicit_approval"] is True
    assert "runtime_selector" in summary["forbidden_next_steps"]
    assert "new_collection_without_fresh_explicit_approval" in summary[
        "forbidden_next_steps"
    ]
    assert summary["selector_training_row_count"] == 0
    assert summary["stage7_training_row_count"] == 0
    assert summary["runtime_authorization_row_count"] == 0


def test_collection_result_fixture_routes_invalid_forbidden_output_to_architecture_review():
    manifest = {
        "jobs": [
            {
                "job_id": "protected_plan_failure.fixture",
                "expected_output_json": (
                    "reports/strategy_arbitration/protected_plan_window_failure_contrasts/"
                    "missing.fixture.json"
                ),
            }
        ]
    }
    payload = _result.build_collection_result_payload(
        manifest=manifest,
        approval_receipt={
            "approval_id": "approve_protected_plan_window_failure_contrast_collection",
            "decision": {
                "status": "approved_for_single_bounded_observation_collection",
                "single_execution_only": True,
            },
        },
        output_validation={
            "decision": {
                "status": "protected_plan_window_failure_contrast_outputs_valid_ready_for_integration"
            },
            "summary": {
                "output_valid_count": 1,
                "selector_training_row_count": 0,
                "stage7_training_row_count": 0,
                "runtime_authorization_row_count": 0,
            },
        },
        integration={
            "summary": {
                "integration_ready": False,
                "integrated_new_failure_count": 0,
                "validated_unique_failure_candidate_count": 0,
                "existing_unique_failure_count": 1,
                "minimum_required_unique_failures": 5,
                "minimum_new_unique_failures_needed": 4,
            }
        },
        post_refresh={
            "summary": {
                "protected_failure_contrast_row_count": 0,
                "all_boundaries_preserved": True,
                "boundary_violation_count": 0,
            }
        },
        benchmark_review={
            "objective_review": {
                "protected_plan_window": {
                    "row_count": 20,
                    "target_label_counts": {
                        "conversion_failure": 1,
                        "conversion_positive": 19,
                    },
                }
            }
        },
    )

    assert payload["decision"]["status"] == "architecture_review_required"
    assert payload["summary"]["output_load_issue_counts"] == {"output_missing": 1}
    assert payload["decision"]["runtime_changes_allowed"] is False
    assert payload["decision"]["selector_training_allowed"] is False
