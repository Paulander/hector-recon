#!/usr/bin/env python3
"""Run the frozen phase-split responsibility-allocation experiment."""

from __future__ import annotations

import argparse
from copy import deepcopy
from dataclasses import asdict, replace
import hashlib
import json
from pathlib import Path
import runpy
import statistics

from recon_lite import EpisodicCompositionConfig, EpisodicCompositionPolicy
from recon_lite import OnlineCompositionConfig


DEFAULT_OUTPUT = Path(
    "reports/autogrowth/generic_core/"
    "responsibility_allocation_key_door_20260712.json"
)
SEEDS = tuple(range(20261601, 20261621))
ARMS = (
    "broadcast",
    "fixed_low",
    "responsibility",
    "shuffled",
    "shared_frozen",
)
PHASE1_CHECKPOINTS = (512, 1024, 2048, 4096)
DEVELOPMENT_EVALUATION_COUNT = 512
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


def _hash_json(value: object) -> str:
    encoded = json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(encoded).hexdigest()


def _write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def _complete_policy_state(policy: EpisodicCompositionPolicy) -> dict[str, object]:
    state = policy.snapshot()
    state["policy_rng_state"] = policy._rng.getstate()
    state["topology_rng_state"] = policy._topology_rng.getstate()
    state["episode_trace"] = [asdict(item) for item in policy.episode_trace]
    if policy.experience_reservoir is not None:
        state["reservoir_rng_state"] = (
            policy.experience_reservoir._rng.getstate()
        )
        state["reservoir_records"] = [
            asdict(item) for item in policy.experience_reservoir.records
        ]
    complete_channels = {}
    for action_id, channel in policy.channels.items():
        learner = channel.learner
        complete_channels[action_id] = {
            "learner_rng_state": learner._rng.getstate(),
            "global_residual_sum": learner.global_residual_sum,
            "pair_evidence": [
                {
                    "members": members,
                    "support": evidence.support,
                    "residual_sum": evidence.residual_sum,
                }
                for members, evidence in sorted(learner.pair_evidence.items())
            ],
            "proposed_pairs": sorted(learner._proposed_pairs),
            "primitive_node_ids": sorted(channel.primitive_node_ids),
            "candidate_node_ids": dict(sorted(
                channel.candidate_node_ids.items()
            )),
        }
    state["complete_channel_state"] = complete_channels
    return state


def _configure_arm(policy: EpisodicCompositionPolicy, arm: str) -> None:
    changes = {
        "broadcast": {
            "residual_update_mode": "broadcast",
            "shared_learning_after_maturity_scale": 1.0,
        },
        "fixed_low": {
            "residual_update_mode": "broadcast",
            "shared_learning_after_maturity_scale": 0.10,
        },
        "responsibility": {
            "residual_update_mode": "responsibility_conserving",
            "shared_learning_after_maturity_scale": 1.0,
        },
        "shuffled": {
            "residual_update_mode": "responsibility_shuffled",
            "shared_learning_after_maturity_scale": 1.0,
        },
        "shared_frozen": {
            "residual_update_mode": "shared_frozen",
            "shared_learning_after_maturity_scale": 1.0,
        },
    }[arm]
    for channel in policy.channels.values():
        channel.learner.config = replace(
            channel.learner.config,
            shared_learning_schedule="fixed",
            **changes,
        )


def _train_episode(
    policy: EpisodicCompositionPolicy,
    task: dict[str, object],
    row: dict[str, object],
    door_observation,
    correct_actions,
) -> tuple[str, str, tuple[str, ...]]:
    policy.begin_episode()
    key_action = policy.choose(
        row["key_active_terminal_ids"],
        legal_action_ids=task["key_action_ids"],
    )
    policy.real_step(clear_trace=False)
    door_atoms = door_observation(task, row, key_action)
    door_action = policy.choose(
        door_atoms,
        legal_action_ids=task["door_action_ids"],
    )
    correct_key, correct_door = correct_actions(task, row)
    policy.observe_terminal(
        1.0
        if key_action == correct_key and door_action == correct_door
        else -1.0
    )
    return key_action, door_action, door_atoms


def _evaluate(
    policy: EpisodicCompositionPolicy,
    task: dict[str, object],
    rows: tuple[dict[str, object], ...],
    door_observation,
    correct_actions,
    *,
    include_mature_composites: bool = True,
    disabled_candidates_by_action: (
        dict[str, frozenset[int]] | None
    ) = None,
) -> dict[str, float]:
    key_correct = door_correct = joint_correct = 0
    for row in rows:
        key_action = policy.greedy_action(
            row["key_active_terminal_ids"],
            include_mature_composites=include_mature_composites,
            legal_action_ids=task["key_action_ids"],
            disabled_candidates_by_action=disabled_candidates_by_action,
        )
        door_action = policy.greedy_action(
            door_observation(task, row, key_action),
            include_mature_composites=include_mature_composites,
            legal_action_ids=task["door_action_ids"],
            disabled_candidates_by_action=disabled_candidates_by_action,
        )
        correct_key, correct_door = correct_actions(task, row)
        key_ok = key_action == correct_key
        door_ok = door_action == correct_door
        key_correct += int(key_ok)
        door_correct += int(door_ok)
        joint_correct += int(key_ok and door_ok)
    count = len(rows)
    return {
        "key_accuracy": key_correct / count,
        "door_accuracy": door_correct / count,
        "joint_success": joint_correct / count,
    }


def _individual_candidate_ablations(
    policy: EpisodicCompositionPolicy,
    task: dict[str, object],
    full_evaluations: dict[str, object],
    door_observation,
    correct_actions,
) -> list[dict[str, object]]:
    rows = []
    for action_id, channel in policy.channels.items():
        for index, candidate in enumerate(channel.learner.candidates):
            if candidate.state != "mature":
                continue
            disabled = {action_id: frozenset({index})}
            effects = {}
            for regime in (0, 1):
                ablated = _evaluate(
                    policy,
                    task,
                    task[f"evaluation_regime_{regime}"],
                    door_observation,
                    correct_actions,
                    disabled_candidates_by_action=disabled,
                )
                effects[f"regime_{regime}"] = {
                    "ablated": ablated,
                    "joint_effect": (
                        full_evaluations[f"regime_{regime}"]["full_graph"][
                            "joint_success"
                        ]
                        - ablated["joint_success"]
                    ),
                }
            rows.append({
                "action_id": action_id,
                "candidate_index": index,
                "members": candidate.members,
                "weight": candidate.shadow_weight,
                "net_improvement": candidate.net_improvement,
                "effects": effects,
            })
    return rows


def _coverage(policy: EpisodicCompositionPolicy, task: dict[str, object]) -> dict[str, object]:
    cues = {value: index for index, value in enumerate(task["door_cue_literals"])}
    regimes = {value: index for index, value in enumerate(task["regime_ids"])}
    found = []
    for action_id in task["door_action_ids"]:
        action_index = task["door_index_by_action"][action_id]
        for index, candidate in enumerate(
            policy.channels[action_id].learner.candidates
        ):
            if candidate.state != "mature":
                continue
            members = set(candidate.members)
            cue_ids = members & set(cues)
            regime_ids = members & set(regimes)
            if len(cue_ids) != 1 or len(regime_ids) != 1:
                continue
            cue_id = next(iter(cue_ids))
            regime_id = next(iter(regime_ids))
            correct_index = int(
                bool(cues[cue_id])
                ^ bool(regimes[regime_id])
                ^ bool(task["door_inverted"])
            )
            expected_positive = action_index == correct_index
            sign_agrees = (
                candidate.shadow_weight > 0.0
                if expected_positive
                else candidate.shadow_weight < 0.0
            )
            found.append({
                "action_id": action_id,
                "candidate_index": index,
                "cue_id": cue_id,
                "regime_id": regime_id,
                "weight": candidate.shadow_weight,
                "expected_positive": expected_positive,
                "sign_agrees": sign_agrees,
                "saturated": abs(candidate.shadow_weight) >= 1.0 - 1e-12,
            })
    covered = {
        (row["action_id"], row["cue_id"], row["regime_id"])
        for row in found
    }
    return {
        "possible_component_count": 8,
        "covered_component_count": len(covered),
        "coverage": len(covered) / 8,
        "sign_agreement_count": sum(row["sign_agrees"] for row in found),
        "saturated_count": sum(row["saturated"] for row in found),
        "components": found,
    }


def _score_diagnostics(
    policy: EpisodicCompositionPolicy,
    task: dict[str, object],
    door_observation,
) -> dict[str, object]:
    output_count = clipped_count = 0
    maximum_abs_raw = 0.0
    absolute_contribution_sum = {
        "bias": 0.0,
        "primitive": 0.0,
        "mature": 0.0,
        "trial_shadow": 0.0,
    }
    for regime in (0, 1):
        for row in task[f"evaluation_regime_{regime}"]:
            for action_id in task["key_action_ids"]:
                decomposition = policy.channels[action_id].score_decomposition(
                    row["key_active_terminal_ids"]
                )
                output_count += 1
                clipped_count += int(decomposition["output_clipped"])
                maximum_abs_raw = max(
                    maximum_abs_raw, abs(decomposition["raw_score"])
                )
                for component_id, value in decomposition[
                    "contributions"
                ].items():
                    kind = (
                        "bias"
                        if component_id == "bias_terminal"
                        else "mature"
                        if component_id.startswith("composite_")
                        else "primitive"
                    )
                    absolute_contribution_sum[kind] += abs(value)
                absolute_contribution_sum["trial_shadow"] += sum(
                    abs(value)
                    for value in decomposition[
                        "shadow_trial_contributions"
                    ].values()
                )
            key_action = policy.greedy_action(
                row["key_active_terminal_ids"],
                legal_action_ids=task["key_action_ids"],
            )
            door_atoms = door_observation(task, row, key_action)
            for action_id in task["door_action_ids"]:
                decomposition = policy.channels[action_id].score_decomposition(
                    door_atoms
                )
                output_count += 1
                clipped_count += int(decomposition["output_clipped"])
                maximum_abs_raw = max(
                    maximum_abs_raw, abs(decomposition["raw_score"])
                )
                for component_id, value in decomposition[
                    "contributions"
                ].items():
                    kind = (
                        "bias"
                        if component_id == "bias_terminal"
                        else "mature"
                        if component_id.startswith("composite_")
                        else "primitive"
                    )
                    absolute_contribution_sum[kind] += abs(value)
                absolute_contribution_sum["trial_shadow"] += sum(
                    abs(value)
                    for value in decomposition[
                        "shadow_trial_contributions"
                    ].values()
                )
    return {
        "output_count": output_count,
        "output_clipped_count": clipped_count,
        "maximum_abs_raw_score": maximum_abs_raw,
        "absolute_contribution_sum": absolute_contribution_sum,
    }


def _swap_shared(
    target: EpisodicCompositionPolicy,
    source: EpisodicCompositionPolicy,
) -> None:
    for action_id in target.action_ids:
        target_learner = target.channels[action_id].learner
        source_learner = source.channels[action_id].learner
        target_learner.bias = source_learner.bias
        target_learner.primitive_weights = deepcopy(
            source_learner.primitive_weights
        )
        target.channels[action_id]._sync_weights()


def _counterfactuals(
    final_policy: EpisodicCompositionPolicy,
    phase0_policy: EpisodicCompositionPolicy,
    task: dict[str, object],
    door_observation,
    correct_actions,
) -> dict[str, object]:
    phase0_shared_final_context = deepcopy(final_policy)
    _swap_shared(phase0_shared_final_context, phase0_policy)
    final_shared_phase0_context = deepcopy(phase0_policy)
    _swap_shared(final_shared_phase0_context, final_policy)
    assemblies = {
        "phase0_shared_final_contextual": phase0_shared_final_context,
        "final_shared_phase0_contextual": final_shared_phase0_context,
        "phase0_shared_phase0_contextual": phase0_policy,
    }
    return {
        name: {
            f"regime_{regime}": _evaluate(
                policy,
                task,
                task[f"evaluation_regime_{regime}"],
                door_observation,
                correct_actions,
            )
            for regime in (0, 1)
        }
        for name, policy in assemblies.items()
    }


def _allocation_metrics(policy: EpisodicCompositionPolicy) -> dict[str, object]:
    learners = [channel.learner for channel in policy.channels.values()]
    return {
        "update_count": sum(item.allocation_update_count for item in learners),
        "component_opportunity_count": sum(
            item.allocation_component_opportunity_count for item in learners
        ),
        "rng_call_count": sum(
            item.allocation_rng_call_count for item in learners
        ),
        "missing_responsibility_count": sum(
            item.allocation_missing_responsibility_count for item in learners
        ),
        "stale_component_count": sum(
            item.allocation_stale_component_count for item in learners
        ),
        "requested_l1_sum": sum(
            item.allocation_requested_l1_sum for item in learners
        ),
        "actual_l1_sum": sum(
            item.allocation_actual_l1_sum for item in learners
        ),
        "maximum_budget_error": max(
            item.allocation_max_budget_error for item in learners
        ),
        "share_sum": {
            kind: sum(item.allocation_share_sum[kind] for item in learners)
            for kind in ("bias", "primitive", "trial", "mature")
        },
        "parameter_clip_counts": {
            kind: sum(item.parameter_clip_counts[kind] for item in learners)
            for kind in ("bias", "primitive", "trial", "mature")
        },
    }


def _same_standard_budget(row: dict[str, object]) -> bool:
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
    partial_path = args.output.with_suffix(".partial.json")
    repo_root = Path(__file__).resolve().parents[2]
    key_door = runpy.run_path(str(KEY_DOOR_RUNNER))
    renewable = runpy.run_path(str(RENEWABLE_RUNNER))
    consolidation = runpy.run_path(str(CONSOLIDATION_RUNNER))
    dose = runpy.run_path(str(DOSE_RUNNER))
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
    phase0_work = []
    for index, seed in enumerate(SEEDS, start=1):
        task = make_task(
            seed,
            development_evaluation_count=DEVELOPMENT_EVALUATION_COUNT,
        )
        policy = EpisodicCompositionPolicy(
            task["all_action_ids"],
            random_seed=seed + 10_000_000,
            config=policy_config,
            composition_config=phase0_config,
        )
        for row in task["train_regime_0"]:
            _train_episode(
                policy, task, row, door_observation, correct_actions
            )
        development = _evaluate(
            policy,
            task,
            task["development_evaluation_regime_0"],
            door_observation,
            correct_actions,
        )
        state = _complete_policy_state(policy)
        checkpoint_hash = _hash_json(state)
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
        phase0_work.append((task, policy, checkpoint_hash))
        _write_json(partial_path, {
            "status": "phase0_in_progress",
            "completed_phase0_tasks": phase0_rows,
        })
        print(f"completed phase0 task {index}/{len(SEEDS)}", flush=True)

    phase0_mastery_pass = all(
        row["phase0_development"]["joint_success"] >= 0.85
        for row in phase0_rows
    )
    if not phase0_mastery_pass:
        payload = {
            "schema_version": "recon_responsibility_allocation_raw.v1",
            "status": "phase0_mastery_failed",
            "source_commit": git_commit(repo_root),
            "phase0_mastery_pass": False,
            "phase0_rows": phase0_rows,
            "phase0_rows_sha256": _hash_json(phase0_rows),
            "runner_sha256": file_hash(Path(__file__)),
        }
        _write_json(args.output, payload)
        partial_path.unlink(missing_ok=True)
        print(args.output)
        print(json.dumps({
            "phase0_mastery_pass": False,
            "minimum_phase0_joint": min(
                row["phase0_development"]["joint_success"]
                for row in phase0_rows
            ),
        }, sort_keys=True))
        return 0

    task_rows = []
    for task_index, (task, phase0_policy, checkpoint_hash) in enumerate(
        phase0_work, start=1
    ):
        clones = {arm: deepcopy(phase0_policy) for arm in ARMS}
        clone_hashes = {
            arm: _hash_json(_complete_policy_state(policy))
            for arm, policy in clones.items()
        }
        clone_parity = all(
            value == checkpoint_hash for value in clone_hashes.values()
        )
        for arm, policy in clones.items():
            _configure_arm(policy, arm)
        arm_rows = {}
        for arm, policy in clones.items():
            action_digest = hashlib.sha256()
            observation_digest = hashlib.sha256()
            trajectory = []
            for episode, row in enumerate(task["train_regime_1"], start=1):
                key_action, door_action, door_atoms = _train_episode(
                    policy, task, row, door_observation, correct_actions
                )
                action_digest.update(
                    f"{key_action}|{door_action}\n".encode()
                )
                observation_digest.update(
                    ("|".join(door_atoms) + "\n").encode()
                )
                if episode in PHASE1_CHECKPOINTS:
                    trajectory.append({
                        "phase1_episode": episode,
                        "old_development": _evaluate(
                            policy,
                            task,
                            task["development_evaluation_regime_0"],
                            door_observation,
                            correct_actions,
                        ),
                    })
            base_result = add_consolidation_metrics(
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
            base_result.update({
                "standard_evaluation_episode_count": (
                    len(PHASE1_CHECKPOINTS)
                    * DEVELOPMENT_EVALUATION_COUNT
                    + 2 * len(task["evaluation_regime_0"])
                ),
                "phase1_action_sequence_sha256": action_digest.hexdigest(),
                "phase1_action_conditioned_observation_sha256": (
                    observation_digest.hexdigest()
                ),
                "old_development_trajectory": trajectory,
                "allocation": _allocation_metrics(policy),
                "candidate_ablations": _individual_candidate_ablations(
                    policy,
                    task,
                    base_result["evaluations"],
                    door_observation,
                    correct_actions,
                ),
                "contextual_coverage": _coverage(policy, task),
                "score_diagnostics": _score_diagnostics(
                    policy, task, door_observation
                ),
                "counterfactual_assemblies": _counterfactuals(
                    policy,
                    phase0_policy,
                    task,
                    door_observation,
                    correct_actions,
                ),
            })
            arm_rows[arm] = base_result
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
        _write_json(partial_path, {
            "status": "phase1_in_progress",
            "phase0_rows_sha256": _hash_json(phase0_rows),
            "completed_task_rows": task_rows,
        })
        print(f"completed phase1 task {task_index}/{len(SEEDS)}", flush=True)

    def median(arm: str, regime: int, metric: str = "joint_success") -> float:
        return statistics.median(
            row["arms"][arm]["evaluations"][f"regime_{regime}"][
                "full_graph"
            ][metric]
            for row in task_rows
        )

    min_advantages = [
        min(
            row["arms"]["responsibility"]["evaluations"]["regime_0"][
                "full_graph"
            ]["joint_success"],
            row["arms"]["responsibility"]["evaluations"]["regime_1"][
                "full_graph"
            ]["joint_success"],
        )
        - min(
            row["arms"]["shuffled"]["evaluations"]["regime_0"][
                "full_graph"
            ]["joint_success"],
            row["arms"]["shuffled"]["evaluations"]["regime_1"][
                "full_graph"
            ]["joint_success"],
        )
        for row in task_rows
    ]
    old_drops = [
        row["phase0_development"]["joint_success"]
        - row["arms"]["responsibility"]["evaluations"]["regime_0"][
            "full_graph"
        ]["joint_success"]
        for row in task_rows
    ]
    max_total_proposals = max(
        channel["total_proposal_count"]
        for row in task_rows
        for arm in ARMS
        for channel in row["arms"][arm]["channels"].values()
    )
    max_live = max(
        channel["max_observed_live_candidate_count"]
        for row in task_rows
        for arm in ARMS
        for channel in row["arms"][arm]["channels"].values()
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
    standard_budget_tasks = sum(_same_standard_budget(row) for row in task_rows)
    raw_gates = {
        "phase0_mastery_task_count": len(phase0_rows),
        "responsibility_median_joint_regime_0": median(
            "responsibility", 0
        ),
        "responsibility_median_joint_regime_1": median(
            "responsibility", 1
        ),
        "responsibility_median_old_drop": statistics.median(old_drops),
        "broadcast_minus_responsibility_new_median": (
            median("broadcast", 1) - median("responsibility", 1)
        ),
        "fixed_low_minus_responsibility_new_median": (
            median("fixed_low", 1) - median("responsibility", 1)
        ),
        "responsibility_higher_old_than_broadcast_task_count": sum(
            row["arms"]["responsibility"]["evaluations"]["regime_0"][
                "full_graph"
            ]["joint_success"]
            > row["arms"]["broadcast"]["evaluations"]["regime_0"][
                "full_graph"
            ]["joint_success"]
            for row in task_rows
        ),
        "responsibility_higher_old_than_fixed_low_task_count": sum(
            row["arms"]["responsibility"]["evaluations"]["regime_0"][
                "full_graph"
            ]["joint_success"]
            > row["arms"]["fixed_low"]["evaluations"]["regime_0"][
                "full_graph"
            ]["joint_success"]
            for row in task_rows
        ),
        "responsibility_min_better_than_shuffled_task_count": sum(
            value > 0.0 for value in min_advantages
        ),
        "responsibility_median_min_advantage_over_shuffled": (
            statistics.median(min_advantages)
        ),
        "responsibility_median_old_composite_effect": statistics.median(
            row["arms"]["responsibility"]["evaluations"]["regime_0"][
                "joint_ablation_drop"
            ]
            for row in task_rows
        ),
        "responsibility_median_new_composite_effect": statistics.median(
            row["arms"]["responsibility"]["evaluations"]["regime_1"][
                "joint_ablation_drop"
            ]
            for row in task_rows
        ),
        "maximum_allocation_budget_error": max(
            row["arms"][arm]["allocation"]["maximum_budget_error"]
            for row in task_rows
            for arm in ("responsibility", "shuffled")
        ),
        "allocation_rng_formula_task_count": sum(
            all(
                row["arms"][arm]["allocation"]["rng_call_count"]
                == row["arms"][arm]["allocation"][
                    "component_opportunity_count"
                ] - row["arms"][arm]["allocation"]["update_count"]
                for arm in ("responsibility", "shuffled")
            )
            for row in task_rows
        ),
        "complete_responsibility_task_count": sum(
            all(
                row["arms"][arm]["allocation"]["update_count"] == 8192
                and row["arms"][arm]["allocation"][
                    "missing_responsibility_count"
                ] == 0
                and row["arms"][arm]["allocation"][
                    "stale_component_count"
                ] == 0
                for arm in ("responsibility", "shuffled")
            )
            for row in task_rows
        ),
        "clone_parity_task_count": sum(
            row["clone_parity"] for row in task_rows
        ),
        "maximum_total_proposals_observed": max_total_proposals,
        "maximum_live_candidates_observed": max_live,
        "total_graph_or_update_mismatch_count": mismatch,
        "total_trial_root_edge_count": trial_edges,
        "identical_standard_budget_task_count": standard_budget_tasks,
        "task_count": len(task_rows),
    }
    gates_pass = all((
        raw_gates["responsibility_median_joint_regime_0"] >= 0.85,
        raw_gates["responsibility_median_joint_regime_1"] >= 0.85,
        raw_gates["responsibility_median_old_drop"] <= 0.05,
        raw_gates["broadcast_minus_responsibility_new_median"] <= 0.05,
        raw_gates["fixed_low_minus_responsibility_new_median"] <= 0.05,
        raw_gates[
            "responsibility_higher_old_than_broadcast_task_count"
        ] >= 16,
        raw_gates[
            "responsibility_higher_old_than_fixed_low_task_count"
        ] >= 14,
        raw_gates[
            "responsibility_min_better_than_shuffled_task_count"
        ] >= 16,
        raw_gates[
            "responsibility_median_min_advantage_over_shuffled"
        ] >= 0.10,
        raw_gates["responsibility_median_old_composite_effect"] >= 0.10,
        raw_gates["responsibility_median_new_composite_effect"] >= 0.10,
        raw_gates["maximum_allocation_budget_error"] <= 1e-12,
        raw_gates["allocation_rng_formula_task_count"] == len(task_rows),
        raw_gates["complete_responsibility_task_count"] == len(task_rows),
        raw_gates["clone_parity_task_count"] == len(task_rows),
        max_total_proposals <= 64,
        max_live <= 4,
        mismatch == 0,
        trial_edges == 0,
        standard_budget_tasks == len(task_rows),
    ))
    payload = {
        "schema_version": "recon_responsibility_allocation_raw.v1",
        "status": "complete",
        "track": "generic_core_development",
        "confirmation_claimed": False,
        "builder_is_runner": True,
        "adjudication_authority": False,
        "source_commit": git_commit(repo_root),
        "frozen_contract": (
            "docs/autogrowth/"
            "GENERIC_CORE_RESPONSIBILITY_ALLOCATION_WORK_PACKAGE_20260712.md"
        ),
        "policy_config": asdict(policy_config),
        "phase0_composition_config": asdict(phase0_config),
        "frozen_seed_range": [SEEDS[0], SEEDS[-1]],
        "phase1_checkpoints": PHASE1_CHECKPOINTS,
        "phase0_mastery_pass": True,
        "phase0_rows": phase0_rows,
        "phase0_rows_sha256": _hash_json(phase0_rows),
        "task_rows": task_rows,
        "task_rows_sha256": _hash_json(task_rows),
        "raw_gate_measurements": raw_gates,
        "gates_pass": gates_pass,
        "composition_implementation_sha256": file_hash(
            repo_root / "libs/recon-lite/src/recon_lite/online_composition.py"
        ),
        "episodic_implementation_sha256": file_hash(
            repo_root / "libs/recon-lite/src/recon_lite/episodic_composition.py"
        ),
        "key_door_runner_sha256": file_hash(KEY_DOOR_RUNNER),
        "renewable_runner_sha256": file_hash(RENEWABLE_RUNNER),
        "consolidation_runner_sha256": file_hash(CONSOLIDATION_RUNNER),
        "runner_sha256": file_hash(Path(__file__)),
    }
    _write_json(args.output, payload)
    partial_path.unlink(missing_ok=True)
    print(args.output)
    print(json.dumps({
        "gates_pass": gates_pass,
        "raw_gate_measurements": raw_gates,
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
