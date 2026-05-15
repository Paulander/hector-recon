#!/usr/bin/env python3
"""Tests for diagnostic-only KRK evaluation speedups."""

import chess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from scripts.test_krk_landmark_progress import (
    _classify_successor_failure,
    _compact_playout_trace,
    _finalize_perf_profile,
    _mate_in_one_available,
    _new_perf_profile,
    _profile_add_count,
    _profile_add_time,
    _playout_stagnation_summary,
    _suggestion_stability_signature,
)


def test_suggestion_stability_signature_uses_top_ranked_move_and_skill():
    suggestions = [
        {
            "move": chess.Move.from_uci("h7c7"),
            "score": 0.1,
            "actuator": "actuator_low",
            "meta": {"curriculum_label": "edge_trap_close"},
        },
        {
            "move": chess.Move.from_uci("h7h1"),
            "score": 0.2,
            "actuator": "actuator_high",
            "meta": {"curriculum_label": "edge_trap_enemy_between"},
        },
    ]

    assert _suggestion_stability_signature(suggestions) == (
        ("krk.edge_trap_enemy_between", "h7h1", "actuator_high"),
    )


def test_suggestion_stability_signature_respects_forced_successor_filter():
    suggestions = [
        {
            "move": chess.Move.from_uci("h7h1"),
            "score": 0.2,
            "actuator": "actuator_high",
            "meta": {"curriculum_label": "edge_trap_enemy_between"},
        },
        {
            "move": chess.Move.from_uci("h7c7"),
            "score": 0.1,
            "actuator": "actuator_low",
            "meta": {"curriculum_label": "edge_trap_close"},
        },
    ]

    assert _suggestion_stability_signature(
        suggestions,
        forced_successor_skill="krk.edge_trap_close",
    ) == (("krk.edge_trap_close", "h7c7", "actuator_low"),)


def test_compact_playout_trace_keeps_selected_skill_and_top_suggestions():
    compact = _compact_playout_trace([
        {
            "ply": 3,
            "turn": "white",
            "fen": "8/8/8/8/8/8/8/8 w - - 0 1",
            "move": "h7d7",
            "resulting_fen": "8/8/8/8/8/8/8/8 b - - 1 1",
            "engine": {
                "move": "h7d7",
                "confidence": 0.14,
                "ticks": 8,
                "early_stopped": True,
                "suggestions": [
                    {
                        "move": "h7d7",
                        "score": 0.14,
                        "actuator": "actuator_1",
                        "meta": {"curriculum_label": "edge_trap_close"},
                    }
                ],
            },
        }
    ])

    assert compact[0]["selected_skill"] == "krk.edge_trap_close"
    assert compact[0]["top_suggestions"] == [
        {"move": "h7d7", "skill_id": "krk.edge_trap_close", "score": 0.14}
    ]


def test_horizon_mate_in_one_available_detects_white_mate_at_limit():
    board = chess.Board("8/5K1k/8/8/8/8/8/2R5 w - - 20 11")

    assert _mate_in_one_available(board)


def test_classify_successor_failure_marks_horizon_mate_in_one():
    classes = _classify_successor_failure(
        parent_skill="krk.fence_established",
        local_confirmed=True,
        conversion_result="max_plies",
        successor_summary={
            "selected_skill": "krk.edge_trap_close",
            "best_score": 0.02,
            "visible_terms": {},
            "missing_afforded_skills": {},
            "route_conflict": False,
            "handoff_gap": False,
        },
        high_score_threshold=5.0,
        final_mate_in_one_available=True,
    )

    assert "horizon_mate_in_one" in classes


def test_playout_stagnation_summary_detects_rook_oscillation():
    summary = _playout_stagnation_summary([
        {
            "turn": "white",
            "fen": "6k1/8/K7/8/4R3/8/8/8 w - - 16 9",
            "move": "e4h4",
            "resulting_fen": "6k1/8/K7/8/7R/8/8/8 b - - 17 9",
        },
        {
            "turn": "black",
            "fen": "6k1/8/K7/8/7R/8/8/8 b - - 17 9",
            "move": "g8f8",
            "resulting_fen": "5k2/8/K7/8/7R/8/8/8 w - - 18 10",
        },
        {
            "turn": "white",
            "fen": "5k2/8/K7/8/7R/8/8/8 w - - 18 10",
            "move": "h4e4",
            "resulting_fen": "5k2/8/K7/8/4R3/8/8/8 b - - 19 10",
        },
    ])

    assert summary["rook_oscillation_detected"]
    assert summary["rook_oscillation_pairs"] == [
        {"moves": "e4h4 / h4e4", "count": 1}
    ]


def test_performance_profile_schema_round_trips_core_buckets():
    profile = _new_perf_profile(True, diagnostic_caches_enabled=True)
    _profile_add_time(profile, "choose_move_details_time", 1.25)
    _profile_add_time(profile, "engine_step_time", 0.75)
    _profile_add_time(profile, "total_wall_time", 2.0)
    _profile_add_count(profile, "samples", 3)
    _profile_add_count(profile, "engine_ticks", 42)

    finalized = _finalize_perf_profile(profile)

    assert finalized["schema_version"] == "krk_performance_profile.v1"
    assert finalized["timers_sec"]["choose_move_details_time"] == 1.25
    assert finalized["timers_sec"]["engine_step_time"] == 0.75
    assert finalized["counts"]["samples"] == 3
    assert finalized["counts"]["engine_ticks"] == 42
    assert finalized["diagnostic_caches_enabled"] is True
    assert "cache" in finalized
