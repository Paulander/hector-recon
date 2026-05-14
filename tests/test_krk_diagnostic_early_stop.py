#!/usr/bin/env python3
"""Tests for diagnostic-only KRK evaluation speedups."""

import chess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from scripts.test_krk_landmark_progress import _suggestion_stability_signature


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
