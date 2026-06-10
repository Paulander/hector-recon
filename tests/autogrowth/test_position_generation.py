import chess

from recon_lite_chess.autogrowth import can_mate_in_one, generate_position_sets, is_valid_krk_seed


def test_position_generation_is_deterministic_and_disjoint() -> None:
    first = generate_position_sets(
        seed=1234,
        train_count=8,
        heldout_weakness_count=4,
        heldout_broader_count=4,
    )
    second = generate_position_sets(
        seed=1234,
        train_count=8,
        heldout_weakness_count=4,
        heldout_broader_count=4,
    )

    assert first == second
    assert first.digest() == second.digest()
    all_fens = [*first.train, *first.heldout]
    assert len(all_fens) == len(set(all_fens))


def test_position_generation_outputs_valid_non_mate_in_one_krk() -> None:
    positions = generate_position_sets(
        seed=99,
        train_count=6,
        heldout_weakness_count=3,
        heldout_broader_count=3,
    )

    for fen in [*positions.train, *positions.heldout]:
        board = chess.Board(fen)
        assert is_valid_krk_seed(board)
        assert board.turn == chess.WHITE
        assert not board.is_stalemate()
        assert not board.is_checkmate()
        assert not can_mate_in_one(board)


def test_weakness_split_is_nontrivial_without_stage_labels() -> None:
    positions = generate_position_sets(
        seed=7,
        train_count=2,
        heldout_weakness_count=5,
        heldout_broader_count=1,
    )

    for fen in positions.heldout_weakness:
        board = chess.Board(fen)
        black_king = board.king(chess.BLACK)
        white_king = board.king(chess.WHITE)
        assert black_king is not None
        assert white_king is not None
        black_file = chess.square_file(black_king)
        black_rank = chess.square_rank(black_king)
        edge_distance = min(black_file, 7 - black_file, black_rank, 7 - black_rank)
        king_distance = max(
            abs(chess.square_file(white_king) - black_file),
            abs(chess.square_rank(white_king) - black_rank),
        )
        assert edge_distance >= 1
        assert king_distance >= 2
        assert "Stage7" not in fen
        assert "box_shrink" not in fen
