import json

import chess

from recon_lite_chess.autogrowth import (
    TerminalAffordanceLearner,
    TerminalSubstrateConfig,
    extract_terminal_feature_vector,
    run_terminal_substrate_revival,
    terminal_action_feature_keys,
    validate_learner_record,
)
from recon_lite_chess.autogrowth.foundation_curriculum import (
    _generate_mate_in_one_positions,
    _mate_moves,
)


def test_tg26h_terminal_feature_vector_bridges_feature_hub_and_firewall() -> None:
    fen = _generate_mate_in_one_positions(count=1, seed=2601, max_attempts=30_000)[0]
    board = chess.Board(fen)
    features = extract_terminal_feature_vector(board)
    move = _mate_moves(board)[0]
    action_keys = [key for key, _scale in terminal_action_feature_keys(board, move)]

    assert "feature_hub_opposition_status" in features
    assert "king_file_delta" in features
    assert "direct_file_opposition" in features
    assert "confinement_area" in features
    assert any(key.startswith("action_pattern:") for key in action_keys)
    assert any(key.startswith("before_terminal:feature_hub_opposition_status") for key in action_keys)
    assert any(key.startswith("delta_terminal:black_king_nearest_edge_distance") for key in action_keys)
    assert not any("is_checkmate_after" in key for key in action_keys)
    validate_learner_record(features)
    validate_learner_record(action_keys)


def test_tg26h_terminal_mate_in_one_training_improves_without_action_ranker_choose() -> None:
    train = _generate_mate_in_one_positions(count=80, seed=2602, max_attempts=80_000)
    heldout = _generate_mate_in_one_positions(
        count=20,
        seed=2603,
        excluded=set(train),
        max_attempts=80_000,
    )
    learner = TerminalAffordanceLearner.create(eta_m3=0.10, rich_feature_credit_scale=0.25)

    before = 0
    after = 0
    for fen in heldout:
        board = chess.Board(fen)
        move = learner.choose(board)
        before += int(move is not None and move.uci() in {item.uci() for item in _mate_moves(board)})
    for fen in train:
        board = chess.Board(fen)
        learner.train_position(board, positive_moves={item.uci() for item in _mate_moves(board)})
    for fen in heldout:
        board = chess.Board(fen)
        move = learner.choose(board)
        after += int(move is not None and move.uci() in {item.uci() for item in _mate_moves(board)})

    assert learner.m3_update_count > 0
    assert len(learner.terminals) > 0
    assert after > before
    assert after / len(heldout) >= 0.80
    payload = learner.to_dict(max_terminals=4)
    assert payload["terminal_count"] > 0
    validate_learner_record(payload["top_positive_terminals"])


def test_tg26h_terminal_substrate_artifact_contract(tmp_path) -> None:
    result = run_terminal_substrate_revival(
        config=TerminalSubstrateConfig(
            seed=2604,
            mate1_train_count=60,
            mate1_heldout_count=20,
            mate1_mirror_count=8,
            mate2_train_count=4,
            mate2_heldout_count=2,
            max_generation_attempts=120_000,
            mate1_pass_threshold=0.80,
            mate2_pass_threshold=0.50,
            max_samples=2,
        )
    )
    output = result.write_json(tmp_path / "tg26h.json")
    payload = json.loads(output.read_text(encoding="utf-8"))

    assert payload["schema_version"] == "krk_autogrowth_tg26h_terminal_substrate_revival.v0"
    assert payload["local_recon_structure"]["behavior_choice_mediated_by_terminal_activations"] is True
    assert payload["local_recon_structure"]["action_ranker_status"] == "diagnostic_baseline_scaffolding"
    assert payload["training_runway"]["schedule_labels_learner_visible"] is False
    assert payload["training_runway"]["runtime_tablebase_or_dtm_move_source"] is False
    assert payload["training_runway"]["direct_provider_override"] is False
    assert payload["terminal_native"]["mate1"]["heldout"]["accuracy"] >= 0.80
    assert payload["terminal_native"]["mate1"]["m3_update_count"] > 0
    assert payload["terminal_native"]["terminal_substrate"]["terminal_count"] > 0
    assert payload["decision"]["action_ranker_claim_status"] == "diagnostic_baseline_only"
    assert payload["decision"]["direct_provider_override"] is False
    validate_learner_record(payload["terminal_native"]["terminal_substrate"]["top_positive_terminals"])
