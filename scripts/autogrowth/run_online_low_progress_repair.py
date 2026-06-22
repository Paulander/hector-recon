#!/usr/bin/env python3
"""Run TG29d online low-progress repair checkpoint."""

from __future__ import annotations

import argparse
from pathlib import Path

from recon_lite_chess.autogrowth import (
    OnlineLowProgressRepairConfig,
    TinyOnlineKRKEpisodeRunnerConfig,
    run_online_low_progress_repair,
)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=Path("reports/autogrowth/krk_autogrowth_tg29d_online_low_progress_repair.json"))
    parser.add_argument("--summary-output", type=Path, default=Path("reports/autogrowth/krk_autogrowth_tg29d_online_low_progress_repair.md"))
    parser.add_argument("--progress-output", type=str, default="reports/autogrowth/krk_autogrowth_tg29d_online_low_progress_repair_progress.json")
    parser.add_argument("--episode-count", type=int, default=4)
    parser.add_argument("--max-white-moves", type=int, default=4)
    parser.add_argument("--max-episode-ablation-count", type=int, default=1)
    parser.add_argument("--smoke", action="store_true")
    args = parser.parse_args()

    base = TinyOnlineKRKEpisodeRunnerConfig(
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
        schedule_names=("tg28h_mixed_balanced_baseline",) if args.smoke else ("mixed_balanced_plus_staged",),
        progress_output=args.progress_output,
    )
    result = run_online_low_progress_repair(
        config=OnlineLowProgressRepairConfig(
            base=base,
            reply_policies=("deterministic_worst_foundation_reply",),
            comparison_reply_policies=() if args.smoke else ("mobility_maximizing",),
            repair_arms=("combined_reply_robust", "balanced_reply_robust_plus_progress") if args.smoke else OnlineLowProgressRepairConfig().repair_arms,
        )
    )
    json_path = result.write_json(args.output)
    md_path = result.write_markdown(args.summary_output)
    print(f"wrote {json_path}")
    print(f"wrote {md_path}")
    for key in (
        "checkpoint_pass",
        "checkpoint_interpretation",
        "repair_applied",
        "selected_repair_arm",
        "episode_success_count",
        "selected_moves_safe_but_low_progress_count",
        "bridge_loop_without_foundation_progress_count",
        "mobility_max_reply_success_rate",
    ):
        print(key, result.decision[key])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
