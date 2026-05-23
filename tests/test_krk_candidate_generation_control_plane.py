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
