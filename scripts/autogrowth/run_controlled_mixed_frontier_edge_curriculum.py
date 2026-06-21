#!/usr/bin/env python3
"""Run TG28h controlled mixed frontier and generic edge/fence curriculum."""

from __future__ import annotations

import argparse
from pathlib import Path

from recon_lite_chess.autogrowth import (
    ControlledMixedFrontierEdgeCurriculumConfig,
    run_controlled_mixed_frontier_edge_curriculum,
)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("reports/autogrowth/krk_autogrowth_tg28h_controlled_mixed_frontier_edge_curriculum.json"),
    )
    parser.add_argument(
        "--progress-output",
        type=str,
        default="reports/autogrowth/krk_autogrowth_tg28h_controlled_mixed_frontier_edge_curriculum_progress.json",
    )
    parser.add_argument("--full-pool-path", type=str, default="reports/autogrowth/pools/tg28f_full_foundation_backed_frontier_pool.jsonl")
    parser.add_argument("--generic-edge-train-count", type=int, default=16)
    parser.add_argument("--generic-edge-heldout-count", type=int, default=8)
    parser.add_argument("--near-miss-train-count", type=int, default=8)
    parser.add_argument("--near-miss-heldout-count", type=int, default=8)
    parser.add_argument("--max-cache-candidate-moves", type=int, default=6)
    parser.add_argument("--replay-count", type=int, default=1)
    parser.add_argument("--smoke", action="store_true")
    args = parser.parse_args()

    cfg = ControlledMixedFrontierEdgeCurriculumConfig(
        foundation_mate1_train_count=4 if args.smoke else 32,
        foundation_mate1_heldout_count=2 if args.smoke else 16,
        foundation_mate2_train_count=1 if args.smoke else 16,
        foundation_mate2_heldout_count=1 if args.smoke else 8,
        bridge_frontier_train_count=1 if args.smoke else 8,
        bridge_frontier_heldout_count=1 if args.smoke else 4,
        generic_edge_safety_regression_count=1 if args.smoke else 4,
        max_cache_candidate_moves=3 if args.smoke else args.max_cache_candidate_moves,
        max_ablation_positions=0 if args.smoke else 1,
        max_foundation_sanity_positions=1,
        max_foundation_ablation_positions=1,
        max_samples=4 if args.smoke else 16,
        replay_count=1 if args.smoke else args.replay_count,
        generic_edge_train_count=2 if args.smoke else args.generic_edge_train_count,
        generic_edge_heldout_count=1 if args.smoke else args.generic_edge_heldout_count,
        near_miss_train_count=1 if args.smoke else args.near_miss_train_count,
        near_miss_heldout_count=1 if args.smoke else args.near_miss_heldout_count,
        schedule_names=("mixed_balanced",) if args.smoke else ControlledMixedFrontierEdgeCurriculumConfig().schedule_names,
        full_pool_path=args.full_pool_path,
        progress_output=args.progress_output,
    )
    result = run_controlled_mixed_frontier_edge_curriculum(config=cfg)
    path = result.write_json(args.output)
    decision = result.to_dict()["decision"]
    print(f"wrote {path}")
    for key in (
        "checkpoint_pass",
        "checkpoint_interpretation",
        "selected_training_schedule",
        "frontier_selected_count",
        "frontier_reply_envelope_foundation_reachable_count",
        "near_miss_false_positive_count",
        "generic_selected_count",
        "generic_edge_fence_success_rate",
        "generic_rook_blunder_count",
        "scheduler_equivalence_mismatch_count",
    ):
        print(key, decision[key])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
