from __future__ import annotations

import copy
from dataclasses import asdict, replace
import gzip
import hashlib
import hmac
import inspect
import json
from pathlib import Path

import chess
import pytest

from recon_lite import FrameContext, FrameKind
from recon_lite_hector.nodes import StemCellState, StemCellTerminal
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
from recon_lite_chess.autogrowth import (
    native_prospective_evidence_authority_v2 as authority_module,
)
from recon_lite_chess.autogrowth.native_prospective_evidence_authority_v2 import (
    ExposureProbe,
    FrozenHypothesis,
    NativeProspectiveAuthorityV2,
    OutcomeBlindExposureScanner,
    ProspectiveProvenanceUnavailable,
    ProspectiveV2IntegrityError,
    ProvenanceKind,
    V2Mode,
    _interaction_manifest,
    _sha,
)
from recon_lite_chess.autogrowth.native_trace_competence_authority import (
    TraceNativeCompetenceOrganism,
    TraceNativeLearningConfig,
)


FREEZE = Path(
    "reports/autogrowth/native_authority/"
    "native_prospective_evidence_authority_freeze.json"
)


def _canonical(value):
    return json.dumps(
        value, sort_keys=True, separators=(",", ":"), allow_nan=False
    ).encode()


def _resign(organism, receipt):
    return replace(
        receipt,
        signature=hmac.new(
            organism._receipt_secret,
            _canonical(receipt.unsigned_manifest()),
            hashlib.sha256,
        ).hexdigest(),
    )


def _atomic_abort(organism, pattern, operation):
    before = organism.continuation_digest()
    with pytest.raises(
        (ProspectiveV2IntegrityError, ProspectiveProvenanceUnavailable),
        match=pattern,
    ):
        operation()
    assert organism.continuation_digest() == before


def _accept_rows(source, fens, desired_outcome, count, prefix):
    accepted = []
    terminal = source.completion_terminal()
    for index, fen in enumerate(fens):
        board = chess.Board(fen)
        frame = FrameContext(
            f"{prefix}:{index}", FrameKind.REAL, values={"board": board}
        )
        actuation, trace = source.r0.emit_action_with_trace(frame)
        if actuation is None or trace is None:
            continue
        successor = board.copy(stack=False)
        successor.push(chess.Move.from_uci(actuation.move_uci))
        if successor.is_checkmate() is not desired_outcome:
            continue
        receipt = terminal.mint(trace, board, successor)
        _record, inserted = source._accept_receipt(receipt)
        assert inserted
        accepted.append((receipt, trace, fen))
        if len(accepted) == count:
            break
    assert len(accepted) == count
    return accepted


def _select_rows(r0, fens, desired_outcome, count, prefix):
    rows = []
    for index, fen in enumerate(fens):
        board = chess.Board(fen)
        actuation, trace = r0.emit_action_with_trace(FrameContext(
            f"{prefix}:{index}", FrameKind.REAL, values={"board": board}
        ))
        if actuation is None or trace is None:
            continue
        successor = board.copy(stack=False)
        successor.push(chess.Move.from_uci(actuation.move_uci))
        if successor.is_checkmate() is desired_outcome:
            rows.append(fen)
        if len(rows) == count:
            break
    assert len(rows) == count
    return tuple(rows)


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
    positives = _accept_rows(
        source, build.pools.r0_train, True, 4, "v2:discovery:positive"
    )
    negatives = _accept_rows(
        source,
        build.pools.gate_train_decoys,
        False,
        4,
        "v2:discovery:negative",
    )
    common = set(positives[0][1].ordered_signal_identities)
    for _receipt, trace, _fen in positives[1:]:
        common.intersection_update(trace.ordered_signal_identities)
    assert "internal:policy_response" in common
    member = "internal:policy_response"
    evidence_ids = tuple(sorted(item[0].event_id for item in positives))

    parent_stem = StemCellTerminal("v2_parent")
    parent_stem.state = StemCellState.MATURE
    parent_stem.trial_node_id = "v2_parent"
    parent_stem.trial_parent_id = "competence_available_root"
    parent = CompetenceContextCell(
        cell_id="v2_parent",
        members=(member,),
        born_round=0,
        born_request_ordinal=0,
        stem_cell=parent_stem,
        polarity=AvailabilityState.AVAILABLE,
        evidence_keys=evidence_ids,
        successes=4,
        support=4,
        success_lower_bound=0.568,
    )
    child_stem = StemCellTerminal("v2_child")
    child_stem.state = StemCellState.MATURE
    child_stem.trial_node_id = "v2_child"
    child_stem.trial_parent_id = "competence_available_root"
    child = CompetenceContextCell(
        cell_id="v2_child",
        members=("context:v2_parent", member),
        born_round=1,
        born_request_ordinal=1,
        stem_cell=child_stem,
        polarity=AvailabilityState.AVAILABLE,
        evidence_keys=evidence_ids,
        successes=4,
        support=4,
        success_lower_bound=0.568,
        lineage_parent_id="v2_parent",
        specialization_depth=1,
        specialization_request_ordinal=1,
        specialization_proposal_ordinal=1,
    )
    source.envelope.cells = {
        parent.cell_id: parent,
        child.cell_id: child,
    }
    source.envelope._member_specs = {parent.members, child.members}
    source.envelope.rebuild_graph()
    later_positive = _select_rows(
        source.r0, build.pools.r0_validation, True, 6, "v2:later:positive"
    )
    later_negative = _select_rows(
        source.r0,
        build.pools.gate_validation_decoys,
        False,
        6,
        "v2:later:negative",
    )
    return {
        "source": source,
        "positive": later_positive,
        "negative": later_negative,
        "discovery_ids": tuple(sorted(source.receipts)),
    }


def _open_mint(organism, fen, *, frame_id="v2-real"):
    board = chess.Board(fen)
    pending, trace = organism.open_real_event(FrameContext(
        frame_id, FrameKind.REAL, values={"board": board}
    ))
    successor = board.copy(stack=False)
    successor.push(chess.Move.from_uci(pending.actuation.move_uci))
    receipt = organism.mint_environment_receipt(
        pending_token=pending.pending_token,
        trace=trace,
        predecessor=board,
        successor=successor,
    )
    return pending, trace, receipt


def _run_rows(organism, fens, prefix):
    emissions = []
    for index, fen in enumerate(fens):
        _pending, _trace, receipt = _open_mint(
            organism, fen, frame_id=f"{prefix}:{index}"
        )
        emissions.append(organism.consume(receipt))
    return emissions


def _clone_cell(cell, cell_id, state, polarity):
    result = copy.deepcopy(cell)
    result.cell_id = cell_id
    result.stem_cell = StemCellTerminal(cell_id)
    result.stem_cell.state = state
    result.stem_cell.trial_node_id = cell_id
    result.stem_cell.trial_parent_id = "competence_available_root"
    result.polarity = polarity
    result.lineage_parent_id = None
    result.specialization_depth = 0
    return result


def test_exact_historical_organism_compatibility_read_only():
    freeze = json.loads(FREEZE.read_text(encoding="utf-8"))
    entry = freeze["krk"]["organisms"][0]["source_artifact"]
    compressed = Path(entry["path"]).read_bytes()
    assert hashlib.sha256(compressed).hexdigest() == entry["compressed_sha256"]
    raw = gzip.decompress(compressed)
    assert hashlib.sha256(raw).hexdigest() == entry["uncompressed_sha256"]
    source = TraceNativeCompetenceOrganism.loads(raw)
    assert source.continuation_digest_v3() == entry["continuation_v3_sha256"]
    before = source.continuation_digest_v3()

    wrapper = NativeProspectiveAuthorityV2.from_organism(
        source, mode=V2Mode.PROSPECTIVE
    )
    assert source.continuation_digest_v3() == before
    assert len(source.envelope.cells) == 155
    assert len(wrapper.historical_tombstones) == 152
    assert len(wrapper.states) == 3
    assert all(
        row["polarity"] is None and row["stem_cell"]["state"] == "PRUNED"
        for row in wrapper.historical_tombstones.values()
    )
    ledger = tuple(sorted(source.receipts))
    frontier = max(item.event_ordinal for item in source.receipts.values())
    assert len(ledger) == 96
    assert all(
        state.hypothesis.provenance_kind
        is ProvenanceKind.HISTORICAL_ACCEPTED_LEDGER
        and state.hypothesis.discovery_receipt_ids == ledger
        and state.hypothesis.birth_frontier == frontier
        and not state.hypothesis.nomination_read_sets
        for state in wrapper.states.values()
    )
    restored = NativeProspectiveAuthorityV2.loads(wrapper.dumps())
    assert restored.continuation_manifest() == wrapper.continuation_manifest()


def test_historical_escrow_parity_and_probation_parent_matching(native_fixture):
    source = native_fixture["source"]
    source_before = source.continuation_digest_v3()
    prospective = NativeProspectiveAuthorityV2.from_organism(
        source, mode=V2Mode.PROSPECTIVE
    )
    legacy = NativeProspectiveAuthorityV2.from_organism(
        source, mode=V2Mode.LEGACY
    )
    assert source.continuation_digest_v3() == source_before
    prospective.assert_candidate_parity(legacy)
    assert prospective._structural_manifest() == legacy._structural_manifest()
    assert all(
        not state.prospectively_certified
        for state in prospective.states.values()
    )
    assert all(
        state.prospectively_certified
        for state in legacy.states.values()
    )

    probation_source = copy.deepcopy(source)
    probation_source.envelope.cells[
        "v2_parent"
    ].stem_cell.state = StemCellState.PROBATION
    probation_source.envelope.rebuild_graph()
    probation = NativeProspectiveAuthorityV2.from_organism(
        probation_source, mode=V2Mode.PROSPECTIVE
    )
    pending, _trace, _receipt = _open_mint(
        probation, native_fixture["positive"][0], frame_id="probation-parent"
    )
    assert "v2_parent" in pending.matching_cell_ids
    assert "v2_child" in pending.matching_cell_ids


def test_tombstones_and_exact_new_nomination_read_sets(native_fixture):
    source = copy.deepcopy(native_fixture["source"])
    tombstone = _clone_cell(
        source.envelope.cells["v2_parent"],
        "historical_tombstone",
        StemCellState.PRUNED,
        None,
    )
    source.envelope.cells[tombstone.cell_id] = tombstone
    source.envelope.rebuild_graph()
    wrapper = NativeProspectiveAuthorityV2.from_organism(
        source, mode=V2Mode.PROSPECTIVE
    )
    assert "historical_tombstone" in wrapper.historical_tombstones
    assert "historical_tombstone" not in wrapper.states

    missing = _clone_cell(
        wrapper.base.envelope.cells["v2_parent"],
        "live_missing_escrow",
        StemCellState.TRIAL,
        AvailabilityState.AVAILABLE,
    )
    wrapper.base.envelope.cells[missing.cell_id] = missing
    _atomic_abort(
        wrapper,
        "growth interface did not expose exact nomination read set",
        wrapper.sync_organism_nominations,
    )
    del wrapper.base.envelope.cells[missing.cell_id]

    no_polarity = _clone_cell(
        wrapper.base.envelope.cells["v2_parent"],
        "live_no_polarity",
        StemCellState.TRIAL,
        None,
    )
    wrapper.base.envelope.cells[no_polarity.cell_id] = no_polarity
    _atomic_abort(
        wrapper,
        "polarity=None",
        wrapper.sync_organism_nominations,
    )
    del wrapper.base.envelope.cells[no_polarity.cell_id]

    ids = native_fixture["discovery_ids"]
    ordinary = _clone_cell(
        wrapper.base.envelope.cells["v2_parent"],
        "new_ordinary",
        StemCellState.TRIAL,
        AvailabilityState.AVAILABLE,
    )
    ordinary.stem_cell.metadata["prospective_nomination_read_set"] = {
        "direct": ids[:2],
        "parent_support": (),
        "eligibility": (),
        "contradiction_trigger": (),
    }
    wrapper.base.envelope.cells[ordinary.cell_id] = ordinary
    assert wrapper.sync_organism_nominations() == ("new_ordinary",)
    hypothesis = wrapper.states["new_ordinary"].hypothesis
    assert hypothesis.provenance_kind is ProvenanceKind.EXACT_NOMINATION_READ_SET
    assert hypothesis.discovery_receipt_ids == tuple(sorted(ids[:2]))
    assert dict(hypothesis.nomination_read_sets)["direct"] == tuple(
        sorted(ids[:2])
    )
    assert wrapper.nomination_events[-1]["cell_ids"] == ["new_ordinary"]

    specialized = _clone_cell(
        wrapper.base.envelope.cells["v2_child"],
        "new_specialized",
        StemCellState.PROBATION,
        AvailabilityState.AVAILABLE,
    )
    specialized.members = (
        "context:new_ordinary",
        "internal:policy_response",
    )
    specialized.lineage_parent_id = "new_ordinary"
    specialized.specialization_depth = 1
    specialized.stem_cell.metadata["prospective_nomination_read_set"] = {
        "direct": ids[:1],
        "parent_support": ids[1:2],
        "eligibility": ids[2:3],
        "contradiction_trigger": ids[3:4],
    }
    wrapper.base.envelope.cells[specialized.cell_id] = specialized
    assert wrapper.sync_organism_nominations() == ("new_specialized",)
    read_sets = dict(
        wrapper.states["new_specialized"].hypothesis.nomination_read_sets
    )
    assert all(read_sets[name] for name in (
        "direct", "parent_support", "eligibility",
        "contradiction_trigger",
    ))


def test_complete_receipt_validation_and_atomic_structure_guard(native_fixture):
    source = native_fixture["source"]
    fen = native_fixture["positive"][0]
    mutations = [
        ("unexpected receipt issuer", lambda r: replace(
            r, issuer_identity="wrong-issuer"
        )),
        ("receipt ID mismatch", lambda r: replace(
            r, receipt_id="wrong-receipt-id"
        )),
        ("source identity mismatch", lambda r: replace(
            r, source_organism_identity="wrong-organism"
        )),
        ("out-of-order ordinal", lambda r: replace(
            r, ordinal=r.ordinal + 1
        )),
        ("wrong or consumed pending token", lambda r: replace(
            r, pending_token="wrong-token"
        )),
        ("trace mismatch", lambda r: replace(
            r, trace=replace(r.trace, frame_id="altered")
        )),
        ("successor mismatch", lambda r: replace(
            r, successor_fen=chess.Board().fen()
        )),
        ("outcome terminal mismatch", lambda r: replace(
            r, outcome_terminal_identity="wrong-terminal"
        )),
    ]
    for index, (message, mutate) in enumerate(mutations):
        organism = NativeProspectiveAuthorityV2.from_organism(
            source, mode=V2Mode.PROSPECTIVE
        )
        _pending, _trace, valid = _open_mint(
            organism, fen, frame_id=f"receipt:{index}"
        )
        altered = _resign(organism, mutate(valid))
        _atomic_abort(
            organism, message,
            lambda altered=altered: organism.consume(altered),
        )

    organism = NativeProspectiveAuthorityV2.from_organism(
        source, mode=V2Mode.PROSPECTIVE
    )
    _pending, _trace, receipt = _open_mint(
        organism, fen, frame_id="typed-digest"
    )
    organism.pending_event = replace(
        organism.pending_event, typed_signal_digest="wrong"
    )
    _atomic_abort(
        organism, "typed-signal digest mismatch",
        lambda: organism.consume(receipt),
    )

    for field_name in ("members", "lineage", "state"):
        organism = NativeProspectiveAuthorityV2.from_organism(
            source, mode=V2Mode.PROSPECTIVE
        )
        _pending, _trace, receipt = _open_mint(
            organism, fen, frame_id=f"structure:{field_name}"
        )
        cell = organism.base.envelope.cells["v2_parent"]
        if field_name == "members":
            cell.members = (*cell.members, "mutated")
        elif field_name == "lineage":
            cell.lineage_parent_id = "mutated-parent"
        else:
            cell.stem_cell.state = StemCellState.PROBATION
        _atomic_abort(
            organism,
            "live structural invariant mutation",
            lambda: organism.consume(receipt),
        )


def test_graph_maturity_disconnect_and_no_python_id_injection(
    native_fixture, monkeypatch
):
    source = native_fixture["source"]
    positives = native_fixture["positive"][:4]
    connected = NativeProspectiveAuthorityV2.from_organism(
        source, mode=V2Mode.PROSPECTIVE
    )
    emissions = _run_rows(connected, positives, "connected-maturity")
    matured = set().union(*(
        set(emission.matured_cell_ids) for emission in emissions
    ))
    assert matured
    assert all(
        connected.states[cell_id].prospectively_certified
        for cell_id in matured
    )

    disconnected = NativeProspectiveAuthorityV2.from_organism(
        source, mode=V2Mode.PROSPECTIVE
    )
    original_terminal = authority_module._authority_terminal

    def without_maturity(node, env):
        if node.meta.get("authority_role") == "maturity":
            return True, False
        return original_terminal(node, env)

    monkeypatch.setattr(
        authority_module, "_authority_terminal", without_maturity
    )
    _run_rows(disconnected, positives, "disconnected-maturity")
    assert all(state.support == 4 for state in disconnected.states.values())
    assert all(
        not state.prospectively_certified
        for state in disconnected.states.values()
    )
    assert "maturity_ids" not in inspect.signature(
        NativeProspectiveAuthorityV2.consume
    ).parameters
    with pytest.raises(TypeError):
        disconnected.consume(None, maturity_ids=("v2_parent",))


def test_graph_revocation_refuted_authority_and_disconnect(
    native_fixture, monkeypatch
):
    source = native_fixture["source"]
    positives = native_fixture["positive"][:4]
    negative = native_fixture["negative"][0]

    connected = NativeProspectiveAuthorityV2.from_organism(
        source, mode=V2Mode.PROSPECTIVE
    )
    _run_rows(connected, positives, "revocation-maturity")
    _pending, _trace, contradiction = _open_mint(
        connected, negative, frame_id="revocation-connected"
    )
    emission = connected.consume(contradiction)
    assert set(emission.revoked_cell_ids) == {
        "v2_parent", "v2_child"
    }
    assert all(
        not state.prospectively_certified
        for state in connected.states.values()
    )

    disconnected = NativeProspectiveAuthorityV2.from_organism(
        source, mode=V2Mode.PROSPECTIVE
    )
    _run_rows(disconnected, positives, "revocation-control-maturity")
    original_terminal = authority_module._authority_terminal

    def without_revocation(node, env):
        if node.meta.get("authority_role") == "revocation":
            return True, False
        return original_terminal(node, env)

    monkeypatch.setattr(
        authority_module, "_authority_terminal", without_revocation
    )
    _pending, _trace, contradiction = _open_mint(
        disconnected, negative, frame_id="revocation-disconnected"
    )
    emission = disconnected.consume(contradiction)
    assert emission.revoked_cell_ids == ()
    assert all(
        state.prospectively_certified
        for state in disconnected.states.values()
    )

    refuted_source = copy.deepcopy(source)
    refuted = _clone_cell(
        refuted_source.envelope.cells["v2_parent"],
        "v2_refuted",
        StemCellState.MATURE,
        AvailabilityState.REFUTED,
    )
    refuted_source.envelope.cells = {refuted.cell_id: refuted}
    refuted_source.envelope._member_specs = {refuted.members}
    refuted_source.envelope.rebuild_graph()
    refuted_organism = NativeProspectiveAuthorityV2.from_organism(
        refuted_source, mode=V2Mode.PROSPECTIVE
    )
    _run_rows(
        refuted_organism,
        native_fixture["negative"][:4],
        "refuted-maturity",
    )
    assert refuted_organism.states[
        "v2_refuted"
    ].prospectively_certified
    pending, _trace, _receipt = _open_mint(
        refuted_organism,
        native_fixture["negative"][4],
        frame_id="refuted-inference",
    )
    assert (
        pending.pre_outcome_classification.state
        is AvailabilityState.REFUTED
    )
    assert pending.pre_outcome_classification.refuted_cell_ids == (
        "v2_refuted",
    )


def test_serialization_duplicate_remint_and_virtual_isolation(native_fixture):
    source = native_fixture["source"]
    organism = NativeProspectiveAuthorityV2.from_organism(
        source, mode=V2Mode.PROSPECTIVE
    )
    _pending, _trace, receipt = _open_mint(
        organism, native_fixture["positive"][0], frame_id="serialization"
    )
    open_restored = NativeProspectiveAuthorityV2.loads(
        organism.dumps()
    )
    assert (
        open_restored.continuation_manifest()
        == organism.continuation_manifest()
    )
    emission = organism.consume(receipt)
    consumed_restored = NativeProspectiveAuthorityV2.loads(
        organism.dumps()
    )
    assert (
        consumed_restored.continuation_manifest()
        == organism.continuation_manifest()
    )
    before = organism.continuation_digest()
    assert organism.consume(receipt) == emission
    assert organism.continuation_digest() == before

    reminted = _resign(organism, replace(
        receipt,
        receipt_id="new-id",
        ordinal=receipt.ordinal + 1,
    ))
    _atomic_abort(
        organism,
        "reminted interaction fingerprint",
        lambda: organism.consume(reminted),
    )

    virtual = FrameContext(
        "dream",
        FrameKind.VIRTUAL,
        values={"board": chess.Board(native_fixture["positive"][1])},
    )
    before = organism.continuation_digest()
    result = organism.open_virtual(virtual)
    assert result["certification_commitment"] is None
    assert organism.continuation_digest() == before
    _atomic_abort(
        organism,
        "VIRTUAL cannot open",
        lambda: organism.open_real_event(virtual),
    )


def _probe(organism, fen, frame_id):
    board = chess.Board(fen)
    _actuation, trace = organism.base.r0.emit_action_with_trace(
        FrameContext(frame_id, FrameKind.REAL, values={"board": board})
    )
    assert trace is not None
    return ExposureProbe(board.fen(), trace)


def _remap_scan(scan, ordinal, qualify):
    result = copy.deepcopy(scan)
    organism_identity = f"cohort-organism-{ordinal}"
    state_identity = f"cohort-state-{ordinal}"
    rows = result["raw_opportunities"]
    if not qualify:
        rows = rows[:1]
    for row in rows:
        row["source_organism_identity"] = organism_identity
        row["source_state_identity"] = state_identity
        row["trace"]["source_organism_identity"] = organism_identity
        row["trace"]["source_state_identity"] = state_identity
        fingerprint = _sha(_interaction_manifest(
            source_organism_identity=organism_identity,
            source_state_identity=state_identity,
            predecessor_fen=row["predecessor_fen"],
            trace_manifest=row["trace"],
            actuation_manifest=row["selected_actuation"],
            successor_fen=row["successor_fen"],
            outcome_terminal_identity=row["outcome_terminal_identity"],
        ))
        row["interaction_fingerprint"] = fingerprint
        row["opportunity_id"] = _sha({
            "interaction_fingerprint": fingerprint,
            "matched_frozen_cell": row["cell_id"],
        })
    result["organism_identity"] = organism_identity
    result["source_state_identity"] = state_identity
    result["raw_opportunities"] = sorted(
        rows, key=lambda row: row["opportunity_id"]
    )
    result["raw_manifest_digest"] = _sha(result["raw_opportunities"])
    per_cell = {}
    for row in result["raw_opportunities"]:
        per_cell.setdefault(row["cell_id"], []).append(
            row["opportunity_id"]
        )
    result["cells"] = {
        cell_id: {
            "distinct_opportunities": len(ids),
            "opportunity_ids": sorted(ids),
        }
        for cell_id, ids in sorted(per_cell.items())
    }
    return result


def test_exposure_distinctness_integrity_and_remint_alignment(native_fixture):
    organism = NativeProspectiveAuthorityV2.from_organism(
        native_fixture["source"], mode=V2Mode.PROSPECTIVE
    )
    identical = _probe(
        organism, native_fixture["positive"][0], "same-exposure"
    )
    collapsed = OutcomeBlindExposureScanner.scan(
        organism, [identical] * 4
    )
    assert max(
        row["distinct_opportunities"]
        for row in collapsed["cells"].values()
    ) == 1
    assert len(collapsed["raw_opportunities"]) == len(
        organism.states
    )

    distinct = [
        _probe(organism, fen, f"distinct-exposure:{index}")
        for index, fen in enumerate(native_fixture["positive"][:4])
    ]
    expanded = OutcomeBlindExposureScanner.scan(
        organism, distinct
    )
    assert max(
        row["distinct_opportunities"]
        for row in expanded["cells"].values()
    ) == 4

    virtual = replace(
        identical.trace, frame_kind=FrameKind.VIRTUAL.name
    )
    _atomic_abort(
        organism,
        "exposure requires REAL",
        lambda: OutcomeBlindExposureScanner.scan(
            organism,
            [ExposureProbe(identical.predecessor_fen, virtual)],
        ),
    )
    mixed = replace(
        identical.trace,
        source_organism_identity="another-organism",
    )
    _atomic_abort(
        organism,
        "source-organism identity mismatch",
        lambda: OutcomeBlindExposureScanner.scan(
            organism,
            [ExposureProbe(identical.predecessor_fen, mixed)],
        ),
    )

    pending, trace, receipt = _open_mint(
        organism,
        native_fixture["positive"][1],
        frame_id="remint-alignment",
    )
    alignment = OutcomeBlindExposureScanner.scan(
        organism,
        [ExposureProbe(pending.predecessor_fen, trace)],
    )
    assert alignment["raw_opportunities"]
    assert {
        row["interaction_fingerprint"]
        for row in alignment["raw_opportunities"]
    } == {receipt.interaction_fingerprint}


def test_raw_manifest_cohort_recomputes_qualification(native_fixture):
    organism = NativeProspectiveAuthorityV2.from_organism(
        native_fixture["source"], mode=V2Mode.PROSPECTIVE
    )
    probes = [
        _probe(organism, fen, f"cohort-exposure:{index}")
        for index, fen in enumerate(native_fixture["positive"][:4])
    ]
    scan = OutcomeBlindExposureScanner.scan(organism, probes)
    cohort = [
        _remap_scan(scan, index, index < 24)
        for index in range(32)
    ]
    admitted = OutcomeBlindExposureScanner.adjudicate_cohort(cohort)
    assert admitted["admitted"]
    assert admitted["qualifying_organisms"] == 24

    fake = copy.deepcopy(cohort)
    fake[0]["qualifies"] = True
    with pytest.raises(
        ProspectiveV2IntegrityError,
        match="caller-supplied exposure qualification",
    ):
        OutcomeBlindExposureScanner.adjudicate_cohort(fake)

    bad_digest = copy.deepcopy(cohort)
    bad_digest[0]["raw_manifest_digest"] = "fabricated"
    with pytest.raises(
        ProspectiveV2IntegrityError,
        match="raw exposure manifest digest mismatch",
    ):
        OutcomeBlindExposureScanner.adjudicate_cohort(bad_digest)

    mixed = copy.deepcopy(cohort)
    mixed[0]["raw_opportunities"][0][
        "source_organism_identity"
    ] = "wrong"
    mixed[0]["raw_manifest_digest"] = _sha(
        mixed[0]["raw_opportunities"]
    )
    with pytest.raises(
        ProspectiveV2IntegrityError,
        match="mixed-organism raw exposure manifest",
    ):
        OutcomeBlindExposureScanner.adjudicate_cohort(mixed)


def test_frozen_hypothesis_rejects_nonexact_provenance():
    with pytest.raises(ProspectiveV2IntegrityError, match="polarity=None"):
        FrozenHypothesis(
            "bad",
            ("x",),
            None,
            None,
            0,
            ("r",),
            _sha(["r"]),
            0,
            "TRIAL",
        )
    with pytest.raises(
        ProspectiveProvenanceUnavailable,
        match="incomplete nomination read set",
    ):
        FrozenHypothesis(
            "bad-reads",
            ("x",),
            AvailabilityState.AVAILABLE,
            None,
            0,
            ("r",),
            _sha(["r"]),
            0,
            "TRIAL",
            ProvenanceKind.EXACT_NOMINATION_READ_SET,
            (),
        )
