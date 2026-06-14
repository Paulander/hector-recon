#!/usr/bin/env python3
"""Run TG26m edge/fence validation with the TG26l context-gated foundation."""

from __future__ import annotations

import argparse
from pathlib import Path

from recon_lite_chess.autogrowth import (
    ContextGatedEdgeFenceValidationConfig,
    run_context_gated_edge_fence_validation,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--smoke", action="store_true")
    parser.add_argument("--seed", type=int, default=20260616)
    parser.add_argument("--train-repetitions", type=int, default=5)
    parser.add_argument("--gate-min-overlap", type=float, default=0.72)
    parser.add_argument("--gate-granularity", choices=("position", "bucket"), default="position")
    parser.add_argument("--train-pool-size", type=int, default=32)
    parser.add_argument("--fence-rehearsal-pool-size", type=int, default=16)
    parser.add_argument("--eval-window-size", type=int, default=16)
    parser.add_argument("--train-chunk-size", type=int, default=64)
    parser.add_argument("--max-chunks-per-stage", type=int, default=2)
    parser.add_argument("--top-k-deep-score", type=int, default=3)
    parser.add_argument("--max-generation-attempts", type=int, default=220_000)
    parser.add_argument("--max-samples", type=int, default=12)
    parser.add_argument("--disable-strict-safety-gate", action="store_true")
    parser.add_argument("--no-symmetries", action="store_true")
    parser.add_argument(
        "--tg26c-main-artifact",
        type=Path,
        default=Path("reports/autogrowth/krk_autogrowth_tg26c_edge_fence_curriculum_handoff.json"),
    )
    parser.add_argument(
        "--tg26i-reference-artifact",
        type=Path,
        default=Path("reports/autogrowth/krk_autogrowth_tg26i_terminal_edge_fence_validation.json"),
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("reports/autogrowth/krk_autogrowth_tg26m_context_gated_edge_fence_validation.json"),
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    default_output = Path("reports/autogrowth/krk_autogrowth_tg26m_context_gated_edge_fence_validation.json")
    output = (
        Path("reports/autogrowth/krk_autogrowth_tg26m_context_gated_edge_fence_validation_smoke.json")
        if args.smoke and args.output == default_output
        else args.output
    )
    result = run_context_gated_edge_fence_validation(
        config=ContextGatedEdgeFenceValidationConfig(
            seed=args.seed,
            include_symmetries=not args.no_symmetries,
            foundation_train_repetitions=1 if args.smoke else args.train_repetitions,
            gate_min_overlap=args.gate_min_overlap,
            gate_granularity=args.gate_granularity,
            train_pool_size=8 if args.smoke else args.train_pool_size,
            fence_rehearsal_pool_size=4 if args.smoke else args.fence_rehearsal_pool_size,
            eval_window_size=4 if args.smoke else args.eval_window_size,
            train_chunk_size=16 if args.smoke else args.train_chunk_size,
            max_chunks_per_stage=1 if args.smoke else args.max_chunks_per_stage,
            mate1_regression_threshold=0.80 if args.smoke else 0.98,
            mate2_regression_threshold=0.80 if args.smoke else 0.95,
            max_generation_attempts=80_000 if args.smoke else args.max_generation_attempts,
            max_samples=3 if args.smoke else args.max_samples,
            top_k_deep_score=max(3, min(args.top_k_deep_score, 4)) if args.smoke else args.top_k_deep_score,
            strict_safety_gate=not args.disable_strict_safety_gate,
            tg26c_main_artifact_path=str(args.tg26c_main_artifact),
            tg26i_reference_artifact_path=str(args.tg26i_reference_artifact),
        )
    )
    path = result.write_json(output)
    payload = result.to_dict()
    print(f"wrote {path}")
    print(
        "foundation: "
        f"mate1={payload['foundation']['mate1_self_accuracy']:.3f} "
        f"mate2={payload['foundation']['mate2_conversion_rate']:.3f} "
        f"no_gate={payload['foundation']['mate2_no_confirmed_gate_count']} "
        f"regression={payload['decision']['foundation_regression_passed']}"
    )
    for stage in payload["stages"]:
        slices = stage["eval_slices"]
        print(
            f"{stage['label']}: "
            f"filtered={slices['filtered_train_like']['conversion_count']}/{slices['filtered_train_like']['position_count']} "
            f"unfiltered={slices['unfiltered_curriculum']['conversion_count']}/{slices['unfiltered_curriculum']['position_count']} "
            f"boundary={slices['boundary_near_miss']['conversion_count']}/{slices['boundary_near_miss']['position_count']} "
            f"m3={stage['m3_update_count']} "
            f"m4={stage['m4_consolidation_event_count']}"
        )
    decision = payload["decision"]
    print(
        "decision: "
        f"status={decision['status']} "
        f"safety={decision['safety_passed']} "
        f"fence_boundary={decision['fence_boundary_nonzero']} "
        f"broad_krk={decision['broad_random_krk_enabled']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
