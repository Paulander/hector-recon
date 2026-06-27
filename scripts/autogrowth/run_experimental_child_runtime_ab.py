#!/usr/bin/env python3
"""Run TG33 controlled experimental child runtime A/B diagnostic."""

from __future__ import annotations

import argparse
from pathlib import Path

from recon_lite_chess.autogrowth import (
    ExperimentalChildRuntimeABConfig,
    run_experimental_child_runtime_ab,
)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=Path("reports/autogrowth/krk_autogrowth_tg33_experimental_child_runtime_ab.json"))
    parser.add_argument("--summary-output", type=Path, default=Path("reports/autogrowth/krk_autogrowth_tg33_experimental_child_runtime_ab.md"))
    parser.add_argument("--progress-output", type=str, default="reports/autogrowth/krk_autogrowth_tg33_experimental_child_runtime_ab_progress.json")
    parser.add_argument("--long", action="store_true")
    parser.add_argument("--max-total-seconds", type=int, default=21600)
    parser.add_argument("--min-target-seconds", type=int, default=14400)
    parser.add_argument("--progress-interval-seconds", type=int, default=300)
    parser.add_argument("--online-stress", choices=("true", "false"), default="true")
    parser.add_argument("--seed-count", type=int, default=5)
    parser.add_argument("--episode-scale", choices=("smoke", "medium", "long", "max"), default="smoke")
    parser.add_argument("--live-cache-sample-rate", type=float, default=0.05)
    parser.add_argument("--hard-decoy-stress", choices=("true", "false"), default="true")
    parser.add_argument("--target-tier", type=int, choices=(1, 2, 3, 4), default=1)
    args = parser.parse_args()

    target_tier = args.target_tier
    episode_scale = args.episode_scale
    seed_count = args.seed_count
    if args.long:
        target_tier = max(target_tier, 3)
        episode_scale = "long"
        seed_count = max(seed_count, 20)

    cfg = ExperimentalChildRuntimeABConfig(
        base=ExperimentalChildRuntimeABConfig().base.__class__(
            progress_output=args.progress_output,
        ),
        long_mode=args.long,
        max_total_seconds=args.max_total_seconds,
        min_target_seconds=args.min_target_seconds if args.long else 0,
        progress_interval_seconds=args.progress_interval_seconds,
        online_stress=args.online_stress == "true",
        seed_count=seed_count,
        episode_scale=episode_scale,
        live_cache_sample_rate=args.live_cache_sample_rate,
        hard_decoy_stress=args.hard_decoy_stress == "true",
        target_tier=target_tier,
    )
    result = run_experimental_child_runtime_ab(config=cfg)
    json_path = result.write_json(args.output)
    md_path = result.write_markdown(args.summary_output)
    print(f"wrote {json_path}")
    print(f"wrote {md_path}")
    for key in (
        "checkpoint_pass",
        "checkpoint_interpretation",
        "repair_applied",
        "selected_repair_arm",
        "branch_count",
        "selected_experimental_branch",
        "total_episode_count",
        "parent_main_success_count",
        "parent_main_success_rate",
        "experimental_child_success_count",
        "experimental_child_success_rate",
        "experimental_child_success_delta_vs_parent",
        "child_intervention_count",
        "child_helped_success_count",
        "child_hurt_success_count",
        "experimental_decoy_false_handoff_count",
        "experimental_hard_decoy_false_handoff_count",
        "live_cache_sample_count",
        "parent_cache_live_mismatch_count",
        "child_cache_live_mismatch_count",
        "long_run_short_finish_reason",
        "parent_foundation_frozen",
        "foundation_unfrozen_in_main_arm",
        "child_used_in_main_runtime",
        "child_used_in_experimental_runtime",
        "action_ranker_used_for_runtime",
        "runtime_tablebase_or_dtm_move_source",
        "python_final_selector_used",
        "direct_provider_override",
    ):
        print(key, result.decision[key])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
