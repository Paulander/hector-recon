from __future__ import annotations

import copy
from dataclasses import asdict, replace
import gzip
import hashlib
import hmac
import inspect
import itertools
import json
import pickle
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
    GraphNativeCompetenceEnvelope,
    SpecializationMode,
)
from recon_lite_chess.autogrowth import (
    native_prospective_evidence_authority_v2 as authority_module,
)
from recon_lite_chess.autogrowth.native_prospective_evidence_authority_v2 import (
    CanonicalExposureCommitment,
    FrozenHypothesis,
    InitializationOrigin,
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
from recon_lite_chess.autogrowth.native_prospective_evidence_authority_v2_lab import (
    RegisteredV2ExposureRow,
    V2LaboratoryRegistry,
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
        record, inserted = source._accept_receipt(receipt)
        assert inserted
        assert source.envelope.add_unique_evidence(record)
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
    epoch = organism.base.envelope.nomination_epoch
    if epoch is not None and not epoch.nomination_closed:
        organism.close_nomination()
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
        ("source identity mismatch|trace mismatch", lambda r: replace(
            r, source_organism_identity="wrong-organism"
        )),
        ("source identity mismatch|trace mismatch", lambda r: replace(
            r, trace=replace(r.trace, source_state_identity="wrong-state")
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
        ("trace/actuation mismatch|actuation mismatch", lambda r: replace(
            r, selected_actuation=replace(
                r.selected_actuation, option_identity="wrong-option"
            )
        )),
        ("successor mismatch|predecessor mismatch", lambda r: replace(
            r, successor_fen=chess.Board().fen()
        )),
        ("successor mismatch|predecessor mismatch", lambda r: replace(
            r, predecessor_fen=r.predecessor_fen.rsplit(" ", 1)[0] + " 99"
        )),
        ("VIRTUAL-to-REAL", lambda r: replace(
            r, frame_kind=FrameKind.VIRTUAL.name
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
        organism, "pending transaction manifest mismatch",
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

    original_terminal = authority_module._authority_terminal

    def without_revocation(node, env):
        if node.meta.get("authority_role") == "revocation":
            return True, False
        return original_terminal(node, env)

    monkeypatch.setattr(
        authority_module, "_authority_terminal", without_revocation
    )
    disconnected = NativeProspectiveAuthorityV2.from_organism(
        source, mode=V2Mode.PROSPECTIVE
    )
    _run_rows(disconnected, positives, "revocation-control-maturity")
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


def _ground_receipts(organism, fens, prefix):
    terminal = organism.base.completion_terminal()
    receipts = []
    for index, fen in enumerate(fens):
        board = chess.Board(fen)
        frame = FrameContext(
            f"{prefix}:{index}", FrameKind.REAL, values={"board": board}
        )
        actuation, trace = organism.base.r0.emit_action_with_trace(frame)
        assert actuation is not None and trace is not None
        successor = board.copy(stack=False)
        successor.push(chess.Move.from_uci(actuation.move_uci))
        receipts.append(terminal.mint(trace, board, successor))
    return tuple(receipts)


def test_discovery_epoch_atomic_native_escrow_and_closure(native_fixture):
    organism = NativeProspectiveAuthorityV2.from_organism(
        native_fixture["source"], mode=V2Mode.PROSPECTIVE
    )
    epoch = organism.base.envelope.nomination_epoch
    assert epoch is not None and not epoch.nomination_closed
    with pytest.raises(
        ProspectiveV2IntegrityError, match="requires closed nomination"
    ):
        board = chess.Board(native_fixture["negative"][0])
        organism.open_real_event(FrameContext(
            "before-close", FrameKind.REAL, values={"board": board}
        ))
    receipts = _ground_receipts(
        organism, native_fixture["negative"][:4], "native-prefix"
    )
    added = organism.nominate_prefix_from_grounded_receipts(receipts)
    epoch = organism.base.envelope.nomination_epoch
    assert epoch is not None
    assert epoch.post_epoch_cell_ids
    assert set(added).issubset(epoch.post_epoch_cell_ids)
    prospective_cells = [
        organism.base.envelope.cells[cell_id]
        for cell_id in epoch.post_epoch_cell_ids
    ]
    assert all(cell.nomination_escrow is not None for cell in prospective_cells)
    assert all(
        cell.polarity is cell.nomination_escrow.fixed_polarity
        for cell in prospective_cells
    )
    assert all(
        cell.nomination_escrow.discovery_exclusion_receipt_ids
        == tuple(sorted(organism.base.receipts))
        for cell in prospective_cells
    )
    nested = [
        cell for cell in prospective_cells
        if any(member.startswith("context:") for member in cell.members)
    ]
    assert nested
    assert all(cell.lineage_parent_id is None for cell in nested)
    assert all(
        cell.nomination_escrow.transitive_ancestor_receipt_ids
        for cell in nested
    )
    polarity_mutation = copy.deepcopy(organism)
    polarity_cell = polarity_mutation.base.envelope.cells[
        added[0]
    ]
    polarity_cell.polarity = (
        AvailabilityState.REFUTED
        if polarity_cell.polarity is AvailabilityState.AVAILABLE
        else AvailabilityState.AVAILABLE
    )
    with pytest.raises(
        ProspectiveV2IntegrityError, match="structural.*mutation|polarity"
    ):
        polarity_mutation.sync_organism_nominations()

    ancestor_mutation = copy.deepcopy(organism)
    nested_cell = next(
        cell for cell in ancestor_mutation.base.envelope.cells.values()
        if cell.cell_id in epoch.post_epoch_cell_ids
        and any(member.startswith("context:") for member in cell.members)
    )
    object.__setattr__(
        nested_cell.nomination_escrow,
        "transitive_ancestor_receipt_ids",
        (),
    )
    with pytest.raises(
        (ProspectiveV2IntegrityError, RuntimeError),
        match="escrow|ancestor|provenance|digest|tombstone",
    ):
        ancestor_mutation.sync_organism_nominations()


    frozen = organism.close_nomination()
    epoch = organism.base.envelope.nomination_epoch
    assert epoch is not None
    assert frozen == epoch.frozen_candidate_manifest
    before = organism.continuation_digest()
    with pytest.raises(ProspectiveV2IntegrityError, match="closed"):
        organism.sync_organism_nominations()
    assert organism.continuation_digest() == before
    with pytest.raises(RuntimeError, match="closed"):
        organism.base.envelope.grow(())
    assert organism.continuation_digest() == before


def test_pruned_post_epoch_cell_retains_birth_escrow(native_fixture):
    organism = NativeProspectiveAuthorityV2.from_organism(
        native_fixture["source"], mode=V2Mode.PROSPECTIVE
    )
    receipts = _ground_receipts(
        organism, native_fixture["negative"][:4], "pruned-prefix"
    )
    organism.base.grow_from_grounded_receipts(receipts)
    epoch = organism.base.envelope.nomination_epoch
    assert epoch is not None and epoch.post_epoch_cell_ids
    cell_id = epoch.post_epoch_cell_ids[0]
    cell = organism.base.envelope.cells[cell_id]
    escrow_manifest = cell.nomination_escrow.manifest()
    cell.stem_cell.state = StemCellState.PRUNED
    cell.prune_reason = "test_lifecycle_prune"
    organism.sync_organism_nominations()
    assert organism.historical_tombstones[cell_id][
        "nomination_escrow"
    ] == escrow_manifest
    organism.close_nomination()
    restored = NativeProspectiveAuthorityV2.loads(organism.dumps())
    assert restored.historical_tombstones[cell_id][
        "nomination_escrow"
    ] == escrow_manifest


def test_specialization_materialization_has_exact_native_escrow(native_fixture):
    source = copy.deepcopy(native_fixture["source"])
    source.learning_config = replace(
        source.learning_config,
        lifecycle_connected=True,
        specialization_mode=SpecializationMode.LOCAL_CONTRAST,
    )
    organism = NativeProspectiveAuthorityV2.from_organism(
        source, mode=V2Mode.PROSPECTIVE
    )
    receipt = _ground_receipts(
        organism, native_fixture["negative"][:1], "specialize-prefix"
    )[0]
    emission = organism.base.observe_grounded(receipt)
    assert emission.specialization_child_ids
    organism.sync_organism_nominations()
    for cell_id in emission.specialization_child_ids:
        cell = organism.base.envelope.cells[cell_id]
        escrow = cell.nomination_escrow
        assert escrow is not None and escrow.operation == "specialization"
        categories = dict(escrow.categorized_reads)
        assert categories["contradiction_trigger"] == (receipt.event_id,)
        assert categories["eligibility"] == (
            escrow.discovery_exclusion_receipt_ids
        )
        assert categories["parent_support"]
        assert escrow.transitive_ancestor_receipt_ids
        hypothesis = organism.states[cell_id].hypothesis
        assert hypothesis.nomination_read_sets == escrow.categorized_reads
        assert hypothesis.hypothesis_digest
    omitted = copy.deepcopy(organism)
    omitted_cell = omitted.base.envelope.cells[
        emission.specialization_child_ids[0]
    ]
    escrow = omitted_cell.nomination_escrow
    object.__setattr__(
        escrow,
        "categorized_reads",
        tuple(
            (name, () if name == "eligibility" else receipt_ids)
            for name, receipt_ids in escrow.categorized_reads
        ),
    )
    with pytest.raises(
        ProspectiveV2IntegrityError, match="eligibility|digest|escrow"
    ):
        omitted.sync_organism_nominations()



def test_ledger_reconstruction_rejects_mutated_authority_caches(native_fixture):
    baseline = NativeProspectiveAuthorityV2.from_organism(
        native_fixture["source"], mode=V2Mode.PROSPECTIVE
    )
    _run_rows(baseline, native_fixture["positive"][:1], "cache-baseline")
    cell_id = next(iter(baseline.states))
    mutations = (
        lambda state: setattr(
            state, "prospectively_certified",
            not state.prospectively_certified,
        ),
        lambda state: setattr(state, "support", state.support + 1),
        lambda state: setattr(state, "successes", state.successes + 1),
        lambda state: setattr(
            state, "success_lower_bound", state.success_lower_bound + 0.01
        ),
        lambda state: setattr(
            state, "support_receipt_ids", (*state.support_receipt_ids, "fake")
        ),
        lambda state: setattr(
            state, "transition_rows",
            (*state.transition_rows, {"transition": "fabricated"}),
        ),
    )
    for mutate in mutations:
        organism = copy.deepcopy(baseline)
        mutate(organism.states[cell_id])
        _atomic_abort(
            organism, "grounded ledger replay", organism.dumps
        )


def test_hypothesis_digest_and_frontier_mutation_fail_atomically(native_fixture):
    for field_name, value in (
        ("birth_frontier", 999999),
        ("discovery_exclusion_receipt_ids", ("fabricated",)),
        ("hypothesis_digest", "fabricated"),
    ):
        organism = NativeProspectiveAuthorityV2.from_organism(
            native_fixture["source"], mode=V2Mode.PROSPECTIVE
        )
        organism.close_nomination()
        hypothesis = next(iter(organism.states.values())).hypothesis
        object.__setattr__(hypothesis, field_name, value)
        _atomic_abort(
            organism, "hypothesis|digest|exclusion", organism.dumps
        )


def test_native_specialized_is_not_mature_for_nested_authority(native_fixture):
    source = copy.deepcopy(native_fixture["source"])
    source.envelope.cells["v2_parent"].stem_cell.state = (
        StemCellState.SPECIALIZED
    )
    source.envelope.rebuild_graph()
    organism = NativeProspectiveAuthorityV2.from_organism(
        source, mode=V2Mode.LEGACY
    )
    organism.close_nomination()
    assert not organism.states["v2_parent"].prospectively_certified
    board = chess.Board(native_fixture["positive"][0])
    pending, _trace = organism.open_real_event(FrameContext(
        "specialized-parent", FrameKind.REAL, values={"board": board}
    ))
    assert "v2_parent" in pending.matching_cell_ids
    assert "v2_child" not in pending.matching_cell_ids


    trial_source = copy.deepcopy(native_fixture["source"])
    trial_source.envelope.cells["v2_parent"].stem_cell.state = (
        StemCellState.TRIAL
    )
    trial_source.envelope.rebuild_graph()
    with pytest.raises(
        ProspectiveProvenanceUnavailable,
        match="unsupported historical live TRIAL",
    ):
        NativeProspectiveAuthorityV2.from_organism(
            trial_source, mode=V2Mode.PROSPECTIVE
        )


def test_real_transaction_order_signature_and_dual_pending(native_fixture):
    organism = NativeProspectiveAuthorityV2.from_organism(
        native_fixture["source"], mode=V2Mode.PROSPECTIVE
    )
    organism.close_nomination()
    donor = NativeProspectiveAuthorityV2.from_organism(
        native_fixture["source"], mode=V2Mode.PROSPECTIVE
    )
    donor.close_nomination()
    _p, _t, unpaired = _open_mint(
        donor, native_fixture["positive"][0], frame_id="unpaired"
    )
    with pytest.raises(ProspectiveV2IntegrityError, match="before prediction"):
        organism.consume(unpaired)
    pending, trace, receipt = _open_mint(
        organism, native_fixture["positive"][0], frame_id="dual-pending"
    )
    board = chess.Board(native_fixture["positive"][1])
    with pytest.raises(
        ProspectiveV2IntegrityError, match="one pending event"
    ):
        organism.open_real_event(FrameContext(
            "dual-pending:second", FrameKind.REAL, values={"board": board}
        ))
    bad_signature = replace(receipt, signature="fabricated")
    _atomic_abort(
        organism, "signature mismatch",
        lambda: organism.consume(bad_signature),
    )
    restored = NativeProspectiveAuthorityV2.loads(organism.dumps())
    emission = restored.consume(receipt)
    before = restored.continuation_digest()
    assert restored.consume(receipt) == emission
    assert restored.continuation_digest() == before
    assert pending.pending_token in restored.consumed_tokens
    assert trace.frame_kind == FrameKind.REAL.name


def _commitment(organism, fen, frame_id):
    epoch = organism.base.envelope.nomination_epoch
    if epoch is not None and not epoch.nomination_closed:
        organism.close_nomination()
    return organism.probe_real_exposure(FrameContext(
        frame_id, FrameKind.REAL, values={"board": chess.Board(fen)}
    ))


def _resign_commitment(commitment):
    return replace(
        commitment,
        binding_signature=hmac.new(
            authority_module._EXPOSURE_BINDING_SECRET,
            _canonical(commitment.unsigned_manifest()),
            hashlib.sha256,
        ).hexdigest(),
    )


def test_bound_exposure_rejects_aliases_mutations_and_outcomes(native_fixture):
    organism = NativeProspectiveAuthorityV2.from_organism(
        native_fixture["source"], mode=V2Mode.PROSPECTIVE
    )
    commitment = _commitment(
        organism, native_fixture["positive"][0], "bound-exposure"
    )
    assert isinstance(commitment, CanonicalExposureCommitment)
    scan = OutcomeBlindExposureScanner.scan(
        organism, [commitment, commitment, commitment, commitment]
    )
    assert max(
        row["distinct_opportunities"] for row in scan["cells"].values()
    ) == 1
    mutations = (
        _resign_commitment(replace(
            commitment, outcome_terminal_identity="fake-terminal"
        )),
        _resign_commitment(replace(
            commitment, source_organism_identity="invented"
        )),
        _resign_commitment(replace(
            commitment, successor_fen=chess.Board().fen()
        )),
        _resign_commitment(replace(
            commitment, authority_topology_digest="invented"
        )),
        _resign_commitment(replace(
            commitment, selected_actuation=replace(
                commitment.selected_actuation, option_identity="invented"
            )
        )),
    )
    for altered in mutations:
        _atomic_abort(
            organism, "exposure|binding|terminal|successor|topology|trace",
            lambda altered=altered: OutcomeBlindExposureScanner.scan(
                organism, [altered]
            ),
        )
    extra = copy.deepcopy(scan)
    extra["observed_outcome"] = True
    with pytest.raises(
        ProspectiveV2IntegrityError, match="outcome-bearing"
    ):
        OutcomeBlindExposureScanner._validate_raw_scan(extra)
    invented = copy.deepcopy(scan)
    invented["source_organism_identity"] = "invented"
    with pytest.raises(
        ProspectiveV2IntegrityError, match="binding signature"
    ):
        OutcomeBlindExposureScanner._validate_raw_scan(invented)
    with pytest.raises(
        ProspectiveV2IntegrityError, match="distinct bound organisms"
    ):
        OutcomeBlindExposureScanner.adjudicate_cohort([scan] * 32)


def test_exposure_receipt_interaction_alignment(native_fixture):
    organism = NativeProspectiveAuthorityV2.from_organism(
        native_fixture["source"], mode=V2Mode.PROSPECTIVE
    )
    organism.close_nomination()
    fen = native_fixture["positive"][0]
    frame_id = "exposure-receipt-alignment"
    commitment = _commitment(organism, fen, frame_id)
    _pending, _trace, receipt = _open_mint(
        organism, fen, frame_id=frame_id
    )
    assert commitment.interaction_fingerprint == receipt.interaction_fingerprint



def test_frozen_hypothesis_rejects_nonexact_provenance():
    with pytest.raises(ProspectiveV2IntegrityError, match="polarity=None"):
        FrozenHypothesis(
            cell_id="bad",
            members=("x",),
            polarity=None,
            lineage_parent_id=None,
            specialization_depth=0,
            discovery_receipt_ids=("r",),
            discovery_receipt_digest=_sha(["r"]),
            birth_frontier=0,
            structural_state="TRIAL",
            nomination_operation="ordinary",
            triggering_receipt_id="r",
            graph_request_root_state="CONFIRMED",
            graph_request_terminal_state="CONFIRMED",
            considered_context_ids=(),
            selected_context_ids=(),
            nomination_read_frontier=0,
            certification_frontier=0,
            nomination_escrow_digest="escrow",
        )
    with pytest.raises(
        ProspectiveProvenanceUnavailable,
        match="incomplete nomination read set",
    ):
        FrozenHypothesis(
            cell_id="bad-reads",
            members=("x",),
            polarity=AvailabilityState.AVAILABLE,
            lineage_parent_id=None,
            specialization_depth=0,
            discovery_receipt_ids=("r",),
            discovery_receipt_digest=_sha(["r"]),
            birth_frontier=0,
            structural_state="TRIAL",
            nomination_operation="ordinary",
            triggering_receipt_id="r",
            graph_request_root_state="CONFIRMED",
            graph_request_terminal_state="CONFIRMED",
            considered_context_ids=(),
            selected_context_ids=(),
            nomination_read_frontier=0,
            certification_frontier=0,
            nomination_escrow_digest="escrow",
            provenance_kind=ProvenanceKind.EXACT_NOMINATION_READ_SET,
            nomination_read_sets=(),
        )


def _cell_behavior_manifest(cell):
    manifest = cell.to_manifest()
    manifest.update({
        "lineage_parent_id": cell.lineage_parent_id,
        "specialization_depth": cell.specialization_depth,
        "specialization_request_ordinal": (
            cell.specialization_request_ordinal
        ),
        "specialization_proposal_ordinal": (
            cell.specialization_proposal_ordinal
        ),
    })
    manifest.pop("nomination_escrow", None)
    if cell.state is StemCellState.PRUNED:
        # A final tombstone has no authority. Fixed birth polarity may remain
        # as provenance metadata without affecting native behavior.
        manifest["polarity"] = None
    return manifest


def _normalized_growth_audit(envelope):
    audit = asdict(envelope.audit)
    final_pruned_ids = {
        cell_id for cell_id, cell in envelope.cells.items()
        if cell.state is StemCellState.PRUNED
    }
    for review in audit["lifecycle_reviews"]:
        for cell in review["cells"]:
            cell.pop("nomination_escrow", None)
            if cell["cell_id"] in final_pruned_ids:
                cell["polarity"] = None
    return audit


def _learner_behavior_manifest(organism, evaluation_fens):
    classifications = []
    actions = []
    for index, fen in enumerate(evaluation_fens):
        frame = FrameContext(
            f"matched-ledger-evaluation:{index}",
            FrameKind.REAL,
            values={"board": chess.Board(fen)},
        )
        actuation, trace = organism.r0.emit_action_with_trace(frame)
        assert actuation is not None and trace is not None
        actions.append({
            "actuation": asdict(actuation),
            "trace": trace.canonical_manifest(),
        })
        classifications.append(
            organism.classify_trace(trace).to_manifest()
        )
    return {
        "receipts": copy.deepcopy(organism.receipts),
        "evidence": copy.deepcopy(organism.envelope.evidence),
        "cells": {
            cell_id: _cell_behavior_manifest(cell)
            for cell_id, cell in sorted(organism.envelope.cells.items())
        },
        "growth_audit": _normalized_growth_audit(organism.envelope),
        "correction_audit": asdict(organism.envelope.correction_audit),
        "specialization_audit": asdict(
            organism.envelope.specialization_audit
        ),
        "member_specs": sorted(organism.envelope._member_specs),
        "next_cell_index": organism.envelope._next_cell_index,
        "review_count": organism.envelope._review_count,
        "specialization_request_ordinal": (
            organism.envelope._specialization_request_ordinal
        ),
        "specialization_proposal_ordinal": (
            organism.envelope._specialization_proposal_ordinal
        ),
        "graph_snapshot": organism.envelope.graph.to_snapshot(),
        "actions": actions,
        "classifications": classifications,
    }


def _assert_matched_ledger_growth_parity(
    source, receipts, *, evaluation_fens
):
    source.validate_canonical_evidence_ledger()
    for receipt_id, receipt in source.receipts.items():
        assert source.envelope.evidence[receipt_id] == (
            source._record_from_receipt(receipt)
        )

    native_source = copy.deepcopy(source)
    instrumented_source = copy.deepcopy(source)
    assert (
        native_source.continuation_manifest_v3()
        == instrumented_source.continuation_manifest_v3()
    )

    native_source.grow_from_grounded_receipts(receipts)
    wrapper = NativeProspectiveAuthorityV2.from_organism(
        instrumented_source, mode=V2Mode.PROSPECTIVE
    )
    wrapper.nominate_prefix_from_grounded_receipts(receipts)
    instrumented = wrapper.base

    native_manifest = _learner_behavior_manifest(
        native_source, evaluation_fens
    )
    instrumented_manifest = _learner_behavior_manifest(
        instrumented, evaluation_fens
    )
    assert native_manifest == instrumented_manifest
    return native_source, instrumented


def test_noncanonical_receipt_evidence_ledger_rejected_atomically(
    native_fixture,
):
    incoherent = copy.deepcopy(native_fixture["source"])
    assert len(incoherent.receipts) == 8
    incoherent.envelope.evidence.clear()
    incoherent.envelope.rebuild_graph()
    before = incoherent.continuation_digest_v3()

    with pytest.raises(
        RuntimeError,
        match="noncanonical receipt/evidence ledger: identity mismatch",
    ):
        NativeProspectiveAuthorityV2.from_organism(
            incoherent, mode=V2Mode.PROSPECTIVE
        )
    assert incoherent.continuation_digest_v3() == before
    assert incoherent.envelope.nomination_epoch is None
    assert not incoherent.envelope.evidence

    altered = copy.deepcopy(native_fixture["source"])
    evidence_id = next(iter(sorted(altered.envelope.evidence)))
    altered.envelope.evidence[evidence_id] = replace(
        altered.envelope.evidence[evidence_id],
        policy_response=False,
    )
    before = altered.continuation_digest_v3()
    with pytest.raises(
        RuntimeError,
        match="noncanonical receipt/evidence ledger: record mismatch",
    ):
        altered.open_prospective_discovery_epoch()
    assert altered.continuation_digest_v3() == before
    assert altered.envelope.nomination_epoch is None


def test_prospective_escrow_instrumentation_preserves_viewed_tape_behavior(native_fixture):
    donor = NativeProspectiveAuthorityV2.from_organism(
        native_fixture["source"], mode=V2Mode.PROSPECTIVE
    )
    receipts = _ground_receipts(
        donor, native_fixture["negative"][:4], "matched-ledger-parity"
    )
    native, instrumented = _assert_matched_ledger_growth_parity(
        native_fixture["source"],
        receipts,
        evaluation_fens=(
            *native_fixture["positive"][:2],
            *native_fixture["negative"][:2],
        ),
    )
    assert len(native.envelope.audit.proposal_rows) == 12
    assert native.envelope.audit.proposal_rows[8]["members"] == [
        "context:v2_child",
        "tg26s_shared_atom_b45e62de533291522a6d",
    ]
    assert (
        native.envelope.audit.proposal_rows
        == instrumented.envelope.audit.proposal_rows
    )


def test_frozen_96_receipt_matched_ledger_parity_smoke():
    freeze = json.loads(FREEZE.read_text(encoding="utf-8"))
    entry = freeze["krk"]["organisms"][0]["source_artifact"]
    source = TraceNativeCompetenceOrganism.loads(
        gzip.decompress(Path(entry["path"]).read_bytes())
    )
    assert len(source.receipts) == len(source.envelope.evidence) == 96
    source.validate_canonical_evidence_ledger()

    build = load_retired_r0_build(NativeAuthorityLabConfig())
    donor = NativeProspectiveAuthorityV2.from_organism(
        source, mode=V2Mode.PROSPECTIVE
    )
    engineering_fens = tuple(build.pools.gate_validation_decoys[:4])
    receipts = _ground_receipts(
        donor, engineering_fens, "frozen-96-matched-ledger"
    )
    native, instrumented = _assert_matched_ledger_growth_parity(
        source,
        receipts,
        evaluation_fens=engineering_fens,
    )
    assert len(native.receipts) == len(instrumented.receipts) == 100

def test_receipt_evidence_record_parity_rejects_each_mutated_field_atomically(
    native_fixture,
):
    source = native_fixture["source"]
    evidence_id = next(iter(sorted(source.envelope.evidence)))
    mutations = {
        "active_signal_ids": lambda record: replace(
            record,
            active_signal_ids=tuple(reversed(record.active_signal_ids)),
            signal_provenance=tuple(reversed(record.signal_provenance)),
        ),
        "typed_provenance": lambda record: replace(
            record, signal_provenance=()
        ),
        "outcome": lambda record: replace(
            record, observed_completion=not record.observed_completion
        ),
        "actuator": lambda record: replace(
            record, actuator_identity="fabricated-actuator"
        ),
        "completion_terminal": lambda record: replace(
            record, completion_terminal_identity="fabricated-terminal"
        ),
        "policy_response": lambda record: replace(
            record, policy_response=not record.policy_response
        ),
    }
    for name, mutate in mutations.items():
        altered = copy.deepcopy(source)
        altered.envelope.evidence[evidence_id] = mutate(
            altered.envelope.evidence[evidence_id]
        )
        before = altered.continuation_digest_v3()
        with pytest.raises(
            RuntimeError,
            match="noncanonical receipt/evidence ledger: record mismatch",
        ):
            NativeProspectiveAuthorityV2.from_organism(
                altered, mode=V2Mode.PROSPECTIVE
            )
        assert altered.continuation_digest_v3() == before, name
        assert altered.envelope.nomination_epoch is None, name


def test_complete_escrow_frontiers_and_semantic_revalidation(
    native_fixture,
):
    organism = NativeProspectiveAuthorityV2.from_organism(
        native_fixture["source"], mode=V2Mode.PROSPECTIVE
    )
    receipts = _ground_receipts(
        organism, native_fixture["negative"][:4], "complete-escrow"
    )
    organism.nominate_prefix_from_grounded_receipts(receipts)
    ordinals = {
        key: value.event_ordinal
        for key, value in organism.base.receipts.items()
    }
    prospective_ids = organism.base.envelope.nomination_epoch.post_epoch_cell_ids
    assert prospective_ids
    for cell_id in prospective_ids:
        cell = organism.base.envelope.cells[cell_id]
        escrow = cell.nomination_escrow
        assert escrow is not None
        reads = set(escrow.discovery_receipt_ids)
        assert escrow.nomination_read_frontier == max(
            (ordinals[item] for item in reads), default=-1
        )
        assert escrow.certification_frontier == max(
            ordinals[item]
            for item in escrow.discovery_exclusion_receipt_ids
        )
        assert escrow.birth_frontier == escrow.certification_frontier
        selected = tuple(sorted(
            member.split(":", 1)[1]
            for member in cell.members
            if member.startswith("context:")
        ))
        assert escrow.selected_context_ids == selected
        assert set(selected).issubset(escrow.considered_context_ids)
        hypothesis = organism.states.get(cell_id)
        if hypothesis is not None:
            frozen = hypothesis.hypothesis
            assert frozen.nomination_escrow_digest == escrow.escrow_digest
            assert (
                frozen.nomination_read_frontier
                == escrow.nomination_read_frontier
            )
            assert (
                frozen.certification_frontier
                == escrow.certification_frontier
            )

    organism.sync_organism_nominations()
    cell_id = next(iter(organism.states))
    if (
        organism.states[cell_id].hypothesis.initialization_origin
        is InitializationOrigin.HISTORICAL
    ):
        cell_id = next(
            item for item in organism.states
            if organism.states[item].hypothesis.initialization_origin
            is InitializationOrigin.PROSPECTIVE
        )
    for field_name, value in (
        ("nomination_read_frontier", -999),
        ("certification_frontier", 999999),
        ("considered_context_ids", ("fabricated-context",)),
        ("selected_context_ids", ("fabricated-context",)),
        ("graph_request_terminal_state", "FAILED"),
    ):
        altered = copy.deepcopy(organism)
        escrow = altered.base.envelope.cells[cell_id].nomination_escrow
        object.__setattr__(escrow, field_name, value)
        before = altered.continuation_digest()
        with pytest.raises(
            (ProspectiveV2IntegrityError, RuntimeError, ValueError),
            match="frontier|context|graph request|escrow|digest|identity",
        ):
            altered.sync_organism_nominations()
        assert altered.continuation_digest() == before


def test_specialization_transaction_rolls_back_every_failure_boundary(
    native_fixture, monkeypatch,
):
    source = copy.deepcopy(native_fixture["source"])
    source.learning_config = replace(
        source.learning_config,
        lifecycle_connected=True,
        specialization_mode=SpecializationMode.LOCAL_CONTRAST,
    )
    organism = NativeProspectiveAuthorityV2.from_organism(
        source, mode=V2Mode.PROSPECTIVE
    )
    receipt = _ground_receipts(
        organism, native_fixture["negative"][:1], "atomic-specialization"
    )[0]
    boundaries = (
        "receipt_acceptance",
        "evidence_insertion",
        "eligibility",
        "parent_transition",
        "escrow_construction",
        "child_registration",
        "counter_update",
        "wrapper_sync",
    )
    original = GraphNativeCompetenceEnvelope._transaction_checkpoint
    for boundary in boundaries:
        before = organism.continuation_digest()

        def fail_at(self, observed, *, expected=boundary):
            original(self, observed)
            if observed == expected:
                raise RuntimeError(f"injected transaction failure: {expected}")

        with monkeypatch.context() as scoped:
            scoped.setattr(
                GraphNativeCompetenceEnvelope,
                "_transaction_checkpoint",
                fail_at,
            )
            with pytest.raises(
                RuntimeError, match=f"injected transaction failure: {boundary}"
            ):
                organism.observe_grounded_and_sync(receipt)
        assert organism.continuation_digest() == before

    emission, added = organism.observe_grounded_and_sync(receipt)
    assert emission.specialization_child_ids
    assert set(emission.specialization_child_ids).issubset(added)
    assert organism.base.envelope.evidence[receipt.event_id] == (
        organism.base._record_from_receipt(receipt)
    )


def test_experimental_identity_and_candidate_identical_arms_are_immutable(
    native_fixture,
):
    organism = NativeProspectiveAuthorityV2.from_organism(
        native_fixture["source"], mode=V2Mode.PROSPECTIVE
    )
    receipts = _ground_receipts(
        organism, native_fixture["negative"][:4], "identity-seal"
    )
    organism.nominate_prefix_from_grounded_receipts(receipts)
    organism.close_nomination()
    assert organism.experimental_identity is not None

    prospective, legacy = organism.clone_candidate_identical_arms()
    prospective.assert_candidate_parity(legacy)
    assert prospective.mode is V2Mode.PROSPECTIVE
    assert legacy.mode is V2Mode.LEGACY
    assert (
        prospective.experimental_identity["candidate_population_identity"]
        == legacy.experimental_identity["candidate_population_identity"]
    )
    assert (
        prospective.experimental_identity["identity_digest"]
        != legacy.experimental_identity["identity_digest"]
    )
    assert {
        key: value.hypothesis.polarity
        for key, value in prospective.states.items()
    } == {
        key: value.hypothesis.polarity
        for key, value in legacy.states.items()
    }
    assert tuple(inspect.signature(
        organism.clone_candidate_identical_arms
    ).parameters) == ()

    mutations = (
        lambda item: item.experimental_identity.__setitem__(
            "identity_digest", "fabricated"
        ),
        lambda item: item.authority_topology.__setitem__(
            "fabricated", True
        ),
        lambda item: object.__setattr__(
            item.states[next(iter(item.states))].hypothesis,
            "hypothesis_digest",
            "fabricated",
        ),
    )
    for mutate in mutations:
        altered = copy.deepcopy(prospective)
        mutate(altered)
        with pytest.raises(
            ProspectiveV2IntegrityError,
            match="identity|topology|hypothesis|digest",
        ):
            altered.dumps()


def test_topology_digest_tracks_executed_graph_semantics(
    native_fixture, monkeypatch,
):
    organism = NativeProspectiveAuthorityV2.from_organism(
        native_fixture["source"], mode=V2Mode.PROSPECTIVE
    )
    organism.close_nomination()
    topology = organism.authority_topology
    assert topology["graph_snapshot"] == authority_module._build_authority_graph(
        organism.states
    ).to_snapshot()
    assert set(topology["root_confirmation_policies"]) == set(
        authority_module.AUTHORITY_ROLES
    )
    assert all(
        value.endswith(":_authority_terminal")
        for node_id, value in topology["predicate_identities"].items()
        if node_id.startswith("v2:")
    )
    assert topology["lifecycle_constants"] == {
        "minimum_support": authority_module.MIN_SUPPORT,
        "lower_bound": authority_module.LOWER_BOUND,
        "wilson_z": authority_module.WILSON_Z,
        "native_maturity_property": (
            "CompetenceContextCell.is_mature:MATURE_only"
        ),
    }

    def altered_terminal(node, env):
        return True, False

    with monkeypatch.context() as scoped:
        scoped.setattr(
            authority_module, "_authority_terminal", altered_terminal
        )
        with pytest.raises(
            ProspectiveV2IntegrityError,
            match="authority topology identity mismatch",
        ):
            organism.dumps()


def test_v3_schema_native_parity_telemetry_and_tombstone_only_admission(
    native_fixture,
):
    available = NativeProspectiveAuthorityV2.from_organism(
        native_fixture["source"], mode=V2Mode.LEGACY
    )
    available.close_nomination()
    positive = chess.Board(native_fixture["positive"][0])
    _actuation, positive_trace = available.base.r0.emit_action_with_trace(
        FrameContext("v3-available", FrameKind.REAL, values={"board": positive})
    )
    assert positive_trace is not None
    available_emissions = available._graph_measure(positive_trace)
    available_classification = available._classification_from_emissions(
        available.states, available_emissions
    )
    assert available_classification.state is AvailabilityState.AVAILABLE
    telemetry_only_states = copy.deepcopy(available.states)
    for state in telemetry_only_states.values():
        state.success_lower_bound = 0.123456789
    telemetry_classification = available._classification_from_emissions(
        telemetry_only_states, available_emissions
    )
    assert telemetry_classification.state is available_classification.state
    assert (
        telemetry_classification.available_cell_ids
        == available_classification.available_cell_ids
    )
    assert (
        telemetry_classification.formal_available
        == available_classification.formal_available
    )
    assert (
        telemetry_classification.probability
        != available_classification.probability
    )

    live_hypothesis = next(iter(available.states.values())).hypothesis
    with pytest.raises(
        ProspectiveV2IntegrityError,
        match="UNKNOWN is not a live fixed hypothesis polarity",
    ):
        replace(live_hypothesis, polarity=AvailabilityState.UNKNOWN)

    trial_source = copy.deepcopy(native_fixture["source"])
    trial_cell = next(iter(trial_source.envelope.cells.values()))
    trial_cell.stem_cell.state = StemCellState.TRIAL
    trial_source.envelope.rebuild_graph()
    with pytest.raises(
        ProspectiveProvenanceUnavailable,
        match="unsupported historical live TRIAL",
    ):
        NativeProspectiveAuthorityV2.from_organism(
            trial_source, mode=V2Mode.PROSPECTIVE
        )

    refuted_source = copy.deepcopy(native_fixture["source"])
    for cell in refuted_source.envelope.cells.values():
        cell.polarity = AvailabilityState.REFUTED
    refuted_source.envelope.rebuild_graph()
    refuted = NativeProspectiveAuthorityV2.from_organism(
        refuted_source, mode=V2Mode.LEGACY
    )
    refuted.close_nomination()
    negative = chess.Board(native_fixture["negative"][0])
    _actuation, negative_trace = refuted.base.r0.emit_action_with_trace(
        FrameContext("v3-refuted", FrameKind.REAL, values={"board": negative})
    )
    assert negative_trace is not None
    assert refuted._classification_from_emissions(
        refuted.states, refuted._graph_measure(negative_trace)
    ).state is AvailabilityState.REFUTED

    old = copy.deepcopy(available)
    old.schema_version = "native_prospective_evidence_authority_v2.v2"
    with pytest.raises(
        ProspectiveV2IntegrityError, match="unsupported V2 schema"
    ):
        NativeProspectiveAuthorityV2.loads(
            pickle.dumps(old, protocol=pickle.HIGHEST_PROTOCOL)
        )

    tombstone_source = copy.deepcopy(native_fixture["source"])
    for cell in tombstone_source.envelope.cells.values():
        cell.stem_cell.state = StemCellState.PRUNED
        cell.polarity = None
        cell.prune_reason = "historical-tombstone"
    tombstone_source.envelope.rebuild_graph()
    tombstones = NativeProspectiveAuthorityV2.from_organism(
        tombstone_source, mode=V2Mode.PROSPECTIVE
    )
    assert not tombstones.states
    assert len(tombstones.historical_tombstones) == 2
    tombstones.close_nomination()
    restored = NativeProspectiveAuthorityV2.loads(tombstones.dumps())
    assert restored.continuation_manifest() == tombstones.continuation_manifest()

def test_registry_bound_exposure_rejects_fabrication_and_admits_24_of_32():
    freeze = json.loads(FREEZE.read_text(encoding="utf-8"))
    entries = freeze["krk"]["organisms"]
    assert len(entries) == 32

    wrappers = {}
    payloads = {}
    rows_by_organism = {}
    qualifying_fens = {}
    for entry in entries:
        ordinal = int(entry["ordinal"])
        artifact = entry["source_artifact"]
        compressed = Path(artifact["path"]).read_bytes()
        assert hashlib.sha256(compressed).hexdigest() == (
            artifact["compressed_sha256"]
        )
        raw = gzip.decompress(compressed)
        assert hashlib.sha256(raw).hexdigest() == (
            artifact["uncompressed_sha256"]
        )
        source = TraceNativeCompetenceOrganism.loads(raw)
        source.validate_canonical_evidence_ledger()
        wrapper = NativeProspectiveAuthorityV2.from_organism(
            source, mode=V2Mode.PROSPECTIVE
        )
        wrapper.close_nomination()
        organism_id = f"organism-{ordinal:02d}"
        wrappers[organism_id] = wrapper
        payloads[organism_id] = wrapper.dumps()

        unique_rows = []
        seen_fens = set()
        for receipt in sorted(
            source.receipts.values(),
            key=lambda item: item.event_ordinal,
        ):
            if receipt.predecessor_fen in seen_fens:
                continue
            seen_fens.add(receipt.predecessor_fen)
            unique_rows.append((
                receipt.predecessor_fen,
                frozenset(
                    cell_id
                    for cell_id in sorted(wrapper.states)
                    if authority_module._structural_pattern_matches(
                        cell_id,
                        wrapper.states,
                        receipt.decision_trace.ordered_signal_identities,
                    )
                ),
            ))
        assert len(unique_rows) >= 4, organism_id
        rows_by_organism[organism_id] = tuple(unique_rows)

        for cell_id in sorted(wrapper.states):
            matching_fens = tuple(
                fen for fen, matching in unique_rows
                if cell_id in matching
            )
            if len(matching_fens) >= 4:
                qualifying_fens[organism_id] = matching_fens[:4]
                break

    def nonqualifying_selection(rows):
        representatives = {}
        for fen, matching in rows:
            representatives.setdefault(matching, fen)
        distinct = tuple(
            (fen, matching)
            for matching, fen in representatives.items()
        )
        for width in range(1, min(4, len(distinct)) + 1):
            for combination in itertools.combinations(distinct, width):
                common = set(combination[0][1])
                for _fen, matching in combination[1:]:
                    common.intersection_update(matching)
                if common:
                    continue
                selected = [fen for fen, _matching in combination]
                selected.extend(
                    fen for fen, _matching in rows
                    if fen not in selected
                )
                return tuple(selected[:4])
        return None

    nonqualifying_fens = {
        organism_id: selected
        for organism_id, rows in rows_by_organism.items()
        if (selected := nonqualifying_selection(rows)) is not None
    }
    all_ids = set(wrappers)
    required_nonqualifiers = all_ids.difference(qualifying_fens)
    assert len(qualifying_fens) >= 24
    assert len(required_nonqualifiers) <= 8
    assert required_nonqualifiers.issubset(nonqualifying_fens)
    optional_nonqualifiers = sorted(
        set(nonqualifying_fens).difference(required_nonqualifiers)
    )
    nonqualifier_ids = required_nonqualifiers | set(
        optional_nonqualifiers[:8 - len(required_nonqualifiers)]
    )
    qualifier_ids = all_ids.difference(nonqualifier_ids)
    assert len(qualifier_ids) == 24
    assert len(nonqualifier_ids) == 8
    assert qualifier_ids.issubset(qualifying_fens)

    selected_fens = {
        organism_id: (
            qualifying_fens[organism_id]
            if organism_id in qualifier_ids
            else nonqualifying_fens[organism_id]
        )
        for organism_id in sorted(wrappers)
    }

    row_order = tuple(f"engineering-row-{index}" for index in range(4))
    exposure_rows = {
        organism_id: tuple(
            RegisteredV2ExposureRow(
                row_id=row_order[index],
                frame_id=f"registry-canary:{organism_id}:{index}",
                predecessor_fen=fen,
            )
            for index, fen in enumerate(selected_fens[organism_id])
        )
        for organism_id in sorted(wrappers)
    }
    package_hashes = {
        "v2_source": hashlib.sha256(Path(
            "src/recon_lite_chess/autogrowth/"
            "native_prospective_evidence_authority_v2.py"
        ).read_bytes()).hexdigest(),
        "lab_source": hashlib.sha256(Path(
            "src/recon_lite_chess/autogrowth/"
            "native_prospective_evidence_authority_v2_lab.py"
        ).read_bytes()).hexdigest(),
    }
    registry = V2LaboratoryRegistry.freeze(
        payloads,
        exposure_rows=exposure_rows,
        row_order=row_order,
        run_identity="v2-readiness-registry-canary.v1",
        package_hashes=package_hashes,
    )
    assert len(registry.organisms) == 32
    assert len(registry.exposure_rows) == 32

    scans = []
    commitments_by_organism = {}
    for organism_id in sorted(wrappers):
        wrapper = wrappers[organism_id]
        commitments = tuple(
            wrapper.probe_real_exposure(FrameContext(
                row.frame_id,
                FrameKind.REAL,
                values={"board": chess.Board(row.predecessor_fen)},
            ))
            for row in exposure_rows[organism_id]
        )
        assert len({
            item.interaction_fingerprint for item in commitments
        }) == 4
        common = set(commitments[0].matching_cell_ids)
        for item in commitments[1:]:
            common.intersection_update(item.matching_cell_ids)
        assert bool(common) is (organism_id in qualifier_ids)
        commitments_by_organism[organism_id] = commitments
        row = registry.scan(
            organism_id,
            payloads[organism_id],
            commitments,
            tape_identity=registry.tape_identity,
            row_order=row_order,
            run_identity=registry.run_identity,
            package_hashes=package_hashes,
        )
        scans.append(row["scan"])

    adjudication = OutcomeBlindExposureScanner.adjudicate_cohort(scans)
    assert adjudication["qualifying_organisms"] == 24
    assert adjudication["admitted"]

    first_id = sorted(wrappers)[0]
    first_wrapper = wrappers[first_id]
    first_payload = payloads[first_id]
    first_commitments = commitments_by_organism[first_id]
    first_rows = exposure_rows[first_id]

    duplicate_rows = {
        duplicate_id: tuple(
            RegisteredV2ExposureRow(
                row_id=row.row_id,
                frame_id=f"{duplicate_id}:{index}",
                predecessor_fen=row.predecessor_fen,
            )
            for index, row in enumerate(first_rows)
        )
        for duplicate_id in ("duplicate-a", "duplicate-b")
    }
    with pytest.raises(
        ProspectiveV2IntegrityError, match="duplicate serialized organism"
    ):
        V2LaboratoryRegistry.freeze(
            {"duplicate-a": first_payload, "duplicate-b": first_payload},
            exposure_rows=duplicate_rows,
            row_order=row_order,
            run_identity=registry.run_identity,
            package_hashes=package_hashes,
        )
    with pytest.raises(
        ProspectiveV2IntegrityError, match="tape/order/run/package mismatch"
    ):
        registry.scan(
            first_id,
            first_payload,
            first_commitments,
            tape_identity="wrong-tape",
            row_order=row_order,
            run_identity=registry.run_identity,
            package_hashes=package_hashes,
        )
    with pytest.raises(
        ProspectiveV2IntegrityError, match="frozen tape"
    ):
        registry.scan(
            first_id,
            first_payload,
            tuple(reversed(first_commitments)),
            tape_identity=registry.tape_identity,
            row_order=row_order,
            run_identity=registry.run_identity,
            package_hashes=package_hashes,
        )
    with pytest.raises(
        ProspectiveV2IntegrityError, match="frozen tape|duplicate"
    ):
        registry.scan(
            first_id,
            first_payload,
            (*first_commitments[:-1], first_commitments[-2]),
            tape_identity=registry.tape_identity,
            row_order=row_order,
            run_identity=registry.run_identity,
            package_hashes=package_hashes,
        )
    fabricated = _resign_commitment(replace(
        first_commitments[0],
        source_binding_identity="re-signed-fabrication",
    ))
    with pytest.raises(
        ProspectiveV2IntegrityError,
        match="differs from exact organism|binding",
    ):
        registry.scan(
            first_id,
            first_payload,
            (fabricated, *first_commitments[1:]),
            tape_identity=registry.tape_identity,
            row_order=row_order,
            run_identity=registry.run_identity,
            package_hashes=package_hashes,
        )
    with pytest.raises(
        ProspectiveV2IntegrityError,
        match="noncanonical or post-outcome row",
    ):
        registry.scan(
            first_id,
            first_payload,
            (
                {"observed_outcome": True},
                *first_commitments[1:],
            ),
            tape_identity=registry.tape_identity,
            row_order=row_order,
            run_identity=registry.run_identity,
            package_hashes=package_hashes,
        )

    open_wrapper = NativeProspectiveAuthorityV2.from_organism(
        TraceNativeCompetenceOrganism.loads(gzip.decompress(
            Path(entries[0]["source_artifact"]["path"]).read_bytes()
        )),
        mode=V2Mode.PROSPECTIVE,
    )
    with pytest.raises(
        ProspectiveV2IntegrityError, match="nomination is not closed"
    ):
        V2LaboratoryRegistry.freeze(
            {"open": open_wrapper.dumps()},
            exposure_rows={"open": tuple(
                RegisteredV2ExposureRow(
                    row_id=row.row_id,
                    frame_id=f"open:{index}",
                    predecessor_fen=row.predecessor_fen,
                )
                for index, row in enumerate(first_rows)
            )},
            row_order=row_order,
            run_identity=registry.run_identity,
            package_hashes=package_hashes,
        )

    pending_wrapper = copy.deepcopy(first_wrapper)
    pending_wrapper.open_real_event(FrameContext(
        "pending-registry-event",
        FrameKind.REAL,
        values={"board": chess.Board(first_rows[0].predecessor_fen)},
    ))
    with pytest.raises(
        ProspectiveV2IntegrityError,
        match="not pre-outcome and transaction-closed",
    ):
        V2LaboratoryRegistry.freeze(
            {"pending": pending_wrapper.dumps()},
            exposure_rows={"pending": tuple(
                RegisteredV2ExposureRow(
                    row_id=row.row_id,
                    frame_id=f"pending:{index}",
                    predecessor_fen=row.predecessor_fen,
                )
                for index, row in enumerate(first_rows)
            )},
            row_order=row_order,
            run_identity=registry.run_identity,
            package_hashes=package_hashes,
        )

    with pytest.raises(
        ProspectiveV2IntegrityError,
        match="noncanonical nested exposure schema",
    ):
        V2LaboratoryRegistry.freeze(
            {"bad": first_payload},
            exposure_rows={"bad": ({"row_id": row_order[0]},)},
            row_order=row_order,
            run_identity=registry.run_identity,
            package_hashes=package_hashes,
        )

    learner_manifest = json.dumps(
        first_wrapper.continuation_manifest(), sort_keys=True
    )
    for forbidden in (
        registry.registry_id,
        registry.tape_identity,
        registry.run_identity,
        *row_order,
        *package_hashes.values(),
    ):
        assert forbidden not in learner_manifest
