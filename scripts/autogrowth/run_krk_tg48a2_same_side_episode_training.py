#!/usr/bin/env python3
"""Run TG48a2 same-side episode training checkpoint."""

from __future__ import annotations

import argparse
import json

from recon_lite_chess.autogrowth import (
    TG48a2SameSideEpisodeTrainingConfig,
    run_tg48a2_same_side_episode_training,
)


DEFAULT_OUTPUT_DIR = "reports/autogrowth/clean_slate_krk/tg48a2_same_side_episode_training"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--run-scale-label", default="smoke")
    parser.add_argument("--seed", type=int, default=20260701)
    parser.add_argument("--train-count", type=int, default=80)
    parser.add_argument("--heldout-count", type=int, default=32)
    parser.add_argument("--regression-count", type=int, default=32)
    parser.add_argument("--decoy-count", type=int, default=32)
    parser.add_argument("--hard-decoy-count", type=int, default=32)
    parser.add_argument("--max-generation-attempts", type=int, default=250_000)
    parser.add_argument("--max-white-moves", type=int, default=3)
    parser.add_argument("--max-total-plies", type=int, default=6)
    args = parser.parse_args()

    output_dir = args.output_dir
    config = TG48a2SameSideEpisodeTrainingConfig(
        output_dir=output_dir,
        output_path=f"{output_dir}/krk_tg48a2_same_side_episode_training.json",
        markdown_path=f"{output_dir}/krk_tg48a2_same_side_episode_training.md",
        train_episode_trace_path=f"{output_dir}/pools/train_episode_traces.jsonl.gz",
        eval_episode_trace_path=f"{output_dir}/pools/eval_episode_traces.jsonl.gz",
        failure_episode_pool_path=f"{output_dir}/pools/failure_episode_pool.jsonl.gz",
        promoted_terminal_audit_path=f"{output_dir}/pools/promoted_terminal_audit.jsonl.gz",
        reward_channel_audit_path=f"{output_dir}/pools/reward_channel_audit.jsonl.gz",
        board_sample_path=f"{output_dir}/pools/board_samples.md",
        run_scale_label=args.run_scale_label,
        seed=args.seed,
        train_count=args.train_count,
        heldout_count=args.heldout_count,
        regression_count=args.regression_count,
        decoy_count=args.decoy_count,
        hard_decoy_count=args.hard_decoy_count,
        max_generation_attempts=args.max_generation_attempts,
        max_white_moves=args.max_white_moves,
        max_total_plies=args.max_total_plies,
    )
    result = run_tg48a2_same_side_episode_training(config=config)
    print(json.dumps(result.decision, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
