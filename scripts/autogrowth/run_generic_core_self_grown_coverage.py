#!/usr/bin/env python3
"""Run the frozen self-grown contextual coverage experiment."""

from __future__ import annotations

import argparse
from copy import deepcopy
from dataclasses import asdict, replace
import hashlib
import json
from pathlib import Path
import runpy
import statistics

from recon_lite import (
    EpisodicCompositionConfig,
    EpisodicCompositionPolicy,
    OnlineCompositionConfig,
)


DEFAULT_OUTPUT = Path(
    "reports/autogrowth/generic_core/"
    "self_grown_contextual_coverage_20260712.json"
)
SEEDS = tuple(range(20261801, 20261821))
ARMS = (
    "four_ranked",
    "eight_ranked",
    "eight_random",
)
CHECKPOINTS = (512, 1024, 2048, 4096)
DEVELOPMENT_COUNT = 512
RESPONSIBILITY_RUNNER = Path(__file__).with_name(
    "run_generic_core_responsibility_allocation.py"
)
KEY_DOOR_RUNNER = Path(__file__).with_name(
    "run_generic_core_multistate_key_door.py"
)
RENEWABLE_RUNNER = Path(__file__).with_name(
    "run_generic_core_renewable_topology.py"
)
CONSOLIDATION_RUNNER = Path(__file__).with_name(
    "run_generic_core_local_consolidation.py"
)
DOSE_RUNNER = Path(__file__).with_name(
    "run_generic_core_consolidation_dose.py"
)


def _shared_state(policy: EpisodicCompositionPolicy) -> dict[str, object]:
    return {
        action_id: {
            "bias": policy.channels[action_id].learner.bias,
            "primitive_weights": dict(sorted(
                policy.channels[action_id].learner.primitive_weights.items()
            )),
        }
        for action_id in policy.action_ids
    }


def _shared_hash(policy: EpisodicCompositionPolicy) -> str:
    encoded = json.dumps(
        _shared_state(policy),
        sort_keys=True,
        separators=(",", ":"),
    ).encode()
    return hashlib.sha256(encoded).hexdigest()


def _configure_arm(
    policy: EpisodicCompositionPolicy,
    task: dict[str, object],
    arm: str,
) -> None:
    expanded = arm != "four_ranked"
    random_control = arm == "eight_random"
    for action_id, channel in policy.channels.items():
        is_door = action_id in task["door_action_ids"]
        channel.learner.config = replace(
            channel.learner.config,
            residual_update_mode="shared_frozen",
            prediction_min=-1.0,
            prediction_max=1.0,
            max_candidates=8 if expanded and is_door else 4,
            max_total_proposals=64,
        )
        if is_door:
            channel.learner.proposal_mode = (
                "matched_random" if random_control else "residual_ranked"
            )


def _same_budget(row: dict[str, object]) -> bool:
    return len({
        (
            row["arms"][arm]["training_episode_count"],
            row["arms"][arm]["standard_evaluation_episode_count"],
            sum(row["arms"][arm]["selection_count"].values()),
            row["arms"][arm]["rng_call_count"],
        )
        for arm in ARMS
    }) == 1


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    partial = args.output.with_suffix(".partial.json")
    repo_root = Path(__file__).resolve().parents[2]
    responsibility = runpy.run_path(str(RESPONSIBILITY_RUNNER))
    key_door = runpy.run_path(str(KEY_DOOR_RUNNER))
    renewable = runpy.run_path(str(RENEWABLE_RUNNER))
    consolidation = runpy.run_path(str(CONSOLIDATION_RUNNER))
    dose = runpy.run_path(str(DOSE_RUNNER))
    complete_state = responsibility["_complete_policy_state"]
    hash_json = responsibility["_hash_json"]
    write_json = responsibility["_write_json"]
    train_episode = responsibility["_train_episode"]
    evaluate = responsibility["_evaluate"]
    candidate_ablations = responsibility["_individual_candidate_ablations"]
    coverage = responsibility["_coverage"]
    score_diagnostics = responsibility["_score_diagnostics"]
    make_task = key_door["_make_task"]
    door_observation = key_door["_door_observation"]
    correct_actions = key_door["_correct_actions"]
    arm_result = key_door["_arm_result"]
    enrich_arm = renewable["_enrich_arm"]
    add_consolidation_metrics = consolidation[
        "_add_consolidation_metrics"
    ]
    file_hash = dose["_file_hash"]
    git_commit = dose["_git_commit"]
    task_manifest = dose["_task_manifest"]
    policy_config = EpisodicCompositionConfig(
        exploration_rate=0.15,
        discount=0.97,
    )
    phase0_config = OnlineCompositionConfig(max_total_proposals=64)
    phase0_rows = []
    work = []
    for index, seed in enumerate(SEEDS, start=1):
        task = make_task(
            seed,
            development_evaluation_count=DEVELOPMENT_COUNT,
        )
        policy = EpisodicCompositionPolicy(
            task["all_action_ids"],
            random_seed=seed + 11_000_000,
            config=policy_config,
            composition_config=phase0_config,
        )
        for row in task["train_regime_0"]:
            train_episode(
                policy, task, row, door_observation, correct_actions
            )
        development = evaluate(
            policy,
            task,
            task["development_evaluation_regime_0"],
            door_observation,
            correct_actions,
        )
        state = complete_state(policy)
        checkpoint_hash = hash_json(state)
        phase0_rows.append({
            "seed": seed,
            **task_manifest(task),
            "development_evaluation_regime_0_sha256": task[
                "development_evaluation_regime_0_sha256"
            ],
            "phase0_development": development,
            "phase0_checkpoint_sha256": checkpoint_hash,
            "phase0_checkpoint_state": state,
        })
        work.append((task, policy, checkpoint_hash))
        write_json(partial, {
            "status": "phase0_in_progress",
            "phase0_rows": phase0_rows,
        })
        print(f"completed phase0 task {index}/{len(SEEDS)}", flush=True)

    mastery = all(
        row["phase0_development"]["joint_success"] >= 0.85
        for row in phase0_rows
    )
    if not mastery:
        payload = {
            "schema_version": "recon_contextual_expressivity_ceiling_raw.v1",
            "status": "phase0_mastery_failed",
            "source_commit": git_commit(repo_root),
            "phase0_rows": phase0_rows,
            "phase0_rows_sha256": hash_json(phase0_rows),
            "runner_sha256": file_hash(Path(__file__)),
        }
        write_json(args.output, payload)
        partial.unlink(missing_ok=True)
        print(args.output)
        print(json.dumps({"phase0_mastery_pass": False}, sort_keys=True))
        return 0

    task_rows = []
    for task_index, (task, phase0_policy, checkpoint_hash) in enumerate(
        work, start=1
    ):
        clones = {arm: deepcopy(phase0_policy) for arm in ARMS}
        clone_hashes = {
            arm: hash_json(complete_state(policy))
            for arm, policy in clones.items()
        }
        clone_parity = all(
            value == checkpoint_hash for value in clone_hashes.values()
        )
        arm_rows = {}
        for arm, policy in clones.items():
            _configure_arm(policy, task, arm)
            shared_before = _shared_hash(policy)
            action_digest = hashlib.sha256()
            observation_digest = hashlib.sha256()
            trajectory = []
            for episode, row in enumerate(task["train_regime_1"], start=1):
                key_action, door_action, door_atoms = train_episode(
                    policy, task, row, door_observation, correct_actions
                )
                action_digest.update(
                    f"{key_action}|{door_action}\n".encode()
                )
                observation_digest.update(
                    ("|".join(door_atoms) + "\n").encode()
                )
                if episode in CHECKPOINTS:
                    trajectory.append({
                        "phase1_episode": episode,
                        "old_development": evaluate(
                            policy,
                            task,
                            task["development_evaluation_regime_0"],
                            door_observation,
                            correct_actions,
                        ),
                    })
            base = add_consolidation_metrics(
                enrich_arm(
                    arm_result(
                        policy,
                        task,
                        clear_at_transition=False,
                    ),
                    policy,
                    task,
                ),
                policy,
            )
            base.update({
                "shared_state_sha256_before": shared_before,
                "shared_state_sha256_after": _shared_hash(policy),
                "shared_state_unchanged": (
                    shared_before == _shared_hash(policy)
                ),
                "standard_evaluation_episode_count": (
                    len(CHECKPOINTS) * DEVELOPMENT_COUNT + 1024
                ),
                "phase1_action_sequence_sha256": action_digest.hexdigest(),
                "phase1_action_conditioned_observation_sha256": (
                    observation_digest.hexdigest()
                ),
                "old_development_trajectory": trajectory,
                "candidate_ablations": candidate_ablations(
                    policy,
                    task,
                    base["evaluations"],
                    door_observation,
                    correct_actions,
                ),
                "contextual_coverage": coverage(policy, task),
                "score_diagnostics": score_diagnostics(
                    policy, task, door_observation
                ),
                "parameter_clip_counts": {
                    kind: sum(
                        channel.learner.parameter_clip_counts[kind]
                        for channel in policy.channels.values()
                    )
                    for kind in ("bias", "primitive", "trial", "mature")
                },
            })
            arm_rows[arm] = base
        task_rows.append({
            "seed": task["seed"],
            "phase0_checkpoint_sha256": checkpoint_hash,
            "clone_hashes": clone_hashes,
            "clone_parity": clone_parity,
            "phase0_development": next(
                row["phase0_development"]
                for row in phase0_rows
                if row["seed"] == task["seed"]
            ),
            "arms": arm_rows,
        })
        write_json(partial, {
            "status": "phase1_in_progress",
            "phase0_rows_sha256": hash_json(phase0_rows),
            "task_rows": task_rows,
        })
        print(f"completed phase1 task {task_index}/{len(SEEDS)}", flush=True)

    arm_summaries = {}
    for arm in ARMS:
        old_values = [
            row["arms"][arm]["evaluations"]["regime_0"]["full_graph"][
                "joint_success"
            ]
            for row in task_rows
        ]
        new_values = [
            row["arms"][arm]["evaluations"]["regime_1"]["full_graph"][
                "joint_success"
            ]
            for row in task_rows
        ]
        old_drops = [
            row["phase0_development"]["joint_success"] - old
            for row, old in zip(task_rows, old_values)
        ]
        summary = {
            "median_joint_regime_0": statistics.median(old_values),
            "median_joint_regime_1": statistics.median(new_values),
            "both_at_least_0_85_task_count": sum(
                min(old, new) >= 0.85
                for old, new in zip(old_values, new_values)
            ),
            "median_old_drop": statistics.median(old_drops),
            "median_old_composite_effect": statistics.median(
                row["arms"][arm]["evaluations"]["regime_0"][
                    "joint_ablation_drop"
                ]
                for row in task_rows
            ),
            "median_new_composite_effect": statistics.median(
                row["arms"][arm]["evaluations"]["regime_1"][
                    "joint_ablation_drop"
                ]
                for row in task_rows
            ),
            "shared_unchanged_task_count": sum(
                row["arms"][arm]["shared_state_unchanged"]
                for row in task_rows
            ),
            "median_contextual_coverage": statistics.median(
                row["arms"][arm]["contextual_coverage"]["coverage"]
                for row in task_rows
            ),
            "median_total_proposals": statistics.median(
                sum(
                    channel["total_proposal_count"]
                    for channel in row["arms"][arm]["channels"].values()
                )
                for row in task_rows
            ),
        }
        summary["coexistence_pass"] = all((
            summary["median_joint_regime_0"] >= 0.85,
            summary["median_joint_regime_1"] >= 0.85,
            summary["both_at_least_0_85_task_count"] >= 16,
            summary["median_old_drop"] <= 0.05,
            summary["median_old_composite_effect"] >= 0.10,
            summary["median_new_composite_effect"] >= 0.10,
            summary["shared_unchanged_task_count"] == len(task_rows),
        ))
        arm_summaries[arm] = summary

    max_total = max(
        channel["total_proposal_count"]
        for row in task_rows
        for arm in ARMS
        for channel in row["arms"][arm]["channels"].values()
    )
    max_sparse_live = max(
        channel["max_observed_live_candidate_count"]
        for row in task_rows
        for arm in ("four_ranked",)
        for channel in row["arms"][arm]["channels"].values()
    )
    max_eight_door_live = max(
        channel["final_live_candidate_count"]
        for row in task_rows
        for arm in ("eight_ranked", "eight_random")
        for action_id, channel in row["arms"][arm]["channels"].items()
        if action_id in next(
            item for item in phase0_rows if item["seed"] == row["seed"]
        )["door_action_ids"]
    )
    mismatch = sum(
        row["arms"][arm]["selection_update_mismatch_count"]
        + sum(
            channel["graph_prediction_mismatch_count"]
            for channel in row["arms"][arm]["channels"].values()
        )
        for row in task_rows
        for arm in ARMS
    )
    trial_edges = sum(
        channel["trial_root_edge_count"]
        for row in task_rows
        for arm in ARMS
        for channel in row["arms"][arm]["channels"].values()
    )
    invariants = {
        "clone_parity_task_count": sum(
            row["clone_parity"] for row in task_rows
        ),
        "identical_standard_budget_task_count": sum(
            _same_budget(row) for row in task_rows
        ),
        "maximum_total_proposals_observed": max_total,
        "maximum_sparse_live_candidates_observed": max_sparse_live,
        "maximum_eight_door_live_candidates_observed": (
            max_eight_door_live
        ),
        "total_graph_or_update_mismatch_count": mismatch,
        "total_trial_root_edge_count": trial_edges,
        "task_count": len(task_rows),
    }
    invariants_pass = all((
        invariants["clone_parity_task_count"] == len(task_rows),
        invariants["identical_standard_budget_task_count"] == len(task_rows),
        max_total <= 64,
        max_sparse_live <= 4,
        max_eight_door_live <= 8,
        mismatch == 0,
        trial_edges == 0,
    ))
    def minimum_score(row: dict[str, object], arm: str) -> float:
        return min(
            row["arms"][arm]["evaluations"]["regime_0"]["full_graph"][
                "joint_success"
            ],
            row["arms"][arm]["evaluations"]["regime_1"]["full_graph"][
                "joint_success"
            ],
        )

    ranked_over_four = [
        minimum_score(row, "eight_ranked")
        - minimum_score(row, "four_ranked")
        for row in task_rows
    ]
    ranked_over_random = [
        minimum_score(row, "eight_ranked")
        - minimum_score(row, "eight_random")
        for row in task_rows
    ]
    development_support = all((
        arm_summaries["eight_ranked"]["coexistence_pass"],
        sum(value > 0.0 for value in ranked_over_four) >= 14,
        sum(value > 0.0 for value in ranked_over_random) >= 14,
        statistics.median(ranked_over_random) >= 0.10,
        arm_summaries["eight_ranked"]["median_contextual_coverage"]
        > arm_summaries["four_ranked"]["median_contextual_coverage"],
        arm_summaries["eight_ranked"]["median_contextual_coverage"]
        > arm_summaries["eight_random"]["median_contextual_coverage"],
        arm_summaries["eight_ranked"]["median_contextual_coverage"] >= 0.75,
        invariants_pass,
    ))
    payload = {
        "schema_version": "recon_self_grown_coverage_raw.v1",
        "status": "complete",
        "track": "generic_core_development",
        "confirmation_claimed": False,
        "autonomous_nomination_claimed": development_support,
        "source_commit": git_commit(repo_root),
        "frozen_contract": (
            "docs/autogrowth/"
            "GENERIC_CORE_SELF_GROWN_COVERAGE_WORK_PACKAGE_20260712.md"
        ),
        "policy_config": asdict(policy_config),
        "phase0_composition_config": asdict(phase0_config),
        "frozen_seed_range": [SEEDS[0], SEEDS[-1]],
        "phase0_rows": phase0_rows,
        "phase0_rows_sha256": hash_json(phase0_rows),
        "task_rows": task_rows,
        "task_rows_sha256": hash_json(task_rows),
        "arm_summaries": arm_summaries,
        "ranked_over_four_task_count": sum(
            value > 0.0 for value in ranked_over_four
        ),
        "ranked_over_random_task_count": sum(
            value > 0.0 for value in ranked_over_random
        ),
        "median_ranked_advantage_over_random": statistics.median(
            ranked_over_random
        ),
        "development_support": development_support,
        "invariants": invariants,
        "invariants_pass": invariants_pass,
        "composition_implementation_sha256": file_hash(
            repo_root / "libs/recon-lite/src/recon_lite/online_composition.py"
        ),
        "episodic_implementation_sha256": file_hash(
            repo_root / "libs/recon-lite/src/recon_lite/episodic_composition.py"
        ),
        "responsibility_runner_sha256": file_hash(RESPONSIBILITY_RUNNER),
        "key_door_runner_sha256": file_hash(KEY_DOOR_RUNNER),
        "runner_sha256": file_hash(Path(__file__)),
    }
    write_json(args.output, payload)
    partial.unlink(missing_ok=True)
    print(args.output)
    print(json.dumps({
        "arm_summaries": arm_summaries,
        "invariants": invariants,
        "invariants_pass": invariants_pass,
        "development_support": development_support,
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
