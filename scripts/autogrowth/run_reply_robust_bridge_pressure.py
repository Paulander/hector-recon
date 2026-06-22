#!/usr/bin/env python3
"""Run TG29c reply-robust bridge pressure checkpoint."""

from __future__ import annotations

import argparse
from pathlib import Path

from recon_lite_chess.autogrowth import (
    ReplyRobustBridgePressureConfig,
    TinyOnlineKRKEpisodeRunnerConfig,
    run_reply_robust_bridge_pressure,
)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("reports/autogrowth/krk_autogrowth_tg29c_reply_robust_bridge_pressure.json"),
    )
    parser.add_argument(
        "--summary-output",
        type=Path,
        default=Path("reports/autogrowth/krk_autogrowth_tg29c_reply_robust_bridge_pressure.md"),
    )
    parser.add_argument(
        "--progress-output",
        type=str,
        default="reports/autogrowth/krk_autogrowth_tg29c_reply_robust_bridge_pressure_progress.json",
    )
    parser.add_argument("--episode-count", type=int, default=4)
    parser.add_argument("--max-white-moves", type=int, default=4)
    parser.add_argument("--max-episode-ablation-count", type=int, default=1)
    parser.add_argument("--max-reply-envelope-replies", type=int, default=2)
    parser.add_argument("--staged-pool-path", type=str, default="reports/autogrowth/pools/tg28l_staged_predecessor_pool.jsonl")
    parser.add_argument("--full-pool-path", type=str, default="reports/autogrowth/pools/tg28f_full_foundation_backed_frontier_pool.jsonl")
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
        staged_pool_path=args.staged_pool_path,
        full_pool_path=args.full_pool_path,
        progress_output=args.progress_output,
    )
    result = run_reply_robust_bridge_pressure(
        config=ReplyRobustBridgePressureConfig(
            base=base,
            max_reply_envelope_replies_per_candidate=2 if args.smoke else args.max_reply_envelope_replies,
            reply_policies=("deterministic_worst_foundation_reply",) if args.smoke else ReplyRobustBridgePressureConfig().reply_policies,
            comparison_reply_policies=() if args.smoke else ReplyRobustBridgePressureConfig().comparison_reply_policies,
            repair_arms=("baseline_no_repair", "combined_reply_robust") if args.smoke else ReplyRobustBridgePressureConfig().repair_arms,
        )
    )
    json_path = result.write_json(args.output)
    md_path = result.write_markdown(args.summary_output)
    decision = result.decision
    print(f"wrote {json_path}")
    print(f"wrote {md_path}")
    for key in (
        "checkpoint_pass",
        "checkpoint_interpretation",
        "repair_applied",
        "selected_repair_arm",
        "episode_count",
        "episode_success_count",
        "bridge_loop_without_foundation_progress_count",
        "worst_foundation_reply_success_rate",
        "rook_blunder_count",
        "illegal_move_count",
        "stalemate_count",
        "scheduler_equivalence_mismatch_count",
    ):
        print(key, decision[key])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
