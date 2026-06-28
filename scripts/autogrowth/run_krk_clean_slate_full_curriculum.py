#!/usr/bin/env python3
"""Run TG46 clean-slate KRK full-curriculum bootstrap."""

from __future__ import annotations

import argparse
from pathlib import Path

from recon_lite_chess.autogrowth import (
    CleanSlateKRKFullCurriculumConfig,
    run_clean_slate_krk_full_curriculum,
)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--fresh-graph", action="store_true", required=True)
    parser.add_argument("--output", type=Path, default=Path("reports/autogrowth/clean_slate_krk/krk_clean_slate_full_curriculum_bootstrap.json"))
    parser.add_argument("--progress-output", type=Path, default=Path("reports/autogrowth/clean_slate_krk/krk_clean_slate_full_curriculum_bootstrap_progress.json"))
    parser.add_argument("--summary-output", type=Path, default=Path("reports/autogrowth/clean_slate_krk/krk_clean_slate_full_curriculum_bootstrap.md"))
    parser.add_argument("--mate1-heldout", type=int, default=200)
    parser.add_argument("--mate2-heldout", type=int, default=120)
    parser.add_argument("--edge-heldout", type=int, default=160)
    args = parser.parse_args()

    cfg = CleanSlateKRKFullCurriculumConfig(
        output_path=str(args.output),
        progress_path=str(args.progress_output),
        markdown_path=str(args.summary_output),
        fresh_graph=args.fresh_graph,
        mate1_heldout_count=args.mate1_heldout,
        mate2_heldout_count=args.mate2_heldout,
        edge_fence_heldout_count=args.edge_heldout,
    )
    result = run_clean_slate_krk_full_curriculum(config=cfg)
    result.write_json(args.output)
    result.write_markdown(args.summary_output)
    d = result.decision
    print(f"wrote {args.output}")
    print(f"wrote {args.summary_output}")
    for key in (
        "checkpoint_pass",
        "checkpoint_interpretation",
        "fresh_graph",
        "full_curriculum_attempted",
        "full_curriculum_completed",
        "first_failed_stage",
        "loaded_prior_tg_artifact_count",
        "loaded_prior_boundary_pool_count",
        "checkpoint_specific_move_rule_count",
        "mate1_heldout_accuracy",
        "mate2_heldout_conversion_rate",
        "edge_fence_success_rate",
        "selected_next_action",
        "selected_next_action_reason",
    ):
        print(key, d[key])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
