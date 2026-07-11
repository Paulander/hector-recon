#!/usr/bin/env python3
"""Emit raw measurements for frozen generic-core development factors."""

from __future__ import annotations

import argparse
from dataclasses import asdict
import hashlib
import json
from pathlib import Path
import random
import subprocess

from recon_lite import RobustReturnConfig, RobustReturnMemory
from recon_lite_hector.learning import (
    IntrinsicCreditConfig,
    IntrinsicCreditEngine,
    Responsibility,
)


DEFAULT_OUTPUT = Path(
    "reports/autogrowth/generic_core/"
    "policy_credit_rare_refutation_delayed_fork_20260712.json"
)


def _hash_json(value: object) -> str:
    encoded = json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(encoded).hexdigest()


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


def _rare_refutation_rows() -> tuple[dict[str, object], ...]:
    config = RobustReturnConfig(
        capacity=32,
        lower_quantile=0.10,
        min_observations=8,
        confidence_prior=3.0,
    )
    rows: list[dict[str, object]] = []
    for seed_index in range(20):
        seed = 20260712 + seed_index
        rng = random.Random(seed)
        identities = [f"anonymous_{seed_index}_a", f"anonymous_{seed_index}_b"]
        rng.shuffle(identities)
        refutable_id, consistent_id = identities
        refutable_returns = [1.0] * 7 + [-1.0]
        consistent_returns = [0.4] * 8
        rng.shuffle(refutable_returns)
        rng.shuffle(consistent_returns)
        memory = RobustReturnMemory(config)
        confidence_before_refutation = None
        for refutable, consistent in zip(
            refutable_returns, consistent_returns, strict=True
        ):
            if refutable < 0.0:
                confidence_before_refutation = memory.estimate(
                    refutable_id
                ).confidence
            memory.observe(refutable_id, refutable)
            memory.observe(consistent_id, consistent)
        rows.append(
            {
                "seed": seed,
                "presented_ids": identities,
                "refutable_id": refutable_id,
                "consistent_id": consistent_id,
                "refutable_returns": refutable_returns,
                "consistent_returns": consistent_returns,
                "confidence_before_refutation": confidence_before_refutation,
                "refutable_estimate": asdict(memory.estimate(refutable_id)),
                "consistent_estimate": asdict(memory.estimate(consistent_id)),
                "mean_selected_id": memory.select(identities, objective="mean"),
                "lower_tail_selected_id": memory.select(
                    identities, objective="lower_tail"
                ),
            }
        )
    return tuple(rows)


def _delayed_episode(
    *,
    early_id: str,
    filler_ids: tuple[str, ...],
    reset_each_step: bool,
) -> dict[str, float]:
    engine = IntrinsicCreditEngine(
        IntrinsicCreditConfig(
            gamma=1.0,
            real_move_cost=0.0,
            eligibility_decay=0.8,
            eta_fast=0.5,
            parent_learning_decay=1.0,
        )
    )
    engine.register(early_id)
    for filler_id in filler_ids:
        engine.register(filler_id)
    terminal_id = f"terminal_{early_id}"
    engine.register(terminal_id)
    engine.begin_episode()
    engine.transition(
        early_id,
        responsibilities=(Responsibility(early_id),),
        prediction_override=0.0,
    )
    for filler_id in filler_ids:
        if reset_each_step:
            engine.begin_episode()
        engine.transition(
            filler_id,
            responsibilities=(Responsibility(filler_id),),
            prediction_override=0.0,
        )
    if reset_each_step:
        engine.begin_episode()
    terminal = engine.transition(
        terminal_id,
        responsibilities=(Responsibility(terminal_id),),
        terminal_value=1.0,
        prediction_override=0.0,
    )
    return {
        "early_fast_value": engine.states[early_id].fast_value,
        "terminal_td_error": terminal.td_error,
    }


def _delayed_fork_rows() -> tuple[dict[str, object], ...]:
    rows: list[dict[str, object]] = []
    for seed_index in range(20):
        seed = 20260712 + seed_index
        rng = random.Random(seed)
        delay = rng.choice((4, 5, 6))
        identities = [f"cell_{seed_index}_{index}" for index in range(delay)]
        rng.shuffle(identities)
        early_id = identities[0]
        filler_ids = tuple(identities[1:-1])
        rows.append(
            {
                "seed": seed,
                "delay": delay,
                "early_id": early_id,
                "filler_ids": filler_ids,
                "persistent_episode": _delayed_episode(
                    early_id=early_id,
                    filler_ids=filler_ids,
                    reset_each_step=False,
                ),
                "per_step_reset_control": _delayed_episode(
                    early_id=early_id,
                    filler_ids=filler_ids,
                    reset_each_step=True,
                ),
            }
        )
    return tuple(rows)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    repo_root = Path(__file__).resolve().parents[2]
    rare_rows = _rare_refutation_rows()
    delayed_rows = _delayed_fork_rows()
    payload = {
        "schema_version": "recon_generic_core_falsification_raw.v1",
        "track": "generic_core_development",
        "confirmation_claimed": False,
        "builder_is_runner": True,
        "adjudication_authority": False,
        "source_commit": _git_commit(repo_root),
        "frozen_seed_range": [20260712, 20260731],
        "rare_refutation": {
            "config": asdict(RobustReturnConfig(
                capacity=32,
                lower_quantile=0.10,
                min_observations=8,
                confidence_prior=3.0,
            )),
            "rows": rare_rows,
            "rows_sha256": _hash_json(rare_rows),
        },
        "delayed_fork": {
            "delays": [4, 5, 6],
            "rows": delayed_rows,
            "rows_sha256": _hash_json(delayed_rows),
        },
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
