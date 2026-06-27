#!/usr/bin/env python3
"""Run TG32 child boundary active learning and shadow-online stress diagnostic."""

from __future__ import annotations

import argparse
from pathlib import Path

from recon_lite_chess.autogrowth import (
    ChildBoundaryActiveLearningShadowStressConfig,
    run_child_boundary_active_learning_shadow_stress,
)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=Path("reports/autogrowth/krk_autogrowth_tg32_child_boundary_active_learning_shadow_stress.json"))
    parser.add_argument("--summary-output", type=Path, default=Path("reports/autogrowth/krk_autogrowth_tg32_child_boundary_active_learning_shadow_stress.md"))
    parser.add_argument("--progress-output", type=str, default="reports/autogrowth/krk_autogrowth_tg32_child_boundary_active_learning_shadow_stress_progress.json")
    parser.add_argument("--long", action="store_true")
    parser.add_argument("--max-total-seconds", type=int, default=21600)
    parser.add_argument("--min-target-seconds", type=int, default=18000)
    parser.add_argument("--progress-interval-seconds", type=int, default=300)
    parser.add_argument("--adaptive-expansion", choices=("true", "false"), default="true")
    parser.add_argument("--active-learning-rounds", type=int, default=5)
    parser.add_argument("--seed-count", type=int, default=10)
    parser.add_argument("--cycles-per-arm", type=int, default=250)
    parser.add_argument("--max-cycles-per-arm", type=int, default=1000)
    parser.add_argument("--shadow-online-stress", choices=("true", "false"), default="true")
    parser.add_argument("--target-tier", type=int, choices=(1, 2, 3, 4), default=1)
    args = parser.parse_args()

    target_tier = max(args.target_tier, 3) if args.long else args.target_tier
    cfg = ChildBoundaryActiveLearningShadowStressConfig(
        base=ChildBoundaryActiveLearningShadowStressConfig().base.__class__(
            progress_output=args.progress_output,
        ),
        long_mode=args.long,
        max_total_seconds=args.max_total_seconds,
        min_target_seconds=args.min_target_seconds if args.long else 0,
        progress_interval_seconds=args.progress_interval_seconds,
        adaptive_expansion=args.adaptive_expansion == "true",
        active_learning_rounds=args.active_learning_rounds,
        seed_count=max(args.seed_count, 10 if args.long else 1),
        cycles_per_arm=max(args.cycles_per_arm, 250 if args.long else args.cycles_per_arm),
        max_cycles_per_arm=max(args.max_cycles_per_arm, 1000 if args.long else args.max_cycles_per_arm),
        shadow_online_stress=args.shadow_online_stress == "true",
        target_tier=target_tier,
    )
    result = run_child_boundary_active_learning_shadow_stress(config=cfg)
    json_path = result.write_json(args.output)
    md_path = result.write_markdown(args.summary_output)
    print(f"wrote {json_path}")
    print(f"wrote {md_path}")
    for key in (
        "checkpoint_pass",
        "checkpoint_interpretation",
        "repair_applied",
        "selected_repair_arm",
        "expanded_boundary_pool_entry_count",
        "unique_boundary_fen_count",
        "lineage_group_count",
        "split_group_leak_count",
        "active_learning_round_count",
        "adaptive_tiers_completed",
        "boundary_train_count",
        "boundary_heldout_count",
        "boundary_regression_count",
        "boundary_decoy_count",
        "hard_decoy_count",
        "child_confusable_decoy_count",
        "child_arm_count",
        "child_seed_count",
        "cycles_per_arm",
        "max_cycles_per_arm",
        "selected_child_arm",
        "child_heldout_recognized_count",
        "child_regression_recognized_count",
        "child_decoy_false_handoff_count",
        "child_hard_decoy_false_positive_count",
        "shadow_child_used",
        "child_shadow_targeted_success_count",
        "child_shadow_success_delta_vs_parent",
        "long_run_short_finish_reason",
        "parent_foundation_frozen",
        "foundation_unfrozen_in_main_arm",
        "child_used_in_main_runtime",
        "action_ranker_used_for_runtime",
        "runtime_tablebase_or_dtm_move_source",
        "python_final_selector_used",
        "direct_provider_override",
    ):
        print(key, result.decision[key])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
