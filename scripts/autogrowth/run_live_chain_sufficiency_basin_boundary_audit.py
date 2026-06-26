#!/usr/bin/env python3
"""Run TG29x live chain-sufficiency and foundation-basin boundary audit."""

from __future__ import annotations

import argparse
from pathlib import Path

from recon_lite_chess.autogrowth import (
    LiveChainSufficiencyBasinBoundaryAuditConfig,
    run_live_chain_sufficiency_basin_boundary_audit,
)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=Path("reports/autogrowth/krk_autogrowth_tg29x_live_chain_sufficiency_basin_boundary_audit.json"))
    parser.add_argument("--summary-output", type=Path, default=Path("reports/autogrowth/krk_autogrowth_tg29x_live_chain_sufficiency_basin_boundary_audit.md"))
    parser.add_argument("--progress-output", type=str, default="reports/autogrowth/krk_autogrowth_tg29x_live_chain_sufficiency_basin_boundary_audit_progress.json")
    args = parser.parse_args()

    cfg = LiveChainSufficiencyBasinBoundaryAuditConfig(
        base=LiveChainSufficiencyBasinBoundaryAuditConfig().base.__class__(
            progress_output=args.progress_output,
        )
    )
    result = run_live_chain_sufficiency_basin_boundary_audit(config=cfg)
    json_path = result.write_json(args.output)
    md_path = result.write_markdown(args.summary_output)
    print(f"wrote {json_path}")
    print(f"wrote {md_path}")
    for key in (
        "checkpoint_pass",
        "checkpoint_interpretation",
        "repair_applied",
        "selected_repair_arm",
        "targeted_episode_count",
        "chain_trace_count",
        "mature_plus_followup_chain_count",
        "chain_reaches_foundation_count",
        "chain_misses_basin_count",
        "followup_success_metric_too_weak_count",
        "foundation_basin_too_narrow_count",
        "better_chain_exists_but_lost_selection_count",
        "targeted_episode_success_count",
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
