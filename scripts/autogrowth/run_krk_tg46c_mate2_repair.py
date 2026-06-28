#!/usr/bin/env python3
"""Run TG46c real clean-slate Mate-in-2 foundation repair."""

from __future__ import annotations

import argparse
import json

from recon_lite_chess.autogrowth import Mate2FoundationRepairConfig, run_mate2_foundation_repair


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--fresh-graph", action="store_true", help="required guard; no prior learned state")
    parser.add_argument("--seed", type=int, default=20260628)
    parser.add_argument("--mate1-train-count", type=int, default=300)
    parser.add_argument("--mate1-regression-count", type=int, default=100)
    parser.add_argument("--mate2-train-count", type=int, default=300)
    parser.add_argument("--mate2-heldout-count", type=int, default=100)
    parser.add_argument("--mate2-regression-count", type=int, default=100)
    parser.add_argument("--pairwise-epochs", type=int, default=1)
    parser.add_argument("--pairwise-top-k", type=int, default=1)
    parser.add_argument("--pairwise-wrong-debt", type=float, default=-0.20)
    parser.add_argument("--output-dir", default=Mate2FoundationRepairConfig().output_dir)
    args = parser.parse_args()

    if not args.fresh_graph:
        raise SystemExit("TG46c requires --fresh-graph")

    output_dir = args.output_dir
    config = Mate2FoundationRepairConfig(
        output_dir=output_dir,
        output_path=f"{output_dir}/krk_tg46c_real_mate2_repair.json",
        progress_path=f"{output_dir}/krk_tg46c_real_mate2_repair_progress.json",
        markdown_path=f"{output_dir}/krk_tg46c_real_mate2_repair.md",
        train_trace_path=f"{output_dir}/pools/tg46c_train_traces.jsonl.gz",
        eval_trace_path=f"{output_dir}/pools/tg46c_eval_traces.jsonl.gz",
        failure_pool_path=f"{output_dir}/pools/tg46c_failure_pool.jsonl.gz",
        repair_arm_log_path=f"{output_dir}/pools/tg46c_repair_arm_comparison.jsonl.gz",
        m4_audit_log_path=f"{output_dir}/pools/tg46c_m4_audit.jsonl.gz",
        graph_summary_path=f"{output_dir}/pools/tg46c_graph_summary.json",
        seed=args.seed,
        mate1_train_count=args.mate1_train_count,
        mate1_regression_count=args.mate1_regression_count,
        mate2_train_count=args.mate2_train_count,
        mate2_heldout_count=args.mate2_heldout_count,
        mate2_regression_count=args.mate2_regression_count,
        pairwise_epochs=args.pairwise_epochs,
        pairwise_top_k=args.pairwise_top_k,
        pairwise_wrong_debt=args.pairwise_wrong_debt,
        fresh_graph=True,
    )
    result = run_mate2_foundation_repair(config=config)
    print(json.dumps(result.decision, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
