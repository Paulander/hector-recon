#!/usr/bin/env python3
"""Run TG28k staged near-miss + ablation restoration checkpoint."""

from __future__ import annotations

import argparse
from pathlib import Path

from recon_lite_chess.autogrowth import (
    PersistedStagedPredecessorPoolConfig,
    StagedNearMissAblationRestorationConfig,
    run_staged_near_miss_ablation_restoration,
)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("reports/autogrowth/krk_autogrowth_tg28k_staged_near_miss_ablation_restoration.json"),
    )
    parser.add_argument(
        "--summary-output",
        type=Path,
        default=Path("reports/autogrowth/krk_autogrowth_tg28k_staged_near_miss_ablation_restoration.md"),
    )
    parser.add_argument("--pool-path", type=str, default="reports/autogrowth/pools/tg28j_staged_predecessor_pool.jsonl")
    parser.add_argument("--pool-index-path", type=str, default="reports/autogrowth/pools/tg28j_staged_predecessor_pool_index.json")
    parser.add_argument("--progress-output", type=str, default="reports/autogrowth/krk_autogrowth_tg28k_staged_near_miss_ablation_restoration_progress.json")
    parser.add_argument("--staged-near-miss-count", type=int, default=2)
    parser.add_argument("--near-miss-heldout-count", type=int, default=2)
    parser.add_argument("--max-ablation-positions", type=int, default=1)
    parser.add_argument("--max-staged-source-positions", type=int, default=32)
    parser.add_argument("--max-staged-first-move-candidates", type=int, default=2)
    parser.add_argument("--smoke", action="store_true")
    args = parser.parse_args()

    pool_cfg = PersistedStagedPredecessorPoolConfig(
        foundation_mate1_train_count=4 if args.smoke else 32,
        foundation_mate1_heldout_count=2 if args.smoke else 16,
        foundation_mate2_train_count=1 if args.smoke else 16,
        foundation_mate2_heldout_count=1 if args.smoke else 8,
        bridge_frontier_train_count=1 if args.smoke else 2,
        bridge_frontier_heldout_count=1 if args.smoke else 1,
        generic_edge_train_count=1 if args.smoke else 4,
        generic_edge_heldout_count=1 if args.smoke else 2,
        staged_train_count=0 if args.smoke else 4,
        staged_heldout_count=0 if args.smoke else 2,
        staged_regression_count=0 if args.smoke else 2,
        staged_near_miss_count=0 if args.smoke else args.staged_near_miss_count,
        near_miss_heldout_count=0 if args.smoke else args.near_miss_heldout_count,
        max_staged_source_positions=1 if args.smoke else args.max_staged_source_positions,
        max_staged_first_move_candidates=1 if args.smoke else args.max_staged_first_move_candidates,
        max_cache_candidate_moves=2 if args.smoke else 3,
        max_ablation_positions=0 if args.smoke else args.max_ablation_positions,
        max_foundation_sanity_positions=1,
        max_foundation_ablation_positions=1,
        max_samples=4 if args.smoke else 16,
        schedule_names=("tg28h_mixed_balanced_baseline",) if args.smoke else PersistedStagedPredecessorPoolConfig().schedule_names,
        staged_pool_path=args.pool_path,
        staged_pool_index_path=args.pool_index_path,
        progress_output=args.progress_output,
    )
    result = run_staged_near_miss_ablation_restoration(
        config=StagedNearMissAblationRestorationConfig(pool_config=pool_cfg)
    )
    json_path = result.write_json(args.output)
    md_path = result.write_markdown(args.summary_output)
    decision = result.to_dict()["decision"]
    print(f"wrote {json_path}")
    print(f"wrote {md_path}")
    for key in (
        "checkpoint_pass",
        "checkpoint_interpretation",
        "selected_training_schedule",
        "staged_pool_entry_count",
        "staged_near_miss_count",
        "near_miss_false_positive_count",
        "restored_ablation_count",
        "staged_any_reply_success_count",
        "foundation_m3_updates_during_training",
        "foundation_m4_promotions_during_training",
    ):
        print(key, decision[key])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
