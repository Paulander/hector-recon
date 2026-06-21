#!/usr/bin/env python3
"""Run TG29a tiny online KRK episode runner checkpoint."""

from __future__ import annotations

import argparse
from pathlib import Path

from recon_lite_chess.autogrowth import (
    TinyOnlineKRKEpisodeRunnerConfig,
    run_tiny_online_krk_episode_runner,
)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("reports/autogrowth/krk_autogrowth_tg29a_tiny_online_krk_episode_runner.json"),
    )
    parser.add_argument(
        "--summary-output",
        type=Path,
        default=Path("reports/autogrowth/krk_autogrowth_tg29a_tiny_online_krk_episode_runner.md"),
    )
    parser.add_argument("--progress-output", type=str, default="reports/autogrowth/krk_autogrowth_tg29a_tiny_online_krk_episode_runner_progress.json")
    parser.add_argument("--episode-count", type=int, default=4)
    parser.add_argument("--max-white-moves", type=int, default=4)
    parser.add_argument("--max-episode-ablation-count", type=int, default=1)
    parser.add_argument("--staged-pool-path", type=str, default="reports/autogrowth/pools/tg28l_staged_predecessor_pool.jsonl")
    parser.add_argument("--full-pool-path", type=str, default="reports/autogrowth/pools/tg28f_full_foundation_backed_frontier_pool.jsonl")
    parser.add_argument("--smoke", action="store_true")
    args = parser.parse_args()

    cfg = TinyOnlineKRKEpisodeRunnerConfig(
        episode_count=1 if args.smoke else args.episode_count,
        max_white_moves_per_episode=1 if args.smoke else args.max_white_moves,
        foundation_mate1_train_count=4 if args.smoke else 32,
        foundation_mate1_heldout_count=2 if args.smoke else 16,
        foundation_mate2_train_count=1 if args.smoke else 16,
        foundation_mate2_heldout_count=1 if args.smoke else 8,
        bridge_frontier_train_count=1 if args.smoke else 2,
        bridge_frontier_heldout_count=1,
        generic_edge_train_count=1 if args.smoke else 4,
        generic_edge_heldout_count=1 if args.smoke else 2,
        staged_train_count=0 if args.smoke else 8,
        staged_heldout_count=0 if args.smoke else 4,
        staged_regression_count=0 if args.smoke else 4,
        staged_near_miss_count=0 if args.smoke else 8,
        near_miss_heldout_count=0 if args.smoke else 8,
        max_ablation_positions=0 if args.smoke else 1,
        max_foundation_sanity_positions=1,
        max_foundation_ablation_positions=1,
        max_samples=4 if args.smoke else 16,
        max_episode_ablation_count=0 if args.smoke else args.max_episode_ablation_count,
        schedule_names=("tg28h_mixed_balanced_baseline",) if args.smoke else TinyOnlineKRKEpisodeRunnerConfig().schedule_names,
        staged_pool_path=args.staged_pool_path,
        full_pool_path=args.full_pool_path,
        progress_output=args.progress_output,
    )
    result = run_tiny_online_krk_episode_runner(config=cfg)
    json_path = result.write_json(args.output)
    md_path = result.write_markdown(args.summary_output)
    decision = result.decision
    print(f"wrote {json_path}")
    print(f"wrote {md_path}")
    for key in (
        "checkpoint_pass",
        "checkpoint_interpretation",
        "episode_count",
        "episode_success_count",
        "foundation_handoff_count",
        "rook_blunder_count",
        "illegal_move_count",
        "stalemate_count",
        "frontier_regression_pass",
        "staged_regression_pass",
        "near_miss_regression_pass",
        "generic_edge_regression_pass",
    ):
        print(key, decision[key])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
