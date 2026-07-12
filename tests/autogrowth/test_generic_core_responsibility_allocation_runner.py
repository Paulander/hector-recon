from __future__ import annotations

from copy import deepcopy
from pathlib import Path
import runpy

from recon_lite import (
    CompositeCandidate,
    EpisodicCompositionPolicy,
    OnlineCompositionConfig,
)


ROOT = Path(__file__).resolve().parents[2]
RUNNER = ROOT / "scripts" / "autogrowth" / (
    "run_generic_core_responsibility_allocation.py"
)
KEY_DOOR = ROOT / "scripts" / "autogrowth" / (
    "run_generic_core_multistate_key_door.py"
)


def _modules():
    return runpy.run_path(str(RUNNER)), runpy.run_path(str(KEY_DOOR))


def _policy() -> EpisodicCompositionPolicy:
    policy = EpisodicCompositionPolicy(
        ("a0", "a1"),
        random_seed=11,
        composition_config=OnlineCompositionConfig(proposal_interval=100),
    )
    channel = policy.channels["a0"]
    channel.learner.bias = 0.2
    channel.learner.primitive_weights = {"x": 0.3, "y": -0.1}
    channel.learner.candidates.append(
        CompositeCandidate(
            members=("x", "y"),
            born_observation=0,
            proposal_score=1.0,
            support_at_proposal=16,
            state="mature",
            shadow_weight=0.4,
        )
    )
    channel._sync_topology()
    channel._sync_weights()
    return policy


def test_development_pool_does_not_change_frozen_train_or_final_pools() -> None:
    _, key_door = _modules()
    make_task = key_door["_make_task"]
    legacy = make_task(101)
    extended = make_task(101, development_evaluation_count=32)

    for name in (
        "train_regime_0_sha256",
        "train_regime_1_sha256",
        "evaluation_regime_0_sha256",
        "evaluation_regime_1_sha256",
    ):
        assert extended[name] == legacy[name]
    assert len(legacy["development_evaluation_regime_0"]) == 0
    assert len(extended["development_evaluation_regime_0"]) == 32


def test_complete_checkpoint_hash_survives_deep_clone() -> None:
    runner, _ = _modules()
    complete = runner["_complete_policy_state"]
    hash_json = runner["_hash_json"]
    policy = _policy()
    clone = deepcopy(policy)

    assert hash_json(complete(clone)) == hash_json(complete(policy))
    assert complete(policy)["policy_rng_state"]
    assert complete(policy)["complete_channel_state"]["a0"][
        "learner_rng_state"
    ]


def test_arm_configuration_changes_only_frozen_config() -> None:
    runner, _ = _modules()
    complete = runner["_complete_policy_state"]
    configure = runner["_configure_arm"]
    policy = _policy()
    before = complete(policy)
    configure(policy, "responsibility")
    after = complete(policy)

    assert policy.channels["a0"].learner.config.residual_update_mode == (
        "responsibility_conserving"
    )
    assert before["channels"]["a0"]["learner"]["bias"] == (
        after["channels"]["a0"]["learner"]["bias"]
    )
    assert before["channels"]["a0"]["learner"]["candidates"] == (
        after["channels"]["a0"]["learner"]["candidates"]
    )


def test_swap_shared_preserves_target_contextual_weights() -> None:
    runner, _ = _modules()
    swap_shared = runner["_swap_shared"]
    target = _policy()
    source = _policy()
    source.channels["a0"].learner.bias = -0.7
    source.channels["a0"].learner.primitive_weights["x"] = -0.6
    contextual_before = target.channels["a0"].learner.candidates[
        0
    ].shadow_weight

    swap_shared(target, source)

    assert target.channels["a0"].learner.bias == -0.7
    assert target.channels["a0"].learner.primitive_weights["x"] == -0.6
    assert target.channels["a0"].learner.candidates[
        0
    ].shadow_weight == contextual_before


def test_standard_budget_allows_different_action_distributions() -> None:
    runner, _ = _modules()
    same_budget = runner["_same_standard_budget"]
    arms = {}
    for index, arm in enumerate(runner["ARMS"]):
        arms[arm] = {
            "training_episode_count": 8192,
            "standard_evaluation_episode_count": 3072,
            "selection_count": {
                "left": 8000 + index,
                "right": 8384 - index,
            },
            "rng_call_count": 49152,
        }
    assert same_budget({"arms": arms})
    arms["shuffled"]["selection_count"]["left"] += 1
    assert not same_budget({"arms": arms})
