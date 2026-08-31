from __future__ import annotations

import chess

from recon_lite_chess.autogrowth.native_intrinsic_curriculum import (
    R1_ACTION_ORDER_LEGACY_LEXICOGRAPHIC,
    R1_ACTION_ORDER_STABLE_HASH_PERMUTATION,
    NativeIntrinsicCurriculumConfig,
    _r1_legal_action_order,
    _stable_hash_action_permutation,
)


def test_legacy_r1_action_order_remains_lexicographic_by_default():
    board = chess.Board("8/8/8/8/8/8/R7/K1k5 w - - 0 1")
    expected = tuple(sorted(move.uci() for move in board.legal_moves))

    assert NativeIntrinsicCurriculumConfig().r1_action_order == (
        R1_ACTION_ORDER_LEGACY_LEXICOGRAPHIC
    )
    observed = _r1_legal_action_order(board)
    assert tuple(move.uci() for move in observed) == expected


def test_adaptive_action_order_is_stable_permutation_and_cycles_without_replacement():
    identifiers = ("act-a", "act-b", "act-c", "act-d", "act-e")
    first = _stable_hash_action_permutation(
        identifiers,
        generic_seed=17,
        position_identity="opaque-position-1",
    )
    permuted_input = _stable_hash_action_permutation(
        tuple(reversed(identifiers)),
        generic_seed=17,
        position_identity="opaque-position-1",
    )

    assert first == permuted_input
    assert set(first) == set(identifiers)
    assert len(first) == len(set(first))
    assert [first[index % len(first)] for index in range(len(first) * 2)] == (
        list(first) + list(first)
    )


def test_adaptive_action_order_is_not_uci_lexicographic_for_selected_position():
    board = chess.Board("8/8/8/8/8/8/R7/K1k5 w - - 0 1")
    legacy = tuple(
        move.uci()
        for move in _r1_legal_action_order(
            board,
            action_order=R1_ACTION_ORDER_LEGACY_LEXICOGRAPHIC,
        )
    )
    adaptive = tuple(
        move.uci()
        for move in _r1_legal_action_order(
            board,
            action_order=R1_ACTION_ORDER_STABLE_HASH_PERMUTATION,
            generic_seed=17,
            position_identity="opaque-position-1",
        )
    )

    assert adaptive != legacy
    assert set(adaptive) == set(legacy)
