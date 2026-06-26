#!/usr/bin/env python3
"""Run TG29y tight follow-up success and frozen foundation basin coverage."""

from __future__ import annotations

import argparse
from pathlib import Path

from recon_lite_chess.autogrowth import (
    TightFollowupSuccessBasinCoverageConfig,
    run_tight_followup_success_basin_coverage,
)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=Path("reports/autogrowth/krk_autogrowth_tg29y_tight_followup_success_basin_coverage.json"))
    parser.add_argument("--summary-output", type=Path, default=Path("reports/autogrowth/krk_autogrowth_tg29y_tight_followup_success_basin_coverage.md"))
    parser.add_argument("--progress-output", type=str, default="reports/autogrowth/krk_autogrowth_tg29y_tight_followup_success_basin_coverage_progress.json")
    args = parser.parse_args()

    cfg = TightFollowupSuccessBasinCoverageConfig(
        base=TightFollowupSuccessBasinCoverageConfig().base.__class__(
            progress_output=args.progress_output,
        )
    )
    result = run_tight_followup_success_basin_coverage(config=cfg)
    json_path = result.write_json(args.output)
    md_path = result.write_markdown(args.summary_output)
    print(f"wrote {json_path}")
    print(f"wrote {md_path}")
    for key in (
        "checkpoint_pass",
        "checkpoint_interpretation",
        "repair_applied",
        "selected_repair_arm",
        "old_followup_success_count",
        "tightened_followup_success_count",
        "false_followup_success_count",
        "basin_boundary_pool_entry_count",
        "basin_boundary_with_partial_support_count",
        "outside_frozen_foundation_basin_count",
        "followup_success_metric_too_weak_count",
        "foundation_basin_too_narrow_count",
        "targeted_episode_success_count",
        "targeted_episode_count",
        "decoy_false_handoff_count",
        "foundation_frozen",
        "foundation_unfrozen_in_main_arm",
        "action_ranker_used_for_runtime",
        "runtime_tablebase_or_dtm_move_source",
        "python_final_selector_used",
        "direct_provider_override",
    ):
        print(key, result.decision[key])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
