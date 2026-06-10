#!/usr/bin/env python3
"""Run KRK Autogrowth v0 M1-M3 baseline/sham evaluation."""

from __future__ import annotations

import argparse
from pathlib import Path

from recon_lite_chess.autogrowth import EvaluationConfig, evaluate_baseline_and_sham


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seed", type=int, default=20260610)
    parser.add_argument("--train-count", type=int, default=200)
    parser.add_argument("--heldout-weakness-count", type=int, default=100)
    parser.add_argument("--heldout-broader-count", type=int, default=100)
    parser.add_argument("--horizons", type=int, nargs="+", default=[40, 80])
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("reports/autogrowth/krk_autogrowth_m1_m3_baseline.json"),
    )
    parser.add_argument(
        "--smoke",
        action="store_true",
        help="Use a tiny deterministic split for quick local validation.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    train_count = 20 if args.smoke else args.train_count
    heldout_weakness_count = 5 if args.smoke else args.heldout_weakness_count
    heldout_broader_count = 5 if args.smoke else args.heldout_broader_count
    output = (
        Path("reports/autogrowth/krk_autogrowth_m1_m3_baseline_smoke.json")
        if args.smoke and args.output == Path("reports/autogrowth/krk_autogrowth_m1_m3_baseline.json")
        else args.output
    )

    config = EvaluationConfig(
        seed=args.seed,
        train_count=train_count,
        heldout_weakness_count=heldout_weakness_count,
        heldout_broader_count=heldout_broader_count,
        horizons=tuple(int(horizon) for horizon in args.horizons),
    )
    result = evaluate_baseline_and_sham(config=config)
    path = result.write_json(output)
    payload = result.to_dict()
    print(f"wrote {path}")
    print(f"dataset_digest={payload['dataset']['digest']}")
    for arm, by_horizon in payload["arms"].items():
        for horizon, metrics in by_horizon.items():
            print(
                f"{arm} h{horizon}: "
                f"mates={metrics['mates']}/{metrics['total']} "
                f"rate={metrics['conversion_rate']:.3f} "
                f"horizon_no_mate={metrics['horizon_no_mate']} "
                f"rook_loss={metrics['rook_losses']} "
                f"draws={metrics['draws']} "
                f"draw_reasons={metrics['draw_reasons']} "
                f"repetitions={metrics['repetition_events']} "
                f"action_vitality={metrics['action_vitality_rate']:.3f} "
                f"illegal={metrics['illegal_moves']} "
                f"stalemate={metrics['stalemates']} "
                f"other={metrics['other_failures']}"
            )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
