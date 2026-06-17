#!/usr/bin/env python3
"""Run TG26r native foundation generalization repair checkpoint."""

from __future__ import annotations

import argparse
from pathlib import Path

from recon_lite_chess.autogrowth import (
    NativeFoundationGeneralizationConfig,
    run_native_foundation_generalization,
)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=Path("reports/autogrowth/krk_autogrowth_tg26r_native_foundation_generalization.json"))
    parser.add_argument("--mate1-train-count", type=int, default=120)
    parser.add_argument("--mate1-heldout-count", type=int, default=40)
    parser.add_argument("--mate2-train-count", type=int, default=60)
    parser.add_argument("--mate2-heldout-count", type=int, default=20)
    parser.add_argument("--train-repetitions", type=int, default=2)
    parser.add_argument("--continuation-repetitions", type=int, default=1)
    parser.add_argument("--max-ticks", type=int, default=80)
    parser.add_argument("--max-samples", type=int, default=16)
    parser.add_argument("--prototype-distance-threshold", type=int, default=12)
    parser.add_argument("--max-prototype-candidates-per-move", type=int, default=3)
    parser.add_argument("--max-prototype-scan-triplets", type=int, default=256)
    parser.add_argument("--smoke", action="store_true")
    args = parser.parse_args()

    output = (
        Path("reports/autogrowth/krk_autogrowth_tg26r_native_foundation_generalization_smoke.json")
        if args.smoke and args.output == Path("reports/autogrowth/krk_autogrowth_tg26r_native_foundation_generalization.json")
        else args.output
    )
    config = NativeFoundationGeneralizationConfig(
        mate1_train_count=12 if args.smoke else args.mate1_train_count,
        mate1_heldout_count=6 if args.smoke else args.mate1_heldout_count,
        mate2_train_count=6 if args.smoke else args.mate2_train_count,
        mate2_heldout_count=3 if args.smoke else args.mate2_heldout_count,
        train_repetitions=1 if args.smoke else args.train_repetitions,
        continuation_repetitions=1 if args.smoke else args.continuation_repetitions,
        max_ticks=args.max_ticks,
        max_samples=args.max_samples,
        prototype_distance_threshold=args.prototype_distance_threshold,
        max_prototype_candidates_per_move=args.max_prototype_candidates_per_move,
        max_prototype_scan_triplets=args.max_prototype_scan_triplets,
        equivalence_mate1_count=1 if args.smoke else 3,
        equivalence_mate2_count=0 if args.smoke else 2,
    )
    result = run_native_foundation_generalization(config=config)
    path = result.write_json(output)
    payload = result.to_dict()
    print(f"wrote {path}")
    for arm_name in ("exact_arm", "prototype_arm", "canonical_arm"):
        arm = payload[arm_name]
        print(
            arm_name,
            "mate1",
            arm["mate1"]["heldout"]["correct_count"],
            "/",
            arm["mate1"]["heldout"]["position_count"],
            "mate2",
            arm["mate2"]["heldout"]["conversion_count"],
            "/",
            arm["mate2"]["heldout"]["position_count"],
            "nulls",
            arm["null_selection_count"],
        )
    print("scheduler_mismatches", payload["scheduler_equivalence"]["mismatch_count"])
    print("checkpoint_pass", payload["decision"]["checkpoint_pass"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
