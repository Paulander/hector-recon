#!/usr/bin/env python3
"""Tests for visible KRK successor-affordance nodes."""

import sys
from pathlib import Path

import chess

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from recon_lite_chess.krk_baseline_nodes import (
    _apply_successor_affordance_bias,
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


def test_edge_trapped_black_king_counts_as_visible_fence_contract():
    env = {
        "board": chess.Board("4k3/7R/1K6/8/8/8/8/8 b - - 1 1"),
        "blackboard": {"successor_affordance_layer_enabled": True},
    }
    context = create_krk_context_terminal("terminal.krk.fence_exists")
    context.meta["term"] = "fence_exists"

    success, done = context.predicate(context, env)

    assert success is True
    assert done is True
    assert env["blackboard"]["krk_visible_terms"]["fence_exists"] is True


def test_fence_maintenance_affordance_can_be_visible_without_durable_skill():
    env = {
        "board": chess.Board("4k3/1R6/1K6/8/8/8/8/8 w - - 0 1"),
        "blackboard": {
            "successor_affordance_layer_enabled": True,
            "krk_visible_terms": {
                "fence_exists": True,
                "fence_needs_repair": True,
                "rook_safe": True,
                "fence_already_satisfied": False,
            },
        },
    }

    affordance = create_krk_successor_affordance("script.krk.successor.fence_maintenance_affordance")
    affordance.meta.update({
        "successor_skill_id": "krk.fence_maintenance",
        "source_terms": ["fence_exists", "fence_needs_repair", "rook_safe"],
        "required_terms": ["fence_exists", "rook_safe"],
        "veto_terms": ["fence_already_satisfied"],
    })

    success, done = affordance.predicate(affordance, env)

    payload = env["blackboard"]["krk_successor_affordances"]["krk.fence_maintenance"]
    assert success is True
    assert done is True
    assert payload["score"] > 0.0
    assert payload["successor"] == "krk.fence_maintenance"


def test_contract_gate_penalizes_unmet_stage0_when_edge_trap_is_eligible():
    move_meta = {}
    adjusted = _apply_successor_affordance_bias(
        5.7,
        skill_id="krk.stage0_basin",
        curriculum_label="stage0_basin",
        blackboard={
            "successor_contract_gate_enabled": True,
            "successor_contract_mismatch_penalty": 10.0,
            "krk_successor_affordances": {
                "krk.stage0_basin": {
                    "score": 0.0,
                    "required_terms": ["mate_basin_available"],
                    "missing_required_terms": ["mate_basin_available"],
                    "veto_terms": [],
                    "contract_met": False,
                },
                "krk.edge_trap_close": {
                    "score": 0.75,
                    "required_terms": ["rook_safe"],
                    "missing_required_terms": [],
                    "veto_terms": [],
                    "contract_met": True,
                },
            },
        },
        move_meta=move_meta,
    )

    assert adjusted < 0.0
    assert move_meta["visible_contract_gate_penalty"] == 10.0
    assert move_meta["visible_contract_gate_reason"]["eligible_alternatives"] == [
        "krk.edge_trap_close"
    ]


def test_contract_gate_does_not_penalize_without_visible_alternative():
    move_meta = {}
    adjusted = _apply_successor_affordance_bias(
        5.7,
        skill_id="krk.stage0_basin",
        curriculum_label="stage0_basin",
        blackboard={
            "successor_contract_gate_enabled": True,
            "successor_contract_mismatch_penalty": 10.0,
            "krk_successor_affordances": {
                "krk.stage0_basin": {
                    "score": 0.0,
                    "missing_required_terms": ["mate_basin_available"],
                    "veto_terms": [],
                    "contract_met": False,
                },
                "krk.edge_trap_close": {
                    "score": 0.0,
                    "missing_required_terms": ["rook_safe"],
                    "veto_terms": [],
                    "contract_met": False,
                },
            },
        },
        move_meta=move_meta,
    )

    assert adjusted == 5.7
    assert "visible_contract_gate_penalty" not in move_meta


def test_role_license_bonus_supports_provider_without_contract_penalty():
    move_meta = {}
    adjusted = _apply_successor_affordance_bias(
        5.7,
        skill_id="krk.stage0_basin",
        curriculum_label="stage0_basin",
        blackboard={
            "successor_role_license_enabled": True,
            "successor_role_license_bonus": 0.05,
            "krk_successor_affordances": {
                "krk.stage0_finish": {
                    "score": 0.0,
                    "role_id": "krk.stage0_finish",
                    "provider_skill_ids": ["krk.stage0_basin"],
                    "missing_required_terms": ["mate_in_one_available"],
                    "veto_terms": [],
                    "contract_met": False,
                },
            },
            "krk_successor_provider_licenses": {
                "krk.stage0_basin": {
                    "krk.stage0_king_approach_after_fence": {
                        "score": 0.75,
                        "role_id": "krk.stage0_king_approach_after_fence",
                        "provider_skill_ids": ["krk.stage0_basin"],
                        "source_terms": ["rook_safe", "white_king_can_improve_support"],
                        "missing_required_terms": [],
                        "veto_terms": [],
                        "contract_met": True,
                    }
                }
            },
        },
        move_meta=move_meta,
    )

    assert abs(adjusted - (5.7 + (0.05 * 0.75))) < 1e-9
    assert abs(move_meta["visible_role_license_bonus"] - (0.05 * 0.75)) < 1e-9
    assert move_meta["visible_role_licenses"][0]["role_id"] == "krk.stage0_king_approach_after_fence"
    assert "visible_contract_gate_penalty" not in move_meta


def test_successor_affordance_records_role_and_provider_license():
    env = {
        "board": chess.Board("4k3/1R6/1K6/8/8/8/8/8 w - - 0 1"),
        "blackboard": {
            "successor_affordance_layer_enabled": True,
            "krk_visible_terms": {
                "rook_safe": True,
                "king_approach_after_fence_available": True,
            },
        },
    }
    affordance = create_krk_successor_affordance("script.krk.successor.stage0_approach_affordance")
    affordance.meta.update({
        "successor_skill_id": "krk.stage0_king_approach_after_fence",
        "role_id": "krk.stage0_king_approach_after_fence",
        "provider_skill_ids": ["krk.stage0_basin"],
        "source_terms": ["rook_safe", "king_approach_after_fence_available"],
        "required_terms": ["rook_safe"],
        "veto_terms": ["mate_in_one_available"],
    })

    success, done = affordance.predicate(affordance, env)

    payload = env["blackboard"]["krk_successor_role_affordances"]["krk.stage0_king_approach_after_fence"]
    licenses = env["blackboard"]["krk_successor_provider_licenses"]["krk.stage0_basin"]
    assert success is True
    assert done is True
    assert payload["role_id"] == "krk.stage0_king_approach_after_fence"
    assert payload["provider_skill_ids"] == ["krk.stage0_basin"]
    assert licenses["krk.stage0_king_approach_after_fence"]["contract_met"] is True
