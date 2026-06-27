#!/usr/bin/env python3
"""Run TG30 boundary dataset expansion and child coverage ladder."""

from __future__ import annotations

import argparse
from pathlib import Path

from recon_lite_chess.autogrowth import (
    BoundaryDatasetExpansionChildCoverageConfig,
    run_boundary_dataset_expansion_child_coverage_ladder,
)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=Path("reports/autogrowth/krk_autogrowth_tg30_boundary_dataset_expansion_child_coverage_ladder.json"))
    parser.add_argument("--summary-output", type=Path, default=Path("reports/autogrowth/krk_autogrowth_tg30_boundary_dataset_expansion_child_coverage_ladder.md"))
    parser.add_argument("--progress-output", type=str, default="reports/autogrowth/krk_autogrowth_tg30_boundary_dataset_expansion_child_coverage_ladder_progress.json")
    args = parser.parse_args()

    cfg = BoundaryDatasetExpansionChildCoverageConfig(
        base=BoundaryDatasetExpansionChildCoverageConfig().base.__class__(
            progress_output=args.progress_output,
        )
    )
    result = run_boundary_dataset_expansion_child_coverage_ladder(config=cfg)
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
        "boundary_train_count",
        "boundary_heldout_count",
        "boundary_regression_count",
        "boundary_decoy_count",
        "parent_recognized_count",
        "parent_partial_support_count",
        "selected_child_arm",
        "child_heldout_recognized_count",
        "child_regression_recognized_count",
        "child_decoy_recognized_count",
        "child_heldout_boundary_coverage_rate",
        "child_decoy_false_handoff_count",
        "shadow_child_used",
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


if __name__ == "__main__":
    raise SystemExit(main())
