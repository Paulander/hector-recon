#!/usr/bin/env python3
"""Tests for KRK cross-stage PlanCapsule evidence requirements and frames."""

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


_requirements = _load_module(
    "write_krk_cross_stage_plan_capsule_evidence_requirements_v0",
    "scripts/write_krk_cross_stage_plan_capsule_evidence_requirements_v0.py",
)
_frames = _load_module(
    "extract_krk_protected_plan_window_frames_v0",
    "scripts/extract_krk_protected_plan_window_frames_v0.py",
)


def _read_report(path: str) -> dict:
    payload = json.loads((ROOT / path).read_text(encoding="utf-8"))
    assert isinstance(payload, dict)
    return payload


def test_cross_stage_plan_capsule_requirements_remain_non_causal():
    payload = _read_report(
        "reports/strategy_arbitration/krk_cross_stage_plan_capsule_evidence_requirements_v0.json"
    )

    assert payload["schema_version"] == "krk_cross_stage_plan_capsule_evidence_requirements.v0"
    assert payload["causal_status"] == "non_causal_requirements_review"
    assert payload["runtime_behavior_changed"] is False
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
    assert (
        payload["decision"]["recommended_next_step"]
        == "continue_non_causal_sequence_policy_design_without_new_labels_or_obtain_protected_failure_contrast_approval"
    )
    readiness = payload["current_readiness"]
    assert readiness["plan_capsule_stage7_only_evidence"] is True
    assert readiness["source_review_protected_cross_stage_evidence"] is False
    assert readiness["replay_free_protected_cross_stage_evidence"] is True
    assert readiness["cross_stage_sequence_evidence_met"] is True
    assert readiness["sequence_policy_benchmark_ready"] is True
    assert (
        readiness["sequence_policy_passive_design_status"]
        == "non_causal_sequence_policy_design_without_new_labels_ready"
    )
    assert readiness["remaining_evidence_gap"] == "protected_plan_window_failure_evidence_sparse"
    assert readiness["protected_failure_contrast_approval_receipt_blockers"] == [
        "approval_receipt_missing"
    ]


def test_cross_stage_plan_capsule_requirements_fixture_can_be_ready():
    payload = _requirements.build_payload(
        plan_capsule_review={
            "readiness": {
                "stage7_only_evidence": False,
                "protected_cross_stage_evidence": True,
                "policy_succeeded": False,
            }
        },
        sequence_policy_design={
            "readiness": {
                "stage7_clean_success_controls_met": True,
                "stage7_clean_failure_controls_met": True,
                "benchmark_ready": True,
                "cross_stage_sequence_evidence_met": True,
                "protected_plan_window_evidence_met": True,
            }
        },
        control_plane_gate={"decision": {"status": "fixture_gate"}},
    )

    assert (
        payload["decision"]["status"]
        == "cross_stage_plan_capsule_evidence_ready_for_non_causal_benchmark"
    )
    assert (
        payload["decision"]["recommended_next_step"]
        == "review_non_causal_sequence_policy_benchmark_results"
    )
    assert payload["decision"]["runtime_changes_allowed"] is False
    assert payload["decision"]["stage8_training_allowed"] is False


def test_protected_plan_window_frames_are_bounded_and_non_causal():
    payload = _read_report(
        "reports/strategy_arbitration/krk_protected_plan_window_frames_v0.json"
    )

    assert payload["schema_version"] == "krk_protected_plan_window_frames.v0"
    assert payload["causal_status"] == "non_causal_replay_free_protected_window_extraction"
    assert payload["runtime_behavior_changed"] is False
    assert payload["runtime_selector_implemented"] is False
    assert payload["runtime_score_changes"] is False
    assert payload["runtime_direct_routing"] is False
    assert payload["runtime_dtm_or_tablebase_lookup"] is False
    assert payload["gameplay_topology_mutation"] is False
    assert payload["stage7_promotion_allowed"] is False
    assert payload["stage8_training_allowed"] is False
    assert payload["summary"]["frame_count"] >= 20
    assert payload["summary"]["protected_cross_stage_evidence_met"] is True
    assert payload["summary"]["selector_training_row_count"] == 0
    assert payload["summary"]["stage7_training_row_count"] == 0
    assert set(payload["summary"]["source_stage_counts"]) == {"stage4", "stage5", "stage6"}
    assert payload["decision"]["runtime_changes_allowed"] is False
    assert payload["decision"]["selector_training_allowed"] is False
    assert payload["decision"]["stage8_training_allowed"] is False
    assert len({frame["frame_id"] for frame in payload["frames"]}) == len(payload["frames"])

    for frame in payload["frames"]:
        assert frame["causal_status"] == "non_causal_replay_free_protected_plan_window"
        assert frame["source_stage"] in {"stage4", "stage5", "stage6"}
        assert frame["stage7_heldout_challenge"] is False
        assert frame["usable_for_selector_training"] is False
        assert frame["usable_for_runtime_authorization"] is False


def test_protected_plan_window_frame_fixture_counts_threshold():
    payload = _frames.build_payload(
        requirements={
            "acceptance_before_sequence_policy_benchmark": {
                "protected_stage4_5_6_frame_count_min": 20
            }
        }
    )

    assert payload["summary"]["frame_count"] >= 20
    assert payload["summary"]["protected_cross_stage_evidence_met"] is True
    assert payload["decision"]["status"] == "protected_cross_stage_plan_window_evidence_extracted"
