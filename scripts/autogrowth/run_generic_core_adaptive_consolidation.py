#!/usr/bin/env python3
"""Run the once-frozen generic-core adaptive-consolidation experiment."""

from __future__ import annotations

import argparse
from dataclasses import asdict
import json
from pathlib import Path
import runpy
import statistics

from recon_lite import EpisodicCompositionConfig, OnlineCompositionConfig


DEFAULT_OUTPUT = Path(
    "reports/autogrowth/generic_core/"
    "adaptive_consolidation_key_door_20260712.json"
)
SEEDS = tuple(range(20261501, 20261521))
ARM_NAMES = ("fixed_full", "fixed_low", "adaptive")
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


def _arms_have_identical_total_budget(
    row: dict[str, object],
    arm_names: tuple[str, ...],
) -> bool:
    if not arm_names:
        return False
    reference = row["arms"][arm_names[0]]
    reference_total_actions = sum(reference["selection_count"].values())
    return all(
        row["arms"][arm]["training_episode_count"]
        == reference["training_episode_count"]
        and row["arms"][arm]["evaluation_episode_count"]
        == reference["evaluation_episode_count"]
        and sum(row["arms"][arm]["selection_count"].values())
        == reference_total_actions
        and row["arms"][arm]["rng_call_count"]
        == reference["rng_call_count"]
        for arm in arm_names[1:]
    )


def _add_adaptive_metrics(
    result: dict[str, object],
    policy: object,
) -> dict[str, object]:
    evidence_total = 0
    minimum_scales = []
    mean_scales = []
    for action_id, channel in policy.channels.items():
        learner = channel.learner
        channel_result = result["channels"][action_id]
        observations = (
            learner.shared_learning_scale_observations_after_maturity
        )
        mean_scale = (
            learner.shared_learning_scale_sum_after_maturity / observations
            if observations
            else 1.0
        )
        channel_result.update({
            "mature_evidence_activation_count": (
                learner.mature_evidence_activation_count
            ),
            "current_shared_learning_scale": (
                learner.current_shared_learning_scale
            ),
            "minimum_shared_learning_scale": (
                learner.minimum_shared_learning_scale
            ),
            "mean_shared_learning_scale_after_maturity": mean_scale,
            "shared_learning_scale_observations_after_maturity": (
                observations
            ),
        })
        evidence_total += learner.mature_evidence_activation_count
        if observations:
            minimum_scales.append(learner.minimum_shared_learning_scale)
            mean_scales.append(mean_scale)
    result.update({
        "mature_evidence_activation_count": evidence_total,
        "minimum_shared_learning_scale": (
            min(minimum_scales) if minimum_scales else 1.0
        ),
        "mean_channel_shared_learning_scale_after_maturity": (
            statistics.mean(mean_scales) if mean_scales else 1.0
        ),
    })
    return result


def _arm_summary(
    rows: list[dict[str, object]],
    arm: str,
) -> dict[str, object]:
    medians = {}
    for regime in (0, 1):
        medians[f"median_joint_regime_{regime}"] = statistics.median(
            row["arms"][arm]["evaluations"][f"regime_{regime}"][
                "full_graph"
            ]["joint_success"]
            for row in rows
        )
        medians[f"median_key_regime_{regime}"] = statistics.median(
            row["arms"][arm]["evaluations"][f"regime_{regime}"][
                "full_graph"
            ]["key_accuracy"]
            for row in rows
        )
    ablation_drops = [
        statistics.mean(
            row["arms"][arm]["evaluations"][f"regime_{regime}"][
                "joint_ablation_drop"
            ]
            for regime in (0, 1)
        )
        for row in rows
    ]
    return {
        **medians,
        "mature_regime_1_pair_task_count": sum(
            row["arms"][arm]["mature_door_cue_regime_1"]
            for row in rows
        ),
        "median_joint_ablation_drop": statistics.median(ablation_drops),
        "median_mature_evidence_activation_count": statistics.median(
            row["arms"][arm]["mature_evidence_activation_count"]
            for row in rows
        ),
        "median_minimum_shared_learning_scale": statistics.median(
            row["arms"][arm]["minimum_shared_learning_scale"]
            for row in rows
        ),
        "median_mean_channel_shared_learning_scale": statistics.median(
            row["arms"][arm][
                "mean_channel_shared_learning_scale_after_maturity"
            ]
            for row in rows
        ),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    repo_root = Path(__file__).resolve().parents[2]
    key_door = runpy.run_path(str(KEY_DOOR_RUNNER))
    renewable = runpy.run_path(str(RENEWABLE_RUNNER))
    consolidation = runpy.run_path(str(CONSOLIDATION_RUNNER))
    dose = runpy.run_path(str(DOSE_RUNNER))
    make_task = key_door["_make_task"]
    train_arm = key_door["_train_arm"]
    arm_result = key_door["_arm_result"]
    enrich_arm = renewable["_enrich_arm"]
    add_consolidation_metrics = consolidation[
        "_add_consolidation_metrics"
    ]
    hash_json = dose["_hash_json"]
    file_hash = dose["_file_hash"]
    git_commit = dose["_git_commit"]
    task_manifest = dose["_task_manifest"]
    policy_config = EpisodicCompositionConfig(
        exploration_rate=0.15,
        discount=0.97,
    )
    composition_configs = {
        "fixed_full": OnlineCompositionConfig(
            max_total_proposals=64,
            shared_learning_after_maturity_scale=1.0,
        ),
        "fixed_low": OnlineCompositionConfig(
            max_total_proposals=64,
            shared_learning_after_maturity_scale=0.10,
        ),
        "adaptive": OnlineCompositionConfig(
            max_total_proposals=64,
            shared_learning_schedule="mature_activation_decay",
            adaptive_shared_learning_floor=0.10,
            adaptive_consolidation_activations=1024,
        ),
    }
    task_rows = []
    for task_index, seed in enumerate(SEEDS, start=1):
        task = make_task(seed)
        arms = {}
        for arm in ARM_NAMES:
            policy = train_arm(
                task=task,
                clear_at_transition=False,
                random_seed=seed + 9_000_000,
                policy_config=policy_config,
                composition_config=composition_configs[arm],
            )
            arms[arm] = _add_adaptive_metrics(
                add_consolidation_metrics(
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
                ),
                policy,
            )
        task_rows.append({
            "seed": seed,
            **task_manifest(task),
            "arms": arms,
        })
        print(f"completed task {task_index}/{len(SEEDS)}", flush=True)

    maximum_total_proposals = max(
        channel["total_proposal_count"]
        for row in task_rows
        for arm in ARM_NAMES
        for channel in row["arms"][arm]["channels"].values()
    )
    maximum_live_candidates = max(
        channel["max_observed_live_candidate_count"]
        for row in task_rows
        for arm in ARM_NAMES
        for channel in row["arms"][arm]["channels"].values()
    )
    mismatch_count = sum(
        row["arms"][arm]["selection_update_mismatch_count"]
        + sum(
            channel["graph_prediction_mismatch_count"]
            for channel in row["arms"][arm]["channels"].values()
        )
        for row in task_rows
        for arm in ARM_NAMES
    )
    trial_root_edges = sum(
        channel["trial_root_edge_count"]
        for row in task_rows
        for arm in ARM_NAMES
        for channel in row["arms"][arm]["channels"].values()
    )
    identical_budget_tasks = sum(
        _arms_have_identical_total_budget(row, ARM_NAMES)
        for row in task_rows
    )
    invariants = {
        "maximum_total_proposals_observed": maximum_total_proposals,
        "maximum_live_candidates_observed": maximum_live_candidates,
        "total_graph_or_update_mismatch_count": mismatch_count,
        "total_trial_root_edge_count": trial_root_edges,
        "identical_total_budget_task_count": identical_budget_tasks,
        "task_count": len(task_rows),
    }
    invariants_pass = all((
        maximum_total_proposals <= 64,
        maximum_live_candidates <= 4,
        mismatch_count == 0,
        trial_root_edges == 0,
        identical_budget_tasks == len(task_rows),
    ))
    summaries = {
        arm: _arm_summary(task_rows, arm)
        for arm in ARM_NAMES
    }
    adaptive = summaries["adaptive"]
    fixed_full = summaries["fixed_full"]
    fixed_low = summaries["fixed_low"]
    raw_gates = {
        "adaptive_median_joint_regime_0": adaptive[
            "median_joint_regime_0"
        ],
        "adaptive_median_joint_regime_1": adaptive[
            "median_joint_regime_1"
        ],
        "adaptive_median_key_regime_0": adaptive["median_key_regime_0"],
        "adaptive_median_key_regime_1": adaptive["median_key_regime_1"],
        "adaptive_higher_old_than_fixed_full_task_count": sum(
            row["arms"]["adaptive"]["evaluations"]["regime_0"][
                "full_graph"
            ]["joint_success"]
            > row["arms"]["fixed_full"]["evaluations"]["regime_0"][
                "full_graph"
            ]["joint_success"]
            for row in task_rows
        ),
        "adaptive_higher_old_than_fixed_low_task_count": sum(
            row["arms"]["adaptive"]["evaluations"]["regime_0"][
                "full_graph"
            ]["joint_success"]
            > row["arms"]["fixed_low"]["evaluations"]["regime_0"][
                "full_graph"
            ]["joint_success"]
            for row in task_rows
        ),
        "fixed_full_minus_adaptive_new_median": (
            fixed_full["median_joint_regime_1"]
            - adaptive["median_joint_regime_1"]
        ),
        "fixed_low_minus_adaptive_new_median": (
            fixed_low["median_joint_regime_1"]
            - adaptive["median_joint_regime_1"]
        ),
        "adaptive_mature_regime_1_pair_task_count": adaptive[
            "mature_regime_1_pair_task_count"
        ],
        "adaptive_median_joint_ablation_drop": adaptive[
            "median_joint_ablation_drop"
        ],
        "adaptive_all_tasks_have_required_local_activity": all(
            row["arms"]["adaptive"]["matured_channel_count"] > 0
            and row["arms"]["adaptive"][
                "mature_evidence_activation_count"
            ] > 0
            and sum(
                channel["shared_update_events_after_maturity"]
                for channel in row["arms"]["adaptive"]["channels"].values()
            ) > 0
            and row["arms"]["adaptive"][
                "matured_channels_with_candidate_updates"
            ] > 0
            for row in task_rows
        ),
        "adaptive_scale_at_most_0_20_task_count": sum(
            row["arms"]["adaptive"]["minimum_shared_learning_scale"]
            <= 0.20
            for row in task_rows
        ),
        "invariants_pass": invariants_pass,
    }
    gates_pass = all((
        raw_gates["adaptive_median_joint_regime_0"] >= 0.85,
        raw_gates["adaptive_median_joint_regime_1"] >= 0.85,
        raw_gates["adaptive_median_key_regime_0"] >= 0.90,
        raw_gates["adaptive_median_key_regime_1"] >= 0.90,
        raw_gates[
            "adaptive_higher_old_than_fixed_full_task_count"
        ] >= 16,
        raw_gates[
            "adaptive_higher_old_than_fixed_low_task_count"
        ] >= 14,
        raw_gates["fixed_full_minus_adaptive_new_median"] <= 0.05,
        raw_gates["fixed_low_minus_adaptive_new_median"] <= 0.05,
        raw_gates["adaptive_mature_regime_1_pair_task_count"] >= 16,
        raw_gates["adaptive_median_joint_ablation_drop"] >= 0.15,
        raw_gates["adaptive_all_tasks_have_required_local_activity"],
        raw_gates["adaptive_scale_at_most_0_20_task_count"] >= 16,
        invariants_pass,
    ))
    payload = {
        "schema_version": "recon_adaptive_consolidation_raw.v1",
        "track": "generic_core_development",
        "confirmation_claimed": False,
        "builder_is_runner": True,
        "adjudication_authority": False,
        "source_commit": git_commit(repo_root),
        "frozen_contract": (
            "docs/autogrowth/"
            "GENERIC_CORE_ADAPTIVE_CONSOLIDATION_WORK_PACKAGE_20260712.md"
        ),
        "predecessor_artifact": (
            "reports/autogrowth/generic_core/"
            "consolidation_dose_key_door_20260712.json"
        ),
        "policy_config": asdict(policy_config),
        "composition_configs": {
            arm: asdict(config)
            for arm, config in composition_configs.items()
        },
        "frozen_seed_range": [SEEDS[0], SEEDS[-1]],
        "task_rows": task_rows,
        "task_rows_sha256": hash_json(task_rows),
        "arm_summaries": summaries,
        "raw_gate_measurements": raw_gates,
        "invariants": invariants,
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
        "dose_runner_sha256": file_hash(DOSE_RUNNER),
        "runner_sha256": file_hash(Path(__file__)),
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(args.output)
    print(json.dumps({
        "arm_summaries": summaries,
        "gates_pass": gates_pass,
        "invariants": invariants,
        "raw_gate_measurements": raw_gates,
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
