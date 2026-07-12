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


def test_adaptive_consolidation_requires_active_mature_evidence() -> None:
    learner = OnlinePairCompositionLearner(
        proposal_mode="residual_ranked",
        random_seed=1,
        config=OnlineCompositionConfig(
            proposal_interval=100,
            shared_learning_schedule="mature_activation_decay",
            adaptive_consolidation_activations=2,
        ),
    )
    learner.observe(("x",), 1.0)
    assert learner.mature_evidence_activation_count == 0
    assert learner.current_shared_learning_scale == 1.0

    learner.candidates.append(
        CompositeCandidate(
            members=("a", "b"),
            born_observation=0,
            proposal_score=1.0,
            support_at_proposal=16,
            state="mature",
        )
    )
    learner.observe(("x",), 1.0)
    assert learner.mature_evidence_activation_count == 0
    assert learner.current_shared_learning_scale == 1.0


def test_adaptive_consolidation_counts_once_and_reaches_floor() -> None:
    learner = OnlinePairCompositionLearner(
        proposal_mode="residual_ranked",
        random_seed=1,
        config=OnlineCompositionConfig(
            learning_rate=0.2,
            proposal_interval=100,
            shared_learning_schedule="mature_activation_decay",
            adaptive_shared_learning_floor=0.1,
            adaptive_consolidation_activations=2,
        ),
    )
    learner.candidates.extend([
        CompositeCandidate(
            members=("a", "b"),
            born_observation=0,
            proposal_score=1.0,
            support_at_proposal=16,
            state="mature",
        ),
        CompositeCandidate(
            members=("a", "c"),
            born_observation=0,
            proposal_score=1.0,
            support_at_proposal=16,
            state="mature",
        ),
    ])
    learner.observe(("a", "b", "c"), 1.0)
    assert learner.mature_evidence_activation_count == 1
    assert learner.current_shared_learning_scale == pytest.approx(0.55)
    assert learner.bias == pytest.approx(0.2 / 4 * 0.55)

    learner.observe(("a", "b", "c"), 1.0)
    assert learner.mature_evidence_activation_count == 2
    assert learner.current_shared_learning_scale == pytest.approx(0.1)
    learner.observe(("a", "b", "c"), 1.0)
    assert learner.mature_evidence_activation_count == 3
    assert learner.current_shared_learning_scale == pytest.approx(0.1)
    snapshot = learner.snapshot()
    assert snapshot["minimum_shared_learning_scale"] == pytest.approx(0.1)
    assert snapshot[
        "shared_learning_scale_observations_after_maturity"
    ] == 3
    assert snapshot[
        "mean_shared_learning_scale_after_maturity"
    ] == pytest.approx(0.25)


def test_adaptive_consolidation_leaves_candidate_updates_full_strength() -> None:
    learner = OnlinePairCompositionLearner(
        proposal_mode="residual_ranked",
        random_seed=1,
        config=OnlineCompositionConfig(
            learning_rate=0.2,
            proposal_interval=100,
            shared_learning_schedule="mature_activation_decay",
            adaptive_shared_learning_floor=0.1,
            adaptive_consolidation_activations=1,
        ),
    )
    mature = CompositeCandidate(
        members=("a", "b"),
        born_observation=0,
        proposal_score=1.0,
        support_at_proposal=16,
        state="mature",
    )
    trial = CompositeCandidate(
        members=("a", "c"),
        born_observation=0,
        proposal_score=1.0,
        support_at_proposal=16,
    )
    learner.candidates.extend((mature, trial))
    learner.observe(("a", "b", "c"), 1.0)

    assert learner.current_shared_learning_scale == pytest.approx(0.1)
    assert learner.bias == pytest.approx(0.2 / 4 * 0.1)
    assert mature.shadow_weight == pytest.approx(0.2)
    assert trial.shadow_weight == pytest.approx(0.2)
    assert learner.candidate_weight_updates_after_maturity == 2


def test_adaptive_consolidation_config_validation() -> None:
    with pytest.raises(ValueError, match="shared_learning_schedule"):
        OnlineCompositionConfig(shared_learning_schedule="unknown")
    with pytest.raises(ValueError, match="adaptive_shared_learning_floor"):
        OnlineCompositionConfig(adaptive_shared_learning_floor=-0.1)
    with pytest.raises(ValueError, match="adaptive_consolidation_activations"):
        OnlineCompositionConfig(adaptive_consolidation_activations=0)


def test_responsibility_allocation_conserves_one_residual_budget() -> None:
    learner = OnlinePairCompositionLearner(
        proposal_mode="residual_ranked",
        random_seed=3,
        config=OnlineCompositionConfig(
            learning_rate=0.2,
            proposal_interval=100,
            residual_update_mode="responsibility_conserving",
            allocation_importance_epsilon=0.01,
        ),
    )
    mature = CompositeCandidate(
        members=("a", "b"),
        born_observation=0,
        proposal_score=1.0,
        support_at_proposal=16,
        state="mature",
    )
    learner.candidates.append(mature)
    component_ids = ("bias_terminal", "a", "b", "composite_0")
    importance = {
        "bias_terminal": 1.0,
        "a": 2.0,
        "b": 3.0,
        "composite_0": 0.0,
    }
    learner.observe(
        ("a", "b"),
        1.0,
        decision_component_ids=component_ids,
        decision_component_importance=importance,
    )

    assert learner.allocation_update_count == 1
    assert learner.allocation_component_opportunity_count == 4
    assert learner.allocation_requested_l1_sum == pytest.approx(0.2)
    assert learner.allocation_max_budget_error <= 1e-12
    assert learner.allocation_missing_responsibility_count == 0
    assert learner.allocation_stale_component_count == 0
    assert mature.shadow_weight > learner.bias
    assert learner.component_importance["composite_0"] > 0.0


def test_shuffled_allocation_matches_budget_and_rng_not_mapping() -> None:
    common = dict(
        learning_rate=0.2,
        proposal_interval=100,
        allocation_importance_epsilon=0.01,
    )
    real = OnlinePairCompositionLearner(
        proposal_mode="residual_ranked",
        random_seed=17,
        config=OnlineCompositionConfig(
            **common,
            residual_update_mode="responsibility_conserving",
        ),
    )
    shuffled = OnlinePairCompositionLearner(
        proposal_mode="residual_ranked",
        random_seed=17,
        config=OnlineCompositionConfig(
            **common,
            residual_update_mode="responsibility_shuffled",
        ),
    )
    ids = ("bias_terminal", "a", "b", "c")
    importance = {
        "bias_terminal": 0.0,
        "a": 1.0,
        "b": 10.0,
        "c": 100.0,
    }
    for learner in (real, shuffled):
        learner.observe(
            ("a", "b", "c"),
            1.0,
            decision_component_ids=ids,
            decision_component_importance=importance,
        )

    assert real.allocation_requested_l1_sum == pytest.approx(
        shuffled.allocation_requested_l1_sum
    )
    assert real.allocation_component_opportunity_count == (
        shuffled.allocation_component_opportunity_count
    )
    assert real.allocation_rng_call_count == shuffled.allocation_rng_call_count
    assert real.allocation_max_budget_error <= 1e-12
    assert shuffled.allocation_max_budget_error <= 1e-12
    assert real.primitive_weights != shuffled.primitive_weights


def test_shared_frozen_updates_candidates_only() -> None:
    learner = OnlinePairCompositionLearner(
        proposal_mode="residual_ranked",
        random_seed=1,
        config=OnlineCompositionConfig(
            learning_rate=0.2,
            proposal_interval=100,
            residual_update_mode="shared_frozen",
        ),
    )
    mature = CompositeCandidate(
        members=("a", "b"),
        born_observation=0,
        proposal_score=1.0,
        support_at_proposal=16,
        state="mature",
    )
    trial = CompositeCandidate(
        members=("a", "c"),
        born_observation=0,
        proposal_score=1.0,
        support_at_proposal=16,
    )
    learner.candidates.extend((mature, trial))
    learner.primitive_weights = {"a": 0.1, "b": -0.1, "c": 0.05}
    before_shared = (learner.bias, dict(learner.primitive_weights))
    learner.observe(("a", "b", "c"), 1.0)

    assert (learner.bias, learner.primitive_weights) == before_shared
    assert mature.shadow_weight != 0.0
    assert trial.shadow_weight != 0.0


def test_residual_update_config_validation() -> None:
    with pytest.raises(ValueError, match="residual_update_mode"):
        OnlineCompositionConfig(residual_update_mode="unknown")
    with pytest.raises(ValueError, match="allocation_importance_epsilon"):
        OnlineCompositionConfig(allocation_importance_epsilon=0.0)
