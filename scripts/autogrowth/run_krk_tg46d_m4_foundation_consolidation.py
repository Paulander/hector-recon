#!/usr/bin/env python3
"""Run TG46d real foundation M4 consolidation repair."""

from __future__ import annotations

import argparse
import json

from recon_lite_chess.autogrowth import (
    M4FoundationConsolidationConfig,
    run_m4_foundation_consolidation,
)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--fresh-graph", action="store_true", help="required guard; no prior learned state")
    parser.add_argument("--seed", type=int, default=20260628)
    parser.add_argument("--mate1-train-count", type=int, default=300)
    parser.add_argument("--mate1-regression-count", type=int, default=100)
    parser.add_argument("--mate2-train-count", type=int, default=300)
    parser.add_argument("--mate2-heldout-count", type=int, default=100)
    parser.add_argument("--mate2-regression-count", type=int, default=100)
    parser.add_argument("--promotion-precision-threshold", type=float, default=0.60)
    parser.add_argument("--output-dir", default=M4FoundationConsolidationConfig().output_dir)
    args = parser.parse_args()

    if not args.fresh_graph:
        raise SystemExit("TG46d requires --fresh-graph")

    output_dir = args.output_dir
    config = M4FoundationConsolidationConfig(
        output_dir=output_dir,
        output_path=f"{output_dir}/krk_tg46d_m4_foundation_consolidation.json",
        progress_path=f"{output_dir}/krk_tg46d_m4_foundation_consolidation_progress.json",
        markdown_path=f"{output_dir}/krk_tg46d_m4_foundation_consolidation.md",
        train_trace_path=f"{output_dir}/pools/tg46d_train_traces.jsonl.gz",
        eval_trace_path=f"{output_dir}/pools/tg46d_eval_traces.jsonl.gz",
        m4_audit_log_path=f"{output_dir}/pools/tg46d_m4_audit.jsonl.gz",
        promotion_candidate_log_path=f"{output_dir}/pools/tg46d_promotion_candidates.jsonl.gz",
        m4_only_eval_log_path=f"{output_dir}/pools/tg46d_m4_only_eval.jsonl.gz",
        graph_summary_path=f"{output_dir}/pools/tg46d_graph_summary.json",
        promoted_foundation_artifact_path=f"{output_dir}/promoted_tg46d_foundation.json",
        seed=args.seed,
        mate1_train_count=args.mate1_train_count,
        mate1_regression_count=args.mate1_regression_count,
        mate2_train_count=args.mate2_train_count,
        mate2_heldout_count=args.mate2_heldout_count,
        mate2_regression_count=args.mate2_regression_count,
        promotion_precision_threshold=args.promotion_precision_threshold,
        fresh_graph=True,
    )
    result = run_m4_foundation_consolidation(config=config)
    print(json.dumps(result.decision, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
