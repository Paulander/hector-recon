#!/usr/bin/env python3
"""Run the once-frozen graph-backed delayed action-policy experiment."""

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
    "delayed_action_policy_anonymous_xor_20260712.json"
)
SEEDS = tuple(range(20260801, 20260821))
TRAIN_EPISODES = 4096
EVALUATION_EPISODES = 512
INTERVENING_STEPS = 4
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
    atom_ids = [f"anonymous_terminal_{index:02d}" for index in range(12)]
    rng.shuffle(atom_ids)
    literal_ids = tuple(
        (atom_ids[2 * index], atom_ids[2 * index + 1]) for index in range(6)
    )
    action_ids = ["anonymous_action_0", "anonymous_action_1"]
    rng.shuffle(action_ids)
    probabilities = tuple(rng.choice(PROBABILITIES) for _ in range(6))
    target_inverted = bool(rng.getrandbits(1))

    def make_rows(count: int) -> tuple[dict[str, object], ...]:
        rows = []
        for _ in range(count):
            bits = tuple(
                int(rng.random() < probability) for probability in probabilities
            )
            active = tuple(
                sorted(literal_ids[index][bit] for index, bit in enumerate(bits))
            )
            action_index = int(bool(bits[0] ^ bits[1]) ^ target_inverted)
            rows.append({
                "active_terminal_ids": active,
                "correct_action_id": action_ids[action_index],
            })
        return tuple(rows)

    train_rows = make_rows(TRAIN_EPISODES)
    evaluation_rows = make_rows(EVALUATION_EPISODES)
    return {
        "seed": seed,
        "literal_ids": literal_ids,
        "signal_literal_sets": (literal_ids[0], literal_ids[1]),
        "action_ids": tuple(sorted(action_ids)),
        "probabilities": probabilities,
        "target_inverted": target_inverted,
        "train_rows": train_rows,
        "evaluation_rows": evaluation_rows,
        "train_rows_sha256": _hash_json(train_rows),
        "evaluation_rows_sha256": _hash_json(evaluation_rows),
    }


def _candidate_rows(
    policy: EpisodicCompositionPolicy,
    signal_literal_sets: tuple[tuple[str, str], tuple[str, str]],
) -> dict[str, tuple[dict[str, object], ...]]:
    left_signal, right_signal = map(set, signal_literal_sets)
    result = {}
    for action_id, channel in policy.channels.items():
        rows = []
        for candidate in channel.learner.candidates:
            members = set(candidate.members)
            row = asdict(candidate)
            row["contains_both_hidden_signal_bits"] = (
                bool(members & left_signal) and bool(members & right_signal)
            )
            rows.append(row)
        result[action_id] = tuple(rows)
    return result


def _run_arm(
    *,
    task: dict[str, object],
    clear_trace_each_step: bool,
    random_seed: int,
    policy_config: EpisodicCompositionConfig,
    composition_config: OnlineCompositionConfig,
) -> dict[str, object]:
    policy = EpisodicCompositionPolicy(
        task["action_ids"],
        random_seed=random_seed,
        config=policy_config,
        composition_config=composition_config,
    )
    for row in task["train_rows"]:
        policy.begin_episode()
        action_id = policy.choose(row["active_terminal_ids"], explore=True)
        for _ in range(INTERVENING_STEPS):
            policy.real_step(clear_trace=clear_trace_each_step)
        terminal_return = 1.0 if action_id == row["correct_action_id"] else -1.0
        policy.observe_terminal(terminal_return)

    full_correct = 0
    disabled_correct = 0
    for row in task["evaluation_rows"]:
        full_correct += int(
            policy.greedy_action(row["active_terminal_ids"])
            == row["correct_action_id"]
        )
        disabled_correct += int(
            policy.greedy_action(
                row["active_terminal_ids"],
                include_mature_composites=False,
            )
            == row["correct_action_id"]
        )

    candidates = _candidate_rows(policy, task["signal_literal_sets"])
    channel_rows = {}
    for action_id, channel in policy.channels.items():
        action_candidates = candidates[action_id]
        channel_rows[action_id] = {
            "candidate_count": len(action_candidates),
            "candidate_state_counts": dict(
                Counter(candidate["state"] for candidate in action_candidates)
            ),
            "mature_hidden_signal_pair_count": sum(
                candidate["state"] == "mature"
                and candidate["contains_both_hidden_signal_bits"]
                for candidate in action_candidates
            ),
            "graph_node_count": len(channel.graph.nodes),
            "graph_edge_count": len(channel.graph.edges),
            "graph_prediction_count": channel.graph_prediction_count,
            "graph_prediction_mismatch_count": (
                channel.graph_prediction_mismatch_count
            ),
            "trial_root_edge_count": channel.trial_root_edge_count,
            "candidates": action_candidates,
        }
    return {
        "clear_trace_each_step": clear_trace_each_step,
        "training_episode_count": TRAIN_EPISODES,
        "evaluation_episode_count": EVALUATION_EPISODES,
        "final_full_graph_accuracy": full_correct / EVALUATION_EPISODES,
        "final_composite_disabled_accuracy": (
            disabled_correct / EVALUATION_EPISODES
        ),
        "full_minus_composite_disabled_accuracy": (
            full_correct - disabled_correct
        ) / EVALUATION_EPISODES,
        "selection_count": policy.selection_count,
        "terminal_return_sum": policy.terminal_return_sum,
        "terminal_count": policy.terminal_count,
        "credited_decision_count": policy.credited_decision_count,
        "terminal_trace_length_counts": dict(Counter(policy.terminal_trace_lengths)),
        "selection_update_mismatch_count": (
            policy.selection_update_mismatch_count
        ),
        "channels": channel_rows,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    repo_root = Path(__file__).resolve().parents[2]
    policy_config = EpisodicCompositionConfig(
        exploration_rate=0.15,
        discount=0.97,
    )
    composition_config = OnlineCompositionConfig()
    task_rows = []
    for seed in SEEDS:
        task = _make_task(seed)
        persistent = _run_arm(
            task=task,
            clear_trace_each_step=False,
            random_seed=seed + 2_000_000,
            policy_config=policy_config,
            composition_config=composition_config,
        )
        reset = _run_arm(
            task=task,
            clear_trace_each_step=True,
            random_seed=seed + 2_000_000,
            policy_config=policy_config,
            composition_config=composition_config,
        )
        task_rows.append({
            "seed": seed,
            "literal_ids": task["literal_ids"],
            "signal_literal_sets": task["signal_literal_sets"],
            "action_ids": task["action_ids"],
            "probabilities": task["probabilities"],
            "target_inverted": task["target_inverted"],
            "train_rows_sha256": task["train_rows_sha256"],
            "evaluation_rows_sha256": task["evaluation_rows_sha256"],
            "persistent_trace": persistent,
            "per_step_reset": reset,
        })

    def arm_total(row: dict[str, object], arm: str, field: str) -> int:
        return sum(
            channel[field] for channel in row[arm]["channels"].values()
        )

    payload = {
        "schema_version": "recon_generic_delayed_action_policy_raw.v1",
        "track": "generic_core_development",
        "confirmation_claimed": False,
        "builder_is_runner": True,
        "adjudication_authority": False,
        "source_commit": _git_commit(repo_root),
        "frozen_contract": (
            "docs/autogrowth/"
            "GENERIC_CORE_DELAYED_ACTION_POLICY_WORK_PACKAGE_20260712.md"
        ),
        "policy_config": asdict(policy_config),
        "composition_config": asdict(composition_config),
        "frozen_seed_range": [SEEDS[0], SEEDS[-1]],
        "train_episodes": TRAIN_EPISODES,
        "evaluation_episodes": EVALUATION_EPISODES,
        "intervening_steps": INTERVENING_STEPS,
        "task_rows": task_rows,
        "task_rows_sha256": _hash_json(task_rows),
        "raw_gate_measurements": {
            "persistent_higher_accuracy_task_count": sum(
                row["persistent_trace"]["final_full_graph_accuracy"]
                > row["per_step_reset"]["final_full_graph_accuracy"]
                for row in task_rows
            ),
            "task_count": len(task_rows),
            "persistent_median_full_graph_accuracy": statistics.median(
                row["persistent_trace"]["final_full_graph_accuracy"]
                for row in task_rows
            ),
            "persistent_median_composite_ablation_drop": statistics.median(
                row["persistent_trace"][
                    "full_minus_composite_disabled_accuracy"
                ]
                for row in task_rows
            ),
            "persistent_mature_signal_pair_task_count": sum(
                arm_total(
                    row,
                    "persistent_trace",
                    "mature_hidden_signal_pair_count",
                ) > 0
                for row in task_rows
            ),
            "total_graph_prediction_mismatch_count": sum(
                arm_total(row, arm, "graph_prediction_mismatch_count")
                + row[arm]["selection_update_mismatch_count"]
                for row in task_rows
                for arm in ("persistent_trace", "per_step_reset")
            ),
            "total_trial_root_edge_count": sum(
                arm_total(row, arm, "trial_root_edge_count")
                for row in task_rows
                for arm in ("persistent_trace", "per_step_reset")
            ),
            "identical_configured_budget_task_count": sum(
                row["persistent_trace"]["training_episode_count"]
                == row["per_step_reset"]["training_episode_count"]
                and row["persistent_trace"]["evaluation_episode_count"]
                == row["per_step_reset"]["evaluation_episode_count"]
                for row in task_rows
            ),
        },
        "implementation_sha256": _file_hash(
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
