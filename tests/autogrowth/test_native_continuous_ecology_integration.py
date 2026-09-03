"""Data-free integration checks for immutable local hypothesis births."""

from dataclasses import replace
from types import SimpleNamespace

import pytest

from recon_lite_chess.autogrowth.native_all_reply_envelope import AvailabilityState
from recon_lite_chess.autogrowth.native_intrinsic_curriculum import (
    _boundary_ecology_step,
    _boundary_observation_from_v2_reference,
    _boundary_promotion_request_from_candidate,
    _new_boundary_ecology_from_authority_history,
    _verify_boundary_ecology_alignment,
)
from recon_lite_chess.autogrowth.native_prospective_boundary_candidate_ecology import (
    BoundaryEcologyConfig,
    BoundaryExpandDemand,
    BoundaryObservation,
    ProspectiveBoundaryCandidateEcology,
)
from recon_lite_chess.autogrowth.native_prospective_evidence_authority_v2 import (
    StructuralMode,
)
from tests.autogrowth.test_native_mixed_evidence_specialization import (
    _consume,
    _mixed_authority,
)


class _BirthAuthority:
    """Only the accepted-REAL/birth interface; no chess or graph fixture."""

    def __init__(self):
        self.accepted_real_references = {}
        self.boundary_hypothesis_births = {}
        self.states = {}
        self.birth_calls = []

    def accept(self, signals, outcome):
        ordinal = len(self.accepted_real_references)
        receipt_id = f"receipt-{ordinal}"
        identities = tuple(sorted(signals))
        self.accepted_real_references[receipt_id] = SimpleNamespace(
            ordinal=ordinal,
            receipt_id=receipt_id,
            stable_physical_interaction_id=f"physical-{ordinal}",
            ordered_signal_identities=identities,
            typed_signal_roles=tuple(
                (signal, "graph_visible_signal") for signal in identities
            ),
            observed_outcome=outcome,
        )
        return receipt_id

    def source_policy_identity_for_receipt(self, receipt_id):
        assert receipt_id in self.accepted_real_references
        return "frozen-policy-v1"

    def register_boundary_hypothesis_birth(self, **fields):
        # Deliberately stricter than production idempotence: the curriculum
        # must recognize reuse, not try to birth the same hypothesis again.
        assert fields["candidate_id"] not in self.boundary_hypothesis_births
        assert fields["birth_frontier_ordinal"] == (
            len(self.accepted_real_references) - 1
        )
        self.birth_calls.append(dict(fields))
        birth = SimpleNamespace(**fields)
        self.boundary_hypothesis_births[fields["candidate_id"]] = birth
        return "test-birth-digest"


def _accept_and_step(authority, ecology, signals, outcome, *, state):
    receipt_id = authority.accept(signals, outcome)
    return _boundary_ecology_step(
        authority,
        ecology,
        receipt_id=receipt_id,
        pre_outcome_state=state,
    )


def _supported_residual_fixture():
    authority = _BirthAuthority()
    ecology = ProspectiveBoundaryCandidateEcology(
        BoundaryEcologyConfig(continuous_evidence=True)
    )
    _accept_and_step(
        authority,
        ecology,
        ("anchor", "separating-feature"),
        True,
        state=AvailabilityState.UNKNOWN,
    )
    parent = next(item for item in ecology.active_sketches if item.arity == 1)
    residual = next(item for item in ecology.active_sketches if item.arity == 2)
    _accept_and_step(
        authority,
        ecology,
        residual.members,
        True,
        state=AvailabilityState.AVAILABLE,
    )
    assert ecology.sketches[residual.sketch_id].prospective_support_count == 1
    return authority, ecology, parent, residual


def test_live_residual_reuse_preserves_original_birth_and_prospective_support():
    authority, ecology, parent, residual = _supported_residual_fixture()
    original_birth = authority.boundary_hypothesis_births[residual.sketch_id]
    birth_calls = tuple(authority.birth_calls)

    promotions, reaction = _accept_and_step(
        authority,
        ecology,
        parent.members,
        False,
        state=AvailabilityState.UNKNOWN,
    )

    assert promotions == ()
    assert residual.sketch_id in reaction["refinement_candidate_ids"]
    assert tuple(authority.birth_calls) == birth_calls
    assert authority.boundary_hypothesis_births[residual.sketch_id] is original_birth
    reused = ecology.sketches[residual.sketch_id]
    assert reused.birth_frontier_ordinal == original_birth.birth_frontier_ordinal == 0
    assert reused.prospective_support_count == 1
    assert reused.positive_receipt_ids == ("receipt-1",)
    assert "receipt-0" not in reused.positive_receipt_ids
    assert set(authority.boundary_hypothesis_births) == set(ecology.sketches)


def test_live_residual_reuse_rejects_a_changed_birth_frontier():
    authority, ecology, parent, residual = _supported_residual_fixture()
    original_birth = authority.boundary_hypothesis_births[residual.sketch_id]
    # Simulate an internal mutation, not a legitimate refinement: the same
    # incarnation may not silently move its semantic evidence boundary.
    ecology._store_sketch(replace(
        ecology.sketches[residual.sketch_id], birth_frontier_ordinal=1
    ))

    with pytest.raises(RuntimeError, match="reused boundary hypothesis changed"):
        _accept_and_step(
            authority,
            ecology,
            parent.members,
            False,
            state=AvailabilityState.UNKNOWN,
        )

    assert authority.boundary_hypothesis_births[residual.sketch_id] is original_birth
    assert original_birth.birth_frontier_ordinal == 0


def test_disabled_mode_preserves_prechange_incarnation_and_ranking_fixture():
    # Recorded from c225fe6a4356af5f2b7b643e52deeab92fab4d24, before V26.
    ecology = ProspectiveBoundaryCandidateEcology(BoundaryEcologyConfig(
        genome_seed=17, continuous_evidence=False
    ))
    stream = (
        (("anchor", "good", "safe"), True),
        (("anchor",), False),
        (("anchor", "good", "safe"), True),
        (("anchor", "good", "safe"), True),
        (("anchor", "good", "safe"), True),
    )
    for ordinal, (signals, outcome) in enumerate(stream):
        ecology.react(
            BoundaryObservation(ordinal, f"r{ordinal}", f"p{ordinal}", signals, outcome),
            pre_outcome_state="unknown",
        )

    assert [
        (item.sketch_id, item.members, item.support_count, item.contradiction_count)
        for item in ecology.rank_candidates()
    ] == [
        ("7e15a9cd7db6e422a49d2fbd1540cae6", ("good",), 4, 0),
        ("2be04b3ce84718661d44fdd9879c1e22", ("anchor", "safe"), 4, 0),
        ("096b416c251991ad25131780c2953ec7", ("anchor", "good", "safe"), 4, 0),
        ("6a5fb62e57182a2f5eae2548bf7b8753", ("anchor", "good"), 3, 0),
        ("fb310d0706e7d279c9e9aa0ca671440a", ("safe",), 2, 0),
    ]


@pytest.mark.parametrize(
    "polarity", (AvailabilityState.AVAILABLE, AvailabilityState.REFUTED)
)
def test_initialization_remembers_only_base_discovery_negatives(polarity):
    authority = _mixed_authority(
        polarity, structural_mode=StructuralMode.EVENT_DRIVEN
    )
    ecology = _new_boundary_ecology_from_authority_history(
        authority, genome_seed=17, continuous_evidence=True
    )
    expected = {
        receipt_id for receipt_id in authority.base.receipts
        if not authority.accepted_real_references[receipt_id].observed_outcome
    }

    assert set(ecology.observations) == expected
    assert all(not item.observed for item in ecology.observations.values())
    assert ecology.lifetime_birth_count == ecology.active_sketch_count == 0
    _verify_boundary_ecology_alignment(authority, ecology, roundtrip=True)


def test_base_negative_blocks_coarse_promotion_after_four_future_successes():
    authority = _mixed_authority(
        AvailabilityState.AVAILABLE, structural_mode=StructuralMode.EVENT_DRIVEN
    )
    ecology = _new_boundary_ecology_from_authority_history(
        authority, genome_seed=17, continuous_evidence=True
    )
    base_negative_ids = set(authority.base.receipts)
    assert len(base_negative_ids) == 4

    discovery = _consume(
        authority, outcome=True, fullmove=900,
        frame_id="continuous-base-negative:discovery",
    )[0][2]
    reference = authority.accepted_real_references[discovery.receipt_id]
    source_identity = authority.source_policy_identity_for_receipt(discovery.receipt_id)
    observation = _boundary_observation_from_v2_reference(
        reference, source_identity=source_identity
    )
    ecology.observe(observation)
    roles = dict(observation.signal_roles)
    # Deliberately propose an actually shared coarse atom; this tests the
    # safety boundary even when the usual local beam prefers a clean atom.
    member = next(iter(sorted(
        identity for identity in observation.signal_ids
        if roles[identity] in {"BASE_TERMINAL", "MATURE_COMPOSITE"}
        and all(
            identity in ecology.observations[receipt_id].signal_ids
            for receipt_id in base_negative_ids
        )
    )))
    candidate = ecology.expand(BoundaryExpandDemand(
        ordinal=observation.ordinal,
        triggering_receipt_id=observation.receipt_id,
        signal_ids=(member,),
        signal_roles=((member, roles[member]),),
        candidate_width=1,
        polarity=True,
    ))[0]
    authority.register_boundary_hypothesis_birth(
        candidate_id=candidate.sketch_id,
        members=candidate.members,
        member_signal_roles=candidate.member_signal_roles,
        source_identity=candidate.source_identity,
        semantic_identity=candidate.semantic_identity,
        birth_frontier_ordinal=candidate.birth_frontier_ordinal,
        triggering_receipt_id=candidate.triggering_receipt_id,
    )
    assert candidate.inherited_negative_count == 4
    assert candidate.prospective_support_count == 0

    for index in range(4):
        receipt = _consume(
            authority, outcome=True, fullmove=901 + index,
            frame_id=f"continuous-base-negative:future-{index}",
        )[0][2]
        promotions, _reaction = _boundary_ecology_step(
            authority, ecology, receipt_id=receipt.receipt_id,
            pre_outcome_state=AvailabilityState.AVAILABLE,
        )
        assert promotions == ()

    latest = ecology.sketches[candidate.sketch_id]
    assert latest.prospective_support_count == 4
    assert latest.inherited_negative_count == 4
    assert set(latest.positive_receipt_ids).isdisjoint(base_negative_ids)
    assert discovery.receipt_id not in latest.positive_receipt_ids
    assert not ecology.promotion_decision(candidate.sketch_id).eligible
    # Local safe-point handling must abstain, not submit the known-bad rule
    # and crash in the authority's independent negative-evidence check.
    assert _boundary_promotion_request_from_candidate(
        authority, ecology, candidate.sketch_id
    ) is None
    _verify_boundary_ecology_alignment(authority, ecology, roundtrip=True)
