from __future__ import annotations

import pickle

import pytest

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
    NativeProspectiveAuthorityV2,
    ProspectiveV2IntegrityError,
    SpecializationCandidateTerminalState,
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
    terminal = SpecializationCandidateTerminalState(
        identity=f"opaque:{index}",
        node_id=f"node:{index}",
        confirmed=index % 2 == 0,
        node_state="CONFIRMED" if index % 2 == 0 else "FAILED",
        inspected_receipt_ids=(receipt,),
    )
    return DeferredSpecializationRequest(
        request_id=f"request-{index:03d}",
        source_generation=0,
        parent_cell_id=f"parent-{index:03d}",
        parent_hypothesis_digest=f"digest-{index:03d}",
        fixed_polarity=AvailabilityState.AVAILABLE,
        contradiction_receipt_id=receipt,
        contradiction_ordinal=index,
        specialization_mode=SpecializationMode.LOCAL_CONTRAST,
        parent_discovery_receipt_ids=(receipt,),
        parent_discovery_support_receipt_ids=(receipt,),
        parent_prospective_support_receipt_ids=(),
        transitive_ancestor_receipt_ids=(),
        candidate_terminals=(terminal,),
    )


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
