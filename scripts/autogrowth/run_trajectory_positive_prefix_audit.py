#!/usr/bin/env python3
"""Run TG29g trajectory-positive prefix audit checkpoint."""

from __future__ import annotations

import argparse
from pathlib import Path

from recon_lite_chess.autogrowth import (
    TinyOnlineKRKEpisodeRunnerConfig,
    TrajectoryPositivePrefixAuditConfig,
    run_trajectory_positive_prefix_audit,
)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=Path("reports/autogrowth/krk_autogrowth_tg29g_trajectory_positive_prefix_audit.json"))
    parser.add_argument("--summary-output", type=Path, default=Path("reports/autogrowth/krk_autogrowth_tg29g_trajectory_positive_prefix_audit.md"))
    parser.add_argument("--progress-output", type=str, default="reports/autogrowth/krk_autogrowth_tg29g_trajectory_positive_prefix_audit_progress.json")
    parser.add_argument("--pool-path", type=str, default="reports/autogrowth/pools/tg29g_trajectory_positive_prefix_pool.jsonl")
    parser.add_argument("--pool-index-path", type=str, default="reports/autogrowth/pools/tg29g_trajectory_positive_prefix_pool_index.json")
    parser.add_argument("--tg29f-artifact-path", type=str, default="reports/autogrowth/krk_autogrowth_tg29f_progress_candidate_selection_repair.json")
    parser.add_argument("--episode-count", type=int, default=2)
    parser.add_argument("--max-white-moves", type=int, default=2)
    parser.add_argument("--max-safe-candidates-per-start", type=int, default=0)
    parser.add_argument("--quick-context", action="store_true")
    parser.add_argument("--skip-optional-repair", action="store_true")
    parser.add_argument("--smoke", action="store_true")
    args = parser.parse_args()

    quick_context = args.quick_context or args.smoke
    foundation_mate1_train_count = 4 if args.smoke else (8 if quick_context else 32)
    foundation_mate1_heldout_count = 2 if args.smoke else (4 if quick_context else 16)
    foundation_mate2_train_count = 1 if args.smoke else (4 if quick_context else 16)
    foundation_mate2_heldout_count = 1 if args.smoke else (2 if quick_context else 8)
    bridge_frontier_train_count = 1 if quick_context else 2
    generic_edge_train_count = 1 if quick_context else 4
    generic_edge_heldout_count = 1 if quick_context else 2
    staged_train_count = 0 if quick_context else 8
    staged_heldout_count = 0 if quick_context else 4
    staged_regression_count = 0 if quick_context else 4
    staged_near_miss_count = 0 if quick_context else 8
    near_miss_heldout_count = 0 if quick_context else 8

    base = TinyOnlineKRKEpisodeRunnerConfig(
        episode_count=1 if args.smoke else args.episode_count,
        max_white_moves_per_episode=1 if args.smoke else args.max_white_moves,
        foundation_mate1_train_count=foundation_mate1_train_count,
        foundation_mate1_heldout_count=foundation_mate1_heldout_count,
        foundation_mate2_train_count=foundation_mate2_train_count,
        foundation_mate2_heldout_count=foundation_mate2_heldout_count,
        bridge_frontier_train_count=bridge_frontier_train_count,
        bridge_frontier_heldout_count=1,
        generic_edge_train_count=generic_edge_train_count,
        generic_edge_heldout_count=generic_edge_heldout_count,
        staged_train_count=staged_train_count,
        staged_heldout_count=staged_heldout_count,
        staged_regression_count=staged_regression_count,
        staged_near_miss_count=staged_near_miss_count,
        near_miss_heldout_count=near_miss_heldout_count,
        max_ablation_positions=0 if args.smoke else 1,
        max_foundation_sanity_positions=1,
        max_foundation_ablation_positions=1,
        max_samples=4 if args.smoke else 16,
        max_episode_ablation_count=0,
        schedule_names=("tg28h_mixed_balanced_baseline",) if args.smoke else ("mixed_balanced_plus_staged",),
        progress_output=args.progress_output,
    )
    result = run_trajectory_positive_prefix_audit(
        config=TrajectoryPositivePrefixAuditConfig(
            base=base,
            tg29f_artifact_path=args.tg29f_artifact_path,
            pool_path=args.pool_path,
            pool_index_path=args.pool_index_path,
            max_failure_starts=1 if args.smoke else 2,
            max_safe_candidates_per_start=1 if args.smoke else args.max_safe_candidates_per_start,
            max_repair_cache_candidate_moves=3 if args.smoke else 6,
            max_reply_envelope_replies_per_candidate=1 if args.smoke else 2,
            run_optional_repair=False if args.smoke else not args.skip_optional_repair,
            audit_context_profile="smoke" if args.smoke else ("quick_context" if args.quick_context else "full"),
            throughput_note=(
                "Quick context used because full TG29g context/all-safe-candidate audit exceeded practical runtime; "
                "use this as bounded trajectory-prefix evidence, not a full-scale competence claim."
                if args.quick_context
                else ""
            ),
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
        "trajectory_positive_candidate_count",
        "trajectory_positive_candidate_lost_selection_count",
        "trajectory_pool_entry_count",
        "bounded_episode_success_count",
        "selected_moves_safe_but_low_progress_count",
        "bridge_loop_without_foundation_progress_count",
    ):
        print(key, result.decision[key])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
