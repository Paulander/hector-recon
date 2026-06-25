#!/usr/bin/env python3
"""Run TG29q horizon-limited continuation repair diagnostics."""

from __future__ import annotations

import argparse
from pathlib import Path

from recon_lite_chess.autogrowth import (
    HorizonLimitedContinuationRepairConfig,
    TinyOnlineKRKEpisodeRunnerConfig,
    run_horizon_limited_continuation_repair,
)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=Path("reports/autogrowth/krk_autogrowth_tg29q_horizon_limited_continuation_repair.json"))
    parser.add_argument("--summary-output", type=Path, default=Path("reports/autogrowth/krk_autogrowth_tg29q_horizon_limited_continuation_repair.md"))
    parser.add_argument("--progress-output", type=str, default="reports/autogrowth/krk_autogrowth_tg29q_horizon_limited_continuation_repair_progress.json")
    parser.add_argument("--smoke", action="store_true")
    parser.add_argument("--baseline-only", action="store_true")
    args = parser.parse_args()

    base = TinyOnlineKRKEpisodeRunnerConfig(
        episode_count=2 if args.smoke else 4,
        max_white_moves_per_episode=6,
        foundation_mate1_train_count=4 if args.smoke else 8,
        foundation_mate1_heldout_count=2 if args.smoke else 4,
        foundation_mate2_train_count=1 if args.smoke else 4,
        foundation_mate2_heldout_count=1 if args.smoke else 2,
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
    cfg = HorizonLimitedContinuationRepairConfig(
        base=base,
        max_extended_failures=0 if args.baseline_only else (1 if args.smoke else 4),
        max_candidate_audit_positions=0 if args.baseline_only else (1 if args.smoke else 2),
        max_candidate_audit_legal_moves=8 if args.smoke else 12,
        run_real_context=not args.baseline_only,
        run_candidate_audit=not args.baseline_only,
        run_compact_regression=not args.smoke and not args.baseline_only,
    )
    result = run_horizon_limited_continuation_repair(config=cfg)
    json_path = result.write_json(args.output)
    md_path = result.write_markdown(args.summary_output)
    print(f"wrote {json_path}")
    print(f"wrote {md_path}")
    for key in (
        "checkpoint_pass",
        "checkpoint_interpretation",
        "repair_applied",
        "selected_repair_arm",
        "solvable_episode_count",
        "episode_success_count",
        "solvable_episode_success_rate",
        "decoy_false_handoff_count",
        "decoy_correct_rejection_count",
        "max4_success_rate",
        "max5_success_rate",
        "max6_success_rate",
        "good_continuation_candidate_exists_and_lost_count",
        "only_low_progress_candidates_exist_count",
        "foundation_basin_not_reached_count",
        "rook_blunder_count",
        "illegal_move_count",
        "stalemate_count",
        "foundation_frozen",
        "action_ranker_used_for_runtime",
        "runtime_tablebase_or_dtm_move_source",
        "direct_provider_override",
    ):
        print(key, result.decision[key])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
