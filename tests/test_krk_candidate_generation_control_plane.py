#!/usr/bin/env python3
"""Tests for non-causal KRK candidate-generation control-plane artifacts."""

import importlib.util
from pathlib import Path


_spec = importlib.util.spec_from_file_location(
    "build_krk_candidate_generation_control_plane_v0",
    Path(__file__).resolve().parents[1]
    / "scripts"
    / "build_krk_candidate_generation_control_plane_v0.py",
)
assert _spec is not None
assert _spec.loader is not None
_module = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_module)

_populate_spec = importlib.util.spec_from_file_location(
    "populate_krk_strategy_sequence_candidate_frames_v1",
    Path(__file__).resolve().parents[1]
    / "scripts"
    / "populate_krk_strategy_sequence_candidate_frames_v1.py",
)
assert _populate_spec is not None
assert _populate_spec.loader is not None
_populate = importlib.util.module_from_spec(_populate_spec)
_populate_spec.loader.exec_module(_populate)


def test_candidate_proposal_coverage_preserves_capacity_label_semantics():
    capacity_rows = [
        {
            "state_id": "state.a",
            "frame_id": "frame.a",
            "fen": "8/8/8/8/8/8/8/8 w - - 0 1",
            "source_stage": "stage5",
            "provider_id": "krk.fence_established",
            "provider_family": "fence_established",
            "capacity_label": "positive_capacity",
            "forced_result": "mate",
            "existing_frame_providers": ["krk.stage0_basin"],
            "stage7_challenge_row": False,
        }
    ]
    ranked_rows = [
        {
            "state_id": "state.a",
            "provider_id": "krk.stage0_basin",
        }
    ]

    rows = _module._coverage_rows(capacity_rows, ranked_rows)

    assert rows[0]["provider_visible_in_current_proposals"] is False
    assert rows[0]["candidate_generation_channel"] == (
        "missing_validated_provider_capacity_candidate"
    )
    assert rows[0]["label_semantics"] == "forced_provider_capacity_label"
    assert rows[0]["usable_for_selector_training"] is False
    assert rows[0]["causal_status"] == "non_causal_capacity_coverage_evidence"


def test_candidate_proposal_coverage_summary_excludes_stage7_training_readiness():
    rows = [
        {
            "capacity_label": "positive_capacity",
            "provider_visible_in_current_proposals": False,
            "provider_family": "fence_established",
            "source_stage": "stage5",
            "stage7_challenge_row": False,
        },
        {
            "capacity_label": "negative_capacity",
            "provider_visible_in_current_proposals": True,
            "provider_family": "edge_trap",
            "source_stage": "stage4",
            "stage7_challenge_row": False,
        },
    ]

    summary = _module._summarize_coverage(rows)

    assert summary["positive_capacity_recall"] == 0.0
    assert summary["missing_positive_capacity_count"] == 1
    assert summary["stage7_row_count"] == 0


def test_strategy_sequence_candidate_frame_schema_is_non_causal():
    review = {
        "decision": {
            "future_runtime_sandbox_requires": [
                "candidate-generation candidate set exists",
            ]
        }
    }

    payload = _module.build_frame_schema_payload(review)

    assert payload["causal_status"] == "non_causal_schema_design"
    assert payload["runtime_behavior_changed"] is False
    assert payload["runtime_defaults_changed"] is False
    assert payload["stage7_promotion_allowed"] is False
    assert payload["stage8_training_allowed"] is False
    assert "direct_provider_request" in payload["forbidden_causal_uses"]
    assert "capacity_evidence" in payload["required_fields"]


def test_strategy_sequence_capacity_frames_are_generation_not_selection_labels():
    frames = _populate.capacity_candidate_frames(
        [
            {
                "state_id": "state.a",
                "fen": "8/8/8/8/8/8/8/8 w - - 0 1",
                "source_stage": "stage5",
                "provider_id": "krk.fence_established",
                "provider_family": "fence_established",
                "capacity_label": "positive_capacity",
                "forced_result": "mate",
                "forced_first_move": "a1a2",
                "stage7_challenge_row": False,
            }
        ]
    )

    assert frames[0]["frame_type"] == "validated_provider_candidate"
    assert frames[0]["label_semantics"] == "capacity_evidence_not_ownership_label"
    assert frames[0]["usable_for_selector_training"] is False
    assert frames[0]["usable_for_candidate_generation_training"] is True
    assert frames[0]["causal_status"] == "non_causal"


def test_strategy_sequence_quality_blocks_stage7_training_rows():
    frames_payload = {
        "runtime_behavior_changed": False,
        "runtime_defaults_changed": False,
        "runtime_selector_implemented": False,
        "runtime_candidate_generator_implemented": False,
        "runtime_terminals_added": False,
        "runtime_dtm_or_tablebase_lookup": False,
        "gameplay_topology_mutation": False,
        "stage7_promotion_allowed": False,
        "stage8_training_allowed": False,
        "summary": {
            "readiness_training_stage7_row_count": 1,
        },
        "frames": [
            {
                "label_semantics": "capacity_evidence_not_ownership_label",
                "usable_for_selector_training": False,
                "stage7_challenge_row": True,
                "frame_type": "candidate_move_hypothesis",
                "sequence_evidence": {},
            }
        ],
    }

    quality = _populate.build_quality_payload(frames_payload)

    assert quality["quality_checks"]["stage7_excluded_from_training_readiness"] is False
    assert quality["decision"]["status"] == "frame_quality_blocked"


def test_progress_window_continuation_index_accepts_list_shape():
    indexed = _populate._continuation_index(
        [
            {
                "move": "a1a2",
                "continuation": {
                    "result": "max_plies",
                },
            }
        ]
    )

    assert indexed == {"a1a2": {"result": "max_plies"}}
