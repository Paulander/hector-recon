#!/usr/bin/env python3
"""Run the full KRK Autogrowth v0 three-arm experiment."""

from __future__ import annotations

import argparse
from pathlib import Path

from recon_lite_chess.autogrowth import AutogrowthExperimentConfig, run_autogrowth_experiment


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seed", type=int, default=20260610)
    parser.add_argument("--train-count", type=int, default=200)
    parser.add_argument("--heldout-weakness-count", type=int, default=100)
    parser.add_argument("--heldout-broader-count", type=int, default=100)
    parser.add_argument("--horizons", type=int, nargs="+", default=[40, 80])
    parser.add_argument("--activation-max-distance", type=float, default=1.5)
    parser.add_argument(
        "--candidate",
        type=Path,
        default=Path("reports/autogrowth/krk_autogrowth_m4_candidates.json"),
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("reports/autogrowth/krk_autogrowth_v0_experiment.json"),
    )
    parser.add_argument(
        "--smoke",
        action="store_true",
        help="Use smoke candidate artifact and tiny deterministic heldout split.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    candidate = (
        Path("reports/autogrowth/krk_autogrowth_m4_candidates_smoke.json")
        if args.smoke and args.candidate == Path("reports/autogrowth/krk_autogrowth_m4_candidates.json")
        else args.candidate
    )
    output = (
        Path("reports/autogrowth/krk_autogrowth_v0_experiment_smoke.json")
        if args.smoke and args.output == Path("reports/autogrowth/krk_autogrowth_v0_experiment.json")
        else args.output
    )
    result = run_autogrowth_experiment(
        config=AutogrowthExperimentConfig(
            seed=args.seed,
            train_count=20 if args.smoke else args.train_count,
            heldout_weakness_count=5 if args.smoke else args.heldout_weakness_count,
            heldout_broader_count=5 if args.smoke else args.heldout_broader_count,
            horizons=tuple(int(horizon) for horizon in args.horizons),
            candidate_path=str(candidate),
            activation_max_distance=float(args.activation_max_distance),
        )
    )
    path = result.write_json(output)
    payload = result.to_dict()
    threshold = payload["threshold_evaluation"]
    print(f"wrote {path}")
    print(f"dataset_digest={payload['dataset']['digest']}")
    print(f"candidate={payload['candidate']['candidate_key']}")
    print(
        "decision: "
        f"status={payload['decision']['status']} "
        f"passed={threshold['passed']} "
        f"failed_checks={threshold['failed_checks']} "
        f"m3_updates={payload['decision']['m3_update_count']} "
        f"m4_events={payload['decision']['m4_event_count']}"
    )
    for horizon, metrics in payload["arms"]["autogrowth_sandbox"].items():
        baseline = payload["arms"]["baseline"][horizon]
        safety = payload["safety"][horizon]
        print(
            f"h{horizon}: "
            f"baseline_mates={baseline['mates']}/{baseline['total']} "
            f"candidate_mates={metrics['mates']}/{metrics['total']} "
            f"activations={metrics['candidate_activated_position_count']} "
            f"changed={metrics['candidate_behavior_changed_position_count']} "
            f"blunder_regressions={safety['blunder_regression_count']}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
