#!/usr/bin/env python3
"""Tests for passive KRK Stage 8 training-readiness review."""

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
    "review_krk_stage8_training_readiness_v0",
    "scripts/review_krk_stage8_training_readiness_v0.py",
)


def _read_report() -> dict:
    payload = json.loads((ROOT / "reports/krk_stage8_training_readiness_review_v0.json").read_text())
    assert isinstance(payload, dict)
    return payload


def test_stage8_training_readiness_review_blocks_current_state():
    payload = _read_report()

    assert payload["schema_version"] == "krk_stage8_training_readiness_review.v0"
    assert payload["causal_status"] == "non_causal_stage8_training_readiness_review"
    assert payload["runtime_behavior_changed"] is False
    assert payload["runtime_selector_implemented"] is False
    assert payload["runtime_score_changes"] is False
    assert payload["runtime_direct_routing"] is False
    assert payload["runtime_dtm_or_tablebase_lookup"] is False
    assert payload["gameplay_topology_mutation"] is False
    assert payload["stage7_promotion_allowed"] is False
    assert payload["stage8_training_allowed"] is False
    assert payload["requirements"]["protected_stage5_6_stack_ready"] is True
    assert payload["requirements"]["stage7_clean_success_controls_ready"] is False
    assert payload["requirements"]["sequence_policy_benchmark_review_ready"] is False
    assert "stage7_clean_success_controls_missing" in payload["blockers"]
    assert "sequence_policy_benchmark_review_not_ready" in payload["blockers"]
    assert (
        payload["decision"]["status"]
        == "stage8_training_blocked_pending_stage7_sequence_gate"
    )
    assert payload["decision"]["implementation_allowed_by_this_review"] is False
    assert payload["decision"]["stage8_training_allowed"] is False


def test_stage8_training_readiness_review_fixture_can_be_review_ready():
    readiness = {
        "protected_stack": {
            "ready": True,
            "m1_m4_preservation_passed": True,
            "kpk_kqk_bridge_preservation_passed": True,
        },
        "stage_status": {
            "stage4": {"ready_for_current_suite": True},
            "stage7": {
                "success_controls_ready": True,
                "success_controls": 5,
                "success_controls_required": 5,
                "ready_for_promotion": True,
            },
        },
    }
    benchmark_review = {
        "decision": {
            "status": "sequence_policy_benchmark_supports_non_causal_sequence_policy_review"
        }
    }

    payload = _review.build_payload(readiness=readiness, benchmark_review=benchmark_review)

    assert (
        payload["decision"]["status"]
        == "stage8_training_review_ready_pending_explicit_approval"
    )
    assert payload["blockers"] == []
    assert payload["warnings"] == []
    assert payload["decision"]["implementation_allowed_by_this_review"] is False
    assert payload["decision"]["stage8_training_allowed"] is False


def test_stage8_training_readiness_review_fixture_blocks_mixed_sequence_result():
    readiness = {
        "protected_stack": {
            "ready": True,
            "m1_m4_preservation_passed": True,
            "kpk_kqk_bridge_preservation_passed": True,
        },
        "stage_status": {
            "stage4": {"ready_for_current_suite": True},
            "stage7": {
                "success_controls_ready": True,
                "success_controls": 5,
                "success_controls_required": 5,
                "ready_for_promotion": False,
            },
        },
    }
    benchmark_review = {
        "decision": {"status": "sequence_policy_benchmark_mixed_plan_window_underpowered"}
    }

    payload = _review.build_payload(readiness=readiness, benchmark_review=benchmark_review)

    assert (
        payload["decision"]["status"]
        == "stage8_training_blocked_pending_stage7_sequence_gate"
    )
    assert "sequence_policy_benchmark_mixed_or_underpowered" in payload["blockers"]
    assert "stage7_not_promoted_and_must_remain_held_out_without_explicit_gate" in payload["warnings"]
    assert payload["decision"]["stage8_training_allowed"] is False
