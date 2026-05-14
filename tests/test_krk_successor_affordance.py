#!/usr/bin/env python3
"""Tests for visible KRK successor-affordance nodes."""

import sys
from pathlib import Path

import chess

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from recon_lite_chess.krk_baseline_nodes import (
    _apply_successor_affordance_bias,
    _apply_visible_stage0_drift_penalty,
    _apply_visible_rook_transfer_move_bias,
    _compute_krk_context_terms,
    create_krk_context_terminal,
    create_krk_successor_affordance,
    krk_move_shape_audit,
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


def test_unmet_or_vetoed_role_license_does_not_bonus_provider():
    for role_payload in [
        {
            "score": 0.75,
            "role_id": "krk.stage0_king_approach_after_fence",
            "provider_skill_ids": ["krk.stage0_basin"],
            "missing_required_terms": ["white_king_can_improve_support"],
            "veto_terms": [],
            "contract_met": False,
        },
        {
            "score": 0.75,
            "role_id": "krk.stage0_king_approach_after_fence",
            "provider_skill_ids": ["krk.stage0_basin"],
            "missing_required_terms": [],
            "veto_terms": ["mate_in_one_available"],
            "contract_met": False,
        },
    ]:
        move_meta = {}
        adjusted = _apply_successor_affordance_bias(
            5.7,
            skill_id="krk.stage0_basin",
            curriculum_label="stage0_basin",
            blackboard={
                "successor_role_license_enabled": True,
                "successor_role_license_bonus": 0.05,
                "krk_successor_provider_licenses": {
                    "krk.stage0_basin": {
                        "krk.stage0_king_approach_after_fence": role_payload
                    }
                },
            },
            move_meta=move_meta,
        )

        assert adjusted == 5.7
        assert "visible_role_license_bonus" not in move_meta


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


def test_context_terminal_caches_full_term_vector_per_board():
    env = {
        "board": chess.Board("4k3/1R6/1K6/8/8/8/8/8 w - - 0 1"),
        "blackboard": {"successor_affordance_layer_enabled": True},
    }
    first = create_krk_context_terminal("terminal.krk.fence_exists")
    first.meta["term"] = "fence_exists"
    second = create_krk_context_terminal("terminal.krk.rook_safe")
    second.meta["term"] = "rook_safe"

    first.predicate(first, env)
    second.predicate(second, env)

    assert env["blackboard"]["krk_context_terms_cache_misses"] == 1
    assert env["blackboard"]["krk_context_terms_cache_hits"] == 1
    assert env["blackboard"]["krk_visible_terms"]["fence_exists"] is True
    assert env["blackboard"]["krk_visible_terms"]["rook_safe"] is True


def test_failed_post_fence_families_expose_rook_transfer_terms():
    for fen in [
        "5k2/7R/1K6/8/8/8/8/8 w - - 2 2",
        "5k2/7R/K7/8/8/8/8/8 w - - 2 2",
        "1k6/7R/2K5/8/8/8/8/8 w - - 2 2",
    ]:
        terms = _compute_krk_context_terms(chess.Board(fen))

        assert terms["post_fence_conversion_needed"] is True
        assert terms["rook_safe"] is True
        assert terms["rook_transfer_after_fence_available"] is True
        assert terms["edge_rook_transfer_recovery_available"] is True
        assert terms["safe_rook_edge_transfer_available"] is True


def test_rook_transfer_role_can_license_multiple_edge_trap_providers():
    env = {
        "board": chess.Board("5k2/7R/1K6/8/8/8/8/8 w - - 2 2"),
        "blackboard": {
            "successor_affordance_layer_enabled": True,
            "krk_visible_terms": {
                "rook_transfer_after_fence_available": True,
                "safe_rook_long_transfer_available": True,
                "safe_rook_edge_transfer_available": True,
                "rook_has_safe_lateral_transfer": True,
                "post_fence_conversion_needed": True,
                "rook_safe": True,
            },
        },
    }
    affordance = create_krk_successor_affordance("script.krk.successor.rook_transfer_after_fence")
    providers = [
        "krk.edge_trap_close",
        "krk.edge_trap_enemy_between",
        "krk.edge_trap_wrong_tempo",
    ]
    affordance.meta.update({
        "successor_skill_id": "krk.rook_transfer_after_fence",
        "role_id": "krk.rook_transfer_after_fence",
        "provider_skill_ids": providers,
        "source_terms": [
            "rook_transfer_after_fence_available",
            "safe_rook_long_transfer_available",
            "safe_rook_edge_transfer_available",
            "rook_has_safe_lateral_transfer",
            "post_fence_conversion_needed",
            "rook_safe",
        ],
        "required_terms": ["rook_transfer_after_fence_available", "rook_safe"],
        "veto_terms": ["mate_in_one_available"],
    })

    success, done = affordance.predicate(affordance, env)

    assert success is True
    assert done is True
    for provider in providers:
        licenses = env["blackboard"]["krk_successor_provider_licenses"][provider]
        assert licenses["krk.rook_transfer_after_fence"]["contract_met"] is True


def test_visible_rook_transfer_move_bonus_supports_matching_rook_transfer_shapes():
    board = chess.Board("5k2/7R/1K6/8/8/8/8/8 w - - 2 2")
    blackboard = {
        "successor_role_license_enabled": True,
        "successor_role_scoped_move_shape_enabled": True,
        "successor_role_scoped_move_shape_bonus": 0.05,
        "krk_successor_provider_licenses": {
            "krk.edge_trap_close": {
                "krk.rook_transfer_after_fence": {
                    "score": 1.0,
                    "role_id": "krk.rook_transfer_after_fence",
                    "provider_skill_ids": ["krk.edge_trap_close"],
                    "source_terms": ["rook_transfer_after_fence_available", "rook_safe"],
                    "missing_required_terms": [],
                    "veto_terms": [],
                    "contract_met": True,
                }
            }
        },
    }
    vertical_meta = {}
    horizontal_meta = {}

    vertical = _apply_visible_rook_transfer_move_bias(
        0.0,
        board=board,
        move=chess.Move.from_uci("h7h1"),
        skill_id="krk.edge_trap_close",
        blackboard=blackboard,
        move_meta=vertical_meta,
    )
    horizontal = _apply_visible_rook_transfer_move_bias(
        0.0,
        board=board,
        move=chess.Move.from_uci("h7c7"),
        skill_id="krk.edge_trap_close",
        blackboard=blackboard,
        move_meta=horizontal_meta,
    )

    assert vertical > 0.0
    assert horizontal > 0.0
    assert vertical_meta["visible_role_scoped_move_shape_bonus"] > 0.0
    assert horizontal_meta["visible_role_scoped_move_shape_bonus"] > 0.0
    assert vertical_meta["visible_role_scoped_move_shape_licenses"]
    assert horizontal_meta["visible_role_scoped_move_shape_licenses"]


def test_edge_rook_recovery_requires_specific_transfer_shape_not_box_shrink_only():
    board = chess.Board("1k6/7R/2K5/8/8/8/8/8 w - - 2 2")
    blackboard = {
        "successor_role_license_enabled": True,
        "successor_role_scoped_move_shape_enabled": True,
        "successor_role_scoped_move_shape_bonus": 0.05,
        "krk_successor_provider_licenses": {
            "krk.edge_trap_close": {
                "krk.edge_rook_transfer_recovery": {
                    "score": 1.0,
                    "role_id": "krk.edge_rook_transfer_recovery",
                    "provider_skill_ids": ["krk.edge_trap_close"],
                    "source_terms": ["edge_rook_transfer_recovery_available", "rook_safe"],
                    "missing_required_terms": [],
                    "veto_terms": [],
                    "contract_met": True,
                }
            }
        },
    }
    box_shrink_only_meta = {}
    far_lateral_meta = {}
    edge_rank_meta = {}

    box_shrink_only = _apply_visible_rook_transfer_move_bias(
        0.0,
        board=board,
        move=chess.Move.from_uci("h7c7"),
        skill_id="krk.edge_trap_close",
        blackboard=blackboard,
        move_meta=box_shrink_only_meta,
    )
    far_lateral = _apply_visible_rook_transfer_move_bias(
        0.0,
        board=board,
        move=chess.Move.from_uci("h7e7"),
        skill_id="krk.edge_trap_close",
        blackboard=blackboard,
        move_meta=far_lateral_meta,
    )
    edge_rank = _apply_visible_rook_transfer_move_bias(
        0.0,
        board=board,
        move=chess.Move.from_uci("h7h1"),
        skill_id="krk.edge_trap_close",
        blackboard=blackboard,
        move_meta=edge_rank_meta,
    )

    assert box_shrink_only == 0.0
    assert "visible_role_scoped_move_shape_bonus" not in box_shrink_only_meta
    assert far_lateral > box_shrink_only
    far_source_terms = far_lateral_meta["visible_role_scoped_move_shape_licenses"][0]["source_terms"]
    assert "rook_destination_not_adjacent_enemy" in far_source_terms
    assert "box_area_decreases_after_move" in far_source_terms
    assert edge_rank > box_shrink_only
    assert edge_rank_meta["visible_role_scoped_move_shape_bonus"] > 0.0
    source_terms = edge_rank_meta["visible_role_scoped_move_shape_licenses"][0]["source_terms"]
    assert "rook_to_edge_rank" in source_terms or "rook_transfer_vertical" in source_terms


def test_visible_role_veto_can_suppress_provider_when_visible_alternative_exists():
    move_meta = {}
    adjusted = _apply_successor_affordance_bias(
        5.7,
        skill_id="krk.stage0_basin",
        curriculum_label="stage0_basin",
        blackboard={
            "successor_role_license_enabled": True,
            "successor_role_veto_penalty": 10.0,
            "krk_successor_provider_licenses": {
                "krk.stage0_basin": {
                    "krk.stage0_king_approach_after_fence": {
                        "score": 0.0,
                        "role_id": "krk.stage0_king_approach_after_fence",
                        "provider_skill_ids": ["krk.stage0_basin"],
                        "source_terms": ["rook_safe"],
                        "missing_required_terms": [],
                        "veto_terms": ["edge_trap_shape_available"],
                        "contract_met": False,
                    }
                },
                "krk.edge_trap_close": {
                    "krk.rook_transfer_after_fence": {
                        "score": 1.0,
                        "role_id": "krk.rook_transfer_after_fence",
                        "provider_skill_ids": ["krk.edge_trap_close"],
                        "source_terms": ["rook_transfer_after_fence_available"],
                        "missing_required_terms": [],
                        "veto_terms": [],
                        "contract_met": True,
                    }
                },
            },
        },
        move_meta=move_meta,
    )

    assert adjusted < 0.0
    assert move_meta["visible_role_veto_penalty"] == 10.0
    assert move_meta["visible_role_vetoes"][0]["veto_terms"] == ["edge_trap_shape_available"]


def test_stage0_drift_penalty_targets_unproductive_king_drift_only():
    board = chess.Board("1k6/7R/2K5/8/8/8/8/8 w - - 2 2")
    blackboard = {
        "successor_role_license_enabled": True,
        "successor_stage0_drift_penalty": 6.0,
        "krk_visible_terms": {
            "edge_trap_close_geometry": True,
            "edge_trap_shape_available": True,
            "fence_stable": True,
            "rook_safe": True,
        },
        "krk_successor_provider_licenses": {
            "krk.edge_trap_close": {
                "krk.edge_trap_close_recovery": {
                    "score": 1.0,
                    "role_id": "krk.edge_trap_close_recovery",
                    "provider_skill_ids": ["krk.edge_trap_close"],
                    "source_terms": ["edge_trap_close_geometry", "rook_safe"],
                    "missing_required_terms": [],
                    "veto_terms": [],
                    "contract_met": True,
                }
            }
        },
    }
    king_meta = {}
    rook_meta = {}

    king_score = _apply_visible_stage0_drift_penalty(
        5.7,
        board=board,
        move=chess.Move.from_uci("c6b6"),
        skill_id="krk.stage0_basin",
        blackboard=blackboard,
        move_meta=king_meta,
    )
    rook_score = _apply_visible_stage0_drift_penalty(
        5.7,
        board=board,
        move=chess.Move.from_uci("h7b7"),
        skill_id="krk.stage0_basin",
        blackboard=blackboard,
        move_meta=rook_meta,
    )

    assert king_score < 0.0
    assert king_meta["visible_stage0_drift_penalty"] == 6.0
    assert rook_score == 5.7
    assert "visible_stage0_drift_penalty" not in rook_meta


def test_move_shape_audit_emits_current_candidate_post_and_worst_reply_terms():
    board = chess.Board("5k2/7R/1K6/8/8/8/8/8 w - - 2 2")
    audit = krk_move_shape_audit(board, chess.Move.from_uci("h7h1"))

    assert audit["legal"] is True
    assert "post_fence_conversion_needed" in audit["current_terms"]
    assert "candidate_is_rook_transfer" in audit["move_shape_terms"]
    assert "rook_transfer_vertical" in audit["move_shape_terms"]
    assert "rook_safe_after_move" in audit["post_move_terms"]
    assert "enemy_edge_distance_not_increased_after_move" in audit["post_move_terms"]
    assert "rook_safe_after_worst_reply" in audit["worst_reply_terms"]
