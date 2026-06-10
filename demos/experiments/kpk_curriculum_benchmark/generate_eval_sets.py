#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path

from benchmark_common import DEFAULT_STAGES, ensure_eval_fens, parse_stage_list


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate deterministic KPK stage eval FEN sets")
    parser.add_argument(
        "--stages",
        type=str,
        default=",".join(str(s) for s in DEFAULT_STAGES),
        help="Comma-separated stage list",
    )
    parser.add_argument("--per-stage", type=int, default=100, help="FENs per stage")
    parser.add_argument("--seed", type=int, default=2026, help="Base seed")
    parser.add_argument(
        "--eval-dir",
        type=Path,
        default=Path("demos/experiments/kpk_curriculum_benchmark/data/eval_fens"),
        help="Output directory for stage FEN files",
    )
    parser.add_argument("--force", action="store_true", help="Regenerate even if files exist")
    args = parser.parse_args()

    stages = parse_stage_list(args.stages)
    paths = ensure_eval_fens(
        eval_dir=args.eval_dir,
        stages=stages,
        per_stage=args.per_stage,
        seed=args.seed,
        force=args.force,
    )
    for stage in stages:
        print(f"stage {stage:02d}: {paths[stage]}")


if __name__ == "__main__":
    main()
