"""Focused authority lifecycle tests for bounded adaptive resource use."""

from __future__ import annotations

import copy
from dataclasses import replace

import pytest

from recon_lite_chess.autogrowth.native_competence_envelope import (
    AvailabilityState,
    PROVENANCE_COMMITMENT_V4,
)
from recon_lite_chess.autogrowth.native_prospective_evidence_authority_v2 import (
    NativeProspectiveAuthorityV2,
    ProspectiveV2IntegrityError,
    StructuralMode,
    _bounded_provenance_witnesses,
    _compact_set_commitment,
)
from recon_lite_chess.autogrowth import (
    native_prospective_evidence_authority_v2 as authority_module,
)

from tests.autogrowth.test_native_mixed_evidence_specialization import (
    ADVERSARIAL,
    _consume,
    _mixed_authority,
    _open_mint,
    _ordinary_boundary_request,
)


def _materialize_one_adaptive_child(
    authority: NativeProspectiveAuthorityV2,
) -> str:
    # One contradiction followed by four local supports is the smallest
    # existing native sequence that emits a recursive specialization request.
    sequence = (
        (False, 300, "resource:contradiction"),
        (True, 301, "resource:support-1"),
        (True, 302, "resource:support-2"),
        (True, 303, "resource:support-3"),
        (True, 304, "resource:support-4"),
    )
    emissions = [
        _consume(
            authority,
            outcome=outcome,
            fullmove=fullmove,
            frame_id=frame_id,
        )[1]
        for outcome, fullmove, frame_id in sequence
    ]
    request_id = emissions[-1].request_queue_appended_ids[0]
    boundary = authority.settle_pending_structural_requests()
    assert boundary is not None
    consumption = authority.request_consumptions[request_id]
    assert consumption.child_cell_id is not None
    return consumption.child_cell_id


def _materialize_one_compact_ordinary_child(
    authority: NativeProspectiveAuthorityV2,
) -> tuple[str, object]:
    receipt_ids = tuple(
        _consume(
            authority,
            outcome=True,
            fullmove=320 + index,
            frame_id=f"resource:compact-ordinary:{index}",
        )[0][2].receipt_id
        for index in range(4)
    )
    legacy = _ordinary_boundary_request(
        authority,
        receipt_ids,
        candidate_id="resource-compact-ordinary",
    )
    frontier = authority.next_expected_ordinal
    support_commitment = _compact_set_commitment(
        legacy.supporting_receipt_ids,
        exclusive_frontier=frontier,
    )
    inspected_commitment = _compact_set_commitment(
        legacy.inspected_receipt_ids,
        exclusive_frontier=frontier,
    )
    request = replace(
        legacy,
        supporting_receipt_ids=support_commitment.witness_ids,
        inspected_receipt_ids=inspected_commitment.witness_ids,
        promotion_gate_digest="",
        provenance_schema_version=PROVENANCE_COMMITMENT_V4,
        supporting_receipt_commitment=support_commitment,
        inspected_receipt_commitment=inspected_commitment,
    )
    assert authority.settle_pending_structural_requests((request,)) is not None
    child_id = authority._adaptive_boundary_child_id(request)
    assert child_id in authority.states
    return child_id, request


def _assert_absent_from_execution_topology(
    authority: NativeProspectiveAuthorityV2,
    cell_id: str,
) -> None:
    """Check the live execution graph across legacy and compact topology."""

    graph = authority_module._build_authority_graph(
        authority._hot_live_states()
    )
    assert all(
        f"v2:{role}:{cell_id}" not in graph.nodes
        for role in authority_module.CELL_AUTHORITY_ROLES
    )
    topology = authority.authority_topology
    if "graph_snapshot" in topology:
        assert cell_id not in topology["graph_snapshot"]["nodes"]
    else:
        assert topology["topology_schema_version"] == (
            "native_v2_authority_topology.v2_digest_only"
        )
        assert topology["graph_snapshot_digest"] == authority_module._sha(
            graph.to_snapshot()
        )
        assert topology["graph_node_count"] == len(graph.nodes)


@pytest.fixture
def event_authority() -> NativeProspectiveAuthorityV2:
    return _mixed_authority(
        AvailabilityState.AVAILABLE,
        structural_mode=StructuralMode.EVENT_DRIVEN,
    )


def test_retirement_releases_live_slot_and_preserves_unique_tombstone(
    event_authority: NativeProspectiveAuthorityV2,
) -> None:
    authority = event_authority
    child_id = _materialize_one_adaptive_child(authority)
    before_retirement = authority.continuation_digest()
    assert len(authority._successor_capacity_occupants()) == 1
    assert authority.deterministic_retirement_candidates() == (child_id,)

    retired = authority.retire_adaptive_leaves(
        (child_id,), reason="negative_causal_rent"
    )
    assert retired == (child_id,)
    assert authority.states[child_id].retired is True
    assert child_id in authority.retired_tombstones
    assert len(authority._successor_capacity_occupants()) == 0
    _assert_absent_from_execution_topology(authority, child_id)
    assert authority.continuation_digest() != before_retirement

    # A tombstone is an immutable identity record, not a recyclable ID.
    tombstone = copy.deepcopy(authority.retired_tombstones[child_id])
    with pytest.raises(ProspectiveV2IntegrityError, match="already retired"):
        authority.retire_adaptive_leaves((child_id,))
    assert authority.retired_tombstones[child_id] == tombstone
    restored = NativeProspectiveAuthorityV2.loads(authority.dumps())
    assert restored.continuation_manifest() == authority.continuation_manifest()
    restored.verify_full_history_boundary("resource retirement round trip")


def test_retired_leaf_stays_dead_in_postbirth_full_replay(
    event_authority: NativeProspectiveAuthorityV2,
) -> None:
    authority = event_authority
    child_id = _materialize_one_adaptive_child(authority)
    authority.retire_adaptive_leaves((child_id,), reason="postbirth_replay")

    # This REAL event is after the retirement ordinal and uses the same local
    # board family that would have matched the child.  Replay must keep the
    # tombstoned child out of commitment while retaining its historical state.
    _consume(
        authority,
        outcome=True,
        fullmove=310,
        frame_id="resource:postbirth-replay:after-retirement",
    )
    _assert_absent_from_execution_topology(authority, child_id)
    authority.verify_full_history_boundary("retired postbirth full replay")
    restored = NativeProspectiveAuthorityV2.loads(authority.dumps())
    restored.verify_full_history_boundary("retired postbirth dump-load replay")
    assert restored.continuation_manifest() == authority.continuation_manifest()


def test_atomic_settlement_reuses_only_freed_live_slot(
    monkeypatch: pytest.MonkeyPatch,
    event_authority: NativeProspectiveAuthorityV2,
) -> None:
    authority = event_authority
    monkeypatch.setattr(
        authority_module, "DORMANT_SPECIALIZATION_CHILD_CAPACITY", 1
    )
    receipts = tuple(
        _consume(
            authority,
            outcome=True,
            fullmove=250 + index,
            frame_id=f"resource:replacement:evidence:{index}",
        )[0][2].receipt_id
        for index in range(4)
    )
    # First fill the sole slot with a concrete positive boundary promotion.
    # Reusing the same positive REAL references for a second, distinct local
    # promotion keeps both candidates uncertified and makes this a positive-
    # only ecology test rather than a manually retired negative child.
    first_promotion = _ordinary_boundary_request(
        authority, receipts, candidate_id="resource-first"
    )
    first_boundary = authority.settle_pending_structural_requests(
        (first_promotion,),
    )
    assert first_boundary is not None
    old_child_id = next(
        cell_id for cell_id, state in authority.states.items()
        if state.hypothesis.source_generation > 0
    )
    assert len(authority._successor_capacity_occupants()) == 1

    promotion = _ordinary_boundary_request(
        authority,
        receipts,
        candidate_id="resource-replacement",
        member_index=1,
    )
    boundary = authority.settle_pending_structural_requests((promotion,))
    assert boundary is not None
    assert old_child_id in authority.retired_tombstones
    assert authority.states[old_child_id].retired is True
    assert boundary.retired_cell_ids == (old_child_id,)
    assert len(authority._successor_capacity_occupants()) == 1
    new_ids = set(authority.states) - {old_child_id}
    assert any(not authority.states[item].retired for item in new_ids)
    assert old_child_id not in authority.authority_topology["graph_snapshot"]["nodes"]
    authority.verify_full_history_boundary("resource slot replacement")
    restored = NativeProspectiveAuthorityV2.loads(authority.dumps())
    assert restored.continuation_manifest() == authority.continuation_manifest()
    assert restored.generation_boundaries[-1].retired_cell_ids == (
        old_child_id,
    )


def test_promotion_and_deferred_birth_share_recycled_slot(
    monkeypatch: pytest.MonkeyPatch,
    event_authority: NativeProspectiveAuthorityV2,
) -> None:
    """Forecast both birth kinds, then retire exactly one weak adaptive leaf."""

    authority = event_authority
    monkeypatch.setattr(
        authority_module,
        "DORMANT_SPECIALIZATION_CHILD_CAPACITY",
        2,
    )
    first_receipts = tuple(
        _consume(
            authority,
            outcome=True,
            fullmove=325 + index,
            frame_id=f"resource:shared-slot:first:{index}",
        )[0][2].receipt_id
        for index in range(4)
    )
    first = _ordinary_boundary_request(
        authority,
        first_receipts,
        candidate_id="resource:shared-slot:first",
        member_index=3,
    )
    authority.settle_pending_structural_requests((first,))
    old_child_id = next(
        cell_id for cell_id, state in authority.states.items()
        if state.hypothesis.source_generation > 0
    )

    # This sequence emits one pending core request while the existing
    # ordinary child is not a live parent.  The later promotion and deferred
    # specialization therefore require one shared recycled slot.
    _consume(
        authority,
        outcome=False,
        fullmove=329,
        frame_id="resource:shared-slot:contradiction",
        fen_template=ADVERSARIAL[AvailabilityState.AVAILABLE],
    )
    second_receipts = tuple(
        _consume(
            authority,
            outcome=True,
            fullmove=330 + index,
            frame_id=f"resource:shared-slot:second:{index}",
        )[0][2].receipt_id
        for index in range(4)
    )
    second = _ordinary_boundary_request(
        authority,
        second_receipts,
        candidate_id="resource:shared-slot:second",
        member_index=0,
    )
    pending = authority._pending_request_ids()
    assert len(pending) == 1

    boundary = authority.settle_pending_structural_requests((second,))
    assert boundary is not None
    assert boundary.retired_cell_ids == (old_child_id,)
    assert authority.states[old_child_id].retired
    assert "resource:shared-slot:second" in (
        authority.boundary_promotion_requests
    )
    deferred = authority.request_consumptions[pending[0]]
    assert deferred.disposition == "MATERIALIZED"
    assert deferred.child_cell_id is not None
    assert len(authority._successor_capacity_occupants()) == 2
    authority.verify_full_history_boundary("promotion and deferred shared slot")


def test_certified_available_anchor_is_last_resort_recyclable(
    monkeypatch: pytest.MonkeyPatch,
    event_authority: NativeProspectiveAuthorityV2,
) -> None:
    authority = event_authority
    monkeypatch.setattr(
        authority_module,
        "DORMANT_SPECIALIZATION_CHILD_CAPACITY",
        1,
    )
    first_receipts = tuple(
        _consume(
            authority,
            outcome=True,
            fullmove=370 + index,
            frame_id=f"resource:certified-anchor:first:{index}",
        )[0][2].receipt_id
        for index in range(4)
    )
    first = _ordinary_boundary_request(
        authority,
        first_receipts,
        candidate_id="resource:certified-anchor:first",
        member_index=0,
    )
    authority.settle_pending_structural_requests((first,))
    first_child_id = next(
        cell_id for cell_id, state in authority.states.items()
        if state.hypothesis.source_generation > 0
    )
    for index in range(4):
        _consume(
            authority,
            outcome=True,
            fullmove=380 + index,
            frame_id=f"resource:certified-anchor:postbirth:{index}",
        )
    assert authority.states[first_child_id].prospectively_certified
    assert authority.deterministic_retirement_candidates() == (first_child_id,)

    second_receipts = tuple(
        _consume(
            authority,
            outcome=True,
            fullmove=390 + index,
            frame_id=f"resource:certified-anchor:second:{index}",
        )[0][2].receipt_id
        for index in range(4)
    )
    second = _ordinary_boundary_request(
        authority,
        second_receipts,
        candidate_id="resource:certified-anchor:second",
        member_index=1,
    )
    boundary = authority.settle_pending_structural_requests((second,))
    assert boundary is not None
    assert boundary.retired_cell_ids == (first_child_id,)
    assert authority.states[first_child_id].retired
    assert len(authority._successor_capacity_occupants()) == 1
    authority.verify_full_history_boundary("certified available anchor recycle")


def test_capacity_replacement_rolls_back_retirement_on_admission_failure(
    monkeypatch: pytest.MonkeyPatch,
    event_authority: NativeProspectiveAuthorityV2,
) -> None:
    authority = event_authority
    monkeypatch.setattr(
        authority_module, "DORMANT_SPECIALIZATION_CHILD_CAPACITY", 1
    )
    receipts = tuple(
        _consume(
            authority,
            outcome=True,
            fullmove=275 + index,
            frame_id=f"resource:rollback:evidence:{index}",
        )[0][2].receipt_id
        for index in range(4)
    )
    first = _ordinary_boundary_request(
        authority, receipts, candidate_id="resource-rollback-first"
    )
    authority.settle_pending_structural_requests((first,))
    old_child_id = next(
        cell_id for cell_id, state in authority.states.items()
        if state.hypothesis.source_generation > 0
    )
    second = _ordinary_boundary_request(
        authority,
        receipts,
        candidate_id="resource-rollback-second",
        member_index=1,
    )
    before = authority.continuation_manifest()

    def fail_admission(*args: object, **kwargs: object) -> str:
        raise ProspectiveV2IntegrityError("synthetic admission failure")

    monkeypatch.setattr(
        NativeProspectiveAuthorityV2,
        "_materialize_boundary_promotion_in_place",
        fail_admission,
    )
    with pytest.raises(ProspectiveV2IntegrityError, match="admission failure"):
        authority.settle_pending_structural_requests((second,))
    assert authority.continuation_manifest() == before
    assert not authority.retired_tombstones
    assert not authority.states[old_child_id].retired
    assert len(authority._successor_capacity_occupants()) == 1
    authority.verify_full_history_boundary("resource replacement rollback")


def test_capacity_failure_leaves_pending_request_retryable(
    monkeypatch: pytest.MonkeyPatch,
    event_authority: NativeProspectiveAuthorityV2,
) -> None:
    authority = event_authority
    monkeypatch.setattr(
        authority_module,
        "DORMANT_SPECIALIZATION_CHILD_CAPACITY",
        1,
    )
    child_id = _materialize_one_adaptive_child(authority)
    _consume(
        authority,
        outcome=False,
        fullmove=315,
        frame_id="resource:retry:contradiction",
        fen_template=ADVERSARIAL[AvailabilityState.AVAILABLE],
    )
    for index in range(4):
        _consume(
            authority,
            outcome=True,
            fullmove=316 + index,
            frame_id=f"resource:retry:support:{index}",
        )
    pending = authority._pending_request_ids()
    assert len(pending) == 1

    # Force a capacity failure while the only live adaptive child is the
    # pending request's parent (and therefore not replaceable).
    monkeypatch.setattr(
        authority_module,
        "DORMANT_SPECIALIZATION_CHILD_CAPACITY",
        0,
    )
    before = authority.continuation_manifest()
    with pytest.raises(ProspectiveV2IntegrityError, match="successor capacity"):
        authority.settle_pending_structural_requests()
    assert authority.continuation_manifest() == before
    assert pending == authority._pending_request_ids()
    assert not authority.request_consumptions.get(pending[0])
    assert not authority.states[child_id].retired

    # A later safe point can retry the same request once capacity is made
    # available; no synthetic REJECTED_CHILD_CAPACITY record was persisted.
    monkeypatch.setattr(
        authority_module,
        "DORMANT_SPECIALIZATION_CHILD_CAPACITY",
        2,
    )
    boundary = authority.settle_pending_structural_requests()
    assert boundary is not None
    assert authority.request_consumptions[pending[0]].disposition == (
        "MATERIALIZED"
    )
    assert len(authority._successor_capacity_occupants()) == 2


def test_deferred_materialization_failure_rolls_back_whole_safe_point(
    monkeypatch: pytest.MonkeyPatch,
    event_authority: NativeProspectiveAuthorityV2,
) -> None:
    authority = event_authority
    for outcome, fullmove, frame_id in (
        (False, 360, "resource:deferred-rollback:contradiction"),
        (True, 361, "resource:deferred-rollback:support-1"),
        (True, 362, "resource:deferred-rollback:support-2"),
        (True, 363, "resource:deferred-rollback:support-3"),
        (True, 364, "resource:deferred-rollback:support-4"),
    ):
        _consume(
            authority,
            outcome=outcome,
            fullmove=fullmove,
            frame_id=frame_id,
        )
    assert authority._pending_request_ids()
    before = authority.continuation_manifest()

    def fail_materialization(*args: object, **kwargs: object) -> str:
        raise ProspectiveV2IntegrityError("synthetic deferred materialization failure")

    monkeypatch.setattr(
        NativeProspectiveAuthorityV2,
        "_materialize_deferred_child_in_place_with_options",
        fail_materialization,
    )
    with pytest.raises(
        ProspectiveV2IntegrityError,
        match="synthetic deferred materialization failure",
    ):
        authority.settle_pending_structural_requests()
    assert authority.continuation_manifest() == before
    assert not authority.retired_tombstones
    assert authority._pending_request_ids()


def test_late_structural_validation_failure_rolls_back_journal(
    monkeypatch: pytest.MonkeyPatch,
    event_authority: NativeProspectiveAuthorityV2,
) -> None:
    """A failure after births and boundaries leaves every projection intact."""

    authority = event_authority
    for outcome, fullmove, frame_id in (
        (False, 365, "resource:late-journal:contradiction"),
        (True, 366, "resource:late-journal:support-1"),
        (True, 367, "resource:late-journal:support-2"),
        (True, 368, "resource:late-journal:support-3"),
        (True, 369, "resource:late-journal:support-4"),
    ):
        _consume(
            authority,
            outcome=outcome,
            fullmove=fullmove,
            frame_id=frame_id,
        )
    assert authority._pending_request_ids()
    before_manifest = authority.continuation_manifest()
    before_live_ids = frozenset(authority._hot_live_states())
    before_occupancy = authority._successor_capacity_occupants()
    before_pending_order = tuple(authority._pending_request_order)
    before_pending_index = frozenset(authority._pending_request_index)
    before_reserved_members = frozenset(authority._reserved_member_pairs)
    before_structure_digest = authority._hot_structure_digest
    before_boundary_digest = authority._boundary_commitment_digest
    before_boundary_count = authority._boundary_commitment_count
    before_topology_schema = (
        authority._live_authority_state_cache.topology_schema_version
    )
    before_recomputed_topology = (
        authority_module._executed_authority_topology_manifest(
            authority._live_authority_state_cache
        )
    )
    assert before_recomputed_topology == authority.authority_topology

    authority_type = type(authority)
    original_validate = authority_type._validate_structural_hot_path

    def validate_then_fail(self, *args: object, **kwargs: object) -> None:
        original_validate(self, *args, **kwargs)
        raise ProspectiveV2IntegrityError(
            "synthetic late structural validation failure"
        )

    monkeypatch.setattr(
        authority_type,
        "_validate_structural_hot_path",
        validate_then_fail,
    )
    with pytest.raises(
        ProspectiveV2IntegrityError,
        match="late structural validation failure",
    ):
        authority.settle_pending_structural_requests()

    assert authority.continuation_manifest() == before_manifest
    assert frozenset(authority._hot_live_states()) == before_live_ids
    assert authority._successor_capacity_occupants() == before_occupancy
    assert tuple(authority._pending_request_order) == before_pending_order
    assert frozenset(authority._pending_request_index) == before_pending_index
    assert frozenset(authority._reserved_member_pairs) == before_reserved_members
    assert authority._hot_structure_digest == before_structure_digest
    assert authority._boundary_commitment_digest == before_boundary_digest
    assert authority._boundary_commitment_count == before_boundary_count
    assert (
        authority._live_authority_state_cache.topology_schema_version
        == before_topology_schema
    )
    assert authority_module._executed_authority_topology_manifest(
        authority._live_authority_state_cache
    ) == before_recomputed_topology

    # The exact same pending request remains cleanly retryable after the
    # journal has restored both durable state and the runtime-only sticky
    # topology representation marker.
    monkeypatch.setattr(
        authority_type,
        "_validate_structural_hot_path",
        original_validate,
    )
    assert authority.settle_pending_structural_requests() is not None
    restored = NativeProspectiveAuthorityV2.loads(authority.dumps())
    assert restored.continuation_manifest() == authority.continuation_manifest()


def test_lineage_dependency_releases_child_then_parent_slots(
    event_authority: NativeProspectiveAuthorityV2,
) -> None:
    """Live descendants protect parents until the whole lineage is released."""

    authority = event_authority
    child_id = _materialize_one_adaptive_child(authority)

    _consume(
        authority,
        outcome=False,
        fullmove=400,
        frame_id="resource:lineage:contradiction",
        fen_template=ADVERSARIAL[AvailabilityState.AVAILABLE],
    )
    for index in range(4):
        _consume(
            authority,
            outcome=True,
            fullmove=401 + index,
            frame_id=f"resource:lineage:support:{index}",
        )
    recursive_request_id = authority._pending_request_ids()[0]
    assert authority.deferred_requests[recursive_request_id].parent_cell_id == (
        child_id
    )
    # A pending request pins its parent even though the parent has no live
    # child yet.
    assert child_id not in authority.deterministic_retirement_candidates()

    authority.settle_pending_structural_requests()
    grandchild_id = authority.deferred_child_births[
        recursive_request_id
    ].child_cell_id
    assert grandchild_id in authority.states
    assert child_id not in authority.deterministic_retirement_candidates()

    # Once the live descendant is retired, the consumed request remains
    # replayable but no longer pins its parent.  Both slots can then be
    # reclaimed in dependency order; the native core is never a candidate.
    authority.retire_adaptive_leaves((grandchild_id,))
    assert authority.deterministic_retirement_candidates() == (child_id,)
    authority.retire_adaptive_leaves((child_id,))
    assert authority.states[child_id].retired
    assert authority.states[grandchild_id].retired
    authority.verify_full_history_boundary("lineage dependency release")


def test_request_consumption_tampering_is_rejected_by_full_replay(
    event_authority: NativeProspectiveAuthorityV2,
) -> None:
    """A persisted disposition or birth mismatch cannot survive validation."""

    authority = event_authority
    _materialize_one_adaptive_child(authority)
    request_id = next(iter(authority.request_consumptions))
    original = authority.request_consumptions[request_id]

    authority.request_consumptions[request_id] = replace(
        original,
        disposition="REJECTED_CHILD_CAPACITY",
    )
    with pytest.raises(
        ProspectiveV2IntegrityError,
        match="REJECTED_CHILD_CAPACITY is not a legal disposition",
    ):
        authority.verify_full_history_boundary("tampered capacity disposition")

    authority.request_consumptions[request_id] = original
    birth = authority.deferred_child_births[request_id]
    authority.deferred_child_births[request_id] = replace(
        birth,
        proposal_ordinal=birth.proposal_ordinal + 1,
    )
    with pytest.raises(
        ProspectiveV2IntegrityError,
        match="deferred child birth differs from request consumption",
    ):
        authority.verify_full_history_boundary("tampered birth members")


def test_generation_boundary_retirement_audit_is_replay_checked(
    event_authority: NativeProspectiveAuthorityV2,
) -> None:
    """Removing a recorded retirement ID is a full-history integrity error."""

    authority = event_authority
    child_id = _materialize_one_adaptive_child(authority)
    authority.retire_adaptive_leaves((child_id,), reason="boundary_audit")
    boundary = authority.generation_boundaries[-1]
    authority.generation_boundaries = (
        *authority.generation_boundaries[:-1],
        replace(boundary, retired_cell_ids=()),
    )
    with pytest.raises(
        ProspectiveV2IntegrityError,
        match="generation boundary retirement audit",
    ):
        authority.verify_full_history_boundary("tampered retirement boundary")


def test_every_generation_boundary_field_is_causally_replayed(
    event_authority: NativeProspectiveAuthorityV2,
) -> None:
    """A plausible-looking edit to any persisted boundary field is rejected."""

    authority = event_authority
    _materialize_one_adaptive_child(authority)
    original = authority.generation_boundaries[-1]
    replacements = {
        "generation": original.generation + 1,
        "phase": authority_module.GenerationPhase.STRUCTURAL_OPEN,
        "event_frontier": original.event_frontier + 1,
        "prior_continuation_digest": "1" * 64,
        "accepted_real_ledger_digest": "2" * 64,
        "request_queue_digest": "3" * 64,
        "structural_epoch_schedule_digest": "4" * 64,
        "candidate_manifest_digest": "5" * 64,
        "parent_decision_history_digest": "6" * 64,
        "specialization_genome_seed": original.specialization_genome_seed + 1,
    }
    for field_name, bad_value in replacements.items():
        authority.generation_boundaries = (
            *authority.generation_boundaries[:-1],
            replace(original, **{field_name: bad_value}),
        )
        with pytest.raises(ProspectiveV2IntegrityError):
            authority.verify_full_history_boundary(
                f"tampered boundary {field_name}"
            )
    authority.generation_boundaries = (
        *authority.generation_boundaries[:-1],
        original,
    )
    authority.verify_full_history_boundary("restored boundary fields")


def test_pending_structure_digest_tamper_is_rejected_and_clean_resume_matches(
    event_authority: NativeProspectiveAuthorityV2,
) -> None:
    authority = event_authority
    _pending, _trace, receipt = _open_mint(
        authority,
        outcome=True,
        fullmove=570,
        frame_id="resource:pending-structure-replay",
    )
    clean_payload = authority.dumps()
    restored = NativeProspectiveAuthorityV2.loads(clean_payload)
    authority.consume(receipt)
    restored.consume(receipt)
    assert restored.continuation_manifest() == authority.continuation_manifest()

    tampered = NativeProspectiveAuthorityV2.loads(clean_payload)
    assert tampered.pending_event is not None
    bad_pending = replace(
        tampered.pending_event,
        structure_invariant_digest="7" * 64,
    )
    tampered.pending_event = bad_pending
    tampered.event_transactions[bad_pending.pending_token] = (
        bad_pending.manifest()
    )
    with pytest.raises(ProspectiveV2IntegrityError, match="structure"):
        NativeProspectiveAuthorityV2.loads(
            authority_module.pickle.dumps(tampered)
        )


def test_retirement_state_before_is_reclosed_against_causal_replay(
    event_authority: NativeProspectiveAuthorityV2,
) -> None:
    authority = event_authority
    child_id = _materialize_one_adaptive_child(authority)
    authority.retire_adaptive_leaves((child_id,), reason="state_before_audit")
    tombstone = copy.deepcopy(authority.retired_tombstones[child_id])
    tombstone["state_before"]["support"] += 1
    payload = authority._retirement_tombstone_payload(
        cell_id=child_id,
        state_before=tombstone["state_before"],
        state_after=tombstone["state_after"],
        retirement_generation=tombstone["retirement_generation"],
        retirement_ordinal=tombstone["retirement_ordinal"],
        retirement_reason=tombstone["retirement_reason"],
    )
    forged_digest = authority_module._sha(payload)
    tombstone["retirement_tombstone_digest"] = forged_digest
    authority.retired_tombstones[child_id] = tombstone
    authority.states[child_id].retirement_tombstone_digest = forged_digest

    # The record is internally self-consistent; only causal replay can prove
    # that its claimed pre-retirement state never existed.
    authority._validate_retirement_tombstone(
        child_id,
        authority.states[child_id],
        tombstone,
    )
    with pytest.raises(
        ProspectiveV2IntegrityError,
        match="state_before differs from replay",
    ):
        authority.verify_full_history_boundary("forged retirement state_before")


def test_raw_classification_retains_conflict_and_lineage_local_retirement(
    event_authority: NativeProspectiveAuthorityV2,
) -> None:
    authority = event_authority
    child_id = _materialize_one_adaptive_child(authority)
    core_id = next(
        item for item, state in authority.states.items()
        if state.hypothesis.source_generation == 0
    )
    classification = authority._classification_from_emissions(
        authority.states,
        {"available": (core_id,), "refuted": (child_id,)},
    )
    # Generation zero is discovery provenance, not the execution-level
    # protected core.  The raw authority must retain the adaptive refutation;
    # the curriculum's local core router decides precedence only after this
    # evidence has been recorded.
    assert classification.state is AvailabilityState.UNKNOWN
    assert classification.available_cell_ids == (core_id,)
    assert classification.refuted_cell_ids == (child_id,)

    # Retirement of the speculative leaf cannot remove the protected core or
    # any unrelated sibling. Its own lineage is the only affected state.
    authority.retire_adaptive_leaves((child_id,))
    assert not authority.states[core_id].retired
    assert not authority.states[core_id].hypothesis.source_generation > 0
    assert authority.states[child_id].retired
    authority.verify_full_history_boundary("core precedence")


def test_invalid_batch_rolls_back_without_tombstone_or_slot_mutation(
    event_authority: NativeProspectiveAuthorityV2,
) -> None:
    authority = event_authority
    child_id = _materialize_one_adaptive_child(authority)
    before = authority.continuation_digest()
    with pytest.raises(ProspectiveV2IntegrityError, match="unknown state"):
        authority.settle_pending_structural_requests(
            retire_cell_ids=("does-not-exist", child_id),
        )
    assert authority.continuation_digest() == before
    assert not authority.retired_tombstones
    assert len(authority._successor_capacity_occupants()) == 1


def test_negative_boundary_successor_is_rejected_before_capacity_mutation(
    event_authority: NativeProspectiveAuthorityV2,
) -> None:
    authority = event_authority
    receipts = tuple(
        _consume(
            authority,
            outcome=True,
            fullmove=350 + index,
            frame_id=f"resource:negative-boundary:{index}",
        )[0][2].receipt_id
        for index in range(4)
    )
    positive = _ordinary_boundary_request(
        authority, receipts, candidate_id="resource-negative-boundary"
    )
    negative = replace(
        positive,
        fixed_polarity=AvailabilityState.REFUTED,
        promotion_gate_digest="",
    )
    before = authority.continuation_digest()
    with pytest.raises(ProspectiveV2IntegrityError, match="negative boundary"):
        authority.settle_pending_structural_requests((negative,))
    assert authority.continuation_digest() == before
    assert not authority.retired_tombstones


def test_compact_promotion_cannot_hide_a_later_matching_contradiction(
    event_authority: NativeProspectiveAuthorityV2,
) -> None:
    authority = event_authority
    receipt_ids = tuple(
        _consume(
            authority,
            outcome=True,
            fullmove=710 + index,
            frame_id=f"resource:stale-promotion:support-{index}",
        )[0][2].receipt_id
        for index in range(4)
    )
    legacy = _ordinary_boundary_request(
        authority,
        receipt_ids,
        candidate_id="resource:stale-promotion",
    )
    frontier = authority.next_expected_ordinal
    support_commitment = _compact_set_commitment(
        legacy.supporting_receipt_ids,
        exclusive_frontier=frontier,
    )
    inspected_commitment = _compact_set_commitment(
        legacy.inspected_receipt_ids,
        exclusive_frontier=frontier,
    )
    compact = replace(
        legacy,
        supporting_receipt_ids=support_commitment.witness_ids,
        inspected_receipt_ids=inspected_commitment.witness_ids,
        promotion_gate_digest="",
        provenance_schema_version=PROVENANCE_COMMITMENT_V4,
        supporting_receipt_commitment=support_commitment,
        inspected_receipt_commitment=inspected_commitment,
    )

    unrelated_trigger = next(
        reference.receipt_id
        for reference in authority.accepted_real_references.values()
        if not reference.observed_outcome
    )
    forged_trigger = replace(
        compact,
        triggering_receipt_id=unrelated_trigger,
        promotion_gate_digest="",
    )
    before_forged = authority.continuation_digest()
    with pytest.raises(
        ProspectiveV2IntegrityError,
        match="positive matching evidence",
    ):
        authority.settle_pending_structural_requests((forged_trigger,))
    assert authority.continuation_digest() == before_forged

    opened, _emission = _consume(
        authority,
        outcome=False,
        fullmove=720,
        frame_id="resource:stale-promotion:matching-contradiction",
    )
    later = authority.accepted_real_references[opened[2].receipt_id]
    assert set(compact.members).issubset(later.ordered_signal_identities)
    assert later.observed_outcome is False
    before = authority.continuation_digest()
    with pytest.raises(
        ProspectiveV2IntegrityError,
        match="current accepted-REAL frontier",
    ):
        authority.settle_pending_structural_requests((compact,))
    assert authority.continuation_digest() == before


def test_v4_deferred_birth_reuses_candidate_commitment_without_history_scan(
    event_authority: NativeProspectiveAuthorityV2,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    authority = event_authority
    sequence = (
        (False, 730, "contradiction"),
        (True, 731, "support-1"),
        (True, 732, "support-2"),
        (True, 733, "support-3"),
        (True, 734, "support-4"),
    )
    emissions = tuple(
        _consume(
            authority,
            outcome=outcome,
            fullmove=fullmove,
            frame_id=f"resource:no-direct-scan:{label}",
        )[1]
        for outcome, fullmove, label in sequence
    )
    request_id = emissions[-1].request_queue_appended_ids[0]
    request = authority.deferred_requests[request_id]
    assert request.provenance_schema_version == PROVENANCE_COMMITMENT_V4

    def forbidden_scan(*_args, **_kwargs):
        raise AssertionError("V4 birth scanned the lifetime REAL ledger")

    monkeypatch.setattr(
        NativeProspectiveAuthorityV2,
        "_matching_parent_plus_identity_receipts",
        forbidden_scan,
    )
    boundary = authority.settle_pending_structural_requests()
    assert boundary is not None
    child_id = authority.request_consumptions[request_id].child_cell_id
    assert child_id is not None
    escrow = authority.deferred_child_escrows[child_id]
    assert len(escrow.categorized_reads) == 7
    assert all(
        len(receipt_ids) <= 4
        for _name, receipt_ids in escrow.categorized_reads
    )
    with pytest.raises(ValueError, match="incomplete nomination"):
        replace(
            escrow,
            categorized_reads=(*escrow.categorized_reads, ("extra", ())),
            escrow_digest="",
        )


def test_v4_ordinary_birth_rederives_reads_after_coherent_rehash(
    event_authority: NativeProspectiveAuthorityV2,
) -> None:
    authority = event_authority
    child_id, request = _materialize_one_compact_ordinary_child(authority)
    escrow = authority.adaptive_boundary_escrows[child_id]
    hypothesis = authority.states[child_id].hypothesis
    direct = dict(escrow.nomination_read_commitments)["direct"]
    forged_direct = replace(direct, query_digest="0" * 64)
    forged_reads = tuple(
        (name, forged_direct if name == "direct" else commitment)
        for name, commitment in escrow.nomination_read_commitments
    )
    forged_escrow = replace(
        escrow,
        nomination_read_commitments=forged_reads,
        escrow_digest="",
    )
    forged_discovery = authority_module._compose_provenance_commitment(
        tuple(commitment for _name, commitment in forged_reads),
        exclusive_frontier=forged_escrow.birth_frontier + 1,
        query_digest=authority_module._compact_query_digest({
            "operation": "ordinary",
            "candidate_id": request.candidate_id,
        }),
    )
    forged_hypothesis = replace(
        hypothesis,
        nomination_escrow_digest=forged_escrow.escrow_digest,
        nomination_read_commitments=forged_reads,
        discovery_read_commitment=forged_discovery,
        discovery_receipt_digest=forged_discovery.digest,
        discovery_receipt_ids=forged_discovery.witness_ids,
        hypothesis_digest="",
    )

    # Every outer digest and witness projection is self-consistent.  The
    # request remains the immutable causal authority and exposes the rekey.
    with pytest.raises(
        ProspectiveV2IntegrityError,
        match="ordinary birth diverges from promotion request",
    ):
        authority._validate_compact_ordinary_birth_contract(
            request,
            forged_escrow,
            forged_hypothesis,
        )


def test_v4_deferred_birth_rederives_reads_after_coherent_rehash(
    event_authority: NativeProspectiveAuthorityV2,
) -> None:
    authority = event_authority
    child_id = _materialize_one_adaptive_child(authority)
    birth = next(
        item for item in authority.deferred_child_births.values()
        if item.child_cell_id == child_id
    )
    request = authority.deferred_requests[birth.request_id]
    escrow = authority.deferred_child_escrows[child_id]
    hypothesis = authority.states[child_id].hypothesis
    direct = dict(escrow.nomination_read_commitments)[
        "direct_child_matches"
    ]
    forged_direct = replace(direct, query_digest="0" * 64)
    forged_reads = tuple(
        (
            name,
            forged_direct
            if name == "direct_child_matches" else commitment,
        )
        for name, commitment in escrow.nomination_read_commitments
    )
    forged_escrow = replace(
        escrow,
        nomination_read_commitments=forged_reads,
        escrow_digest="",
    )
    forged_discovery = authority_module._compose_provenance_commitment(
        tuple(commitment for _name, commitment in forged_reads),
        exclusive_frontier=forged_escrow.birth_frontier + 1,
        query_digest=authority_module._compact_query_digest({
            "operation": "specialization",
            "parent_hypothesis_digest": request.parent_hypothesis_digest,
        }),
    )
    forged_hypothesis = replace(
        hypothesis,
        nomination_escrow_digest=forged_escrow.escrow_digest,
        nomination_read_commitments=forged_reads,
        discovery_read_commitment=forged_discovery,
        discovery_receipt_digest=forged_discovery.digest,
        discovery_receipt_ids=forged_discovery.witness_ids,
        hypothesis_digest="",
    )

    with pytest.raises(
        ProspectiveV2IntegrityError,
        match="deferred birth diverges from specialization request",
    ):
        authority._validate_compact_deferred_birth_contract(
            request,
            birth,
            forged_escrow,
            forged_hypothesis,
        )


def _forge_future_compact_birth(
    authority: NativeProspectiveAuthorityV2,
    child_id: str,
    escrow_ledger: dict,
) -> None:
    state = authority.states[child_id]
    hypothesis = state.hypothesis
    escrow = escrow_ledger[child_id]
    future_birth_frontier = hypothesis.birth_frontier + 1
    assert future_birth_frontier < authority.next_expected_ordinal
    exclusion = authority._accepted_real_prefix_commitment_at(
        future_birth_frontier + 1
    )
    forged_escrow = replace(
        escrow,
        birth_frontier=future_birth_frontier,
        certification_frontier=future_birth_frontier,
        discovery_exclusion_receipt_ids=exclusion.witness_ids,
        discovery_exclusion_commitment=exclusion,
        escrow_digest="",
    )
    forged_hypothesis = replace(
        hypothesis,
        birth_frontier=future_birth_frontier,
        certification_frontier=future_birth_frontier,
        nomination_escrow_digest=forged_escrow.escrow_digest,
        discovery_exclusion_receipt_ids=exclusion.witness_ids,
        discovery_exclusion_commitment=exclusion,
        hypothesis_digest="",
    )
    authority.states[child_id] = replace(
        state,
        hypothesis=forged_hypothesis,
    )
    escrow_ledger[child_id] = forged_escrow


def test_v4_ordinary_future_birth_is_rejected_at_exact_replay_safe_point(
    event_authority: NativeProspectiveAuthorityV2,
) -> None:
    authority = event_authority
    child_id, _request = _materialize_one_compact_ordinary_child(authority)
    _consume(
        authority,
        outcome=True,
        fullmove=329,
        frame_id="resource:ordinary-future-birth:postbirth",
    )
    _forge_future_compact_birth(
        authority,
        child_id,
        authority.adaptive_boundary_escrows,
    )
    with pytest.raises(
        ProspectiveV2IntegrityError,
        match="compact ordinary birth frontier differs.*safe point",
    ):
        authority._verify_generation_boundary_replay()


def test_v4_deferred_future_birth_is_rejected_at_exact_replay_safe_point(
    event_authority: NativeProspectiveAuthorityV2,
) -> None:
    authority = event_authority
    child_id = _materialize_one_adaptive_child(authority)
    _consume(
        authority,
        outcome=True,
        fullmove=329,
        frame_id="resource:deferred-future-birth:postbirth",
    )
    _forge_future_compact_birth(
        authority,
        child_id,
        authority.deferred_child_escrows,
    )
    with pytest.raises(
        ProspectiveV2IntegrityError,
        match="compact deferred birth frontier differs.*safe point",
    ):
        authority._verify_generation_boundary_replay()


def test_compact_request_deserialization_enforces_candidate_beam(
    event_authority: NativeProspectiveAuthorityV2,
) -> None:
    authority = event_authority
    sequence = (
        (False, 740, "contradiction"),
        (True, 741, "support-1"),
        (True, 742, "support-2"),
        (True, 743, "support-3"),
        (True, 744, "support-4"),
    )
    emissions = tuple(
        _consume(
            authority,
            outcome=outcome,
            fullmove=fullmove,
            frame_id=f"resource:beam-cap:{label}",
        )[1]
        for outcome, fullmove, label in sequence
    )
    request = authority.deferred_requests[
        emissions[-1].request_queue_appended_ids[0]
    ]
    assert request.candidate_terminals
    oversized = (
        request.candidate_terminals
        * (65 // len(request.candidate_terminals) + 1)
    )[:65]
    with pytest.raises(
        ProspectiveV2IntegrityError,
        match="candidate beam",
    ):
        replace(request, candidate_terminals=oversized)


def test_legacy_topology_recloses_old_full_meta_but_runtime_is_digest_only(
    event_authority: NativeProspectiveAuthorityV2,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    authority = event_authority
    assert "topology_schema_version" not in authority.authority_topology
    legacy = authority_module._executed_authority_topology_manifest(
        authority._hot_live_states()
    )
    assert legacy == authority.authority_topology
    legacy_leaves = tuple(
        node["meta"]
        for node in legacy["graph_snapshot"]["nodes"].values()
        if node["meta"].get("cell_id")
    )
    assert legacy_leaves
    assert all("frozen_hypothesis" in meta for meta in legacy_leaves)
    restored = NativeProspectiveAuthorityV2.loads(authority.dumps())
    assert restored.authority_topology == legacy

    def forbidden_manifest(_self):
        raise AssertionError("runtime copied a full frozen hypothesis")

    monkeypatch.setattr(
        authority_module.FrozenHypothesis,
        "manifest",
        forbidden_manifest,
    )
    runtime = authority_module._build_authority_graph(
        authority._hot_live_states()
    )
    runtime_leaves = tuple(
        node.meta for node in runtime.nodes.values()
        if node.meta.get("cell_id")
    )
    assert all("hypothesis_digest" in meta for meta in runtime_leaves)
    assert all("frozen_hypothesis" not in meta for meta in runtime_leaves)


def test_full_ledger_replay_uses_the_bounded_chronological_live_view(
    event_authority: NativeProspectiveAuthorityV2,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    authority = event_authority
    child_id = _materialize_one_adaptive_child(authority)
    authority.retire_adaptive_leaves(
        (child_id,), reason="replay_live_view_probe"
    )
    _consume(
        authority,
        outcome=True,
        fullmove=760,
        frame_id="resource:post-retirement-live-view",
    )
    original = (
        NativeProspectiveAuthorityV2
        ._incremental_predecessor_digest_from_parts
    )
    observed_sizes: list[int] = []

    def probe(self, **kwargs):
        states = kwargs["states"]
        assert isinstance(states, authority_module._LiveAuthorityStateView)
        assert child_id not in states or not states[child_id].retired
        observed_sizes.append(len(states))
        return original(self, **kwargs)

    monkeypatch.setattr(
        NativeProspectiveAuthorityV2,
        "_incremental_predecessor_digest_from_parts",
        probe,
    )
    authority._verify_ledger_derived_state()
    assert observed_sizes
    assert max(observed_sizes) <= len(
        authority._successor_capacity_occupants()
    ) + sum(
        state.hypothesis.source_generation == 0
        for state in authority.states.values()
    ) + 1


def test_many_compact_prefixes_reclose_in_one_accepted_real_pass(
    event_authority: NativeProspectiveAuthorityV2,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    authority = event_authority
    for index in range(6):
        _consume(
            authority,
            outcome=bool(index % 2),
            fullmove=770 + index,
            frame_id=f"resource:prefix-pass:{index}",
        )
    frontiers = tuple(range(
        min(authority._accepted_real_reference_ordinals) + 1,
        authority.next_expected_ordinal + 1,
    ))
    original = authority_module._next_hot_append_digest
    append_count = 0

    def count_append(previous, kind, value, count):
        nonlocal append_count
        append_count += 1
        return original(previous, kind, value, count)

    monkeypatch.setattr(
        authority_module,
        "_next_hot_append_digest",
        count_append,
    )
    commitments = authority._accepted_real_prefix_commitments(frontiers)
    expected_rows = sum(
        reference.ordinal < max(frontiers)
        for reference in authority.accepted_real_references.values()
    )
    assert append_count == expected_rows
    assert set(commitments) == set(frontiers)
    assert all(
        len(commitment.witness_ids) <= 4
        for commitment in commitments.values()
    )
    with pytest.raises(
        ProspectiveV2IntegrityError,
        match="exceeds the accepted REAL ledger",
    ):
        authority._accepted_real_prefix_commitments((
            authority.next_expected_ordinal + 1,
        ))
