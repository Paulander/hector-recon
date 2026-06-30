#!/usr/bin/env python3
"""Run TG48a edge-killbox curriculum."""

from __future__ import annotations

import argparse
import json

from recon_lite_chess.autogrowth import (
    EdgeKillboxCurriculumConfig,
    run_edge_killbox_curriculum,
)


DEFAULT_OUTPUT_DIR = "reports/autogrowth/clean_slate_krk/tg48a_edge_killbox_curriculum"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--run-scale-label", default="smoke")
    parser.add_argument("--seed", type=int, default=20260630)
    parser.add_argument("--train-count", type=int, default=60)
    parser.add_argument("--heldout-count", type=int, default=24)
    parser.add_argument("--regression-count", type=int, default=24)
    parser.add_argument("--decoy-count", type=int, default=24)
    parser.add_argument("--hard-decoy-count", type=int, default=24)
    parser.add_argument("--max-generation-attempts", type=int, default=250_000)
    parser.add_argument("--max-horizon-plies", type=int, default=6)
    args = parser.parse_args()

    output_dir = args.output_dir
    config = EdgeKillboxCurriculumConfig(
        output_dir=output_dir,
        output_path=f"{output_dir}/krk_tg48a_edge_killbox_curriculum.json",
        markdown_path=f"{output_dir}/krk_tg48a_edge_killbox_curriculum.md",
        train_trace_path=f"{output_dir}/pools/tg48a_train_traces.jsonl.gz",
        eval_trace_path=f"{output_dir}/pools/tg48a_eval_traces.jsonl.gz",
        failure_pool_path=f"{output_dir}/pools/tg48a_failure_pool.jsonl.gz",
        generator_samples_path=f"{output_dir}/pools/tg48a_generator_samples.jsonl.gz",
        graph_summary_path=f"{output_dir}/pools/tg48a_graph_summary.json",
        run_scale_label=args.run_scale_label,
        seed=args.seed,
        train_count=args.train_count,
        heldout_count=args.heldout_count,
        regression_count=args.regression_count,
        decoy_count=args.decoy_count,
        hard_decoy_count=args.hard_decoy_count,
        max_generation_attempts=args.max_generation_attempts,
        max_horizon_plies=args.max_horizon_plies,
    )
    result = run_edge_killbox_curriculum(config=config)
    print(json.dumps(result.decision, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
