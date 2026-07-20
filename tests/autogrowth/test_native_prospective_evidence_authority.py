from __future__ import annotations

import copy

import chess
import pytest

from recon_lite import FrameContext, FrameKind
from recon_lite_chess.autogrowth.native_authority_lab import (
    NativeAuthorityLabConfig,
    load_retired_r0_build,
)
from recon_lite_chess.autogrowth.native_competence_envelope import (
    AvailabilityState,
    CompetenceContextCell,
    CompetenceEnvelopeConfig,
    SpecializationMode,
)
from recon_lite_chess.autogrowth.native_prospective_evidence_authority import (
    CertificationMode,
    CertificationStatus,
    NativeProspectiveCompetenceOrganism,
    ProspectiveCellCertification,
    ProspectiveCertificationConfig,
    ProspectiveEvidenceAuthority,
    SyntheticReceiptIssuer,
    ValidatedCertificationEvent,
    synthetic_prediction,
)
from recon_lite_chess.autogrowth.native_trace_competence_authority import (
    TraceNativeCompetenceOrganism,
    TraceNativeLearningConfig,
)
from recon_lite_hector.nodes import StemCellState, StemCellTerminal


def _state(
    cell_id: str = "candidate",
    members: tuple[str, ...] = ("p0", "p1"),
    *,
    frontier: int = 3,
) -> ProspectiveCellCertification:
    return ProspectiveCellCertification(
        cell_id=cell_id,
        members=members,
        polarity=AvailabilityState.AVAILABLE,
        lineage_parent_id=None,
        specialization_depth=0,
        birth_event_ordinal=3,
        certification_frontier=frontier,
        proposal_receipt_ids=("proposal-3",),
        discovery_receipt_ids=("d0", "d1", "d2", "proposal-3"),
        discovery_support=4,
        discovery_successes=4,
        discovery_failures=0,
        discovery_success_lower_bound=0.568,
        discovery_failure_lower_bound=0.0,
    )


def _event(issuer: SyntheticReceiptIssuer, ordinal: int, outcome: bool = True):
    receipt = issuer.mint(
        event_ordinal=ordinal,
        active_signal_ids=("p0", "p1", "noise"),
        observed_outcome=outcome,
    )
    return receipt, issuer.validate(receipt)


def test_prospective_requires_prediction_and_four_post_frontier_receipts() -> None:
    issuer = SyntheticReceiptIssuer()
    state = _state()
    authority = ProspectiveEvidenceAuthority(
        ProspectiveCertificationConfig(CertificationMode.PROSPECTIVE),
        {state.cell_id: state},
    )
    first_receipt, first_event = _event(issuer, 4)
    with pytest.raises(RuntimeError, match="prior REAL prediction"):
        authority.consume(first_event)

    assert authority.deficit_manifest()["rows"][0]["deficit"] == 4
    for ordinal in range(4, 8):
        receipt, event = _event(issuer, ordinal)
        prediction = synthetic_prediction(authority, receipt)
        assert prediction.emitted_before_outcome
        assert prediction.classification.state is AvailabilityState.UNKNOWN
        emission = authority.consume(event)
        assert emission.certified_cell_ids == ("candidate",)
        if ordinal < 7:
            assert not emission.matured_cell_ids
            assert state.status is CertificationStatus.PROVISIONAL
        else:
            assert emission.matured_cell_ids == ("candidate",)
            assert state.status is CertificationStatus.MATURE

    assert state.prospective_successes == 4
    assert state.prospective_contradictions == 0
    assert state.maturity_receipt_id is not None
    assert set(state.certification_receipt_ids).isdisjoint(
        state.discovery_receipt_ids
    )
    assert authority.deficit_manifest()["rows"][0]["deficit"] == 0

    before = authority.to_manifest()
    duplicate = authority.consume(first_event)
    assert duplicate == authority.emissions[first_event.receipt_id]
    assert authority.to_manifest() == before


def test_pre_frontier_proposal_and_virtual_events_cannot_certify() -> None:
    issuer = SyntheticReceiptIssuer()
    state = _state(frontier=4)
    authority = ProspectiveEvidenceAuthority(
        ProspectiveCertificationConfig(CertificationMode.PROSPECTIVE),
        {state.cell_id: state},
    )
    receipt, event = _event(issuer, 4)
    synthetic_prediction(authority, receipt)
    emission = authority.consume(event)
    assert emission.excluded_cell_ids == ("candidate",)
    assert state.prospective_support == 0

    before = authority.to_manifest()
    virtual = authority.predict(
        trace_identity="virtual",
        active_signal_ids=("p0", "p1"),
        policy_response=True,
        frame_kind=FrameKind.VIRTUAL,
    )
    assert virtual.frame_kind == FrameKind.VIRTUAL.name
    assert not authority.pending_predictions
    assert authority.to_manifest() == before

    bad = ValidatedCertificationEvent(
        receipt_id="virtual-receipt",
        event_ordinal=5,
        trace_identity="virtual",
        active_signal_ids=("p0", "p1"),
        observed_outcome=True,
        frame_kind=FrameKind.VIRTUAL.name,
        grounded_provenance="none",
    )
    with pytest.raises(ValueError, match="virtual"):
        authority.consume(bad)


def test_later_contradiction_revokes_mature_authority() -> None:
    issuer = SyntheticReceiptIssuer()
    state = _state()
    authority = ProspectiveEvidenceAuthority(
        ProspectiveCertificationConfig(CertificationMode.PROSPECTIVE),
        {state.cell_id: state},
    )
    for ordinal in range(4, 8):
        receipt, event = _event(issuer, ordinal, True)
        synthetic_prediction(authority, receipt)
        authority.consume(event)
    assert state.status is CertificationStatus.MATURE

    receipt, event = _event(issuer, 8, False)
    prediction = synthetic_prediction(authority, receipt)
    assert prediction.classification.state is AvailabilityState.AVAILABLE
    emission = authority.consume(event)
    assert emission.revoked_cell_ids == ("candidate",)
    assert state.status is CertificationStatus.REVOKED
    assert state.revocation_receipt_id == receipt.event_id
    assert state.transitions[-1].transition == "MATURE_TO_REVOKED"


def test_legacy_same_ledger_self_certifies_but_prospective_does_not() -> None:
    issuer = SyntheticReceiptIssuer()
    events = []
    for ordinal in range(4):
        receipt = issuer.mint(
            event_ordinal=ordinal,
            active_signal_ids=("p0", "p1"),
            observed_outcome=True,
        )
        events.append(issuer.validate(receipt))

    legacy_state = _state()
    legacy = ProspectiveEvidenceAuthority(
        ProspectiveCertificationConfig(CertificationMode.LEGACY_SAME_LEDGER),
        {legacy_state.cell_id: legacy_state},
    )
    assert legacy.legacy_certify(events) == ("candidate",)
    assert legacy_state.status is CertificationStatus.MATURE

    prospective_state = _state()
    prospective = ProspectiveEvidenceAuthority(
        ProspectiveCertificationConfig(CertificationMode.PROSPECTIVE),
        {prospective_state.cell_id: prospective_state},
    )
    assert prospective_state.status is CertificationStatus.PROVISIONAL
    assert prospective_state.prospective_support == 0


@pytest.fixture(scope="module")
def r0():
    return load_retired_r0_build(NativeAuthorityLabConfig()).organism


def _source_with_one_cell(r0):
    config = CompetenceEnvelopeConfig(selection_seed=271828)
    source = TraceNativeCompetenceOrganism.empty(
        r0,
        envelope_config=config,
        learning_config=TraceNativeLearningConfig(
            lifecycle_connected=True,
            specialization_mode=SpecializationMode.DISCONNECTED,
            genome_seed=config.selection_seed,
        ),
    )
    build = load_retired_r0_build(NativeAuthorityLabConfig())
    selected = None
    for index, fen in enumerate(build.pools.r0_train):
        board = chess.Board(fen)
        frame = FrameContext(
            f"prospective-source:{index}", FrameKind.REAL, values={"board": board}
        )
        actuation, trace = source.r0.emit_action_with_trace(frame)
        if actuation is None or trace is None:
            continue
        successor = board.copy(stack=False)
        successor.push(chess.Move.from_uci(actuation.move_uci))
        if successor.is_checkmate():
            selected = (board, trace, successor)
            break
    assert selected is not None
    board, trace, successor = selected
    member = next(
        identity for identity in trace.ordered_signal_identities
        if identity != "internal:policy_response"
    )
    stem = StemCellTerminal("prospective_test_cell")
    stem.state = StemCellState.MATURE
    stem.trial_node_id = "prospective_test_cell"
    stem.trial_parent_id = "competence_available_root"
    cell = CompetenceContextCell(
        cell_id="prospective_test_cell",
        members=(member,),
        born_round=0,
        born_request_ordinal=0,
        stem_cell=stem,
        polarity=AvailabilityState.AVAILABLE,
        evidence_keys=("discovery",),
        successes=4,
        support=4,
        success_lower_bound=0.568,
        conservative_success_estimate=0.568,
        uncertainty=0.432,
    )
    source.envelope.cells[cell.cell_id] = cell
    source.envelope._member_specs.add(cell.members)
    source.envelope.rebuild_graph()
    return source, board, trace, successor


def test_native_prediction_receipt_serialization_and_dream_isolation(r0) -> None:
    source, board, _trace, _successor = _source_with_one_cell(r0)
    organism = NativeProspectiveCompetenceOrganism.from_frozen_patterns(
        source,
        config=ProspectiveCertificationConfig(CertificationMode.PROSPECTIVE),
        certification_frontier=-1,
        reset_historical_authority=True,
    )
    assert organism.authority.cells["prospective_test_cell"].status is CertificationStatus.PROVISIONAL
    terminal = organism.base.completion_terminal()
    for ordinal in range(4):
        frame = FrameContext(
            f"prospective-real:{ordinal}", FrameKind.REAL, values={"board": board}
        )
        actuation, trace = organism.base.r0.emit_action_with_trace(frame)
        assert actuation is not None and trace is not None
        successor = board.copy(stack=False)
        successor.push(chess.Move.from_uci(actuation.move_uci))
        organism.predict_real_trace(trace)
        receipt = terminal.mint(trace, board, successor)
        organism.observe_grounded(receipt)
    assert organism.authority.cells["prospective_test_cell"].status is CertificationStatus.MATURE
    assert organism.base.envelope.cells["prospective_test_cell"].is_mature

    for cell_id, members, parent_id, depth in (
        ("new_ordinary", ("new:ordinary",), None, 0),
        (
            "new_specialization",
            ("context:prospective_test_cell", "new:contrast"),
            "prospective_test_cell",
            1,
        ),
    ):
        stem = StemCellTerminal(cell_id)
        stem.state = StemCellState.MATURE
        stem.trial_node_id = cell_id
        stem.trial_parent_id = "competence_available_root"
        cell = CompetenceContextCell(
            cell_id=cell_id,
            members=members,
            born_round=9,
            born_request_ordinal=9,
            stem_cell=stem,
            polarity=AvailabilityState.AVAILABLE,
            evidence_keys=(f"discovery:{cell_id}",),
            successes=4,
            support=4,
            success_lower_bound=0.568,
            conservative_success_estimate=0.568,
            uncertainty=0.432,
            lineage_parent_id=parent_id,
            specialization_depth=depth,
        )
        organism.base.envelope.cells[cell_id] = cell
        organism.base.envelope._member_specs.add(cell.members)
    organism.base.envelope.rebuild_graph()
    assert organism.register_new_cells(certification_frontier=10) == (
        "new_ordinary", "new_specialization"
    )
    for cell_id in ("new_ordinary", "new_specialization"):
        state = organism.authority.cells[cell_id]
        assert state.status is CertificationStatus.PROVISIONAL
        assert state.prospective_support == 0
        assert state.certification_frontier == 10
        assert organism.base.envelope.cells[cell_id].state is StemCellState.TRIAL
    assert organism.authority.cells["new_specialization"].specialization_depth == 1
    assert organism.authority.cells["new_specialization"].lineage_parent_id == (
        "prospective_test_cell"
    )

    restored = NativeProspectiveCompetenceOrganism.loads(organism.dumps())
    assert restored.continuation_manifest() == organism.continuation_manifest()
    before = restored.continuation_digest()
    session = restored.dream_session()
    result = session.request(FrameContext(
        "prospective-virtual", FrameKind.VIRTUAL, values={"board": board}
    ))
    session.close()
    assert result["certification_support_added"] == 0
    assert restored.continuation_digest() == before
