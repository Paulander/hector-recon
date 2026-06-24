#!/usr/bin/env python3
"""Run TG29o S1 full-reply evidence cache and online recheck."""

from __future__ import annotations

import argparse
from pathlib import Path

from recon_lite_chess.autogrowth import (
    S1FullReplyCacheOnlineRecheckConfig,
    TinyOnlineKRKEpisodeRunnerConfig,
    run_s1_full_reply_cache_online_recheck,
)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=Path("reports/autogrowth/krk_autogrowth_tg29o_s1_full_reply_cache_online_recheck.json"))
    parser.add_argument("--summary-output", type=Path, default=Path("reports/autogrowth/krk_autogrowth_tg29o_s1_full_reply_cache_online_recheck.md"))
    parser.add_argument("--progress-output", type=str, default="reports/autogrowth/krk_autogrowth_tg29o_s1_full_reply_cache_online_recheck_progress.json")
    parser.add_argument("--quick-context", action="store_true")
    parser.add_argument("--smoke", action="store_true")
    parser.add_argument("--skip-larger-online", action="store_true")
    args = parser.parse_args()

    quick_context = args.quick_context or args.smoke
    base = TinyOnlineKRKEpisodeRunnerConfig(
        episode_count=2,
        max_white_moves_per_episode=2,
        foundation_mate1_train_count=4 if args.smoke else (8 if quick_context else 32),
        foundation_mate1_heldout_count=2 if args.smoke else (4 if quick_context else 16),
        foundation_mate2_train_count=1 if args.smoke else (4 if quick_context else 16),
        foundation_mate2_heldout_count=1 if args.smoke else (2 if quick_context else 8),
        bridge_frontier_train_count=0,
        bridge_frontier_heldout_count=0,
        generic_edge_train_count=0,
        generic_edge_heldout_count=0,
        staged_train_count=0,
        staged_heldout_count=0,
        staged_regression_count=0,
        staged_near_miss_count=0,
        near_miss_heldout_count=0,
        max_ablation_positions=0,
        max_foundation_sanity_positions=1,
        max_foundation_ablation_positions=1,
        max_samples=4 if args.smoke else 16,
        max_episode_ablation_count=1,
        schedule_names=("tg29l_minimal_real_context",),
        progress_output=args.progress_output,
    )
    result = run_s1_full_reply_cache_online_recheck(
        config=S1FullReplyCacheOnlineRecheckConfig(
            base=base,
            run_slightly_larger_online_set=not args.skip_larger_online,
        )
    )
    json_path = result.write_json(args.output)
    md_path = result.write_markdown(args.summary_output)
    print(f"wrote {json_path}")
    print(f"wrote {md_path}")
    for key in (
        "checkpoint_pass",
        "checkpoint_interpretation",
        "selected_repair_arm",
        "s1_cache_entry_count",
        "s1_cache_hit_rate_first_pass",
        "s1_cache_hit_rate_second_pass",
        "s1_cache_live_mismatch_count",
        "s1_train_count",
        "s1_heldout_count",
        "s1_near_miss_count",
        "s1_selected_all_reply_foundation_count",
        "s1_selected_one_reply_later_failed_count",
        "max2_episode_success_count",
        "max2_episode_count",
        "max3_episode_success_count",
        "max3_episode_count",
        "s1_full_reply_repair_ablation_causal",
        "foundation_frozen",
        "action_ranker_used_for_runtime",
        "runtime_tablebase_or_dtm_move_source",
        "direct_provider_override",
    ):
        print(key, result.decision[key])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
