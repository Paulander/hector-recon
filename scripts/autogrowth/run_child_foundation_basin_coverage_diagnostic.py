#!/usr/bin/env python3
"""Run TG29z frozen-parent child foundation basin coverage diagnostic."""

from __future__ import annotations

import argparse
from pathlib import Path

from recon_lite_chess.autogrowth import (
    ChildFoundationBasinCoverageConfig,
    run_child_foundation_basin_coverage_diagnostic,
)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=Path("reports/autogrowth/krk_autogrowth_tg29z_child_foundation_basin_coverage_diagnostic.json"))
    parser.add_argument("--summary-output", type=Path, default=Path("reports/autogrowth/krk_autogrowth_tg29z_child_foundation_basin_coverage_diagnostic.md"))
    parser.add_argument("--progress-output", type=str, default="reports/autogrowth/krk_autogrowth_tg29z_child_foundation_basin_coverage_diagnostic_progress.json")
    args = parser.parse_args()

    cfg = ChildFoundationBasinCoverageConfig(
        base=ChildFoundationBasinCoverageConfig().base.__class__(
            progress_output=args.progress_output,
        )
    )
    result = run_child_foundation_basin_coverage_diagnostic(config=cfg)
    json_path = result.write_json(args.output)
    md_path = result.write_markdown(args.summary_output)
    print(f"wrote {json_path}")
    print(f"wrote {md_path}")
    for key in (
        "checkpoint_pass",
        "checkpoint_interpretation",
        "repair_applied",
        "selected_repair_arm",
        "parent_boundary_state_count",
        "parent_recognized_boundary_count",
        "parent_partial_support_count",
        "parent_outside_basin_count",
        "child_branch_created",
        "child_train_recognized_count",
        "child_heldout_recognized_count",
        "child_regression_recognized_count",
        "child_boundary_coverage_rate",
        "child_heldout_boundary_coverage_rate",
        "child_learns_train_only_count",
        "child_fails_boundary_count",
        "child_decoy_false_handoff_count",
        "parent_foundation_frozen",
        "foundation_unfrozen_in_main_arm",
        "child_used_in_main_runtime",
        "child_used_in_shadow_only",
        "action_ranker_used_for_runtime",
        "runtime_tablebase_or_dtm_move_source",
        "python_final_selector_used",
        "direct_provider_override",
    ):
        print(key, result.decision[key])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
