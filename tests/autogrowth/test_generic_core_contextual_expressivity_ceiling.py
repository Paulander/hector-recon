from __future__ import annotations

from pathlib import Path
import runpy

from recon_lite import (
    EpisodicCompositionPolicy,
    OnlineCompositionConfig,
)


ROOT = Path(__file__).resolve().parents[2]
RUNNER = ROOT / "scripts" / "autogrowth" / (
    "run_generic_core_contextual_expressivity_ceiling.py"
)
KEY_DOOR = ROOT / "scripts" / "autogrowth" / (
    "run_generic_core_multistate_key_door.py"
)


def _modules():
    return runpy.run_path(str(RUNNER)), runpy.run_path(str(KEY_DOOR))


def _policy_and_task():
    runner, key_door = _modules()
    task = key_door["_make_task"](303)
    policy = EpisodicCompositionPolicy(
        task["all_action_ids"],
        random_seed=9,
        composition_config=OnlineCompositionConfig(
            proposal_interval=100,
            max_total_proposals=64,
        ),
    )
    return runner, key_door, policy, task


def test_exhaustive_injection_is_content_blind_complete_and_idempotent() -> None:
    runner, _, policy, task = _policy_and_task()
    inject = runner["_inject_exhaustive_pairs"]

    assert inject(policy, task) == 8
    assert inject(policy, task) == 0
    expected = {
        tuple(sorted((cue, regime)))
        for cue in task["door_cue_literals"]
        for regime in task["regime_ids"]
    }
    for action_id in task["door_action_ids"]:
        actual = {
            tuple(sorted(candidate.members))
            for candidate in policy.channels[action_id].learner.candidates
            if candidate.state == "mature"
        }
        assert actual == expected
        assert all(
            candidate.shadow_weight == 0.0
            for candidate in policy.channels[action_id].learner.candidates
        )


def test_high_gain_exhaustive_arm_sets_only_frozen_ceiling_controls() -> None:
    runner, _, policy, task = _policy_and_task()
    inserted = runner["_configure_arm"](
        policy, task, "exhaustive_high_gain"
    )

    assert inserted == 8
    for action_id, channel in policy.channels.items():
        config = channel.learner.config
        assert config.residual_update_mode == "shared_frozen"
        assert (config.prediction_min, config.prediction_max) == (-4.0, 4.0)
        assert config.max_total_proposals == 64
        assert config.max_candidates == (
            8 if action_id in task["door_action_ids"] else 4
        )


def test_shared_hash_is_unchanged_by_phase1_learning() -> None:
    runner, key_door, policy, task = _policy_and_task()
    runner["_configure_arm"](policy, task, "exhaustive_bounded")
    before = runner["_shared_hash"](policy)
    responsibility = runpy.run_path(
        str(ROOT / "scripts" / "autogrowth" /
            "run_generic_core_responsibility_allocation.py")
    )
    responsibility["_train_episode"](
        policy,
        task,
        task["train_regime_1"][0],
        key_door["_door_observation"],
        key_door["_correct_actions"],
    )
    assert runner["_shared_hash"](policy) == before
