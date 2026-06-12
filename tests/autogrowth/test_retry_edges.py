import json

import chess

from recon_lite_hector.nodes.stem_cell import StemCellState, StemCellTerminal

from recon_lite_chess.autogrowth import (
    KRKPositionSet,
    RetryEdgeConfig,
    choose_continuation_retry_action,
    extract_learner_features,
    run_retry_edge_experiment,
)


def _signed_bucket(value: int) -> int:
    if value > 0:
        return 1
    if value < 0:
        return -1
    return 0


def _magnitude_bucket(value: int) -> int:
    return min(3, abs(int(value)))


def _action_schema(board: chess.Board, move: chess.Move) -> dict[str, int]:
    piece = board.piece_at(move.from_square)
    file_delta = chess.square_file(move.to_square) - chess.square_file(move.from_square)
    rank_delta = chess.square_rank(move.to_square) - chess.square_rank(move.from_square)
    return {
        "piece_type": 0 if piece is None else int(piece.piece_type),
        "file_delta_sign": _signed_bucket(file_delta),
        "rank_delta_sign": _signed_bucket(rank_delta),
        "file_delta_magnitude": _magnitude_bucket(file_delta),
        "rank_delta_magnitude": _magnitude_bucket(rank_delta),
        "gives_check": int(board.gives_check(move)),
        "is_capture": int(board.is_capture(move)),
    }


def _script_node(
    board: chess.Board,
    *,
    key: str,
    first: chess.Move,
    second: chess.Move,
    weight: float,
    rank: int,
) -> dict:
    features = extract_learner_features(board)
    cell = StemCellTerminal(f"script_{key}")
    cell.state = StemCellState.TRIAL
    cell.trial_node_id = f"TRIAL_{cell.cell_id}"
    cell.trial_parent_id = "tg21_retry_edge_test_parent"
    cell.xp = cell.XP_INITIAL
    candidate = {
        "candidate_key": key,
        "rank": rank,
        "before_cluster": {"feature_names": sorted(features), "prototype": features},
        "script_plan": {
            "node_type": "SCRIPT",
            "actions": [_action_schema(board, first), _action_schema(board, second)],
            "relation_plan": {
                "parent_relation": "SUB",
                "step_relation": "POR",
                "confirmation_relation": "SUR",
                "can_be_inhibited_by": "RET",
                "chooses_move_directly": False,
            },
        },
        "after_cluster": {"feature_names": sorted(features), "prototype": features},
        "evidence": {"mean_candidate_credit": weight},
    }
    return {
        "candidate": candidate,
        "candidate_key": key,
        "rank": rank,
        "cell": cell,
        "local_weight": weight,
        "learner_visible": {"node_type": "SCRIPT", "candidate_key": key, "local_weight": weight},
        "diagnostics": {
            "training_sequences": 0,
            "positive_training_credit": 0,
            "negative_training_credit": 0,
            "neutral_training_credit": 0,
            "m3_fast_weight_delta": 0.0,
        },
    }


def test_tg21_retry_edge_bonus_is_local_to_active_suppressed_context() -> None:
    board = chess.Board("8/k7/8/2K5/8/1R6/8/8 w - - 2 2")
    active = _script_node(
        board,
        key="active",
        first=chess.Move.from_uci("c5b5"),
        second=chess.Move.from_uci("b3b7"),
        weight=5.0,
        rank=1,
    )
    unsupported = _script_node(
        board,
        key="unsupported",
        first=chess.Move.from_uci("c5c6"),
        second=chess.Move.from_uci("c5c6"),
        weight=3.0,
        rank=2,
    )
    supported = _script_node(
        board,
        key="supported",
        first=chess.Move.from_uci("c5d5"),
        second=chess.Move.from_uci("c5d5"),
        weight=1.0,
        rank=3,
    )

    decision = choose_continuation_retry_action(
        board,
        script_nodes=[active, unsupported, supported],
        active_script={"candidate_key": "active"},
        requested_successors=[],
        activation_max_distance=0.0,
        chain_request_bonus=0.75,
        lag_negative_threshold=1,
        update_nodes=False,
        position_counts={},
        retry_edge_weights={"active->supported": 1.0},
        retry_edge_bonus=3.0,
    )

    assert decision["node"]["candidate_key"] == "supported"
    assert decision["move"] == chess.Move.from_uci("c5d5")
    assert decision["retry_counts"]["retry_edge_bonus_hit_count"] == 1
    assert unsupported["diagnostics"].get("lag_negative_training_count", 0) == 0


def test_tg21_retry_edge_experiment_writes_artifact(tmp_path) -> None:
    fen = "8/8/8/8/2K5/6k1/2R5/8 w - - 0 1"
    result = run_retry_edge_experiment(
        config=RetryEdgeConfig(
            seed=1,
            train_count=2,
            heldout_weakness_count=1,
            heldout_broader_count=0,
            min_support=1,
            max_candidates=2,
            horizons=(4,),
            min_sequence_credit=0.01,
            activation_max_distance=1.0,
            after_max_distance=4.0,
            chain_max_distance=4.0,
            max_chain_edges=8,
        ),
        positions=KRKPositionSet(seed=1, train=(fen, fen), heldout_weakness=(fen,), heldout_broader=()),
    )
    output = result.write_json(tmp_path / "tg21_retry_edges.json")
    payload = json.loads(output.read_text(encoding="utf-8"))

    assert payload["schema_version"] == "krk_autogrowth_tg21_retry_edges.v0"
    assert payload["local_recon_structure"]["edge_bonus_applies_only_inside_local_retry"] is True
    assert payload["local_recon_structure"]["direct_move_override"] is False
    assert payload["decision"]["direct_move_override"] is False
    assert "real_fragment_chain_retry_edges" in payload["arms"]
    assert "learned_edge_count" in payload["retry_edges"]
