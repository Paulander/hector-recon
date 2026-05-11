#!/usr/bin/env python3
"""Tests for visible KRK successor-affordance nodes."""

import sys
from pathlib import Path

import chess

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from recon_lite_chess.krk_baseline_nodes import (
    create_krk_context_terminal,
    create_krk_successor_affordance,
)


def test_context_terminal_is_inert_when_successor_layer_disabled():
    node = create_krk_context_terminal("terminal.krk.fence_exists")
    node.meta["term"] = "fence_exists"
    env = {
        "board": chess.Board("4k3/1R6/1K6/8/8/8/8/8 w - - 0 1"),
        "blackboard": {"successor_affordance_layer_enabled": False},
    }

    success, done = node.predicate(node, env)

    assert success is False
    assert done is True
    assert "krk_visible_terms" not in env["blackboard"]


def test_visible_successor_affordance_records_source_terms_when_enabled():
    env = {
        "board": chess.Board("4k3/1R6/1K6/8/8/8/8/8 w - - 0 1"),
        "blackboard": {"successor_affordance_layer_enabled": True},
    }
    context = create_krk_context_terminal("terminal.krk.rook_safe")
    context.meta["term"] = "rook_safe"
    context.predicate(context, env)

    affordance = create_krk_successor_affordance("script.krk.successor.edge_trap_close_affordance")
    affordance.meta.update({
        "successor_skill_id": "krk.edge_trap_close",
        "source_terms": ["rook_safe", "enemy_king_not_at_edge"],
        "required_terms": ["rook_safe"],
        "veto_terms": ["mate_basin_available"],
    })

    success, done = affordance.predicate(affordance, env)

    payload = env["blackboard"]["krk_successor_affordances"]["krk.edge_trap_close"]
    assert success is True
    assert done is True
    assert payload["score"] == 0.5
    assert payload["source_terms"] == ["rook_safe"]
    assert payload["veto_terms"] == []
