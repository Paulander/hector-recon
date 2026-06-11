import json

import chess

from recon_lite_chess.autogrowth import (
    KRKPositionSet,
    LocalArbitrationConfig,
    LocalSuppressorConfig,
    arbitrate_local_action,
    build_local_action_nodes,
    derive_local_suppressor,
    extract_learner_features,
    run_local_arbitration_experiment,
    validate_learner_record,
)


def _candidate_for_board(
    board: chess.Board,
    action_schema: dict[str, int],
    *,
    key: str,
    rank: int,
    mean_credit: float,
) -> dict:
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
        "candidate_key": key,
        "rank": rank,
        "selected_for_m5": rank == 1,
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
            "mean_generic_progress_credit": mean_credit,
            "mean_terminal_reward": 0.0,
            "mean_candidate_credit": mean_credit,
            "positive_credit_count": 1 if mean_credit > 0.0 else 0,
            "negative_credit_count": 1 if mean_credit < 0.0 else 0,
            "example_trace_keys": ["test_trace"],
        },
    }


def _fixture_candidates() -> tuple[str, dict, dict]:
    fen = "8/8/8/8/2K5/6k1/2R5/8 w - - 0 1"
    board = chess.Board(fen)
    risky = _candidate_for_board(
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
        key="test_m12_risky_action",
        rank=1,
        mean_credit=1.0,
    )
    safer = _candidate_for_board(
        board,
        {
            "piece_type": 4,
            "file_delta_sign": 0,
            "rank_delta_sign": 1,
            "file_delta_magnitude": 0,
            "rank_delta_magnitude": 1,
            "gives_check": 1,
            "is_capture": 0,
        },
        key="test_m12_safer_action",
        rank=2,
        mean_credit=0.1,
    )
    return fen, risky, safer


def test_local_arbitration_requires_action_nodes() -> None:
    board = chess.Board(_fixture_candidates()[0])

    decision = arbitrate_local_action(
        board,
        action_nodes=[],
        suppressor_model=None,
        activation_max_distance=0.0,
        suppressor_max_distance=0.75,
    )

    assert decision["move"] is None
    assert decision["used_external_move_source"] is False


def test_suppressor_inhibits_only_its_sibling_action() -> None:
    fen, risky, safer = _fixture_candidates()
    _cell, suppressor_model = derive_local_suppressor(
        [fen],
        candidate=risky,
        config=LocalSuppressorConfig(train_count=1, heldout_weakness_count=1, heldout_broader_count=0, horizon=4),
    )
    action_nodes = build_local_action_nodes(
        [],
        candidates=[risky, safer],
        suppressor_model=suppressor_model,
        config=LocalArbitrationConfig(train_count=1, heldout_weakness_count=1, heldout_broader_count=0, horizon=4),
    )
    board = chess.Board(fen)

    unsuppressed = arbitrate_local_action(
        board,
        action_nodes=action_nodes,
        suppressor_model=None,
        activation_max_distance=0.0,
        suppressor_max_distance=0.75,
    )
    suppressed = arbitrate_local_action(
        board,
        action_nodes=action_nodes,
        suppressor_model=suppressor_model,
        activation_max_distance=0.0,
        suppressor_max_distance=0.75,
    )

    assert unsuppressed["selected_candidate_key"] == "test_m12_risky_action"
    assert suppressed["selected_candidate_key"] == "test_m12_safer_action"
    assert suppressed["suppressed_count"] >= 1
    assert suppressed["move"] == chess.Move.from_uci("c2c3")


def test_action_nodes_are_stem_cell_trial_and_firewall_clean() -> None:
    fen, risky, safer = _fixture_candidates()
    _cell, suppressor_model = derive_local_suppressor(
        [fen],
        candidate=risky,
        config=LocalSuppressorConfig(train_count=1, heldout_weakness_count=1, heldout_broader_count=0, horizon=4),
    )
    action_nodes = build_local_action_nodes(
        [fen],
        candidates=[risky, safer],
        suppressor_model=suppressor_model,
        config=LocalArbitrationConfig(train_count=1, heldout_weakness_count=1, heldout_broader_count=0, horizon=4),
    )

    for node in action_nodes:
        assert node["cell"].state.name == "TRIAL"
        assert node["learner_visible"]["node_type"] == "ACTION"
        validate_learner_record(node["learner_visible"])


def test_local_arbitration_result_writes_artifact(tmp_path) -> None:
    fen, risky, safer = _fixture_candidates()
    result = run_local_arbitration_experiment(
        config=LocalArbitrationConfig(
            seed=1,
            train_count=1,
            heldout_weakness_count=1,
            heldout_broader_count=0,
            candidate_path="unused",
            candidate_count=2,
            horizon=4,
            activation_max_distance=0.0,
            suppressor_max_distance=0.75,
        ),
        positions=KRKPositionSet(seed=1, train=(fen,), heldout_weakness=(fen,), heldout_broader=()),
        candidates=[risky, safer],
    )
    output = result.write_json(tmp_path / "local_arbitration.json")
    payload = json.loads(output.read_text(encoding="utf-8"))

    assert payload["schema_version"] == "krk_autogrowth_m12_local_arbitration.v0"
    assert payload["local_recon_structure"]["move_choice_mediated_by_local_action_nodes"] is True
    assert payload["decision"]["direct_move_override"] is False
    assert payload["decision"]["external_move_ranking_applied"] is False
    assert payload["arms"]["local_action_arbitration"]["action_selected_count"] > 0
    assert payload["arms"]["local_action_arbitration"]["suppressed_action_option_count"] > 0
