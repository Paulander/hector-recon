#!/usr/bin/env python3
"""Run the once-frozen renewable-topology key-door experiment."""

from __future__ import annotations

import argparse
from dataclasses import asdict
import hashlib
import json
from pathlib import Path
import runpy
import statistics
import subprocess

from recon_lite import (
    EpisodicCompositionConfig,
    OnlineCompositionConfig,
)


DEFAULT_OUTPUT = Path(
    "reports/autogrowth/generic_core/"
    "renewable_topology_key_door_20260712.json"
)
SEEDS = tuple(range(20261101, 20261121))
PREDECESSOR_RUNNER = Path(__file__).with_name(
    "run_generic_core_multistate_key_door.py"
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


def _enrich_arm(
    result: dict[str, object],
    policy: object,
    task: dict[str, object],
) -> dict[str, object]:
    regime_0_id, regime_1_id = task["regime_ids"]
    cue_ids = set(task["door_cue_literals"])
    mature_regime_0 = 0
    mature_regime_1 = 0
    actions_at_four_mature = []
    for action_id, channel in policy.channels.items():
        candidates = channel.learner.candidates
        live_count = sum(
            candidate.state in {"trial", "mature"}
            for candidate in candidates
        )
        mature_count = sum(
            candidate.state == "mature" for candidate in candidates
        )
        channel_result = result["channels"][action_id]
        channel_result.update({
            "total_proposal_count": len(candidates),
            "final_live_candidate_count": live_count,
            "max_observed_live_candidate_count": (
                channel.learner.max_observed_live_candidate_count
            ),
            "total_proposal_limit": (
                channel.learner.config.max_total_proposals
            ),
        })
        if mature_count == channel.learner.config.max_candidates:
            actions_at_four_mature.append(action_id)
        if action_id not in task["door_action_ids"]:
            continue
        for candidate in candidates:
            if candidate.state != "mature":
                continue
            members = set(candidate.members)
            if not members & cue_ids:
                continue
            mature_regime_0 += int(regime_0_id in members)
            mature_regime_1 += int(regime_1_id in members)
    result.update({
        "mature_door_cue_regime_0_count": mature_regime_0,
        "mature_door_cue_regime_1_count": mature_regime_1,
        "mature_door_cue_regime_1": mature_regime_1 > 0,
        "actions_at_four_mature_candidates": actions_at_four_mature,
    })
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    repo_root = Path(__file__).resolve().parents[2]
    predecessor = runpy.run_path(str(PREDECESSOR_RUNNER))
    make_task = predecessor["_make_task"]
    train_arm = predecessor["_train_arm"]
    arm_result = predecessor["_arm_result"]
    policy_config = EpisodicCompositionConfig(
        exploration_rate=0.15,
        discount=0.97,
    )
    composition_config = OnlineCompositionConfig(
        max_total_proposals=64,
    )
    task_rows = []
    for seed in SEEDS:
        task = make_task(seed)
        persistent_policy = train_arm(
            task=task,
            clear_at_transition=False,
            random_seed=seed + 6_000_000,
            policy_config=policy_config,
            composition_config=composition_config,
        )
        reset_policy = train_arm(
            task=task,
            clear_at_transition=True,
            random_seed=seed + 6_000_000,
            policy_config=policy_config,
            composition_config=composition_config,
        )
        persistent = _enrich_arm(
            arm_result(
                persistent_policy,
                task,
                clear_at_transition=False,
            ),
            persistent_policy,
            task,
        )
        reset = _enrich_arm(
            arm_result(
                reset_policy,
                task,
                clear_at_transition=True,
            ),
            reset_policy,
            task,
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
            "persistent": persistent,
            "transition_reset": reset,
        })

    ablation_drops = [
        statistics.mean(
            row["persistent"]["evaluations"][f"regime_{regime}"][
                "joint_ablation_drop"
            ]
            for regime in (0, 1)
        )
        for row in task_rows
    ]
    payload = {
        "schema_version": "recon_renewable_topology_raw.v1",
        "track": "generic_core_development",
        "confirmation_claimed": False,
        "builder_is_runner": True,
        "adjudication_authority": False,
        "source_commit": _git_commit(repo_root),
        "frozen_contract": (
            "docs/autogrowth/"
            "GENERIC_CORE_RENEWABLE_TOPOLOGY_WORK_PACKAGE_20260712.md"
        ),
        "predecessor_artifact": (
            "reports/autogrowth/generic_core/"
            "multistate_key_door_20260712.json"
        ),
        "policy_config": asdict(policy_config),
        "composition_config": asdict(composition_config),
        "frozen_seed_range": [SEEDS[0], SEEDS[-1]],
        "task_rows": task_rows,
        "task_rows_sha256": _hash_json(task_rows),
        "raw_gate_measurements": {
            "persistent_mature_regime_1_pair_task_count": sum(
                row["persistent"]["mature_door_cue_regime_1"]
                for row in task_rows
            ),
            "persistent_median_joint_regime_0": statistics.median(
                row["persistent"]["evaluations"]["regime_0"]["full_graph"][
                    "joint_success"
                ]
                for row in task_rows
            ),
            "persistent_median_joint_regime_1": statistics.median(
                row["persistent"]["evaluations"]["regime_1"]["full_graph"][
                    "joint_success"
                ]
                for row in task_rows
            ),
            "persistent_median_key_regime_0": statistics.median(
                row["persistent"]["evaluations"]["regime_0"]["full_graph"][
                    "key_accuracy"
                ]
                for row in task_rows
            ),
            "persistent_median_key_regime_1": statistics.median(
                row["persistent"]["evaluations"]["regime_1"]["full_graph"][
                    "key_accuracy"
                ]
                for row in task_rows
            ),
            "persistent_higher_joint_regime_0_task_count": sum(
                row["persistent"]["evaluations"]["regime_0"]["full_graph"][
                    "joint_success"
                ]
                > row["transition_reset"]["evaluations"]["regime_0"][
                    "full_graph"
                ]["joint_success"]
                for row in task_rows
            ),
            "persistent_higher_joint_regime_1_task_count": sum(
                row["persistent"]["evaluations"]["regime_1"]["full_graph"][
                    "joint_success"
                ]
                > row["transition_reset"]["evaluations"]["regime_1"][
                    "full_graph"
                ]["joint_success"]
                for row in task_rows
            ),
            "persistent_median_joint_ablation_drop": statistics.median(
                ablation_drops
            ),
            "maximum_total_proposals_observed": max(
                channel["total_proposal_count"]
                for row in task_rows
                for arm in ("persistent", "transition_reset")
                for channel in row[arm]["channels"].values()
            ),
            "maximum_live_candidates_observed": max(
                channel["max_observed_live_candidate_count"]
                for row in task_rows
                for arm in ("persistent", "transition_reset")
                for channel in row[arm]["channels"].values()
            ),
            "total_graph_or_update_mismatch_count": sum(
                row[arm]["selection_update_mismatch_count"]
                + sum(
                    channel["graph_prediction_mismatch_count"]
                    for channel in row[arm]["channels"].values()
                )
                for row in task_rows
                for arm in ("persistent", "transition_reset")
            ),
            "total_trial_root_edge_count": sum(
                channel["trial_root_edge_count"]
                for row in task_rows
                for arm in ("persistent", "transition_reset")
                for channel in row[arm]["channels"].values()
            ),
            "identical_configured_budget_task_count": sum(
                row["persistent"]["training_episode_count"]
                == row["transition_reset"]["training_episode_count"]
                and row["persistent"]["evaluation_episode_count"]
                == row["transition_reset"]["evaluation_episode_count"]
                and row["persistent"]["rng_call_count"]
                == row["transition_reset"]["rng_call_count"]
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
        "predecessor_runner_sha256": _file_hash(PREDECESSOR_RUNNER),
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
