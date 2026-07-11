from __future__ import annotations

from collections import Counter

import chess
import pytest

from recon_lite import LinkType

from recon_lite_hector.learning import (
    IntrinsicCreditConfig,
    IntrinsicCreditEngine,
    Responsibility,
)
from recon_lite_chess.autogrowth.native_intrinsic_curriculum import (
    R0_BALANCED_STRATA,
    R0_COMPETENCE_ID,
    R1_BALANCED_STRATA,
    R1_RETIRED_DEVELOPMENT_FENS,
    _balanced_r0_quotas,
    _balanced_r1_quotas,
    _build_r0_replay_memory,
    _choose_with_child_priority,
    _classify_r0_stratum,
    _classify_r1_stratum,
    _execute_white_and_observe,
    _generate_balanced_r0_split,
    _generate_balanced_r1_split,
    _r0_available,
    _r0_available_with_dispatch_cache,
    _r1_orbit_key,
    _replay_r0,
)
from recon_lite_chess.autogrowth.foundation_curriculum import (
    _forced_mate_in_two_first_moves,
    _mate_moves,
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
            score_hierarchy_edge_weights=True,
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


def test_balanced_r1_quotas_cover_all_setup_and_orientation_strata() -> None:
    quotas = _balanced_r1_quotas(16)

    assert tuple(quotas) == R1_BALANCED_STRATA
    assert sum(quotas.values()) == 16
    assert all(
        quotas[f"rook_barrier:{side}"] == 2
        for side in ("left", "right", "bottom", "top")
    )
    assert all(
        quotas[f"king_edge:{side}"] == 1
        for side in ("left", "right", "bottom", "top")
    )
    assert all(
        quotas[f"king_corner:{corner}"] == 1
        for corner in ("a1", "a8", "h1", "h8")
    )
    with pytest.raises(ValueError):
        _balanced_r1_quotas(12)


def test_balanced_r0_splits_cover_all_locations_and_are_orbit_disjoint() -> None:
    used_fens: set[str] = set()
    used_orbits: set[str] = set()
    train, train_labels = _generate_balanced_r0_split(
        count=16,
        seed=20260719,
        used_fens=used_fens,
        used_orbits=used_orbits,
        max_attempts=300_000,
    )
    heldout, heldout_labels = _generate_balanced_r0_split(
        count=8,
        seed=20260720,
        used_fens=used_fens,
        used_orbits=used_orbits,
        max_attempts=300_000,
    )

    assert tuple(_balanced_r0_quotas(8)) == R0_BALANCED_STRATA
    assert Counter(train_labels) == Counter(_balanced_r0_quotas(16))
    assert Counter(heldout_labels) == Counter(_balanced_r0_quotas(8))
    generated_orbits = [_r1_orbit_key(fen) for fen in (*train, *heldout)]
    assert len(generated_orbits) == len(set(generated_orbits))
    for fen, label in zip(
        (*train, *heldout), (*train_labels, *heldout_labels), strict=True
    ):
        board = chess.Board(fen)
        assert _mate_moves(board)
        assert _classify_r0_stratum(board) == label
    with pytest.raises(ValueError):
        _balanced_r0_quotas(12)


def test_balanced_r1_splits_are_stratified_and_orbit_disjoint() -> None:
    used_fens: set[str] = set()
    retired_orbits = {_r1_orbit_key(fen) for fen in R1_RETIRED_DEVELOPMENT_FENS}
    used_orbits = set(retired_orbits)

    train, train_labels = _generate_balanced_r1_split(
        count=16,
        seed=20260718,
        used_fens=used_fens,
        used_orbits=used_orbits,
        max_attempts=300_000,
    )
    heldout, heldout_labels = _generate_balanced_r1_split(
        count=16,
        seed=20260719,
        used_fens=used_fens,
        used_orbits=used_orbits,
        max_attempts=300_000,
    )

    assert Counter(train_labels) == Counter(_balanced_r1_quotas(16))
    assert Counter(heldout_labels) == Counter(_balanced_r1_quotas(16))
    assert set(train).isdisjoint(heldout)
    generated_orbits = [_r1_orbit_key(fen) for fen in (*train, *heldout)]
    assert len(generated_orbits) == len(set(generated_orbits))
    assert not retired_orbits.intersection(generated_orbits)

    for fen, label in zip((*train, *heldout), (*train_labels, *heldout_labels), strict=True):
        board = chess.Board(fen)
        forced = tuple(_forced_mate_in_two_first_moves(board))
        assert forced
        assert _classify_r1_stratum(board, forced) == label


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
    assert any(
        row["move"] != mating_move.uci() and row["score"] > 0.0
        for row in rows
    )


def test_hierarchy_score_uses_current_triplet_edge_for_shared_atom() -> None:
    graph = _graph()
    board = chess.Board(MATE_ONE_FEN)
    first_move, second_move = list(board.legal_moves)[:2]
    first_id = graph.ensure_triplet(board, first_move, stage="shared_parent_test")
    second_id = graph.ensure_triplet(board, second_move, stage="shared_parent_test")
    roles = {
        "before_feature",
        "delta_feature",
        "after_feature",
        "projection_feature",
    }
    shared_ids = [
        node_id
        for node_id in graph.triplet_nodes[first_id] & graph.triplet_nodes[second_id]
        if graph.graph.nodes[node_id].meta.get("role") in roles
    ]
    assert shared_ids

    def parent_id(triplet_id: str, role: str) -> str:
        suffix = {
            "before_feature": "before_script",
            "delta_feature": "action_script",
            "projection_feature": "action_script",
            "after_feature": "after_script",
        }[role]
        return f"{triplet_id}_{suffix}"

    for node_id in graph.triplet_nodes[second_id]:
        node = graph.graph.nodes[node_id]
        role = str(node.meta.get("role", ""))
        node.meta["local_weight"] = 0.0
        if role in roles:
            edge = graph.graph.get_edge(parent_id(second_id, role), node_id, LinkType.SUB)
            assert edge is not None
            edge.w = 0.0
    shared_id = shared_ids[0]
    role = str(graph.graph.nodes[shared_id].meta["role"])
    first_edge = graph.graph.get_edge(parent_id(first_id, role), shared_id, LinkType.SUB)
    second_edge = graph.graph.get_edge(parent_id(second_id, role), shared_id, LinkType.SUB)
    assert first_edge is not None and second_edge is not None
    first_edge.w = 1.0
    second_edge.w = -1.0

    confirmation = graph.confirm_candidate(
        board, triplet_id=second_id, move_uci=second_move.uci()
    )
    assert confirmation["selected_move"] == second_move.uci()
    score, _ = graph._confirmed_terminal_score(second_id)
    assert score == pytest.approx(-1.0)


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
