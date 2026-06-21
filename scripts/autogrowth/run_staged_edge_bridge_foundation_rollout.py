#!/usr/bin/env python3
"""Run TG28i short staged edge/fence -> bridge -> frozen foundation rollout."""

from __future__ import annotations

import argparse
from pathlib import Path

from recon_lite_chess.autogrowth import (
    StagedEdgeBridgeFoundationRolloutConfig,
    run_staged_edge_bridge_foundation_rollout,
)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("reports/autogrowth/krk_autogrowth_tg28i_staged_edge_bridge_foundation_rollout.json"),
    )
    parser.add_argument(
        "--progress-output",
        type=str,
        default="reports/autogrowth/krk_autogrowth_tg28i_staged_edge_bridge_foundation_rollout_progress.json",
    )
    parser.add_argument("--full-pool-path", type=str, default="reports/autogrowth/pools/tg28f_full_foundation_backed_frontier_pool.jsonl")
    parser.add_argument("--bridge-frontier-train-count", type=int, default=8)
    parser.add_argument("--bridge-frontier-heldout-count", type=int, default=4)
    parser.add_argument("--generic-edge-train-count", type=int, default=16)
    parser.add_argument("--generic-edge-heldout-count", type=int, default=8)
    parser.add_argument("--near-miss-train-count", type=int, default=8)
    parser.add_argument("--near-miss-heldout-count", type=int, default=8)
    parser.add_argument("--staged-train-count", type=int, default=4)
    parser.add_argument("--staged-heldout-count", type=int, default=4)
    parser.add_argument("--max-staged-source-positions", type=int, default=StagedEdgeBridgeFoundationRolloutConfig().max_staged_source_positions)
    parser.add_argument("--max-staged-first-move-candidates", type=int, default=StagedEdgeBridgeFoundationRolloutConfig().max_staged_first_move_candidates)
    parser.add_argument("--max-cache-candidate-moves", type=int, default=6)
    parser.add_argument("--max-ablation-positions", type=int, default=1)
    parser.add_argument("--smoke", action="store_true")
    args = parser.parse_args()

    cfg = StagedEdgeBridgeFoundationRolloutConfig(
        foundation_mate1_train_count=4 if args.smoke else 32,
        foundation_mate1_heldout_count=2 if args.smoke else 16,
        foundation_mate2_train_count=1 if args.smoke else 16,
        foundation_mate2_heldout_count=1 if args.smoke else 8,
        bridge_frontier_train_count=1 if args.smoke else args.bridge_frontier_train_count,
        bridge_frontier_heldout_count=1 if args.smoke else args.bridge_frontier_heldout_count,
        generic_edge_safety_regression_count=1 if args.smoke else 8,
        max_cache_candidate_moves=3 if args.smoke else args.max_cache_candidate_moves,
        max_ablation_positions=0 if args.smoke else args.max_ablation_positions,
        max_foundation_sanity_positions=1,
        max_foundation_ablation_positions=1,
        max_samples=4 if args.smoke else 16,
        replay_count=1,
        generic_edge_train_count=2 if args.smoke else args.generic_edge_train_count,
        generic_edge_heldout_count=1 if args.smoke else args.generic_edge_heldout_count,
        near_miss_train_count=1 if args.smoke else args.near_miss_train_count,
        near_miss_heldout_count=1 if args.smoke else args.near_miss_heldout_count,
        staged_train_count=1 if args.smoke else args.staged_train_count,
        staged_heldout_count=1 if args.smoke else args.staged_heldout_count,
        staged_generation_multiplier=2 if args.smoke else StagedEdgeBridgeFoundationRolloutConfig().staged_generation_multiplier,
        max_staged_source_positions=4 if args.smoke else args.max_staged_source_positions,
        max_staged_first_move_candidates=2 if args.smoke else args.max_staged_first_move_candidates,
        max_staged_black_replies_after_edge=1 if args.smoke else StagedEdgeBridgeFoundationRolloutConfig().max_staged_black_replies_after_edge,
        max_staged_black_replies_after_bridge=1,
        schedule_names=("tg28h_mixed_balanced_baseline", "mixed_balanced_plus_staged") if args.smoke else StagedEdgeBridgeFoundationRolloutConfig().schedule_names,
        full_pool_path=args.full_pool_path,
        progress_output=args.progress_output,
    )
    result = run_staged_edge_bridge_foundation_rollout(config=cfg)
    path = result.write_json(args.output)
    decision = result.to_dict()["decision"]
    print(f"wrote {path}")
    for key in (
        "checkpoint_pass",
        "checkpoint_interpretation",
        "selected_training_schedule",
        "frontier_selected_count",
        "near_miss_false_positive_count",
        "generic_edge_fence_success_rate",
        "staged_heldout_count",
        "staged_selected_first_move_count",
        "staged_s1_bridge_selected_count",
        "staged_any_reply_success_count",
        "foundation_m3_updates_during_training",
        "foundation_m4_promotions_during_training",
        "scheduler_equivalence_mismatch_count",
    ):
        print(key, decision[key])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
