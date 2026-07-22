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
    CanonicalExposureCommitment,
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
        ProspectiveProvenanceUnavailable, match="live historical candidate"
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


def test_trigger_fixed_polarity_behavior_gate_aborts_on_context_divergence(
    native_fixture,
):
    """Preserve the binding readiness abort; do not tune this divergence away."""

    donor = NativeProspectiveAuthorityV2.from_organism(
        native_fixture["source"], mode=V2Mode.PROSPECTIVE
    )
    receipts = _ground_receipts(
        donor, native_fixture["negative"][:4], "behavior-readiness-abort"
    )
    baseline = copy.deepcopy(native_fixture["source"])
    baseline.grow_from_grounded_receipts(receipts)

    instrumented = NativeProspectiveAuthorityV2.from_organism(
        native_fixture["source"], mode=V2Mode.PROSPECTIVE
    )
    instrumented.nominate_prefix_from_grounded_receipts(receipts)
    observed = instrumented.base

    behavior_keys = (
        "round_index", "request_ordinal", "members", "genome_seed",
        "graph_request_state", "admitted", "reason", "cell_id",
    )
    baseline_rows = [
        {key: row.get(key) for key in behavior_keys}
        for row in baseline.envelope.audit.proposal_rows
    ]
    instrumented_rows = [
        {key: row.get(key) for key in behavior_keys}
        for row in observed.envelope.audit.proposal_rows
    ]
    differences = tuple(
        (index, left, right)
        for index, (left, right) in enumerate(
            zip(baseline_rows, instrumented_rows)
        )
        if left != right
    )
    assert differences
    index, native_row, escrow_row = differences[0]
    assert index == 8
    assert native_row["round_index"] == escrow_row["round_index"] == 2
    assert native_row["request_ordinal"] == escrow_row["request_ordinal"] == 0
    assert native_row["members"] == [
        "context:competence_context_0001",
        "tg26s_shared_atom_b45e62de533291522a6d",
    ]
    assert escrow_row["members"] == [
        "context:v2_child",
        "tg26s_shared_atom_b45e62de533291522a6d",
    ]
    assert native_row["cell_id"] == escrow_row["cell_id"] == (
        "competence_context_0007"
    )
