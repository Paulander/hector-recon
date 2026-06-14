#!/usr/bin/env python3
"""Run TG26n single persistent graph KRK curriculum checkpoint."""

from __future__ import annotations

import argparse
from pathlib import Path

from recon_lite_chess.autogrowth import SingleGraphCurriculumConfig, run_single_graph_curriculum


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=Path("reports/autogrowth/krk_autogrowth_tg26n_single_graph_curriculum.json"))
    parser.add_argument("--train-repetitions", type=int, default=5)
    parser.add_argument("--continuation-repetitions", type=int, default=2)
    parser.add_argument("--max-samples", type=int, default=32)
    parser.add_argument(
        "--score-context-free-action-terminals",
        action="store_true",
        help="Restore the older flat action-pattern terminal contribution to move scores.",
    )
    parser.add_argument("--max-abs-local-weight", type=float, default=1.0)
    parser.add_argument("--no-symmetries", action="store_true")
    parser.add_argument("--smoke", action="store_true")
    args = parser.parse_args()

    default_output = Path("reports/autogrowth/krk_autogrowth_tg26n_single_graph_curriculum.json")
    output = (
        Path("reports/autogrowth/krk_autogrowth_tg26n_single_graph_curriculum_smoke.json")
        if args.smoke and args.output == default_output
        else args.output
    )
    result = run_single_graph_curriculum(
        config=SingleGraphCurriculumConfig(
            include_symmetries=not args.no_symmetries,
            train_repetitions=1 if args.smoke else args.train_repetitions,
            continuation_repetitions=1 if args.smoke else args.continuation_repetitions,
            score_context_free_action_terminals=args.score_context_free_action_terminals,
            max_abs_local_weight=args.max_abs_local_weight,
            mate1_threshold=0.0 if args.smoke else 0.98,
            mate2_threshold=0.0 if args.smoke else 0.95,
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
        "terminals",
        payload["graph"]["terminal_substrate"]["terminal_count"],
        "triplets",
        payload["graph"]["triplet_count"],
        "mature_triplets",
        payload["graph"]["mature_triplet_count"],
    )
    print("checkpoint_pass", payload["decision"]["checkpoint_pass"])
    print("hardcoded_mate1_handoff", payload["purity_boundary"]["hardcoded_mate1_handoff"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
