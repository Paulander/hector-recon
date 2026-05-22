#!/usr/bin/env python3
"""Tests for non-causal progress-window reconsideration audit helpers."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from scripts.audit_krk_progress_window_reconsideration_post_activation_v0 import (
    _classification,
    _recommended_next,
)


def test_post_activation_classifies_missing_good_candidate_when_supported_moves_fail():
    records = [
        {
            "supported_candidate_mate_count": 0,
            "unsupported_visible_candidate_mate_count": 0,
            "selected_supported_continuation_h40": {"result": "max_plies"},
            "selected_supported_move_improves_local_progress_terms": True,
            "selected_supported_move_preserves_safety": True,
        }
    ]

    result = _classification(records)

    assert result["primary"] == "candidate_set_missing_good_alternative"
    assert "visible_support_terms_overbroad" in result["labels"]
    assert _recommended_next(result["primary"]) == (
        "return_to_candidate_generation_or_broader_strategy_sequence_track"
    )


def test_post_activation_classifies_ranking_when_supported_mate_exists_unselected():
    records = [
        {
            "supported_candidate_mate_count": 1,
            "unsupported_visible_candidate_mate_count": 0,
            "selected_supported_continuation_h40": {"result": "max_plies"},
            "selected_supported_move_improves_local_progress_terms": True,
            "selected_supported_move_preserves_safety": True,
        }
    ]

    result = _classification(records)

    assert result["primary"] == "supported_candidate_ranking_wrong"
