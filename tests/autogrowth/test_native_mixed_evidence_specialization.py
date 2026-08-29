from __future__ import annotations

import copy

import chess
import pytest

from recon_lite import FrameContext, FrameKind
from recon_lite_hector.learning import (
    IntrinsicCreditConfig,
    IntrinsicCreditEngine,
)
from recon_lite_hector.nodes import StemCellState, StemCellTerminal
from recon_lite_chess.autogrowth.native_authority_handover import (
    FrozenCompetenceProvenance,
    NativeR0Organism,
)
from recon_lite_chess.autogrowth.native_competence_envelope import (
    AvailabilityState,
    CompetenceContextCell,
    CompetenceEnvelopeConfig,
    DormantOrigin,
    SpecializationMode,
)
from recon_lite_chess.autogrowth.native_prospective_evidence_authority_v2 import (
    HISTORY_VALIDATION_INCREMENTAL,
    HISTORY_VALIDATION_LEGACY,
    MIN_SUPPORT,
    NativeProspectiveAuthorityV2,
    RequestBasis,
    V2Mode,
)
from recon_lite_chess.autogrowth.native_single_graph_curriculum import (
    NativeReConKRKGraph,
    NativeSingleGraphConfig,
)
from recon_lite_chess.autogrowth.native_trace_competence_authority import (
    TraceNativeCompetenceOrganism,
    TraceNativeLearningConfig,
)


MATE = "8/8/8/8/8/6K1/R7/7k w - - 0 {fullmove}"
NONMATE = "8/8/8/8/8/5K2/R7/7k w - - 0 {fullmove}"
ADVERSARIAL = {
    AvailabilityState.AVAILABLE: (
        "8/8/8/8/8/8/RK6/3k4 w - - 0 {fullmove}"
    ),
    AvailabilityState.REFUTED: (
        "8/8/8/8/8/7K/R7/7k w - - 0 {fullmove}"
    ),
}
PARENT_ID = "mixed_evidence_shadow"
R0_ID = "mixed_evidence_test_r0"


def _after(board: chess.Board, move: chess.Move) -> chess.Board:
    successor = board.copy(stack=False)
    successor.push(move)
    return successor


def _board(outcome: bool, fullmove: int) -> chess.Board:
    return chess.Board(
        (MATE if outcome else NONMATE).format(fullmove=fullmove)
    )


def _mixed_outcome_r0() -> NativeR0Organism:
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
    move = chess.Move.from_uci("a2a1")
    for _ in range(4):
        for outcome in (True, False):
            board = _board(outcome, 1)
            assert move in board.legal_moves
            assert _after(board, move).is_checkmate() is outcome
            graph.apply_intrinsic_td(
                board,
                move,
                td_error=1.0,
                stage_diagnostic="mixed_evidence_specialization_test",
            )
    graph.mature_existing_graph()
    graph.freeze_existing_parameters(
        reason="mixed_evidence_specialization_test"
    )
    credit = IntrinsicCreditEngine(
        IntrinsicCreditConfig(min_grounding_evidence=3)
    )
    credit.register(R0_ID, mature=True)
    state = credit.states[R0_ID]
    state.fast_value = state.slow_value = 0.8
    state.terminal_evidence = 3
    state.causal_confirmations = 1
    state.grounding_level = 0
    return NativeR0Organism(
        graph=graph,
        credit=credit,
        provenance=FrozenCompetenceProvenance.from_credit(credit, R0_ID),
        frozen_triplet_ids=frozenset(graph.triplet_ids),
        source_manifest={"kind": "mixed_evidence_specialization_test"},
    )


def _accept_historical(
    source: TraceNativeCompetenceOrganism,
    *,
    outcome: bool,
) -> tuple[str, ...]:
    terminal = source.completion_terminal()
    receipt_ids: list[str] = []
    for fullmove in range(1, 5):
        board = _board(outcome, fullmove)
        actuation, trace = source.r0.emit_action_with_trace(FrameContext(
            f"mixed-evidence-discovery:{outcome}:{fullmove}",
            FrameKind.REAL,
            {"board": board},
        ))
        assert actuation is not None and trace is not None
        successor = _after(
            board, chess.Move.from_uci(actuation.move_uci)
        )
        assert successor.is_checkmate() is outcome
        receipt = terminal.mint(trace, board, successor)
        record, inserted = source._accept_receipt(receipt)
        assert inserted
        assert source.envelope.add_unique_evidence(record)
        receipt_ids.append(receipt.event_id)
    return tuple(sorted(receipt_ids))


def _mixed_authority(
    polarity: AvailabilityState,
) -> NativeProspectiveAuthorityV2:
    envelope_config = CompetenceEnvelopeConfig(selection_seed=81357)
    source = TraceNativeCompetenceOrganism.empty(
        _mixed_outcome_r0(),
        envelope_config=envelope_config,
        learning_config=TraceNativeLearningConfig(
            lifecycle_connected=True,
            specialization_mode=SpecializationMode.LOCAL_CONTRAST,
            genome_seed=envelope_config.selection_seed,
        ),
    )
    support_outcome = polarity is AvailabilityState.AVAILABLE
    # Historical reads are deliberately polarity-contradictory so the four
    # prospective supports below are the complete eligibility support set.
    evidence_ids = _accept_historical(
        source, outcome=not support_outcome
    )
    stem = StemCellTerminal(PARENT_ID)
    stem.state = StemCellState.DORMANT
    stem.trial_node_id = PARENT_ID
    stem.trial_parent_id = "competence_available_root"
    parent = CompetenceContextCell(
        cell_id=PARENT_ID,
        members=("internal:policy_response",),
        born_round=0,
        born_request_ordinal=0,
        stem_cell=stem,
        polarity=polarity,
        evidence_keys=evidence_ids,
        failures=len(evidence_ids),
        support=len(evidence_ids),
        prune_reason="mixed_outcomes",
        dormant_origin=DormantOrigin.MIXED_OUTCOME_SHADOW,
    )
    source.envelope.cells = {PARENT_ID: parent}
    source.envelope._member_specs = {parent.members}
    source.envelope.rebuild_graph()
    authority = NativeProspectiveAuthorityV2.from_organism(
        source,
        mode=V2Mode.PROSPECTIVE,
        specialization_mode=SpecializationMode.LOCAL_CONTRAST,
        # Four historical rows make ordinal 4 next. C + S1..S5 ends at 10.
        structural_epoch_schedule=(10,),
    )
    authority.close_nomination()
    assert authority.next_expected_ordinal == 4
    return authority


def _open_mint(
    authority: NativeProspectiveAuthorityV2,
    *,
    outcome: bool,
    fullmove: int,
    frame_id: str,
    fen_template: str | None = None,
    frame_session=None,
):
    board = (
        _board(outcome, fullmove)
        if fen_template is None
        else chess.Board(fen_template.format(fullmove=fullmove))
    )
    pending, trace = authority.open_real_event(FrameContext(
        frame_id, FrameKind.REAL, {"board": board}
    ), frame_session=frame_session)
    successor = _after(
        board, chess.Move.from_uci(pending.actuation.move_uci)
    )
    assert successor.is_checkmate() is outcome
    receipt = authority.mint_environment_receipt(
        pending_token=pending.pending_token,
        trace=trace,
        predecessor=board,
        successor=successor,
    )
    return pending, trace, receipt


def _consume(
    authority: NativeProspectiveAuthorityV2,
    *,
    outcome: bool,
    fullmove: int,
    frame_id: str,
    fen_template: str | None = None,
    frame_session=None,
):
    opened = _open_mint(
        authority,
        outcome=outcome,
        fullmove=fullmove,
        frame_id=frame_id,
        fen_template=fen_template,
        frame_session=frame_session,
    )
    return opened, authority.consume(
        opened[2], frame_session=frame_session
    )


@pytest.mark.parametrize(
    "polarity",
    (AvailabilityState.AVAILABLE, AvailabilityState.REFUTED),
)
def test_uncertified_mixed_evidence_request_and_child_are_prospective(
    polarity: AvailabilityState,
) -> None:
    initial = _mixed_authority(polarity)
    incremental = copy.deepcopy(initial)
    replay = copy.deepcopy(initial)
    incremental.set_history_validation_mode_for_development(
        HISTORY_VALIDATION_INCREMENTAL
    )
    replay.set_history_validation_mode_for_development(
        HISTORY_VALIDATION_LEGACY
    )
    support_outcome = polarity is AvailabilityState.AVAILABLE
    sequence = (
        (not support_outcome, 20, "contradiction"),
        (support_outcome, 21, "support-1"),
        (support_outcome, 22, "support-2"),
        (support_outcome, 23, "support-3"),
        (support_outcome, 24, "support-4"),
        (support_outcome, 25, "support-5-one-shot"),
    )
    receipts = []
    emissions = []
    for index, (outcome, fullmove, label) in enumerate(sequence):
        frame_id = f"mixed-evidence:{polarity.value}:{label}"
        incremental_open = _open_mint(
            incremental,
            outcome=outcome,
            fullmove=fullmove,
            frame_id=frame_id,
        )
        replay_open = _open_mint(
            replay,
            outcome=outcome,
            fullmove=fullmove,
            frame_id=frame_id,
        )
        assert incremental_open == replay_open
        emission = incremental.consume(incremental_open[2])
        replay_emission = replay.consume(replay_open[2])
        assert emission == replay_emission
        assert incremental.continuation_manifest() == (
            replay.continuation_manifest()
        )
        incremental.verify_full_history_boundary(
            f"mixed evidence event {index}"
        )
        receipts.append(incremental_open[2])
        emissions.append(emission)

    assert all(
        not emission.graph_specialization_request_ids
        for emission in emissions[:4]
    )
    request_emission = emissions[4]
    assert request_emission.graph_specialization_request_ids == (PARENT_ID,)
    assert request_emission.graph_revocation_ids == ()
    assert request_emission.revoked_cell_ids == ()
    assert emissions[5].graph_specialization_request_ids == ()
    parent_state = incremental.states[PARENT_ID]
    assert not parent_state.prospectively_certified
    assert (
        parent_state.support,
        parent_state.successes,
        parent_state.contradictions,
    ) == (6, 5, 1)
    assert incremental.lifetime_requested_parent_ids == (PARENT_ID,)

    request_id = request_emission.request_queue_appended_ids[0]
    request = incremental.deferred_requests[request_id]
    assert request.request_basis is RequestBasis.UNCERTIFIED_MIXED_EVIDENCE
    assert request.fixed_polarity is polarity
    assert request.contradiction_receipt_id == receipts[0].receipt_id
    assert request.contradiction_ordinal == receipts[0].ordinal
    assert request.request_emission_receipt_id == receipts[4].receipt_id
    assert request.request_emission_ordinal == receipts[4].ordinal
    assert request.parent_prospective_support_receipt_ids == tuple(sorted(
        receipt.receipt_id for receipt in receipts[1:5]
    ))
    confirmed = tuple(
        item for item in request.candidate_terminals if item.confirmed
    )
    assert confirmed
    assert all(
        item.supporting_occurrence_count == MIN_SUPPORT
        and not item.present_in_triggering_contradiction
        and receipts[0].receipt_id in item.inspected_receipt_ids
        and receipts[4].receipt_id in item.inspected_receipt_ids
        for item in confirmed
    )

    restored = NativeProspectiveAuthorityV2.loads(incremental.dumps())
    assert restored.continuation_manifest() == incremental.continuation_manifest()
    assert restored.deferred_requests[request_id] == request
    restored.verify_full_history_boundary("mixed evidence round trip")

    restored.seal_prospective_generation()
    restored.open_structural_successor()
    consumption = restored.consume_next_structural_request()
    assert consumption.request_id == request_id
    assert consumption.genome_call_count == 1
    assert consumption.disposition == "PENDING_CHILD"
    child_id = restored.materialize_deferred_child(request_id)
    child = restored.states[child_id]
    assert child.hypothesis.polarity is polarity
    assert child.hypothesis.lineage_parent_id == PARENT_ID
    assert child.hypothesis.specialization_depth == 1
    assert (
        child.hypothesis.dormant_origin
        is DormantOrigin.DEFERRED_SPECIALIZATION_CHILD
    )
    assert (
        child.support,
        child.successes,
        child.contradictions,
        child.prospectively_certified,
    ) == (0, 0, 0, False)
    escrow = restored.deferred_child_escrows[child_id]
    categories = dict(escrow.categorized_reads)
    assert categories["contradiction_trigger"] == (receipts[0].receipt_id,)
    assert categories["parent_prospective_support"] == tuple(sorted(
        receipt.receipt_id for receipt in receipts[1:5]
    ))
    assert request.request_emission_receipt_id in categories[
        "eligibility_reads"
    ]
    assert set(escrow.discovery_exclusion_receipt_ids) == set(
        restored.accepted_real_references
    )

    restored = NativeProspectiveAuthorityV2.loads(restored.dumps())
    restored.open_prospective_successor()
    contradicted = copy.deepcopy(restored)
    for index, fullmove in enumerate(range(30, 34)):
        _consume(
            restored,
            outcome=support_outcome,
            fullmove=fullmove,
            frame_id=f"child-clean:{polarity.value}:{index}",
        )
    clean_child = restored.states[child_id]
    assert (
        clean_child.successes,
        clean_child.contradictions,
        clean_child.prospectively_certified,
    ) == (4, 0, True)

    contradiction_opened, _ = _consume(
        contradicted,
        outcome=not support_outcome,
        fullmove=40,
        frame_id=f"child-contradiction:{polarity.value}",
        fen_template=ADVERSARIAL[polarity],
    )
    selected_identity = contradicted.states[
        child_id
    ].hypothesis.members[1]
    assert selected_identity in contradiction_opened[1].ordered_signal_identities
    for index, fullmove in enumerate(range(41, 45)):
        _consume(
            contradicted,
            outcome=support_outcome,
            fullmove=fullmove,
            frame_id=f"child-after-contradiction:{polarity.value}:{index}",
        )
    contradicted_child = contradicted.states[child_id]
    assert (
        contradicted_child.successes,
        contradicted_child.contradictions,
        contradicted_child.prospectively_certified,
    ) == (4, 1, False)
    contradicted.verify_full_history_boundary(
        f"mixed child contradiction {polarity.value}"
    )


@pytest.mark.parametrize(
    "polarity",
    (AvailabilityState.AVAILABLE, AvailabilityState.REFUTED),
)
def test_certified_revocation_keeps_current_contradiction_as_anchor(
    polarity: AvailabilityState,
) -> None:
    authority = _mixed_authority(polarity)
    support_outcome = polarity is AvailabilityState.AVAILABLE
    for index, fullmove in enumerate(range(50, 54)):
        _opened, emission = _consume(
            authority,
            outcome=support_outcome,
            fullmove=fullmove,
            frame_id=f"certified-support:{polarity.value}:{index}",
        )
        assert emission.graph_specialization_request_ids == ()
    assert authority.states[PARENT_ID].prospectively_certified

    opened, emission = _consume(
        authority,
        outcome=not support_outcome,
        fullmove=54,
        frame_id=f"certified-revocation:{polarity.value}",
    )
    assert emission.graph_revocation_ids == (PARENT_ID,)
    assert emission.graph_specialization_request_ids == (PARENT_ID,)
    assert not authority.states[PARENT_ID].prospectively_certified
    request = authority.deferred_requests[
        emission.request_queue_appended_ids[0]
    ]
    assert request.request_basis is RequestBasis.CERTIFIED_REVOCATION
    assert request.graph_revocation_confirmed
    assert request.request_emission_receipt_id == opened[2].receipt_id
    assert request.contradiction_receipt_id == opened[2].receipt_id
    assert request.request_emission_ordinal == opened[2].ordinal
    assert request.contradiction_ordinal == opened[2].ordinal
    authority.verify_full_history_boundary(
        f"certified revocation {polarity.value}"
    )
    restored = NativeProspectiveAuthorityV2.loads(authority.dumps())
    assert restored.continuation_manifest() == authority.continuation_manifest()


def test_epoch_frame_session_is_exact_and_clones_frozen_r0_once(
    monkeypatch,
) -> None:
    initial = _mixed_authority(AvailabilityState.AVAILABLE)
    baseline = copy.deepcopy(initial)
    reused = copy.deepcopy(initial)
    phase = "baseline"
    copies = {"baseline": 0, "reused": 0}
    original = NativeReConKRKGraph.frame_runtime_copy

    def counted(runtime_graph):
        copies[phase] += 1
        return original(runtime_graph)

    monkeypatch.setattr(
        NativeReConKRKGraph, "frame_runtime_copy", counted
    )
    sequence = (
        (False, 70, "contradiction"),
        (True, 71, "support-1"),
        (True, 72, "support-2"),
    )
    expected = []
    for outcome, fullmove, label in sequence:
        virtual = baseline.open_virtual(FrameContext(
            f"frame-session:virtual:{label}",
            FrameKind.VIRTUAL,
            {"board": _board(outcome, fullmove)},
        ))
        opened = _open_mint(
            baseline,
            outcome=outcome,
            fullmove=fullmove,
            frame_id=f"frame-session:real:{label}",
        )
        emission = baseline.consume(opened[2])
        expected.append((
            virtual,
            opened,
            emission,
            baseline.continuation_manifest(),
        ))

    phase = "reused"
    session = reused.frame_session()
    try:
        for index, (outcome, fullmove, label) in enumerate(sequence):
            virtual = reused.open_virtual(
                FrameContext(
                    f"frame-session:virtual:{label}",
                    FrameKind.VIRTUAL,
                    {"board": _board(outcome, fullmove)},
                ),
                frame_session=session,
            )
            opened = _open_mint(
                reused,
                outcome=outcome,
                fullmove=fullmove,
                frame_id=f"frame-session:real:{label}",
                frame_session=session,
            )
            emission = reused.consume(
                opened[2], frame_session=session
            )
            assert (
                virtual,
                opened,
                emission,
                reused.continuation_manifest(),
            ) == expected[index]
    finally:
        session.close()

    assert copies == {
        "baseline": 2 * len(sequence),
        "reused": 1,
    }
    reused.verify_full_history_boundary("epoch frame session parity")


def test_epoch_frame_session_closes_across_structural_replacement() -> None:
    authority = _mixed_authority(AvailabilityState.AVAILABLE)
    session = authority.frame_session()
    sequence = (
        (False, 80, "contradiction"),
        (True, 81, "support-1"),
        (True, 82, "support-2"),
        (True, 83, "support-3"),
        (True, 84, "support-4"),
        (True, 85, "support-5"),
    )
    for outcome, fullmove, label in sequence:
        _consume(
            authority,
            outcome=outcome,
            fullmove=fullmove,
            frame_id=f"frame-session-structure:{label}",
            frame_session=session,
        )
    assert authority.next_expected_ordinal == 10
    authority.seal_prospective_generation()
    authority.open_structural_successor()
    while any(
        request_id not in authority.request_consumptions
        for request_id in authority.sealed_request_ids
    ):
        consumption = authority.consume_next_structural_request()
        if consumption.child_cell_id is not None:
            authority.materialize_deferred_child(consumption.request_id)
    authority.open_prospective_successor()
    session.close()

    resumed_session = authority.frame_session()
    try:
        _consume(
            authority,
            outcome=True,
            fullmove=86,
            frame_id="frame-session-structure:post-boundary",
            frame_session=resumed_session,
        )
    finally:
        resumed_session.close()
    authority.verify_full_history_boundary(
        "epoch frame session structural replacement"
    )


def test_epoch_frame_session_detects_runtime_semantic_mutation() -> None:
    authority = _mixed_authority(AvailabilityState.AVAILABLE)
    session = authority.frame_session()
    session.r0_session.virtual_graph.graph.edges[0].w += 0.125

    with pytest.raises(
        RuntimeError, match="runtime changed frozen inference semantics"
    ):
        session.close()


def test_epoch_frame_session_source_audits_are_constant_per_epoch(
    monkeypatch,
) -> None:
    authority = _mixed_authority(AvailabilityState.AVAILABLE)
    r0_type = type(authority.base.r0)
    original = r0_type.persistent_identity_audit
    audit_calls = 0

    def counted(organism):
        nonlocal audit_calls
        audit_calls += 1
        return original(organism)

    monkeypatch.setattr(r0_type, "persistent_identity_audit", counted)
    session = authority.frame_session()
    calls_after_open = audit_calls
    assert calls_after_open == 3
    try:
        for index, (outcome, fullmove) in enumerate((
            (False, 90),
            (True, 91),
            (True, 92),
        )):
            authority.open_virtual(
                FrameContext(
                    f"constant-audit:virtual:{index}",
                    FrameKind.VIRTUAL,
                    {"board": _board(outcome, fullmove)},
                ),
                frame_session=session,
            )
            opened = _open_mint(
                authority,
                outcome=outcome,
                fullmove=fullmove,
                frame_id=f"constant-audit:real:{index}",
                frame_session=session,
            )
            authority.consume(opened[2], frame_session=session)
            assert audit_calls == calls_after_open
    finally:
        session.close()
    assert audit_calls == 6
