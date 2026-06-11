import json

import chess

from recon_lite_hector.nodes.stem_cell import StemCellState, StemCellTerminal

from recon_lite_chess.autogrowth import (
    KRKPositionSet,
    LagTerminalConfig,
    choose_lag_fragment_chain_action,
    evaluate_lag_terminal,
    extract_learner_features,
    run_lag_terminal_experiment,
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


def _script_node_for_move(board: chess.Board, move: chess.Move, *, key: str = "lag_test") -> dict:
    features = extract_learner_features(board)
    schema = _action_schema(board, move)
    cell = StemCellTerminal(f"script_{key}")
    cell.state = StemCellState.TRIAL
    cell.trial_node_id = f"TRIAL_{cell.cell_id}"
    cell.trial_parent_id = "tg19_lag_test_parent"
    cell.xp = cell.XP_INITIAL
    candidate = {
        "candidate_key": key,
        "rank": 1,
        "before_cluster": {"feature_names": sorted(features), "prototype": features},
        "script_plan": {
            "node_type": "SCRIPT",
            "actions": [schema, schema],
            "relation_plan": {
                "parent_relation": "SUB",
                "step_relation": "POR",
                "confirmation_relation": "SUR",
                "can_be_inhibited_by": "RET",
                "chooses_move_directly": False,
            },
        },
        "after_cluster": {"feature_names": sorted(features), "prototype": features},
        "evidence": {"mean_candidate_credit": 0.0},
    }
    return {
        "candidate": candidate,
        "candidate_key": key,
        "rank": 1,
        "cell": cell,
        "local_weight": 0.0,
        "learner_visible": {"node_type": "SCRIPT", "candidate_key": key, "local_weight": 0.0},
        "diagnostics": {
            "training_sequences": 0,
            "positive_training_credit": 0,
            "negative_training_credit": 0,
            "neutral_training_credit": 0,
            "m3_fast_weight_delta": 0.0,
        },
    }


def test_tg19_lag_terminal_detects_rook_threat_next_turn() -> None:
    board = chess.Board("8/8/8/8/2K5/6k1/2R5/8 w - - 0 1")
    risky = chess.Move.from_uci("c2f2")
    safe = chess.Move.from_uci("c2a2")

    risky_lag = evaluate_lag_terminal(board, risky, position_counts={})
    safe_lag = evaluate_lag_terminal(board, safe, position_counts={})

    assert risky_lag["inhibits"] is True
    assert risky_lag["lag_rook_threat_delta_count"] == 1
    assert safe_lag["inhibits"] is False
    assert safe_lag["lag_suppression_count"] == 0


def test_tg19_lag_suppresses_action_without_learning_on_heldout_call() -> None:
    board = chess.Board("8/8/8/8/2K5/6k1/2R5/8 w - - 0 1")
    node = _script_node_for_move(board, chess.Move.from_uci("c2f2"))

    decision = choose_lag_fragment_chain_action(
        board,
        script_nodes=[node],
        active_script=None,
        requested_successors=[],
        activation_max_distance=0.0,
        chain_request_bonus=0.75,
        lag_negative_threshold=1,
        update_nodes=False,
        position_counts={},
    )

    assert decision["move"] is None
    assert decision["lag_counts"]["lag_suppression_count"] == 1
    assert node["diagnostics"].get("lag_negative_training_count", 0) == 0
    assert node["cell"].candidate_stats.credit_stats.negative_intervention == 0


def test_tg19_lag_training_records_local_stem_cell_evidence() -> None:
    board = chess.Board("8/8/8/8/2K5/6k1/2R5/8 w - - 0 1")
    node = _script_node_for_move(board, chess.Move.from_uci("c2f2"))

    decision = choose_lag_fragment_chain_action(
        board,
        script_nodes=[node],
        active_script=None,
        requested_successors=[],
        activation_max_distance=0.0,
        chain_request_bonus=0.75,
        lag_negative_threshold=1,
        update_nodes=True,
        position_counts={},
    )

    assert decision["move"] is None
    assert node["diagnostics"]["lag_negative_training_count"] == 1
    assert node["cell"].candidate_stats.relevance_stats.activation_count == 1
    assert node["cell"].candidate_stats.relevance_stats.sibling_contrast == 1.0
    assert node["cell"].candidate_stats.survival_stats.suppressed_sibling == "c2f2"


def test_tg19_lag_allows_safe_local_action() -> None:
    board = chess.Board("8/8/8/8/2K5/6k1/2R5/8 w - - 0 1")
    node = _script_node_for_move(board, chess.Move.from_uci("c2a2"))

    decision = choose_lag_fragment_chain_action(
        board,
        script_nodes=[node],
        active_script=None,
        requested_successors=[],
        activation_max_distance=0.0,
        chain_request_bonus=0.75,
        lag_negative_threshold=1,
        update_nodes=True,
        position_counts={},
    )

    assert decision["move"] == chess.Move.from_uci("c2a2")
    assert decision["lag_counts"]["lag_suppression_count"] == 0
    assert node["diagnostics"].get("lag_negative_training_count", 0) == 0


def test_tg19_lag_experiment_writes_machine_readable_artifact(tmp_path) -> None:
    fen = "8/8/8/8/2K5/6k1/2R5/8 w - - 0 1"
    result = run_lag_terminal_experiment(
        config=LagTerminalConfig(
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
    output = result.write_json(tmp_path / "tg19_lag.json")
    payload = json.loads(output.read_text(encoding="utf-8"))

    assert payload["schema_version"] == "krk_autogrowth_tg19_lag_terminals.v0"
    assert payload["local_recon_structure"]["lag_node_type"] == "TERMINAL"
    assert payload["local_recon_structure"]["lag_terminal_can_inhibit_candidate_action"] is True
    assert payload["local_recon_structure"]["direct_move_override"] is False
    assert payload["local_recon_structure"]["selector_behavior_enabled"] is False
    assert "real_fragment_chain_no_lag" in payload["arms"]
    assert "real_fragment_chain_lag" in payload["arms"]
    assert payload["decision"]["direct_move_override"] is False
