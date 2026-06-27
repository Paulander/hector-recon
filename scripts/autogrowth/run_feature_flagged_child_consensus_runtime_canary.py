#!/usr/bin/env python3
"""Run TG35 feature-flagged child-consensus runtime canary."""

from __future__ import annotations

import argparse
from pathlib import Path

from recon_lite_chess.autogrowth import (
    FeatureFlaggedChildConsensusRuntimeCanaryConfig,
    run_feature_flagged_child_consensus_runtime_canary,
)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=Path("reports/autogrowth/krk_autogrowth_tg35_feature_flagged_child_consensus_runtime_canary.json"))
    parser.add_argument("--summary-output", type=Path, default=Path("reports/autogrowth/krk_autogrowth_tg35_feature_flagged_child_consensus_runtime_canary.md"))
    parser.add_argument("--progress-output", type=str, default="reports/autogrowth/krk_autogrowth_tg35_feature_flagged_child_consensus_runtime_canary_progress.json")
    parser.add_argument("--long", action="store_true")
    parser.add_argument("--max-total-seconds", type=int, default=21600)
    parser.add_argument("--min-target-seconds", type=int, default=14400)
    parser.add_argument("--progress-interval-seconds", type=int, default=300)
    parser.add_argument("--episode-tier-start", type=int, default=20000)
    parser.add_argument("--episode-tier-max", type=int, default=250000)
    parser.add_argument("--seed-count", type=int, default=10)
    parser.add_argument("--live-cache-sample-target", type=int, default=5000)
    parser.add_argument("--target-tier", type=int, choices=(1, 2, 3, 4, 5), default=1)
    parser.add_argument("--write-full-logs", action="store_true")
    args = parser.parse_args()

    seed_count = args.seed_count
    sample_target = args.live_cache_sample_target
    if args.long:
        seed_count = max(seed_count, 50)
        sample_target = max(sample_target, 5000)

    cfg = FeatureFlaggedChildConsensusRuntimeCanaryConfig(
        base=FeatureFlaggedChildConsensusRuntimeCanaryConfig().base.__class__(
            progress_output=args.progress_output,
        ),
        long_mode=args.long,
        max_total_seconds=args.max_total_seconds,
        min_target_seconds=args.min_target_seconds if args.long else 0,
        progress_interval_seconds=args.progress_interval_seconds,
        episode_tier_start=args.episode_tier_start,
        episode_tier_max=args.episode_tier_max,
        seed_count=seed_count,
        live_cache_sample_target=sample_target,
        target_tier=args.target_tier,
        write_full_logs=args.write_full_logs,
    )
    result = run_feature_flagged_child_consensus_runtime_canary(config=cfg)
    json_path = result.write_json(args.output)
    md_path = result.write_markdown(args.summary_output)
    print(f"wrote {json_path}")
    print(f"wrote {md_path}")
    for key in (
        "checkpoint_pass",
        "checkpoint_interpretation",
        "artifact_hygiene_applied",
        "large_log_policy",
        "largest_committed_file_bytes",
        "runtime_policy_installed",
        "default_runtime_policy",
        "canary_runtime_policy_name",
        "parent_only_default_unchanged",
        "total_episode_count",
        "paired_episode_count",
        "parent_main_success_count",
        "canary_success_count",
        "canary_success_delta_vs_parent",
        "paired_help_count",
        "paired_hurt_count",
        "paired_net_help",
        "parity_selected_move_mismatch_count",
        "parity_outcome_mismatch_count",
        "parity_gate_mismatch_count",
        "canary_decoy_false_handoff_count",
        "canary_hard_decoy_false_handoff_count",
        "live_cache_sample_count",
        "parent_foundation_frozen",
        "foundation_unfrozen_in_main_arm",
        "child_used_in_main_runtime",
        "child_used_in_experimental_runtime",
        "long_run_short_finish_reason",
    ):
        print(key, result.decision[key])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
