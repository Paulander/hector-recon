#!/usr/bin/env python3
"""Run TG29p cached online episode scale matrix."""

from __future__ import annotations

import argparse
from pathlib import Path

from recon_lite_chess.autogrowth import (
    CachedOnlineEpisodeScaleMatrixConfig,
    TinyOnlineKRKEpisodeRunnerConfig,
    run_cached_online_episode_scale_matrix,
)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=Path("reports/autogrowth/krk_autogrowth_tg29p_cached_online_episode_scale_matrix.json"))
    parser.add_argument("--summary-output", type=Path, default=Path("reports/autogrowth/krk_autogrowth_tg29p_cached_online_episode_scale_matrix.md"))
    parser.add_argument("--progress-output", type=str, default="reports/autogrowth/krk_autogrowth_tg29p_cached_online_episode_scale_matrix_progress.json")
    parser.add_argument("--quick-context", action="store_true")
    parser.add_argument("--bounded-scale", action="store_true")
    parser.add_argument("--smoke", action="store_true")
    args = parser.parse_args()

    quick_context = args.quick_context or args.bounded_scale or args.smoke
    base = TinyOnlineKRKEpisodeRunnerConfig(
        episode_count=4,
        max_white_moves_per_episode=4,
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
    if args.smoke:
        start_counts = {
            "known_repaired_starts": 2,
            "staged_pool_starts": 1,
            "frontier_near_starts": 1,
            "generic_edge_starts": 1,
            "near_miss_or_decoy_starts": 1,
        }
    elif args.bounded_scale:
        start_counts = {
            "known_repaired_starts": 2,
            "staged_pool_starts": 1,
            "frontier_near_starts": 1,
            "generic_edge_starts": 1,
            "near_miss_or_decoy_starts": 1,
        }
    else:
        start_counts = None
    cfg = CachedOnlineEpisodeScaleMatrixConfig(
        base=base,
        start_counts=start_counts,
        horizons=(2,) if args.smoke else (2, 3, 4),
        black_reply_policies=("deterministic_worst_foundation_reply",) if args.smoke else ("deterministic_worst_foundation_reply", "mobility_maximizing", "fixed_seed_random"),
        diagnostic_arm_start_limit=2 if args.smoke else 4,
        run_diagnostic_arms=not args.smoke,
        run_representative_ablations=not args.smoke,
        run_compact_regression=not args.smoke,
    )
    result = run_cached_online_episode_scale_matrix(config=cfg)
    json_path = result.write_json(args.output)
    md_path = result.write_markdown(args.summary_output)
    print(f"wrote {json_path}")
    print(f"wrote {md_path}")
    for key in (
        "checkpoint_pass",
        "checkpoint_interpretation",
        "selected_policy_arm",
        "total_episode_count",
        "episode_success_count",
        "episode_success_rate",
        "max2_success_rate",
        "max3_success_rate",
        "max4_success_rate",
        "worst_foundation_reply_success_rate",
        "mobility_max_reply_success_rate",
        "random_reply_success_rate",
        "rook_blunder_count",
        "illegal_move_count",
        "stalemate_count",
        "s1_selected_all_reply_foundation_count",
        "s1_selected_one_reply_later_failed_count",
        "foundation_frozen",
        "action_ranker_used_for_runtime",
        "runtime_tablebase_or_dtm_move_source",
        "direct_provider_override",
    ):
        print(key, result.decision[key])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
