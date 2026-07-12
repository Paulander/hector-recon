from __future__ import annotations

from pathlib import Path
import runpy

from recon_lite import EpisodicCompositionPolicy, OnlineCompositionConfig


ROOT = Path(__file__).resolve().parents[2]
RUNNER = ROOT / "scripts" / "autogrowth" / (
    "run_generic_core_self_grown_coverage.py"
)
KEY_DOOR = ROOT / "scripts" / "autogrowth" / (
    "run_generic_core_multistate_key_door.py"
)


def test_eight_ranked_and_random_match_capacity_not_nomination() -> None:
    runner = runpy.run_path(str(RUNNER))
    key_door = runpy.run_path(str(KEY_DOOR))
    task = key_door["_make_task"](404)
    policies = {}
    for arm in ("eight_ranked", "eight_random"):
        policy = EpisodicCompositionPolicy(
            task["all_action_ids"],
            random_seed=7,
            composition_config=OnlineCompositionConfig(
                max_total_proposals=64
            ),
        )
        runner["_configure_arm"](policy, task, arm)
        policies[arm] = policy

    for action_id in task["door_action_ids"]:
        ranked = policies["eight_ranked"].channels[action_id].learner
        random = policies["eight_random"].channels[action_id].learner
        assert ranked.config == random.config
        assert ranked.config.max_candidates == 8
        assert ranked.proposal_mode == "residual_ranked"
        assert random.proposal_mode == "matched_random"
    for policy in policies.values():
        for action_id in task["key_action_ids"]:
            learner = policy.channels[action_id].learner
            assert learner.config.max_candidates == 4
            assert learner.proposal_mode == "residual_ranked"
