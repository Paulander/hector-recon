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
    str(ROOT / "scripts/autogrowth/run_generic_core_support_directed_exploration_admitted.py")
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


def test_only_exploration_request_mode_varies_across_rent_arms() -> None:
    policy = EpisodicCompositionPolicy(
        ("action_a", "action_b"),
        random_seed=81,
        reservoir_config=ExperienceReservoirConfig(capacity=64),
    )
    configs = {}
    for arm in RUNNER["RENT_ARMS"]:
        clone = deepcopy(policy)
        RUNNER["_configure_arm"](clone, arm)
        config = clone.causal_rent_config
        assert config is not None
        configs[arm] = config

    assert {
        arm: config.exploration_request_mode
        for arm, config in configs.items()
    } == {
        "rent_batch_4_ranked": "ordinary_random",
        "rent_batch_4_support_directed": "support_directed",
        "rent_batch_4_support_shuffled": "support_shuffled",
    }
    assert {
        config.temporary_challenger_allowance for config in configs.values()
    } == {4}
    assert len({
        tuple(
            (name, value)
            for name, value in config.__dict__.items()
            if name != "exploration_request_mode"
        )
        for config in configs.values()
    }) == 1


def test_target_diagnostics_reconstruct_exact_four_post_hoc() -> None:
    task = _small_task()
    policy = EpisodicCompositionPolicy(
        task["all_action_ids"],
        random_seed=82,
        reservoir_config=ExperienceReservoirConfig(capacity=64),
    )
    RUNNER["_configure_arm"](policy, "rent_batch_4_support_directed")
    for action_id in task["door_action_ids"]:
        channel = policy.channels[action_id]
        for cue in (0, 1):
            members = tuple(sorted((
                task["door_cue_literals"][cue],
                task["regime_ids"][1],
            )))
            channel.learner.candidates.append(CompositeCandidate(
                members=members,
                born_observation=0,
                proposal_score=1.0,
                support_at_proposal=16,
                state="mature",
                shadow_weight=0.9,
            ))
        channel.sync_external_lifecycle()

    rows = RUNNER["_target_candidate_diagnostics"](policy, task)

    assert len(rows) == 4
    assert all(row["found"] for row in rows)
    assert all(row["mature"] for row in rows)
    assert len({
        (row["action_id"], tuple(row["members"])) for row in rows
    }) == 4


def test_admission_boundary_requires_all_three_conditions() -> None:
    passes = RUNNER["_passes_admission"]
    development = {"joint_success": 0.85}
    quiescence = {"post_trial_count": 0, "behavior_unchanged": True}

    assert passes(development, quiescence) is True
    assert passes({"joint_success": 0.849}, quiescence) is False
    assert passes(
        development, {"post_trial_count": 1, "behavior_unchanged": True}
    ) is False
    assert passes(
        development, {"post_trial_count": 0, "behavior_unchanged": False}
    ) is False


def test_committed_contract_matches_head() -> None:
    contract = ROOT / RUNNER["CONTRACT"]
    assert RUNNER["_head_file_matches"](ROOT, contract) is True


def test_fresh_admission_protocol_constants_are_frozen() -> None:
    assert RUNNER["CANDIDATE_SEEDS"] == tuple(range(20262201, 20262241))
    assert RUNNER["ADMITTED_COUNT"] == 20
    assert RUNNER["DEMANDS"] == (2,)
    assert RUNNER["ARMS"] == (
        "fixed_8_ranked",
        "rent_batch_4_ranked",
        "rent_batch_4_support_directed",
        "rent_batch_4_support_shuffled",
    )
