#!/usr/bin/env python3
from __future__ import annotations

import argparse
import platform
import sys
import time
from pathlib import Path
from typing import Any, Dict, List

from benchmark_common import (
    DEFAULT_STAGES,
    REPO_ROOT,
    ensure_eval_fens,
    expand_per_stage,
    load_fens,
    parse_int_list,
    parse_stage_list,
    timestamp_utc,
    write_json,
)
from kpk_stage_env import KPKStageEnv

try:
    from stable_baselines3 import PPO
except ImportError:
    print("ERROR: stable-baselines3 is required.")
    print("Install with: uv pip install stable-baselines3 gymnasium")
    sys.exit(2)


def evaluate_model(model: PPO, stage: int, fens: List[str], max_moves: int) -> Dict[str, Any]:
    env = KPKStageEnv(stage=stage, max_moves=max_moves)
    outcomes = {
        "checkmate": 0,
        "promotion": 0,
        "loss": 0,
        "draw": 0,
        "timeout": 0,
        "unknown": 0,
    }
    total_moves = 0

    for fen in fens:
        obs, _ = env.reset(options={"fen": fen})
        done = False
        info: Dict[str, Any] = {}
        while not done:
            action, _ = model.predict(obs, deterministic=True)
            obs, _reward, terminated, truncated, info = env.step(int(action))
            done = bool(terminated or truncated)

        outcome = str(info.get("outcome", "unknown"))
        outcomes[outcome] = outcomes.get(outcome, 0) + 1
        total_moves += int(info.get("move_count", 0))

    episodes = len(fens)
    success = outcomes["checkmate"] + outcomes["promotion"]
    return {
        "stage": stage,
        "episodes": episodes,
        "success_rate": success / episodes if episodes else 0.0,
        "win_rate": outcomes["checkmate"] / episodes if episodes else 0.0,
        "promotion_rate": outcomes["promotion"] / episodes if episodes else 0.0,
        "avg_moves": total_moves / episodes if episodes else 0.0,
        "outcomes": outcomes,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Sequential PPO curriculum run for KPK")
    parser.add_argument(
        "--stages",
        type=str,
        default=",".join(str(s) for s in DEFAULT_STAGES),
        help="Comma-separated stage list",
    )
    parser.add_argument(
        "--timesteps-per-stage",
        type=str,
        default="50000",
        help="One value or comma-separated values per stage",
    )
    parser.add_argument("--eval-per-stage", type=int, default=100, help="Eval episodes per stage")
    parser.add_argument("--max-moves", type=int, default=100, help="Max plies per episode")
    parser.add_argument("--seed", type=int, default=42, help="PPO seed")
    parser.add_argument("--eval-seed", type=int, default=2026, help="Eval FEN seed")
    parser.add_argument(
        "--strict-stage-advance",
        action="store_true",
        help=(
            "Stop curriculum progression when eval success_rate falls below "
            "--advance-threshold."
        ),
    )
    parser.add_argument(
        "--advance-threshold",
        type=float,
        default=0.9,
        help="Minimum success_rate required to continue to next stage (default: 0.9)",
    )
    parser.add_argument(
        "--eval-dir",
        type=Path,
        default=Path("demos/experiments/kpk_curriculum_benchmark/data/eval_fens"),
        help="Eval FEN directory",
    )
    parser.add_argument("--regen-eval-fens", action="store_true", help="Regenerate eval FEN sets")
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=None,
        help="Run output directory. Defaults to _private/ppo/<timestamp>",
    )
    args = parser.parse_args()

    stages = parse_stage_list(args.stages)
    per_stage_steps = expand_per_stage(parse_int_list(args.timesteps_per_stage), len(stages))

    if args.output_dir is None:
        run_dir = (
            REPO_ROOT
            / "demos/experiments/kpk_curriculum_benchmark/_private/ppo"
            / timestamp_utc()
        )
    else:
        run_dir = args.output_dir
    run_dir.mkdir(parents=True, exist_ok=True)

    ensure_eval_fens(
        eval_dir=args.eval_dir,
        stages=stages,
        per_stage=args.eval_per_stage,
        seed=args.eval_seed,
        force=args.regen_eval_fens,
    )

    eval_fens: Dict[int, List[str]] = {}
    for stage in stages:
        eval_fens[stage] = load_fens(args.eval_dir / f"stage_{stage:02d}.fens")[: args.eval_per_stage]

    print(f"PPO curriculum run dir: {run_dir}")
    print(f"Stages: {stages}")
    print(f"Timesteps per stage: {per_stage_steps}")

    start = time.time()
    stage_rows: List[Dict[str, Any]] = []
    model: PPO | None = None

    for idx, stage in enumerate(stages):
        steps = per_stage_steps[idx]
        train_env = KPKStageEnv(stage=stage, max_moves=args.max_moves)

        if model is None:
            model = PPO(
                "MlpPolicy",
                train_env,
                verbose=1,
                seed=args.seed,
                learning_rate=3e-4,
                n_steps=2048,
                batch_size=64,
                n_epochs=10,
                gamma=0.99,
                gae_lambda=0.95,
                clip_range=0.2,
                ent_coef=0.01,
            )
        else:
            model.set_env(train_env)

        stage_start = time.time()
        model.learn(total_timesteps=steps, reset_num_timesteps=False, progress_bar=False)
        stage_train_time = time.time() - stage_start

        model_path = run_dir / f"stage_{stage:02d}_model"
        model.save(model_path)

        eval_row = evaluate_model(
            model=model,
            stage=stage,
            fens=eval_fens[stage],
            max_moves=args.max_moves,
        )
        eval_row["timesteps"] = steps
        eval_row["train_seconds"] = stage_train_time
        eval_row["model_path"] = str(model_path) + ".zip"
        stage_rows.append(eval_row)
        write_json(run_dir / f"stage_{stage:02d}_results.json", eval_row)

        print(
            f"stage {stage:02d}: success={eval_row['success_rate']:.3f} "
            f"(win={eval_row['win_rate']:.3f}, promo={eval_row['promotion_rate']:.3f}) "
            f"time={stage_train_time:.1f}s"
        )

        if args.strict_stage_advance and eval_row["success_rate"] < args.advance_threshold:
            print(
                f"Stopping PPO stage progression: success_rate "
                f"{eval_row['success_rate']:.3f} < threshold {args.advance_threshold:.3f}"
            )
            break

    total = time.time() - start
    payload = {
        "run_type": "ppo_curriculum",
        "created_utc": timestamp_utc(),
        "repo_root": str(REPO_ROOT),
        "python": sys.version,
        "platform": platform.platform(),
        "config": {
            "stages": stages,
            "timesteps_per_stage": per_stage_steps,
            "eval_per_stage": args.eval_per_stage,
            "max_moves": args.max_moves,
            "seed": args.seed,
            "eval_seed": args.eval_seed,
            "eval_dir": str(args.eval_dir),
            "strict_stage_advance": args.strict_stage_advance,
            "advance_threshold": args.advance_threshold,
        },
        "total_train_seconds": total,
        "stage_results": stage_rows,
    }
    write_json(run_dir / "ppo_curriculum_results.json", payload)
    print(f"Saved: {run_dir / 'ppo_curriculum_results.json'}")


if __name__ == "__main__":
    main()
