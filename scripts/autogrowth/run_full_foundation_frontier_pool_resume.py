#!/usr/bin/env python3
"""Run TG28f full TG27b frontier pool resume checkpoint."""

from __future__ import annotations

import argparse
from pathlib import Path

from recon_lite_chess.autogrowth import (
    FullFoundationFrontierPoolResumeConfig,
    run_full_foundation_frontier_pool_resume,
)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("reports/autogrowth/krk_autogrowth_tg28f_full_foundation_frontier_pool_resume.json"),
    )
    parser.add_argument("--full-pool-path", type=str, default="reports/autogrowth/pools/tg28f_full_foundation_backed_frontier_pool.jsonl")
    parser.add_argument("--full-pool-index-path", type=str, default="reports/autogrowth/pools/tg28f_full_foundation_backed_frontier_pool_index.json")
    parser.add_argument("--compact-pool-path", type=str, default="reports/autogrowth/pools/tg28e_foundation_backed_frontier_pool.jsonl")
    parser.add_argument(
        "--progress-output",
        type=str,
        default="reports/autogrowth/krk_autogrowth_tg28f_full_foundation_frontier_pool_resume_progress.json",
    )
    parser.add_argument("--bridge-frontier-train-count", type=int, default=8)
    parser.add_argument("--bridge-frontier-heldout-count", type=int, default=4)
    parser.add_argument("--generic-edge-safety-regression-count", type=int, default=4)
    parser.add_argument("--minimum-train-count", type=int, default=6)
    parser.add_argument("--minimum-heldout-count", type=int, default=2)
    parser.add_argument("--minimum-regression-count", type=int, default=2)
    parser.add_argument("--max-generation-attempts", type=int, default=250_000)
    parser.add_argument("--max-pool-generation-seconds", type=float, default=780.0)
    parser.add_argument("--max-cache-candidate-moves", type=int, default=12)
    parser.add_argument("--max-ablation-positions", type=int, default=2)
    parser.add_argument("--max-foundation-sanity-positions", type=int, default=2)
    parser.add_argument("--max-foundation-ablation-positions", type=int, default=2)
    parser.add_argument("--replay-count", type=int, default=2)
    parser.add_argument("--smoke", action="store_true")
    args = parser.parse_args()

    cfg = FullFoundationFrontierPoolResumeConfig(
        foundation_mate1_train_count=4 if args.smoke else 32,
        foundation_mate1_heldout_count=2 if args.smoke else 16,
        foundation_mate2_train_count=1 if args.smoke else 16,
        foundation_mate2_heldout_count=1 if args.smoke else 8,
        bridge_frontier_train_count=2 if args.smoke else args.bridge_frontier_train_count,
        bridge_frontier_heldout_count=1 if args.smoke else args.bridge_frontier_heldout_count,
        generic_edge_safety_regression_count=1 if args.smoke else args.generic_edge_safety_regression_count,
        minimum_train_count=1 if args.smoke else args.minimum_train_count,
        minimum_heldout_count=1 if args.smoke else args.minimum_heldout_count,
        minimum_regression_count=1 if args.smoke else args.minimum_regression_count,
        basin_random_count=2 if args.smoke else 8,
        max_generation_attempts=20_000 if args.smoke else args.max_generation_attempts,
        max_pool_generation_seconds=180.0 if args.smoke else args.max_pool_generation_seconds,
        max_cache_candidate_moves=3 if args.smoke else args.max_cache_candidate_moves,
        max_ablation_positions=0 if args.smoke else args.max_ablation_positions,
        max_foundation_sanity_positions=1 if args.smoke else args.max_foundation_sanity_positions,
        max_foundation_ablation_positions=1 if args.smoke else args.max_foundation_ablation_positions,
        max_samples=4 if args.smoke else 16,
        replay_count=1 if args.smoke else args.replay_count,
        compact_pool_path=args.compact_pool_path,
        full_pool_path=args.full_pool_path,
        full_pool_index_path=args.full_pool_index_path,
        progress_output=args.progress_output,
    )
    result = run_full_foundation_frontier_pool_resume(config=cfg)
    path = result.write_json(args.output)
    decision = result.to_dict()["decision"]
    print(f"wrote {path}")
    for key in (
        "checkpoint_pass",
        "checkpoint_interpretation",
        "full_tg27b_config_used",
        "resumed_from_existing_full_pool",
        "full_pool_entry_count",
        "full_pool_train_count",
        "full_pool_heldout_count",
        "full_pool_regression_count",
        "minimum_full_pool_completed",
        "target_full_pool_completed",
        "selected_move_count",
        "reply_envelope_foundation_reachable_count",
        "rook_blunder_count",
        "timeout_count",
        "scheduler_equivalence_mismatch_count",
    ):
        print(key, decision[key])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
