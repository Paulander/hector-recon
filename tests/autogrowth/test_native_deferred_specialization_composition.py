from __future__ import annotations

import pickle
import inspect

import pytest

from recon_lite import Node, NodeState, NodeType
from recon_lite_hector.nodes import StemCellState

from recon_lite_chess.autogrowth.native_competence_envelope import (
    AvailabilityState,
    DormantOrigin,
    SpecializationMode,
    StructuralMatchDescriptor,
    canonical_structural_pattern_matches,
)
from recon_lite_chess.autogrowth.native_prospective_evidence_authority_v2 import (
    DeferredSpecializationRequest,
    GenerationPhase,
    MIN_SUPPORT,
    NativeProspectiveAuthorityV2,
    ProspectiveV2IntegrityError,
    RequestBasis,
    SpecializationCandidateTerminalState,
    _v2_specialization_eligibility_terminal,
)


def _descriptor(
    cell_id: str,
    members: tuple[str, ...],
    state: StemCellState,
    *,
    parent: str | None = None,
    depth: int = 0,
    operation: str = "historical",
    parent_digest: str | None = None,
    digest: str | None = None,
) -> StructuralMatchDescriptor:
    return StructuralMatchDescriptor(
        cell_id=cell_id,
        members=members,
        structural_state=state.name,
        lineage_parent_id=parent,
        specialization_depth=depth,
        nomination_operation=operation,
        parent_hypothesis_digest=parent_digest,
        hypothesis_digest=digest,
    )


@pytest.mark.parametrize(
    ("parent_state", "expected"),
    [
        (StemCellState.MATURE, True),
        (StemCellState.PROBATION, True),
        (StemCellState.DORMANT, True),
        (StemCellState.PRUNED, False),
    ],
)
def test_canonical_matcher_lineage_only_states(parent_state, expected):
    parent = _descriptor(
        "parent", ("opaque:a",), parent_state, digest="parent-digest"
    )
    child = _descriptor(
        "child",
        ("context:parent", "opaque:b"),
        StemCellState.DORMANT,
        parent="parent",
        depth=1,
        operation="specialization",
        parent_digest="parent-digest",
        digest="child-digest",
    )
    assert canonical_structural_pattern_matches(
        "child", {"parent": parent, "child": child}, ("opaque:a", "opaque:b")
    ) is expected


def test_canonical_matcher_rejects_unrelated_or_unbound_dormant_parent():
    parent = _descriptor(
        "parent", ("opaque:a",), StemCellState.DORMANT,
        digest="parent-digest",
    )
    unrelated = _descriptor(
        "child", ("context:parent", "opaque:b"), StemCellState.DORMANT,
        parent="other", depth=1, operation="specialization",
        parent_digest="parent-digest", digest="child-digest",
    )
    wrong_digest = _descriptor(
        "child", ("context:parent", "opaque:b"), StemCellState.DORMANT,
        parent="parent", depth=1, operation="specialization",
        parent_digest="wrong", digest="child-digest",
    )
    for child in (unrelated, wrong_digest):
        assert not canonical_structural_pattern_matches(
            "child", {"parent": parent, "child": child},
            ("opaque:a", "opaque:b"),
        )


def _request(index: int) -> DeferredSpecializationRequest:
    receipt = f"receipt-{index:03d}"
    supporting_receipts = tuple(
        f"{receipt}-support-{item}" for item in range(MIN_SUPPORT)
    )
    supporting_interactions = tuple(
        f"physical-{index:03d}-{item}" for item in range(MIN_SUPPORT)
    )
    terminal = SpecializationCandidateTerminalState(
        identity=f"opaque:{index}",
        node_id=f"node:{index}",
        role_permitted=True,
        recursively_implied_by_parent=False,
        supporting_receipt_ids=supporting_receipts,
        supporting_stable_physical_interaction_ids=(
            supporting_interactions
        ),
        supporting_occurrence_count=MIN_SUPPORT,
        present_in_triggering_contradiction=index % 2 != 0,
        specialization_mode=SpecializationMode.LOCAL_CONTRAST,
        confirmed=index % 2 == 0,
        node_state="CONFIRMED" if index % 2 == 0 else "FAILED",
        inspected_receipt_ids=tuple(sorted({receipt, *supporting_receipts})),
    )
    return DeferredSpecializationRequest(
        request_id=f"request-{index:03d}",
        source_generation=0,
        parent_cell_id=f"parent-{index:03d}",
        parent_hypothesis_digest=f"digest-{index:03d}",
        fixed_polarity=AvailabilityState.AVAILABLE,
        request_basis=RequestBasis.CERTIFIED_REVOCATION,
        request_emission_receipt_id=receipt,
        request_emission_ordinal=index,
        contradiction_receipt_id=receipt,
        contradiction_ordinal=index,
        specialization_mode=SpecializationMode.LOCAL_CONTRAST,
        parent_discovery_receipt_ids=(receipt,),
        parent_discovery_support_receipt_ids=(receipt,),
        parent_prospective_support_receipt_ids=(),
        transitive_ancestor_receipt_ids=(),
        candidate_terminals=(terminal,),
        graph_revocation_confirmed=True,
        graph_request_confirmed=True,
    )


@pytest.mark.parametrize(
    "field",
    ("graph_revocation_confirmed", "graph_request_confirmed"),
)
def test_request_graph_truth_claims_are_explicit_booleans(field: str):
    values = dict(_request(0).__dict__)
    values[field] = 1
    with pytest.raises(
        ProspectiveV2IntegrityError, match="not Boolean"
    ):
        DeferredSpecializationRequest(**values)


def test_request_capacity_accepts_192_and_rejects_193_atomically():
    authority = object.__new__(NativeProspectiveAuthorityV2)
    authority.request_queue = tuple(
        f"request-{index:03d}" for index in range(191)
    )
    authority._validate_request_append_capacity((_request(191),))
    authority.request_queue = tuple(
        f"request-{index:03d}" for index in range(192)
    )
    before = authority.request_queue
    with pytest.raises(
        ProspectiveV2IntegrityError, match="request queue capacity"
    ):
        authority._validate_request_append_capacity((_request(192),))
    assert authority.request_queue == before


def test_candidate_confirmed_and_rejected_states_pickle_exact():
    request = _request(7)
    restored = pickle.loads(pickle.dumps(request))
    assert restored == request
    assert restored.candidate_terminals[0].confirmed is False
    assert restored.candidate_terminals[0].node_state == "FAILED"


def _eligibility_node(
    *,
    mode: SpecializationMode,
    implied: bool = False,
    count: int = MIN_SUPPORT,
    in_contradiction: bool = False,
) -> Node:
    return Node(
        "eligibility",
        NodeType.TERMINAL,
        predicate=_v2_specialization_eligibility_terminal,
        meta={
            "role_permitted": True,
            "recursively_implied_by_parent": implied,
            "supporting_occurrence_count": count,
            "present_in_triggering_contradiction": in_contradiction,
            "specialization_mode": mode.value,
        },
    )


@pytest.mark.parametrize(
    ("mode", "implied", "count", "in_contradiction", "expected"),
    [
        (SpecializationMode.COUNTEREXAMPLE_BLIND, True, MIN_SUPPORT, False, False),
        (SpecializationMode.COUNTEREXAMPLE_BLIND, False, MIN_SUPPORT - 1, False, False),
        (SpecializationMode.COUNTEREXAMPLE_BLIND, False, MIN_SUPPORT, True, True),
        (SpecializationMode.LOCAL_CONTRAST, False, MIN_SUPPORT, True, False),
        (SpecializationMode.LOCAL_CONTRAST, False, MIN_SUPPORT, False, True),
    ],
)
def test_complete_graph_eligibility_rule(
    mode, implied, count, in_contradiction, expected
):
    node = _eligibility_node(
        mode=mode,
        implied=implied,
        count=count,
        in_contradiction=in_contradiction,
    )
    processed, confirmed = _v2_specialization_eligibility_terminal(node, {})
    assert processed is True
    assert confirmed is expected


def test_local_and_blind_candidate_population_differs_only_at_predicate():
    local = _request(7).candidate_terminals[0]
    blind = SpecializationCandidateTerminalState(
        **{
            **local.__dict__,
            "specialization_mode": SpecializationMode.COUNTEREXAMPLE_BLIND,
            "confirmed": True,
            "node_state": NodeState.CONFIRMED.name,
        }
    )
    ignored = {
        "specialization_mode",
        "present_in_triggering_contradiction",
        "confirmed",
        "node_state",
    }
    assert {
        key: value for key, value in local.manifest().items()
        if key not in ignored
    } == {
        key: value for key, value in blind.manifest().items()
        if key not in ignored
    }
    assert pickle.loads(pickle.dumps((local, blind))) == (local, blind)


def _synthetic_structural_authority(
    requests: tuple[DeferredSpecializationRequest, ...],
) -> NativeProspectiveAuthorityV2:
    authority = object.__new__(NativeProspectiveAuthorityV2)
    authority.generation_phase = GenerationPhase.STRUCTURAL_OPEN
    authority.sealed_request_ids = tuple(item.request_id for item in requests)
    authority.deferred_requests = {
        item.request_id: item for item in requests
    }
    authority.request_consumptions = {}
    authority.deferred_child_births = {}
    authority.states = {}
    authority.current_generation = 1
    authority.specialization_genome_seed = 117
    return authority


def test_structural_consumption_is_organism_owned_and_canonical(monkeypatch):
    monkeypatch.setattr(
        NativeProspectiveAuthorityV2,
        "_verify_invariants",
        lambda _self: None,
    )
    first = _request(0)
    second = DeferredSpecializationRequest(
        **{
            **_request(2).__dict__,
            "request_id": "request-001",
            "parent_cell_id": first.parent_cell_id,
            "parent_hypothesis_digest": first.parent_hypothesis_digest,
            "candidate_terminals": first.candidate_terminals,
        }
    )
    authority = _synthetic_structural_authority((first, second))
    assert not hasattr(authority, "consume_structural_request")
    assert tuple(inspect.signature(
        authority.consume_next_structural_request
    ).parameters) == ()

    first_result = authority.consume_next_structural_request()
    assert first_result.request_id == first.request_id
    assert first_result.attempt_ordinal == 0
    assert first_result.genome_seed == authority.specialization_genome_seed
    assert first_result.genome_call_count == 1

    restored = pickle.loads(pickle.dumps(authority))
    assert restored.request_consumptions == authority.request_consumptions
    second_result = authority.consume_next_structural_request()
    assert second_result.request_id == second.request_id
    assert second_result.attempt_ordinal == 1
    assert second_result.disposition == "REJECTED_DUPLICATE_PATTERN"
    assert second_result.selected_members == first_result.selected_members
    with pytest.raises(
        ProspectiveV2IntegrityError, match="fully consumed"
    ):
        authority.consume_next_structural_request()
    assert len(authority.request_consumptions) == 2


def test_all_192_sealed_requests_consume_one_permanent_slot(monkeypatch):
    monkeypatch.setattr(
        NativeProspectiveAuthorityV2,
        "_verify_invariants",
        lambda _self: None,
    )
    template = _request(0)
    requests = tuple(
        DeferredSpecializationRequest(
            **{
                **template.__dict__,
                "request_id": f"request-{index:03d}",
                "request_emission_receipt_id": f"receipt-{index:03d}",
                "request_emission_ordinal": index,
                "contradiction_receipt_id": f"receipt-{index:03d}",
                "contradiction_ordinal": index,
            }
        )
        for index in range(192)
    )
    authority = _synthetic_structural_authority(requests)
    results = tuple(
        authority.consume_next_structural_request() for _ in requests
    )
    assert tuple(item.request_id for item in results) == tuple(
        item.request_id for item in requests
    )
    assert tuple(item.attempt_ordinal for item in results) == tuple(range(192))
    assert all(item.genome_call_count == 1 for item in results)
    assert len(authority.request_consumptions) == 192
    assert results[-1].disposition == "REJECTED_DUPLICATE_PATTERN"
    with pytest.raises(ProspectiveV2IntegrityError, match="fully consumed"):
        authority.consume_next_structural_request()


def test_dormant_origins_are_distinct_serialized_values():
    assert DormantOrigin.MIXED_OUTCOME_SHADOW.value != (
        DormantOrigin.DEFERRED_SPECIALIZATION_CHILD.value
    )
    assert pickle.loads(pickle.dumps(
        DormantOrigin.MIXED_OUTCOME_SHADOW
    )) is DormantOrigin.MIXED_OUTCOME_SHADOW
    assert pickle.loads(pickle.dumps(
        DormantOrigin.DEFERRED_SPECIALIZATION_CHILD
    )) is DormantOrigin.DEFERRED_SPECIALIZATION_CHILD
