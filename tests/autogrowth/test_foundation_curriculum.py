import json

import chess

from recon_lite_chess.autogrowth import (
    ActionRanker,
    FoundationCurriculumConfig,
    run_foundation_curriculum,
    validate_learner_record,
)
from recon_lite_chess.autogrowth.foundation_curriculum import (
    _generate_forced_mate_in_two_positions,
    _generate_mate_in_one_positions,
    _mate_moves,
    _forced_mate_in_two_first_moves,
)


def test_tg25_generates_legal_mate_in_one_positions() -> None:
    fens = _generate_mate_in_one_positions(
        count=8,
        seed=11,
        max_attempts=30_000,
    )

    assert len(fens) == 8
    for fen in fens:
        board = chess.Board(fen)
        assert board.turn == chess.WHITE
        assert board.is_valid()
        assert 1 <= len(_mate_moves(board)) <= 3


def test_tg25_generates_verified_forced_mate_in_two_positions() -> None:
    fens = _generate_forced_mate_in_two_positions(
        count=4,
        seed=12,
        max_attempts=40_000,
    )

    assert len(fens) == 4
    for fen in fens:
        board = chess.Board(fen)
        forced = _forced_mate_in_two_first_moves(board)
        assert forced
        assert not _mate_moves(board)


def test_tg25_mate_in_one_training_improves_action_ranker() -> None:
    train = _generate_mate_in_one_positions(count=80, seed=21, max_attempts=80_000)
    heldout = _generate_mate_in_one_positions(
        count=20,
        seed=22,
        excluded=set(train),
        max_attempts=80_000,
    )
    untrained = ActionRanker.create(eta_m3=0.10)
    trained = ActionRanker.create(eta_m3=0.10)

    before = 0
    after = 0
    for fen in heldout:
        board = chess.Board(fen)
        move = untrained.choose(board)
        before += int(move is not None and move.uci() in {item.uci() for item in _mate_moves(board)})
    for fen in train:
        board = chess.Board(fen)
        trained.train_position(board, positive_moves={item.uci() for item in _mate_moves(board)})
    for fen in heldout:
        board = chess.Board(fen)
        move = trained.choose(board)
        after += int(move is not None and move.uci() in {item.uci() for item in _mate_moves(board)})

    assert trained.m3_update_count > 0
    assert after > before
    assert after / len(heldout) >= 0.80
    validate_learner_record(trained.to_dict()["top_nodes"])


def test_tg25_foundation_artifact_keeps_curriculum_out_of_learner_records(tmp_path) -> None:
    result = run_foundation_curriculum(
        config=FoundationCurriculumConfig(
            seed=31,
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
    output = result.write_json(tmp_path / "tg25_foundation.json")
    payload = json.loads(output.read_text(encoding="utf-8"))

    assert payload["schema_version"] == "krk_autogrowth_tg25_foundation_curriculum.v0"
    assert payload["training_runway"]["uses_curriculum_as_experience_distribution"] is True
    assert payload["training_runway"]["curriculum_labels_learner_visible"] is False
    assert payload["training_runway"]["runtime_tablebase_or_dtm_move_source"] is False
    assert payload["training_runway"]["direct_provider_override"] is False
    assert payload["local_recon_structure"]["move_choice_mediated_by_local_action_nodes"] is True
    assert payload["mate1"]["heldout"]["accuracy"] >= 0.80
    assert payload["mate1"]["m3_update_count"] > 0
    assert payload["mate1"]["m4_consolidation_event_count"] in (0, 1)
    assert payload["decision"]["curriculum_labels_learner_visible"] is False
    validate_learner_record(payload["mate1_ranker"]["top_nodes"])
    if payload["mate2_first_ranker"] is not None:
        validate_learner_record(payload["mate2_first_ranker"]["top_nodes"])
