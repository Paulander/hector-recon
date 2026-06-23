#!/usr/bin/env python3
"""Run TG29i stable trajectory cache selection microprobe checkpoint."""

from __future__ import annotations

import argparse
from pathlib import Path

from recon_lite_chess.autogrowth import (
    StableTrajectoryCacheSelectionMicroprobeConfig,
    TinyOnlineKRKEpisodeRunnerConfig,
    run_stable_trajectory_cache_selection_microprobe,
)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=Path("reports/autogrowth/krk_autogrowth_tg29i_stable_trajectory_cache_selection_microprobe.json"))
    parser.add_argument("--summary-output", type=Path, default=Path("reports/autogrowth/krk_autogrowth_tg29i_stable_trajectory_cache_selection_microprobe.md"))
    parser.add_argument("--progress-output", type=str, default="reports/autogrowth/krk_autogrowth_tg29i_stable_trajectory_cache_selection_microprobe_progress.json")
    parser.add_argument("--tg29h-artifact-path", type=str, default="reports/autogrowth/krk_autogrowth_tg29h_cached_trajectory_selection_repair.json")
    parser.add_argument("--source-cache-path", type=str, default="reports/autogrowth/pools/tg29h_trajectory_rollout_cache.jsonl")
    parser.add_argument("--cache-path", type=str, default="reports/autogrowth/pools/tg29i_stable_trajectory_rollout_cache.jsonl")
    parser.add_argument("--cache-index-path", type=str, default="reports/autogrowth/pools/tg29i_stable_trajectory_rollout_cache_index.json")
    parser.add_argument("--quick-context", action="store_true")
    parser.add_argument("--smoke", action="store_true")
    args = parser.parse_args()

    quick_context = args.quick_context or args.smoke
    base = TinyOnlineKRKEpisodeRunnerConfig(
        episode_count=1 if args.smoke else 2,
        max_white_moves_per_episode=1 if args.smoke else 2,
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
    result = run_stable_trajectory_cache_selection_microprobe(
        config=StableTrajectoryCacheSelectionMicroprobeConfig(
            base=base,
            tg29h_artifact_path=args.tg29h_artifact_path,
            source_cache_path=args.source_cache_path,
            trajectory_cache_path=args.cache_path,
            trajectory_cache_index_path=args.cache_index_path,
        )
    )
    json_path = result.write_json(args.output)
    md_path = result.write_markdown(args.summary_output)
    print(f"wrote {json_path}")
    print(f"wrote {md_path}")
    for key in (
        "checkpoint_pass",
        "checkpoint_interpretation",
        "stable_cache_key_mismatch_count",
        "cache_hit_rate_first_pass",
        "cache_hit_rate_second_pass",
        "live_rollout_count_first_pass",
        "live_rollout_count_second_pass",
        "known_trajectory_candidate_runtime_present_count",
        "trajectory_positive_candidate_selected_after_combined_repair_count",
    ):
        print(key, result.decision[key])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
