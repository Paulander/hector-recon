#!/usr/bin/env python3
"""Run TG29f progress candidate selection repair checkpoint."""

from __future__ import annotations

import argparse
from pathlib import Path

from recon_lite_chess.autogrowth import (
    ProgressCandidateSelectionRepairConfig,
    TinyOnlineKRKEpisodeRunnerConfig,
    run_progress_candidate_selection_repair,
)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=Path("reports/autogrowth/krk_autogrowth_tg29f_progress_candidate_selection_repair.json"))
    parser.add_argument("--summary-output", type=Path, default=Path("reports/autogrowth/krk_autogrowth_tg29f_progress_candidate_selection_repair.md"))
    parser.add_argument("--progress-output", type=str, default="reports/autogrowth/krk_autogrowth_tg29f_progress_candidate_selection_repair_progress.json")
    parser.add_argument("--tg29e-artifact-path", type=str, default="reports/autogrowth/krk_autogrowth_tg29e_reply_robust_progress_positive_pool.json")
    parser.add_argument("--episode-count", type=int, default=2)
    parser.add_argument("--max-white-moves", type=int, default=2)
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
        max_episode_ablation_count=0,
        schedule_names=("tg28h_mixed_balanced_baseline",) if args.smoke else ("mixed_balanced_plus_staged",),
        progress_output=args.progress_output,
    )
    result = run_progress_candidate_selection_repair(
        config=ProgressCandidateSelectionRepairConfig(
            base=base,
            tg29e_artifact_path=args.tg29e_artifact_path,
            max_lost_turns=1 if args.smoke else 2,
            max_repair_cache_candidate_moves=3 if args.smoke else 6,
            max_reply_envelope_replies_per_candidate=1 if args.smoke else 2,
        )
    )
    json_path = result.write_json(args.output)
    md_path = result.write_markdown(args.summary_output)
    print(f"wrote {json_path}")
    print(f"wrote {md_path}")
    for key in (
        "checkpoint_pass",
        "checkpoint_interpretation",
        "selected_arm",
        "repair_applied",
        "lost_turn_count",
        "explained_lost_turn_count",
        "better_progress_candidate_selected_after_repair_count",
        "episode_success_count",
        "selected_moves_safe_but_low_progress_count",
    ):
        print(key, result.decision[key])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
