from __future__ import annotations

from copy import deepcopy
from pathlib import Path
import runpy

from recon_lite import (
    CompositeCandidate,
    EpisodicCompositionPolicy,
    ExperienceReservoirConfig,
    OnlineCompositionConfig,
)


ROOT = Path(__file__).resolve().parents[2]
RUNNER = runpy.run_path(
    str(ROOT / "scripts/autogrowth/run_generic_core_challenger_throughput_dose.py")
)
KEY_DOOR = runpy.run_path(
    str(ROOT / "scripts/autogrowth/run_generic_core_multistate_key_door.py")
)


def _small_task() -> dict[str, object]:
    task = RUNNER["_prepare_task"](
        KEY_DOOR["_make_task"](
            20261801,
            development_evaluation_count=16,
        )
    )
    return RUNNER["_truncate_task"](
        task,
        train_count=32,
        development_count=16,
        evaluation_count=16,
    )


def test_matched_demand_changes_only_the_outcome_mapping() -> None:
    task = _small_task()
    rows = task["train_regime_1"]
    assert len(rows) == 32
    assert all("correct_door_index" not in row for row in rows)

    changed_at_m1 = set()
    for row in rows:
        m0 = RUNNER["_correct_actions"](task, row, 0)
        m1 = RUNNER["_correct_actions"](task, row, 1)
        m2 = RUNNER["_correct_actions"](task, row, 2)
        assert m0[0] == m1[0] == m2[0]
        assert m0[1] != m2[1]
        if m0[1] != m1[1]:
            changed_at_m1.add(int(row["door_cue_bit"]))

    assert changed_at_m1 == {task["m1_changed_cue_bit"]}
    assert RUNNER["_changed_cue_bits"](task, 0) == frozenset()
    assert len(RUNNER["_changed_cue_bits"](task, 1)) == 1
    assert RUNNER["_changed_cue_bits"](task, 2) == frozenset({0, 1})


def test_checkpoint_quiescence_removes_only_shadow_trials() -> None:
    task = _small_task()
    policy = EpisodicCompositionPolicy(
        task["all_action_ids"],
        random_seed=7,
        composition_config=OnlineCompositionConfig(proposal_interval=100),
        reservoir_config=ExperienceReservoirConfig(capacity=64),
    )
    action_id = task["door_action_ids"][0]
    channel = policy.channels[action_id]
    members = tuple(sorted((
        task["door_cue_literals"][0],
        task["regime_ids"][0],
    )))
    channel.learner.candidates.append(CompositeCandidate(
        members=members,
        born_observation=0,
        proposal_score=1.0,
        support_at_proposal=16,
        state="trial",
        shadow_weight=0.9,
    ))
    channel.sync_external_lifecycle()

    result = RUNNER["_quiesce_checkpoint"](policy, task)

    assert result["pre_trial_count"] == 1
    assert result["post_trial_count"] == 0
    assert result["behavior_unchanged"] is True
    assert channel.learner.candidates[0].state == "pruned"
    assert "composite_0" not in channel.graph.nodes


def test_capacity_configuration_is_identical_for_every_action_channel() -> None:
    task = _small_task()
    base = EpisodicCompositionPolicy(
        task["all_action_ids"],
        random_seed=8,
        reservoir_config=ExperienceReservoirConfig(capacity=64),
    )
    fixed = deepcopy(base)
    batch_4 = deepcopy(base)

    RUNNER["_configure_arm"](fixed, "fixed_8_ranked")
    RUNNER["_configure_arm"](batch_4, "rent_batch_4_ranked")

    assert {
        channel.learner.config.max_candidates
        for channel in fixed.channels.values()
    } == {8}
    assert {
        channel.learner.config.max_total_proposals
        for channel in fixed.channels.values()
    } == {64}
    assert all(
        channel.learner.config.residual_update_mode == "shared_frozen"
        for channel in fixed.channels.values()
    )
    assert batch_4.causal_rent_config is not None
    assert (
        batch_4.causal_rent_config.temporary_challenger_allowance == 4
    )
    assert batch_4.causal_rent_config.global_capacity == 32
    assert all(
        channel.learner.external_lifecycle
        for channel in batch_4.channels.values()
    )


def test_only_temporary_challenger_allowance_varies_across_ranked_doses() -> None:
    policy = EpisodicCompositionPolicy(
        ("action_a", "action_b"),
        random_seed=81,
        reservoir_config=ExperienceReservoirConfig(capacity=64),
    )
    configs = {}
    for arm in (
        "rent_batch_1_ranked",
        "rent_batch_2_ranked",
        "rent_batch_4_ranked",
    ):
        clone = deepcopy(policy)
        RUNNER["_configure_arm"](clone, arm)
        config = clone.causal_rent_config
        assert config is not None
        configs[arm] = config

    assert configs["rent_batch_1_ranked"].temporary_challenger_allowance == 1
    assert configs["rent_batch_2_ranked"].temporary_challenger_allowance == 2
    assert configs["rent_batch_4_ranked"].temporary_challenger_allowance == 4
    assert len({
        tuple(
            (name, value)
            for name, value in config.__dict__.items()
            if name != "temporary_challenger_allowance"
        )
        for config in configs.values()
    }) == 1


def test_common_experience_shadows_receive_identical_records() -> None:
    policy = EpisodicCompositionPolicy(
        ("action_a", "action_b"),
        random_seed=9,
        composition_config=OnlineCompositionConfig(
            proposal_interval=128,
            min_pair_support=16,
            max_total_proposals=64,
        ),
        reservoir_config=ExperienceReservoirConfig(capacity=64),
    )
    ranked = deepcopy(policy)
    shuffled = deepcopy(policy)
    RUNNER["_configure_arm"](ranked, "rent_batch_4_ranked")
    RUNNER["_configure_arm"](shuffled, "rent_batch_4_shuffled")
    stream = [
        {
            "terminal_return": 1.0 if index % 2 else -1.0,
            "decisions": [{
                "action_id": "action_a",
                "active_atom_ids": ("atom_x", "atom_y"),
                "legal_action_ids": ("action_a", "action_b"),
                "decision_scores": (
                    ("action_a", 0.0), ("action_b", 0.0)
                ),
                "elapsed_steps": 0,
            }],
        }
        for index in range(128)
    ]

    ranked_digest = RUNNER["_replay_reference_stream"](ranked, stream)
    shuffled_digest = RUNNER["_replay_reference_stream"](shuffled, stream)

    assert ranked_digest == shuffled_digest
    assert ranked.experience_reservoir is not None
    assert shuffled.experience_reservoir is not None
    assert ranked.experience_reservoir.snapshot()["records_sha256"] == (
        shuffled.experience_reservoir.snapshot()["records_sha256"]
    )
    assert ranked.causal_rent_proposal_opportunity_count == 1
    assert shuffled.causal_rent_proposal_opportunity_count == 1
