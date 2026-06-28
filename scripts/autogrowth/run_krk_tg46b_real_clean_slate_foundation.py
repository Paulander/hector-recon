#!/usr/bin/env python3
"""Run TG46b real clean-slate KRK foundation."""

from __future__ import annotations

import argparse
import json

from recon_lite_chess.autogrowth import (
    RealCleanSlateFoundationConfig,
    run_real_clean_slate_krk_foundation,
)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--fresh-graph", action="store_true", help="required guard; start from no learned artifacts")
    parser.add_argument("--seed", type=int, default=20260628)
    parser.add_argument("--mate1-train-count", type=int, default=300)
    parser.add_argument("--mate1-heldout-count", type=int, default=100)
    parser.add_argument("--mate2-train-count", type=int, default=300)
    parser.add_argument("--mate2-heldout-count", type=int, default=100)
    parser.add_argument("--max-generation-attempts", type=int, default=500_000)
    parser.add_argument("--eta-m3", type=float, default=0.10)
    parser.add_argument("--rich-feature-credit-scale", type=float, default=0.25)
    parser.add_argument("--output-dir", default=str(RealCleanSlateFoundationConfig().output_dir))
    args = parser.parse_args()

    if not args.fresh_graph:
        raise SystemExit("TG46b requires --fresh-graph")

    cfg = RealCleanSlateFoundationConfig(
        output_dir=args.output_dir,
        output_path=f"{args.output_dir}/krk_tg46b_real_clean_slate_foundation.json",
        progress_path=f"{args.output_dir}/krk_tg46b_real_clean_slate_foundation_progress.json",
        markdown_path=f"{args.output_dir}/krk_tg46b_real_clean_slate_foundation.md",
        mate1_train_trace_path=f"{args.output_dir}/pools/tg46b_mate1_train_traces.jsonl.gz",
        mate1_eval_trace_path=f"{args.output_dir}/pools/tg46b_mate1_eval_traces.jsonl.gz",
        mate2_train_trace_path=f"{args.output_dir}/pools/tg46b_mate2_train_traces.jsonl.gz",
        mate2_eval_trace_path=f"{args.output_dir}/pools/tg46b_mate2_eval_traces.jsonl.gz",
        failure_pool_path=f"{args.output_dir}/pools/tg46b_failure_pool.jsonl.gz",
        graph_summary_path=f"{args.output_dir}/pools/tg46b_graph_summary.json",
        seed=args.seed,
        mate1_train_count=args.mate1_train_count,
        mate1_heldout_count=args.mate1_heldout_count,
        mate2_train_count=args.mate2_train_count,
        mate2_heldout_count=args.mate2_heldout_count,
        max_generation_attempts=args.max_generation_attempts,
        eta_m3=args.eta_m3,
        rich_feature_credit_scale=args.rich_feature_credit_scale,
        fresh_graph=True,
    )
    result = run_real_clean_slate_krk_foundation(config=cfg)
    print(json.dumps(result.decision, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
