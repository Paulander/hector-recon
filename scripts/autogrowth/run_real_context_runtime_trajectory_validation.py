#!/usr/bin/env python3
"""Run TG29l real-context runtime trajectory validation."""

from __future__ import annotations

import argparse
from pathlib import Path

from recon_lite_chess.autogrowth import (
    RealContextRuntimeTrajectoryValidationConfig,
    TinyOnlineKRKEpisodeRunnerConfig,
    run_real_context_runtime_trajectory_validation,
)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=Path("reports/autogrowth/krk_autogrowth_tg29l_real_context_runtime_trajectory_validation.json"))
    parser.add_argument("--summary-output", type=Path, default=Path("reports/autogrowth/krk_autogrowth_tg29l_real_context_runtime_trajectory_validation.md"))
    parser.add_argument("--progress-output", type=str, default="reports/autogrowth/krk_autogrowth_tg29l_real_context_runtime_trajectory_validation_progress.json")
    parser.add_argument("--quick-context", action="store_true")
    parser.add_argument("--smoke", action="store_true")
    parser.add_argument("--skip-episodes", action="store_true")
    parser.add_argument("--skip-ablations", action="store_true")
    args = parser.parse_args()

    quick_context = args.quick_context or args.smoke
    base = TinyOnlineKRKEpisodeRunnerConfig(
        episode_count=1 if args.smoke else 2,
        max_white_moves_per_episode=1 if args.smoke else 2,
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
    result = run_real_context_runtime_trajectory_validation(
        config=RealContextRuntimeTrajectoryValidationConfig(
            base=base,
            run_tiny_episode_check=not args.skip_episodes,
            run_minimal_ablations=not args.skip_ablations,
        )
    )
    json_path = result.write_json(args.output)
    md_path = result.write_markdown(args.summary_output)
    print(f"wrote {json_path}")
    print(f"wrote {md_path}")
    for key in (
        "checkpoint_pass",
        "checkpoint_interpretation",
        "context_built",
        "context_build_blocker",
        "total_context_build_seconds",
        "e2d3_real_context_selected",
        "d3c3_real_context_selected",
        "known_trajectory_real_context_selected_count",
        "bounded_episode_success_count",
        "trajectory_repair_ablation_causal",
        "rook_blunder_count",
        "illegal_move_count",
        "stalemate_count",
    ):
        print(key, result.decision[key])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
