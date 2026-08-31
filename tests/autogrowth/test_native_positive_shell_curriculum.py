from __future__ import annotations

from types import SimpleNamespace

import pytest

from recon_lite_chess.autogrowth.native_all_reply_envelope import (
    AvailabilityState,
)
from recon_lite_chess.autogrowth.native_intrinsic_curriculum import (
    _adaptive_positive_lineage_audit,
    _boundary_promotion_request_from_candidate,
    _boundary_ecology_step,
)
from recon_lite_chess.autogrowth.native_prospective_evidence_authority_v2 import (
    NativeProspectiveAuthorityV2,
    StructuralMode,
    _compact_set_commitment,
)
from recon_lite_chess.autogrowth.native_prospective_boundary_candidate_ecology import (
    ProspectiveBoundaryCandidateEcology,
    SketchLifecycle,
)

from tests.autogrowth.test_native_mixed_evidence_specialization import (
    _consume,
    _mixed_authority,
)


class _BoundaryAuthority:
    def __init__(self) -> None:
        self.accepted_real_references: dict[str, SimpleNamespace] = {}
        self.states: dict[str, object] = {}
        self.current_generation = 0

    def add(
        self,
        ordinal: int,
        *,
        signals: tuple[str, ...],
        observed: bool,
    ) -> str:
        receipt_id = f"receipt-{ordinal}"
        ordered = tuple(sorted(signals))
        self.accepted_real_references[receipt_id] = SimpleNamespace(
            ordinal=ordinal,
            receipt_id=receipt_id,
            stable_physical_interaction_id=f"physical-{ordinal}",
            ordered_signal_identities=ordered,
            typed_signal_roles=tuple(
                (signal_id, "BASE_TERMINAL") for signal_id in ordered
            ),
            observed_outcome=observed,
        )
        return receipt_id


class _NoLifetimeStateValues(dict):
    def values(self):
        raise AssertionError("promotion de-dup scanned lifetime states")


class _GuardedBoundaryAuthority(_BoundaryAuthority):
    def __init__(self) -> None:
        super().__init__()
        self.states = _NoLifetimeStateValues()
        self.live_state_reads = 0

    def _hot_live_states(self):
        self.live_state_reads += 1
        return {}


def test_failure_is_contrast_only_and_cannot_birth_a_negative_candidate() -> None:
    authority = _BoundaryAuthority()
    ecology = ProspectiveBoundaryCandidateEcology()
    receipt_id = authority.add(0, signals=("coarse",), observed=False)

    promotions, event = _boundary_ecology_step(
        authority,
        ecology,
        receipt_id=receipt_id,
        pre_outcome_state=AvailabilityState.UNKNOWN,
    )

    assert promotions == ()
    assert event["contrast_observation"] is True
    assert event["surprise_success"] is False
    assert event["born_candidate_ids"] == []
    assert ecology.lifetime_birth_count == 0


def test_first_contradiction_abstains_and_buds_a_positive_residual() -> None:
    authority = _BoundaryAuthority()
    ecology = ProspectiveBoundaryCandidateEcology()
    positive_id = authority.add(
        0,
        signals=("coarse", "local-residual"),
        observed=True,
    )
    _promotions, birth_event = _boundary_ecology_step(
        authority,
        ecology,
        receipt_id=positive_id,
        pre_outcome_state=AvailabilityState.UNKNOWN,
    )
    parent = min(
        (
            ecology.sketches[candidate_id]
            for candidate_id in birth_event["born_candidate_ids"]
            if ecology.sketches[candidate_id].arity == 1
        ),
        key=lambda item: item.sketch_id,
    )
    remaining_signal = next(
        signal_id
        for signal_id in ("coarse", "local-residual")
        if signal_id not in parent.members
    )
    negative_id = authority.add(
        1,
        signals=parent.members,
        observed=False,
    )

    promotions, contrast_event = _boundary_ecology_step(
        authority,
        ecology,
        receipt_id=negative_id,
        pre_outcome_state=AvailabilityState.UNKNOWN,
    )

    assert promotions == ()
    assert contrast_event["born_candidate_ids"] == []
    assert contrast_event["refinement_candidate_ids"]
    refined_parent = ecology.sketches[parent.sketch_id]
    assert refined_parent.state is SketchLifecycle.REFINING
    assert negative_id in refined_parent.abstained_receipt_ids
    children = tuple(
        ecology.sketches[candidate_id]
        for candidate_id in contrast_event["refinement_candidate_ids"]
    )
    assert all(child.polarity is True for child in children)
    assert all(
        child.parent_sketch_id == parent.sketch_id
        or child.sketch_id in refined_parent.residual_sketch_ids
        for child in children
    )
    assert any(remaining_signal in child.members for child in children)

    settled = ecology.settle_refinements()
    assert parent.sketch_id in {item.sketch_id for item in settled}
    assert ecology.sketches[parent.sketch_id].state is SketchLifecycle.DORMANT


def test_only_a_supported_positive_shell_can_request_authority_promotion() -> None:
    authority = _BoundaryAuthority()
    ecology = ProspectiveBoundaryCandidateEcology()
    promotions = ()
    for ordinal in range(4):
        receipt_id = authority.add(
            ordinal,
            signals=("reusable-local-pattern",),
            observed=True,
        )
        promotions, event = _boundary_ecology_step(
            authority,
            ecology,
            receipt_id=receipt_id,
            pre_outcome_state=AvailabilityState.UNKNOWN,
        )

    assert len(promotions) == 1
    request = promotions[0]
    assert request.fixed_polarity is AvailabilityState.AVAILABLE
    assert request.triggering_receipt_id in request.inspected_receipt_ids
    assert set(request.supporting_receipt_ids) <= set(
        request.inspected_receipt_ids
    )
    assert event["promotion_candidate_id"] == request.candidate_id


def test_positive_promotion_commitment_covers_late_lexical_trigger() -> None:
    """V4 may bound witnesses while retaining the trigger in its commitment."""

    class _LateTriggerAuthority(_BoundaryAuthority):
        def add(
            self,
            ordinal: int,
            *,
            signals: tuple[str, ...],
            observed: bool,
        ) -> str:
            # The bounded witness list is lexically selected.  Put the
            # positive birth trigger after four later supports so this test
            # exercises the exact V14 post-epoch-4 failure mode.
            receipt_id = (
                "z-trigger" if ordinal == 0 else f"a-support-{ordinal:02d}"
            )
            ordered = tuple(sorted(signals))
            self.accepted_real_references[receipt_id] = SimpleNamespace(
                ordinal=ordinal,
                receipt_id=receipt_id,
                stable_physical_interaction_id=f"physical-{ordinal}",
                ordered_signal_identities=ordered,
                typed_signal_roles=tuple(
                    (signal_id, "BASE_TERMINAL") for signal_id in ordered
                ),
                observed_outcome=observed,
            )
            return receipt_id

    authority = _LateTriggerAuthority()
    ecology = ProspectiveBoundaryCandidateEcology()
    promotions = ()
    for ordinal in range(5):
        receipt_id = authority.add(
            ordinal,
            signals=("late-trigger-pattern",),
            observed=True,
        )
        promotions, _event = _boundary_ecology_step(
            authority,
            ecology,
            receipt_id=receipt_id,
            pre_outcome_state=AvailabilityState.UNKNOWN,
        )

    assert len(promotions) == 1
    request = promotions[0]
    assert request.triggering_receipt_id not in request.inspected_receipt_ids
    expected_commitment = _compact_set_commitment(
        tuple(authority.accepted_real_references),
        exclusive_frontier=5,
    )
    assert request.inspected_receipt_commitment == expected_commitment
    assert expected_commitment.count == 5

    # Supply only the tiny committed root shape consumed by the report-only
    # lineage audit.  The authority's real transaction is intentionally out
    # of scope here; this fixture isolates the V4 witness/commitment contract.
    ecology.mark_promoted(request.candidate_id)
    root_child_id = f"v2_adaptive_boundary_{request.request_digest}"
    authority.boundary_promotion_requests = {
        request.candidate_id: request,
    }
    authority.states = {
        root_child_id: SimpleNamespace(
            hypothesis=SimpleNamespace(
                members=request.members,
                polarity=AvailabilityState.AVAILABLE,
                source_generation=request.source_generation + 1,
                lineage_parent_id=None,
                specialization_depth=0,
                triggering_receipt_id=request.triggering_receipt_id,
                discovery_exclusion_receipt_ids=(),
                birth_frontier=5,
            ),
            prospectively_certified=False,
            certification_receipt_ids=(),
            support_receipt_ids=(),
            contradiction_receipt_ids=(),
            support=0,
            contradictions=0,
            retired=False,
        ),
    }

    audit = _adaptive_positive_lineage_audit(authority, ecology)
    assert audit["lineage_count"] == 1
    row = audit["rows"][0]
    assert row["authority_inspected_receipt_ids"] == list(
        request.inspected_receipt_ids
    )
    assert row["authority_inspected_receipt_commitment"] == (
        expected_commitment.manifest()
    )


def test_promotion_dedup_reads_only_bounded_live_authority_state() -> None:
    authority = _GuardedBoundaryAuthority()
    ecology = ProspectiveBoundaryCandidateEcology()
    promotions = ()
    for ordinal in range(4):
        receipt_id = authority.add(
            ordinal,
            signals=("bounded-live-pattern",),
            observed=True,
        )
        promotions, _event = _boundary_ecology_step(
            authority,
            ecology,
            receipt_id=receipt_id,
            pre_outcome_state=AvailabilityState.UNKNOWN,
        )

    assert len(promotions) == 1
    assert authority.live_state_reads >= 1


def test_authority_handoff_recloses_intervening_nonmatching_real_reads() -> None:
    """The atomic handoff binds the complete post-birth evidence interval."""

    authority = _BoundaryAuthority()
    ecology = ProspectiveBoundaryCandidateEcology()
    trigger_id = authority.add(0, signals=("anchor",), observed=True)
    _promotions, event = _boundary_ecology_step(
        authority,
        ecology,
        receipt_id=trigger_id,
        pre_outcome_state=AvailabilityState.UNKNOWN,
    )
    candidate = next(
        ecology.sketches[candidate_id]
        for candidate_id in event["born_candidate_ids"]
        if ecology.sketches[candidate_id].members == ("anchor",)
    )
    intervening_id = authority.add(
        1,
        signals=("unrelated",),
        observed=False,
    )
    _boundary_ecology_step(
        authority,
        ecology,
        receipt_id=intervening_id,
        pre_outcome_state=AvailabilityState.UNKNOWN,
    )
    for ordinal in range(2, 5):
        receipt_id = authority.add(
            ordinal,
            signals=("anchor",),
            observed=True,
        )
        _boundary_ecology_step(
            authority,
            ecology,
            receipt_id=receipt_id,
            pre_outcome_state=AvailabilityState.UNKNOWN,
        )

    request = _boundary_promotion_request_from_candidate(
        authority,
        ecology,
        candidate.sketch_id,
    )

    assert request is not None
    assert request.supporting_receipt_ids == (
        "receipt-0",
        "receipt-2",
        "receipt-3",
        "receipt-4",
    )
    complete_inspected = tuple(
        f"receipt-{ordinal}" for ordinal in range(5)
    )
    assert request.inspected_receipt_commitment == _compact_set_commitment(
        complete_inspected,
        exclusive_frontier=5,
    )
    assert len(request.inspected_receipt_ids) <= 4
    assert intervening_id in request.inspected_receipt_ids


def test_real_authority_positive_lineage_audit_maps_postbirth_certification() -> None:
    """A committed ecology bud joins one root cell and its REAL evidence."""

    authority = _mixed_authority(
        AvailabilityState.AVAILABLE,
        structural_mode=StructuralMode.EVENT_DRIVEN,
    )
    ecology = ProspectiveBoundaryCandidateEcology()
    promotions = ()
    for ordinal in range(4):
        opened, _emission = _consume(
            authority,
            outcome=True,
            fullmove=400 + ordinal,
            frame_id=f"positive-lineage:birth:{ordinal}",
        )
        promotions, _event = _boundary_ecology_step(
            authority,
            ecology,
            receipt_id=opened[2].receipt_id,
            pre_outcome_state=AvailabilityState.UNKNOWN,
        )
    assert len(promotions) == 1
    request = promotions[0]
    authority.settle_pending_structural_requests(promotions)
    ecology.mark_promoted(request.candidate_id)
    root_child_id = authority._adaptive_boundary_child_id(request)
    hypothesis = authority.states[root_child_id].hypothesis
    exclusion = hypothesis.discovery_exclusion_commitment
    assert exclusion is not None
    assert hypothesis.discovery_exclusion_receipt_ids == exclusion.witness_ids
    assert exclusion.count == len(authority.accepted_real_references)
    assert exclusion.exclusive_frontier == authority.next_expected_ordinal
    assert exclusion == authority._accepted_real_prefix_commitment(
        authority.accepted_real_references
    )

    # Certification starts only after the adaptive root exists.  A fourth
    # clean REAL event is enough for the native prospective maturity rule.
    for ordinal in range(4):
        opened, _emission = _consume(
            authority,
            outcome=True,
            fullmove=410 + ordinal,
            frame_id=f"positive-lineage:postbirth:{ordinal}",
        )
        _boundary_ecology_step(
            authority,
            ecology,
            receipt_id=opened[2].receipt_id,
            pre_outcome_state=AvailabilityState.UNKNOWN,
        )

    audit = _adaptive_positive_lineage_audit(authority, ecology)
    assert audit["lineage_count"] == 1
    assert audit["certification_leak_count"] == 0
    assert audit["all_certification_disjoint"] is True
    assert audit["all_certification_postbirth"] is True
    row = audit["rows"][0]
    assert row["candidate_id"] == request.candidate_id
    assert row["members"] == list(request.members)
    assert row["root_child_id"] in authority.states
    assert row["ecology_triggering_receipt_id"] == request.triggering_receipt_id
    assert set(row["authority_supporting_receipt_ids"]) <= set(
        row["authority_inspected_receipt_ids"]
    )
    assert len(row["nodes"]) == 1
    node = row["nodes"][0]
    assert node["cell_id"] == row["root_child_id"]
    assert node["certified"] is True
    assert node["postbirth_certification_receipt_ids"]
    assert node["certification_leak_receipt_ids"] == []
    assert node["certification_discovery_disjoint"] is True
    assert node["all_certification_postbirth"] is True

    restored_authority = NativeProspectiveAuthorityV2.loads(authority.dumps())
    restored_ecology = ProspectiveBoundaryCandidateEcology.loads(ecology.dumps())
    assert _adaptive_positive_lineage_audit(
        restored_authority,
        restored_ecology,
    ) == audit

    tampered_authority = NativeProspectiveAuthorityV2.loads(
        authority.dumps()
    )
    tampered_state = tampered_authority.states[root_child_id]
    tampered_state.certification_receipt_ids.append(
        tampered_state.hypothesis.discovery_exclusion_receipt_ids[0]
    )
    with pytest.raises(
        RuntimeError,
        match="reused discovery or pre-birth evidence",
    ):
        _adaptive_positive_lineage_audit(
            tampered_authority,
            restored_ecology,
        )


def test_ecology_authority_interval_restore_has_exact_continuation() -> None:
    """The ecology sidecar and authority resume as one deterministic interval."""

    def apply_interval(
        authority,
        ecology,
        ordinals: range,
    ) -> tuple:
        promotions = ()
        for ordinal in ordinals:
            opened, _emission = _consume(
                authority,
                outcome=True,
                fullmove=500 + ordinal,
                frame_id=f"positive-lineage:interval:{ordinal}",
            )
            promotions, _event = _boundary_ecology_step(
                authority,
                ecology,
                receipt_id=opened[2].receipt_id,
                pre_outcome_state=AvailabilityState.UNKNOWN,
            )
        return promotions

    uninterrupted_authority = _mixed_authority(
        AvailabilityState.AVAILABLE,
        structural_mode=StructuralMode.EVENT_DRIVEN,
    )
    uninterrupted_ecology = ProspectiveBoundaryCandidateEcology()
    promotions = apply_interval(
        uninterrupted_authority,
        uninterrupted_ecology,
        range(4),
    )
    assert len(promotions) == 1
    uninterrupted_authority.settle_pending_structural_requests(promotions)
    uninterrupted_ecology.mark_promoted(promotions[0].candidate_id)
    apply_interval(uninterrupted_authority, uninterrupted_ecology, range(4, 8))

    resumed_authority = _mixed_authority(
        AvailabilityState.AVAILABLE,
        structural_mode=StructuralMode.EVENT_DRIVEN,
    )
    resumed_ecology = ProspectiveBoundaryCandidateEcology()
    apply_interval(resumed_authority, resumed_ecology, range(2))
    authority_payload = resumed_authority.dumps()
    ecology_payload = resumed_ecology.dumps()
    resumed_authority = NativeProspectiveAuthorityV2.loads(authority_payload)
    resumed_ecology = ProspectiveBoundaryCandidateEcology.loads(ecology_payload)
    resumed_promotions = apply_interval(
        resumed_authority,
        resumed_ecology,
        range(2, 4),
    )
    assert len(resumed_promotions) == 1
    resumed_authority.settle_pending_structural_requests(resumed_promotions)
    resumed_ecology.mark_promoted(resumed_promotions[0].candidate_id)
    apply_interval(resumed_authority, resumed_ecology, range(4, 8))

    assert resumed_authority.continuation_manifest() == (
        uninterrupted_authority.continuation_manifest()
    )
    assert resumed_ecology.manifest() == uninterrupted_ecology.manifest()
    assert _adaptive_positive_lineage_audit(
        resumed_authority,
        resumed_ecology,
    ) == _adaptive_positive_lineage_audit(
        uninterrupted_authority,
        uninterrupted_ecology,
    )
