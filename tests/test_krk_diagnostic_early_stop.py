#!/usr/bin/env python3
"""Tests for diagnostic-only KRK evaluation speedups."""

import chess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from scripts.test_krk_landmark_progress import (
    COMPOSITION_PROFILE_HANDOFF_V1,
    COMPOSITION_PROFILE_NONE,
    _apply_composition_profile_to_eval_kwargs,
    _classify_successor_failure,
    _cli_option_provided,
    _compact_playout_trace,
    _composition_profile_metadata,
    _finalize_perf_profile,
    _merge_count_dict,
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


def test_merge_count_dict_handles_nested_buckets():
    target = {"a": 1, "nested": {"mate": 2}}
    _merge_count_dict(target, {"a": 3, "nested": {"mate": 4, "draw": 1}})

    assert target == {"a": 4, "nested": {"mate": 6, "draw": 1}}


def test_composition_profile_none_preserves_default_eval_kwargs():
    base = {
        "successor_affordance_layer_enabled": False,
        "successor_role_license_enabled": False,
        "successor_role_scoped_move_shape_enabled": False,
        "enable_diagnostic_caches": False,
    }

    updated, runtime_overrides = _apply_composition_profile_to_eval_kwargs(
        base,
        COMPOSITION_PROFILE_NONE,
    )

    assert updated == {**base, "composition_profile": None}
    assert runtime_overrides == {}


def test_handoff_composition_v1_applies_named_experimental_profile():
    base = {
        "successor_affordance_layer_enabled": False,
        "successor_role_license_enabled": False,
        "successor_role_scoped_move_shape_enabled": False,
        "successor_role_scoped_move_shape_bonus": 0.0,
        "stagnation_breaker_enabled": False,
        "stagnation_breaker_bonus": 0.0,
        "post_break_continuation_enabled": False,
        "post_break_continuation_bonus": 0.0,
        "successor_stage0_drift_penalty": 0.0,
        "enable_diagnostic_caches": False,
    }

    updated, runtime_overrides = _apply_composition_profile_to_eval_kwargs(
        base,
        COMPOSITION_PROFILE_HANDOFF_V1,
        use_validation_defaults=True,
    )

    assert updated["composition_profile"] == COMPOSITION_PROFILE_HANDOFF_V1
    assert updated["successor_affordance_layer_enabled"] is True
    assert updated["successor_role_license_enabled"] is True
    assert updated["successor_role_scoped_move_shape_enabled"] is True
    assert updated["successor_role_scoped_move_shape_bonus"] == 0.05
    assert updated["stagnation_breaker_enabled"] is True
    assert updated["stagnation_breaker_bonus"] == 0.5
    assert updated["post_break_continuation_enabled"] is True
    assert updated["post_break_continuation_bonus"] == 0.25
    assert updated["successor_stage0_drift_penalty"] == 6.0
    assert updated["enable_diagnostic_caches"] is True
    assert runtime_overrides == {"parallel_workers": 8, "chunk_size": 25}


def test_handoff_composition_v1_metadata_is_non_default_and_domain_scoped():
    metadata = _composition_profile_metadata(COMPOSITION_PROFILE_HANDOFF_V1)

    assert metadata["schema_version"] == "composition_profile.v1"
    assert metadata["profile_id"] == COMPOSITION_PROFILE_HANDOFF_V1
    assert metadata["domain"] == "KRK"
    assert metadata["experimental_profile"] is True
    assert metadata["default_policy"] is False
    assert "handoff_packets" in metadata["non_causal_records"]


def test_cli_option_provided_accepts_space_and_equals_forms():
    assert _cli_option_provided("--parallel-workers", ["--parallel-workers", "1"])
    assert _cli_option_provided("--parallel-workers", ["--parallel-workers=1"])
    assert not _cli_option_provided("--parallel-workers", ["--chunk-size", "25"])
