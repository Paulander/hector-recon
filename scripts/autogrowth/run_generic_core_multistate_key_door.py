#!/usr/bin/env python3
"""Run the once-frozen anonymous multi-state key-door experiment."""

from __future__ import annotations

import argparse
from collections import Counter
from dataclasses import asdict
import hashlib
import json
from pathlib import Path
import random
import statistics
import subprocess

from recon_lite import (
    EpisodicCompositionConfig,
    EpisodicCompositionPolicy,
    OnlineCompositionConfig,
)


DEFAULT_OUTPUT = Path(
    "reports/autogrowth/generic_core/"
    "multistate_key_door_20260712.json"
)
SEEDS = tuple(range(20261001, 20261021))
TRAIN_PER_REGIME = 4096
EVALUATION_PER_REGIME = 512
PROBABILITIES = (0.25, 0.35, 0.65, 0.75)


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


def _make_task(seed: int) -> dict[str, object]:
    rng = random.Random(seed)
    terminal_ids = [f"anonymous_terminal_{index:02d}" for index in range(18)]
    rng.shuffle(terminal_ids)
    key_literals = tuple(
        (terminal_ids[2 * index], terminal_ids[2 * index + 1])
        for index in range(4)
    )
    carried_ids = (terminal_ids[8], terminal_ids[9])
    door_cue_literals = (terminal_ids[10], terminal_ids[11])
    door_nuisance_literals = (
        (terminal_ids[12], terminal_ids[13]),
        (terminal_ids[14], terminal_ids[15]),
    )
    regime_ids = (terminal_ids[16], terminal_ids[17])
    action_ids = [f"anonymous_action_{index}" for index in range(4)]
    rng.shuffle(action_ids)
    key_action_ids = tuple(sorted(action_ids[:2]))
    door_action_ids = tuple(sorted(action_ids[2:]))
    key_index_by_action = {
        action_id: index for index, action_id in enumerate(action_ids[:2])
    }
    door_index_by_action = {
        action_id: index for index, action_id in enumerate(action_ids[2:])
    }
    key_inverted = bool(rng.getrandbits(1))
    door_inverted = bool(rng.getrandbits(1))
    key_probabilities = tuple(rng.choice(PROBABILITIES) for _ in range(4))
    door_probabilities = tuple(rng.choice(PROBABILITIES) for _ in range(3))

    def make_rows(regime: int, count: int) -> tuple[dict[str, object], ...]:
        rows = []
        for _ in range(count):
            key_bits = tuple(
                int(rng.random() < probability)
                for probability in key_probabilities
            )
            door_bits = tuple(
                int(rng.random() < probability)
                for probability in door_probabilities
            )
            key_active = tuple(
                sorted(
                    key_literals[index][bit]
                    for index, bit in enumerate(key_bits)
                )
            )
            correct_key_index = int(
                bool(key_bits[0] ^ key_bits[1]) ^ key_inverted
            )
            correct_door_index = int(
                bool(door_bits[0]) ^ bool(regime) ^ door_inverted
            )
            rows.append({
                "key_active_terminal_ids": key_active,
                "door_cue_bit": door_bits[0],
                "door_nuisance_bits": door_bits[1:],
                "regime": regime,
                "correct_key_index": correct_key_index,
                "correct_door_index": correct_door_index,
            })
        return tuple(rows)

    train_regime_0 = make_rows(0, TRAIN_PER_REGIME)
    train_regime_1 = make_rows(1, TRAIN_PER_REGIME)
    evaluation_regime_0 = make_rows(0, EVALUATION_PER_REGIME)
    evaluation_regime_1 = make_rows(1, EVALUATION_PER_REGIME)
    return {
        "seed": seed,
        "key_literals": key_literals,
        "carried_ids": carried_ids,
        "door_cue_literals": door_cue_literals,
        "door_nuisance_literals": door_nuisance_literals,
        "regime_ids": regime_ids,
        "all_action_ids": tuple(sorted(action_ids)),
        "key_action_ids": key_action_ids,
        "door_action_ids": door_action_ids,
        "key_index_by_action": key_index_by_action,
        "door_index_by_action": door_index_by_action,
        "key_inverted": key_inverted,
        "door_inverted": door_inverted,
        "train_regime_0": train_regime_0,
        "train_regime_1": train_regime_1,
        "evaluation_regime_0": evaluation_regime_0,
        "evaluation_regime_1": evaluation_regime_1,
        "train_regime_0_sha256": _hash_json(train_regime_0),
        "train_regime_1_sha256": _hash_json(train_regime_1),
        "evaluation_regime_0_sha256": _hash_json(evaluation_regime_0),
        "evaluation_regime_1_sha256": _hash_json(evaluation_regime_1),
    }


def _door_observation(
    task: dict[str, object],
    row: dict[str, object],
    selected_key_action: str,
) -> tuple[str, ...]:
    key_index = task["key_index_by_action"][selected_key_action]
    atoms = [
        task["carried_ids"][key_index],
        task["door_cue_literals"][row["door_cue_bit"]],
        task["regime_ids"][row["regime"]],
    ]
    atoms.extend(
        task["door_nuisance_literals"][index][bit]
        for index, bit in enumerate(row["door_nuisance_bits"])
    )
    return tuple(sorted(atoms))


def _correct_actions(
    task: dict[str, object], row: dict[str, object]
) -> tuple[str, str]:
    key_action = next(
        action_id
        for action_id, index in task["key_index_by_action"].items()
        if index == row["correct_key_index"]
    )
    door_action = next(
        action_id
        for action_id, index in task["door_index_by_action"].items()
        if index == row["correct_door_index"]
    )
    return key_action, door_action


def _train_arm(
    *,
    task: dict[str, object],
    clear_at_transition: bool,
    random_seed: int,
    policy_config: EpisodicCompositionConfig,
    composition_config: OnlineCompositionConfig,
) -> EpisodicCompositionPolicy:
    policy = EpisodicCompositionPolicy(
        task["all_action_ids"],
        random_seed=random_seed,
        config=policy_config,
        composition_config=composition_config,
    )
    for phase in ("train_regime_0", "train_regime_1"):
        for row in task[phase]:
            policy.begin_episode()
            key_action = policy.choose(
                row["key_active_terminal_ids"],
                legal_action_ids=task["key_action_ids"],
            )
            policy.real_step(clear_trace=clear_at_transition)
            door_action = policy.choose(
                _door_observation(task, row, key_action),
                legal_action_ids=task["door_action_ids"],
            )
            correct_key, correct_door = _correct_actions(task, row)
            terminal_return = (
                1.0
                if key_action == correct_key and door_action == correct_door
                else -1.0
            )
            policy.observe_terminal(terminal_return)
    return policy


def _evaluate(
    policy: EpisodicCompositionPolicy,
    task: dict[str, object],
    rows: tuple[dict[str, object], ...],
    *,
    include_mature_composites: bool,
) -> dict[str, float]:
    key_correct = door_correct = joint_correct = 0
    for row in rows:
        key_action = policy.greedy_action(
            row["key_active_terminal_ids"],
            include_mature_composites=include_mature_composites,
            legal_action_ids=task["key_action_ids"],
        )
        door_action = policy.greedy_action(
            _door_observation(task, row, key_action),
            include_mature_composites=include_mature_composites,
            legal_action_ids=task["door_action_ids"],
        )
        correct_key, correct_door = _correct_actions(task, row)
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


def _candidate_diagnostics(
    policy: EpisodicCompositionPolicy,
    task: dict[str, object],
) -> dict[str, object]:
    key_left, key_right = map(set, task["key_literals"][:2])
    cue = set(task["door_cue_literals"])
    regime = set(task["regime_ids"])
    channels = {}
    for action_id, channel in policy.channels.items():
        candidates = []
        for candidate in channel.learner.candidates:
            members = set(candidate.members)
            row = asdict(candidate)
            row["hidden_key_signal_pair"] = (
                bool(members & key_left) and bool(members & key_right)
            )
            row["hidden_door_cue_regime_pair"] = (
                bool(members & cue) and bool(members & regime)
            )
            candidates.append(row)
        channels[action_id] = {
            "candidate_count": len(candidates),
            "state_counts": dict(
                Counter(candidate["state"] for candidate in candidates)
            ),
            "graph_node_count": len(channel.graph.nodes),
            "graph_edge_count": len(channel.graph.edges),
            "graph_prediction_count": channel.graph_prediction_count,
            "graph_prediction_mismatch_count": (
                channel.graph_prediction_mismatch_count
            ),
            "trial_root_edge_count": channel.trial_root_edge_count,
            "candidates": candidates,
        }
    return {
        "channels": channels,
        "mature_hidden_key_signal_pair": any(
            candidate["state"] == "mature"
            and candidate["hidden_key_signal_pair"]
            for channel in channels.values()
            for candidate in channel["candidates"]
        ),
        "mature_hidden_door_cue_regime_pair": any(
            candidate["state"] == "mature"
            and candidate["hidden_door_cue_regime_pair"]
            for channel in channels.values()
            for candidate in channel["candidates"]
        ),
    }


def _arm_result(
    policy: EpisodicCompositionPolicy,
    task: dict[str, object],
    *,
    clear_at_transition: bool,
) -> dict[str, object]:
    evaluations = {}
    for regime in (0, 1):
        rows = task[f"evaluation_regime_{regime}"]
        full = _evaluate(
            policy, task, rows, include_mature_composites=True
        )
        disabled = _evaluate(
            policy, task, rows, include_mature_composites=False
        )
        evaluations[f"regime_{regime}"] = {
            "full_graph": full,
            "composite_disabled": disabled,
            "joint_ablation_drop": (
                full["joint_success"] - disabled["joint_success"]
            ),
        }
    diagnostics = _candidate_diagnostics(policy, task)
    return {
        "clear_at_transition": clear_at_transition,
        "training_episode_count": 2 * TRAIN_PER_REGIME,
        "evaluation_episode_count": 2 * EVALUATION_PER_REGIME,
        "selection_count": policy.selection_count,
        "terminal_return_sum": policy.terminal_return_sum,
        "terminal_count": policy.terminal_count,
        "credited_decision_count": policy.credited_decision_count,
        "terminal_trace_length_counts": dict(
            Counter(policy.terminal_trace_lengths)
        ),
        "rng_call_count": policy.rng_call_count,
        "selection_update_mismatch_count": (
            policy.selection_update_mismatch_count
        ),
        "evaluations": evaluations,
        **diagnostics,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    repo_root = Path(__file__).resolve().parents[2]
    policy_config = EpisodicCompositionConfig(
        exploration_rate=0.15, discount=0.97
    )
    composition_config = OnlineCompositionConfig()
    task_rows = []
    for seed in SEEDS:
        task = _make_task(seed)
        persistent_policy = _train_arm(
            task=task,
            clear_at_transition=False,
            random_seed=seed + 5_000_000,
            policy_config=policy_config,
            composition_config=composition_config,
        )
        reset_policy = _train_arm(
            task=task,
            clear_at_transition=True,
            random_seed=seed + 5_000_000,
            policy_config=policy_config,
            composition_config=composition_config,
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
            "persistent": _arm_result(
                persistent_policy, task, clear_at_transition=False
            ),
            "transition_reset": _arm_result(
                reset_policy, task, clear_at_transition=True
            ),
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
        "schema_version": "recon_multistate_key_door_raw.v1",
        "track": "generic_core_development",
        "confirmation_claimed": False,
        "builder_is_runner": True,
        "adjudication_authority": False,
        "source_commit": _git_commit(repo_root),
        "frozen_contract": (
            "docs/autogrowth/"
            "GENERIC_CORE_MULTISTATE_KEY_DOOR_WORK_PACKAGE_20260712.md"
        ),
        "policy_config": asdict(policy_config),
        "composition_config": asdict(composition_config),
        "frozen_seed_range": [SEEDS[0], SEEDS[-1]],
        "train_per_regime": TRAIN_PER_REGIME,
        "evaluation_per_regime": EVALUATION_PER_REGIME,
        "task_rows": task_rows,
        "task_rows_sha256": _hash_json(task_rows),
        "raw_gate_measurements": {
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
            "persistent_median_joint_ablation_drop": statistics.median(
                ablation_drops
            ),
            "persistent_mature_both_hidden_pair_task_count": sum(
                row["persistent"]["mature_hidden_key_signal_pair"]
                and row["persistent"][
                    "mature_hidden_door_cue_regime_pair"
                ]
                for row in task_rows
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
        "episodic_implementation_sha256": _file_hash(
            repo_root / "libs/recon-lite/src/recon_lite/episodic_composition.py"
        ),
        "composition_implementation_sha256": _file_hash(
            repo_root / "libs/recon-lite/src/recon_lite/online_composition.py"
        ),
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
