from __future__ import annotations

import copy
from dataclasses import asdict, fields
import pickle

import pytest

from recon_lite import FrameKind
from recon_lite_chess.autogrowth.native_authority_handover import (
    GraphActuation,
    GraphSignalTrace,
    GraphTerminalSignal,
)
from recon_lite_chess.autogrowth.native_competence_envelope import (
    AvailabilityState,
    NOMINATION_ESCROW_V1,
    NOMINATION_ESCROW_V2,
    NominationEscrow,
)
from recon_lite_chess.autogrowth.native_residual_consensus_candidate_allocation import (
    AllocationMode,
    ResidualConsensusGrowthGenome,
    ResidualConsensusMemory,
    responsibility_derangement,
)
from recon_lite_chess.autogrowth.native_trace_competence_authority import (
    GroundedOutcomeReceipt,
)


def _receipt(index: int, *, positive: bool) -> GroundedOutcomeReceipt:
    identities = (
        ("opaque:a", "opaque:b", "opaque:c", f"opaque:p{index % 5}")
        if positive else
        ("opaque:a", "opaque:b", f"opaque:n{index % 5}", "opaque:z")
    )
    actuation = GraphActuation(
        actuator_identity="opaque:actuator",
        move_uci="a1a2",
        option_identity="opaque:option",
        activation=1.0,
        candidate_count=1,
        formal_ticks=1,
    )
    signals = tuple(
        GraphTerminalSignal(
            identity=identity,
            role="BASE_TERMINAL",
            source_node_identity=identity,
            terminal_kind="opaque",
            provenance="test_graph_trace",
        )
        for identity in identities
    )
    trace = GraphSignalTrace(
        frame_id=f"real:{index}",
        frame_kind=FrameKind.REAL.name,
        source_organism_identity="opaque:source",
        source_state_identity="opaque:state",
        option_identity=actuation.option_identity,
        actuation=actuation,
        confirmed_base_terminal_node_ids=identities,
        confirmed_mature_composite_ids=(),
        terminal_signals=signals,
    )
    return GroundedOutcomeReceipt(
        event_id=f"event:{index:02d}",
        event_ordinal=index,
        context_fingerprint=f"physical:{index:02d}",
        decision_trace=trace,
        predecessor_fen="8/8/8/8/8/8/8/K6k w - - 0 1",
        successor_fen="8/8/8/8/8/8/K7/7k b - - 1 1",
        completion_terminal_identity="opaque:completion",
        completion_terminal_role="OUTCOME_GROUNDED_COMPLETION",
        completion_terminal_provenance="test",
        observed_terminal_result=positive,
        issuer_identity="test",
        signature="test",
    )


def _memory() -> ResidualConsensusMemory:
    memory = ResidualConsensusMemory()
    for index in range(64):
        positive = index % 2 == 0
        assert memory.ingest(
            frame_kind=FrameKind.REAL,
            receipt=_receipt(index, positive=positive),
            pre_outcome_state=AvailabilityState.UNKNOWN,
            pre_outcome_probability=0.5,
            signed_availability_residual=0.5 if positive else -0.5,
        )
    memory.freeze()
    return memory


def test_unique_real_memory_is_idempotent_and_virtual_read_only() -> None:
    memory = ResidualConsensusMemory()
    receipt = _receipt(0, positive=True)
    assert memory.ingest(
        frame_kind=FrameKind.REAL,
        receipt=receipt,
        pre_outcome_state=AvailabilityState.UNKNOWN,
        pre_outcome_probability=0.5,
        signed_availability_residual=0.5,
    )
    assert not memory.ingest(
        frame_kind=FrameKind.REAL,
        receipt=receipt,
        pre_outcome_state=AvailabilityState.UNKNOWN,
        pre_outcome_probability=0.5,
        signed_availability_residual=0.5,
    )
    before = memory.manifest()
    with pytest.raises(ValueError, match="REAL interactions only"):
        memory.ingest(
            frame_kind=FrameKind.VIRTUAL,
            receipt=_receipt(1, positive=False),
            pre_outcome_state=AvailabilityState.UNKNOWN,
            pre_outcome_probability=0.5,
            signed_availability_residual=-0.5,
        )
    assert memory.manifest() == before


def test_responsibility_derangement_is_engaged_and_no_fixed_point() -> None:
    memory = _memory()
    mapping, audit = responsibility_derangement(
        memory.ordered_events, seed=9173
    )
    assert set(mapping) == set(memory.events)
    assert audit["fixed_points"] == 0
    assert audit["polarity_changes"] >= 16
    assert sorted(mapping.values()) == sorted(mapping)


def test_primary_allocators_share_bounded_without_replacement_search() -> None:
    memories = [_memory() for _ in range(3)]
    mapping, _audit = responsibility_derangement(
        memories[1].ordered_events, seed=9173
    )
    genomes = (
        ResidualConsensusGrowthGenome(
            seed=9173, memory=memories[0],
            mode=AllocationMode.TRUE_CONSENSUS,
        ),
        ResidualConsensusGrowthGenome(
            seed=9173, memory=memories[1],
            mode=AllocationMode.RESPONSIBILITY_DERANGED,
            derangement=mapping,
        ),
        ResidualConsensusGrowthGenome(
            seed=9173, memory=memories[2],
            mode=AllocationMode.HASH_WITHOUT_REPLACEMENT,
        ),
    )
    kwargs = {
        "active_base_ids": tuple(
            ["opaque:a", "opaque:b", "opaque:c", "opaque:z"]
            + [f"opaque:p{index}" for index in range(5)]
            + [f"opaque:n{index}" for index in range(5)]
        ),
        "active_mature_context_ids": (),
        "round_index": 2,
        "request_ordinal": 0,
    }
    first = [genome.propose(**kwargs) for genome in genomes]
    second = [genome.propose(**kwargs) for genome in genomes]
    assert all(item is not None for item in first)
    assert all(item is None for item in second)
    manifests = [genome.manifest() for genome in genomes]
    matched_fields = (
        "proposal_slots_consumed",
        "unique_candidate_tuples_examined",
        "candidate_score_evaluations",
        "duplicate_candidate_slots",
        "proposal_slots_by_tuple_width",
        "attempted_pattern_digest",
    )
    assert len({
        tuple(str(manifest[field]) for field in matched_fields)
        for manifest in manifests
    }) == 1
    assert first[0].consensus_read_ids == tuple(sorted(memories[0].events))
    assert first[1].consensus_read_ids == tuple(sorted(memories[1].events))
    assert first[2].consensus_read_ids == ()


def _escrow(categories, version: str) -> NominationEscrow:
    return NominationEscrow(
        operation="ordinary",
        fixed_polarity=AvailabilityState.AVAILABLE,
        categorized_reads=categories,
        transitive_ancestor_receipt_ids=(),
        discovery_exclusion_receipt_ids=("event:00", "event:01"),
        birth_frontier=1,
        triggering_receipt_id="event:00",
        graph_request_root_state="CONFIRMED",
        graph_request_terminal_state="CONFIRMED",
        considered_context_ids=(),
        selected_context_ids=(),
        nomination_read_frontier=1,
        certification_frontier=1,
        escrow_schema_version=version,
    )


def test_consensus_escrow_is_complete_and_v1_manifest_stays_unversioned() -> None:
    v1 = _escrow((
        ("direct", ("event:00",)),
        ("parent_support", ()),
        ("eligibility", ()),
        ("contradiction_trigger", ()),
    ), NOMINATION_ESCROW_V1)
    assert "escrow_schema_version" not in v1.manifest()
    v2 = _escrow((
        ("direct", ("event:00",)),
        ("parent_support", ()),
        ("eligibility", ()),
        ("contradiction_trigger", ()),
        ("consensus_reads", ("event:00", "event:01")),
    ), NOMINATION_ESCROW_V2)
    assert v2.manifest()["escrow_schema_version"] == NOMINATION_ESCROW_V2
    assert dict(v2.categorized_reads)["consensus_reads"] == (
        "event:00", "event:01"
    )
    assert v2.discovery_receipt_ids == ("event:00", "event:01")


@pytest.mark.parametrize("version", (NOMINATION_ESCROW_V1, NOMINATION_ESCROW_V2))
def test_nomination_escrow_deepcopy_is_field_and_manifest_exact(
    version: str,
) -> None:
    categories = (
        ("direct", ("event:00",)),
        ("parent_support", ()),
        ("eligibility", ()),
        ("contradiction_trigger", ()),
    )
    if version == NOMINATION_ESCROW_V2:
        categories = (*categories, ("consensus_reads", ("event:01",)))
    original = _escrow(categories, version)
    copied = copy.deepcopy(original)
    assert copied is not original
    assert copied.manifest() == original.manifest()
    assert copied.escrow_digest == original.escrow_digest
    assert all(
        getattr(copied, item.name) == getattr(original, item.name)
        for item in fields(NominationEscrow)
    )


def test_nomination_escrow_deepcopy_mechanically_preserves_bad_digest() -> None:
    original = _escrow((
        ("direct", ("event:00",)),
        ("parent_support", ()),
        ("eligibility", ()),
        ("contradiction_trigger", ()),
    ), NOMINATION_ESCROW_V1)
    object.__setattr__(original, "escrow_digest", "0" * 64)
    copied = copy.deepcopy(original)
    assert copied.escrow_digest == "0" * 64
    assert copied.manifest() == original.manifest()


@pytest.mark.parametrize("version", (NOMINATION_ESCROW_V1, NOMINATION_ESCROW_V2))
def test_nomination_escrow_valid_pickle_round_trip(version: str) -> None:
    categories = (
        ("direct", ("event:00",)),
        ("parent_support", ()),
        ("eligibility", ()),
        ("contradiction_trigger", ()),
    )
    if version == NOMINATION_ESCROW_V2:
        categories = (*categories, ("consensus_reads", ("event:01",)))
    original = _escrow(categories, version)
    restored = pickle.loads(pickle.dumps(original))
    assert restored.manifest() == original.manifest()
    assert restored.escrow_schema_version == version


def _raw_escrow_state(
    source: NominationEscrow, *, include_schema: bool = True
) -> NominationEscrow:
    raw = object.__new__(NominationEscrow)
    for item in fields(NominationEscrow):
        if item.name == "escrow_schema_version" and not include_schema:
            continue
        object.__setattr__(raw, item.name, getattr(source, item.name))
    return raw


def test_nomination_escrow_missing_schema_restores_strict_v1() -> None:
    original = _escrow((
        ("direct", ("event:00",)),
        ("parent_support", ()),
        ("eligibility", ()),
        ("contradiction_trigger", ()),
    ), NOMINATION_ESCROW_V1)
    legacy = _raw_escrow_state(original, include_schema=False)
    restored = pickle.loads(pickle.dumps(legacy))
    assert restored.escrow_schema_version == NOMINATION_ESCROW_V1
    assert restored.manifest() == original.manifest()


def test_nomination_escrow_corrupt_pickle_fails_closed() -> None:
    original = _escrow((
        ("direct", ("event:00",)),
        ("parent_support", ()),
        ("eligibility", ()),
        ("contradiction_trigger", ()),
    ), NOMINATION_ESCROW_V1)
    corrupt = _raw_escrow_state(original)
    object.__setattr__(corrupt, "escrow_digest", "0" * 64)
    payload = pickle.dumps(corrupt)
    with pytest.raises(ValueError, match="nomination escrow digest mismatch"):
        pickle.loads(payload)
