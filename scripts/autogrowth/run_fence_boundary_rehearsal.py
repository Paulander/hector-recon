#!/usr/bin/env python3
"""Run TG26f fence boundary rehearsal checkpoint."""

from __future__ import annotations

import argparse
from pathlib import Path

from recon_lite_chess.autogrowth import FenceBoundaryRehearsalConfig, run_fence_boundary_rehearsal


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--smoke", action="store_true")
    parser.add_argument("--seed", type=int, default=20260616)
    parser.add_argument("--foundation-seed", type=int, default=20260612)
    parser.add_argument("--foundation-mate1-train-count", type=int, default=300)
    parser.add_argument("--foundation-mate1-heldout-count", type=int, default=100)
    parser.add_argument("--foundation-mate1-mirror-count", type=int, default=40)
    parser.add_argument("--foundation-mate2-train-count", type=int, default=100)
    parser.add_argument("--foundation-mate2-heldout-count", type=int, default=32)
    parser.add_argument("--train-pool-size", type=int, default=64)
    parser.add_argument("--fence-rehearsal-pool-size", type=int, default=32)
    parser.add_argument("--eval-window-size", type=int, default=32)
    parser.add_argument("--train-chunk-size", type=int, default=128)
    parser.add_argument("--max-chunks-per-stage", type=int, default=2)
    parser.add_argument("--top-k-deep-score", type=int, default=6)
    parser.add_argument("--max-generation-attempts", type=int, default=300_000)
    parser.add_argument("--max-samples", type=int, default=12)
    parser.add_argument("--disable-strict-safety-gate", action="store_true")
    parser.add_argument(
        "--tg26c-main-artifact",
        type=Path,
        default=Path("reports/autogrowth/krk_autogrowth_tg26c_edge_fence_curriculum_handoff.json"),
    )
    parser.add_argument(
        "--tg26e-reference-artifact",
        type=Path,
        default=Path("reports/autogrowth/krk_autogrowth_tg26e_persisted_pool_validation.json"),
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("reports/autogrowth/krk_autogrowth_tg26f_fence_boundary_rehearsal.json"),
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    output = args.output
    if args.smoke and output == Path("reports/autogrowth/krk_autogrowth_tg26f_fence_boundary_rehearsal.json"):
        output = Path("reports/autogrowth/krk_autogrowth_tg26f_fence_boundary_rehearsal_smoke.json")
    result = run_fence_boundary_rehearsal(
        config=FenceBoundaryRehearsalConfig(
            seed=args.seed,
            foundation_seed=args.foundation_seed,
            foundation_mate1_train_count=24 if args.smoke else args.foundation_mate1_train_count,
            foundation_mate1_heldout_count=8 if args.smoke else args.foundation_mate1_heldout_count,
            foundation_mate1_mirror_count=4 if args.smoke else args.foundation_mate1_mirror_count,
            foundation_mate2_train_count=4 if args.smoke else args.foundation_mate2_train_count,
            foundation_mate2_heldout_count=2 if args.smoke else args.foundation_mate2_heldout_count,
            train_pool_size=8 if args.smoke else args.train_pool_size,
            fence_rehearsal_pool_size=4 if args.smoke else args.fence_rehearsal_pool_size,
            eval_window_size=4 if args.smoke else args.eval_window_size,
            train_chunk_size=16 if args.smoke else args.train_chunk_size,
            max_chunks_per_stage=1 if args.smoke else args.max_chunks_per_stage,
            top_k_deep_score=max(3, min(args.top_k_deep_score, 4)) if args.smoke else args.top_k_deep_score,
            max_generation_attempts=80_000 if args.smoke else args.max_generation_attempts,
            max_samples=3 if args.smoke else args.max_samples,
            strict_safety_gate=not args.disable_strict_safety_gate,
            tg26c_main_artifact_path=str(args.tg26c_main_artifact),
            tg26e_reference_artifact_path=str(args.tg26e_reference_artifact),
        )
    )
    path = result.write_json(output)
    payload = result.to_dict()
    print(f"wrote {path}")
    for stage in payload["stages"]:
        print(stage["label"])
        for name, metrics in stage["eval_slices"].items():
            print(
                f"  {name}: conversion={metrics['conversion_count']}/{metrics['position_count']} "
                f"handoff={metrics['earlier_region_handoff_count']}/{metrics['position_count']} "
                f"rook_loss={metrics['rook_loss_count']} confinement={metrics['confinement_regression_count']}"
            )
    decision = payload["decision"]
    print(
        "decision: "
        f"foundation={decision['foundation_regression_passed']} "
        f"safety={decision['safety_passed']} "
        f"edge_stable={decision['edge_stability_preserved']} "
        f"fence_unfiltered={decision['fence_unfiltered_nonzero']} "
        f"fence_boundary={decision['fence_boundary_nonzero']} "
        f"m4={decision['m4_consolidation_event_count']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
