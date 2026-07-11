#!/usr/bin/env python3
"""Run the once-frozen anonymous online-composition development experiment."""

from __future__ import annotations

import argparse
from dataclasses import asdict
import hashlib
import json
from pathlib import Path
import random
import statistics
import subprocess
from typing import Iterable

from recon_lite import OnlineCompositionConfig, OnlinePairCompositionLearner


DEFAULT_OUTPUT = Path(
    "reports/autogrowth/generic_core/"
    "online_composition_anonymous_xor_20260712.json"
)
SEEDS = tuple(range(20260712, 20260732))
TRAIN_SIZE = 2048
EVALUATION_SIZE = 512
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
    atom_ids = [f"anonymous_atom_{index:02d}" for index in range(12)]
    rng.shuffle(atom_ids)
    literal_ids = tuple(
        (atom_ids[2 * index], atom_ids[2 * index + 1]) for index in range(6)
    )
    probabilities = tuple(rng.choice(PROBABILITIES) for _ in range(6))
    target_inverted = bool(rng.getrandbits(1))

    def make_rows(count: int) -> tuple[dict[str, object], ...]:
        rows: list[dict[str, object]] = []
        for _ in range(count):
            bits = tuple(
                int(rng.random() < probability) for probability in probabilities
            )
            active = tuple(sorted(literal_ids[index][bit] for index, bit in enumerate(bits)))
            positive = bool(bits[0] ^ bits[1]) ^ target_inverted
            rows.append({"active_atom_ids": active, "target": 1.0 if positive else -1.0})
        return tuple(rows)

    train_rows = make_rows(TRAIN_SIZE)
    evaluation_rows = make_rows(EVALUATION_SIZE)
    return {
        "seed": seed,
        "literal_ids": literal_ids,
        "signal_literal_sets": (literal_ids[0], literal_ids[1]),
        "probabilities": probabilities,
        "target_inverted": target_inverted,
        "train_rows": train_rows,
        "evaluation_rows": evaluation_rows,
        "train_rows_sha256": _hash_json(train_rows),
        "evaluation_rows_sha256": _hash_json(evaluation_rows),
    }


def _mean_squared_error(
    learner: OnlinePairCompositionLearner,
    rows: Iterable[dict[str, object]],
) -> float:
    errors = []
    for row in rows:
        prediction = learner.predict(row["active_atom_ids"])
        errors.append((float(row["target"]) - prediction) ** 2)
    return sum(errors) / len(errors)


def _candidate_rows(
    learner: OnlinePairCompositionLearner,
    signal_literal_sets: tuple[tuple[str, str], tuple[str, str]],
) -> tuple[dict[str, object], ...]:
    left_signal, right_signal = map(set, signal_literal_sets)
    rows = []
    for candidate in learner.candidates:
        members = set(candidate.members)
        is_signal_pair = bool(members & left_signal) and bool(members & right_signal)
        row = asdict(candidate)
        row["contains_both_hidden_signal_bits"] = is_signal_pair
        row["disabled_mean_squared_error"] = (
            candidate.disabled_error_sum / candidate.confirmation_count
            if candidate.confirmation_count
            else None
        )
        row["enabled_mean_squared_error"] = (
            candidate.enabled_error_sum / candidate.confirmation_count
            if candidate.confirmation_count
            else None
        )
        rows.append(row)
    return tuple(rows)


def _run_arm(
    *,
    mode: str,
    seed: int,
    rows: tuple[dict[str, object], ...],
    evaluation_rows: tuple[dict[str, object], ...],
    signal_literal_sets: tuple[tuple[str, str], tuple[str, str]],
    config: OnlineCompositionConfig,
) -> dict[str, object]:
    learner = OnlinePairCompositionLearner(
        proposal_mode=mode,
        random_seed=seed + 1_000_000,
        config=config,
    )
    prequential_error_sum = 0.0
    for row in rows:
        prediction = learner.observe(row["active_atom_ids"], float(row["target"]))
        prequential_error_sum += (float(row["target"]) - prediction) ** 2
    candidates = _candidate_rows(learner, signal_literal_sets)
    return {
        "proposal_mode": mode,
        "prequential_train_mse": prequential_error_sum / len(rows),
        "final_evaluation_mse": _mean_squared_error(learner, evaluation_rows),
        "candidate_count": len(candidates),
        "mature_candidate_count": sum(row["state"] == "mature" for row in candidates),
        "mature_hidden_signal_pair": any(
            row["state"] == "mature" and row["contains_both_hidden_signal_bits"]
            for row in candidates
        ),
        "trial_prediction_influence_count": learner.trial_prediction_influence_count,
        "candidates": candidates,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    repo_root = Path(__file__).resolve().parents[2]
    config = OnlineCompositionConfig()
    task_rows: list[dict[str, object]] = []
    for seed in SEEDS:
        task = _make_task(seed)
        signal_sets = task["signal_literal_sets"]
        ranked = _run_arm(
            mode="residual_ranked",
            seed=seed,
            rows=task["train_rows"],
            evaluation_rows=task["evaluation_rows"],
            signal_literal_sets=signal_sets,
            config=config,
        )
        random_arm = _run_arm(
            mode="matched_random",
            seed=seed,
            rows=task["train_rows"],
            evaluation_rows=task["evaluation_rows"],
            signal_literal_sets=signal_sets,
            config=config,
        )
        task_rows.append({
            "seed": seed,
            "literal_ids": task["literal_ids"],
            "signal_literal_sets": signal_sets,
            "probabilities": task["probabilities"],
            "target_inverted": task["target_inverted"],
            "train_rows_sha256": task["train_rows_sha256"],
            "evaluation_rows_sha256": task["evaluation_rows_sha256"],
            "untrained_zero_prediction_mse": 1.0,
            "residual_ranked": ranked,
            "matched_random": random_arm,
            "random_minus_ranked_evaluation_mse": (
                random_arm["final_evaluation_mse"]
                - ranked["final_evaluation_mse"]
            ),
        })

    paired_differences = [
        row["random_minus_ranked_evaluation_mse"] for row in task_rows
    ]
    payload = {
        "schema_version": "recon_generic_online_composition_raw.v1",
        "track": "generic_core_development",
        "confirmation_claimed": False,
        "builder_is_runner": True,
        "adjudication_authority": False,
        "source_commit": _git_commit(repo_root),
        "frozen_contract": (
            "docs/autogrowth/"
            "GENERIC_CORE_ONLINE_COMPOSITION_WORK_PACKAGE_20260712.md"
        ),
        "learner_config": asdict(config),
        "frozen_seed_range": [SEEDS[0], SEEDS[-1]],
        "train_size": TRAIN_SIZE,
        "evaluation_size": EVALUATION_SIZE,
        "task_rows": task_rows,
        "task_rows_sha256": _hash_json(task_rows),
        "raw_gate_measurements": {
            "ranked_lower_evaluation_mse_task_count": sum(
                row["residual_ranked"]["final_evaluation_mse"]
                < row["matched_random"]["final_evaluation_mse"]
                for row in task_rows
            ),
            "task_count": len(task_rows),
            "median_random_minus_ranked_evaluation_mse": statistics.median(
                paired_differences
            ),
            "ranked_mature_hidden_signal_pair_task_count": sum(
                row["residual_ranked"]["mature_hidden_signal_pair"]
                for row in task_rows
            ),
            "total_trial_prediction_influence_count": sum(
                row[arm]["trial_prediction_influence_count"]
                for row in task_rows
                for arm in ("residual_ranked", "matched_random")
            ),
            "identical_actual_candidate_budget_task_count": sum(
                row["residual_ranked"]["candidate_count"]
                == row["matched_random"]["candidate_count"]
                for row in task_rows
            ),
        },
        "implementation_sha256": _file_hash(
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
