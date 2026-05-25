#!/usr/bin/env python3
"""Tests for KRK Stage 7 post-label outcome review."""

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
    "review_krk_stage7_post_label_outcome_v0",
    "scripts/review_krk_stage7_post_label_outcome_v0.py",
)


def _read_report() -> dict:
    payload = json.loads((ROOT / "reports/krk_stage7_post_label_outcome_review_v0.json").read_text())
    assert isinstance(payload, dict)
    return payload


def test_stage7_post_label_outcome_current_artifact_waits_for_outputs():
    payload = _read_report()

    assert payload["schema_version"] == "krk_stage7_post_label_outcome_review.v0"
    assert payload["causal_status"] == "non_causal_post_label_outcome_review"
    assert payload["runtime_behavior_changed"] is False
    assert payload["runtime_selector_implemented"] is False
    assert payload["runtime_dtm_or_tablebase_lookup"] is False
    assert payload["gameplay_topology_mutation"] is False
    assert payload["stage7_promotion_allowed"] is False
    assert payload["stage8_training_allowed"] is False
    assert payload["summary"]["outputs_present_count"] == 0
    assert payload["summary"]["success_controls"] == 2
    assert payload["summary"]["success_controls_met"] is False
    assert payload["summary"]["stage7_training_row_count"] == 0
    assert payload["summary"]["selector_training_row_count"] == 0
    assert payload["summary"]["runtime_authorization_row_count"] == 0
    assert payload["decision"]["status"] == "post_label_outcome_pending_explicit_label_outputs"
    assert payload["decision"]["label_run_allowed"] is False
    assert payload["decision"]["runtime_changes_allowed"] is False
    assert payload["decision"]["stage7_promotion_allowed"] is False
    assert payload["decision"]["stage8_training_allowed"] is False


def test_stage7_post_label_outcome_blocks_invalid_outputs():
    payload = _review.build_payload(
        output_validation={
            "summary": {"output_exists_count": 1, "output_valid_count": 0},
            "decision": {
                "status": "stage7_diverse_clean_sampling_outputs_invalid_block_integration"
            },
        },
        integration={
            "summary": {
                "combined_success_controls": 2,
                "success_controls_required": 5,
                "success_controls_met": False,
                "combined_failure_controls": 8,
                "failure_controls_required": 5,
                "failure_controls_met": True,
            },
            "decision": {"status": "stage7_diverse_clean_sampling_integration_blocked_invalid_outputs"},
        },
        pipeline={"summary": {"sequence_policy_inputs_ready": False}, "decision": {"status": "blocked"}},
        benchmark_review={"decision": {"status": "sequence_policy_benchmark_review_blocked_pending_ready_inputs"}},
        readiness={"stage7_sampling_gate": {"invalid_existing_output_count": 1}, "decision": {"status": "blocked"}},
        stage8_review={"decision": {"status": "stage8_training_blocked_pending_stage7_sequence_gate"}},
    )

    assert payload["decision"]["status"] == "post_label_outcome_invalid_outputs_block_integration"
    assert "stage7_diverse_clean_outputs_invalid" in payload["blockers"]
    assert payload["summary"]["invalid_output_count"] == 1
    assert payload["decision"]["runtime_changes_allowed"] is False
    assert payload["decision"]["stage8_training_allowed"] is False


def test_stage7_post_label_outcome_detects_sequence_policy_review_ready():
    payload = _review.build_payload(
        output_validation={
            "summary": {"output_exists_count": 8, "output_valid_count": 8},
            "decision": {
                "status": "stage7_diverse_clean_sampling_outputs_valid_ready_for_integration"
            },
        },
        integration={
            "summary": {
                "combined_success_controls": 5,
                "success_controls_required": 5,
                "success_controls_met": True,
                "combined_failure_controls": 8,
                "failure_controls_required": 5,
                "failure_controls_met": True,
            },
            "decision": {
                "status": "stage7_diverse_clean_sampling_integration_success_controls_met"
            },
        },
        pipeline={
            "summary": {"sequence_policy_inputs_ready": True},
            "decision": {
                "status": "sequence_policy_pipeline_refreshed_ready_for_non_causal_benchmark_review"
            },
        },
        benchmark_review={
            "decision": {
                "status": "sequence_policy_benchmark_supports_non_causal_sequence_policy_review"
            }
        },
        readiness={
            "stage7_sampling_gate": {"invalid_existing_output_count": 0},
            "decision": {"status": "krk_suite_readiness_ready_for_next_runtime_or_training_review"},
        },
        stage8_review={
            "decision": {
                "status": "stage8_training_blocked_pending_stage7_sequence_gate"
            }
        },
    )

    assert (
        payload["decision"]["status"]
        == "post_label_outcome_sequence_policy_review_ready_stage8_blocked"
    )
    assert "sequence_policy_benchmark_supportive" in payload["findings"]
    assert payload["decision"]["stage8_training_allowed"] is False
