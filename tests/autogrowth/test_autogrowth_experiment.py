import json

import chess

from recon_lite_chess.autogrowth import (
    AutogrowthExperimentConfig,
    KRKPositionSet,
    extract_learner_features,
    run_autogrowth_experiment,
)


def _candidate_artifact(path, board: chess.Board) -> None:
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
    candidate = {
        "candidate_key": "test_v0_candidate",
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
        "action_schema": {
            "piece_type": 4,
            "file_delta_sign": -1,
            "rank_delta_sign": 0,
            "file_delta_magnitude": 2,
            "rank_delta_magnitude": 0,
            "gives_check": 0,
            "is_capture": 0,
        },
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
    payload = {
        "schema_version": "krk_autogrowth_m4_candidates.v0",
        "candidates": [candidate],
    }
    path.write_text(json.dumps(payload), encoding="utf-8")


def test_full_autogrowth_experiment_writes_three_arm_failure_artifact(tmp_path) -> None:
    fen = "8/6k1/8/8/2K5/8/2R5/8 w - - 0 1"
    candidate_path = tmp_path / "candidate.json"
    _candidate_artifact(candidate_path, chess.Board(fen))
    positions = KRKPositionSet(seed=1, train=(), heldout_weakness=(fen,), heldout_broader=())

    result = run_autogrowth_experiment(
        config=AutogrowthExperimentConfig(
            seed=1,
            train_count=0,
            heldout_weakness_count=1,
            heldout_broader_count=0,
            horizons=(40, 80),
            candidate_path=str(candidate_path),
            activation_max_distance=0.0,
        ),
        positions=positions,
    )
    output = result.write_json(tmp_path / "experiment.json")
    payload = json.loads(output.read_text(encoding="utf-8"))

    assert payload["schema_version"] == "krk_autogrowth_v0_experiment.v0"
    assert set(payload["arms"]) == {"baseline", "sham_growth", "autogrowth_sandbox"}
    assert payload["threshold_evaluation"]["passed"] is False
    assert "h40_conversion_plus_10pp" in payload["threshold_evaluation"]["failed_checks"]
    assert payload["decision"]["status"] == "fail_quarantine_candidate"
    assert payload["decision"]["candidate_promoted"] is False
    assert payload["decision"]["candidate_nodes_spawned"] == 1
    assert payload["decision"]["deleted_candidate_count"] == 1
    assert payload["decision"]["m3_update_count"] > 0
    assert payload["decision"]["m4_event_count"] == 0
