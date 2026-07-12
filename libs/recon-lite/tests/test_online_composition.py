from __future__ import annotations

import math

import pytest

from recon_lite import (
    CompositeCandidate,
    OnlineCompositionConfig,
    OnlinePairCompositionLearner,
)


def test_trial_candidate_is_shadow_only_until_mature() -> None:
    learner = OnlinePairCompositionLearner(
        proposal_mode="residual_ranked",
        random_seed=7,
        config=OnlineCompositionConfig(proposal_interval=100),
    )
    learner.primitive_weights = {"a": 0.2, "b": -0.1}
    trial = CompositeCandidate(
        members=("a", "b"),
        born_observation=0,
        proposal_score=1.0,
        support_at_proposal=16,
        shadow_weight=0.75,
    )
    learner.candidates.append(trial)

    assert learner.predict(("a", "b")) == pytest.approx(0.1)
    trial.state = "mature"
    assert learner.predict(("a", "b")) == pytest.approx(0.85)


def test_future_paired_error_controls_lifecycle() -> None:
    config = OnlineCompositionConfig(
        learning_rate=0.5,
        proposal_interval=100,
        burn_in_activations=1,
        confirmation_activations=3,
        causal_margin=0.01,
        resource_cost=0.002,
    )
    learner = OnlinePairCompositionLearner(
        proposal_mode="residual_ranked", random_seed=7, config=config
    )
    useful = CompositeCandidate(
        members=("a", "b"),
        born_observation=0,
        proposal_score=1.0,
        support_at_proposal=16,
    )
    learner.candidates.append(useful)
    for _ in range(4):
        learner.observe(("a", "b"), 1.0)

    assert useful.state == "mature"
    assert useful.confirmation_count == 3
    assert useful.paired_improvement is not None
    assert useful.paired_improvement > config.causal_margin + config.resource_cost


def test_trial_expires_without_enough_active_confirmations() -> None:
    learner = OnlinePairCompositionLearner(
        proposal_mode="residual_ranked",
        random_seed=7,
        config=OnlineCompositionConfig(
            proposal_interval=100,
            trial_max_age=3,
        ),
    )
    trial = CompositeCandidate(
        members=("a", "b"),
        born_observation=0,
        proposal_score=1.0,
        support_at_proposal=16,
    )
    learner.candidates.append(trial)
    for _ in range(3):
        learner.observe(("x",), 0.0)
    assert trial.state == "pruned"
    assert trial.confirmation_count == 0


def test_ranked_and_random_arms_share_candidate_budget() -> None:
    config = OnlineCompositionConfig(
        proposal_interval=4,
        min_pair_support=1,
        max_candidates=3,
        trial_max_age=100,
    )
    ranked = OnlinePairCompositionLearner(
        proposal_mode="residual_ranked", random_seed=11, config=config
    )
    random_arm = OnlinePairCompositionLearner(
        proposal_mode="matched_random", random_seed=13, config=config
    )
    stream = [
        (("a", "b", "c"), 1.0),
        (("a", "b", "d"), -1.0),
        (("a", "c", "d"), 1.0),
        (("b", "c", "d"), -1.0),
    ] * 4
    for atoms, target in stream:
        assert math.isfinite(ranked.observe(atoms, target))
        assert math.isfinite(random_arm.observe(atoms, target))

    assert len(ranked.candidates) == len(random_arm.candidates) == 3
    assert all(candidate.support_at_proposal >= 1 for candidate in ranked.candidates)
    assert all(candidate.support_at_proposal >= 1 for candidate in random_arm.candidates)


def test_nonfinite_target_is_rejected() -> None:
    learner = OnlinePairCompositionLearner(
        proposal_mode="residual_ranked", random_seed=1
    )
    with pytest.raises(ValueError):
        learner.observe(("a",), float("nan"))


def test_pruned_candidate_releases_live_slot_with_bounded_lifetime() -> None:
    config = OnlineCompositionConfig(
        proposal_interval=1,
        min_pair_support=1,
        max_candidates=1,
        max_total_proposals=3,
    )
    learner = OnlinePairCompositionLearner(
        proposal_mode="residual_ranked", random_seed=1, config=config
    )
    learner.observe(("a", "b"), 1.0)
    assert len(learner.candidates) == 1
    learner.candidates[0].state = "pruned"

    learner.observe(("a", "c"), 1.0)
    assert len(learner.candidates) == 2
    learner.candidates[1].state = "mature"
    learner.observe(("b", "c"), 1.0)
    assert len(learner.candidates) == 2

    learner.candidates[1].state = "pruned"
    learner.observe(("b", "c"), 1.0)
    assert len(learner.candidates) == 3
    learner.candidates[2].state = "pruned"
    learner.observe(("d", "e"), 1.0)
    assert len(learner.candidates) == 3
    snapshot = learner.snapshot()
    assert snapshot["live_candidate_count"] == 0
    assert snapshot["candidate_state_counts"]["pruned"] == 3
    assert snapshot["total_proposal_limit"] == 3


def test_legacy_default_remains_lifetime_candidate_cap() -> None:
    config = OnlineCompositionConfig(
        proposal_interval=1,
        min_pair_support=1,
        max_candidates=1,
    )
    learner = OnlinePairCompositionLearner(
        proposal_mode="residual_ranked", random_seed=1, config=config
    )
    learner.observe(("a", "b"), 1.0)
    learner.candidates[0].state = "pruned"
    learner.observe(("a", "c"), 1.0)
    assert len(learner.candidates) == 1
    assert learner.snapshot()["total_proposal_limit"] == 1


def test_consolidation_freezes_shared_but_not_mature_candidate_weight() -> None:
    learner = OnlinePairCompositionLearner(
        proposal_mode="residual_ranked",
        random_seed=1,
        config=OnlineCompositionConfig(
            proposal_interval=100,
            shared_learning_after_maturity_scale=0.0,
        ),
    )
    mature = CompositeCandidate(
        members=("a", "b"),
        born_observation=0,
        proposal_score=1.0,
        support_at_proposal=16,
        state="mature",
        shadow_weight=0.25,
    )
    learner.candidates.append(mature)
    learner.primitive_weights = {"a": 0.1, "b": -0.1}
    bias_before = learner.bias
    primitive_before = dict(learner.primitive_weights)
    candidate_before = mature.shadow_weight
    learner.observe(("a", "b"), 1.0)

    assert learner.bias == bias_before
    assert learner.primitive_weights == primitive_before
    assert mature.shadow_weight != candidate_before
    assert learner.first_maturity_observation == 1
    assert learner.shared_update_events_after_maturity == 0
    assert learner.candidate_weight_updates_after_maturity > 0


def test_default_keeps_shared_weights_plastic_after_maturity() -> None:
    learner = OnlinePairCompositionLearner(
        proposal_mode="residual_ranked",
        random_seed=1,
        config=OnlineCompositionConfig(proposal_interval=100),
    )
    learner.candidates.append(
        CompositeCandidate(
            members=("a", "b"),
            born_observation=0,
            proposal_score=1.0,
            support_at_proposal=16,
            state="mature",
        )
    )
    learner.observe(("a", "b"), 1.0)
    assert learner.bias != 0.0
    assert learner.shared_update_events_after_maturity == 1


def test_consolidated_channel_can_still_propose_new_trial() -> None:
    learner = OnlinePairCompositionLearner(
        proposal_mode="residual_ranked",
        random_seed=1,
        config=OnlineCompositionConfig(
            proposal_interval=1,
            min_pair_support=1,
            max_candidates=2,
            max_total_proposals=3,
            shared_learning_after_maturity_scale=0.0,
        ),
    )
    learner.candidates.append(
        CompositeCandidate(
            members=("x", "y"),
            born_observation=0,
            proposal_score=1.0,
            support_at_proposal=16,
            state="mature",
        )
    )
    learner.observe(("a", "b"), 1.0)
    assert len(learner.candidates) == 2
    assert learner.candidates[1].state == "trial"
    assert learner.shared_update_events_after_maturity == 0
