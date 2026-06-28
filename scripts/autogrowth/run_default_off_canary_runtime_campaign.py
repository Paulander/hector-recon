#!/usr/bin/env python3
"""Run TG39-TG45 default-off child-consensus canary campaign."""

from __future__ import annotations

import argparse
from pathlib import Path

from recon_lite_chess.autogrowth import (
    DefaultOffCanaryRuntimeCampaignConfig,
    run_default_off_canary_runtime_campaign,
)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=Path("reports/autogrowth/krk_autogrowth_tg39_tg45_default_off_canary_runtime_campaign.json"))
    parser.add_argument("--summary-output", type=Path, default=Path("reports/autogrowth/krk_autogrowth_tg39_tg45_default_off_canary_runtime_campaign.md"))
    parser.add_argument("--progress-output", type=str, default="reports/autogrowth/krk_autogrowth_tg39_tg45_default_off_canary_runtime_campaign_progress.json")
    parser.add_argument("--long", action="store_true")
    parser.add_argument("--target-tier", type=int, choices=(1, 2, 3, 4, 5), default=1)
    parser.add_argument("--stage-play-tier-start", type=int, default=100000)
    parser.add_argument("--stage-play-tier-max", type=int, default=2000000)
    parser.add_argument("--hard-decoy-count", type=int, default=10000)
    parser.add_argument("--live-recompute-sample-target", type=int, default=50000)
    parser.add_argument("--seed-count", type=int, default=50)
    parser.add_argument("--max-total-seconds", type=int, default=36000)
    parser.add_argument("--min-target-seconds", type=int, default=28800)
    args = parser.parse_args()

    cfg = DefaultOffCanaryRuntimeCampaignConfig(
        base=DefaultOffCanaryRuntimeCampaignConfig().base.__class__(
            progress_output=args.progress_output,
        ),
        long_mode=args.long,
        target_tier=args.target_tier,
        stage_play_tier_start=args.stage_play_tier_start,
        stage_play_tier_max=args.stage_play_tier_max,
        hard_decoy_count=args.hard_decoy_count,
        live_recompute_sample_target=args.live_recompute_sample_target,
        seed_count=args.seed_count,
        max_total_seconds=args.max_total_seconds,
        min_target_seconds=args.min_target_seconds if args.long else 0,
        campaign_output_path=str(args.output),
        campaign_markdown_path=str(args.summary_output),
    )
    result = run_default_off_canary_runtime_campaign(config=cfg)
    result.write_json(args.output)
    result.write_markdown(args.summary_output)
    d = result.campaign["decision"]
    print(f"wrote {args.output}")
    print(f"wrote {args.summary_output}")
    for key in (
        "campaign_checkpoint_pass",
        "campaign_interpretation",
        "phases_completed",
        "paired_stage_play_episode_count",
        "parent_stage_play_success_rate",
        "canary_stage_play_success_rate",
        "canary_stage_play_success_delta",
        "paired_help_count",
        "paired_hurt_count",
        "hard_decoy_count",
        "live_recompute_sample_count",
        "live_cache_mismatch_count",
        "selected_next_action",
        "selected_next_action_reason",
        "overnight_budget_used_reason",
    ):
        print(key, d[key])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
