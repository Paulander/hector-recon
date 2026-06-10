import json

import chess
import pytest

from recon_lite_chess.autogrowth import (
    FORBIDDEN_LEARNER_TERMS,
    extract_learner_features,
    make_trace_record,
    validate_learner_record,
)


def test_learner_features_exclude_forbidden_terms() -> None:
    board = chess.Board("8/8/8/4k3/8/8/8/R3K3 w - - 0 1")

    features = extract_learner_features(board)
    serialized = json.dumps(features, sort_keys=True).lower()

    assert features["side_white_to_move"] == 1.0
    assert features["rook_present"] == 1.0
    for term in FORBIDDEN_LEARNER_TERMS:
        assert term not in serialized


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
