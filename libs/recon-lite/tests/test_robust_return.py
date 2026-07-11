from __future__ import annotations

import random

import pytest

from recon_lite import RobustReturnConfig, RobustReturnMemory


def test_rare_refutation_frozen_randomized_instances() -> None:
    """Mean and lower-tail objectives must disagree on every frozen instance."""

    config = RobustReturnConfig(
        capacity=32,
        lower_quantile=0.10,
        min_observations=8,
        confidence_prior=3.0,
    )
    for seed in range(20):
        rng = random.Random(20260712 + seed)
        identities = [f"anonymous_{seed}_a", f"anonymous_{seed}_b"]
        rng.shuffle(identities)
        refutable_id, consistent_id = identities
        refutable_returns = [1.0] * 7 + [-1.0]
        consistent_returns = [0.4] * 8
        rng.shuffle(refutable_returns)
        rng.shuffle(consistent_returns)

        memory = RobustReturnMemory(config)
        confidence_before_refutation = None
        for refutable, consistent in zip(
            refutable_returns, consistent_returns, strict=True
        ):
            if refutable < 0.0:
                confidence_before_refutation = memory.estimate(
                    refutable_id
                ).confidence
            memory.observe(refutable_id, refutable)
            memory.observe(consistent_id, consistent)

        refutable = memory.estimate(refutable_id)
        consistent = memory.estimate(consistent_id)
        assert confidence_before_refutation is not None
        assert confidence_before_refutation < 1.0
        assert refutable.mean > consistent.mean
        assert refutable.lower_quantile < consistent.lower_quantile
        assert memory.select(identities, objective="mean") == refutable_id
        assert memory.select(identities, objective="lower_tail") == consistent_id


def test_bounded_memory_retains_rare_low_tail_without_failure_labels() -> None:
    memory = RobustReturnMemory(
        RobustReturnConfig(capacity=8, lower_quantile=0.125)
    )
    memory.observe("anonymous_option", -1.0)
    for _ in range(100):
        memory.observe("anonymous_option", 1.0)

    estimate = memory.estimate("anonymous_option")
    assert estimate.observation_count == 101
    assert estimate.retained_count == 8
    assert estimate.minimum == -1.0
    assert estimate.lower_quantile == -1.0


def test_robust_return_snapshot_contains_only_ids_and_scalar_returns() -> None:
    memory = RobustReturnMemory()
    memory.observe("cell_7", 0.25)
    memory.observe("cell_7", -0.5)

    snapshot = memory.snapshot()
    assert snapshot["schema_version"] == "recon_robust_return.v1"
    assert snapshot["states"]["cell_7"]["returns"] == [0.25, -0.5]
    assert "stage" not in repr(snapshot).lower()
    assert "correct" not in repr(snapshot).lower()


@pytest.mark.parametrize("value", [float("nan"), float("inf")])
def test_robust_return_rejects_nonfinite_observations(value: float) -> None:
    memory = RobustReturnMemory()
    with pytest.raises(ValueError, match="observed return must be finite"):
        memory.observe("cell", value)
