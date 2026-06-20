#!/usr/bin/env python3
"""Run TG28c frozen-foundation response cache bridge retrieval."""

from __future__ import annotations

import argparse
from pathlib import Path

from recon_lite_chess.autogrowth import (
    FrozenFoundationResponseCacheBridgeRetrievalConfig,
    run_frozen_foundation_response_cache_bridge_retrieval,
)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("reports/autogrowth/krk_autogrowth_tg28c_frozen_foundation_response_cache_bridge_retrieval.json"),
    )
    parser.add_argument(
        "--progress-output",
        type=str,
        default="reports/autogrowth/krk_autogrowth_tg28c_frozen_foundation_response_cache_bridge_retrieval_progress.json",
    )
    parser.add_argument("--bridge-train-count", type=int, default=4)
    parser.add_argument("--bridge-heldout-count", type=int, default=4)
    parser.add_argument("--generic-edge-safety-heldout-count", type=int, default=2)
    parser.add_argument("--max-cache-candidate-moves", type=int, default=10)
    parser.add_argument("--max-ablation-positions", type=int, default=2)
    parser.add_argument("--smoke", action="store_true")
    args = parser.parse_args()
    output = (
        Path("reports/autogrowth/krk_autogrowth_tg28c_frozen_foundation_response_cache_bridge_retrieval_smoke.json")
        if args.smoke
        and args.output == Path("reports/autogrowth/krk_autogrowth_tg28c_frozen_foundation_response_cache_bridge_retrieval.json")
        else args.output
    )
    cfg = FrozenFoundationResponseCacheBridgeRetrievalConfig(
        foundation_mate1_train_count=4 if args.smoke else 32,
        foundation_mate1_heldout_count=2 if args.smoke else 16,
        foundation_mate2_train_count=1 if args.smoke else 16,
        foundation_mate2_heldout_count=1 if args.smoke else 8,
        bridge_train_count=2 if args.smoke else args.bridge_train_count,
        bridge_heldout_count=2 if args.smoke else args.bridge_heldout_count,
        generic_edge_safety_heldout_count=1 if args.smoke else args.generic_edge_safety_heldout_count,
        basin_random_count=2 if args.smoke else 8,
        max_cache_candidate_moves=3 if args.smoke else args.max_cache_candidate_moves,
        max_ablation_positions=0 if args.smoke else args.max_ablation_positions,
        max_foundation_sanity_positions=1 if args.smoke else 2,
        max_foundation_ablation_positions=1 if args.smoke else 2,
        max_samples=4 if args.smoke else 16,
        replay_count=1 if args.smoke else 2,
        progress_output=args.progress_output,
    )
    result = run_frozen_foundation_response_cache_bridge_retrieval(config=cfg)
    path = result.write_json(output)
    decision = result.to_dict()["decision"]
    print(f"wrote {path}")
    for key in (
        "checkpoint_pass",
        "checkpoint_interpretation",
        "foundation_frozen",
        "foundation_cache_state_count",
        "foundation_cache_live_mismatch_count",
        "foundation_mate1_accuracy",
        "foundation_mate2_conversion_rate",
        "bridge_candidate_generated_count",
        "reply_envelope_foundation_reachable_count",
        "selected_move_count",
        "null_move_count",
        "scheduler_equivalence_mismatch_count",
    ):
        print(key, decision[key])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
