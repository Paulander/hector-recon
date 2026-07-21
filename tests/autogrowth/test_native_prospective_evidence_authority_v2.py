from __future__ import annotations

import copy
from dataclasses import replace
import hashlib
import hmac
import json

import chess
import pytest

from recon_lite import FrameContext, FrameKind
from recon_lite_hector.nodes import StemCellState, StemCellTerminal
from recon_lite_chess.autogrowth.native_authority_lab import NativeAuthorityLabConfig, load_retired_r0_build
from recon_lite_chess.autogrowth.native_competence_envelope import (
    AvailabilityState, CompetenceContextCell, CompetenceEnvelopeConfig,
    SpecializationMode,
)
from recon_lite_chess.autogrowth.native_prospective_evidence_authority_v2 import (
    FrozenHypothesis, NativeProspectiveAuthorityV2, OutcomeBlindExposureScanner,
    ProspectiveProvenanceUnavailable, ProspectiveV2IntegrityError, V2Mode,
)
from recon_lite_chess.autogrowth.native_trace_competence_authority import (
    TraceNativeCompetenceOrganism, TraceNativeLearningConfig,
)


def _canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()


def _resign(organism, receipt):
    return replace(
        receipt,
        signature=hmac.new(
            organism._receipt_secret, _canonical(receipt.unsigned_manifest()),
            hashlib.sha256,
        ).hexdigest(),
    )


def _atomic_abort(organism, pattern, operation):
    before = organism.continuation_digest()
    with pytest.raises((ProspectiveV2IntegrityError, ProspectiveProvenanceUnavailable), match=pattern):
        operation()
    assert organism.continuation_digest() == before


@pytest.fixture(scope="module")
def native_fixture():
    build = load_retired_r0_build(NativeAuthorityLabConfig())
    config = CompetenceEnvelopeConfig(selection_seed=271828)
    source = TraceNativeCompetenceOrganism.empty(
        build.organism,
        envelope_config=config,
        learning_config=TraceNativeLearningConfig(
            lifecycle_connected=False,
            specialization_mode=SpecializationMode.DISCONNECTED,
            genome_seed=config.selection_seed,
        ),
    )
    accepted = []
    later = []
    terminal = source.completion_terminal()
    for index, fen in enumerate(build.pools.r0_train):
        board = chess.Board(fen)
        frame = FrameContext(f"v2-fixture:{index}", FrameKind.REAL, values={"board": board})
        actuation, trace = source.r0.emit_action_with_trace(frame)
        if actuation is None or trace is None:
            continue
        successor = board.copy(stack=False)
        successor.push(chess.Move.from_uci(actuation.move_uci))
        if not successor.is_checkmate():
            continue
        if len(accepted) < 4:
            receipt = terminal.mint(trace, board, successor)
            _record, inserted = source._accept_receipt(receipt)
            assert inserted
            accepted.append((receipt, trace, board))
        else:
            later.append((fen, trace.ordered_signal_identities))
        if len(accepted) == 4 and len(later) >= 6:
            break
    assert len(accepted) == 4 and len(later) >= 6
    common = set(accepted[0][1].ordered_signal_identities)
    for _receipt, trace, _board in accepted[1:]:
        common.intersection_update(trace.ordered_signal_identities)
    member = sorted(common)[0]
    evidence_ids = tuple(sorted(item[0].event_id for item in accepted))

    parent_stem = StemCellTerminal("v2_parent")
    parent_stem.state = StemCellState.MATURE
    parent_stem.trial_node_id = "v2_parent"
    parent_stem.trial_parent_id = "competence_available_root"
    parent = CompetenceContextCell(
        cell_id="v2_parent", members=(member,), born_round=0,
        born_request_ordinal=0, stem_cell=parent_stem,
        polarity=AvailabilityState.AVAILABLE, evidence_keys=evidence_ids,
        successes=4, support=4, success_lower_bound=0.568,
    )
    child_stem = StemCellTerminal("v2_child")
    child_stem.state = StemCellState.MATURE
    child_stem.trial_node_id = "v2_child"
    child_stem.trial_parent_id = "competence_available_root"
    child = CompetenceContextCell(
        cell_id="v2_child", members=("context:v2_parent", member),
        born_round=1, born_request_ordinal=1, stem_cell=child_stem,
        polarity=AvailabilityState.AVAILABLE, evidence_keys=evidence_ids,
        successes=4, support=4, success_lower_bound=0.568,
        lineage_parent_id="v2_parent", specialization_depth=1,
        specialization_request_ordinal=1, specialization_proposal_ordinal=1,
    )
    source.envelope.cells = {parent.cell_id: parent, child.cell_id: child}
    source.envelope._member_specs = {parent.members, child.members}
    source.envelope.specialization_audit.request_rows.append({
        "admitted": True, "cell_id": child.cell_id,
        "evidence_key": accepted[0][0].event_id,
    })
    source.envelope.rebuild_graph()
    return source, tuple(fen for fen, _signals in later)


def _open_mint(organism, fen, *, frame_id="v2-real"):
    board = chess.Board(fen)
    pending, trace = organism.open_real_event(
        FrameContext(frame_id, FrameKind.REAL, values={"board": board})
    )
    successor = board.copy(stack=False)
    successor.push(chess.Move.from_uci(pending.actuation.move_uci))
    receipt = organism.mint_environment_receipt(
        pending_token=pending.pending_token, trace=trace,
        predecessor=board, successor=successor,
    )
    return pending, trace, receipt


def test_complete_hypothesis_and_uniform_structural_authority(native_fixture):
    source, fens = native_fixture
    source_before = source.continuation_digest_v3()
    prospective = NativeProspectiveAuthorityV2.from_organism(source, mode=V2Mode.PROSPECTIVE)
    legacy = NativeProspectiveAuthorityV2.from_organism(source, mode=V2Mode.LEGACY)
    assert source.continuation_digest_v3() == source_before
    prospective.assert_candidate_parity(legacy)
    assert prospective._structural_manifest() == legacy._structural_manifest()
    assert all(not state.prospectively_certified for state in prospective.states.values())
    assert all(state.prospectively_certified for state in legacy.states.values())
    parent = prospective.states["v2_parent"].hypothesis
    child = prospective.states["v2_child"].hypothesis
    assert set(parent.discovery_receipt_ids).issubset(child.discovery_receipt_ids)
    assert child.birth_frontier == max(item.event_ordinal for item in source.receipts.values())
    pp, pt = prospective.open_real_event(FrameContext("parity:p", FrameKind.REAL, values={"board": chess.Board(fens[0])}))
    lp, lt = legacy.open_real_event(FrameContext("parity:l", FrameKind.REAL, values={"board": chess.Board(fens[0])}))
    assert pp.actuation == lp.actuation
    assert pt.ordered_signal_identities == lt.ordered_signal_identities
    assert pp.matching_cell_ids == lp.matching_cell_ids
    assert pp.pre_outcome_classification.state is AvailabilityState.UNKNOWN
    assert lp.pre_outcome_classification.state is AvailabilityState.AVAILABLE
    assert prospective._structural_manifest() == legacy._structural_manifest()


def test_birth_polarity_frontier_and_provenance_fail_hard(native_fixture):
    source, _fens = native_fixture
    source_none = copy.deepcopy(source)
    source_none.envelope.cells["v2_parent"].polarity = None
    before = source_none.continuation_digest_v3()
    with pytest.raises(ProspectiveV2IntegrityError, match="polarity=None"):
        NativeProspectiveAuthorityV2.from_organism(source_none, mode=V2Mode.PROSPECTIVE)
    assert source_none.continuation_digest_v3() == before

    source_missing = copy.deepcopy(source)
    missing = source_missing.envelope.cells["v2_parent"].evidence_keys[0]
    del source_missing.receipts[missing]
    before = source_missing.continuation_digest_v3()
    with pytest.raises(ProspectiveProvenanceUnavailable, match="prospective_provenance_unavailable"):
        NativeProspectiveAuthorityV2.from_organism(source_missing, mode=V2Mode.PROSPECTIVE)
    assert source_missing.continuation_digest_v3() == before

    with pytest.raises(ProspectiveV2IntegrityError, match="runner-supplied frontier"):
        NativeProspectiveAuthorityV2.from_organism(
            source, mode=V2Mode.PROSPECTIVE, frontier=999
        )
    with pytest.raises(ProspectiveV2IntegrityError, match="polarity=None"):
        FrozenHypothesis(
            "bad", ("x",), None, None, 0, ("r",),
            hashlib.sha256(b'["r"]').hexdigest(), 0, "TRIAL",
        )


def test_real_transaction_pending_order_and_forbidden_scans(native_fixture):
    source, fens = native_fixture
    organism = NativeProspectiveAuthorityV2.from_organism(source, mode=V2Mode.PROSPECTIVE)
    pending, _trace, _receipt = _open_mint(organism, fens[0])
    _atomic_abort(organism, "exactly one pending", lambda: organism.open_real_event(
        FrameContext("second", FrameKind.REAL, values={"board": chess.Board(fens[1])})
    ))
    born = copy.deepcopy(organism.base.envelope.cells["v2_parent"])
    born.cell_id = "born_during_event"
    born.stem_cell = StemCellTerminal("born_during_event")
    born.stem_cell.state = StemCellState.TRIAL
    organism.base.envelope.cells[born.cell_id] = born
    _atomic_abort(
        organism, "candidate born during event",
        organism.sync_organism_nominations,
    )
    _atomic_abort(organism, "post-outcome matching", organism.match_after_outcome)
    _atomic_abort(organism, "retrospective ledger scan", organism.retrospective_certify)
    _atomic_abort(organism, "suffix nomination", organism.nominate_suffix)
    assert organism.pending_event == pending


def test_receipt_before_prediction_and_all_commitment_mismatches(native_fixture):
    source, fens = native_fixture
    maker = NativeProspectiveAuthorityV2.from_organism(source, mode=V2Mode.PROSPECTIVE)
    _pending, _trace, receipt = _open_mint(maker, fens[0])
    fresh = NativeProspectiveAuthorityV2.from_organism(source, mode=V2Mode.PROSPECTIVE)
    _atomic_abort(fresh, "receipt before prediction", lambda: fresh.consume(receipt))

    mutations = [
        ("out-of-order ordinal", lambda r: replace(r, ordinal=r.ordinal - 1)),
        ("out-of-order ordinal", lambda r: replace(r, ordinal=r.ordinal + 1)),
        ("wrong or consumed pending token", lambda r: replace(r, pending_token="wrong")),
        ("trace mismatch", lambda r: replace(r, trace=replace(r.trace, frame_id="altered"))),
        ("successor mismatch", lambda r: replace(r, successor_fen=chess.Board().fen())),
        ("outcome terminal mismatch", lambda r: replace(r, outcome_terminal_identity="wrong")),
    ]
    for index, (message, mutate) in enumerate(mutations):
        organism = NativeProspectiveAuthorityV2.from_organism(source, mode=V2Mode.PROSPECTIVE)
        _pending, _trace, valid = _open_mint(organism, fens[index % len(fens)], frame_id=f"mismatch:{index}")
        altered = _resign(organism, mutate(valid))
        _atomic_abort(organism, message, lambda altered=altered: organism.consume(altered))


def test_actuation_and_polarity_mutation_are_atomic(native_fixture):
    source, fens = native_fixture
    organism = NativeProspectiveAuthorityV2.from_organism(source, mode=V2Mode.PROSPECTIVE)
    _pending, _trace, receipt = _open_mint(organism, fens[0])
    changed_actuation = replace(receipt.selected_actuation, option_identity="changed")
    altered = _resign(organism, replace(receipt, selected_actuation=changed_actuation))
    _atomic_abort(organism, "actuation mismatch", lambda: organism.consume(altered))

    organism = NativeProspectiveAuthorityV2.from_organism(source, mode=V2Mode.PROSPECTIVE)
    pending, _trace, receipt = _open_mint(organism, fens[0])
    assert "v2_parent" in pending.matching_cell_ids
    organism.base.envelope.cells["v2_parent"].polarity = AvailabilityState.REFUTED
    _atomic_abort(organism, "polarity mutation", lambda: organism.consume(receipt))


def test_duplicate_remint_serialization_and_structural_invariance(native_fixture):
    source, fens = native_fixture
    organism = NativeProspectiveAuthorityV2.from_organism(source, mode=V2Mode.PROSPECTIVE)
    structural = organism._structural_manifest()
    _pending, _trace, receipt = _open_mint(organism, fens[0])
    open_restored = NativeProspectiveAuthorityV2.loads(organism.dumps())
    assert open_restored.continuation_manifest() == organism.continuation_manifest()
    assert open_restored.event_transactions[receipt.pending_token]["state"] == "OPEN"
    emission = organism.consume(receipt)
    assert organism._structural_manifest() == structural
    consumed_restored = NativeProspectiveAuthorityV2.loads(organism.dumps())
    assert consumed_restored.continuation_manifest() == organism.continuation_manifest()
    assert consumed_restored.event_transactions[receipt.pending_token]["state"] == "CONSUMED"
    born = copy.deepcopy(organism.base.envelope.cells["v2_parent"])
    born.cell_id = "organism_nominated"
    born.stem_cell = StemCellTerminal("organism_nominated")
    born.stem_cell.state = StemCellState.TRIAL
    organism.base.envelope.cells[born.cell_id] = born
    assert organism.sync_organism_nominations() == ("organism_nominated",)
    assert not organism.states["organism_nominated"].prospectively_certified
    assert organism.states["organism_nominated"].hypothesis.polarity is AvailabilityState.AVAILABLE
    before = organism.continuation_digest()
    assert organism.consume(receipt) == emission
    assert organism.continuation_digest() == before
    reminted = _resign(organism, replace(
        receipt, receipt_id="new-id", ordinal=receipt.ordinal + 1
    ))
    _atomic_abort(organism, "reminted interaction fingerprint", lambda: organism.consume(reminted))


def test_graph_maturity_after_four_distinct_post_frontier_receipts(native_fixture):
    source, fens = native_fixture
    organism = NativeProspectiveAuthorityV2.from_organism(source, mode=V2Mode.PROSPECTIVE)
    structural = organism._structural_manifest()
    matured = set()
    for index, fen in enumerate(fens[:4]):
        _pending, _trace, receipt = _open_mint(organism, fen, frame_id=f"support:{index}")
        emission = organism.consume(receipt)
        matured.update(emission.matured_cell_ids)
    assert matured
    assert all(organism.states[cell_id].prospectively_certified for cell_id in matured)
    assert all(organism.states[cell_id].successes >= 4 for cell_id in matured)
    assert organism._structural_manifest() == structural


def test_virtual_capability_and_cross_frame_pairing(native_fixture):
    source, fens = native_fixture
    organism = NativeProspectiveAuthorityV2.from_organism(source, mode=V2Mode.PROSPECTIVE)
    virtual = FrameContext("dream", FrameKind.VIRTUAL, values={"board": chess.Board(fens[0])})
    _atomic_abort(organism, "VIRTUAL cannot open", lambda: organism.open_real_event(virtual))
    before = organism.continuation_digest()
    ordinal_before = organism.next_expected_ordinal
    result = organism.open_virtual(virtual)
    assert result["certification_commitment"] is None
    assert organism.pending_event is None
    assert organism.next_expected_ordinal == ordinal_before
    assert organism.continuation_digest() == before

    organism = NativeProspectiveAuthorityV2.from_organism(source, mode=V2Mode.PROSPECTIVE)
    _pending, _trace, receipt = _open_mint(organism, fens[0])
    virtual_trace = replace(receipt.trace, frame_kind=FrameKind.VIRTUAL.name)
    altered = _resign(organism, replace(
        receipt, frame_kind=FrameKind.VIRTUAL.name, trace=virtual_trace
    ))
    _atomic_abort(organism, "VIRTUAL-to-REAL", lambda: organism.consume(altered))


def test_forbidden_relabel_candidate_disparity_and_exposure_outcome_blind(native_fixture):
    source, fens = native_fixture
    organism = NativeProspectiveAuthorityV2.from_organism(source, mode=V2Mode.PROSPECTIVE)
    _atomic_abort(organism, "outcome relabeling", organism.consume_with_authority_outcome)
    other = NativeProspectiveAuthorityV2.from_organism(source, mode=V2Mode.LEGACY)
    altered = replace(other.states["v2_parent"].hypothesis, members=("changed",))
    other.states["v2_parent"].hypothesis = altered
    _atomic_abort(organism, "candidate-manifest disparity", lambda: organism.assert_candidate_parity(other))

    traces = []
    for index, fen in enumerate(fens[:4]):
        board = chess.Board(fen)
        _actuation, trace = organism.base.r0.emit_action_with_trace(
            FrameContext(f"exposure:{index}", FrameKind.REAL, values={"board": board})
        )
        assert trace is not None
        traces.append(trace)
    class PoisonOutcomeTrace:
        def __init__(self, trace):
            self._trace = trace
        @property
        def observed_outcome(self):
            raise AssertionError("exposure scanner read outcome")
        def __getattr__(self, name):
            return getattr(self._trace, name)

    before = organism.continuation_digest()
    result = OutcomeBlindExposureScanner.scan(
        organism, [PoisonOutcomeTrace(trace) for trace in traces]
    )
    assert result["outcome_fields_read"] == 0
    assert organism.continuation_digest() == before
    admitted = OutcomeBlindExposureScanner.adjudicate_cohort(
        [{"qualifies": index < 24} for index in range(32)]
    )
    assert admitted["admitted"] and admitted["qualifying_organisms"] == 24
    starved = OutcomeBlindExposureScanner.adjudicate_cohort(
        [{"qualifies": index < 23} for index in range(32)]
    )
    assert not starved["admitted"]
    assert starved["stop_reason"] == "prospective_evidence_starvation"
