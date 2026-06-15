#!/usr/bin/env python3
"""Run TG26o native ReCoN single-graph KRK curriculum checkpoint."""

from __future__ import annotations

import argparse
from pathlib import Path

from recon_lite_chess.autogrowth import NativeSingleGraphConfig, run_native_single_graph_curriculum


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=Path("reports/autogrowth/krk_autogrowth_tg26o_native_single_graph_curriculum.json"))
    parser.add_argument("--train-repetitions", type=int, default=5)
    parser.add_argument("--continuation-repetitions", type=int, default=2)
    parser.add_argument("--max-ticks", type=int, default=18)
    parser.add_argument("--max-samples", type=int, default=32)
    parser.add_argument("--no-symmetries", action="store_true")
    parser.add_argument("--smoke", action="store_true")
    args = parser.parse_args()

    default_output = Path("reports/autogrowth/krk_autogrowth_tg26o_native_single_graph_curriculum.json")
    output = (
        Path("reports/autogrowth/krk_autogrowth_tg26o_native_single_graph_curriculum_smoke.json")
        if args.smoke and args.output == default_output
        else args.output
    )
    result = run_native_single_graph_curriculum(
        config=NativeSingleGraphConfig(
            include_symmetries=not args.no_symmetries,
            train_repetitions=1 if args.smoke else args.train_repetitions,
            continuation_repetitions=1 if args.smoke else args.continuation_repetitions,
            mate1_threshold=0.0 if args.smoke else 0.98,
            mate2_threshold=0.0 if args.smoke else 0.95,
            max_ticks=args.max_ticks,
            max_samples=args.max_samples,
        )
    )
    path = result.write_json(output)
    payload = result.to_dict()
    print(f"wrote {path}")
    print(
        "mate1",
        payload["mate1"]["evaluation"]["correct_count"],
        "/",
        payload["mate1"]["evaluation"]["position_count"],
    )
    print(
        "mate2",
        payload["mate2"]["evaluation"]["conversion_count"],
        "/",
        payload["mate2"]["evaluation"]["position_count"],
        "same_graph_second_moves",
        payload["mate2"]["evaluation"]["same_graph_second_move_count"],
    )
    print(
        "graph",
        "nodes",
        payload["graph"]["node_count"],
        "edges",
        payload["graph"]["edge_count"],
        "triplets",
        payload["graph"]["triplet_count"],
        "formal_pairs_valid",
        payload["graph"]["formal_pairs_valid"],
    )
    print("checkpoint_pass", payload["decision"]["checkpoint_pass"])
    print("python_batch_scorer_used_for_runtime_choice", payload["purity_boundary"]["python_batch_scorer_used_for_runtime_choice"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
