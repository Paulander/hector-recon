from __future__ import annotations

import pytest

from recon_lite import (
    GraphBackedRobustActionPolicy,
    RobustActionPolicyConfig,
    RobustReturnConfig,
)


def _policy(objective: str) -> GraphBackedRobustActionPolicy:
    return GraphBackedRobustActionPolicy(
        ("anonymous_a", "anonymous_b"),
        objective=objective,
        random_seed=7,
        config=RobustActionPolicyConfig(exploration_rate=0.15),
        return_config=RobustReturnConfig(
            capacity=256,
            lower_quantile=0.10,
            min_observations=8,
            confidence_prior=3.0,
        ),
    )


def test_graph_score_equals_selected_memory_statistic() -> None:
    policy = _policy("lower_tail")
    for value in (1.0,) * 7 + (-1.0,):
        policy.observe("anonymous_a", value)
    for _ in range(8):
        policy.observe("anonymous_b", 0.4)

    assert policy.score("anonymous_a") == pytest.approx(
        policy.memory.estimate("anonymous_a").robust_score
    )
    assert policy.score("anonymous_b") == pytest.approx(
        policy.memory.estimate("anonymous_b").robust_score
    )
    assert policy.graph_prediction_mismatch_count == 0


def test_mean_and_lower_tail_change_live_graph_choice() -> None:
    mean_policy = _policy("mean")
    tail_policy = _policy("lower_tail")
    for policy in (mean_policy, tail_policy):
        for value in (1.0,) * 7 + (-1.0,):
            policy.observe("anonymous_a", value)
        for _ in range(8):
            policy.observe("anonymous_b", 0.4)

    assert mean_policy.greedy_action() == "anonymous_a"
    assert tail_policy.greedy_action() == "anonymous_b"
    assert mean_policy.graph_prediction_mismatch_count == 0
    assert tail_policy.graph_prediction_mismatch_count == 0


def test_exploration_uses_constant_rng_call_budget() -> None:
    mean_policy = _policy("mean")
    tail_policy = _policy("lower_tail")
    for _ in range(10):
        mean_policy.choose(explore=True)
        tail_policy.choose(explore=True)

    assert mean_policy.rng_call_count == tail_policy.rng_call_count == 30
