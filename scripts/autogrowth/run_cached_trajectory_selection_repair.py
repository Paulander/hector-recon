#!/usr/bin/env python3
"""Run TG29h cached trajectory selection repair checkpoint."""

from __future__ import annotations

import argparse
from pathlib import Path

from recon_lite_chess.autogrowth import (
    CachedTrajectorySelectionRepairConfig,
    TinyOnlineKRKEpisodeRunnerConfig,
    run_cached_trajectory_selection_repair,
)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=Path("reports/autogrowth/krk_autogrowth_tg29h_cached_trajectory_selection_repair.json"))
    parser.add_argument("--summary-output", type=Path, default=Path("reports/autogrowth/krk_autogrowth_tg29h_cached_trajectory_selection_repair.md"))
    parser.add_argument("--progress-output", type=str, default="reports/autogrowth/krk_autogrowth_tg29h_cached_trajectory_selection_repair_progress.json")
    parser.add_argument("--cache-path", type=str, default="reports/autogrowth/pools/tg29h_trajectory_rollout_cache.jsonl")
    parser.add_argument("--cache-index-path", type=str, default="reports/autogrowth/pools/tg29h_trajectory_rollout_cache_index.json")
    parser.add_argument("--tg29f-artifact-path", type=str, default="reports/autogrowth/krk_autogrowth_tg29f_progress_candidate_selection_repair.json")
    parser.add_argument("--tg29g-artifact-path", type=str, default="reports/autogrowth/krk_autogrowth_tg29g_trajectory_positive_prefix_audit.json")
    parser.add_argument("--episode-count", type=int, default=2)
    parser.add_argument("--max-white-moves", type=int, default=2)
    parser.add_argument("--max-safe-candidates-per-start", type=int, default=8)
    parser.add_argument("--skip-repair-episodes", action="store_true")
    parser.add_argument("--no-seed-cache-from-tg29g", action="store_true")
    parser.add_argument("--quick-context", action="store_true")
    parser.add_argument("--smoke", action="store_true")
    args = parser.parse_args()

    quick_context = args.quick_context or args.smoke
    base = TinyOnlineKRKEpisodeRunnerConfig(
        episode_count=1 if args.smoke else args.episode_count,
        max_white_moves_per_episode=1 if args.smoke else args.max_white_moves,
        foundation_mate1_train_count=4 if args.smoke else (8 if quick_context else 32),
        foundation_mate1_heldout_count=2 if args.smoke else (4 if quick_context else 16),
        foundation_mate2_train_count=1 if args.smoke else (4 if quick_context else 16),
        foundation_mate2_heldout_count=1 if args.smoke else (2 if quick_context else 8),
        bridge_frontier_train_count=1 if quick_context else 2,
        bridge_frontier_heldout_count=1,
        generic_edge_train_count=1 if quick_context else 4,
        generic_edge_heldout_count=1 if quick_context else 2,
        staged_train_count=0 if quick_context else 8,
        staged_heldout_count=0 if quick_context else 4,
        staged_regression_count=0 if quick_context else 4,
        staged_near_miss_count=0 if quick_context else 8,
        near_miss_heldout_count=0 if quick_context else 8,
        max_ablation_positions=0 if args.smoke else 1,
        max_foundation_sanity_positions=1,
        max_foundation_ablation_positions=1,
        max_samples=4 if args.smoke else 16,
        max_episode_ablation_count=0,
        schedule_names=("tg28h_mixed_balanced_baseline",) if args.smoke else ("mixed_balanced_plus_staged",),
        progress_output=args.progress_output,
    )
    result = run_cached_trajectory_selection_repair(
        config=CachedTrajectorySelectionRepairConfig(
            base=base,
            tg29f_artifact_path=args.tg29f_artifact_path,
            tg29g_artifact_path=args.tg29g_artifact_path,
            trajectory_cache_path=args.cache_path,
            trajectory_cache_index_path=args.cache_index_path,
            max_failure_starts=1 if args.smoke else 2,
            max_safe_candidates_per_start=1 if args.smoke else args.max_safe_candidates_per_start,
            max_repair_cache_candidate_moves=3 if args.smoke else 6,
            max_reply_envelope_replies_per_candidate=1 if args.smoke else 2,
            seed_cache_from_tg29g=not args.no_seed_cache_from_tg29g,
            run_repair_episodes=False if args.smoke else not args.skip_repair_episodes,
            audit_context_profile="smoke" if args.smoke else ("quick_context" if args.quick_context else "full"),
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
        "trajectory_cache_entry_count",
        "trajectory_cache_hit_count",
        "live_rollout_count",
        "audited_candidate_count",
        "trajectory_positive_candidate_count",
        "better_trajectory_candidate_selected_after_repair_count",
        "bounded_episode_success_count",
        "candidate_cap_blocked_count",
    ):
        print(key, result.decision[key])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
