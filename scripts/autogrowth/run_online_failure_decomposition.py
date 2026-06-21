#!/usr/bin/env python3
"""Run TG29b online failure decomposition checkpoint."""

from __future__ import annotations

import argparse
from pathlib import Path

from recon_lite_chess.autogrowth import (
    OnlineFailureDecompositionConfig,
    TinyOnlineKRKEpisodeRunnerConfig,
    run_online_failure_decomposition,
)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("reports/autogrowth/krk_autogrowth_tg29b_online_failure_decomposition.json"),
    )
    parser.add_argument(
        "--summary-output",
        type=Path,
        default=Path("reports/autogrowth/krk_autogrowth_tg29b_online_failure_decomposition.md"),
    )
    parser.add_argument(
        "--progress-output",
        type=str,
        default="reports/autogrowth/krk_autogrowth_tg29b_online_failure_decomposition_progress.json",
    )
    parser.add_argument("--episode-count", type=int, default=4)
    parser.add_argument("--max-white-moves", type=int, default=4)
    parser.add_argument("--max-episode-ablation-count", type=int, default=1)
    parser.add_argument("--max-deep-offline-audit-turns", type=int, default=0)
    parser.add_argument("--staged-pool-path", type=str, default="reports/autogrowth/pools/tg28l_staged_predecessor_pool.jsonl")
    parser.add_argument("--full-pool-path", type=str, default="reports/autogrowth/pools/tg28f_full_foundation_backed_frontier_pool.jsonl")
    parser.add_argument("--smoke", action="store_true")
    args = parser.parse_args()

    base = TinyOnlineKRKEpisodeRunnerConfig(
        episode_count=1 if args.smoke else args.episode_count,
        max_white_moves_per_episode=1 if args.smoke else args.max_white_moves,
        foundation_mate1_train_count=4 if args.smoke else 32,
        foundation_mate1_heldout_count=2 if args.smoke else 16,
        foundation_mate2_train_count=1 if args.smoke else 16,
        foundation_mate2_heldout_count=1 if args.smoke else 8,
        bridge_frontier_train_count=1 if args.smoke else 2,
        bridge_frontier_heldout_count=1,
        generic_edge_train_count=1 if args.smoke else 4,
        generic_edge_heldout_count=1 if args.smoke else 2,
        staged_train_count=0 if args.smoke else 8,
        staged_heldout_count=0 if args.smoke else 4,
        staged_regression_count=0 if args.smoke else 4,
        staged_near_miss_count=0 if args.smoke else 8,
        near_miss_heldout_count=0 if args.smoke else 8,
        max_ablation_positions=0 if args.smoke else 1,
        max_foundation_sanity_positions=1,
        max_foundation_ablation_positions=1,
        max_samples=4 if args.smoke else 16,
        max_episode_ablation_count=0 if args.smoke else args.max_episode_ablation_count,
        schedule_names=("tg28h_mixed_balanced_baseline",) if args.smoke else ("mixed_balanced_plus_staged",),
        staged_pool_path=args.staged_pool_path,
        full_pool_path=args.full_pool_path,
        progress_output=args.progress_output,
    )
    result = run_online_failure_decomposition(
        config=OnlineFailureDecompositionConfig(
            base=base,
            max_deep_offline_audit_turns=0 if args.smoke else args.max_deep_offline_audit_turns,
        )
    )
    json_path = result.write_json(args.output)
    md_path = result.write_markdown(args.summary_output)
    decision = result.decision
    print(f"wrote {json_path}")
    print(f"wrote {md_path}")
    for key in (
        "checkpoint_pass",
        "checkpoint_interpretation",
        "repair_applied",
        "repair_type",
        "episode_count",
        "episode_success_count",
        "foundation_handoff_count",
        "max_move_failure_count",
        "bridge_loop_without_foundation_progress_count",
        "selected_safe_but_low_progress_count",
        "edge_to_bridge_transition_count",
        "bridge_to_foundation_transition_count",
        "deep_offline_audit_turn_count",
        "foundation_cache_live_mismatch_count",
        "scheduler_equivalence_mismatch_count",
    ):
        print(key, decision[key])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
