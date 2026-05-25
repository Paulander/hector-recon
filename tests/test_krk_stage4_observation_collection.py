#!/usr/bin/env python3
"""Tests for Stage 4 observation-only joined trace/ownership collection."""

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


_collection = _load_module(
    "run_krk_stage4_joined_trace_ownership_collection_v0",
    "scripts/run_krk_stage4_joined_trace_ownership_collection_v0.py",
)
_manifest = _load_module(
    "build_krk_selector_objective_seed_manifest_v2",
    "scripts/build_krk_selector_objective_seed_manifest_v2.py",
)
_probe = _load_module(
    "probe_krk_selector_objective_seed_manifest_v2",
    "scripts/probe_krk_selector_objective_seed_manifest_v2.py",
)


def _read_report(path: str) -> dict:
    payload = json.loads((ROOT / path).read_text(encoding="utf-8"))
    assert isinstance(payload, dict)
    return payload


def test_stage4_collection_report_is_observation_only_and_valid():
    payload = _read_report(
        "reports/strategy_arbitration/krk_stage4_joined_trace_ownership_collection_v0.json"
    )

    assert payload["schema_version"] == "krk_stage4_joined_trace_ownership_collection.v0"
    assert payload["decision"]["status"] == "stage4_joined_trace_ownership_collection_complete"
    assert payload["decision"]["collection_valid"] is True
    assert payload["decision"]["selector_allowed"] is False
    assert payload["decision"]["runtime_changes_allowed"] is False
    assert payload["runtime_behavior_changed"] is False
    assert payload["runtime_score_changes"] is False
    assert payload["runtime_direct_routing"] is False
    assert payload["runtime_dtm_or_tablebase_lookup"] is False
    assert payload["gameplay_topology_mutation"] is False
    summary = payload["summary"]
    assert summary["stage4_row_count"] == 6
    assert summary["stage7_training_row_count"] == 0
    assert summary["selector_training_row_count"] == 0
    assert summary["default_off_equivalence_passed"] is True
    assert summary["selected_move_delta_count"] == 0
    assert summary["selected_provider_delta_count"] == 0
    assert summary["score_delta_count"] == 0
    assert summary["routing_delta_count"] == 0


def test_stage4_collection_fixture_preserves_boundaries():
    packet = {
        "approved_if_later_explicitly_authorized": {
            "max_rows": 2,
            "protected_stages": ["stage4"],
            "excluded_stages": ["stage5", "stage6", "stage7", "stage8"],
        },
        "review_rows": [
            {
                "state_id": "state.stage4",
                "source_stage": "stage4",
                "selected_provider": "krk.stage0_basin",
                "target_label": "selected_owner_failed",
            },
            {
                "state_id": "state.stage7",
                "source_stage": "stage7",
                "selected_provider": "krk.box_shrink",
                "target_label": "selected_owner_failed",
            },
        ],
    }
    context = {
        "rows": [
            {
                "state_id": "state.stage4",
                "frame_id": "cp.krk.state.stage4",
                "fen": "8/k7/3K4/8/8/1R6/8/8 w - - 2 2",
                "active_landmark_label": "wrong_tempo_control",
            },
            {
                "state_id": "state.stage7",
                "frame_id": "cp.krk.state.stage7",
                "fen": "8/k7/3K4/8/8/1R6/8/8 w - - 2 2",
                "active_landmark_label": "box_shrink",
            },
        ]
    }

    def fake_runner(case, enabled):
        if not enabled:
            return {
                "move": "d6c7",
                "selected_provider": "krk.stage0_basin",
                "confidence": 1.0,
                "observation": {},
            }
        return {
            "move": "d6c7",
            "selected_provider": "krk.stage0_basin",
            "confidence": 1.0,
            "observation": {
                "frames": [
                    {
                        "candidate_source": "validated_provider_pack",
                        "capacity_evidence_kind": "positive_capacity",
                        "causal_status": "observation_only",
                        "direct_request": False,
                        "score_delta": 0.0,
                        "protected_status": "protected_control",
                    }
                ]
            },
        }

    payload = _collection.build_payload(
        packet=packet,
        context=context,
        decision_runner=fake_runner,
    )

    assert payload["summary"]["attempted_row_count"] == 1
    assert payload["summary"]["stage4_row_count"] == 1
    assert payload["summary"]["stage7_training_row_count"] == 0
    assert payload["summary"]["switch_contrast_with_positive_capacity_count"] == 1
    assert payload["decision"]["collection_valid"] is True
    assert payload["decision"]["selector_allowed"] is False


def test_selector_seed_manifest_v2_adds_stage4_without_training_rows():
    payload = _read_report("reports/strategy_arbitration/krk_selector_objective_seed_manifest_v2.json")

    assert payload["schema_version"] == "krk_selector_objective_seed_manifest.v2"
    assert payload["decision"]["status"] == "selector_objective_seed_manifest_v2_ready_non_causal"
    assert payload["summary"]["added_stage4_seed_row_count"] == 6
    assert payload["summary"]["source_stage_counts"]["stage4"] == 6
    assert payload["summary"]["candidate_switch_contrast_seed_count"] >= 4
    assert payload["summary"]["safe_preservation_contrast_seed_count"] >= 4
    assert payload["summary"]["selector_training_row_count"] == 0
    assert payload["summary"]["stage7_training_row_count"] == 0
    assert payload["decision"]["selector_allowed"] is False
    assert payload["decision"]["runtime_changes_allowed"] is False


def test_selector_seed_manifest_v2_fixture_counts_switch_and_preserve():
    seed_v1 = {
        "seed_rows": [
            {
                "state_id": "safe",
                "source_stage": "stage5",
                "selected_provider": "krk.stage0_basin",
                "selected_owner_label": "selected_owner_converted",
                "positive_trace_provider_candidate_count": 1,
                "objective_channel": "safe_preservation_contrast_seed",
            }
        ]
    }
    collection = {
        "decision": {"collection_valid": True},
        "rows": [
            {
                "state_id": "switch",
                "source_stage": "stage4",
                "selected_provider_label": "krk.stage0_basin",
                "selected_owner_label": "selected_owner_failed",
                "enabled_observation_frame_count": 3,
                "positive_capacity_frame_count": 1,
                "recovery_class": "stage4_selected_failure_with_visible_positive_capacity",
                "joined_trace_ownership_row": True,
            }
        ],
    }

    payload = _manifest.build_payload(seed_v1=seed_v1, stage4_collection=collection)

    assert payload["summary"]["added_stage4_seed_row_count"] == 1
    assert payload["summary"]["candidate_switch_contrast_seed_count"] == 1
    assert payload["summary"]["safe_preservation_contrast_seed_count"] == 1
    assert payload["summary"]["selector_training_row_count"] == 0
    assert payload["summary"]["stage7_training_row_count"] == 0


def test_selector_seed_probe_v2_ready_but_non_causal():
    payload = _read_report("reports/strategy_arbitration/krk_selector_objective_seed_probe_v2.json")

    assert payload["schema_version"] == "krk_selector_objective_seed_probe.v2"
    assert (
        payload["decision"]["status"]
        == "selector_objective_seed_probe_v2_ready_for_non_causal_benchmark"
    )
    assert payload["summary"]["has_switch_and_preserve_seeds"] is True
    assert payload["summary"]["benchmark_underpowered"] is False
    assert payload["summary"]["runtime_feature_eligible_prediction_count"] == 0
    assert payload["summary"]["selector_training_row_count"] == 0
    assert payload["summary"]["stage7_training_row_count"] == 0
    assert payload["interpretation"]["semantics_confirmed"] is True
    assert payload["interpretation"]["selector_training_supported"] is False
    assert payload["interpretation"]["runtime_selector_supported"] is False
    assert payload["decision"]["selector_allowed"] is False
