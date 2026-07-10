from __future__ import annotations

import chess

from recon_lite_hector.learning import (
    IntrinsicCreditConfig,
    IntrinsicCreditEngine,
    Responsibility,
)

from recon_lite_chess.autogrowth.native_intrinsic_curriculum import (
    R0_COMPETENCE_ID,
    _build_r0_replay_memory,
    _execute_white_and_observe,
    _choose_with_child_priority,
    _replay_r0,
    _r0_available,
    _r0_available_with_dispatch_cache,
)
from recon_lite_chess.autogrowth.native_single_graph_curriculum import (
    NativeReConKRKGraph,
    NativeSingleGraphConfig,
)


MATE_ONE_FEN = "k7/8/1K6/8/8/8/8/7R w - - 0 1"


def _graph() -> NativeReConKRKGraph:
    return NativeReConKRKGraph(
        config=NativeSingleGraphConfig(
            include_symmetries=False,
            eta_m3=0.1,
            max_ticks=80,
            key_mode="canonical",
            shared_feature_atoms=True,
            shared_projection_atoms=True,
            include_grouped_cache_terminals=False,
            score_action_pattern_atoms=True,
        )
    )


def test_native_intrinsic_graph_starts_with_empty_learned_state() -> None:
    graph = _graph()
    audit = graph.learned_state_audit()

    assert audit == {
        "node_count": 1,
        "edge_count": 0,
        "triplet_count": 0,
        "trainable_edge_count": 0,
        "nonzero_trainable_edge_count": 0,
        "nonzero_local_weight_node_count": 0,
        "m3_update_count": 0,
        "m4_event_count": 0,
    }


def test_observed_action_td_updates_only_executed_native_branch() -> None:
    graph = _graph()
    board = chess.Board(MATE_ONE_FEN)
    mating_move = next(
        move
        for move in board.legal_moves
        if _execute_white_and_observe(board, move) == "mate"
    )
    triplet_id = graph.ensure_triplet(board, mating_move, stage="R0_test")
    confirmation = graph.confirm_candidate(
        board,
        triplet_id=triplet_id,
        move_uci=mating_move.uci(),
    )
    assert confirmation["selected_move"] == mating_move.uci()

    credit = IntrinsicCreditEngine(
        IntrinsicCreditConfig(
            eta_fast=0.5,
            eta_slow=1.0,
            min_grounding_evidence=1,
        )
    )
    credit.register(R0_COMPETENCE_ID)
    credit.register(triplet_id, hierarchy_depth=1)
    credit.begin_episode()
    event = credit.transition(
        triplet_id,
        responsibilities=(
            Responsibility(triplet_id),
            Responsibility(R0_COMPETENCE_ID, parent_distance=1),
        ),
        terminal_kind="mate",
    )
    graph.apply_intrinsic_td(
        board,
        mating_move,
        td_error=event.td_error,
        stage_diagnostic="R0_test",
    )

    audit = graph.learned_state_audit()
    assert audit["triplet_count"] == 1
    assert audit["m3_update_count"] > 0
    assert audit["nonzero_trainable_edge_count"] > 0
    assert credit.states[R0_COMPETENCE_ID].terminal_evidence == 1


def test_nonmating_action_receives_only_metabolic_td_not_teacher_failure() -> None:
    board = chess.Board(MATE_ONE_FEN)
    nonmating = next(
        move
        for move in board.legal_moves
        if _execute_white_and_observe(board, move) is None
    )
    assert _execute_white_and_observe(board, nonmating) is None

    credit = IntrinsicCreditEngine(
        IntrinsicCreditConfig(real_move_cost=0.02, eta_fast=0.5)
    )
    credit.register("observed_action")
    event = credit.transition("observed_action", terminal_kind=None)

    assert event.immediate_reward == -0.02
    assert event.successor_value == 0.0
    assert event.terminal_kind is None
    assert credit.states["observed_action"].terminal_evidence == 0


def test_shared_triplet_is_evaluated_for_each_overlapping_current_move() -> None:
    graph = _graph()
    board = chess.Board(MATE_ONE_FEN)
    mating_move = next(
        move
        for move in board.legal_moves
        if _execute_white_and_observe(board, move) == "mate"
    )
    triplet_id = graph.apply_intrinsic_td(
        board,
        mating_move,
        td_error=1.0,
        stage_diagnostic="R0_pair_mapping_test",
    )

    audit = graph.audit_choice(board)
    rows = [
        row
        for row in audit["confirmed_candidates"]
        if row["triplet_id"] == triplet_id
    ]

    assert audit["candidate_triplet_count"] > audit["unique_candidate_triplet_count"]
    assert len({row["move"] for row in rows}) > 1


def test_virtual_frame_availability_uses_child_move_without_grounding() -> None:
    graph = _graph()
    board = chess.Board(MATE_ONE_FEN)
    mating_move = next(
        move
        for move in board.legal_moves
        if _execute_white_and_observe(board, move) == "mate"
    )
    graph.apply_intrinsic_td(
        board,
        mating_move,
        td_error=1.0,
        stage_diagnostic="R0_virtual_frame_test",
    )

    available, response = _r0_available(
        graph,
        None,
        board,
        mode="virtual_frame_verified",
    )

    assert available is True
    assert response["selected_move"] == mating_move.uci()
    assert response["availability_source"] == "mature_child_selected_virtual_frame"
    assert response["virtual_frame_terminal_grounding_granted"] is False

    graph.freeze_existing_parameters(reason="R0_test_consolidation")
    cache: dict[str, dict[str, object]] = {}
    first_available, _first_response, first_hit, first_mismatch = (
        _r0_available_with_dispatch_cache(
            graph,
            None,
            board,
            mode="virtual_frame_verified",
            allowed_triplets=frozenset(graph.triplet_ids),
            cache=cache,
            enabled=True,
        )
    )
    second_available, second_response, second_hit, second_mismatch = (
        _r0_available_with_dispatch_cache(
            graph,
            None,
            board,
            mode="virtual_frame_verified",
            allowed_triplets=frozenset(graph.triplet_ids),
            cache=cache,
            enabled=True,
        )
    )
    assert (first_available, first_hit, first_mismatch) == (True, False, False)
    assert (second_available, second_hit, second_mismatch) == (True, True, False)
    assert second_response["availability_source"] == "live_confirmed_frozen_child_dispatch_memory"
    hierarchical = _choose_with_child_priority(
        graph,
        board,
        r0_child_triplet_ids=frozenset(graph.triplet_ids),
    )
    assert hierarchical == mating_move


def test_r0_replay_uses_graph_selected_action_and_real_outcome() -> None:
    graph = _graph()
    board = chess.Board(MATE_ONE_FEN)
    mating_move = next(
        move
        for move in board.legal_moves
        if _execute_white_and_observe(board, move) == "mate"
    )
    graph.apply_intrinsic_td(
        board,
        mating_move,
        td_error=1.0,
        stage_diagnostic="R0_replay_setup",
    )
    credit = IntrinsicCreditEngine(
        IntrinsicCreditConfig(
            eta_fast=0.5,
            min_grounding_evidence=1,
        )
    )
    credit.register(R0_COMPETENCE_ID)
    before_updates = graph.m3_update_count

    replay = _replay_r0(
        graph,
        credit,
        (MATE_ONE_FEN,),
        epoch=0,
        count=1,
    )

    assert replay["episodes"] == 1
    assert replay["observed_mates"] == 1
    assert replay["observed_nonmates"] == 0
    assert replay["formal_confirmation_failures"] == 0
    assert replay["cached_outcome_mismatches"] == 0
    assert graph.m3_update_count > before_updates
    assert credit.states[R0_COMPETENCE_ID].terminal_evidence == 1


def test_cached_r0_replay_is_graph_memory_live_confirmed_and_reexecuted() -> None:
    graph = _graph()
    board = chess.Board(MATE_ONE_FEN)
    mating_move = next(
        move
        for move in board.legal_moves
        if _execute_white_and_observe(board, move) == "mate"
    )
    for _ in range(8):
        graph.apply_intrinsic_td(
            board,
            mating_move,
            td_error=1.0,
            stage_diagnostic="R0_cached_replay_setup",
        )
    memory, audit = _build_r0_replay_memory(graph, (MATE_ONE_FEN,))
    assert audit["teacher_solution_labels_consumed"] == 0
    assert audit["experience_count"] == 1
    assert memory[0].move_uci == mating_move.uci()
    assert memory[0].observed_terminal == "mate"

    credit = IntrinsicCreditEngine(
        IntrinsicCreditConfig(eta_fast=0.5, min_grounding_evidence=1)
    )
    credit.register(R0_COMPETENCE_ID)
    replay = _replay_r0(
        graph,
        credit,
        (MATE_ONE_FEN,),
        epoch=0,
        count=1,
        memory=memory,
    )

    assert replay["episodes"] == 1
    assert replay["observed_mates"] == 1
    assert replay["formal_confirmation_failures"] == 0
    assert replay["cached_outcome_mismatches"] == 0
