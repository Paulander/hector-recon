#!/usr/bin/env python3
"""Run the once-frozen learner-local consolidation experiment."""

from __future__ import annotations

import argparse
from dataclasses import asdict
import hashlib
import json
from pathlib import Path
import runpy
import statistics
import subprocess

from recon_lite import EpisodicCompositionConfig, OnlineCompositionConfig


DEFAULT_OUTPUT = Path(
    "reports/autogrowth/generic_core/"
    "local_consolidation_key_door_20260712.json"
)
SEEDS = tuple(range(20261201, 20261221))
KEY_DOOR_RUNNER = Path(__file__).with_name(
    "run_generic_core_multistate_key_door.py"
)
RENEWABLE_RUNNER = Path(__file__).with_name(
    "run_generic_core_renewable_topology.py"
)


def _hash_json(value: object) -> str:
    encoded = json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(encoded).hexdigest()


def _file_hash(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _git_commit(repo_root: Path) -> str:
    result = subprocess.run(
        ("git", "rev-parse", "HEAD"),
        cwd=repo_root,
        check=False,
        capture_output=True,
        text=True,
        timeout=10,
    )
    return result.stdout.strip() if result.returncode == 0 else "unavailable"


def _weight_summary(values: list[float]) -> dict[str, float | int]:
    return {
        "count": len(values),
        "minimum": min(values) if values else 0.0,
        "maximum": max(values) if values else 0.0,
        "l1": sum(abs(value) for value in values),
    }


def _add_consolidation_metrics(
    result: dict[str, object],
    policy: object,
) -> dict[str, object]:
    matured_channels = 0
    matured_with_zero_shared_updates = 0
    matured_with_candidate_updates = 0
    for action_id, channel in policy.channels.items():
        learner = channel.learner
        channel_result = result["channels"][action_id]
        primitive_values = list(learner.primitive_weights.values())
        candidate_values = [
            candidate.shadow_weight for candidate in learner.candidates
        ]
        channel_result.update({
            "first_maturity_observation": (
                learner.first_maturity_observation
            ),
            "shared_update_events_before_maturity": (
                learner.shared_update_events_before_maturity
            ),
            "shared_update_events_after_maturity": (
                learner.shared_update_events_after_maturity
            ),
            "candidate_weight_updates_after_maturity": (
                learner.candidate_weight_updates_after_maturity
            ),
            "bias": learner.bias,
            "primitive_weight_summary": _weight_summary(primitive_values),
            "candidate_weight_summary": _weight_summary(candidate_values),
        })
        if learner.first_maturity_observation is None:
            continue
        matured_channels += 1
        matured_with_zero_shared_updates += int(
            learner.shared_update_events_after_maturity == 0
        )
        matured_with_candidate_updates += int(
            learner.candidate_weight_updates_after_maturity > 0
        )
    result.update({
        "matured_channel_count": matured_channels,
        "matured_channels_with_zero_shared_updates": (
            matured_with_zero_shared_updates
        ),
        "matured_channels_with_candidate_updates": (
            matured_with_candidate_updates
        ),
    })
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    repo_root = Path(__file__).resolve().parents[2]
    key_door = runpy.run_path(str(KEY_DOOR_RUNNER))
    renewable = runpy.run_path(str(RENEWABLE_RUNNER))
    make_task = key_door["_make_task"]
    train_arm = key_door["_train_arm"]
    arm_result = key_door["_arm_result"]
    enrich_arm = renewable["_enrich_arm"]
    policy_config = EpisodicCompositionConfig(
        exploration_rate=0.15,
        discount=0.97,
    )
    control_config = OnlineCompositionConfig(
        max_total_proposals=64,
        shared_learning_after_maturity_scale=1.0,
    )
    consolidated_config = OnlineCompositionConfig(
        max_total_proposals=64,
        shared_learning_after_maturity_scale=0.0,
    )
    task_rows = []
    for seed in SEEDS:
        task = make_task(seed)
        control_policy = train_arm(
            task=task,
            clear_at_transition=False,
            random_seed=seed + 7_000_000,
            policy_config=policy_config,
            composition_config=control_config,
        )
        consolidated_policy = train_arm(
            task=task,
            clear_at_transition=False,
            random_seed=seed + 7_000_000,
            policy_config=policy_config,
            composition_config=consolidated_config,
        )
        control = _add_consolidation_metrics(
            enrich_arm(
                arm_result(
                    control_policy,
                    task,
                    clear_at_transition=False,
                ),
                control_policy,
                task,
            ),
            control_policy,
        )
        consolidated = _add_consolidation_metrics(
            enrich_arm(
                arm_result(
                    consolidated_policy,
                    task,
                    clear_at_transition=False,
                ),
                consolidated_policy,
                task,
            ),
            consolidated_policy,
        )
        task_rows.append({
            "seed": seed,
            "key_literals": task["key_literals"],
            "carried_ids": task["carried_ids"],
            "door_cue_literals": task["door_cue_literals"],
            "door_nuisance_literals": task["door_nuisance_literals"],
            "regime_ids": task["regime_ids"],
            "key_action_ids": task["key_action_ids"],
            "door_action_ids": task["door_action_ids"],
            "key_index_by_action": task["key_index_by_action"],
            "door_index_by_action": task["door_index_by_action"],
            "key_inverted": task["key_inverted"],
            "door_inverted": task["door_inverted"],
            "train_regime_0_sha256": task["train_regime_0_sha256"],
            "train_regime_1_sha256": task["train_regime_1_sha256"],
            "evaluation_regime_0_sha256": task[
                "evaluation_regime_0_sha256"
            ],
            "evaluation_regime_1_sha256": task[
                "evaluation_regime_1_sha256"
            ],
            "renewable_control": control,
            "consolidated": consolidated,
        })

    consolidated_ablation_drops = [
        statistics.mean(
            row["consolidated"]["evaluations"][f"regime_{regime}"][
                "joint_ablation_drop"
            ]
            for regime in (0, 1)
        )
        for row in task_rows
    ]
    control_new_median = statistics.median(
        row["renewable_control"]["evaluations"]["regime_1"]["full_graph"][
            "joint_success"
        ]
        for row in task_rows
    )
    consolidated_new_median = statistics.median(
        row["consolidated"]["evaluations"]["regime_1"]["full_graph"][
            "joint_success"
        ]
        for row in task_rows
    )
    payload = {
        "schema_version": "recon_local_consolidation_raw.v1",
        "track": "generic_core_development",
        "confirmation_claimed": False,
        "builder_is_runner": True,
        "adjudication_authority": False,
        "source_commit": _git_commit(repo_root),
        "frozen_contract": (
            "docs/autogrowth/"
            "GENERIC_CORE_LOCAL_CONSOLIDATION_WORK_PACKAGE_20260712.md"
        ),
        "predecessor_artifact": (
            "reports/autogrowth/generic_core/"
            "renewable_topology_key_door_20260712.json"
        ),
        "policy_config": asdict(policy_config),
        "control_composition_config": asdict(control_config),
        "consolidated_composition_config": asdict(consolidated_config),
        "frozen_seed_range": [SEEDS[0], SEEDS[-1]],
        "task_rows": task_rows,
        "task_rows_sha256": _hash_json(task_rows),
        "raw_gate_measurements": {
            "consolidated_median_joint_regime_0": statistics.median(
                row["consolidated"]["evaluations"]["regime_0"]["full_graph"][
                    "joint_success"
                ]
                for row in task_rows
            ),
            "consolidated_median_joint_regime_1": (
                consolidated_new_median
            ),
            "consolidated_median_key_regime_0": statistics.median(
                row["consolidated"]["evaluations"]["regime_0"]["full_graph"][
                    "key_accuracy"
                ]
                for row in task_rows
            ),
            "consolidated_median_key_regime_1": statistics.median(
                row["consolidated"]["evaluations"]["regime_1"]["full_graph"][
                    "key_accuracy"
                ]
                for row in task_rows
            ),
            "consolidated_higher_old_joint_task_count": sum(
                row["consolidated"]["evaluations"]["regime_0"]["full_graph"][
                    "joint_success"
                ]
                > row["renewable_control"]["evaluations"]["regime_0"][
                    "full_graph"
                ]["joint_success"]
                for row in task_rows
            ),
            "control_minus_consolidated_new_median": (
                control_new_median - consolidated_new_median
            ),
            "consolidated_mature_regime_1_pair_task_count": sum(
                row["consolidated"]["mature_door_cue_regime_1"]
                for row in task_rows
            ),
            "consolidated_median_joint_ablation_drop": statistics.median(
                consolidated_ablation_drops
            ),
            "consolidated_all_matured_channels_shared_updates_zero": all(
                row["consolidated"][
                    "matured_channels_with_zero_shared_updates"
                ] == row["consolidated"]["matured_channel_count"]
                for row in task_rows
            ),
            "consolidated_all_tasks_candidate_updates_after_maturity": all(
                row["consolidated"][
                    "matured_channels_with_candidate_updates"
                ] > 0
                for row in task_rows
            ),
            "maximum_total_proposals_observed": max(
                channel["total_proposal_count"]
                for row in task_rows
                for arm in ("renewable_control", "consolidated")
                for channel in row[arm]["channels"].values()
            ),
            "maximum_live_candidates_observed": max(
                channel["max_observed_live_candidate_count"]
                for row in task_rows
                for arm in ("renewable_control", "consolidated")
                for channel in row[arm]["channels"].values()
            ),
            "total_graph_or_update_mismatch_count": sum(
                row[arm]["selection_update_mismatch_count"]
                + sum(
                    channel["graph_prediction_mismatch_count"]
                    for channel in row[arm]["channels"].values()
                )
                for row in task_rows
                for arm in ("renewable_control", "consolidated")
            ),
            "total_trial_root_edge_count": sum(
                channel["trial_root_edge_count"]
                for row in task_rows
                for arm in ("renewable_control", "consolidated")
                for channel in row[arm]["channels"].values()
            ),
            "identical_configured_budget_task_count": sum(
                row["renewable_control"]["training_episode_count"]
                == row["consolidated"]["training_episode_count"]
                and row["renewable_control"]["evaluation_episode_count"]
                == row["consolidated"]["evaluation_episode_count"]
                and row["renewable_control"]["rng_call_count"]
                == row["consolidated"]["rng_call_count"]
                for row in task_rows
            ),
            "task_count": len(task_rows),
        },
        "composition_implementation_sha256": _file_hash(
            repo_root / "libs/recon-lite/src/recon_lite/online_composition.py"
        ),
        "episodic_implementation_sha256": _file_hash(
            repo_root / "libs/recon-lite/src/recon_lite/episodic_composition.py"
        ),
        "key_door_runner_sha256": _file_hash(KEY_DOOR_RUNNER),
        "renewable_runner_sha256": _file_hash(RENEWABLE_RUNNER),
        "runner_sha256": _file_hash(Path(__file__)),
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(args.output)
    print(json.dumps(payload["raw_gate_measurements"], sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
