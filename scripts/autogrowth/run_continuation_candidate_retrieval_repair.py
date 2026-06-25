#!/usr/bin/env python3
"""Run TG29r continuation candidate retrieval repair diagnostics."""

from __future__ import annotations

import argparse
from pathlib import Path

from recon_lite_chess.autogrowth import (
    ContinuationCandidateRetrievalRepairConfig,
    TinyOnlineKRKEpisodeRunnerConfig,
    run_continuation_candidate_retrieval_repair,
)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=Path("reports/autogrowth/krk_autogrowth_tg29r_continuation_candidate_retrieval_repair.json"))
    parser.add_argument("--summary-output", type=Path, default=Path("reports/autogrowth/krk_autogrowth_tg29r_continuation_candidate_retrieval_repair.md"))
    parser.add_argument("--progress-output", type=str, default="reports/autogrowth/krk_autogrowth_tg29r_continuation_candidate_retrieval_repair_progress.json")
    parser.add_argument("--smoke", action="store_true")
    parser.add_argument("--baseline-only", action="store_true")
    args = parser.parse_args()

    base = TinyOnlineKRKEpisodeRunnerConfig(
        episode_count=2 if args.smoke else 4,
        max_white_moves_per_episode=6,
        foundation_mate1_train_count=4 if args.smoke else 8,
        foundation_mate1_heldout_count=2 if args.smoke else 4,
        foundation_mate2_train_count=1 if args.smoke else 4,
        foundation_mate2_heldout_count=1 if args.smoke else 2,
        bridge_frontier_train_count=0,
        bridge_frontier_heldout_count=0,
        generic_edge_train_count=0,
        generic_edge_heldout_count=0,
        staged_train_count=0,
        staged_heldout_count=0,
        staged_regression_count=0,
        staged_near_miss_count=0,
        near_miss_heldout_count=0,
        max_ablation_positions=0,
        max_foundation_sanity_positions=1,
        max_foundation_ablation_positions=1,
        max_samples=4 if args.smoke else 16,
        max_episode_ablation_count=1,
        schedule_names=("tg29l_minimal_real_context",),
        progress_output=args.progress_output,
    )
    cfg = ContinuationCandidateRetrievalRepairConfig(
        base=base,
        current_runtime_cap=12,
        widened_cap=16 if args.smoke else 32,
        max_blocked_turns=0 if args.baseline_only else (1 if args.smoke else 4),
        max_black_replies_per_candidate=1 if args.smoke else 2,
        run_real_context=not args.baseline_only,
        run_compact_regression=False,
    )
    result = run_continuation_candidate_retrieval_repair(config=cfg)
    json_path = result.write_json(args.output)
    md_path = result.write_markdown(args.summary_output)
    print(f"wrote {json_path}")
    print(f"wrote {md_path}")
    for key in (
        "checkpoint_pass",
        "checkpoint_interpretation",
        "repair_applied",
        "selected_repair_arm",
        "blocked_turn_count",
        "legal_candidate_count",
        "safe_candidate_count",
        "continuation_positive_candidate_count",
        "continuation_positive_in_runtime_count",
        "continuation_positive_dropped_count",
        "candidate_cap_blocked_count",
        "retrieval_blocked_count",
        "materialization_blocked_count",
        "retrieval_cache_entry_count",
        "targeted_episode_success_count",
        "targeted_episode_count",
        "foundation_frozen",
        "action_ranker_used_for_runtime",
        "runtime_tablebase_or_dtm_move_source",
        "direct_provider_override",
    ):
        print(key, result.decision[key])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
