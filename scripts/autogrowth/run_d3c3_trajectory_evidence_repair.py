#!/usr/bin/env python3
"""Run TG29j d3c3 trajectory evidence repair checkpoint."""

from __future__ import annotations

import argparse
from pathlib import Path

from recon_lite_chess.autogrowth import (
    D3C3TrajectoryEvidenceRepairConfig,
    TinyOnlineKRKEpisodeRunnerConfig,
    run_d3c3_trajectory_evidence_repair,
)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=Path("reports/autogrowth/krk_autogrowth_tg29j_d3c3_trajectory_evidence_repair.json"))
    parser.add_argument("--summary-output", type=Path, default=Path("reports/autogrowth/krk_autogrowth_tg29j_d3c3_trajectory_evidence_repair.md"))
    parser.add_argument("--progress-output", type=str, default="reports/autogrowth/krk_autogrowth_tg29j_d3c3_trajectory_evidence_repair_progress.json")
    parser.add_argument("--tg29h-artifact-path", type=str, default="reports/autogrowth/krk_autogrowth_tg29h_cached_trajectory_selection_repair.json")
    parser.add_argument("--tg29i-artifact-path", type=str, default="reports/autogrowth/krk_autogrowth_tg29i_stable_trajectory_cache_selection_microprobe.json")
    parser.add_argument("--trajectory-cache-path", type=str, default="reports/autogrowth/pools/tg29i_stable_trajectory_rollout_cache.jsonl")
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
    result = run_d3c3_trajectory_evidence_repair(
        config=D3C3TrajectoryEvidenceRepairConfig(
            base=base,
            tg29h_artifact_path=args.tg29h_artifact_path,
            tg29i_artifact_path=args.tg29i_artifact_path,
            trajectory_cache_path=args.trajectory_cache_path,
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
        "e2d3_selected_before",
        "e2d3_selected_after",
        "d3c3_selected_before",
        "d3c3_selected_after",
        "known_trajectory_candidate_selected_after_count",
        "d3c3_failure_bucket_before",
        "d3c3_failure_bucket_after",
    ):
        print(key, result.decision[key])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
