from __future__ import annotations

import chess
import pytest

from recon_lite import ChildResponse, FrameContext, FrameKind
from recon_lite_hector.learning import IntrinsicCreditConfig, IntrinsicCreditEngine
from recon_lite_chess.autogrowth.native_authority_handover import (
    ACTUATOR_PREFIX, ChildQuery, FrozenCompetenceProvenance,
    GraphActuation, NativeR0Organism,
)
from recon_lite_chess.autogrowth.native_child_availability_diagnostic import AvailabilityDiagnosticConfig
from recon_lite_chess.autogrowth.native_child_availability import (
    FailClosedNativeHandoverGenome, observe_query_completion, observe_real_child,
    response_with_availability,
)
from recon_lite_chess.autogrowth.native_intrinsic_curriculum import R0_COMPETENCE_ID
from recon_lite_chess.autogrowth.native_single_graph_curriculum import (
    NativeReConKRKGraph, NativeSingleGraphConfig,
)

MATE_ONE = "8/8/8/8/8/7K/5R2/7k w - - 0 1"
R1_ROW = "3K4/k7/7R/8/8/8/8/8 w - - 0 1"


def _tiny_organism() -> NativeR0Organism:
    board = chess.Board(MATE_ONE)
    mate = next(
        move for move in board.legal_moves
        if _after(board, move).is_checkmate()
    )
    graph = NativeReConKRKGraph(config=NativeSingleGraphConfig(
        include_symmetries=False, max_ticks=80, indexed_scheduler=True,
        key_mode="canonical", shared_feature_atoms=True,
        shared_projection_atoms=True, include_grouped_cache_terminals=False,
        score_action_pattern_atoms=True, terminal_score_normalization="sqrt",
    ))
    graph.apply_intrinsic_td(
        board, mate, td_error=1.0, stage_diagnostic="retired_test"
    )
    graph.mature_existing_graph()
    graph.freeze_existing_parameters(reason="unit_test")
    credit = IntrinsicCreditEngine(IntrinsicCreditConfig(min_grounding_evidence=3))
    credit.register(R0_COMPETENCE_ID, mature=True)
    state = credit.states[R0_COMPETENCE_ID]
    state.slow_value = state.fast_value = 0.8
    state.terminal_evidence = 3
    state.causal_confirmations = 1
    state.grounding_level = 0
    provenance = FrozenCompetenceProvenance.from_credit(credit, R0_COMPETENCE_ID)
    return NativeR0Organism(
        graph=graph, credit=credit, provenance=provenance,
        frozen_triplet_ids=frozenset(graph.triplet_ids),
        source_manifest={"kind": "retired_unit_test"},
    )


def _after(board: chess.Board, move: chess.Move) -> chess.Board:
    result = board.copy(stack=False)
    result.push(move)
    return result


def _query(*, available: bool, frame_id: str) -> ChildQuery:
    response = ChildResponse(
        child_id="grounded_child", confirmed=available, policy_response=True,
        available=available, expected_value=0.8 if available else 0.0,
        uncertainty=0.1, grounded=True, grounding_source="observed_outcomes",
    )
    return ChildQuery(response, None, frame_id, 0, ())


def _synthetic_slots(board: chess.Board, target: str) -> tuple[dict, dict]:
    slots = {}
    frames = {}
    for move in sorted(board.legal_moves, key=lambda item: item.uci()):
        after = _after(board, move)
        rows = []
        for index, reply in enumerate(sorted(after.legal_moves, key=lambda item: item.uci())):
            available = move.uci() == target
            rows.append(_query(available=available, frame_id=f"{move.uci()}:{reply.uci()}"))
            successor = _after(after, reply)
            frames[(move.uci(), index)] = FrameContext(
                frame_id=f"{move.uci()}:{reply.uci()}", kind=FrameKind.VIRTUAL,
                values={"board": successor}, hypothetical_action=move.uci(),
            )
        slots[move.uci()] = tuple(rows)
    return slots, frames


def test_child_contract_separates_policy_availability_value_and_grounding() -> None:
    response = ChildResponse(
        child_id="child", confirmed=False, policy_response=True, available=False,
        expected_value=0.7, uncertainty=0.2, grounded=True,
        grounding_source="past_real_outcomes",
    )
    assert response.policy_response is True
    assert response.available is False
    assert response.confirmed is False
    assert response.grounded is True
    assert response.selection_strength == 0.0
    with pytest.raises(ValueError, match="AVAILABLE requires POLICY_RESPONSE"):
        ChildResponse(
            child_id="child", confirmed=True, policy_response=False, available=True,
            expected_value=0.7, uncertainty=0.2, grounded=True,
            grounding_source="past_real_outcomes",
        )


def test_fail_closed_option_and_separate_graph_exploration() -> None:
    board = chess.Board(R1_ROW)
    slots, frames = _synthetic_slots(board, "d8c8")
    genome = FailClosedNativeHandoverGenome()
    decision = genome.decide_from_available_slots(board, slots, frames)
    assert decision.selection_mode == "exploit"
    assert decision.exploit_actuation is not None
    assert decision.exploit_actuation.move_uci == "d8c8"
    target = list(slots["d8c8"])
    target[0] = _query(available=False, frame_id=target[0].frame_id)
    slots["d8c8"] = tuple(target)
    failed = genome.decide_from_available_slots(board, slots, frames)
    assert failed.exploit_actuation is None
    assert failed.exploit_actuator_multiplicity == 0
    assert failed.selection_mode == "explore"
    assert failed.exploration_actuation is not None
    assert failed.host_fallback_count == 0
    disconnected = genome.decide_from_available_slots(
        board, slots, frames, disconnected=True
    )
    assert disconnected.exploit_actuation is None
    assert disconnected.selection_mode == "explore"


def test_real_child_action_confirms_declared_completion_only_after_execution() -> None:
    organism = _tiny_organism()
    board = chess.Board(MATE_ONE)
    observation = observe_real_child(organism, board)
    assert observation.response.policy_response is True
    assert observation.response.available is True
    assert observation.completion_confirmed is True
    assert observation.observed_terminal == "mate"
    assert board.is_checkmate()


def test_noncompletion_is_local_competence_failure_without_fabricated_loss() -> None:
    organism = _tiny_organism()
    board = chess.Board("8/8/8/8/4K3/8/6R1/7k w - - 0 1")
    move = chess.Move.from_uci("g2g3")
    assert move in board.legal_moves
    query = ChildQuery(
        response=ChildResponse(
            child_id=organism.provenance.child_id, confirmed=True,
            policy_response=True, available=True, expected_value=0.8,
            uncertainty=0.1, grounded=True,
            grounding_source=organism.provenance.grounding_source,
        ),
        actuation=GraphActuation(
            actuator_identity=f"{ACTUATOR_PREFIX}{move.uci()}",
            move_uci=move.uci(), option_identity="diagnostic", activation=0.5,
            candidate_count=1, formal_ticks=1,
        ), frame_id="real-failure", persistent_mutation_count=0, effect_attempts=(),
    )
    observation = observe_query_completion(organism, board, query)
    assert observation.response.policy_response is True
    assert observation.response.available is False
    assert observation.response.grounded is True
    assert observation.local_competence_failure is True
    assert observation.observed_terminal is None
    assert observation.fabricated_terminal_reward is False
    assert response_with_availability(
        organism, query, available=False
    ).response.expected_value == 0.0

def test_diagnostic_config_is_retired_only() -> None:
    config = AvailabilityDiagnosticConfig()
    assert "retired_r0_child_availability" in config.output_path
    assert config.r1_row_index == 0
