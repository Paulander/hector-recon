import json

import chess

from recon_lite_chess.autogrowth import (
    KRKPositionSet,
    SandboxConfig,
    evaluate_candidate_sandbox,
    evaluate_sandbox_arm,
    extract_learner_features,
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
        "candidate_key": "test_m5_sandbox_candidate",
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


def test_m5_sandbox_candidate_can_change_behavior_without_illegal_move() -> None:
    fen = "8/6k1/8/8/2K5/8/2R5/8 w - - 0 1"
    board = chess.Board(fen)
    candidate = _candidate_for_board(
        board,
        {
            "piece_type": 4,
            "file_delta_sign": -1,
            "rank_delta_sign": 0,
            "file_delta_magnitude": 2,
            "rank_delta_magnitude": 0,
            "gives_check": 0,
            "is_capture": 0,
        },
    )

    metrics, outcomes = evaluate_sandbox_arm(
        [fen],
        candidate=candidate,
        horizon=4,
        activation_max_distance=0.0,
    )

    assert outcomes[0]["outcome"] == "horizon_no_mate"
    assert metrics.candidate_terminal_activations == 1
    assert metrics.candidate_action_matches == 1
    assert metrics.candidate_move_count == 1
    assert metrics.candidate_changed_move_count == 1
    assert metrics.candidate_activated_position_count == 1
    assert metrics.candidate_behavior_changed_position_count == 1
    assert metrics.m3_update_count == 1
    assert metrics.negative_credit_count + metrics.positive_credit_count == 1
    assert metrics.illegal_moves == 0
    assert metrics.stalemates == 0
    assert metrics.rook_losses == 0


def test_m5_sandbox_result_counts_regressions_and_writes_artifact(tmp_path) -> None:
    fen = "8/6k1/8/8/2K5/8/2R5/8 w - - 0 1"
    board = chess.Board(fen)
    candidate = _candidate_for_board(
        board,
        {
            "piece_type": 4,
            "file_delta_sign": -1,
            "rank_delta_sign": 0,
            "file_delta_magnitude": 2,
            "rank_delta_magnitude": 0,
            "gives_check": 0,
            "is_capture": 0,
        },
    )
    positions = KRKPositionSet(seed=1, train=(), heldout_weakness=(fen,), heldout_broader=())
    result = evaluate_candidate_sandbox(
        config=SandboxConfig(
            seed=1,
            train_count=0,
            heldout_weakness_count=1,
            heldout_broader_count=0,
            horizons=(4,),
            candidate_path="unused",
            activation_max_distance=0.0,
        ),
        positions=positions,
        candidate=candidate,
    )
    output = result.write_json(tmp_path / "sandbox.json")
    payload = json.loads(output.read_text(encoding="utf-8"))

    assert payload["schema_version"] == "krk_autogrowth_m5_sandbox.v0"
    assert payload["candidate"]["status"] == "m5_spawned_sandbox_only"
    assert payload["candidate"]["candidate_active_in_sandbox"] is True
    assert payload["candidate"]["candidate_active_in_runtime"] is False
    assert payload["decision"]["candidate_promoted"] is False
    assert payload["decision"]["status"] == "candidate_quarantined_after_sandbox"
    assert payload["decision"]["m3_update_count"] == 1
    assert payload["decision"]["m4_event_count"] == 0
    assert payload["decision"]["deleted_candidate_count"] == 1
    assert payload["learning_decisions"]["4"]["decision"] == "quarantine"
    assert payload["learning_decisions"]["4"]["m3_update_count"] == 1
    assert payload["learning_decisions"]["4"]["m4_consolidation_event_count"] == 0
    assert "no_heldout_conversion_gain" in payload["learning_decisions"]["4"]["reasons"]
    assert payload["arms"]["autogrowth_sandbox"]["4"]["candidate_behavior_changed_position_count"] == 1
    assert payload["safety"]["4"]["illegal_regression_count"] == 0
    assert payload["safety"]["4"]["stalemate_regression_count"] == 0
    assert payload["safety"]["4"]["blunder_regression_count"] == 0
