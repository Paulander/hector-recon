#!/usr/bin/env python3
"""Tests for reviewed Stage 7 diverse clean sampling manifest."""

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


_manifest = _load_module(
    "write_stage7_diverse_clean_sampling_manifest_v0",
    "scripts/write_stage7_diverse_clean_sampling_manifest_v0.py",
)


def _read_report(path: str) -> dict:
    payload = json.loads((ROOT / path).read_text(encoding="utf-8"))
    assert isinstance(payload, dict)
    return payload


def test_stage7_diverse_clean_sampling_manifest_requires_approval():
    payload = _read_report(
        "reports/structural_candidates/stage7_diverse_clean_sampling_manifest_v0.json"
    )

    assert payload["schema_version"] == "stage7_diverse_clean_sampling_manifest.v0"
    assert payload["causal_status"] == "non_causal_label_manifest_review_only"
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
        == "stage7_diverse_clean_sampling_manifest_review_ready_pending_explicit_approval"
    )
    assert payload["decision"]["implementation_authorized_by_this_manifest"] is False
    assert payload["decision"]["runtime_changes_allowed"] is False
    assert payload["decision"]["stage7_promotion_allowed"] is False
    assert payload["decision"]["stage8_training_allowed"] is False
    assert payload["summary"]["job_count"] == 8
    assert payload["summary"]["max_total_samples"] == 64
    assert payload["summary"]["topology_exists"] is True
    assert payload["summary"]["label_run_allowed_by_this_manifest"] is False
    assert payload["summary"]["stage7_training_row_count"] == 0


def test_stage7_diverse_clean_sampling_jobs_are_bounded_and_clean():
    payload = _read_report(
        "reports/structural_candidates/stage7_diverse_clean_sampling_manifest_v0.json"
    )

    forbidden_flags = set(payload["jobs"][0]["forbidden_flags"])
    assert "--enable-stage7-king-tempo" in forbidden_flags
    assert "--enable-candidate-move-layer" in forbidden_flags
    for job in payload["jobs"]:
        command = job["command"]
        assert job["samples"] == 8
        assert job["playout_max_plies"] == 40
        assert job["runtime_work_allowed"] is False
        assert job["stage7_training_row"] is False
        assert job["stage7_promotion_allowed"] is False
        assert job["stage8_training_allowed"] is False
        for flag in job["forbidden_flags"]:
            assert flag not in command
        assert "--label" in command
        assert command[command.index("--label") + 1] == "box_shrink"
        assert "--source-stage-names" in command
        assert "--playout-max-plies" in command
        assert command[command.index("--playout-max-plies") + 1] == "40"


def test_stage7_diverse_clean_sampling_manifest_fixture_uses_active_topology():
    active_stack = {
        "active_protected_stack": {
            "stage6_drive_overlay": {
                "topology": "snapshots/krk_triplet_pipeline/clean_retrain_checkpoint_v0_retry1/stage6_overlay_composed/topology/krk_entry_topology.json"
            }
        }
    }
    recovery = {
        "acceptance": {"clean_sequence_success_controls_required": 5},
        "summary": {
            "role_counts": {
                "clean_sequence_success_control": 2,
                "clean_sequence_hard_negative": 8,
            }
        },
    }
    sampling_review = {"summary": {"sampling_overlap_detected": True}}

    payload = _manifest.build_payload(
        active_stack=active_stack,
        recovery=recovery,
        sampling_review=sampling_review,
    )

    assert payload["summary"]["job_count"] == 8
    assert payload["summary"]["label_run_allowed_by_this_manifest"] is False
    assert payload["jobs"][0]["topology"] == active_stack["active_protected_stack"]["stage6_drive_overlay"]["topology"]
    assert payload["current_gap"]["clean_sequence_success_controls_have"] == 2
    assert payload["current_gap"]["clean_sequence_hard_negatives_have"] == 8
    assert payload["decision"]["implementation_authorized_by_this_manifest"] is False
