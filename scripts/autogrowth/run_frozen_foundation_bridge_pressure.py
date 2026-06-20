#!/usr/bin/env python3
"""Run TG28b frozen-foundation bridge-pressure checkpoint."""

from __future__ import annotations

import argparse
from pathlib import Path

from recon_lite_chess.autogrowth import (
    FrozenFoundationBridgePressureConfig,
    run_frozen_foundation_bridge_pressure,
)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("reports/autogrowth/krk_autogrowth_tg28b_frozen_foundation_bridge_pressure.json"),
    )
    parser.add_argument(
        "--progress-output",
        type=str,
        default="reports/autogrowth/krk_autogrowth_tg28b_frozen_foundation_bridge_pressure_progress.json",
    )
    parser.add_argument("--bridge-train-count", type=int, default=12)
    parser.add_argument("--bridge-heldout-count", type=int, default=8)
    parser.add_argument("--generic-edge-safety-heldout-count", type=int, default=8)
    parser.add_argument("--top-k-deep-foundation-checks", type=int, default=6)
    parser.add_argument("--max-edge-candidates-per-position", type=int, default=8)
    parser.add_argument("--max-ablation-positions", type=int, default=4)
    parser.add_argument("--max-foundation-ablation-positions", type=int, default=2)
    parser.add_argument("--max-foundation-sanity-positions", type=int, default=2)
    parser.add_argument("--replay-count", type=int, default=2)
    parser.add_argument("--smoke", action="store_true")
    args = parser.parse_args()

    output = (
        Path("reports/autogrowth/krk_autogrowth_tg28b_frozen_foundation_bridge_pressure_smoke.json")
        if args.smoke and args.output == Path("reports/autogrowth/krk_autogrowth_tg28b_frozen_foundation_bridge_pressure.json")
        else args.output
    )
    cfg = FrozenFoundationBridgePressureConfig(
        foundation_mate1_train_count=4 if args.smoke else 32,
        foundation_mate1_heldout_count=2 if args.smoke else 16,
        foundation_mate2_train_count=1 if args.smoke else 16,
        foundation_mate2_heldout_count=1 if args.smoke else 8,
        bridge_train_count=2 if args.smoke else args.bridge_train_count,
        bridge_heldout_count=2 if args.smoke else args.bridge_heldout_count,
        generic_edge_safety_heldout_count=1 if args.smoke else args.generic_edge_safety_heldout_count,
        top_k_deep_foundation_checks=1 if args.smoke else args.top_k_deep_foundation_checks,
        max_edge_candidates_per_position=3 if args.smoke else args.max_edge_candidates_per_position,
        max_ablation_positions=0 if args.smoke else args.max_ablation_positions,
        max_foundation_sanity_positions=1 if args.smoke else args.max_foundation_sanity_positions,
        max_foundation_ablation_positions=1 if args.smoke else args.max_foundation_ablation_positions,
        max_bounded_replies_per_candidate=1 if args.smoke else 4,
        max_bounded_second_moves_per_reply=1 if args.smoke else 2,
        max_samples=4 if args.smoke else 16,
        replay_count=1 if args.smoke else args.replay_count,
        progress_output=args.progress_output,
    )
    result = run_frozen_foundation_bridge_pressure(config=cfg)
    path = result.write_json(output)
    decision = result.to_dict()["decision"]
    print(f"wrote {path}")
    for key in (
        "checkpoint_pass",
        "foundation_frozen",
        "foundation_mate1_accuracy",
        "foundation_mate2_conversion_rate",
        "foundation_m3_updates_during_bridge_training",
        "foundation_m3_updates_during_eval",
        "edge_fence_success_rate",
        "confinement_area_improvement_rate",
        "rook_blunder_count",
        "reply_envelope_foundation_reachable_count",
        "reply_envelope_foundation_coverage_rate",
        "bounded_bridge_foundation_reachable_count",
        "foundation_handoff_conversion_count",
        "selected_move_count",
        "null_move_count",
        "scheduler_equivalence_mismatch_count",
    ):
        print(key, decision[key])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
