import json

import chess
import pytest

from recon_lite_chess.autogrowth import (
    FORBIDDEN_LEARNER_TERMS,
    extract_learner_features,
    learner_visible_key_firewall_leaks,
    make_trace_record,
    validate_learner_record,
    validate_learner_visible_keys,
)
from recon_lite_chess.autogrowth.context_gated_curriculum import context_terminal_keys
from recon_lite_chess.autogrowth.fence_boundary_signal import _delta_action_feature_keys
from recon_lite_chess.autogrowth.foundation_curriculum import _action_feature_keys
from recon_lite_chess.autogrowth.single_graph_curriculum import _triplet_keys
from recon_lite_chess.autogrowth.terminal_substrate import terminal_action_feature_keys
from recon_lite_chess.autogrowth.tg48a2_same_side_microstage import _micro_terminal_keys


REMOVE_MARKED_FEATURES = {
    "legal_move_count",
    "black_reply_mobility",
    "is_checkmate",
    "is_stalemate",
    "rook_lateral_escape_available",
    "white_king_controls_escape_band",
}

BK_NEIGHBOR_FEATURES = {
    "bk_neighbor_n_available",
    "bk_neighbor_ne_available",
    "bk_neighbor_e_available",
    "bk_neighbor_se_available",
    "bk_neighbor_s_available",
    "bk_neighbor_sw_available",
    "bk_neighbor_w_available",
    "bk_neighbor_nw_available",
}


def test_learner_features_exclude_forbidden_terms() -> None:
    board = chess.Board("8/8/8/4k3/8/8/8/R3K3 w - - 0 1")

    features = extract_learner_features(board)
    serialized = json.dumps(features, sort_keys=True).lower()

    assert features["side_white_to_move"] == 1.0
    assert features["rook_present"] == 1.0
    for term in FORBIDDEN_LEARNER_TERMS:
        assert term not in serialized


def test_learner_features_are_dieted_to_percepts() -> None:
    features = extract_learner_features(
        chess.Board("8/8/8/4k3/8/8/8/R3K3 w - - 0 1")
    )

    assert BK_NEIGHBOR_FEATURES <= features.keys()
    assert not (REMOVE_MARKED_FEATURES & features.keys()) and not any(
        key.startswith("feature_hub_") for key in features
    )


def test_trace_record_excludes_forbidden_terms() -> None:
    board = chess.Board("8/8/8/4k3/8/8/8/R3K3 w - - 0 1")
    move = chess.Move.from_uci("a1a5")
    assert move in board.legal_moves
    after = board.copy(stack=False)
    after.push(move)

    record = make_trace_record(
        board=board,
        move=move,
        after_board=after,
        outcome="pending",
        ply=0,
    )
    serialized = json.dumps(record, sort_keys=True).lower()

    assert record["action"]["uci"] == "a1a5"
    for term in FORBIDDEN_LEARNER_TERMS:
        assert term not in serialized


def test_validate_learner_record_rejects_forbidden_vocabulary() -> None:
    with pytest.raises(ValueError, match="forbidden"):
        validate_learner_record({"feature": "Stage7_box_shrink_provider"})


def test_learner_key_firewall_rejects_historical_action_leaks() -> None:
    leaks = learner_visible_key_firewall_leaks(
        [
            "action_pattern:gives_check=1",
            "action_pattern:black_reply_mobility_after=3",
            "action_pattern:pair:gives_check:black_reply_mobility_after=1:3",
            "action_pattern:is_stalemate_after=0",
            "before_terminal:direct_file_opposition=1",
            "micro_delta:black_mobility=positive",
            "micro_guard:stalemate_after=0",
        ]
    )

    leaked = {name for names in leaks.values() for name in names}
    assert "black_reply_mobility_after" in leaked
    assert "is_stalemate_after" in leaked
    assert "direct_file_opposition" in leaked
    assert "black_mobility" in leaked
    assert "stalemate_after" in leaked
    validate_learner_visible_keys(["action_pattern:gives_check=1"], builder="test")


def test_all_learner_key_builders_pass_shared_firewall() -> None:
    board = chess.Board("8/k4K2/8/8/8/8/1R6/8 w - - 0 1")
    move = next(iter(sorted(board.legal_moves, key=lambda item: item.uci())))
    after = board.copy(stack=False)
    after.push(move)

    builder_keys = {
        "foundation_action": [f"action_pattern:{key}" for key in _action_feature_keys(board, move)],
        "terminal_action": [key for key, _scale in terminal_action_feature_keys(board, move)],
        "single_graph_triplet": [key for group in _triplet_keys(board, move) for key in group],
        "context_terminal": list(context_terminal_keys(board)),
        "fence_boundary_delta": list(_delta_action_feature_keys(board, move)),
        "tg48a2_micro": [key for key, _scale in _micro_terminal_keys(board, move)],
    }
    builder_keys["trace_record"] = (
        list(make_trace_record(board=board, move=move, after_board=after, outcome="pending", ply=0)["before_features"])
        + list(make_trace_record(board=board, move=move, after_board=after, outcome="pending", ply=0)["after_features"])
    )

    for builder, keys in builder_keys.items():
        assert not learner_visible_key_firewall_leaks(keys), builder
