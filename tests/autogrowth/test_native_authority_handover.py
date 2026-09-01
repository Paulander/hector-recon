from __future__ import annotations

import copy
from pathlib import Path

import chess
import pytest

from recon_lite import (
    AnonymousChoiceOption,
    ChildResponse,
    FrameContext,
    FrameKind,
    LinkType,
    NodeType,
)
from recon_lite_hector.nodes import StemCellState
from recon_lite_hector.learning import IntrinsicCreditConfig, IntrinsicCreditEngine
from recon_lite_chess.autogrowth.native_authority_handover import (
    ChildQuery,
    FrozenCompetenceProvenance,
    GraphTerminalSignal,
    NativeHandoverGenome,
    NativeR0Organism,
    _OptionSignalCapture,
    _alias_invariant_capture_union,
    _formal_native_options,
    native_authority_tripwires,
    run_dream_firewall_canary,
)
from recon_lite_chess.autogrowth.native_intrinsic_curriculum import R0_COMPETENCE_ID
from recon_lite_chess.autogrowth.native_single_graph_curriculum import (
    ROOT_ID,
    NativeReConKRKGraph,
    NativeSingleGraphConfig,
    _triplet_keys,
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


def test_dream_session_uses_projected_guard_not_full_serialization(
    monkeypatch,
) -> None:
    organism = _tiny_organism()
    frame = FrameContext(
        "projected-guard",
        FrameKind.VIRTUAL,
        {"board": chess.Board(MATE_ONE)},
    )
    original_guard = organism.inference_guard_identity
    calls = 0

    def counted_guard() -> str:
        nonlocal calls
        calls += 1
        return original_guard()

    def forbidden_full_audit():
        raise AssertionError("dream hot path used the full serialization audit")

    monkeypatch.setattr(organism, "inference_guard_identity", counted_guard)
    monkeypatch.setattr(organism, "persistent_state_audit", forbidden_full_audit)
    session = organism.dream_session()
    try:
        query = session.request(frame)
    finally:
        session.close()

    assert query.persistent_mutation_count == 0
    assert calls == 3


def test_dream_session_guard_detects_static_source_manifest_mutation() -> None:
    organism = _tiny_organism()
    session = organism.dream_session()
    organism.source_manifest["unexpected_mutation"] = True

    with pytest.raises(RuntimeError, match="mutated the persistent organism"):
        session.request(FrameContext(
            "manifest-mutation",
            FrameKind.VIRTUAL,
            {"board": chess.Board(MATE_ONE)},
        ))


def test_dream_session_guard_detects_inference_metadata_mutation() -> None:
    organism = _tiny_organism()
    session = organism.dream_session()
    action_node = next(
        node for node in organism.graph.graph.nodes.values()
        if "action_uci" in node.meta
    )
    original = str(action_node.meta["action_uci"])
    action_node.meta["action_uci"] = (
        "a1a2" if original != "a1a2" else "a1a3"
    )

    with pytest.raises(RuntimeError, match="mutated the persistent organism"):
        session.request(FrameContext(
            "action-metadata-mutation",
            FrameKind.VIRTUAL,
            {"board": chess.Board(MATE_ONE)},
        ))


def test_inference_guard_binds_composite_trace_index() -> None:
    organism = _tiny_organism()
    before = organism.inference_guard_identity()
    organism.graph.composite_node_by_triplet[(
        "unexpected-composite", "unexpected-triplet"
    )] = "unexpected-node"

    assert organism.inference_guard_identity() != before


def test_inference_guard_binds_behavioral_graph_adjacency() -> None:
    organism = _tiny_organism()
    before = organism.inference_guard_identity()
    key = next(iter(organism.graph.graph.out))
    organism.graph.graph.out[key] = []

    assert organism.inference_guard_identity() != before


def test_inference_guard_binds_node_object_identity() -> None:
    organism = _tiny_organism()
    before = organism.inference_guard_identity()
    node = next(iter(organism.graph.graph.nodes.values()))
    node.nid = "mutated-node-identity"

    assert organism.inference_guard_identity() != before


def test_inference_guard_binds_cached_trace_identity() -> None:
    organism = _tiny_organism()
    before = organism.inference_guard_identity()
    organism._trace_state_identity_cache = "mutated-trace-identity"

    assert organism.inference_guard_identity() != before


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


def test_same_move_aliases_share_formally_confirmed_trace_evidence() -> None:
    """Alias order and anonymous winner must not change graph evidence."""

    board = chess.Board(MATE_ONE)
    target = chess.Move.from_uci("f2f1")
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
    for move in board.legal_moves:
        graph.ensure_triplet(board, move, stage="alias_trace_test")

    def atom_ids(triplet_id: str) -> set[str]:
        return {
            node_id
            for node_id in graph.triplet_nodes[triplet_id]
            if graph.graph.nodes[node_id].ntype is NodeType.TERMINAL
            and graph.graph.nodes[node_id].meta.get("shared_feature_atom")
        }

    # Choose deterministic aliases with different attached shared atoms.
    ordered_aliases = tuple(sorted(
        graph.triplet_ids,
        key=lambda item: (len(atom_ids(item)), item),
    ))
    first_alias, second_alias = ordered_aliases[0], ordered_aliases[-1]
    aliases = (first_alias, second_alias)
    assert atom_ids(first_alias) != atom_ids(second_alias)
    common_atoms = sorted(atom_ids(first_alias) & atom_ids(second_alias))
    assert len(common_atoms) >= 2
    composite_id = graph.materialize_shared_composite(
        common_atoms[:2], aliases, stage="alias_trace_test"
    )
    graph.composite_cells[composite_id].state = StemCellState.MATURE

    first_root_edge = graph.graph.get_edge(ROOT_ID, first_alias, LinkType.SUB)
    second_root_edge = graph.graph.get_edge(ROOT_ID, second_alias, LinkType.SUB)
    assert first_root_edge is not None and second_root_edge is not None
    first_root_edge.w = 0.25
    second_root_edge.w = 0.75

    target_keys = _triplet_keys(
        board,
        target,
        key_mode=graph.config.key_mode,
    )

    def run(allowed: tuple[str, ...]):
        graph._triplets_from_active_shared_atoms = (  # type: ignore[method-assign]
            lambda keys: allowed if keys == target_keys else ()
        )
        return _formal_native_options(
            graph,
            board,
            allowed_triplets=allowed,
            per_actuator_budget=16,
        )

    single_first, _ticks, first_captures = run((first_alias,))
    single_second, _ticks, second_captures = run((second_alias,))
    paired_forward, _ticks, forward_captures = run(
        (first_alias, second_alias)
    )
    paired_reverse, _ticks, reverse_captures = run(
        (second_alias, first_alias)
    )
    assert len(single_first) == len(single_second) == 1
    assert len(paired_forward) == len(paired_reverse) == 2
    first_option = single_first[0].identity
    second_option = single_second[0].identity
    expected_base_ids = tuple(sorted(
        set(first_captures[first_option].base_terminal_node_ids)
        | set(second_captures[second_option].base_terminal_node_ids)
    ))
    expected_composite_ids = tuple(sorted(
        set(first_captures[first_option].mature_composite_ids)
        | set(second_captures[second_option].mature_composite_ids)
    ))

    def evidence(captures, option_identity):
        capture = captures[option_identity]
        return (
            capture.base_terminal_node_ids,
            capture.mature_composite_ids,
            capture.terminal_signals,
        )

    expected = (
        expected_base_ids,
        expected_composite_ids,
        forward_captures[paired_forward[0].identity].terminal_signals,
    )
    assert expected_base_ids
    assert expected_composite_ids == (composite_id,)
    assert evidence(forward_captures, paired_forward[0].identity) == expected
    assert evidence(forward_captures, paired_forward[1].identity) == expected
    assert evidence(reverse_captures, paired_reverse[0].identity) == expected
    assert evidence(reverse_captures, paired_reverse[1].identity) == expected
    assert tuple(signal.identity for signal in expected[2]) == tuple(sorted(
        (*expected_base_ids, *expected_composite_ids)
    ))
    composite_instances = {
        graph.composite_node_by_triplet[(composite_id, alias)]
        for alias in aliases
    }
    composite_signal = next(
        signal for signal in expected[2]
        if signal.identity == composite_id
    )
    assert composite_signal.source_node_identity in composite_instances
    assert composite_signal.provenance == (
        "same_actuator_formally_confirmed_mature_composite"
    )

    # Alias identity and strength still belong to each option; only evidence
    # is shared.  The larger root weight remains visible to the choice genome.
    assert {option.identity for option in paired_forward} == {
        first_option,
        second_option,
    }
    assert paired_forward[0].activation != paired_forward[1].activation


def test_alias_evidence_union_isolated_by_exact_actuator() -> None:
    first = AnonymousChoiceOption(
        identity="alias:first",
        actuator_identity="chess_move:a1a2",
        activation=0.25,
        confirmed=True,
    )
    second = AnonymousChoiceOption(
        identity="alias:second",
        actuator_identity="chess_move:a1a2",
        activation=0.75,
        confirmed=True,
    )
    other = AnonymousChoiceOption(
        identity="alias:other",
        actuator_identity="chess_move:b1b2",
        activation=0.5,
        confirmed=True,
    )

    def capture(option_identity: str, signal_identity: str):
        signal = GraphTerminalSignal(
            identity=signal_identity,
            role="BASE_TERMINAL",
            source_node_identity=signal_identity,
            terminal_kind="shared_feature_atom",
            provenance="same_actuator_formally_confirmed_terminal",
        )
        return _OptionSignalCapture(
            option_identity=option_identity,
            base_terminal_node_ids=(signal_identity,),
            mature_composite_ids=(),
            terminal_signals=(signal,),
        )

    captures = {
        first.identity: capture(first.identity, "atom:first"),
        second.identity: capture(second.identity, "atom:second"),
        other.identity: capture(other.identity, "atom:other"),
    }
    normalized = _alias_invariant_capture_union(
        (first, second, other), captures
    )

    assert normalized[first.identity].base_terminal_node_ids == (
        "atom:first", "atom:second"
    )
    assert normalized[second.identity].base_terminal_node_ids == (
        "atom:first", "atom:second"
    )
    assert normalized[other.identity] == captures[other.identity]
