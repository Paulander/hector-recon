from dataclasses import FrozenInstanceError, replace
from itertools import combinations
from typing import Optional

import pytest

from recon_lite_chess.autogrowth.native_prospective_boundary_candidate_ecology import (
    BoundaryEcologyConfig,
    BoundaryExpandDemand,
    BoundaryObservation,
    DuplicatePhysicalReceiptError,
    MAX_RETAINED_CONTRADICTION_RECEIPTS,
    MAX_RETAINED_READ_RECEIPTS,
    MAX_RETAINED_REFINEMENT_RECEIPTS,
    MAX_RETAINED_SUPPORT_RECEIPTS,
    ProspectiveBoundaryCandidateEcology,
    SketchLifecycle,
)


def _observation(index: int, members, observed: bool = True, physical: Optional[str] = None):
    return BoundaryObservation(
        ordinal=index,
        receipt_id=f"receipt-{index}",
        physical_id=physical or f"physical-{index}",
        signal_ids=tuple(sorted(set(members))),
        observed=observed,
    )


class _NoLifetimeValuesDict(dict):
    """Permit keyed hot-path access while rejecting lifetime scans."""

    def values(self):
        raise AssertionError("hot path scanned the lifetime sketch ledger")


def _pad_inactive_sketch_history(
    ecology: ProspectiveBoundaryCandidateEcology,
    template,
    count: int = 2048,
) -> None:
    for index in range(count):
        padded = replace(
            template,
            sketch_id=f"historical-tombstone-{index:05d}",
            state=SketchLifecycle.DORMANT,
            retirement_reason="historical_test_padding",
        )
        ecology._sketches[padded.sketch_id] = padded
        ecology._tombstones[padded.sketch_id] = padded
    ecology._births += count


def test_expand_buds_at_most_three_cheap_competing_sketches():
    ecology = ProspectiveBoundaryCandidateEcology()
    trigger = _observation(0, ("alpha", "beta", "gamma", "delta"), True)
    ecology.observe(trigger)
    sketches = ecology.expand(
        BoundaryExpandDemand(
            ordinal=0,
            signal_ids=("alpha", "beta", "gamma", "delta"),
            candidate_width=3,
            triggering_receipt_id=trigger.receipt_id,
            polarity=True,
        )
    )

    assert len(sketches) == 3
    assert {sketch.arity for sketch in sketches} == {1, 2, 3}
    assert all(sketch.state is SketchLifecycle.ACTIVE for sketch in sketches)
    assert all(sketch.arity <= 3 for sketch in sketches)
    assert ecology.active_sketch_count == 3


def test_react_owns_birth_and_single_promotion_deterministically() -> None:
    def run():
        ecology = ProspectiveBoundaryCandidateEcology()
        reactions = []
        for ordinal in range(4):
            reactions.append(ecology.react(
                _observation(ordinal, ("alpha", "beta"), True),
                pre_outcome_state="unknown",
            ))
        return ecology, reactions

    first, first_reactions = run()
    second, second_reactions = run()

    assert [item.to_manifest() for item in first_reactions] == [
        item.to_manifest() for item in second_reactions
    ]
    assert [item.digest for item in first_reactions] == [
        item.digest for item in second_reactions
    ]
    assert first.manifest() == second.manifest()
    final = first_reactions[-1]
    assert final.promotion_candidate_id is not None
    assert final.surprise_success is True
    assert "ranked_candidate_ids" not in final.to_manifest()
    with pytest.raises(FrozenInstanceError):
        final.promotion_candidate_id = "host-substitution"


def test_react_retires_authority_duplicate_before_nominating() -> None:
    ecology = ProspectiveBoundaryCandidateEcology()
    reaction = None
    for ordinal in range(4):
        reaction = ecology.react(
            _observation(ordinal, ("known-pattern",), True),
            pre_outcome_state="unknown",
            live_positive_patterns=(("known-pattern",),),
        )

    assert reaction is not None
    assert reaction.promotion_candidate_id is None
    assert reaction.retired_redundant_candidate_ids
    retired = tuple(
        ecology.sketches[candidate_id]
        for candidate_id in reaction.retired_redundant_candidate_ids
    )
    assert all(
        item.retirement_reason == "redundant_authority_pattern"
        for item in retired
    )


def test_react_treats_failure_as_contrast_without_birth() -> None:
    ecology = ProspectiveBoundaryCandidateEcology()
    reaction = ecology.react(
        _observation(0, ("coarse",), False),
        pre_outcome_state="unknown",
    )

    assert reaction.contrast_observation is True
    assert reaction.surprise_success is False
    assert reaction.born_candidate_ids == ()
    assert reaction.promotion_candidate_id is None
    assert ecology.lifetime_birth_count == 0


def test_expand_never_scans_lifetime_tombstones() -> None:
    def run(*, padded: bool):
        ecology = ProspectiveBoundaryCandidateEcology()
        historical = _observation(0, ("historical",), True)
        ecology.observe(historical)
        template = ecology.expand(BoundaryExpandDemand(
            ordinal=0,
            signal_ids=historical.signal_ids,
            candidate_width=1,
            triggering_receipt_id=historical.receipt_id,
            polarity=True,
        ))[0]
        for ordinal in range(1, 4):
            ecology.observe(_observation(ordinal, template.members, True))
        ecology.mark_promoted(template.sketch_id)
        if padded:
            _pad_inactive_sketch_history(ecology, template)
            ecology._sketches = _NoLifetimeValuesDict(ecology._sketches)
        trigger = _observation(4, ("fresh-pattern",), True)
        before_births = ecology.lifetime_birth_count
        before_prunes = dict(ecology._prune_counts)
        ecology.observe(trigger)
        born = ecology.expand(BoundaryExpandDemand(
            ordinal=4,
            signal_ids=trigger.signal_ids,
            candidate_width=1,
            triggering_receipt_id=trigger.receipt_id,
            polarity=True,
        ))
        return (
            tuple(item.members for item in born),
            ecology.lifetime_birth_count - before_births,
            ecology.active_sketch_count,
            {
                key: ecology._prune_counts[key] - before_prunes[key]
                for key in before_prunes
            },
        )

    assert run(padded=True) == run(padded=False)


def test_refinement_and_settlement_never_scan_lifetime_tombstones() -> None:
    def run(*, padded: bool):
        ecology = ProspectiveBoundaryCandidateEcology()
        trigger = _observation(0, ("anchor", "good"), True)
        ecology.observe(trigger)
        parent = ecology.expand(BoundaryExpandDemand(
            ordinal=0,
            signal_ids=("anchor",),
            candidate_width=1,
            triggering_receipt_id=trigger.receipt_id,
            polarity=True,
        ))[0]
        if padded:
            _pad_inactive_sketch_history(ecology, parent)
            ecology._sketches = _NoLifetimeValuesDict(ecology._sketches)
        before_births = ecology.lifetime_birth_count
        before_prunes = dict(ecology._prune_counts)
        ecology.observe(_observation(1, ("anchor", "bad"), False))
        refinement_ids = ecology.last_refinement_ids
        settled = ecology.settle_refinements()
        return (
            tuple(
                ecology.sketches[candidate_id].members
                for candidate_id in refinement_ids
            ),
            tuple((item.members, item.state.value) for item in settled),
            ecology.lifetime_birth_count - before_births,
            ecology.active_sketch_count,
            {
                key: ecology._prune_counts[key] - before_prunes[key]
                for key in before_prunes
            },
        )

    assert run(padded=True) == run(padded=False)


def test_contrastive_beam_keeps_pure_width_three_when_narrower_terms_are_impure():
    ecology = ProspectiveBoundaryCandidateEcology()
    rows = (
        _observation(0, ("a", "b", "c", "positive-0"), True),
        _observation(1, ("a", "b", "c", "positive-1"), True),
        _observation(2, ("a", "b", "c", "positive-2"), True),
        _observation(3, ("a", "d", "e"), False),
        _observation(4, ("b", "d", "f"), False),
        _observation(5, ("c", "e", "f"), False),
        _observation(6, ("a", "b", "d"), False),
        _observation(7, ("a", "c", "e"), False),
        _observation(8, ("b", "c", "f"), False),
    )
    ecology.observe_many(rows)
    trigger = _observation(9, ("a", "b", "c", "current"), True)
    ecology.observe(trigger)

    sketches = ecology.expand(BoundaryExpandDemand(
        9,
        trigger.signal_ids,
        candidate_width=3,
        triggering_receipt_id=trigger.receipt_id,
        polarity=True,
    ))

    assert len(sketches) == 3
    assert {item.arity for item in sketches} == {1, 2, 3}
    assert ("a", "b", "c") in {item.members for item in sketches}


def test_high_dimensional_hash_exploration_reaches_width_three_residual():
    """A useful residual need not occur in the canonical combination prefix."""

    signal_ids = tuple(f"signal-{index:03d}" for index in range(100))
    # For the default genome and ordinal below this is the first stable-hash
    # triple, while its canonical combination rank is far beyond the first
    # 4096 width-three combinations.  The test therefore exercises the
    # reserved exploration path rather than the old naive prefix.
    residual = ("signal-022", "signal-032", "signal-066")
    rows = (
        _observation(0, residual, True),
        _observation(1, residual, True),
        _observation(2, residual, True),
        _observation(3, (residual[0], residual[1], "negative-ab"), False),
        _observation(4, (residual[0], residual[2], "negative-ac"), False),
        _observation(5, (residual[1], residual[2], "negative-bc"), False),
    )
    ecology = ProspectiveBoundaryCandidateEcology()
    ecology.observe_many(rows)
    trigger = _observation(6, signal_ids, True)
    ecology.observe(trigger)

    sketches = ecology.expand(BoundaryExpandDemand(
        ordinal=6,
        signal_ids=signal_ids,
        candidate_width=3,
        triggering_receipt_id=trigger.receipt_id,
        polarity=True,
    ))

    canonical_prefix = tuple(combinations(signal_ids, 3))[:4096]
    assert residual not in canonical_prefix
    assert residual in {item.members for item in sketches}
    # Every narrower projection is contradicted, while the conjunction is
    # pure in the bounded local ledger.
    for width in (1, 2):
        for members in combinations(residual, width):
            assert any(
                not observation.observed
                and set(members).issubset(observation.signal_ids)
                for observation in rows
            )
    local_matches = [
        observation
        for observation in (*rows, trigger)
        if set(residual).issubset(observation.signal_ids)
    ]
    assert (
        sum(item.observed for item in local_matches),
        sum(not item.observed for item in local_matches),
    ) == (4, 0)


def test_candidate_beam_width_changes_residual_extension_frontier():
    pool = tuple(f"signal-{index:02d}" for index in range(30))
    target = ("signal-00", "signal-01", "signal-02")
    rows = []
    ordinal = 0
    for _ in range(10):
        rows.append(_observation(ordinal, target, True))
        ordinal += 1
    for _ in range(3):
        rows.append(_observation(ordinal, ("signal-20",), True))
        ordinal += 1
    for _ in range(2):
        rows.append(_observation(ordinal, ("signal-10",), True))
        ordinal += 1
    for _ in range(2):
        rows.append(_observation(ordinal, ("signal-11",), True))
        ordinal += 1
    for _ in range(3):
        rows.append(_observation(ordinal, ("signal-01", "signal-29"), False))
        ordinal += 1
    for _ in range(3):
        rows.append(_observation(ordinal, ("signal-00", "signal-28"), False))
        ordinal += 1
    for _ in range(3):
        rows.append(_observation(ordinal, ("signal-02", "signal-29"), False))
        ordinal += 1
    trigger = _observation(ordinal, pool, True)

    def ranked(beam_width):
        ecology = ProspectiveBoundaryCandidateEcology(
            BoundaryEcologyConfig(
                candidate_beam_width=beam_width,
                candidate_search_budget=64,
            )
        )
        ecology.observe_many((*rows, trigger))
        return ecology._ranked_residual_candidates(
            pool,
            trigger=trigger,
            candidate_width=3,
            ordinal=trigger.ordinal,
            polarity=True,
        )

    narrow = ranked(1)
    wide = ranked(4)
    assert narrow != wide
    assert target not in narrow
    assert target in wide


def test_reliability_precedes_raw_support_for_single_candidates():
    ecology = ProspectiveBoundaryCandidateEcology()
    rows = (
        _observation(0, ("pure",), True),
        _observation(1, ("broad",), True),
        _observation(2, ("broad",), True),
        _observation(3, ("broad",), False),
        _observation(4, ("broad",), False),
        _observation(5, ("broad",), False),
        _observation(6, ("broad",), False),
    )
    trigger = _observation(7, ("pure", "broad"), True)
    ecology.observe_many((*rows, trigger))
    sketches = ecology.expand(BoundaryExpandDemand(
        ordinal=7,
        signal_ids=trigger.signal_ids,
        candidate_width=1,
        triggering_receipt_id=trigger.receipt_id,
        polarity=True,
    ))

    assert len(sketches) == 1
    assert sketches[0].members == ("pure",)
    # ``pure`` is 2/2; ``broad`` is 3/7.  A support-first rank would choose
    # broad, despite its lower reliability and eventual contradiction death.


def test_expand_excludes_universal_policy_response_signal():
    ecology = ProspectiveBoundaryCandidateEcology()
    trigger = BoundaryObservation(
        ordinal=0,
        receipt_id="receipt-0",
        physical_id="physical-0",
        signal_ids=("base:local", "internal:policy_response"),
        signal_roles=(
            ("base:local", "BASE_TERMINAL"),
            ("internal:policy_response", "POLICY_RESPONSE"),
        ),
        observed=True,
    )
    ecology.observe(trigger)
    sketches = ecology.expand(BoundaryExpandDemand(
        ordinal=0,
        signal_ids=trigger.signal_ids,
        signal_roles=trigger.signal_roles,
        candidate_width=2,
        triggering_receipt_id=trigger.receipt_id,
        polarity=True,
    ))

    assert tuple(sketch.members for sketch in sketches) == (("base:local",),)


def test_promotion_enumerates_support_contradiction_and_all_reads(monkeypatch):
    ecology = ProspectiveBoundaryCandidateEcology()
    trigger = _observation(0, ("a", "b", "c"), True)
    ecology.observe(trigger)
    candidate = ecology.expand(
        BoundaryExpandDemand(
            0,
            ("a", "b", "c"),
            candidate_width=1,
            triggering_receipt_id=trigger.receipt_id,
            polarity=True,
        )
    )[0]
    for index in range(1, 4):
        ecology.observe(_observation(index, candidate.members, True))
    # A nonmatching read must still be part of the inspection/exclusion set.
    ecology.observe(_observation(4, ("unrelated",), True))

    decision = ecology.promotion_decision(candidate.sketch_id, full_audit=True)
    assert decision.eligible is True
    assert decision.support_count == 4
    assert decision.contradiction_count == 0
    assert decision.supporting_receipt_ids == tuple(f"receipt-{i}" for i in range(4))
    assert decision.inspected_receipt_ids == tuple(f"receipt-{i}" for i in range(5))
    assert decision.discovery_exclusion_receipt_ids == decision.inspected_receipt_ids
    assert decision.wilson_lower_bound >= 0.55
    with pytest.raises(FrozenInstanceError):
        decision.eligible = False

    monkeypatch.setattr(
        ecology,
        "_full_promotion_audit",
        lambda _candidate: pytest.fail(
            "commit-time promotion must not perform a full ledger audit"
        ),
    )
    promoted = ecology.mark_promoted(candidate.sketch_id)
    assert promoted.state is SketchLifecycle.DORMANT
    assert promoted.retirement_reason == "promoted"
    assert candidate.sketch_id in ecology.tombstones
    assert ecology.active_sketch_count == 0
    with pytest.raises(ValueError, match="active candidate"):
        ecology.mark_promoted(candidate.sketch_id)


def test_long_lived_broad_sketch_keeps_bounded_local_receipts():
    ecology = ProspectiveBoundaryCandidateEcology()
    trigger = _observation(0, ("broad",), True)
    ecology.observe(trigger)
    candidate = ecology.expand(BoundaryExpandDemand(
        0,
        ("broad",),
        candidate_width=1,
        triggering_receipt_id=trigger.receipt_id,
        polarity=True,
    ))[0]
    for index in range(1, 101):
        ecology.observe(_observation(index, ("broad",), True))

    stored = ecology.sketches[candidate.sketch_id]
    local_decision = ecology.promotion_decision(candidate.sketch_id)
    assert local_decision.support_count == 101
    assert len(local_decision.supporting_receipt_ids) == 4
    assert len(local_decision.inspected_receipt_ids) == 4
    decision = ecology.promotion_decision(candidate.sketch_id, full_audit=True)
    assert stored.support_count == 101
    assert len(stored.read_receipt_ids) == 4
    assert decision.support_count == 101
    assert len(decision.supporting_receipt_ids) == 101
    assert len(decision.inspected_receipt_ids) == 101


def test_first_contradiction_abstains_and_keeps_lineage_for_refinement():
    ecology = ProspectiveBoundaryCandidateEcology()
    trigger = _observation(0, ("a", "good"), True)
    ecology.observe(trigger)
    candidate = ecology.expand(
        BoundaryExpandDemand(
            0,
            ("a", "good"),
            candidate_width=1,
            triggering_receipt_id=trigger.receipt_id,
            polarity=True,
        )
    )[0]
    assert candidate.members == ("a",)
    ecology.observe(_observation(1, ("a", "bad"), False))

    state = ecology.sketches[candidate.sketch_id]
    decision = ecology.promotion_decision(candidate.sketch_id, full_audit=True)
    assert state.state is SketchLifecycle.REFINING
    assert state.retirement_reason == "contrast_requires_residual_refinement"
    assert state.support_count == 1
    assert state.contradiction_count == 1
    assert decision.eligible is False
    assert decision.reason == "lifecycle_refining"
    assert decision.contradicting_receipt_ids == ("receipt-1",)
    assert candidate.sketch_id not in ecology.tombstones
    residuals = tuple(
        item for item in ecology.sketches.values()
        if item.parent_sketch_id == candidate.sketch_id
    )
    assert len(residuals) == 1
    assert residuals[0].members == ("a", "good")
    assert residuals[0].state is SketchLifecycle.ACTIVE
    assert residuals[0].read_receipt_ids == ("receipt-0",)
    assert residuals[0].refinement_source_receipt_id == "receipt-1"
    assert ecology.last_refinement_ids == (residuals[0].sketch_id,)


def test_negative_trigger_cannot_birth_or_promote_a_negative_candidate():
    ecology = ProspectiveBoundaryCandidateEcology()
    failure = _observation(0, ("a", "bad"), False)
    ecology.observe(failure)
    with pytest.raises(ValueError, match="positive triggering"):
        BoundaryExpandDemand(
            ordinal=0,
            signal_ids=failure.signal_ids,
            candidate_width=1,
            triggering_receipt_id=failure.receipt_id,
            polarity=False,
        )
    assert ecology.active_sketch_count == 0
    assert ecology.lifetime_birth_count == 0


def test_failure_driven_residual_cleanly_separates_coarse_positive_rule():
    ecology = ProspectiveBoundaryCandidateEcology()
    trigger = _observation(0, ("anchor", "local-good"), True)
    ecology.observe(trigger)
    coarse = ecology.expand(BoundaryExpandDemand(
        ordinal=0,
        signal_ids=trigger.signal_ids,
        candidate_width=1,
        triggering_receipt_id=trigger.receipt_id,
        polarity=True,
    ))[0]
    ecology.observe(_observation(1, ("anchor", "local-bad"), False))
    residual = next(
        item for item in ecology.sketches.values()
        if item.parent_sketch_id == coarse.sketch_id
    )
    assert residual.members == ("anchor", "local-good")
    # The failure is contrast for the coarse parent, but not evidence against
    # the residual because its local micropattern is absent from the failure.
    assert ecology.sketches[coarse.sketch_id].contradiction_count == 1
    assert residual.contradiction_count == 0
    for index in range(2, 5):
        ecology.observe(_observation(index, residual.members, True))
    assert ecology.promotion_decision(
        residual.sketch_id,
        full_audit=True,
    ).eligible is True
    assert ecology.promotion_decision(
        coarse.sketch_id,
        full_audit=True,
    ).eligible is False


def test_refinement_parent_dies_only_after_bounded_exhaustion():
    ecology = ProspectiveBoundaryCandidateEcology()
    trigger = _observation(0, ("a",), True)
    ecology.observe(trigger)
    parent = ecology.expand(BoundaryExpandDemand(
        ordinal=0,
        signal_ids=trigger.signal_ids,
        candidate_width=1,
        triggering_receipt_id=trigger.receipt_id,
        polarity=True,
    ))[0]
    ecology.observe(_observation(1, ("a",), False))
    assert ecology.sketches[parent.sketch_id].state is SketchLifecycle.REFINING
    ecology.settle_refinements()
    assert ecology.sketches[parent.sketch_id].state is SketchLifecycle.REFINING
    ecology.observe(_observation(2, ("a",), False))
    ecology.observe(_observation(3, ("a",), False))
    changed = ecology.settle_refinements()
    assert changed
    assert ecology.sketches[parent.sketch_id].state is SketchLifecycle.DEAD
    assert parent.sketch_id in ecology.tombstones


def test_dead_sketch_frees_capacity_and_births_continue_beyond_cap():
    ecology = ProspectiveBoundaryCandidateEcology(
        BoundaryEcologyConfig(active_sketch_cap=1)
    )
    first_trigger = _observation(0, ("first",), True)
    ecology.observe(first_trigger)
    first = ecology.expand(
        BoundaryExpandDemand(
            0,
            ("first",),
            candidate_width=1,
            triggering_receipt_id=first_trigger.receipt_id,
            polarity=True,
        )
    )[0]
    second_trigger = _observation(1, ("second",), True)
    ecology.observe(second_trigger)
    second = ecology.expand(
        BoundaryExpandDemand(
            1,
            ("second",),
            candidate_width=1,
            triggering_receipt_id=second_trigger.receipt_id,
            polarity=True,
        )
    )[0]

    assert ecology.sketches[first.sketch_id].state is SketchLifecycle.DORMANT
    assert second.state is SketchLifecycle.ACTIVE
    assert ecology.active_sketch_count == 1
    assert ecology.lifetime_birth_count == 2
    assert len(ecology.tombstones) == 1


def test_duplicate_physical_receipt_is_rejected():
    ecology = ProspectiveBoundaryCandidateEcology()
    trigger = _observation(0, ("a",), True, physical="same")
    ecology.observe(trigger)
    ecology.expand(
        BoundaryExpandDemand(
            0,
            ("a",),
            candidate_width=1,
            triggering_receipt_id=trigger.receipt_id,
            polarity=True,
        )
    )
    with pytest.raises(DuplicatePhysicalReceiptError):
        ecology.observe(_observation(1, ("a",), True, physical="same"))


def test_observation_has_no_semantic_selector_inputs_and_is_immutable():
    observation = BoundaryObservation(0, "r", "p", ("signal",), True)
    assert {"fen", "move", "mate_depth", "curriculum_label"}.isdisjoint(
        observation.__dataclass_fields__
    )
    assert observation.receipt_kind == "REAL"
    with pytest.raises(FrozenInstanceError):
        observation.observed = False
    with pytest.raises(TypeError):
        BoundaryObservation(0, "r", "p", ("signal",), True, fen="x")


def test_observation_permutation_and_manifest_roundtrip_are_deterministic():
    demand = BoundaryExpandDemand(
        0,
        ("a", "b", "c", "d"),
        candidate_width=3,
        triggering_receipt_id="receipt-0",
        polarity=True,
    )
    observations = tuple(
        _observation(index, ("a", "b", "c", "d"), index < 4)
        for index in range(5)
    )
    first = ProspectiveBoundaryCandidateEcology()
    second = ProspectiveBoundaryCandidateEcology()
    first.observe(observations[0])
    second.observe(observations[0])
    first.expand(demand)
    second.expand(demand)
    first.observe_many(observations[1:])
    second.observe_many(reversed(observations[1:]))

    assert first.manifest() == second.manifest()
    restored = ProspectiveBoundaryCandidateEcology.from_manifest(first.manifest())
    assert restored.manifest() == first.manifest()
    assert restored.dumps() == first.dumps()


def test_refinement_snapshot_restore_preserves_lineage_and_event_view():
    ecology = ProspectiveBoundaryCandidateEcology()
    trigger = _observation(0, ("anchor", "good"), True)
    ecology.observe(trigger)
    parent = ecology.expand(BoundaryExpandDemand(
        ordinal=0,
        signal_ids=trigger.signal_ids,
        candidate_width=1,
        triggering_receipt_id=trigger.receipt_id,
        polarity=True,
    ))[0]
    ecology.observe(_observation(1, ("anchor", "bad"), False))
    snapshot = ecology.dumps()
    restored = ProspectiveBoundaryCandidateEcology.loads(snapshot)

    assert restored.manifest() == ecology.manifest()
    assert restored.last_refinement_ids == ecology.last_refinement_ids
    assert restored.sketches[parent.sketch_id].state is SketchLifecycle.REFINING
    child = next(
        item for item in restored.sketches.values()
        if item.parent_sketch_id == parent.sketch_id
    )
    assert child.members == ("anchor", "good")

    # Replaying the same next REAL observation from both snapshots must
    # produce the same exact state and newly discovered children.
    next_row = _observation(2, ("anchor", "better"), False)
    ecology.observe(next_row)
    restored.observe(next_row)
    assert restored.manifest() == ecology.manifest()


def test_capacity_pressure_during_refinement_cannot_leave_stale_parent_tombstone():
    ecology = ProspectiveBoundaryCandidateEcology(
        BoundaryEcologyConfig(active_sketch_cap=1)
    )
    trigger = _observation(0, ("anchor", "good"), True)
    ecology.observe(trigger)
    parent = ecology.expand(BoundaryExpandDemand(
        ordinal=0,
        signal_ids=trigger.signal_ids,
        candidate_width=1,
        triggering_receipt_id=trigger.receipt_id,
        polarity=True,
    ))[0]
    ecology.observe(_observation(1, ("anchor", "bad"), False))
    assert ecology.sketches[parent.sketch_id].state is SketchLifecycle.REFINING
    assert parent.sketch_id not in ecology.tombstones
    assert ProspectiveBoundaryCandidateEcology.loads(ecology.dumps()).manifest() == ecology.manifest()


def test_retired_pattern_can_rebud_as_a_fresh_incarnation():
    ecology = ProspectiveBoundaryCandidateEcology()
    first_trigger = _observation(0, ("known-shell",), True)
    ecology.observe(first_trigger)
    first = ecology.expand(BoundaryExpandDemand(
        ordinal=0,
        signal_ids=first_trigger.signal_ids,
        candidate_width=1,
        triggering_receipt_id=first_trigger.receipt_id,
        polarity=True,
    ))[0]
    for index in range(1, 4):
        ecology.observe(_observation(index, first.members, True))
    old_id = first.sketch_id
    ecology.mark_promoted(old_id)
    assert old_id in ecology.tombstones

    later_trigger = _observation(4, first.members, True)
    ecology.observe(later_trigger)
    reborn = ecology.expand(BoundaryExpandDemand(
        ordinal=4,
        signal_ids=later_trigger.signal_ids,
        candidate_width=1,
        triggering_receipt_id=later_trigger.receipt_id,
        polarity=True,
    ))[0]

    assert reborn.members == first.members
    assert reborn.sketch_id != old_id
    assert old_id in ecology.tombstones
    assert reborn.sketch_id not in ecology.tombstones
    restored = ProspectiveBoundaryCandidateEcology.loads(ecology.dumps())
    assert restored.manifest() == ecology.manifest()


def test_existing_live_superset_is_reused_as_parent_residual():
    ecology = ProspectiveBoundaryCandidateEcology()
    trigger = _observation(0, ("anchor", "good"), True)
    ecology.observe(trigger)
    born = ecology.expand(BoundaryExpandDemand(
        ordinal=0,
        signal_ids=trigger.signal_ids,
        candidate_width=2,
        triggering_receipt_id=trigger.receipt_id,
        polarity=True,
    ))
    parent = next(item for item in born if item.members == ("anchor",))
    existing_residual = next(
        item for item in born if item.members == ("anchor", "good")
    )

    ecology.observe(_observation(1, ("anchor", "bad"), False))
    current_parent = ecology.sketches[parent.sketch_id]
    assert current_parent.state is SketchLifecycle.REFINING
    assert current_parent.residual_sketch_ids == (existing_residual.sketch_id,)
    assert ecology.last_refinement_ids == (existing_residual.sketch_id,)
    # No duplicate incarnation was created for the live strict superset.
    assert sum(
        item.members == existing_residual.members
        for item in ecology.sketches.values()
    ) == 1

    settled = ecology.settle_refinements()
    assert tuple(item.sketch_id for item in settled) == (parent.sketch_id,)
    assert ecology.sketches[parent.sketch_id].state is SketchLifecycle.DORMANT
    assert ecology.sketches[existing_residual.sketch_id].state is SketchLifecycle.ACTIVE


def test_local_promotion_gate_ignores_unbounded_prebirth_history(monkeypatch):
    """Only an explicit full audit may scan the complete REAL ledger."""

    ecology = ProspectiveBoundaryCandidateEcology()
    ecology.observe_many(
        _observation(index, ("unrelated",), True)
        for index in range(1001)
    )
    trigger = _observation(1001, ("anchor",), True)
    ecology.observe(trigger)
    candidate = ecology.expand(BoundaryExpandDemand(
        ordinal=1001,
        signal_ids=trigger.signal_ids,
        candidate_width=1,
        triggering_receipt_id=trigger.receipt_id,
        polarity=True,
    ))[0]
    ecology.observe_many(
        _observation(index, ("anchor",), True)
        for index in range(1002, 1005)
    )

    original_audit = ecology._full_promotion_audit
    calls = []

    def spy(candidate_to_audit):
        calls.append(candidate_to_audit.sketch_id)
        return original_audit(candidate_to_audit)

    monkeypatch.setattr(ecology, "_full_promotion_audit", spy)
    observations = ecology._observations

    class ValuesGuard(dict):
        def values(self):
            raise AssertionError("local promotion gate scanned the REAL ledger")

    monkeypatch.setattr(ecology, "_observations", ValuesGuard(observations))
    local = ecology.promotion_decision(candidate.sketch_id)
    assert local.eligible is True
    assert len(local.inspected_receipt_ids) == 4
    assert calls == []

    monkeypatch.setattr(ecology, "_observations", observations)
    audited = ecology.promotion_decision(
        candidate.sketch_id,
        full_audit=True,
    )
    assert audited.eligible is True
    assert len(audited.inspected_receipt_ids) == 4
    assert calls == [candidate.sketch_id]


def test_exhausted_refiner_stops_hot_path_and_bounds_long_contrast_cache():
    """A no-residual parent cannot scan or retain an unbounded contrast tail."""

    ecology = ProspectiveBoundaryCandidateEcology()
    trigger = _observation(0, ("anchor",), True)
    ecology.observe(trigger)
    parent = ecology.expand(BoundaryExpandDemand(
        ordinal=0,
        signal_ids=trigger.signal_ids,
        candidate_width=1,
        triggering_receipt_id=trigger.receipt_id,
        polarity=True,
    ))[0]
    # Fill the bounded positive cache, then demonstrate that the first
    # contradiction gets a refinement opportunity rather than immediate death.
    ecology.observe_many(
        _observation(index, ("anchor",), True)
        for index in range(1, 4)
    )
    ecology.observe(_observation(4, ("anchor",), False))
    assert ecology.sketches[parent.sketch_id].state is SketchLifecycle.REFINING
    assert ecology.active_sketch_count == 1

    # There are no locally visible residual signals.  More than one thousand
    # further contrasts must therefore reach a terminal tombstone at the
    # explicit refinement cap, after which the active scan is empty.
    ecology.observe_many(
        _observation(index, ("anchor",), False)
        for index in range(5, 1005)
    )
    stored = ecology.sketches[parent.sketch_id]
    assert stored.state is SketchLifecycle.DEAD
    assert stored.retirement_reason == "exhausted_refinement_budget"
    assert parent.sketch_id in ecology.tombstones
    assert ecology.active_sketch_count == 0
    assert len(stored.positive_receipt_ids) <= MAX_RETAINED_SUPPORT_RECEIPTS
    assert len(stored.negative_receipt_ids) <= MAX_RETAINED_CONTRADICTION_RECEIPTS
    assert len(stored.read_receipt_ids) <= MAX_RETAINED_READ_RECEIPTS
    assert len(stored.abstained_receipt_ids) <= MAX_RETAINED_REFINEMENT_RECEIPTS
    assert len(stored.refinement_receipt_ids) <= MAX_RETAINED_REFINEMENT_RECEIPTS

    # The complete REAL ledger still feeds certification, while the candidate
    # cache stays fixed-size and a late contrast cannot revive or promote it.
    decision = ecology.promotion_decision(parent.sketch_id)
    assert decision.eligible is False
    assert decision.reason == "lifecycle_dead"
    full_decision = ecology.promotion_decision(
        parent.sketch_id,
        full_audit=True,
    )
    assert full_decision.contradiction_count == 1001
    dead_snapshot = stored
    ecology.observe(_observation(1005, ("anchor",), False))
    assert ecology.sketches[parent.sketch_id] == dead_snapshot

    restored = ProspectiveBoundaryCandidateEcology.loads(ecology.dumps())
    assert restored.manifest() == ecology.manifest()


def test_retroactive_residual_failed_audit_reconciles_once(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A hidden pre-creation contrast cannot cause repeated prefix audits."""

    ecology = ProspectiveBoundaryCandidateEcology()
    first = _observation(0, ("anchor",), True)
    ecology.observe(first)
    parent = ecology.expand(BoundaryExpandDemand(
        ordinal=0,
        signal_ids=first.signal_ids,
        candidate_width=1,
        triggering_receipt_id=first.receipt_id,
        polarity=True,
    ))[0]
    ecology.observe(_observation(1, ("anchor", "residual"), True))
    # This contrast predates the residual's materialization.  It cannot
    # propose that residual itself because the separating signal is present.
    ecology.observe(_observation(2, ("anchor", "residual"), False))
    assert not ecology.last_refinement_ids
    ecology.observe(_observation(3, ("anchor", "residual"), True))
    # A later coarse-only contrast now creates a residual grounded at ordinal
    # one, behind the already accepted matching contrast at ordinal two.
    ecology.observe(_observation(4, ("anchor",), False))
    residual_id = next(
        candidate_id for candidate_id in ecology.last_refinement_ids
        if ecology.sketches[candidate_id].members
        == ("anchor", "residual")
    )
    for ordinal in range(5, 8):
        ecology.observe(
            _observation(ordinal, ("anchor", "residual"), True)
        )
    assert ecology.promotion_decision(residual_id).eligible is True

    original = ecology._full_promotion_audit
    audited: list[str] = []

    def counted(candidate):
        audited.append(candidate.sketch_id)
        return original(candidate)

    monkeypatch.setattr(ecology, "_full_promotion_audit", counted)
    decision = ecology.audit_promotion_at_safe_point(residual_id)
    assert decision.eligible is False
    assert decision.contradiction_count == 1
    reconciled = ecology.sketches[residual_id]
    assert reconciled.state is not SketchLifecycle.ACTIVE
    assert reconciled.lifetime_support_count == 5
    assert reconciled.lifetime_contradiction_count == 1
    assert audited == [residual_id]

    for ordinal in range(8, 136):
        ecology.observe(_observation(ordinal, ("unrelated",), True))
        retry = ecology.audit_promotion_at_safe_point(residual_id)
        assert retry.eligible is False
    assert audited == [residual_id]


def test_sequential_promotion_audits_are_bounded_by_live_tenure() -> None:
    """Certification work follows candidate tenure, not lifetime prefixes.

    For any stream the sum of live candidate tenures is bounded by
    ``active_sketch_cap * accepted_events``.  This sequential construction is
    deliberately hostile to prefix rescans: every new candidate is born late
    in an ever-growing ledger, but its exact promotion audit must inspect only
    its own four-event lifetime.
    """

    config = BoundaryEcologyConfig(
        max_candidates_per_demand=1,
        active_sketch_cap=4,
    )
    ecology = ProspectiveBoundaryCandidateEcology(config=config)
    total_inspected = 0
    total_tenure = 0
    accepted_events = 0

    for cycle in range(24):
        member = f"late-pattern-{cycle}"
        birth_ordinal = accepted_events
        trigger = _observation(birth_ordinal, (member,), True)
        ecology.observe(trigger)
        accepted_events += 1
        candidate = ecology.expand(BoundaryExpandDemand(
            ordinal=birth_ordinal,
            signal_ids=trigger.signal_ids,
            candidate_width=1,
            triggering_receipt_id=trigger.receipt_id,
            polarity=True,
        ))[0]
        for _ in range(3):
            ecology.observe(
                _observation(accepted_events, (member,), True)
            )
            accepted_events += 1

        decision = ecology.promotion_decision(
            candidate.sketch_id,
            full_audit=True,
        )
        assert decision.eligible is True
        assert decision.inspected_ordinal_interval == (
            birth_ordinal,
            accepted_events - 1,
        )
        assert len(decision.inspected_receipt_ids) == 4
        total_inspected += len(decision.inspected_receipt_ids)
        total_tenure += accepted_events - birth_ordinal
        ecology.mark_promoted(candidate.sketch_id)

    assert total_inspected == total_tenure == 24 * 4
    assert total_inspected <= config.active_sketch_cap * accepted_events
