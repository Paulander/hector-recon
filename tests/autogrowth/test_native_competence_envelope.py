from __future__ import annotations

import pickle

import pytest

from recon_lite_hector.nodes import StemCellState, StemCellTerminal

from recon_lite_chess.autogrowth.native_competence_envelope import (
    AVAILABILITY_ERROR_ID,
    AvailabilityState,
    CompetenceContextCell,
    CompetenceContextGrowthGenome,
    CompetenceEvidenceRecord,
    EnvelopeClassification,
    GraphNativeCompetenceEnvelope,
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
