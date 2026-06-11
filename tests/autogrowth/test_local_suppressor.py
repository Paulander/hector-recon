import json

import chess

from recon_lite_chess.autogrowth import (
    KRKPositionSet,
    LocalSuppressorConfig,
    derive_local_suppressor,
    evaluate_local_suppressor_arm,
    evaluate_sandbox_arm,
    extract_learner_features,
    run_local_suppressor_experiment,
    suppressor_confirms,
    validate_learner_record,
)


def _candidate_for_board(board: chess.Board, action_schema: dict[str, int]) -> dict:
    features = extract_learner_features(board)
    before_names = [
        "black_king_nearest_edge_distance",
        "white_king_to_black_king_distance",
        "white_rook_to_black_king_distance",
        "white_king_to_rook_distance",
        "rook_attacked_by_black",
        "is_check",
    ]
    after_names = [
        "black_king_nearest_edge_distance",
        "black_reply_mobility",
        "white_king_to_black_king_distance",
        "white_rook_to_black_king_distance",
        "white_king_to_rook_distance",
        "rook_attacked_by_black",
        "is_check",
        "is_stalemate",
    ]
    return {
        "candidate_key": "test_m11_local_sibling",
        "rank": 1,
        "selected_for_m5": True,
        "status": "m4_mined_not_spawned",
        "source_split": "train",
        "behavior_change_applied": False,
        "candidate_active_in_runtime": False,
        "recon_topology_plan": {
            "node_types": ["TERMINAL", "ACTION", "TERMINAL", "SCRIPT"],
            "relation_types": ["SUB", "SUR", "POR", "RET"],
            "spawn_count": 1,
            "spawned_now": False,
            "m3_update_count": 0,
            "m4_event_count": 0,
            "local_parent_id": "test_local_parent",
        },
        "before_cluster": {
            "feature_names": before_names,
            "prototype": {name: features[name] for name in before_names},
        },
        "action_schema": action_schema,
        "after_delta_cluster": {
            "feature_names": after_names,
            "prototype": {name: 0.0 for name in after_names},
        },
        "after_cluster": {
            "feature_names": sorted(features),
            "prototype": features,
        },
        "evidence": {
            "support_count": 1,
            "position_count": 1,
            "mean_generic_progress_credit": 0.0,
            "mean_terminal_reward": 0.0,
            "mean_candidate_credit": 0.0,
            "positive_credit_count": 0,
            "negative_credit_count": 0,
            "example_trace_keys": ["test_trace"],
        },
    }


def _risky_candidate() -> tuple[str, dict]:
    fen = "8/8/8/8/2K5/6k1/2R5/8 w - - 0 1"
    board = chess.Board(fen)
    candidate = _candidate_for_board(
        board,
        {
            "piece_type": 4,
            "file_delta_sign": 1,
            "rank_delta_sign": 0,
            "file_delta_magnitude": 3,
            "rank_delta_magnitude": 0,
            "gives_check": 0,
            "is_capture": 0,
        },
    )
    return fen, candidate


def test_local_suppressor_is_stem_cell_trial_and_firewall_clean() -> None:
    fen, candidate = _risky_candidate()
    cell, model = derive_local_suppressor(
        [fen],
        candidate=candidate,
        config=LocalSuppressorConfig(train_count=1, heldout_weakness_count=1, heldout_broader_count=0, horizon=4),
    )

    assert cell.state.name == "TRIAL"
    assert cell.candidate_survival_decision() == "suppress"
    assert cell.candidate_stats.credit_stats.negative_intervention > 0
    assert model["learner_visible"]["relation_plan"]["chooses_move_directly"] is False
    validate_learner_record(model["learner_visible"])


def test_suppressor_cannot_choose_move_directly() -> None:
    fen, candidate = _risky_candidate()
    _cell, model = derive_local_suppressor(
        [fen],
        candidate=candidate,
        config=LocalSuppressorConfig(train_count=1, heldout_weakness_count=1, heldout_broader_count=0, horizon=4),
    )
    board = chess.Board(fen)
    move = chess.Move.from_uci("c2f2")

    decision = suppressor_confirms(board, move, suppressor_model=model, max_distance=0.75)

    assert isinstance(decision, bool)
    assert decision is True


def test_removing_suppressor_returns_unsuppressed_candidate_behavior() -> None:
    fen, candidate = _risky_candidate()
    _cell, model = derive_local_suppressor(
        [fen],
        candidate=candidate,
        config=LocalSuppressorConfig(train_count=1, heldout_weakness_count=1, heldout_broader_count=0, horizon=4),
    )
    unsuppressed_metrics, unsuppressed_outcomes = evaluate_sandbox_arm(
        [fen],
        candidate=candidate,
        horizon=4,
        activation_max_distance=0.0,
    )
    disabled_metrics, disabled_outcomes = evaluate_local_suppressor_arm(
        [fen],
        candidate=candidate,
        suppressor_model=None,
        horizon=4,
        activation_max_distance=0.0,
        suppressor_max_distance=0.75,
    )
    suppressed_metrics, _suppressed_outcomes = evaluate_local_suppressor_arm(
        [fen],
        candidate=candidate,
        suppressor_model=model,
        horizon=4,
        activation_max_distance=0.0,
        suppressor_max_distance=0.75,
    )

    assert disabled_outcomes[0]["outcome"] == unsuppressed_outcomes[0]["outcome"]
    assert disabled_metrics.candidate_move_count == unsuppressed_metrics.candidate_move_count
    assert disabled_metrics.candidate_changed_move_count == unsuppressed_metrics.candidate_changed_move_count
    assert suppressed_metrics.suppressed_sibling_action_count > 0
    assert suppressed_metrics.candidate_move_count < unsuppressed_metrics.candidate_move_count


def test_local_suppressor_result_writes_artifact(tmp_path) -> None:
    fen, candidate = _risky_candidate()
    result = run_local_suppressor_experiment(
        config=LocalSuppressorConfig(
            seed=1,
            train_count=1,
            heldout_weakness_count=1,
            heldout_broader_count=0,
            candidate_path="unused",
            horizon=4,
            activation_max_distance=0.0,
            suppressor_max_distance=0.75,
        ),
        positions=KRKPositionSet(seed=1, train=(fen,), heldout_weakness=(fen,), heldout_broader=()),
        candidate=candidate,
    )
    output = result.write_json(tmp_path / "local_suppressor.json")
    payload = json.loads(output.read_text(encoding="utf-8"))

    assert payload["schema_version"] == "krk_autogrowth_m11_local_suppressor.v0"
    assert payload["decision"]["behavior_mediated_by_stem_cell_trial_structure"] is True
    assert payload["decision"]["chooses_moves_directly"] is False
    assert payload["arms"]["local_suppressor"]["suppressed_sibling_action_count"] > 0
    assert payload["suppressor"]["cell"]["candidate_stats"]["credit_stats"]["negative_intervention"] > 0
