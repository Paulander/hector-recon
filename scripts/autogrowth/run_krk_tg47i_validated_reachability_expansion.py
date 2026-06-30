#!/usr/bin/env python3
"""Run TG47i validated reachability expansion audit."""

from __future__ import annotations

import argparse
import json

from recon_lite_chess.autogrowth import (
    ValidatedReachabilityExpansionConfig,
    run_validated_reachability_expansion,
)


DEFAULT_OUTPUT_DIR = "reports/autogrowth/clean_slate_krk/tg47i_validated_reachability_expansion"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--max-positions", type=int, default=None)
    parser.add_argument("--first-move-mode", choices=["selected_only", "top_k", "exhaustive"], default="top_k")
    parser.add_argument("--second-move-mode", choices=["top_k", "exhaustive"], default="exhaustive")
    parser.add_argument("--top-k-first", type=int, default=3)
    parser.add_argument("--top-k-second", type=int, default=3)
    parser.add_argument("--max-white-horizon", type=int, choices=[2, 3], default=2)
    args = parser.parse_args()

    output_dir = args.output_dir
    config = ValidatedReachabilityExpansionConfig(
        output_dir=output_dir,
        output_path=f"{output_dir}/krk_tg47i_validated_reachability_expansion.json",
        markdown_path=f"{output_dir}/krk_tg47i_validated_reachability_expansion.md",
        trace_path=f"{output_dir}/pools/tg47i_validated_reachability_traces.jsonl.gz",
        boundary_failure_path=f"{output_dir}/pools/tg47i_boundary_failures.jsonl.gz",
        partial_near_basin_path=f"{output_dir}/pools/tg47i_validated_partial_near_basin.jsonl.gz",
        max_positions=args.max_positions,
        first_move_mode=args.first_move_mode,
        second_move_mode=args.second_move_mode,
        top_k_first=args.top_k_first,
        top_k_second=args.top_k_second,
        max_white_horizon=args.max_white_horizon,
    )
    result = run_validated_reachability_expansion(config=config)
    print(json.dumps(result.decision, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
