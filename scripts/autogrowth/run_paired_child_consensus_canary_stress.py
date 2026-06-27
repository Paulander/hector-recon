#!/usr/bin/env python3
"""Run TG34 paired child-consensus canary stress diagnostic."""

from __future__ import annotations

import argparse
from pathlib import Path

from recon_lite_chess.autogrowth import (
    PairedChildConsensusCanaryStressConfig,
    run_paired_child_consensus_canary_stress,
)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=Path("reports/autogrowth/krk_autogrowth_tg34_paired_child_consensus_canary_stress.json"))
    parser.add_argument("--summary-output", type=Path, default=Path("reports/autogrowth/krk_autogrowth_tg34_paired_child_consensus_canary_stress.md"))
    parser.add_argument("--progress-output", type=str, default="reports/autogrowth/krk_autogrowth_tg34_paired_child_consensus_canary_stress_progress.json")
    parser.add_argument("--long", action="store_true")
    parser.add_argument("--max-total-seconds", type=int, default=21600)
    parser.add_argument("--min-target-seconds", type=int, default=14400)
    parser.add_argument("--progress-interval-seconds", type=int, default=300)
    parser.add_argument("--paired-ab", choices=("true", "false"), default="true")
    parser.add_argument("--episode-tier-start", type=int, default=20000)
    parser.add_argument("--episode-tier-max", type=int, default=250000)
    parser.add_argument("--seed-count", type=int, default=10)
    parser.add_argument("--live-cache-sample-target", type=int, default=250)
    parser.add_argument("--hard-decoy-stress", choices=("true", "false"), default="true")
    parser.add_argument("--adaptive-stress", choices=("true", "false"), default="true")
    parser.add_argument("--target-tier", type=int, choices=(1, 2, 3, 4), default=1)
    args = parser.parse_args()

    target_tier = args.target_tier
    seed_count = args.seed_count
    sample_target = args.live_cache_sample_target
    if args.long:
        seed_count = max(seed_count, 50)
        sample_target = max(sample_target, 1000)

    cfg = PairedChildConsensusCanaryStressConfig(
        base=PairedChildConsensusCanaryStressConfig().base.__class__(
            progress_output=args.progress_output,
        ),
        long_mode=args.long,
        max_total_seconds=args.max_total_seconds,
        min_target_seconds=args.min_target_seconds if args.long else 0,
        progress_interval_seconds=args.progress_interval_seconds,
        paired_ab=args.paired_ab == "true",
        episode_tier_start=args.episode_tier_start,
        episode_tier_max=args.episode_tier_max,
        seed_count=seed_count,
        live_cache_sample_target=sample_target,
        hard_decoy_stress=args.hard_decoy_stress == "true",
        adaptive_stress=args.adaptive_stress == "true",
        target_tier=target_tier,
    )
    result = run_paired_child_consensus_canary_stress(config=cfg)
    json_path = result.write_json(args.output)
    md_path = result.write_markdown(args.summary_output)
    print(f"wrote {json_path}")
    print(f"wrote {md_path}")
    for key in (
        "checkpoint_pass",
        "checkpoint_interpretation",
        "repair_applied",
        "selected_repair_arm",
        "selected_canary_branch",
        "total_episode_count",
        "paired_episode_count",
        "parent_main_success_count",
        "tg33_experimental_success_count",
        "canary_success_count",
        "canary_success_delta_vs_parent",
        "paired_help_count",
        "paired_hurt_count",
        "paired_net_help",
        "canary_decoy_false_handoff_count",
        "canary_hard_decoy_false_handoff_count",
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
