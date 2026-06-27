#!/usr/bin/env python3
"""Run TG31 child boundary coverage scale and shadow stability diagnostic."""

from __future__ import annotations

import argparse
from pathlib import Path

from recon_lite_chess.autogrowth import (
    ChildBoundaryCoverageScaleShadowStabilityConfig,
    run_child_boundary_coverage_scale_shadow_stability,
)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=Path("reports/autogrowth/krk_autogrowth_tg31_child_boundary_coverage_scale_shadow_stability.json"))
    parser.add_argument("--summary-output", type=Path, default=Path("reports/autogrowth/krk_autogrowth_tg31_child_boundary_coverage_scale_shadow_stability.md"))
    parser.add_argument("--progress-output", type=str, default="reports/autogrowth/krk_autogrowth_tg31_child_boundary_coverage_scale_shadow_stability_progress.json")
    parser.add_argument("--long", action="store_true", help="Use the long-run target sizes and cycle schedule.")
    parser.add_argument("--max-total-seconds", type=int, default=21600)
    parser.add_argument("--min-target-seconds", type=int, default=14400)
    parser.add_argument("--progress-interval-seconds", type=int, default=300)
    parser.add_argument("--boundary-target-scale", choices=("minimum", "preferred", "stretch"), default="minimum")
    parser.add_argument("--child-cycle-scale", choices=("short", "medium", "long"), default="short")
    parser.add_argument("--multi-seed-count", type=int, default=3)
    args = parser.parse_args()

    train, heldout, regression, decoy = _targets(args.boundary_target_scale, args.long)
    cycle_scale = args.child_cycle_scale
    seed_count = args.multi_seed_count
    if args.long:
        cycle_scale = "medium" if cycle_scale == "short" else cycle_scale
        seed_count = max(seed_count, 5)

    cfg = ChildBoundaryCoverageScaleShadowStabilityConfig(
        base=ChildBoundaryCoverageScaleShadowStabilityConfig().base.__class__(
            progress_output=args.progress_output,
        ),
        long_mode=args.long,
        max_total_seconds=args.max_total_seconds,
        min_target_seconds=args.min_target_seconds if args.long else 0,
        progress_interval_seconds=args.progress_interval_seconds,
        boundary_target_scale=args.boundary_target_scale,
        child_cycle_scale=cycle_scale,
        multi_seed_count=seed_count,
        target_train_count=train,
        target_heldout_count=heldout,
        target_regression_count=regression,
        target_decoy_count=decoy,
    )
    result = run_child_boundary_coverage_scale_shadow_stability(config=cfg)
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
        "boundary_train_count",
        "boundary_heldout_count",
        "boundary_regression_count",
        "boundary_decoy_count",
        "parent_recognized_count",
        "parent_partial_support_count",
        "child_arm_count",
        "child_seed_count",
        "cycles_per_arm",
        "selected_child_arm",
        "child_heldout_recognized_count",
        "child_regression_recognized_count",
        "child_decoy_recognized_count",
        "child_heldout_boundary_coverage_rate",
        "child_worst_seed_heldout_coverage_rate",
        "child_decoy_false_handoff_count",
        "shadow_child_used",
        "child_shadow_targeted_success_count",
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


def _targets(scale: str, long: bool) -> tuple[int, int, int, int]:
    if scale == "stretch":
        return 384, 256, 192, 192
    if scale == "preferred" or long:
        return 192, 128, 96, 96
    return 96, 64, 48, 48


if __name__ == "__main__":
    raise SystemExit(main())
