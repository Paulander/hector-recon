#!/usr/bin/env python3
"""Run TG36-TG38 KRK runtime stage-gate campaign."""

from __future__ import annotations

import argparse
from pathlib import Path

from recon_lite_chess.autogrowth import (
    RuntimeStageGateCampaignConfig,
    run_runtime_stage_gate_campaign,
)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=Path("reports/autogrowth/krk_autogrowth_tg36_tg38_runtime_stage_gate_campaign.json"))
    parser.add_argument("--summary-output", type=Path, default=Path("reports/autogrowth/krk_autogrowth_tg36_tg38_runtime_stage_gate_campaign.md"))
    parser.add_argument("--progress-output", type=str, default="reports/autogrowth/krk_autogrowth_tg36_tg38_runtime_stage_gate_campaign_progress.json")
    parser.add_argument("--long", action="store_true")
    parser.add_argument("--target-tier", type=int, choices=(1, 2, 3, 4, 5), default=1)
    parser.add_argument("--stage-play-tier-start", type=int, default=50000)
    parser.add_argument("--stage-play-tier-max", type=int, default=1000000)
    parser.add_argument("--seed-count", type=int, default=50)
    parser.add_argument("--live-cache-sample-target", type=int, default=10000)
    parser.add_argument("--parity-episode-count", type=int, default=2000)
    parser.add_argument("--max-total-seconds", type=int, default=36000)
    parser.add_argument("--min-target-seconds", type=int, default=28800)
    args = parser.parse_args()

    seed_count = args.seed_count
    live_cache_sample_target = args.live_cache_sample_target
    parity_episode_count = args.parity_episode_count
    if args.long:
        seed_count = max(seed_count, 50)
        live_cache_sample_target = max(live_cache_sample_target, 10000)
        parity_episode_count = max(parity_episode_count, 2000)

    cfg = RuntimeStageGateCampaignConfig(
        base=RuntimeStageGateCampaignConfig().base.__class__(
            progress_output=args.progress_output,
        ),
        long_mode=args.long,
        target_tier=args.target_tier,
        stage_play_tier_start=args.stage_play_tier_start,
        stage_play_tier_max=args.stage_play_tier_max,
        seed_count=seed_count,
        live_cache_sample_target=live_cache_sample_target,
        parity_episode_count=parity_episode_count,
        max_total_seconds=args.max_total_seconds,
        min_target_seconds=args.min_target_seconds if args.long else 0,
        campaign_output_path=str(args.output),
        campaign_markdown_path=str(args.summary_output),
    )
    result = run_runtime_stage_gate_campaign(config=cfg)
    result.write_json(args.output)
    result.write_markdown(args.summary_output)
    decision = result.campaign["decision"]
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
        "paired_net_help",
        "decoy_false_handoff_count",
        "hard_decoy_false_handoff_count",
        "live_cache_sample_count",
        "parent_cache_live_mismatch_count",
        "child_cache_live_mismatch_count",
        "selected_next_action",
        "selected_next_action_reason",
        "overnight_budget_used_reason",
    ):
        print(key, decision[key])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
