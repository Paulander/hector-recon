from __future__ import annotations

import copy
from dataclasses import replace
import inspect

import chess
import pytest

from recon_lite import FrameContext, FrameKind, Node, NodeType
from recon_lite_chess.autogrowth.native_authority_lab import (
    NativeAuthorityLabConfig,
    load_retired_r0_build,
)
from recon_lite_chess.autogrowth.native_competence_envelope import (
    CompetenceEnvelopeConfig,
    GraphNativeCompetenceEnvelope,
    SpecializationMode,
    extract_active_competence_signals,
)
from recon_lite_chess.autogrowth.native_trace_competence_authority import (
    GroundedOutcomeReceipt,
    TraceNativeCompetenceOrganism,
    TraceNativeLearningConfig,
)


@pytest.fixture(scope="module")
def r0():
    return load_retired_r0_build(NativeAuthorityLabConfig()).organism


def _wrapper(r0, *, mode=SpecializationMode.LOCAL_CONTRAST):
    config = CompetenceEnvelopeConfig(selection_seed=314159)
    return TraceNativeCompetenceOrganism.empty(
        r0,
        envelope_config=config,
        learning_config=TraceNativeLearningConfig(
            lifecycle_connected=True,
            specialization_mode=mode,
            genome_seed=config.selection_seed,
        ),
    )


def _real_decision(wrapper, board, frame_id="authority-real"):
    frame = FrameContext(frame_id, FrameKind.REAL, values={"board": board})
    actuation, trace = wrapper.r0.emit_action_with_trace(frame)
    assert actuation is not None and trace is not None
    successor = board.copy(stack=False)
    successor.push(chess.Move.from_uci(actuation.move_uci))
    return actuation, trace, successor


def test_selected_trace_matches_shadow_without_cross_option_union(r0) -> None:
    wrapper = _wrapper(r0)
    board = chess.Board(load_retired_r0_build(NativeAuthorityLabConfig()).pools.r0_train[0])
    actuation, trace, _ = _real_decision(wrapper, board)
    shadow = extract_active_competence_signals(r0, board, actuation)
    assert trace.ordered_signal_identities == shadow
    assert trace.option_identity == actuation.option_identity
    assert trace.actuation == actuation
    assert trace.ordered_signal_identities.count("internal:policy_response") == 1
    assert all(item.identity in shadow for item in trace.terminal_signals)


def test_real_virtual_and_permuted_graph_outputs_are_frame_local(r0) -> None:
    wrapper = _wrapper(r0)
    build = load_retired_r0_build(NativeAuthorityLabConfig())
    boards = [chess.Board(item) for item in build.pools.r0_train[:2]]

    def run(kind, order):
        rows = {}
        for index in order:
            frame = FrameContext(
                f"frame:{index}", kind, values={"board": boards[index]}
            )
            actuation, trace = wrapper.r0.emit_action_with_trace(frame)
            rows[index] = (actuation, trace)
        return rows

    real = run(FrameKind.REAL, (0, 1))
    virtual = run(FrameKind.VIRTUAL, (0, 1))
    permuted = run(FrameKind.REAL, (1, 0))
    for index in range(2):
        assert real[index][0] == virtual[index][0] == permuted[index][0]
        assert (
            real[index][1].terminal_signals
            == virtual[index][1].terminal_signals
            == permuted[index][1].terminal_signals
        )
        assert real[index][1].confirmed_base_terminal_node_ids == (
            virtual[index][1].confirmed_base_terminal_node_ids
        )
        assert real[index][1].confirmed_mature_composite_ids == (
            virtual[index][1].confirmed_mature_composite_ids
        )


def test_grounded_terminal_mints_real_receipt_and_virtual_cannot(r0) -> None:
    wrapper = _wrapper(r0)
    board = chess.Board(load_retired_r0_build(NativeAuthorityLabConfig()).pools.r0_train[0])
    _, trace, successor = _real_decision(wrapper, board)
    receipt = wrapper.completion_terminal().mint(trace, board, successor)
    assert receipt.event_id != receipt.context_fingerprint
    assert receipt.observed_terminal_result == successor.is_checkmate()
    before = len(wrapper.envelope.evidence)
    emission = wrapper.observe_grounded(receipt)
    assert emission.evidence_inserted
    assert len(wrapper.envelope.evidence) == before + 1

    virtual = FrameContext("virtual", FrameKind.VIRTUAL, values={"board": board})
    _, virtual_trace = wrapper.r0.emit_action_with_trace(virtual)
    with pytest.raises(ValueError, match="REAL"):
        wrapper.completion_terminal().mint(virtual_trace, board, successor)


def test_duplicate_event_is_idempotent_but_repeated_context_is_new_event(r0) -> None:
    wrapper = _wrapper(r0)
    board = chess.Board(load_retired_r0_build(NativeAuthorityLabConfig()).pools.r0_train[0])
    _, trace, successor = _real_decision(wrapper, board, "repeat-context")
    terminal = wrapper.completion_terminal()
    first = terminal.mint(trace, board, successor)
    wrapper.observe_grounded(first)
    after_first = wrapper.continuation_digest_v3()
    duplicate = wrapper.observe_grounded(first)
    assert duplicate == wrapper.observation_emissions[first.event_id]
    assert wrapper.continuation_digest_v3() == after_first
    second = terminal.mint(trace, board, successor)
    wrapper.observe_grounded(second)
    assert first.context_fingerprint == second.context_fingerprint
    assert first.event_id != second.event_id
    assert len(wrapper.receipts) == 2

    altered = replace(first, observed_terminal_result=not first.observed_terminal_result)
    with pytest.raises(RuntimeError):
        wrapper.observe_grounded(altered)


def test_wrong_successor_stale_and_cross_organism_traces_fail_closed(r0) -> None:
    wrapper = _wrapper(r0)
    board = chess.Board(load_retired_r0_build(NativeAuthorityLabConfig()).pools.r0_train[0])
    _, trace, successor = _real_decision(wrapper, board)
    wrong = board.copy(stack=False)
    wrong.push(next(iter(wrong.legal_moves)))
    if wrong.fen() != successor.fen():
        with pytest.raises(RuntimeError, match="successor"):
            wrapper.completion_terminal().mint(trace, board, wrong)
    stale = replace(trace, source_state_identity="stale")
    with pytest.raises(RuntimeError, match="stale"):
        wrapper.completion_terminal().mint(stale, board, successor)
    other = _wrapper(r0)
    other.r0.provenance = replace(other.r0.provenance, child_id="other-child")
    with pytest.raises(RuntimeError, match="another"):
        other.completion_terminal().mint(trace, board, successor)


def test_runner_cannot_inject_learning_law_or_evidence() -> None:
    observe = inspect.signature(TraceNativeCompetenceOrganism.observe_grounded)
    grow = inspect.signature(TraceNativeCompetenceOrganism.grow_from_grounded_receipts)
    assert tuple(observe.parameters) == ("self", "receipt")
    assert tuple(grow.parameters) == ("self", "receipts")
    forbidden = {
        "record", "active_signal_ids", "observed_completion", "frame",
        "lifecycle_connected", "specialization_mode", "genome",
        "eligible_specialization_pairs", "target_cell_identity",
    }
    assert forbidden.isdisjoint(observe.parameters)
    assert forbidden.isdisjoint(grow.parameters)


def test_serialization_has_exact_next_event_equivalence_and_dream_purity(r0) -> None:
    wrapper = _wrapper(r0)
    restored = TraceNativeCompetenceOrganism.loads(wrapper.dumps())
    board = chess.Board(load_retired_r0_build(NativeAuthorityLabConfig()).pools.r0_train[0])
    _, left_trace, left_successor = _real_decision(wrapper, board, "next-event")
    _, right_trace, right_successor = _real_decision(restored, board, "next-event")
    left = wrapper.completion_terminal().mint(left_trace, board, left_successor)
    right = restored.completion_terminal().mint(right_trace, board, right_successor)
    assert left == right
    assert wrapper.observe_grounded(left) == restored.observe_grounded(right)
    assert wrapper.continuation_manifest_v3() == restored.continuation_manifest_v3()

    before = restored.continuation_digest_v3()
    session = restored.dream_session()
    query = session.request(FrameContext(
        "pure-dream", FrameKind.VIRTUAL, values={"board": board}
    ))
    session.close()
    assert query.graph_signal_trace is not None
    assert restored.continuation_digest_v3() == before


def test_v3_covers_configuration_xp_and_learned_state_but_rebuilds_transients(r0) -> None:
    wrapper = _wrapper(r0)
    baseline = wrapper.continuation_digest_v3()

    mode_changed = copy.deepcopy(wrapper)
    mode_changed.learning_config = replace(
        mode_changed.learning_config,
        specialization_mode=SpecializationMode.COUNTEREXAMPLE_BLIND,
    )
    assert mode_changed.continuation_digest_v3() != baseline

    # A genuine cell/XP mutation must be visible once a cell exists.
    from recon_lite_chess.autogrowth.native_competence_envelope import (
        CompetenceContextCell,
    )
    from recon_lite_hector.nodes import StemCellTerminal
    changed = copy.deepcopy(wrapper)
    stem = StemCellTerminal("manifest-cell")
    cell = CompetenceContextCell("manifest-cell", ("atom",), 0, 0, stem)
    changed.envelope.cells[cell.cell_id] = cell
    changed.envelope._member_specs.add(cell.members)
    changed.envelope.rebuild_graph()
    with_cell = changed.continuation_digest_v3()
    changed.envelope.cells[cell.cell_id].stem_cell.candidate_stats.credit_stats.xp = 3.0
    assert changed.continuation_digest_v3() != with_cell
    restored_changed = TraceNativeCompetenceOrganism.loads(changed.dumps())
    assert restored_changed.continuation_manifest_v3() == changed.continuation_manifest_v3()

    wiring_changed = copy.deepcopy(wrapper)
    wiring_changed.learning_config = replace(
        wiring_changed.learning_config, lifecycle_connected=False
    )
    assert wiring_changed.continuation_digest_v3() != baseline

    weight_changed = copy.deepcopy(wrapper)
    edge = weight_changed.r0.graph.graph.edges[0]
    edge.w = float(edge.w) + 0.125
    assert weight_changed.continuation_digest_v3() != baseline

    transient = copy.deepcopy(wrapper)
    transient.envelope.graph.add_node(Node(
        "transient-runtime-only", NodeType.TERMINAL,
        predicate=lambda _node, _env: (True, True),
    ))
    assert transient.continuation_digest_v3() == baseline


def test_legacy_extractor_is_not_called_by_production_dream(r0, monkeypatch) -> None:
    import recon_lite_chess.autogrowth.native_competence_envelope as module

    wrapper = _wrapper(r0)
    monkeypatch.setattr(
        module,
        "extract_active_competence_signals",
        lambda *_a, **_k: (_ for _ in ()).throw(
            AssertionError("production called shadow extractor")
        ),
    )
    board = chess.Board(load_retired_r0_build(NativeAuthorityLabConfig()).pools.r0_train[0])
    session = wrapper.dream_session()
    try:
        query = session.request(FrameContext(
            "tripwire-dream", FrameKind.VIRTUAL, values={"board": board}
        ))
    finally:
        session.close()
    assert query.active_competence_signal_ids
