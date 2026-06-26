#!/usr/bin/env python3
"""Run TG29w reply-robust mature follow-up repair diagnostics."""

from __future__ import annotations

import argparse
from pathlib import Path

from recon_lite_chess.autogrowth import ReplyRobustMatureFollowupRepairConfig, run_reply_robust_mature_followup_repair


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=Path("reports/autogrowth/krk_autogrowth_tg29w_reply_robust_mature_followup_repair.json"))
    parser.add_argument("--summary-output", type=Path, default=Path("reports/autogrowth/krk_autogrowth_tg29w_reply_robust_mature_followup_repair.md"))
    parser.add_argument("--progress-output", type=str, default="reports/autogrowth/krk_autogrowth_tg29w_reply_robust_mature_followup_repair_progress.json")
    args = parser.parse_args()

    cfg = ReplyRobustMatureFollowupRepairConfig(
        base=ReplyRobustMatureFollowupRepairConfig().base.__class__(
            progress_output=args.progress_output,
        )
    )
    result = run_reply_robust_mature_followup_repair(config=cfg)
    json_path = result.write_json(args.output)
    md_path = result.write_markdown(args.summary_output)
    print(f"wrote {json_path}")
    print(f"wrote {md_path}")
    for key in (
        "checkpoint_pass",
        "checkpoint_interpretation",
        "repair_applied",
        "selected_repair_arm",
        "selected_mature_candidate_count",
        "reply_fragile_mature_candidate_count",
        "useful_with_followup_count",
        "foundation_basin_missed_count",
        "followup_ecology_materialized_count",
        "followup_candidate_selected_count",
        "followup_candidate_success_count",
        "targeted_episode_success_count",
        "targeted_episode_count",
        "decoy_correct_rejection_count",
        "decoy_false_handoff_count",
        "foundation_frozen",
        "action_ranker_used_for_runtime",
        "runtime_tablebase_or_dtm_move_source",
        "python_final_selector_used",
        "direct_provider_override",
    ):
        print(key, result.decision[key])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
