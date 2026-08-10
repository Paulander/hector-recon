from __future__ import annotations

import hashlib
import inspect
import pickle

import pytest

from recon_lite import FrameContext, FrameKind
from recon_lite_hector.nodes import StemCellState, StemCellTerminal

from recon_lite_chess.autogrowth.native_competence_envelope import (
    AVAILABILITY_ERROR_ID,
    AvailabilityState,
    CompetenceContextCell,
    CompetenceContextGrowthGenome,
    CompetenceEvidenceRecord,
    EnvelopeClassification,
    GraphNativeCompetenceEnvelope,
    MixedOutcomeDisposition,
    wilson_lower_bound,
)


def _record(
    key: str,
    signals: tuple[str, ...],
    outcome: bool,
) -> CompetenceEvidenceRecord:
    return CompetenceEvidenceRecord(
        evidence_key=key,
        active_signal_ids=signals,
        policy_response=True,
        observed_completion=outcome,
        actuator_identity="chess_move:a1a2",
        completion_terminal_identity="mate",
    )


def _cell(
    cell_id: str,
    members: tuple[str, ...],
    *,
    state: StemCellState = StemCellState.TRIAL,
    polarity: AvailabilityState | None = None,
) -> CompetenceContextCell:
    stem = StemCellTerminal(cell_id)
    stem.state = state
    stem.trial_node_id = cell_id
    return CompetenceContextCell(
        cell_id=cell_id,
        members=members,
        born_round=0,
        born_request_ordinal=0,
        stem_cell=stem,
        polarity=polarity,
    )


def test_frozen_wilson_rule_needs_four_pure_examples() -> None:
    assert wilson_lower_bound(3, 3, 1.6448536269514722) < 0.55
    assert wilson_lower_bound(4, 4, 1.6448536269514722) > 0.55


def test_trial_is_shadow_only_then_mature_available_routes_formally() -> None:
    envelope = GraphNativeCompetenceEnvelope()
    trial = _cell("competence_context_0000", ("atom:a",))
    envelope.cells[trial.cell_id] = trial
    envelope.rebuild_graph()
    assert envelope.classify(
        ("atom:a",), policy_response=True
    ).state == AvailabilityState.UNKNOWN
    for index in range(4):
        envelope.add_unique_evidence(
            _record(f"success-{index}", ("atom:a",), True)
        )
    envelope._review_lifecycle(final=False)
    envelope.rebuild_graph()
    result = envelope.classify(("atom:a",), policy_response=True)
    assert trial.state == StemCellState.MATURE
    assert trial.polarity == AvailabilityState.AVAILABLE
    assert result.state == AvailabilityState.AVAILABLE
    assert result.available_cell_ids == (trial.cell_id,)
    assert envelope.classify(
        ("atom:a",), policy_response=False
    ).state == AvailabilityState.UNKNOWN


def test_mixed_outcome_finalization_clones_to_shadow_or_tombstone_only() -> None:
    envelope = GraphNativeCompetenceEnvelope()
    mixed = _cell(
        "competence_context_0000",
        ("atom:mixed",),
        polarity=AvailabilityState.AVAILABLE,
    )
    mixed.lineage_parent_id = "lineage:parent"
    mixed.specialization_depth = 1
    sparse = _cell(
        "competence_context_0001",
        ("atom:sparse",),
        polarity=AvailabilityState.AVAILABLE,
    )
    envelope.cells = {mixed.cell_id: mixed, sparse.cell_id: sparse}
    for index, outcome in enumerate((True, False, True, False)):
        envelope.add_unique_evidence(
            _record(f"mixed-{index}", ("atom:mixed",), outcome)
        )
    envelope.add_unique_evidence(
        _record("sparse-0", ("atom:sparse",), True)
    )
    envelope.rebuild_graph()

    before = pickle.dumps(envelope, protocol=pickle.HIGHEST_PROTOCOL)
    shadow = pickle.loads(before)
    tombstone = pickle.loads(before)
    shadow._review_lifecycle(
        final=True,
        mixed_outcome_disposition=MixedOutcomeDisposition.RETAIN_SHADOW,
    )
    tombstone._review_lifecycle(
        final=True,
        mixed_outcome_disposition=MixedOutcomeDisposition.TOMBSTONE,
    )
    shadow.rebuild_graph()
    tombstone.rebuild_graph()

    retained = shadow.cells[mixed.cell_id]
    removed = tombstone.cells[mixed.cell_id]
    assert retained.is_shadow
    assert retained.state is StemCellState.DORMANT
    assert removed.state is StemCellState.PRUNED
    assert retained.prune_reason == removed.prune_reason == "mixed_outcomes"
    assert retained.members == removed.members == mixed.members
    assert retained.polarity is removed.polarity is mixed.polarity
    assert retained.lineage_parent_id == removed.lineage_parent_id
    assert retained.specialization_depth == removed.specialization_depth
    assert shadow.cells[sparse.cell_id].state is StemCellState.PRUNED
    assert tombstone.cells[sparse.cell_id].state is StemCellState.PRUNED
    assert shadow.cells[sparse.cell_id].prune_reason == "insufficient_support"
    assert tombstone.cells[sparse.cell_id].prune_reason == "insufficient_support"

    retained_state = retained.stem_cell.state
    retained.stem_cell.state = removed.stem_cell.state
    assert retained.to_manifest() == removed.to_manifest()
    retained.stem_cell.state = retained_state


def test_dormant_shadow_has_no_envelope_decision_or_correction_path() -> None:
    envelope = GraphNativeCompetenceEnvelope()
    shadow = _cell(
        "competence_context_0000",
        ("atom:shadow",),
        state=StemCellState.DORMANT,
        polarity=AvailabilityState.AVAILABLE,
    )
    shadow.prune_reason = "mixed_outcomes"
    shadow.support = 4
    shadow.successes = 2
    shadow.failures = 2
    envelope.cells[shadow.cell_id] = shadow
    envelope.rebuild_graph()

    assert shadow.is_shadow
    assert not shadow.competes_for_active_capacity
    assert envelope.classify(
        ("atom:shadow",), policy_response=True
    ).state is AvailabilityState.UNKNOWN
    before = (shadow.support, shadow.evidence_keys)
    emission = envelope.observe_real_outcome(
        _real_frame("shadow-correction-exclusion"),
        _record("later-real", ("atom:shadow",), True),
        lifecycle_connected=True,
    )
    assert emission.matching_cell_ids == ()
    assert emission.transitioned_cell_ids == ()
    assert (shadow.support, shadow.evidence_keys) == before


def test_refuted_is_separate_and_conflict_fails_to_unknown() -> None:
    envelope = GraphNativeCompetenceEnvelope()
    positive = _cell(
        "competence_context_0000",
        ("atom:a",),
        state=StemCellState.MATURE,
        polarity=AvailabilityState.AVAILABLE,
    )
    positive.success_lower_bound = 0.7
    positive.uncertainty = 0.3
    negative = _cell(
        "competence_context_0001",
        ("atom:b",),
        state=StemCellState.MATURE,
        polarity=AvailabilityState.REFUTED,
    )
    negative.failure_lower_bound = 0.8
    negative.uncertainty = 0.2
    envelope.cells = {positive.cell_id: positive, negative.cell_id: negative}
    envelope.rebuild_graph()
    assert envelope.classify(
        ("atom:b",), policy_response=True
    ).state == AvailabilityState.REFUTED
    conflict = envelope.classify(
        ("atom:a", "atom:b"), policy_response=True
    )
    assert conflict.state == AvailabilityState.UNKNOWN
    assert conflict.formal_available is True
    assert conflict.formal_refuted is True


@pytest.mark.parametrize(
    ("polarity", "matching_signal", "expected_state"),
    [
        (AvailabilityState.AVAILABLE, "atom:a", AvailabilityState.AVAILABLE),
        (AvailabilityState.AVAILABLE, "atom:b", AvailabilityState.AVAILABLE),
        (AvailabilityState.REFUTED, "atom:a", AvailabilityState.REFUTED),
        (AvailabilityState.REFUTED, "atom:b", AvailabilityState.REFUTED),
    ],
)
def test_two_mature_cells_use_one_of_n_semantics(
    polarity: AvailabilityState,
    matching_signal: str,
    expected_state: AvailabilityState,
) -> None:
    envelope = GraphNativeCompetenceEnvelope()
    first = _cell(
        "competence_context_0000",
        ("atom:a",),
        state=StemCellState.MATURE,
        polarity=polarity,
    )
    second = _cell(
        "competence_context_0001",
        ("atom:b",),
        state=StemCellState.MATURE,
        polarity=polarity,
    )
    for cell in (first, second):
        cell.success_lower_bound = 0.7
        cell.failure_lower_bound = 0.7
        cell.uncertainty = 0.3
    envelope.cells = {first.cell_id: first, second.cell_id: second}
    envelope.rebuild_graph()

    result = envelope.classify((matching_signal,), policy_response=True)

    assert result.state == expected_state
    expected_id = first.cell_id if matching_signal == "atom:a" else second.cell_id
    if polarity == AvailabilityState.AVAILABLE:
        assert result.available_cell_ids == (expected_id,)
        assert result.refuted_cell_ids == ()
    else:
        assert result.available_cell_ids == ()
        assert result.refuted_cell_ids == (expected_id,)


def test_available_and_refuted_conflict_is_unknown_with_independent_formal_flags() -> None:
    envelope = GraphNativeCompetenceEnvelope()
    available = _cell(
        "competence_context_0000",
        ("atom:a",),
        state=StemCellState.MATURE,
        polarity=AvailabilityState.AVAILABLE,
    )
    refuted = _cell(
        "competence_context_0001",
        ("atom:b",),
        state=StemCellState.MATURE,
        polarity=AvailabilityState.REFUTED,
    )
    available.success_lower_bound = 0.7
    refuted.failure_lower_bound = 0.7
    envelope.cells = {available.cell_id: available, refuted.cell_id: refuted}
    envelope.rebuild_graph()

    result = envelope.classify(("atom:a", "atom:b"), policy_response=True)

    assert result.state == AvailabilityState.UNKNOWN
    assert result.available_cell_ids == (available.cell_id,)
    assert result.refuted_cell_ids == (refuted.cell_id,)
    assert result.formal_available is True
    assert result.formal_refuted is True


@pytest.mark.parametrize("policy_response", [False, True])
def test_formal_classification_flags_track_matching_cells_independently_of_conflict(
    policy_response: bool,
) -> None:
    envelope = GraphNativeCompetenceEnvelope()
    available = _cell(
        "competence_context_0000",
        ("atom:a",),
        state=StemCellState.MATURE,
        polarity=AvailabilityState.AVAILABLE,
    )
    refuted = _cell(
        "competence_context_0001",
        ("atom:b",),
        state=StemCellState.MATURE,
        polarity=AvailabilityState.REFUTED,
    )
    available.success_lower_bound = 0.7
    refuted.failure_lower_bound = 0.7
    envelope.cells = {available.cell_id: available, refuted.cell_id: refuted}
    envelope.rebuild_graph()

    for signals in (("atom:a",), ("atom:b",), ("atom:a", "atom:b"), ()):
        result = envelope.classify(signals, policy_response=policy_response)
        assert result.formal_available == (
            policy_response and bool(result.available_cell_ids)
        )
        assert result.formal_refuted == (
            policy_response and bool(result.refuted_cell_ids)
        )


def test_availability_error_is_graph_native_and_distinct_from_value() -> None:
    envelope = GraphNativeCompetenceEnvelope()
    unknown = envelope.classify(("atom:a",), policy_response=True)
    emission = envelope.emit_growth_request(
        observed_completion=True,
        classification=unknown,
    )
    assert emission.emitted is True
    assert emission.availability_error == 0.5
    node = envelope.graph.nodes[AVAILABILITY_ERROR_ID]
    assert node.meta["distinct_from_value_residual"] is True
    available = EnvelopeClassification(
        state=AvailabilityState.AVAILABLE,
        probability=0.8,
        uncertainty=0.2,
        available_cell_ids=("cell",),
        refuted_cell_ids=(),
        formal_available=True,
        formal_refuted=False,
        policy_response=True,
    )
    no_request = envelope.emit_growth_request(
        observed_completion=True,
        classification=available,
    )
    assert no_request.emitted is False
    assert no_request.availability_error == 0.0


def test_growth_genome_is_deterministic_content_blind_and_recursive() -> None:
    genome = CompetenceContextGrowthGenome(2026071606)
    kwargs = {
        "active_base_ids": ("atom:c", "atom:a", "atom:b"),
        "active_mature_context_ids": ("competence_context_0001",),
        "round_index": 2,
        "request_ordinal": 7,
    }
    first = genome.propose(**kwargs)
    second = genome.propose(**kwargs)
    assert first == second
    assert first is not None
    assert len(first.members) == 2
    assert sum(member.startswith("context:") for member in first.members) == 1


def test_unique_evidence_cannot_be_double_grounded() -> None:
    envelope = GraphNativeCompetenceEnvelope()
    record = _record("unique", ("atom:a",), True)
    assert envelope.add_unique_evidence(record) is True
    assert envelope.add_unique_evidence(record) is False
    changed = _record("unique", ("atom:a",), False)
    try:
        envelope.add_unique_evidence(changed)
    except RuntimeError as exc:
        assert "collision" in str(exc)
    else:
        raise AssertionError("different observation reused one evidence key")


def test_fixed_growth_is_self_materialized_and_serializable_without_fen() -> None:
    records = tuple(
        _record(f"p-{index}", ("atom:a", "atom:b", f"atom:{index % 2}"), True)
        for index in range(4)
    ) + tuple(
        _record(f"n-{index}", ("atom:c", "atom:d", f"atom:{index % 2}"), False)
        for index in range(4)
    )
    envelope = GraphNativeCompetenceEnvelope()
    audit = envelope.grow(records)
    assert audit.request_opportunities == 24
    assert audit.graph_request_emissions > 0
    assert audit.admitted_proposals > 0
    assert len(envelope.cells) > 0
    assert any(cell.state == StemCellState.MATURE for cell in envelope.cells.values())
    payload = pickle.dumps(envelope, protocol=pickle.HIGHEST_PROTOCOL)
    assert b" w - " not in payload
    restored = pickle.loads(payload)
    assert restored.to_manifest() == envelope.to_manifest()


def _real_frame(label: str = "synthetic") -> FrameContext:
    return FrameContext(frame_id=label, kind=FrameKind.REAL, values={})


def _mature_envelope(
    *cells: tuple[str, tuple[str, ...], AvailabilityState]
) -> GraphNativeCompetenceEnvelope:
    envelope = GraphNativeCompetenceEnvelope()
    for cell_id, members, polarity in cells:
        cell = _cell(
            cell_id,
            members,
            state=StemCellState.MATURE,
            polarity=polarity,
        )
        cell.support = 4
        cell.successes = 4 if polarity == AvailabilityState.AVAILABLE else 0
        cell.failures = 4 if polarity == AvailabilityState.REFUTED else 0
        cell.success_lower_bound = 0.6 if polarity == AvailabilityState.AVAILABLE else 0.0
        cell.failure_lower_bound = 0.6 if polarity == AvailabilityState.REFUTED else 0.0
        envelope.cells[cell_id] = cell
    envelope.rebuild_graph()
    return envelope


def test_graph_local_failure_revokes_only_active_available_cell() -> None:
    envelope = _mature_envelope(
        ("broad", ("atom:a",), AvailabilityState.AVAILABLE),
        ("sibling", ("atom:a", "atom:b"), AvailabilityState.AVAILABLE),
        ("inactive", ("atom:c",), AvailabilityState.AVAILABLE),
    )
    assert envelope.classify(("atom:a",), policy_response=True).available_cell_ids == (
        "broad",
    )

    emission = envelope.observe_real_outcome(
        _real_frame(), _record("real-failure", ("atom:a",), False),
        lifecycle_connected=True,
    )

    assert emission.contradiction_cell_ids == ("broad",)
    assert emission.transitioned_cell_ids == ("broad",)
    assert envelope.cells["broad"].state == StemCellState.PROBATION
    assert envelope.cells["broad"].failures == 1
    assert envelope.cells["sibling"].state == StemCellState.MATURE
    assert envelope.cells["inactive"].state == StemCellState.MATURE
    assert envelope.classify(("atom:a",), policy_response=True).state == (
        AvailabilityState.UNKNOWN
    )


def test_supporting_outcome_preserves_mature_siblings_and_two_or_cells_revoke() -> None:
    envelope = _mature_envelope(
        ("first", ("atom:a",), AvailabilityState.AVAILABLE),
        ("second", ("atom:b",), AvailabilityState.AVAILABLE),
    )
    support = envelope.observe_real_outcome(
        _real_frame("support"),
        _record("support", ("atom:a", "atom:b"), True),
        lifecycle_connected=True,
    )
    assert support.supporting_cell_ids == ("first", "second")
    assert support.contradiction_cell_ids == ()
    assert all(cell.state == StemCellState.MATURE for cell in envelope.cells.values())

    failure = envelope.observe_real_outcome(
        _real_frame("failure"),
        _record("failure", ("atom:a", "atom:b"), False),
        lifecycle_connected=True,
    )
    assert failure.contradiction_cell_ids == ("first", "second")
    assert failure.transitioned_cell_ids == ("first", "second")
    assert all(cell.state == StemCellState.PROBATION for cell in envelope.cells.values())


def test_refuted_polarity_is_revoked_symmetrically() -> None:
    envelope = _mature_envelope(
        ("refuted", ("atom:a",), AvailabilityState.REFUTED),
    )
    assert envelope.classify(("atom:a",), policy_response=True).state == (
        AvailabilityState.REFUTED
    )
    emission = envelope.observe_real_outcome(
        _real_frame(), _record("completion", ("atom:a",), True),
        lifecycle_connected=True,
    )
    assert emission.contradiction_cell_ids == ("refuted",)
    assert envelope.cells["refuted"].state == StemCellState.PROBATION
    assert envelope.classify(("atom:a",), policy_response=True).state == (
        AvailabilityState.UNKNOWN
    )


def test_duplicate_evidence_is_idempotent_and_disconnected_correction_is_telemetry_only() -> None:
    envelope = _mature_envelope(
        ("broad", ("atom:a",), AvailabilityState.AVAILABLE),
    )
    record = _record("unique-failure", ("atom:a",), False)
    first = envelope.observe_real_outcome(
        _real_frame(), record, lifecycle_connected=False
    )
    first_state = pickle.dumps(envelope, protocol=pickle.HIGHEST_PROTOCOL)
    duplicate = envelope.observe_real_outcome(
        _real_frame(), record, lifecycle_connected=True
    )
    assert first.contradiction_cell_ids == ("broad",)
    assert first.transitioned_cell_ids == ()
    assert envelope.cells["broad"].state == StemCellState.MATURE
    assert duplicate.evidence_inserted is False
    assert duplicate.contradiction_cell_ids == ()
    assert envelope.cells["broad"].support == 1
    assert envelope.correction_audit.contradiction_hits == 1
    assert envelope.correction_audit.duplicate_observations == 1
    assert first_state != pickle.dumps(envelope, protocol=pickle.HIGHEST_PROTOCOL)


def test_probation_and_evidence_survive_serialization() -> None:
    envelope = _mature_envelope(
        ("broad", ("atom:a",), AvailabilityState.AVAILABLE),
    )
    envelope.observe_real_outcome(
        _real_frame(), _record("failure", ("atom:a",), False),
        lifecycle_connected=True,
    )
    restored = pickle.loads(
        pickle.dumps(envelope, protocol=pickle.HIGHEST_PROTOCOL)
    )
    assert restored.to_manifest() == envelope.to_manifest()
    assert restored.cells["broad"].state == StemCellState.PROBATION
    assert restored.cells["broad"].evidence_keys == ("failure",)


def test_virtual_correction_is_rejected_without_persistent_mutation() -> None:
    envelope = _mature_envelope(
        ("broad", ("atom:a",), AvailabilityState.AVAILABLE),
    )
    before = hashlib.sha256(
        pickle.dumps(envelope, protocol=pickle.HIGHEST_PROTOCOL)
    ).hexdigest()
    with pytest.raises(ValueError, match="REAL FrameContext"):
        envelope.observe_real_outcome(
            FrameContext("dream", FrameKind.VIRTUAL, values={}),
            _record("dream-failure", ("atom:a",), False),
            lifecycle_connected=True,
        )
    after = hashlib.sha256(
        pickle.dumps(envelope, protocol=pickle.HIGHEST_PROTOCOL)
    ).hexdigest()
    assert after == before


def test_connected_correction_api_cannot_accept_responsible_cell_identity() -> None:
    signature = inspect.signature(GraphNativeCompetenceEnvelope.observe_real_outcome)
    assert "cell_id" not in signature.parameters
    assert "responsible_cell_id" not in signature.parameters
    envelope = _mature_envelope(
        ("broad", ("atom:a",), AvailabilityState.AVAILABLE),
    )
    with pytest.raises(TypeError):
        envelope.observe_real_outcome(
            _real_frame(),
            _record("failure", ("atom:a",), False),
            lifecycle_connected=True,
            responsible_cell_id="broad",  # type: ignore[call-arg]
        )
