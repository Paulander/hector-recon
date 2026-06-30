import chess

from recon_lite_chess.autogrowth.terminal_substrate import (
    TerminalAffordanceLearner,
    terminal_action_feature_keys,
)
from recon_lite_chess.autogrowth.validated_basin_acceptance import (
    ValidatedBasinAcceptanceConfig,
    _classify_validated_blocker,
    _decision,
    _validate_foundation_response_at_white_turn,
    _validate_mate1_response,
    _validate_mate2_response,
)


def _learner_for_move(board: chess.Board, move: chess.Move) -> TerminalAffordanceLearner:
    learner = TerminalAffordanceLearner.create(eta_m3=0.08)
    for key, _scale in terminal_action_feature_keys(
        board,
        move,
        hub=learner.hub,
        feature_cache=learner.feature_cache,
    ):
        terminal = learner.get_terminal(key)
        terminal.local_weight = 1.0
    return learner


def _first(*, graph_all: bool = False, graph_partial: bool = False, valid_all: bool = False, valid_partial: bool = False) -> dict:
    return {
        "graph_positive_all_reply_handoff": graph_all,
        "graph_positive_partial_handoff": graph_partial,
        "validated_all_reply_handoff": valid_all,
        "validated_partial_handoff": valid_partial,
    }


def test_tg47h_positive_graph_weight_alone_is_not_validated_basin() -> None:
    board = chess.Board("8/8/8/8/8/8/4R3/4K1k1 w - - 0 1")
    nonmate = next(move for move in board.legal_moves if not _validate_mate1_response(board, move))
    parent = {
        "mate1": _learner_for_move(board, nonmate),
        "mate2_first": TerminalAffordanceLearner.create(eta_m3=0.08),
    }

    detail = _validate_foundation_response_at_white_turn(board, parent)

    assert detail["graph_positive_response"] is True
    assert detail["validator_confirmed_response"] is False
    assert detail["validator_failure_reason"] in {
        "mate1_selected_move_not_checkmate",
        "graph_positive_not_validator_confirmed",
    }


def test_tg47h_mate1_response_requires_actual_checkmate() -> None:
    board = chess.Board("8/8/8/8/8/8/4R3/4K1k1 w - - 0 1")
    nonmate = next(move for move in board.legal_moves if not board.gives_check(move))

    assert _validate_mate1_response(board, nonmate) is False


def test_tg47h_mate2_response_requires_all_reply_validation() -> None:
    board = chess.Board("8/8/8/8/8/8/4R3/4K1k1 w - - 0 1")
    first = next(iter(board.legal_moves))
    parent = {
        "mate1": TerminalAffordanceLearner.create(eta_m3=0.08),
        "mate2_first": TerminalAffordanceLearner.create(eta_m3=0.08),
    }

    assert _validate_mate2_response(board, first, parent) is False


def test_tg47h_partial_only_support_is_not_handoff() -> None:
    blocker = _classify_validated_blocker(
        family="fence_hold_progress",
        selected=_first(valid_partial=True),
        oracle=_first(),
    )

    assert blocker == "validated_partial_only_support"


def test_tg47h_decoy_graph_positive_response_is_quarantined() -> None:
    blocker = _classify_validated_blocker(
        family="decoy_edge",
        selected=_first(graph_all=True),
        oracle=_first(),
    )

    assert blocker == "graph_positive_decoy_false_basin_quarantined"


def test_tg47h_decision_reports_quarantine_purity_and_mutation_invariants() -> None:
    audit_rows = [
        {
            "family": "decoy_edge",
            "selected_first_validated_audit": _first(graph_all=True),
            "oracle_first_validated_audit": _first(),
            "graph_positive_decoy_all_reply_false_handoff": True,
            "graph_positive_decoy_partial_false_handoff": False,
            "validated_decoy_all_reply_false_handoff": False,
            "validated_decoy_partial_false_handoff": False,
            "validated_blocker_classification": "graph_positive_decoy_false_basin_quarantined",
        }
    ]
    quarantine_rows = [
        {
            "family": "decoy_edge",
            "active_tg46d_terminal_keys": ["action_pattern:black_reply_mobility_after=0"],
        }
    ]

    decision = _decision(
        config=ValidatedBasinAcceptanceConfig(),
        parent_hash="parent-hash",
        parent_before={"pass": True},
        parent_after={"pass": True},
        audit_rows=audit_rows,
        quarantine_rows=quarantine_rows,
        parent_weight_delta=0,
        edge_weight_delta=0,
        total_seconds=0.1,
    )

    assert decision["checkpoint_interpretation"] == "graph_positive_basin_overgeneralization_quarantined"
    assert decision["selected_next_action"] == "rerun_tg47g_reachability_with_validated_basin"
    assert decision["false_basin_activation_count"] == 1
    assert decision["parent_foundation_weight_delta_during_audit"] == 0
    assert decision["edge_learner_weight_delta_during_audit"] == 0
    assert decision["runtime_tablebase_or_dtm_move_source"] is False
    assert decision["action_ranker_used_for_runtime"] is False
    assert decision["python_final_selector_used"] is False
    assert decision["direct_provider_override"] is False
    assert decision["learner_visible_basin_labels"] is False


def test_tg47h_validated_decoy_partial_support_selects_decoy_leak() -> None:
    audit_rows = [
        {
            "family": "hard_decoy_edge",
            "selected_first_validated_audit": _first(valid_partial=True),
            "oracle_first_validated_audit": _first(),
            "graph_positive_decoy_all_reply_false_handoff": False,
            "graph_positive_decoy_partial_false_handoff": False,
            "validated_decoy_all_reply_false_handoff": False,
            "validated_decoy_partial_false_handoff": True,
            "validated_blocker_classification": "validated_decoy_partial_handoff_leak",
        }
    ]

    decision = _decision(
        config=ValidatedBasinAcceptanceConfig(),
        parent_hash="parent-hash",
        parent_before={"pass": True},
        parent_after={"pass": True},
        audit_rows=audit_rows,
        quarantine_rows=[],
        parent_weight_delta=0,
        edge_weight_delta=0,
        total_seconds=0.1,
    )

    assert decision["checkpoint_interpretation"] == "validated_decoy_handoff_leak"
    assert decision["selected_next_action"] == "quarantine_validated_decoy_leak_before_training"
