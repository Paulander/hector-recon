#!/usr/bin/env python3
"""Run TG26b KRK edge/fence failure repair checkpoint."""

from __future__ import annotations

import argparse
from pathlib import Path

from recon_lite_chess.autogrowth import EdgeFenceCurriculumConfig, run_edge_fence_curriculum


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seed", type=int, default=20260613)
    parser.add_argument("--foundation-seed", type=int, default=20260612)
    parser.add_argument("--foundation-mate1-train-count", type=int, default=1000)
    parser.add_argument("--foundation-mate1-heldout-count", type=int, default=300)
    parser.add_argument("--foundation-mate1-mirror-count", type=int, default=120)
    parser.add_argument("--foundation-mate2-train-count", type=int, default=300)
    parser.add_argument("--foundation-mate2-heldout-count", type=int, default=100)
    parser.add_argument("--train-chunk-size", type=int, default=160)
    parser.add_argument("--eval-window-size", type=int, default=48)
    parser.add_argument("--max-chunks-per-stage", type=int, default=2)
    parser.add_argument("--consecutive-pass-windows-required", type=int, default=2)
    parser.add_argument("--edge-success-threshold", type=float, default=0.95)
    parser.add_argument("--fence-success-threshold", type=float, default=0.90)
    parser.add_argument("--mate1-regression-threshold", type=float, default=0.99)
    parser.add_argument("--mate2-regression-threshold", type=float, default=0.90)
    parser.add_argument("--eta-m3", type=float, default=0.06)
    parser.add_argument("--max-generation-attempts", type=int, default=250_000)
    parser.add_argument("--max-samples", type=int, default=12)
    parser.add_argument("--top-k-deep-score", type=int, default=6)
    parser.add_argument("--disable-strict-safety-gate", action="store_true")
    parser.add_argument("--disable-edge-handoff-generation", action="store_true")
    parser.add_argument("--fence-handoff-generation", action="store_true")
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("reports/autogrowth/krk_autogrowth_tg26b_edge_fence_failure_repair.json"),
    )
    parser.add_argument("--smoke", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    default_output = Path("reports/autogrowth/krk_autogrowth_tg26b_edge_fence_failure_repair.json")
    output = (
        Path("reports/autogrowth/krk_autogrowth_tg26b_edge_fence_failure_repair_smoke.json")
        if args.smoke and args.output == default_output
        else args.output
    )
    result = run_edge_fence_curriculum(
        config=EdgeFenceCurriculumConfig(
            seed=args.seed,
            foundation_seed=args.foundation_seed,
            foundation_mate1_train_count=40 if args.smoke else args.foundation_mate1_train_count,
            foundation_mate1_heldout_count=12 if args.smoke else args.foundation_mate1_heldout_count,
            foundation_mate1_mirror_count=6 if args.smoke else args.foundation_mate1_mirror_count,
            foundation_mate2_train_count=8 if args.smoke else args.foundation_mate2_train_count,
            foundation_mate2_heldout_count=4 if args.smoke else args.foundation_mate2_heldout_count,
            train_chunk_size=30 if args.smoke else args.train_chunk_size,
            eval_window_size=12 if args.smoke else args.eval_window_size,
            max_chunks_per_stage=1 if args.smoke else args.max_chunks_per_stage,
            consecutive_pass_windows_required=1
            if args.smoke
            else args.consecutive_pass_windows_required,
            edge_success_threshold=min(args.edge_success_threshold, 0.80)
            if args.smoke
            else args.edge_success_threshold,
            fence_success_threshold=min(args.fence_success_threshold, 0.75)
            if args.smoke
            else args.fence_success_threshold,
            mate1_regression_threshold=min(args.mate1_regression_threshold, 0.95)
            if args.smoke
            else args.mate1_regression_threshold,
            mate2_regression_threshold=min(args.mate2_regression_threshold, 0.75)
            if args.smoke
            else args.mate2_regression_threshold,
            eta_m3=args.eta_m3,
            max_generation_attempts=min(args.max_generation_attempts, 120_000)
            if args.smoke
            else args.max_generation_attempts,
            max_samples=args.max_samples,
            top_k_deep_score=max(3, min(args.top_k_deep_score, 4)) if args.smoke else args.top_k_deep_score,
            strict_safety_gate=not args.disable_strict_safety_gate,
            edge_generation_requires_handoff_candidate=not args.disable_edge_handoff_generation,
            fence_generation_requires_handoff_candidate=args.fence_handoff_generation,
        )
    )
    path = result.write_json(output)
    payload = result.to_dict()
    print(f"wrote {path}")
    for stage in payload["stages"]:
        final = stage["final_eval"]
        print(
            f"{stage['label']}: "
            f"conversion={final['conversion_count']}/{final['position_count']} "
            f"handoff={final['earlier_region_handoff_count']}/{final['position_count']} "
            f"rook_loss={final['rook_loss_count']} "
            f"confinement_regression={final['confinement_regression_count']} "
            f"avg_reward={final['avg_reward']:.3f} "
            f"m3={stage['m3_update_count']} "
            f"m4={stage['m4_consolidation_event_count']} "
            f"advanced={stage['advanced']}"
        )
    decision = payload["decision"]
    print(
        "decision: "
        f"status={decision['status']} "
        f"continue={decision['continue_conditions_passed']} "
        f"foundation_regression={decision['foundation_regression_passed']} "
        f"labels_visible={decision['curriculum_labels_learner_visible']} "
        f"direct_provider_override={decision['direct_provider_override']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
