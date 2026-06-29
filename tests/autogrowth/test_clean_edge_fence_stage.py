from recon_lite_chess.autogrowth.clean_edge_fence_stage import (
    CleanEdgeFenceStageConfig,
    _collect_failure_pool_rows,
    _combine_m3_plus_m4,
    _is_veto_terminal_key,
    _promote_edge_fence,
    _purity_boundary,
    _score_components,
    _stage_success,
)
import chess
from recon_lite_chess.autogrowth.terminal_substrate import TerminalAffordanceLearner


def _terminal(learner: TerminalAffordanceLearner, key: str, *, weight: float, positive: int, negative: int) -> None:
    terminal = learner.get_terminal(key)
    terminal.local_weight = weight
    terminal.positive_credit = positive
    terminal.negative_credit = negative


def test_tg47_m4_promotes_repeated_affordance_and_explicit_veto_only() -> None:
    learner = TerminalAffordanceLearner.create(eta_m3=0.08)
    _terminal(
        learner,
        "action_pattern:pair:gives_check:black_reply_mobility_after=1:3",
        weight=0.80,
        positive=20,
        negative=4,
    )
    _terminal(
        learner,
        "action_pattern:black_reply_mobility_after=0",
        weight=0.20,
        positive=1,
        negative=0,
    )
    _terminal(
        learner,
        "action_pattern:rook_attacked_after=1",
        weight=-0.90,
        positive=2,
        negative=20,
    )
    _terminal(
        learner,
        "before_terminal:rook_present=1",
        weight=-1.10,
        positive=2,
        negative=20,
    )

    terminal_audit = {
        "action_pattern:pair:gives_check:black_reply_mobility_after=1:3": {
            "family_audit": {"edge_trap_progress": {"support": 8, "success": 7, "failure": 1, "precision": 0.875}},
            "decoy_activation_count": 0,
            "hard_decoy_activation_count": 0,
            "unsafe_activation_count": 0,
            "decoy_false_handoff_activation_count": 0,
            "hard_decoy_false_handoff_activation_count": 0,
        }
    }
    promoted, audit = _promote_edge_fence(
        learner,
        CleanEdgeFenceStageConfig(m4_precision_threshold=0.58, m4_min_positive_support=12, m4_min_negative_support=12),
        terminal_audit=terminal_audit,
    )

    promoted_keys = set(promoted.terminals)
    assert "action_pattern:pair:gives_check:black_reply_mobility_after=1:3" in promoted_keys
    assert "action_pattern:rook_attacked_after=1" in promoted_keys
    assert "action_pattern:black_reply_mobility_after=0" not in promoted_keys
    assert "before_terminal:rook_present=1" not in promoted_keys

    promoted_as = {row["terminal_key"]: row["promoted_as"] for row in audit["candidate_rows"] if row["promoted"]}
    assert promoted_as["action_pattern:pair:gives_check:black_reply_mobility_after=1:3"] == "affordance"
    assert promoted_as["action_pattern:rook_attacked_after=1"] == "veto"
    assert audit["edge_fence_m4_true_promotion_count"] == audit["edge_fence_m4_promoted_terminal_count"]
    assert audit["edge_fence_m4_true_promotion_count"] == 2
    assert audit["edge_fence_m4_promoted_veto_terminal_count"] == 1
    assert audit["edge_fence_m4_promoted_affordance_terminal_count"] == 1


def test_tg47_veto_terminal_key_is_explicit_not_broad_safety_context() -> None:
    assert _is_veto_terminal_key("action_pattern:rook_attacked_after=1")
    assert _is_veto_terminal_key("delta_terminal:confinement_area=positive")
    assert not _is_veto_terminal_key("action_pattern:rook_attacked_after=0")
    assert not _is_veto_terminal_key("before_terminal:rook_present=1")


def test_tg47b_combined_m3_m4_arm_is_not_m3_alias() -> None:
    m3 = TerminalAffordanceLearner.create(eta_m3=0.08)
    m4 = TerminalAffordanceLearner.create(eta_m3=0.08)
    _terminal(m3, "action_pattern:rank_delta_magnitude=1", weight=0.2, positive=12, negative=1)
    _terminal(m4, "action_pattern:rook_attacked_after=1", weight=-0.9, positive=1, negative=12)

    combined = _combine_m3_plus_m4(edge_learner=m3, m4_learner=m4)

    assert combined is not m3
    assert set(combined.terminals) == {
        "action_pattern:rank_delta_magnitude=1",
        "action_pattern:rook_attacked_after=1",
    }


def test_tg47b_decoy_partial_handoff_is_failure() -> None:
    metrics = {
        "illegal": False,
        "rook_risk": False,
        "rook_missing": False,
        "stalemate": False,
        "confinement_regressed": False,
        "all_reply_handoff": False,
        "partial_reply_handoff": True,
        "rook_safe": True,
        "confinement_improved": True,
        "black_mobility_reduced": True,
        "edge_progress": False,
        "low_progress": False,
    }

    assert _stage_success(metrics, "decoy_edge") is False


def test_tg47b_rook_risk_fails_even_with_progress() -> None:
    metrics = {
        "illegal": False,
        "rook_risk": True,
        "rook_missing": False,
        "stalemate": False,
        "confinement_regressed": False,
        "all_reply_handoff": True,
        "partial_reply_handoff": False,
        "rook_safe": False,
        "confinement_improved": True,
        "black_mobility_reduced": True,
        "edge_progress": True,
        "low_progress": False,
    }

    assert _stage_success(metrics, "edge_trap_progress") is False


def test_tg47b_m4_blocks_broad_positive_with_unsafe_or_decoy_activation() -> None:
    learner = TerminalAffordanceLearner.create(eta_m3=0.08)
    _terminal(learner, "action_pattern:gives_check=1", weight=1.0, positive=40, negative=1)
    audit = {
        "action_pattern:gives_check=1": {
            "family_audit": {"edge_trap_progress": {"support": 10, "success": 9, "failure": 1, "precision": 0.9}},
            "decoy_activation_count": 2,
            "hard_decoy_activation_count": 0,
            "unsafe_activation_count": 1,
            "decoy_false_handoff_activation_count": 1,
            "hard_decoy_false_handoff_activation_count": 0,
        }
    }

    promoted, result = _promote_edge_fence(learner, CleanEdgeFenceStageConfig(), terminal_audit=audit)

    assert "action_pattern:gives_check=1" not in promoted.terminals
    row = next(item for item in result["candidate_rows"] if item["terminal_key"] == "action_pattern:gives_check=1")
    assert row["broad_standalone_affordance"] is True
    assert row["promoted"] is False


def test_tg47b_failure_pool_includes_decoy_and_unsafe_failures() -> None:
    unsafe = {
        "trace_type": "M4_consolidated_only",
        "index": 0,
        "fen": "8/8/8/8/8/8/8/K6k w - - 0 1",
        "family": "fence_hold_progress",
        "selected": "a1a2",
        "success": False,
        "metrics": {
            "rook_risk": True,
            "rook_missing": False,
            "stalemate": False,
            "illegal": False,
            "confinement_regressed": False,
            "all_reply_handoff": False,
            "partial_reply_handoff": False,
        },
    }
    decoy = {
        **unsafe,
        "trace_type": "decoy_eval",
        "index": 1,
        "family": "decoy_edge",
        "metrics": {**unsafe["metrics"], "rook_risk": False, "partial_reply_handoff": True},
    }
    empty = {"rows": []}
    rows = _collect_failure_pool_rows(
        parent_only=empty,
        m3_only=empty,
        m4_only={"rows": [unsafe]},
        m3_plus_m4=empty,
        regression_m4=empty,
        decoy_eval={"rows": [decoy]},
    )

    assert any(row["family"] == "fence_hold_progress" for row in rows)
    assert any(row["family"] == "decoy_edge" for row in rows)


def test_tg47b_parent_and_purity_invariants_point_to_clean_tg46d() -> None:
    cfg = CleanEdgeFenceStageConfig()
    purity = _purity_boundary()

    assert cfg.parent_foundation_artifact_path.endswith("tg46d_m4_foundation_consolidation/promoted_tg46d_foundation.json")
    assert purity["runtime_tablebase_or_dtm_move_source"] is False
    assert purity["action_ranker_used_for_runtime"] is False
    assert purity["python_final_selector_used"] is False
    assert purity["direct_provider_override"] is False


def test_tg47c_derived_veto_dominates_unsafe_successor_score() -> None:
    board = chess.Board("8/7K/8/8/6k1/8/5R2/8 w - - 0 1")
    learner = TerminalAffordanceLearner.create(eta_m3=0.08)
    unsafe = chess.Move.from_uci("f2f4")
    safe = chess.Move.from_uci("f2f6")

    unsafe_score = _score_components(board, unsafe, parent=None, edge_learner=learner)
    safe_score = _score_components(board, safe, parent=None, edge_learner=learner)

    assert "derived_veto_terminal:rook_capturable_by_reply=1" in unsafe_score["active_veto_terminal_keys"]
    assert unsafe_score["final_score"] < safe_score["final_score"]
