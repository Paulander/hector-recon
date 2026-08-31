from __future__ import annotations

import copy
from dataclasses import replace

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
    BoundaryPromotionRequest,
    HISTORY_VALIDATION_INCREMENTAL,
    HISTORY_VALIDATION_LEGACY,
    MIN_SUPPORT,
    NativeProspectiveAuthorityV2,
    ProspectiveV2IntegrityError,
    RequestBasis,
    StructuralMode,
    V2Mode,
)
from recon_lite_chess.autogrowth.native_prospective_boundary_candidate_ecology import (
    ProspectiveBoundaryCandidateEcology,
)
from recon_lite_chess.autogrowth.native_intrinsic_curriculum import (
    _v2_r0_observe_training_successor,
)
from recon_lite_chess.autogrowth import (
    native_prospective_evidence_authority_v2 as authority_module,
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
    *,
    structural_mode: StructuralMode = StructuralMode.SCHEDULED,
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
        structural_epoch_schedule=(10,)
        if structural_mode is StructuralMode.SCHEDULED else (),
        structural_mode=structural_mode,
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


def _ordinary_boundary_request(
    authority: NativeProspectiveAuthorityV2,
    receipt_ids: tuple[str, ...],
    *,
    candidate_id: str,
    member_index: int = 0,
) -> BoundaryPromotionRequest:
    references = [
        authority.accepted_real_references[item] for item in receipt_ids
    ]
    common = set(references[0].ordered_signal_identities)
    for reference in references[1:]:
        common.intersection_update(reference.ordered_signal_identities)
    roles = dict(references[0].typed_signal_roles)
    reusable = tuple(sorted(
        item for item in common
        if roles.get(item) in {"BASE_TERMINAL", "MATURE_COMPOSITE"}
    ))
    member = reusable[member_index]
    trigger = references[0]
    inspected = tuple(sorted(
        item.receipt_id
        for item in authority.accepted_real_references.values()
        if item.ordinal >= trigger.ordinal
    ))
    support = tuple(sorted(
        item.receipt_id
        for item in authority.accepted_real_references.values()
        if (
            item.ordinal >= trigger.ordinal
            and member in item.ordered_signal_identities
            and item.observed_outcome
        )
    ))
    return BoundaryPromotionRequest(
        candidate_id=candidate_id,
        members=(member,),
        fixed_polarity=AvailabilityState.AVAILABLE,
        triggering_receipt_id=trigger.receipt_id,
        supporting_receipt_ids=support,
        inspected_receipt_ids=inspected,
        source_generation=authority.current_generation,
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
    expected_inspected = tuple(sorted(
        receipt.receipt_id for receipt in receipts[:5]
    ))
    assert all(
        item.supporting_occurrence_count == MIN_SUPPORT
        and not item.present_in_triggering_contradiction
        and set(item.inspected_receipt_ids).issubset(expected_inspected)
        and item.inspected_receipt_commitment is not None
        and item.inspected_receipt_commitment.count
        == len(expected_inspected)
        and item.inspected_receipt_commitment.digest
        == authority_module._sha(list(expected_inspected))
        and item.inspected_receipt_commitment.exclusive_frontier
        == request.request_emission_ordinal + 1
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
    read_commitments = dict(escrow.nomination_read_commitments)
    assert request.candidate_inspected_commitment is not None
    assert categories["eligibility_reads"] == (
        request.candidate_inspected_commitment.witness_ids
    )
    assert read_commitments["eligibility_reads"] == (
        request.candidate_inspected_commitment
    )
    exclusion = escrow.discovery_exclusion_commitment
    assert exclusion is not None
    assert escrow.discovery_exclusion_receipt_ids == exclusion.witness_ids
    assert exclusion.count == len(restored.accepted_real_references)
    assert exclusion.exclusive_frontier == restored.next_expected_ordinal

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
    # Frame opening uses the bounded authority hot-path guard; the frozen-R0
    # session still performs its two source identity reads, but no full
    # authority reclosure is needed per epoch.
    assert calls_after_open == 2
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
    assert audit_calls == 5


def test_event_driven_recursive_reclosure_has_no_same_event_certification():
    authority = _mixed_authority(
        AvailabilityState.AVAILABLE,
        structural_mode=StructuralMode.EVENT_DRIVEN,
    )
    first_sequence = (
        (False, 20, "event-driven:contradiction"),
        (True, 21, "event-driven:support-1"),
        (True, 22, "event-driven:support-2"),
        (True, 23, "event-driven:support-3"),
        (True, 24, "event-driven:support-4"),
    )
    emissions = [
        authority.consume(_open_mint(
            authority,
            outcome=outcome,
            fullmove=fullmove,
            frame_id=frame_id,
        )[2])
        for outcome, fullmove, frame_id in first_sequence
    ]
    assert emissions[-1].graph_specialization_request_ids == (PARENT_ID,)
    assert not any(
        state.hypothesis.specialization_depth == 1
        for state in authority.states.values()
    )
    boundary = authority.settle_pending_structural_requests()
    assert boundary is not None and boundary.event_frontier == 9
    child_id = next(
        cell_id for cell_id, state in authority.states.items()
        if state.hypothesis.specialization_depth == 1
    )
    child = authority.states[child_id]
    assert (
        child.support,
        child.successes,
        child.contradictions,
        child.prospectively_certified,
    ) == (0, 0, 0, False)

    _opened, contradiction = _consume(
        authority,
        outcome=False,
        fullmove=40,
        frame_id="event-driven:child-contradiction",
        fen_template=ADVERSARIAL[AvailabilityState.AVAILABLE],
    )
    assert contradiction.graph_specialization_request_ids == ()
    for index, fullmove in enumerate(range(41, 45)):
        _opened, emission = _consume(
            authority,
            outcome=True,
            fullmove=fullmove,
            frame_id=f"event-driven:child-support-{index}",
        )
    assert emission.graph_specialization_request_ids == (child_id,)
    assert not any(
        state.hypothesis.specialization_depth == 2
        for state in authority.states.values()
    )
    assert (
        authority.states[child_id].successes,
        authority.states[child_id].contradictions,
    ) == (4, 1)

    second_boundary = authority.settle_pending_structural_requests()
    assert second_boundary is not None
    assert second_boundary.event_frontier == 14
    grandchild = next(
        state for state in authority.states.values()
        if state.hypothesis.specialization_depth == 2
    )
    assert grandchild.hypothesis.specialization_depth == (
        authority.states[child_id].hypothesis.specialization_depth + 1
    )
    assert (
        grandchild.support,
        grandchild.successes,
        grandchild.contradictions,
        grandchild.prospectively_certified,
    ) == (0, 0, 0, False)
    authority.verify_full_history_boundary("event-driven recursive reclosure")


def test_event_driven_settlement_is_frontier_selected_and_atomic(
    monkeypatch,
):
    authority = _mixed_authority(
        AvailabilityState.AVAILABLE,
        structural_mode=StructuralMode.EVENT_DRIVEN,
    )
    before = authority.continuation_digest()
    assert authority.settle_pending_structural_requests() is None
    assert authority.continuation_digest() == before

    sequence = (
        (False, 50, "event-atomic:contradiction"),
        (True, 51, "event-atomic:support-1"),
        (True, 52, "event-atomic:support-2"),
        (True, 53, "event-atomic:support-3"),
        (True, 54, "event-atomic:support-4"),
    )
    for outcome, fullmove, frame_id in sequence:
        _consume(
            authority,
            outcome=outcome,
            fullmove=fullmove,
            frame_id=frame_id,
        )
    before_failure = authority.continuation_digest()
    with monkeypatch.context() as scoped:
        scoped.setattr(
            authority_module,
            "_executed_authority_topology_manifest",
            lambda _states: (_ for _ in ()).throw(
                RuntimeError("injected topology failure")
            ),
        )
        with pytest.raises(RuntimeError, match="injected topology failure"):
            authority.settle_pending_structural_requests()
    assert authority.continuation_digest() == before_failure
    assert not any(
        state.hypothesis.specialization_depth == 1
        for state in authority.states.values()
    )

    deepcopy_calls = 0
    topology_calls = 0
    verify_calls = 0
    original_deepcopy = authority_module.copy.deepcopy
    original_topology = authority_module._executed_authority_topology_manifest
    original_verify = NativeProspectiveAuthorityV2._verify_invariants

    def counted_deepcopy(value, memo=None):
        nonlocal deepcopy_calls
        if isinstance(value, NativeProspectiveAuthorityV2):
            deepcopy_calls += 1
        return original_deepcopy(value, memo)

    def counted_topology(states):
        nonlocal topology_calls
        topology_calls += 1
        return original_topology(states)

    def counted_verify(self, *args, **kwargs):
        nonlocal verify_calls
        verify_calls += 1
        return original_verify(self, *args, **kwargs)

    monkeypatch.setattr(authority_module.copy, "deepcopy", counted_deepcopy)
    monkeypatch.setattr(
        authority_module,
        "_executed_authority_topology_manifest",
        counted_topology,
    )
    monkeypatch.setattr(
        NativeProspectiveAuthorityV2, "_verify_invariants", counted_verify
    )
    boundary = authority.settle_pending_structural_requests()
    assert boundary is not None and boundary.event_frontier == 9
    assert deepcopy_calls == 0
    assert topology_calls == 1
    assert verify_calls == 0


def test_event_driven_boundary_promotion_is_zero_authority_and_prospective():
    authority = _mixed_authority(
        AvailabilityState.AVAILABLE,
        structural_mode=StructuralMode.EVENT_DRIVEN,
    )
    receipts = tuple(
        _consume(
            authority,
            outcome=True,
            fullmove=110 + index,
            frame_id=f"ordinary-boundary:support-{index}",
        )[0][2].receipt_id
        for index in range(4)
    )
    request = _ordinary_boundary_request(
        authority,
        receipts,
        candidate_id="ordinary-boundary-candidate",
    )
    states_before = set(authority.states)
    boundary = authority.settle_pending_structural_requests((request,))
    assert boundary is not None
    child_id = next(iter(set(authority.states) - states_before))
    child = authority.states[child_id]
    assert child.hypothesis.nomination_operation == "ordinary"
    assert child.hypothesis.lineage_parent_id is None
    assert child.hypothesis.specialization_depth == 0
    assert child.hypothesis.dormant_origin is (
        DormantOrigin.ADAPTIVE_BOUNDARY_CHILD
    )
    assert child.hypothesis.source_generation == 1
    assert (
        child.support,
        child.successes,
        child.contradictions,
        child.prospectively_certified,
    ) == (0, 0, 0, False)
    assert set(child.hypothesis.discovery_exclusion_receipt_ids) == set(
        authority.accepted_real_references
    )

    # Discovery support cannot certify the child.  Only later REAL evidence
    # can close its prospective gate.
    for index in range(4):
        _consume(
            authority,
            outcome=True,
            fullmove=120 + index,
            frame_id=f"ordinary-boundary:prospective-{index}",
        )
    assert authority.states[child_id].prospectively_certified
    authority.verify_full_history_boundary("ordinary boundary promotion")
    restored = NativeProspectiveAuthorityV2.loads(authority.dumps())
    assert restored.continuation_manifest() == authority.continuation_manifest()


def test_boundary_promotion_rejects_incomplete_reads_atomically():
    authority = _mixed_authority(
        AvailabilityState.AVAILABLE,
        structural_mode=StructuralMode.EVENT_DRIVEN,
    )
    receipts = tuple(
        _consume(
            authority,
            outcome=True,
            fullmove=130 + index,
            frame_id=f"ordinary-boundary-invalid:support-{index}",
        )[0][2].receipt_id
        for index in range(4)
    )
    valid = _ordinary_boundary_request(
        authority,
        receipts,
        candidate_id="ordinary-boundary-invalid",
    )
    invalid = BoundaryPromotionRequest(
        candidate_id=valid.candidate_id,
        members=valid.members,
        fixed_polarity=valid.fixed_polarity,
        triggering_receipt_id=valid.triggering_receipt_id,
        supporting_receipt_ids=valid.supporting_receipt_ids,
        inspected_receipt_ids=valid.inspected_receipt_ids[:-1],
        source_generation=valid.source_generation,
    )
    before = authority.continuation_digest()
    with pytest.raises(
        ProspectiveV2IntegrityError,
        match="inspected reads are incomplete",
    ):
        authority.settle_pending_structural_requests((invalid,))
    assert authority.continuation_digest() == before
    assert valid.candidate_id not in authority.boundary_promotion_requests


def test_boundary_sketch_may_survive_unrelated_atomic_commit():
    authority = _mixed_authority(
        AvailabilityState.AVAILABLE,
        structural_mode=StructuralMode.EVENT_DRIVEN,
    )
    receipts = tuple(
        _consume(
            authority,
            outcome=True,
            fullmove=140 + index,
            frame_id=f"ordinary-boundary-cross-generation:{index}",
        )[0][2].receipt_id
        for index in range(4)
    )
    first = _ordinary_boundary_request(
        authority,
        receipts,
        candidate_id="ordinary-boundary-first",
        member_index=0,
    )
    authority.settle_pending_structural_requests((first,))
    digest_after_first = authority.continuation_digest()
    assert authority.settle_pending_structural_requests((first,)) is None
    assert authority.continuation_digest() == digest_after_first

    # The second sketch was born from the same earlier evidence, but commits
    # in the new generation.  A content-blind safe point must not invalidate
    # an otherwise complete local ledger.
    second = _ordinary_boundary_request(
        authority,
        receipts,
        candidate_id="ordinary-boundary-second",
        member_index=1,
    )
    assert second.source_generation == 1
    boundary = authority.settle_pending_structural_requests((second,))
    assert boundary is not None
    assert second.candidate_id in authority.boundary_promotion_requests
    authority.verify_full_history_boundary(
        "ordinary boundary cross-generation survival"
    )


def test_multiple_local_promotions_share_one_atomic_safe_point():
    authority = _mixed_authority(
        AvailabilityState.AVAILABLE,
        structural_mode=StructuralMode.EVENT_DRIVEN,
    )
    receipts = tuple(
        _consume(
            authority,
            outcome=True,
            fullmove=150 + index,
            frame_id=f"ordinary-boundary-batch:{index}",
        )[0][2].receipt_id
        for index in range(4)
    )
    requests = tuple(
        _ordinary_boundary_request(
            authority,
            receipts,
            candidate_id=f"ordinary-boundary-batch-{index}",
            member_index=index,
        )
        for index in range(2)
    )
    states_before = set(authority.states)
    boundaries_before = len(authority.generation_boundaries)
    boundary = authority.settle_pending_structural_requests(requests)
    assert boundary is not None
    assert authority.current_generation == 1
    assert len(authority.generation_boundaries) - boundaries_before == 3
    assert len(set(authority.states) - states_before) == 2
    assert set(authority.boundary_promotion_requests) == {
        item.candidate_id for item in requests
    }
    authority.verify_full_history_boundary("ordinary boundary batch")


def test_curriculum_path_commits_local_bud_only_at_post_real_safe_point():
    authority = _mixed_authority(
        AvailabilityState.AVAILABLE,
        structural_mode=StructuralMode.EVENT_DRIVEN,
    )
    ecology = ProspectiveBoundaryCandidateEcology()
    seen: set[str] = set()
    structurals = []
    for index in range(4):
        available, response, duplicate, structural = (
            _v2_r0_observe_training_successor(
                authority,
                _board(True, 160 + index),
                seen_predecessor_fens=seen,
                frame_id=f"curriculum-boundary:{index}",
                boundary_ecology=ecology,
            )
        )
        assert not duplicate
        assert response["boundary_ecology"]["observed_outcome"] is True
        assert available is False
        structurals.append(structural)

    committed = [item for item in structurals if item is not None]
    assert len(committed) == 1
    assert committed[0]["mode"] == StructuralMode.EVENT_DRIVEN.value
    assert committed[0]["safe_point"] == "post_consumption_quiescent_real"
    assert committed[0]["safe_point_content_blind"] is True
    assert len(committed[0]["promotion_candidate_ids"]) == 1
    assert len(authority.boundary_promotion_requests) == 1
    adaptive_children = [
        state for state in authority.states.values()
        if state.hypothesis.dormant_origin
        is DormantOrigin.ADAPTIVE_BOUNDARY_CHILD
    ]
    assert len(adaptive_children) == 1
    assert adaptive_children[0].support == 0
    assert not adaptive_children[0].prospectively_certified
    assert len(ecology.observations) == 4
    assert sum(
        item.retirement_reason == "promoted"
        for item in ecology.tombstones.values()
    ) == 1


def test_scheduled_structural_mode_remains_explicitly_backward_compatible():
    authority = _mixed_authority(AvailabilityState.AVAILABLE)
    assert authority.structural_mode is StructuralMode.SCHEDULED
    with pytest.raises(
        ProspectiveV2IntegrityError,
        match="event-driven settlement requires event-driven",
    ):
        authority.settle_pending_structural_requests()


def test_adaptive_boundary_child_reopens_only_on_postbirth_real_evidence():
    authority = _mixed_authority(
        AvailabilityState.AVAILABLE,
        structural_mode=StructuralMode.EVENT_DRIVEN,
    )
    discovery_receipts = tuple(
        _consume(
            authority,
            outcome=True,
            fullmove=180 + index,
            frame_id=f"adaptive-recursive:discovery:{index}",
        )[0][2].receipt_id
        for index in range(4)
    )
    request = _ordinary_boundary_request(
        authority,
        discovery_receipts,
        candidate_id="adaptive-recursive-boundary",
    )
    authority.settle_pending_structural_requests((request,))
    child_id = next(
        cell_id for cell_id, state in authority.states.items()
        if state.hypothesis.dormant_origin
        is DormantOrigin.ADAPTIVE_BOUNDARY_CHILD
    )
    child = authority.states[child_id]
    assert child.support == 0
    assert child.hypothesis.discovery_support_receipt_ids
    assert set(child.hypothesis.discovery_exclusion_receipt_ids) == set(
        authority.accepted_real_references
    )

    contradiction_opened, contradiction_emission = _consume(
        authority,
        outcome=False,
        fullmove=190,
        frame_id="adaptive-recursive:postbirth-contradiction",
        fen_template=ADVERSARIAL[AvailabilityState.AVAILABLE],
    )
    selected_identity = child.hypothesis.members[0]
    assert selected_identity in contradiction_opened[1].ordered_signal_identities
    assert contradiction_emission.graph_specialization_request_ids == (
        PARENT_ID,
    )

    postbirth_support_receipts = []
    for index, fullmove in enumerate(range(191, 195)):
        opened, emission = _consume(
            authority,
            outcome=True,
            fullmove=fullmove,
            frame_id=f"adaptive-recursive:postbirth-support:{index}",
        )
        postbirth_support_receipts.append(opened[2])
        if index < 3:
            # Four discovery supports do not count toward the child's
            # prospective trigger; three post-birth supports are still short.
            assert emission.graph_specialization_request_ids == ()

    assert emission.graph_specialization_request_ids == (child_id,)
    request_id = emission.request_queue_appended_ids[0]
    recursive_request = authority.deferred_requests[request_id]
    assert recursive_request.parent_cell_id == child_id
    assert recursive_request.request_basis is RequestBasis.UNCERTIFIED_MIXED_EVIDENCE
    assert recursive_request.request_emission_receipt_id == (
        postbirth_support_receipts[-1].receipt_id
    )
    assert recursive_request.contradiction_receipt_id == contradiction_opened[2].receipt_id
    assert recursive_request.parent_prospective_support_receipt_ids == tuple(
        sorted(item.receipt_id for item in postbirth_support_receipts)
    )
    assert not set(recursive_request.parent_prospective_support_receipt_ids).intersection(
        child.hypothesis.discovery_exclusion_receipt_ids
    )
    authority.verify_full_history_boundary(
        "adaptive child recursive postbirth evidence"
    )


def test_shared_successor_capacity_fails_before_mutation_when_all_parents_live(
    monkeypatch,
):
    monkeypatch.setattr(
        authority_module,
        "DORMANT_SPECIALIZATION_CHILD_CAPACITY",
        2,
    )
    authority = _mixed_authority(
        AvailabilityState.AVAILABLE,
        structural_mode=StructuralMode.EVENT_DRIVEN,
    )
    first_receipts = tuple(
        _consume(
            authority,
            outcome=True,
            fullmove=200 + index,
            frame_id=f"capacity:first-promotion:{index}",
        )[0][2].receipt_id
        for index in range(4)
    )
    first_promotion = _ordinary_boundary_request(
        authority,
        first_receipts,
        candidate_id="capacity-first-promotion",
    )
    authority.settle_pending_structural_requests((first_promotion,))
    assert len(authority._successor_capacity_occupants()) == 1

    _opened, revocation = _consume(
        authority,
        outcome=False,
        fullmove=204,
        frame_id="capacity:deferred-revocation",
    )
    deferred_id = revocation.request_queue_appended_ids[0]
    second_receipts = tuple(
        _consume(
            authority,
            outcome=True,
            fullmove=205 + index,
            frame_id=f"capacity:second-promotion:{index}",
        )[0][2].receipt_id
        for index in range(4)
    )
    second_promotion = _ordinary_boundary_request(
        authority,
        second_receipts,
        candidate_id="capacity-second-promotion",
        member_index=1,
    )

    # Two deferred requests are pending: the first belongs to the core and
    # the second belongs to the existing adaptive child.  Both parents are
    # protected, so there is no legal leaf to retire for the incoming
    # promotion plus both concrete deferred proposals.  Capacity failure is
    # raised before any request, promotion, or retirement mutates the
    # authority; the queue remains retryable.
    before = authority.continuation_manifest()
    with pytest.raises(
        ProspectiveV2IntegrityError,
        match="successor capacity requires",
    ):
        authority.settle_pending_structural_requests((second_promotion,))
    assert authority.continuation_manifest() == before
    assert deferred_id in authority._pending_request_ids()
    assert "capacity-second-promotion" not in authority.boundary_promotion_requests
    assert not authority.retired_tombstones
    assert len(authority._successor_capacity_occupants()) == 1
    authority.verify_full_history_boundary("shared successor capacity")


def test_deferred_reservation_and_materialization_share_one_capacity_slot(
    monkeypatch,
):
    monkeypatch.setattr(
        authority_module,
        "DORMANT_SPECIALIZATION_CHILD_CAPACITY",
        1,
    )
    authority = _mixed_authority(
        AvailabilityState.AVAILABLE,
        structural_mode=StructuralMode.EVENT_DRIVEN,
    )
    sequence = (
        (False, 220, "deferred-slot:contradiction"),
        (True, 221, "deferred-slot:support-1"),
        (True, 222, "deferred-slot:support-2"),
        (True, 223, "deferred-slot:support-3"),
        (True, 224, "deferred-slot:support-4"),
    )
    emissions = [
        authority.consume(_open_mint(
            authority,
            outcome=outcome,
            fullmove=fullmove,
            frame_id=frame_id,
        )[2])
        for outcome, fullmove, frame_id in sequence
    ]
    request_id = emissions[-1].request_queue_appended_ids[0]
    boundary = authority.settle_pending_structural_requests()
    assert boundary is not None
    consumption = authority.request_consumptions[request_id]
    assert consumption.disposition == "MATERIALIZED"
    assert len(authority.deferred_child_births) == 1
    assert len(authority._successor_capacity_occupants()) == 1
    assert sum(
        state.hypothesis.source_generation > 0
        for state in authority.states.values()
    ) == 1
    authority.verify_full_history_boundary(
        "deferred reservation materialization shared slot"
    )


def _authority_with_one_pending_compact_request(
) -> tuple[NativeProspectiveAuthorityV2, str]:
    authority = _mixed_authority(
        AvailabilityState.AVAILABLE,
        structural_mode=StructuralMode.EVENT_DRIVEN,
    )
    sequence = (
        (False, 800, "commitment:contradiction"),
        (True, 801, "commitment:support-1"),
        (True, 802, "commitment:support-2"),
        (True, 803, "commitment:support-3"),
        (True, 804, "commitment:support-4"),
    )
    emissions = tuple(
        _consume(
            authority,
            outcome=outcome,
            fullmove=fullmove,
            frame_id=frame_id,
        )[1]
        for outcome, fullmove, frame_id in sequence
    )
    return authority, emissions[-1].request_queue_appended_ids[0]


def _replace_pending_request(
    authority: NativeProspectiveAuthorityV2,
    old_request_id: str,
    forged,
) -> str:
    draft = replace(
        forged,
        request_id="UNBOUND_V7_SPECIALIZATION_REQUEST",
    )
    new_request_id = authority_module._sha({
        "kind": "V2_GRAPH_SPECIALIZATION_REQUEST_V7",
        "request": draft.identity_manifest(),
    })
    forged = replace(draft, request_id=new_request_id)
    authority.deferred_requests = {new_request_id: forged}
    authority.request_queue = type(authority.request_queue)((new_request_id,))
    authority._pending_request_order = [new_request_id]
    authority._pending_request_index = {new_request_id}
    emission_id = forged.request_emission_receipt_id
    emission = authority.emissions[emission_id]
    authority.emissions[emission_id] = replace(
        emission,
        request_queue_appended_ids=(new_request_id,),
        candidate_terminal_states=((
            forged.parent_cell_id,
            forged.candidate_terminals,
        ),),
    )
    return new_request_id


def test_compact_request_parent_query_is_recomputed_not_format_checked() -> None:
    authority, request_id = _authority_with_one_pending_compact_request()
    request = authority.deferred_requests[request_id]
    forged = replace(request, parent_query_commitment="0" * 64)
    _replace_pending_request(authority, request_id, forged)

    with pytest.raises(
        ProspectiveV2IntegrityError,
        match="parent query commitment mismatch",
    ):
        authority._verify_deferred_specialization_requests(
            reconstruct_evidence=False
        )


def test_compact_candidate_inspected_commitment_is_reconstructed() -> None:
    authority, request_id = _authority_with_one_pending_compact_request()
    request = authority.deferred_requests[request_id]
    assert request.candidate_inspected_commitment is not None
    forged = replace(
        request,
        candidate_inspected_commitment=replace(
            request.candidate_inspected_commitment,
            digest="0" * 64,
        ),
    )
    _replace_pending_request(authority, request_id, forged)

    with pytest.raises(
        ProspectiveV2IntegrityError,
        match="inspected commitment mismatch",
    ):
        authority._verify_deferred_specialization_requests(
            reconstruct_evidence=True
        )
