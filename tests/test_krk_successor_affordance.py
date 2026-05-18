#!/usr/bin/env python3
"""Tests for visible KRK successor-affordance nodes."""

import sys
from pathlib import Path

import chess

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from recon_lite_chess.krk_baseline_nodes import (
    _apply_explicit_support_move_shape_bias,
    _apply_successor_affordance_bias,
    _apply_visible_post_break_continuation_bias,
    _apply_visible_stage0_drift_penalty,
    _apply_visible_rook_transfer_move_bias,
    _apply_visible_stagnation_breaker_bias,
    _compute_krk_context_terms,
    _provider_role_licenses,
    _stage7_drive_repair_move_audit,
    _stage7_king_tempo_move_audit,
    _stage7_post_box_continuation_move_audit,
    _stage7_post_king_tempo_move_audit,
    create_krk_context_terminal,
    create_krk_role_provider_support_adapter,
    create_krk_stage7_drive_repair_terminal,
    create_krk_stage7_king_tempo_terminal,
    create_krk_stage7_post_box_continuation_terminal,
    create_krk_stage7_post_king_tempo_terminal,
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


def test_role_provider_support_adapter_records_explicit_support_only_when_enabled():
    env = {
        "blackboard": {
            "explicit_role_provider_support_enabled": True,
            "krk_successor_provider_licenses": {
                "krk.drive_to_edge": {
                    "krk.box_shrink_to_drive_repair": {
                        "contract_met": True,
                        "source_terms": ["box_shrink_drive_repair_available"],
                    },
                },
            },
        },
    }
    adapter = create_krk_role_provider_support_adapter(
        "script.krk.support.box_shrink_to_drive_repair_to_drive_to_edge"
    )
    adapter.meta.update({
        "role_id": "krk.box_shrink_to_drive_repair",
        "provider_skill_id": "krk.drive_to_edge",
        "support_weight": 0.25,
    })

    success, done = adapter.predicate(adapter, env)

    assert success is True
    assert done is True
    support = env["blackboard"]["krk_explicit_role_provider_supports"]["krk.drive_to_edge"][
        "krk.box_shrink_to_drive_repair"
    ]
    assert support["score"] == 0.25
    assert support["source_terms"] == ["box_shrink_drive_repair_available"]


def test_role_provider_support_adapter_can_use_role_payload_without_provider_augmentation():
    env = {
        "blackboard": {
            "explicit_role_provider_support_enabled": True,
            "krk_successor_provider_licenses": {
                "krk.drive_to_edge": {
                    "krk.box_shrink_to_drive_repair": {
                        "contract_met": True,
                        "source_terms": ["box_shrink_drive_repair_available"],
                    },
                },
            },
            "krk_successor_role_affordances": {
                "krk.box_shrink_to_drive_repair": {
                    "contract_met": True,
                    "source_terms": ["box_shrink_drive_repair_available"],
                }
            },
        },
    }
    adapter = create_krk_role_provider_support_adapter(
        "script.krk.support.box_shrink_to_drive_repair_to_fence"
    )
    adapter.meta.update({
        "role_id": "krk.box_shrink_to_drive_repair",
        "provider_skill_id": "krk.fence_established",
        "support_weight": 0.25,
    })

    success, done = adapter.predicate(adapter, env)

    assert success is True
    assert done is True
    assert "krk.fence_established" not in env["blackboard"]["krk_successor_provider_licenses"]
    support = env["blackboard"]["krk_explicit_role_provider_supports"]["krk.fence_established"][
        "krk.box_shrink_to_drive_repair"
    ]
    assert support["score"] == 0.25
    assert support["direct_request"] is False


def test_role_provider_support_adapter_is_inert_when_disabled():
    env = {
        "blackboard": {
            "explicit_role_provider_support_enabled": False,
            "krk_successor_provider_licenses": {
                "krk.drive_to_edge": {
                    "krk.box_shrink_to_drive_repair": {"contract_met": True},
                },
            },
        },
    }
    adapter = create_krk_role_provider_support_adapter("script.krk.support.disabled")
    adapter.meta.update({
        "role_id": "krk.box_shrink_to_drive_repair",
        "provider_skill_id": "krk.drive_to_edge",
        "support_weight": 0.25,
    })

    success, done = adapter.predicate(adapter, env)

    assert success is False
    assert done is True
    assert "krk_explicit_role_provider_supports" not in env["blackboard"]


def test_role_provider_support_adapter_respects_support_required_terms():
    env = {
        "blackboard": {
            "explicit_role_provider_support_enabled": True,
            "krk_visible_terms": {"white_king_support_available": False},
            "krk_successor_provider_licenses": {
                "krk.edge_trap_close": {
                    "krk.edge_rook_transfer_recovery": {
                        "contract_met": True,
                        "source_terms": ["edge_rook_transfer_recovery_available"],
                    },
                },
            },
        },
    }
    adapter = create_krk_role_provider_support_adapter("script.krk.support.edge")
    adapter.meta.update({
        "role_id": "krk.edge_rook_transfer_recovery",
        "provider_skill_id": "krk.edge_trap_close",
        "support_weight": 0.25,
        "support_required_terms": ["white_king_support_available"],
    })

    success, done = adapter.predicate(adapter, env)

    assert success is False
    assert done is True
    assert "krk_explicit_role_provider_supports" not in env["blackboard"]
    blocked = adapter.meta["last_explicit_role_provider_support_blocked"]
    assert blocked["missing_support_required_terms"] == ["white_king_support_available"]
    assert blocked["direct_request"] is False

    env["blackboard"]["krk_visible_terms"]["white_king_support_available"] = True
    success, done = adapter.predicate(adapter, env)

    assert success is True
    assert done is True
    support = env["blackboard"]["krk_explicit_role_provider_supports"]["krk.edge_trap_close"][
        "krk.edge_rook_transfer_recovery"
    ]
    assert support["score"] == 0.25


def test_move_shape_gated_explicit_support_only_boosts_matching_move():
    board = chess.Board("8/8/8/8/4R3/2k5/4K3/8 w - - 2 2")
    support = {
        "role_id": "krk.box_shrink_to_drive_repair",
        "provider_skill_id": "krk.drive_to_edge",
        "score": 0.25,
        "source_terms": ["box_shrink_drive_repair_available"],
        "role_contract_met": True,
        "adapter_node": "script.krk.support.drive",
        "direct_request": False,
        "support_move_shape_required_terms": [
            "candidate_is_rook_transfer",
            "rook_lateral_transfer",
        ],
        "support_post_move_required_terms": ["rook_safe_after_move"],
    }
    blackboard = {
        "explicit_role_provider_support_enabled": True,
        "krk_explicit_role_provider_supports": {
            "krk.drive_to_edge": {
                "krk.box_shrink_to_drive_repair": support,
            }
        },
    }

    matching_meta = {}
    matching_score = _apply_explicit_support_move_shape_bias(
        1.0,
        board=board,
        move=chess.Move.from_uci("e4h4"),
        skill_id="krk.drive_to_edge",
        blackboard=blackboard,
        move_meta=matching_meta,
    )

    assert matching_score == 1.25
    assert matching_meta["visible_role_provider_support_adapter"]["move_shape_gated"] is True
    assert "rook_lateral_transfer" in matching_meta[
        "visible_role_provider_support_adapter"
    ]["matched_move_shape_terms"]

    nonmatching_meta = {}
    nonmatching_score = _apply_explicit_support_move_shape_bias(
        1.0,
        board=board,
        move=chess.Move.from_uci("e2e3"),
        skill_id="krk.drive_to_edge",
        blackboard=blackboard,
        move_meta=nonmatching_meta,
    )

    assert nonmatching_score == 1.0
    assert "visible_role_provider_support_adapter" not in nonmatching_meta


def test_stage7_king_tempo_terminal_is_default_off_and_selects_visible_quiet_tempo():
    board = chess.Board("6k1/R7/8/8/8/8/5K2/8 w - - 2 2")
    node = create_krk_stage7_king_tempo_terminal("terminal.krk.stage7_king_tempo")

    env = {"board": board, "blackboard": {}}
    success, done = node.predicate(node, env)

    assert success is False
    assert done is True
    assert "actuator_suggestions" not in env

    env = {
        "board": board,
        "blackboard": {
            "stage7_king_tempo_enabled": True,
            "stage7_king_tempo_score": 25.0,
        },
    }
    success, done = node.predicate(node, env)

    assert success is True
    assert done is True
    suggestion = env["actuator_suggestions"][0]
    assert suggestion["move"].uci() == "f2e2"
    assert suggestion["curriculum_label"] == "stage7_king_tempo"
    license_payload = suggestion["meta"]["visible_stage7_king_tempo_license"]
    assert license_payload["direct_request"] is False
    assert "king_quiet_tempo_not_toward_enemy" in license_payload["source_terms"]
    assert "compact_box_area_before_move" in license_payload["source_terms"]
    audit = suggestion["meta"]["visible_move_shape_audit"]
    assert audit["current_box_area"] == 7
    assert audit["veto_terms"] == []


def test_stage7_king_tempo_terminal_blocks_large_box_toward_rook_move():
    board = chess.Board("6k1/8/8/8/R7/8/4K3/8 w - - 2 2")
    node = create_krk_stage7_king_tempo_terminal("terminal.krk.stage7_king_tempo")
    env = {
        "board": board,
        "blackboard": {
            "stage7_king_tempo_enabled": True,
            "stage7_king_tempo_score": 25.0,
        },
    }

    success, done = node.predicate(node, env)

    assert success is False
    assert done is True
    assert "actuator_suggestions" not in env
    audit = _stage7_king_tempo_move_audit(board, chess.Move.from_uci("e2d2"))
    assert audit["stage7_king_tempo_candidate"] is False
    assert "box_area_large_before_move" in audit["veto_terms"]
    assert "king_moves_toward_rook_support" in audit["veto_terms"]


def test_explicit_role_provider_support_augments_visible_role_score_only_when_enabled():
    blackboard = {
        "explicit_role_provider_support_enabled": True,
        "krk_successor_provider_licenses": {
            "krk.drive_to_edge": {
                "krk.box_shrink_to_drive_repair": {
                    "role_id": "krk.box_shrink_to_drive_repair",
                    "contract_met": True,
                    "score": 1.0,
                },
            },
        },
        "krk_explicit_role_provider_supports": {
            "krk.drive_to_edge": {
                "krk.box_shrink_to_drive_repair": {
                    "role_contract_met": True,
                    "score": 0.25,
                },
            },
        },
    }

    licenses = _provider_role_licenses("krk.drive_to_edge", blackboard)

    assert licenses[0]["score"] == 1.25
    assert licenses[0]["explicit_role_provider_support_score"] == 0.25

    blackboard["explicit_role_provider_support_enabled"] = False
    licenses = _provider_role_licenses("krk.drive_to_edge", blackboard)
    assert licenses[0]["score"] == 1.0
    assert "explicit_role_provider_support_score" not in licenses[0]


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


def test_box_shrink_drive_repair_context_exposes_visible_terms():
    board = chess.Board("8/8/8/8/7R/2k5/4K3/8 w - - 2 2")
    terms = _compute_krk_context_terms(board)

    assert terms["box_shrink_drive_repair_available"] is True
    assert terms["fence_or_cut_not_preserved"] is True
    assert terms["drive_to_edge_affordance_after_box_shrink"] is True
    assert terms["repair_or_reestablish_cut_available"] is True
    assert terms["rook_safe"] is True
    assert terms["enemy_king_not_at_edge"] is True


def test_box_shrink_drive_repair_role_licenses_drive_to_edge_provider():
    env = {
        "board": chess.Board("8/8/8/8/7R/2k5/4K3/8 w - - 2 2"),
        "blackboard": {"successor_affordance_layer_enabled": True},
    }
    for term in [
        "box_shrink_drive_repair_available",
        "fence_or_cut_not_preserved",
        "drive_to_edge_affordance_after_box_shrink",
        "repair_or_reestablish_cut_available",
        "enemy_king_not_at_edge",
        "rook_safe",
    ]:
        node = create_krk_context_terminal(f"terminal.krk.{term}")
        node.meta["term"] = term
        node.predicate(node, env)

    affordance = create_krk_successor_affordance(
        "script.krk.successor.box_shrink_to_drive_repair_affordance"
    )
    affordance.meta.update({
        "successor_skill_id": "krk.box_shrink_to_drive_repair",
        "role_id": "krk.box_shrink_to_drive_repair",
        "provider_skill_ids": ["krk.drive_to_edge"],
        "source_terms": [
            "box_shrink_drive_repair_available",
            "fence_or_cut_not_preserved",
            "drive_to_edge_affordance_after_box_shrink",
            "repair_or_reestablish_cut_available",
            "enemy_king_not_at_edge",
            "rook_safe",
        ],
        "required_terms": [
            "box_shrink_drive_repair_available",
            "enemy_king_not_at_edge",
            "rook_safe",
        ],
        "veto_terms": ["mate_in_one_available"],
    })

    success, done = affordance.predicate(affordance, env)

    payload = env["blackboard"]["krk_successor_role_affordances"]["krk.box_shrink_to_drive_repair"]
    licenses = env["blackboard"]["krk_successor_provider_licenses"]["krk.drive_to_edge"]
    assert success is True
    assert done is True
    assert payload["contract_met"] is True
    assert licenses["krk.box_shrink_to_drive_repair"]["provider_skill_ids"] == ["krk.drive_to_edge"]


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


def test_visible_drive_repair_move_bonus_supports_licensed_king_repair_shape():
    board = chess.Board("8/8/8/8/7R/2k5/4K3/8 w - - 2 2")
    blackboard = {
        "successor_role_license_enabled": True,
        "successor_role_scoped_move_shape_enabled": True,
        "successor_role_scoped_move_shape_bonus": 0.05,
        "krk_successor_provider_licenses": {
            "krk.drive_to_edge": {
                "krk.box_shrink_to_drive_repair": {
                    "score": 1.0,
                    "role_id": "krk.box_shrink_to_drive_repair",
                    "provider_skill_ids": ["krk.drive_to_edge"],
                    "source_terms": [
                        "box_shrink_drive_repair_available",
                        "enemy_king_not_at_edge",
                        "rook_safe",
                    ],
                    "missing_required_terms": [],
                    "veto_terms": [],
                    "contract_met": True,
                }
            }
        },
    }
    move_meta = {}

    adjusted = _apply_visible_rook_transfer_move_bias(
        0.0,
        board=board,
        move=chess.Move.from_uci("e2e3"),
        skill_id="krk.drive_to_edge",
        blackboard=blackboard,
        move_meta=move_meta,
    )

    assert adjusted > 0.0
    assert move_meta["visible_role_scoped_move_shape_bonus"] > 0.0
    licenses = move_meta["visible_role_scoped_move_shape_licenses"]
    assert licenses[0]["role_id"] == "krk.box_shrink_to_drive_repair"
    assert "box_shrink_drive_repair_available" in licenses[0]["source_terms"]
    assert "candidate_is_king_move" in licenses[0]["source_terms"]


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


def test_post_break_continuation_bonus_requires_visible_recent_break_context():
    board = chess.Board("5k2/8/K7/8/7R/8/8/8 w - - 18 10")
    blackboard = {
        "post_break_continuation_enabled": True,
        "post_break_continuation_bonus": 0.25,
        "krk_dynamic_context_terms": {
            "rook_oscillation_loop_recently_broken": True,
            "confinement_preserved_after_break": True,
            "post_stagnation_break_continuation_needed": True,
            "safe_followup_available": True,
        },
        "krk_post_break_continuation_context": {
            "breaker_move": "h4d4",
            "legal_post_break_followup_moves": ["a6a7", "a6b7"],
        },
    }
    licensed_meta = {}
    unlicensed_meta = {}

    licensed = _apply_visible_post_break_continuation_bias(
        1.0,
        board=board,
        move=chess.Move.from_uci("a6b7"),
        skill_id="krk.stage0_basin",
        blackboard=blackboard,
        move_meta=licensed_meta,
    )
    missing_context = _apply_visible_post_break_continuation_bias(
        1.0,
        board=board,
        move=chess.Move.from_uci("a6b7"),
        skill_id="krk.stage0_basin",
        blackboard={
            **blackboard,
            "krk_dynamic_context_terms": {
                "rook_oscillation_loop_recently_broken": True,
                "confinement_preserved_after_break": False,
                "post_stagnation_break_continuation_needed": True,
                "safe_followup_available": True,
            },
        },
        move_meta=unlicensed_meta,
    )

    assert licensed == 1.25
    assert licensed_meta["visible_post_break_continuation_bonus"] == 0.25
    assert licensed_meta["visible_post_break_continuation_license"]["role_id"] == (
        "krk.post_stagnation_break_continuation"
    )
    assert "candidate_is_king_move" in licensed_meta[
        "visible_post_break_continuation_license"
    ]["source_terms"]
    assert missing_context == 1.0
    assert "visible_post_break_continuation_bonus" not in unlicensed_meta


def test_stagnation_breaker_king_support_bonus_is_narrow_and_visible():
    board = chess.Board("5k2/8/8/K7/7R/8/8/8 w - - 18 10")
    blackboard = {
        "stagnation_breaker_enabled": True,
        "stagnation_breaker_bonus": 0.5,
        "stagnation_breaker_king_support_bonus": 2.0,
        "krk_dynamic_context_terms": {
            "rook_oscillation_loop": True,
            "no_box_progress_recently": True,
            "safe_loop_breaking_move_available": True,
        },
        "krk_stagnation_context": {
            "legal_loop_breaking_moves": ["a5b6", "h4f4"],
            "legal_loop_breaking_move_audits": [
                {
                    "move": "a5b6",
                    "source_terms": [
                        "escapes_rook_oscillation_pair",
                        "not_immediate_rook_reverse",
                        "rook_safe_after_move",
                        "no_draw_after_move",
                        "box_area_not_increased_after_move",
                        "enemy_edge_distance_not_increased_after_move",
                    ],
                },
                {
                    "move": "h4f4",
                    "source_terms": [
                        "escapes_rook_oscillation_pair",
                        "not_immediate_rook_reverse",
                        "rook_safe_after_move",
                        "no_draw_after_move",
                        "box_area_not_increased_after_move",
                        "enemy_edge_distance_not_increased_after_move",
                    ],
                },
            ],
        },
    }
    king_meta = {}
    rook_meta = {}

    king_score = _apply_visible_stagnation_breaker_bias(
        1.0,
        board=board,
        move=chess.Move.from_uci("a5b6"),
        skill_id="krk.stage0_basin",
        blackboard=blackboard,
        move_meta=king_meta,
    )
    rook_score = _apply_visible_stagnation_breaker_bias(
        1.0,
        board=board,
        move=chess.Move.from_uci("h4f4"),
        skill_id="krk.edge_trap_close",
        blackboard=blackboard,
        move_meta=rook_meta,
    )

    assert king_score == 3.5
    assert rook_score == 1.5
    assert king_meta["visible_stagnation_breaker_bonus"] == 2.5
    assert king_meta["visible_stagnation_breaker_king_support_bonus"] == 2.0
    assert king_meta["visible_stagnation_breaker_king_support_license"]["role_id"] == (
        "krk.stagnation_breaker_king_support"
    )
    assert "visible_stagnation_breaker_king_support_bonus" not in rook_meta


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


def test_stage7_post_king_tempo_audit_selects_failed_family_converter():
    board = chess.Board("4k3/R7/8/8/8/8/5K2/8 w - - 4 3")

    converter = _stage7_post_king_tempo_move_audit(board, chess.Move.from_uci("a7c7"))
    runtime_bad = _stage7_post_king_tempo_move_audit(board, chess.Move.from_uci("f2g3"))
    drawish = _stage7_post_king_tempo_move_audit(board, chess.Move.from_uci("a7d7"))

    assert converter["stage7_post_king_tempo_candidate"] is True
    assert converter["box_shrink_lateral_followup"] is True
    assert "post_box_area_equals_5" in converter["source_terms"]
    assert runtime_bad["stage7_post_king_tempo_candidate"] is False
    assert drawish["stage7_post_king_tempo_candidate"] is False


def test_stage7_drive_repair_audit_selects_visible_broken_fence_repair():
    board = chess.Board("8/8/8/8/7R/2k5/4K3/8 w - - 2 2")

    checking_repair = _stage7_drive_repair_move_audit(board, chess.Move.from_uci("h4h3"))
    quiet_king = _stage7_drive_repair_move_audit(board, chess.Move.from_uci("e2e3"))

    assert checking_repair["stage7_drive_repair_candidate"] is True
    assert checking_repair["safe_check_or_cut_repair"] is True
    assert "box_shrink_drive_repair_available" in checking_repair["source_terms"]
    assert "rook_safe_after_worst_reply" in checking_repair["source_terms"]
    assert quiet_king["stage7_drive_repair_candidate"] is True
    assert quiet_king["king_support_repair"] is True
    assert "king_support_repair" in quiet_king["source_terms"]


def test_stage7_drive_repair_terminal_is_opt_in_and_scoped():
    node = create_krk_stage7_drive_repair_terminal()
    board = chess.Board("8/8/8/8/7R/2k5/4K3/8 w - - 2 2")
    disabled_env = {"board": board, "blackboard": {"stage7_drive_repair_enabled": False}}
    wrong_scope_env = {
        "board": board,
        "blackboard": {
            "stage7_drive_repair_enabled": True,
            "active_landmark_label": "fence_established",
            "stage7_provider_scope_label": "box_shrink",
        },
    }
    enabled_env = {
        "board": board,
        "blackboard": {
            "stage7_drive_repair_enabled": True,
            "stage7_drive_repair_post_reply_context": True,
            "stage7_drive_repair_score": 28.0,
            "active_landmark_label": "box_shrink",
        },
    }

    assert node.predicate(node, disabled_env) == (False, True)
    assert node.predicate(node, wrong_scope_env) == (False, True)
    success, done = node.predicate(node, enabled_env)

    assert success is True
    assert done is True
    assert enabled_env["suggested_move"] == "h4e4"
    suggestion = enabled_env["actuator_suggestions"][0]
    assert suggestion["curriculum_label"] == "stage7_drive_repair"
    payload = suggestion["meta"]["visible_stage7_drive_repair_license"]
    assert payload["direct_request"] is False
    assert payload["causal_status"] == "sandbox_opt_in"
    assert "box_area_decreases_after_move" in payload["source_terms"]


def test_stage7_drive_repair_terminal_can_license_initial_visible_box_shrink():
    node = create_krk_stage7_drive_repair_terminal()
    board = chess.Board("8/8/8/8/3k4/8/3K4/R7 w - - 0 1")
    env = {
        "board": board,
        "blackboard": {
            "stage7_drive_repair_enabled": True,
            "stage7_drive_repair_score": 28.0,
            "active_landmark_label": "box_shrink",
        },
    }

    success, done = node.predicate(node, env)

    assert success is True
    assert done is True
    assert env["suggested_move"] == "a1d1"
    suggestion = env["actuator_suggestions"][0]
    payload = suggestion["meta"]["visible_stage7_drive_repair_license"]
    assert payload["direct_request"] is False
    assert "box_area_decreases_after_move" in payload["source_terms"]
    assert "fence_exists_after_move" in payload["source_terms"]


def test_stage7_post_king_tempo_terminal_is_opt_in_and_after_king_tempo_only():
    node = create_krk_stage7_post_king_tempo_terminal()
    board = chess.Board("4k3/R7/8/8/8/8/5K2/8 w - - 4 3")
    disabled_env = {
        "board": board,
        "blackboard": {
            "stage7_post_king_tempo_enabled": False,
            "stage7_king_tempo_already_used": True,
        },
    }
    before_tempo_env = {
        "board": board,
        "blackboard": {
            "stage7_post_king_tempo_enabled": True,
            "stage7_king_tempo_already_used": False,
        },
    }
    wrong_scope_env = {
        "board": board,
        "blackboard": {
            "stage7_post_king_tempo_enabled": True,
            "stage7_king_tempo_already_used": True,
            "active_landmark_label": "edge_trap_wrong_tempo",
            "stage7_provider_scope_label": "box_shrink",
        },
    }
    enabled_env = {
        "board": board,
        "blackboard": {
            "stage7_post_king_tempo_enabled": True,
            "stage7_post_king_tempo_score": 30.0,
            "stage7_king_tempo_already_used": True,
        },
    }

    assert node.predicate(node, disabled_env) == (False, True)
    assert node.predicate(node, before_tempo_env) == (False, True)
    assert node.predicate(node, wrong_scope_env) == (False, True)
    success, done = node.predicate(node, enabled_env)

    assert success is True
    assert done is True
    assert enabled_env["suggested_move"] == "a7c7"
    suggestion = enabled_env["actuator_suggestions"][0]
    assert suggestion["curriculum_label"] == "stage7_post_king_tempo"
    assert suggestion["meta"]["visible_stage7_post_king_tempo_license"]["direct_request"] is False


def test_stage7_post_box_continuation_terminal_is_opt_in_and_post_reply_scoped():
    node = create_krk_stage7_post_box_continuation_terminal()
    board = chess.Board("8/8/8/R7/4k3/8/3K4/8 w - - 2 2")
    disabled_env = {
        "board": board,
        "blackboard": {
            "stage7_post_box_continuation_enabled": False,
            "stage7_post_box_post_reply_context": True,
        },
    }
    before_reply_env = {
        "board": board,
        "blackboard": {
            "stage7_post_box_continuation_enabled": True,
            "stage7_post_box_post_reply_context": False,
        },
    }
    enabled_env = {
        "board": board,
        "blackboard": {
            "stage7_post_box_continuation_enabled": True,
            "stage7_post_box_post_reply_context": True,
            "stage7_post_box_continuation_score": 32.0,
        },
    }

    assert node.predicate(node, disabled_env) == (False, True)
    assert node.predicate(node, before_reply_env) == (False, True)
    success, done = node.predicate(node, enabled_env)

    assert success is True
    assert done is True
    assert enabled_env["suggested_move"] == "d2c3"
    suggestion = enabled_env["actuator_suggestions"][0]
    assert suggestion["curriculum_label"] == "stage7_post_box_continuation"
    payload = suggestion["meta"]["visible_stage7_post_box_continuation_license"]
    assert payload["direct_request"] is False
    assert "dtm_oracle_move_selection" in payload["runtime_forbidden_terms"]


def test_stage7_post_box_continuation_move_audit_has_no_state_hash_or_oracle_terms():
    board = chess.Board("8/8/R7/8/2k5/8/8/3K4 w - - 2 2")
    audit = _stage7_post_box_continuation_move_audit(board, chess.Move.from_uci("a6d6"))

    assert audit["stage7_post_box_continuation_candidate"] is True
    assert "box_area_decreases_after_move" in audit["source_terms"]
    assert "dtm_oracle_move_selection" in audit["runtime_forbidden_terms"]
    assert "state_hash_exception" in audit["runtime_forbidden_terms"]
