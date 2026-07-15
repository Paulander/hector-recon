from __future__ import annotations

import copy
from pathlib import Path

import chess

from recon_lite import ChildResponse, FrameContext, FrameKind
from recon_lite_hector.learning import IntrinsicCreditConfig, IntrinsicCreditEngine
from recon_lite_chess.autogrowth.native_authority_handover import (
    ChildQuery,
    FrozenCompetenceProvenance,
    NativeHandoverGenome,
    NativeR0Organism,
    native_authority_tripwires,
    run_dream_firewall_canary,
)
from recon_lite_chess.autogrowth.native_intrinsic_curriculum import R0_COMPETENCE_ID
from recon_lite_chess.autogrowth.native_single_graph_curriculum import (
    NativeReConKRKGraph,
    NativeSingleGraphConfig,
)


MATE_ONE = "8/8/8/8/8/7K/5R2/7k w - - 0 1"


def _tiny_organism() -> NativeR0Organism:
    board = chess.Board(MATE_ONE)
    mating = []
    for move in board.legal_moves:
        successor = board.copy(stack=False)
        successor.push(move)
        if successor.is_checkmate():
            mating.append(move)
    assert mating
    graph = NativeReConKRKGraph(config=NativeSingleGraphConfig(
        include_symmetries=False,
        max_ticks=80,
        indexed_scheduler=True,
        key_mode="canonical",
        shared_feature_atoms=True,
        shared_projection_atoms=True,
        include_grouped_cache_terminals=False,
        score_action_pattern_atoms=True,
        terminal_score_normalization="sqrt",
    ))
    graph.apply_intrinsic_td(board, mating[0], td_error=1.0, stage_diagnostic="retired_test")
    graph.mature_existing_graph()
    graph.freeze_existing_parameters(reason="unit_test")
    credit = IntrinsicCreditEngine(IntrinsicCreditConfig(min_grounding_evidence=3))
    credit.register(R0_COMPETENCE_ID, mature=True)
    state = credit.states[R0_COMPETENCE_ID]
    state.slow_value = 0.8
    state.fast_value = 0.8
    state.terminal_evidence = 3
    state.causal_confirmations = 1
    state.grounding_level = 0
    provenance = FrozenCompetenceProvenance.from_credit(credit, R0_COMPETENCE_ID)
    return NativeR0Organism(
        graph=graph,
        credit=credit,
        provenance=provenance,
        frozen_triplet_ids=frozenset(graph.triplet_ids),
        source_manifest={"kind": "retired_unit_test"},
    )


def test_trainer_free_organism_emits_formal_actuator_and_roundtrips(tmp_path: Path) -> None:
    organism = _tiny_organism()
    board = chess.Board(MATE_ONE)
    old_selector_calls = organism.graph.runtime_choice_count
    actuation = organism.emit_action(board)
    assert actuation is not None
    assert actuation.graph_owned is True
    assert actuation.host_fallback is False
    assert organism.graph.runtime_choice_count == old_selector_calls
    successor = board.copy(stack=False)
    successor.push(chess.Move.from_uci(actuation.move_uci))
    assert successor.is_checkmate()
    artifact = tmp_path / "r0.pkl"
    metadata = organism.save(artifact)
    restored = NativeR0Organism.load(artifact)
    assert metadata["trainer_object_serialized"] is False
    assert restored.emit_action(board) == actuation


def test_actual_child_query_is_deep_isolated_and_does_not_verify_dream_outcome() -> None:
    organism = _tiny_organism()
    board = chess.Board(MATE_ONE)
    frame = FrameContext("actual-r0", FrameKind.VIRTUAL, {"board": board}, hypothetical_action="a1a2")
    graph_before = copy.deepcopy(organism.graph.to_dict())
    query = organism.request_child(frame)
    assert query.response.confirmed is True
    assert query.response.grounded is True
    assert query.response.expected_value == organism.provenance.consolidated_value
    assert query.persistent_mutation_count == 0
    assert organism.graph.to_dict() == graph_before
    assert board.fen() == MATE_ONE


class _PlantedTestChild:
    def dream_session(self):
        return self

    def close(self) -> None:
        pass

    def request(self, frame: FrameContext) -> ChildQuery:
        preferred = frame.hypothetical_action == "f2f8"
        response = ChildResponse(
            child_id="test_child",
            confirmed=preferred,
            expected_value=0.8 if preferred else 0.0,
            uncertainty=0.1,
            grounded=preferred,
            grounding_source="test_only" if preferred else None,
        )
        return ChildQuery(response, None, frame.frame_id, 0, ())


def test_parent_all_replies_changes_graph_action_and_disconnect_removes_effect() -> None:
    board = chess.Board(MATE_ONE)
    genome = NativeHandoverGenome()
    full = genome.decide(board, _PlantedTestChild(), arm="actual_child")
    disconnected = genome.decide(board, _PlantedTestChild(), arm="disconnected")
    assert full.actuation.move_uci == "f2f8"
    assert full.actuator_multiplicity == 1
    assert full.host_fallback_count == 0
    assert full.planted_response_count == 0
    assert disconnected.actuation.move_uci != full.actuation.move_uci


def test_experimental_path_survives_fail_hard_legacy_authority_tripwires() -> None:
    organism = _tiny_organism()
    with native_authority_tripwires() as counts:
        actuation = organism.emit_action(chess.Board(MATE_ONE))
    assert actuation is not None
    assert counts == {"weighted_selector": 0, "provider_fallback": 0, "child_priority": 0}


def test_dream_firewall_rejects_persistent_capabilities_and_isolates_board() -> None:
    organism = _tiny_organism()
    board = chess.Board(MATE_ONE)
    result = run_dream_firewall_canary(organism, board)
    assert result.rejected_operations == (
        "update_weight", "update_lifecycle", "update_reservoir",
        "set_maturity", "reward", "update_topology", "actuate",
    )
    assert result.persistent_mutation_count == 0
    assert result.board_isolated is True
    assert set(result.clone_mutations_exercised) == {"weight", "lifecycle", "topology", "maturity", "board"}


def test_shuffled_control_preserves_child_response_multiset() -> None:
    board = chess.Board(MATE_ONE)
    genome = NativeHandoverGenome()
    full = genome.decide(board, _PlantedTestChild(), arm="actual_child")
    shuffled = genome.decide(board, _PlantedTestChild(), arm="shuffled", shuffle_seed=7)
    def multiset(decision):
        return sorted(
            tuple(sorted(query.response.to_dict().items()))
            for queries in decision.response_slots.values()
            for query in queries
        )
    assert multiset(full) == multiset(shuffled)
    assert full.graph_node_count == shuffled.graph_node_count
    assert full.graph_edge_count == shuffled.graph_edge_count


class _AllReplyTestChild:
    def dream_session(self):
        return self

    def close(self) -> None:
        pass

    def __init__(self, preferred_action: str, failing_action: str | None = None) -> None:
        self.preferred_action = preferred_action
        self.failing_action = failing_action
        self.failed_once = False

    def request(self, frame: FrameContext) -> ChildQuery:
        confirmed = True
        if frame.hypothetical_action == self.failing_action and not self.failed_once:
            confirmed = False
            self.failed_once = True
        value = 0.9 if frame.hypothetical_action == self.preferred_action else 0.4
        response = ChildResponse(
            child_id="test_child",
            confirmed=confirmed,
            expected_value=value if confirmed else 0.0,
            uncertainty=0.1,
            grounded=confirmed,
            grounding_source="test_only" if confirmed else None,
        )
        return ChildQuery(response, None, frame.frame_id, 0, ())


def test_one_reply_failure_blocks_the_all_replies_parent_leg() -> None:
    board = chess.Board("8/8/8/8/4K3/8/6R1/7k w - - 0 1")
    candidates = []
    for move in sorted(board.legal_moves, key=lambda item: item.uci()):
        after = board.copy(stack=False)
        after.push(move)
        if after.legal_moves.count() >= 2:
            candidates.append(move.uci())
    assert candidates
    target = candidates[-1]
    genome = NativeHandoverGenome()
    all_confirm = genome.decide(board, _AllReplyTestChild(target), arm="actual_child")
    one_fails = genome.decide(board, _AllReplyTestChild(target, target), arm="actual_child")
    assert all_confirm.actuation.move_uci == target
    assert one_fails.actuation.move_uci != target
