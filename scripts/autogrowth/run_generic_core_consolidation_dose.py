#!/usr/bin/env python3
"""Run the once-frozen generic-core consolidation-dose experiment."""

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
    "consolidation_dose_key_door_20260712.json"
)
SEEDS = tuple(range(20261401, 20261421))
SCALES = (0.10, 0.25, 0.50, 1.00)
KEY_DOOR_RUNNER = Path(__file__).with_name(
    "run_generic_core_multistate_key_door.py"
)
RENEWABLE_RUNNER = Path(__file__).with_name(
    "run_generic_core_renewable_topology.py"
)
CONSOLIDATION_RUNNER = Path(__file__).with_name(
    "run_generic_core_local_consolidation.py"
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


def _arm_name(scale: float) -> str:
    return f"scale_{scale:.2f}".replace(".", "_")


def _task_manifest(task: dict[str, object]) -> dict[str, object]:
    keys = (
        "key_literals",
        "carried_ids",
        "door_cue_literals",
        "door_nuisance_literals",
        "regime_ids",
        "key_action_ids",
        "door_action_ids",
        "key_index_by_action",
        "door_index_by_action",
        "key_inverted",
        "door_inverted",
        "train_regime_0_sha256",
        "train_regime_1_sha256",
        "evaluation_regime_0_sha256",
        "evaluation_regime_1_sha256",
    )
    return {key: task[key] for key in keys}


def _arms_have_identical_budget(
    row: dict[str, object],
    arm_names: tuple[str, ...],
) -> bool:
    if not arm_names:
        return False
    reference = row["arms"][arm_names[0]]
    fields = (
        "training_episode_count",
        "evaluation_episode_count",
        "selection_count",
        "rng_call_count",
    )
    return all(
        all(
            row["arms"][arm][field] == reference[field]
            for field in fields
        )
        for arm in arm_names[1:]
    )


def _median(rows: list[dict[str, object]], arm: str, metric: str, regime: int) -> float:
    return statistics.median(
        row["arms"][arm]["evaluations"][f"regime_{regime}"]["full_graph"][
            metric
        ]
        for row in rows
    )


def _dose_summary(
    rows: list[dict[str, object]],
    arm: str,
    control_arm: str,
) -> dict[str, object]:
    regime_0_joint = _median(rows, arm, "joint_success", 0)
    regime_1_joint = _median(rows, arm, "joint_success", 1)
    control_regime_1_joint = _median(rows, control_arm, "joint_success", 1)
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
        "median_joint_regime_0": regime_0_joint,
        "median_joint_regime_1": regime_1_joint,
        "median_key_regime_0": _median(rows, arm, "key_accuracy", 0),
        "median_key_regime_1": _median(rows, arm, "key_accuracy", 1),
        "higher_old_joint_than_control_task_count": sum(
            row["arms"][arm]["evaluations"]["regime_0"]["full_graph"][
                "joint_success"
            ]
            > row["arms"][control_arm]["evaluations"]["regime_0"][
                "full_graph"
            ]["joint_success"]
            for row in rows
        ),
        "control_minus_dose_new_joint_median": (
            control_regime_1_joint - regime_1_joint
        ),
        "mature_regime_1_pair_task_count": sum(
            row["arms"][arm]["mature_door_cue_regime_1"]
            for row in rows
        ),
        "median_joint_ablation_drop": statistics.median(ablation_drops),
        "all_tasks_have_matured_channel": all(
            row["arms"][arm]["matured_channel_count"] > 0 for row in rows
        ),
        "all_tasks_have_candidate_updates_after_maturity": all(
            row["arms"][arm]["matured_channels_with_candidate_updates"] > 0
            for row in rows
        ),
        "all_tasks_have_shared_updates_after_maturity": all(
            sum(
                channel["shared_update_events_after_maturity"]
                for channel in row["arms"][arm]["channels"].values()
            )
            > 0
            for row in rows
        ),
        "minimum_of_joint_medians": min(regime_0_joint, regime_1_joint),
        "mean_of_joint_medians": statistics.mean(
            (regime_0_joint, regime_1_joint)
        ),
    }


def _eligible(summary: dict[str, object], invariants_pass: bool) -> bool:
    return all((
        summary["median_joint_regime_0"] >= 0.85,
        summary["median_joint_regime_1"] >= 0.85,
        summary["median_key_regime_0"] >= 0.90,
        summary["median_key_regime_1"] >= 0.90,
        summary["higher_old_joint_than_control_task_count"] >= 16,
        summary["control_minus_dose_new_joint_median"] <= 0.05,
        summary["mature_regime_1_pair_task_count"] >= 16,
        summary["median_joint_ablation_drop"] >= 0.15,
        summary["all_tasks_have_matured_channel"],
        summary["all_tasks_have_candidate_updates_after_maturity"],
        summary["all_tasks_have_shared_updates_after_maturity"],
        invariants_pass,
    ))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    repo_root = Path(__file__).resolve().parents[2]
    key_door = runpy.run_path(str(KEY_DOOR_RUNNER))
    renewable = runpy.run_path(str(RENEWABLE_RUNNER))
    consolidation = runpy.run_path(str(CONSOLIDATION_RUNNER))
    make_task = key_door["_make_task"]
    train_arm = key_door["_train_arm"]
    arm_result = key_door["_arm_result"]
    enrich_arm = renewable["_enrich_arm"]
    add_consolidation_metrics = consolidation[
        "_add_consolidation_metrics"
    ]
    policy_config = EpisodicCompositionConfig(
        exploration_rate=0.15,
        discount=0.97,
    )
    composition_configs = {
        _arm_name(scale): OnlineCompositionConfig(
            max_total_proposals=64,
            shared_learning_after_maturity_scale=scale,
        )
        for scale in SCALES
    }
    task_rows = []
    for task_index, seed in enumerate(SEEDS, start=1):
        task = make_task(seed)
        arms = {}
        for arm, composition_config in composition_configs.items():
            policy = train_arm(
                task=task,
                clear_at_transition=False,
                random_seed=seed + 8_000_000,
                policy_config=policy_config,
                composition_config=composition_config,
            )
            arms[arm] = add_consolidation_metrics(
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
        task_rows.append({
            "seed": seed,
            **_task_manifest(task),
            "arms": arms,
        })
        print(f"completed task {task_index}/{len(SEEDS)}", flush=True)

    arm_names = tuple(composition_configs)
    control_arm = _arm_name(1.0)
    maximum_total_proposals = max(
        channel["total_proposal_count"]
        for row in task_rows
        for arm in arm_names
        for channel in row["arms"][arm]["channels"].values()
    )
    maximum_live_candidates = max(
        channel["max_observed_live_candidate_count"]
        for row in task_rows
        for arm in arm_names
        for channel in row["arms"][arm]["channels"].values()
    )
    mismatch_count = sum(
        row["arms"][arm]["selection_update_mismatch_count"]
        + sum(
            channel["graph_prediction_mismatch_count"]
            for channel in row["arms"][arm]["channels"].values()
        )
        for row in task_rows
        for arm in arm_names
    )
    trial_root_edges = sum(
        channel["trial_root_edge_count"]
        for row in task_rows
        for arm in arm_names
        for channel in row["arms"][arm]["channels"].values()
    )
    identical_budget_tasks = sum(
        _arms_have_identical_budget(row, arm_names)
        for row in task_rows
    )
    invariants = {
        "maximum_total_proposals_observed": maximum_total_proposals,
        "maximum_live_candidates_observed": maximum_live_candidates,
        "total_graph_or_update_mismatch_count": mismatch_count,
        "total_trial_root_edge_count": trial_root_edges,
        "identical_experience_action_rng_budget_task_count": (
            identical_budget_tasks
        ),
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
        arm: _dose_summary(task_rows, arm, control_arm)
        for arm in arm_names
    }
    eligible_arms = [
        _arm_name(scale)
        for scale in SCALES
        if scale < 1.0
        and _eligible(summaries[_arm_name(scale)], invariants_pass)
    ]
    selected_arm = (
        max(
            eligible_arms,
            key=lambda arm: (
                summaries[arm]["minimum_of_joint_medians"],
                summaries[arm]["mean_of_joint_medians"],
                composition_configs[
                    arm
                ].shared_learning_after_maturity_scale,
            ),
        )
        if eligible_arms
        else None
    )
    payload = {
        "schema_version": "recon_consolidation_dose_raw.v1",
        "track": "generic_core_development",
        "confirmation_claimed": False,
        "builder_is_runner": True,
        "adjudication_authority": False,
        "source_commit": _git_commit(repo_root),
        "frozen_contract": (
            "docs/autogrowth/"
            "GENERIC_CORE_CONSOLIDATION_DOSE_WORK_PACKAGE_20260712.md"
        ),
        "repair_contract": (
            "docs/autogrowth/"
            "GENERIC_CORE_CONSOLIDATION_DOSE_REPAIR_WORK_PACKAGE_20260712.md"
        ),
        "predecessor_artifact": (
            "reports/autogrowth/generic_core/"
            "local_consolidation_key_door_20260712.json"
        ),
        "policy_config": asdict(policy_config),
        "composition_configs": {
            arm: asdict(config)
            for arm, config in composition_configs.items()
        },
        "frozen_seed_range": [SEEDS[0], SEEDS[-1]],
        "task_rows": task_rows,
        "task_rows_sha256": _hash_json(task_rows),
        "dose_summaries": summaries,
        "invariants": invariants,
        "invariants_pass": invariants_pass,
        "eligible_arms": eligible_arms,
        "selected_arm": selected_arm,
        "selected_scale": (
            composition_configs[
                selected_arm
            ].shared_learning_after_maturity_scale
            if selected_arm is not None
            else None
        ),
        "composition_implementation_sha256": _file_hash(
            repo_root / "libs/recon-lite/src/recon_lite/online_composition.py"
        ),
        "episodic_implementation_sha256": _file_hash(
            repo_root / "libs/recon-lite/src/recon_lite/episodic_composition.py"
        ),
        "key_door_runner_sha256": _file_hash(KEY_DOOR_RUNNER),
        "renewable_runner_sha256": _file_hash(RENEWABLE_RUNNER),
        "consolidation_runner_sha256": _file_hash(CONSOLIDATION_RUNNER),
        "runner_sha256": _file_hash(Path(__file__)),
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(args.output)
    print(json.dumps({
        "dose_summaries": summaries,
        "eligible_arms": eligible_arms,
        "invariants": invariants,
        "invariants_pass": invariants_pass,
        "selected_arm": selected_arm,
        "selected_scale": payload["selected_scale"],
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
