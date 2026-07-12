#!/usr/bin/env python3
"""Run the fresh-seed robust estimator repair experiment once."""

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
    GraphBackedRobustActionPolicy,
    RobustActionPolicyConfig,
    RobustReturnConfig,
)
from scripts.autogrowth.run_generic_core_robust_graph_choice import (
    _response_stream,
    _return_for,
)


DEFAULT_OUTPUT = Path(
    "reports/autogrowth/generic_core/"
    "robust_estimator_repair_fresh_20260712.json"
)
SEEDS = tuple(range(20260901, 20260921))
TRAIN_EPISODES = 2048
EVALUATION_EPISODES = 512


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
    action_ids = ["anonymous_action_0", "anonymous_action_1"]
    rng.shuffle(action_ids)
    refutable_action_id, consistent_action_id = action_ids
    train_responses = _response_stream(rng, TRAIN_EPISODES)
    evaluation_responses = _response_stream(rng, EVALUATION_EPISODES)
    return {
        "seed": seed,
        "action_ids": tuple(sorted(action_ids)),
        "refutable_action_id": refutable_action_id,
        "consistent_action_id": consistent_action_id,
        "train_responses": train_responses,
        "evaluation_responses": evaluation_responses,
        "train_responses_sha256": _hash_json(train_responses),
        "evaluation_responses_sha256": _hash_json(evaluation_responses),
    }


def _action_measurements(
    policy: GraphBackedRobustActionPolicy,
) -> dict[str, dict[str, object]]:
    measurements = {}
    for action_id in policy.action_ids:
        state = policy.memory.states.get(action_id)
        row = asdict(policy.memory.estimate(action_id))
        row["exact_return_sum"] = 0.0 if state is None else state.return_sum
        row["return_sum_compensation"] = (
            0.0 if state is None else state.return_sum_compensation
        )
        row["retained_returns"] = [] if state is None else list(state.returns)
        row["graph_score"] = policy.score(action_id)
        measurements[action_id] = row
    return measurements


def _run_arm(
    *,
    objective: str,
    task: dict[str, object],
    random_seed: int,
    policy_config: RobustActionPolicyConfig,
    return_config: RobustReturnConfig,
) -> dict[str, object]:
    policy = GraphBackedRobustActionPolicy(
        task["action_ids"],
        objective=objective,
        random_seed=random_seed,
        config=policy_config,
        return_config=return_config,
    )
    for response in task["train_responses"]:
        action_id = policy.choose(explore=True)
        policy.observe(
            action_id,
            _return_for(
                action_id,
                refutable_action_id=task["refutable_action_id"],
                refutable_response=response,
            ),
        )

    final_action = policy.greedy_action()
    evaluation_actions = []
    evaluation_returns = []
    for response in task["evaluation_responses"]:
        action_id = policy.greedy_action()
        evaluation_actions.append(action_id)
        evaluation_returns.append(
            _return_for(
                action_id,
                refutable_action_id=task["refutable_action_id"],
                refutable_response=response,
            )
        )
    action_measurements = _action_measurements(policy)
    return {
        "objective": objective,
        "training_episode_count": TRAIN_EPISODES,
        "evaluation_episode_count": EVALUATION_EPISODES,
        "training_selection_count": dict(policy.selection_count),
        "observed_return_count": policy.observed_return_count,
        "rng_call_count": policy.rng_call_count,
        "graph_prediction_count": policy.graph_prediction_count,
        "graph_prediction_mismatch_count": (
            policy.graph_prediction_mismatch_count
        ),
        "final_greedy_action_id": final_action,
        "evaluation_selection_count": dict(Counter(evaluation_actions)),
        "evaluation_mean_return": statistics.mean(evaluation_returns),
        "evaluation_minimum_return": min(evaluation_returns),
        "evaluation_refutation_count": sum(
            value == -1.0 for value in evaluation_returns
        ),
        "action_measurements": action_measurements,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    repo_root = Path(__file__).resolve().parents[2]
    policy_config = RobustActionPolicyConfig(exploration_rate=0.15)
    return_config = RobustReturnConfig(
        capacity=256,
        lower_quantile=0.10,
        min_observations=8,
        confidence_prior=3.0,
    )
    task_rows = []
    for seed in SEEDS:
        task = _make_task(seed)
        mean_arm = _run_arm(
            objective="mean",
            task=task,
            random_seed=seed + 4_000_000,
            policy_config=policy_config,
            return_config=return_config,
        )
        lower_tail = _run_arm(
            objective="lower_tail",
            task=task,
            random_seed=seed + 4_000_000,
            policy_config=policy_config,
            return_config=return_config,
        )
        task_rows.append({
            "seed": seed,
            "action_ids": task["action_ids"],
            "refutable_action_id": task["refutable_action_id"],
            "consistent_action_id": task["consistent_action_id"],
            "train_responses_sha256": task["train_responses_sha256"],
            "evaluation_responses_sha256": task[
                "evaluation_responses_sha256"
            ],
            "mean": mean_arm,
            "lower_tail": lower_tail,
        })

    payload = {
        "schema_version": "recon_robust_estimator_repair_raw.v1",
        "track": "generic_core_development",
        "confirmation_claimed": False,
        "builder_is_runner": True,
        "adjudication_authority": False,
        "source_commit": _git_commit(repo_root),
        "frozen_contract": (
            "docs/autogrowth/"
            "GENERIC_CORE_ROBUST_ESTIMATOR_REPAIR_WORK_PACKAGE_20260712.md"
        ),
        "predecessor_artifact": (
            "reports/autogrowth/generic_core/"
            "robust_graph_choice_rare_refutation_20260712.json"
        ),
        "policy_config": asdict(policy_config),
        "return_config": asdict(return_config),
        "frozen_seed_range": [SEEDS[0], SEEDS[-1]],
        "train_episodes": TRAIN_EPISODES,
        "evaluation_episodes": EVALUATION_EPISODES,
        "task_rows": task_rows,
        "task_rows_sha256": _hash_json(task_rows),
        "raw_gate_measurements": {
            "mean_refutable_action_task_count": sum(
                row["mean"]["final_greedy_action_id"]
                == row["refutable_action_id"]
                for row in task_rows
            ),
            "lower_tail_consistent_action_task_count": sum(
                row["lower_tail"]["final_greedy_action_id"]
                == row["consistent_action_id"]
                for row in task_rows
            ),
            "lower_tail_higher_minimum_return_task_count": sum(
                row["lower_tail"]["evaluation_minimum_return"]
                > row["mean"]["evaluation_minimum_return"]
                for row in task_rows
            ),
            "refutable_exact_mean_within_tolerance_task_count": sum(
                abs(
                    row["mean"]["action_measurements"][
                        row["refutable_action_id"]
                    ]["mean"]
                    - 0.75
                ) <= 0.10
                for row in task_rows
            ),
            "total_graph_prediction_mismatch_count": sum(
                row[arm]["graph_prediction_mismatch_count"]
                for row in task_rows
                for arm in ("mean", "lower_tail")
            ),
            "identical_budget_task_count": sum(
                row["mean"]["training_episode_count"]
                == row["lower_tail"]["training_episode_count"]
                and row["mean"]["evaluation_episode_count"]
                == row["lower_tail"]["evaluation_episode_count"]
                and row["mean"]["rng_call_count"]
                == row["lower_tail"]["rng_call_count"]
                for row in task_rows
            ),
            "task_count": len(task_rows),
        },
        "return_implementation_sha256": _file_hash(
            repo_root / "libs/recon-lite/src/recon_lite/robust_return.py"
        ),
        "policy_implementation_sha256": _file_hash(
            repo_root / "libs/recon-lite/src/recon_lite/robust_policy.py"
        ),
        "environment_helper_sha256": _file_hash(
            repo_root
            / "scripts/autogrowth/run_generic_core_robust_graph_choice.py"
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
