#!/usr/bin/env python3
"""Run M5 sandbox evaluation for one mined KRK autogrowth candidate."""

from __future__ import annotations

import argparse
from pathlib import Path

from recon_lite_chess.autogrowth import SandboxConfig, evaluate_candidate_sandbox


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
        default=Path("reports/autogrowth/krk_autogrowth_m5_sandbox.json"),
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
        Path("reports/autogrowth/krk_autogrowth_m5_sandbox_smoke.json")
        if args.smoke and args.output == Path("reports/autogrowth/krk_autogrowth_m5_sandbox.json")
        else args.output
    )
    result = evaluate_candidate_sandbox(
        config=SandboxConfig(
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
    print(f"wrote {path}")
    print(f"dataset_digest={payload['dataset']['digest']}")
    print(f"candidate={payload['candidate']['candidate_key']}")
    for horizon, metrics in payload["arms"]["autogrowth_sandbox"].items():
        safety = payload["safety"][horizon]
        paired = payload["paired_deltas"][horizon]
        learning = payload["learning_decisions"][horizon]
        print(
            f"sandbox h{horizon}: "
            f"mates={metrics['mates']}/{metrics['total']} "
            f"rate={metrics['conversion_rate']:.3f} "
            f"activations={metrics['candidate_activated_position_count']} "
            f"changed_positions={metrics['candidate_behavior_changed_position_count']} "
            f"candidate_moves={metrics['candidate_move_count']} "
            f"illegal={metrics['illegal_moves']} "
            f"stalemate={metrics['stalemates']} "
            f"rook_loss={metrics['rook_losses']} "
            f"baseline_regressions={safety['protected_baseline_regression_count']} "
            f"blunder_regressions={safety['blunder_regression_count']} "
            f"delta_success={paired['candidate_succeeds_where_baseline_fails']} "
            f"m3_updates={learning['m3_update_count']} "
            f"decision={learning['decision']}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
