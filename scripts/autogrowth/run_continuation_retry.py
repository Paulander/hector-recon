#!/usr/bin/env python3
"""Run TG20 local continuation retry checkpoint."""

from __future__ import annotations

import argparse
from pathlib import Path

from recon_lite_chess.autogrowth import ContinuationRetryConfig, run_continuation_retry_experiment


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seed", type=int, default=20260610)
    parser.add_argument("--train-count", type=int, default=200)
    parser.add_argument("--heldout-weakness-count", type=int, default=100)
    parser.add_argument("--heldout-broader-count", type=int, default=100)
    parser.add_argument("--min-support", type=int, default=1)
    parser.add_argument("--max-candidates", type=int, default=12)
    parser.add_argument("--horizons", type=int, nargs="+", default=[40, 80])
    parser.add_argument("--min-sequence-credit", type=float, default=0.10)
    parser.add_argument("--activation-max-distance", type=float, default=0.5)
    parser.add_argument("--after-max-distance", type=float, default=1.5)
    parser.add_argument("--chain-max-distance", type=float, default=1.5)
    parser.add_argument("--max-chain-edges", type=int, default=64)
    parser.add_argument("--chain-request-bonus", type=float, default=0.75)
    parser.add_argument("--eta-m3", type=float, default=0.08)
    parser.add_argument("--lag-negative-threshold", type=int, default=1)
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("reports/autogrowth/krk_autogrowth_tg20_continuation_retry.json"),
    )
    parser.add_argument("--smoke", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    default_output = Path("reports/autogrowth/krk_autogrowth_tg20_continuation_retry.json")
    output = (
        Path("reports/autogrowth/krk_autogrowth_tg20_continuation_retry_smoke.json")
        if args.smoke and args.output == default_output
        else args.output
    )
    result = run_continuation_retry_experiment(
        config=ContinuationRetryConfig(
            seed=args.seed,
            train_count=20 if args.smoke else args.train_count,
            heldout_weakness_count=5 if args.smoke else args.heldout_weakness_count,
            heldout_broader_count=5 if args.smoke else args.heldout_broader_count,
            min_support=args.min_support,
            max_candidates=min(args.max_candidates, 4) if args.smoke else args.max_candidates,
            horizons=tuple(int(item) for item in ([min(args.horizons)] if args.smoke else args.horizons)),
            min_sequence_credit=float(args.min_sequence_credit),
            activation_max_distance=float(args.activation_max_distance),
            after_max_distance=float(args.after_max_distance),
            chain_max_distance=float(args.chain_max_distance),
            max_chain_edges=int(args.max_chain_edges),
            chain_request_bonus=float(args.chain_request_bonus),
            eta_m3=float(args.eta_m3),
            lag_negative_threshold=int(args.lag_negative_threshold),
        )
    )
    path = result.write_json(output)
    payload = result.to_dict()
    primary = str(payload["decision"]["primary_horizon"])
    retry = payload["arms"]["real_fragment_chain_lag_retry"][primary]
    lag = payload["arms"]["real_fragment_chain_lag_only"][primary]
    baseline = payload["arms"]["baseline"][primary]
    decision = payload["decision"]
    print(f"wrote {path}")
    print(f"dataset_digest={payload['dataset']['digest']}")
    print(
        "continuation_retry: "
        f"candidates={len(payload['candidates'])} "
        f"edges={payload['triplet_chain_view']['chain_edge_count']} "
        f"training_retries={payload['arms']['training_continuation_retry']['retry_success_count']} "
        f"training_m3={payload['arms']['training_continuation_retry']['m3_update_count']}"
    )
    print(
        f"h{primary}: "
        f"baseline_mates={baseline['mates']}/{baseline['total']} "
        f"lag_mates={lag['mates']}/{lag['total']} "
        f"retry_mates={retry['mates']}/{retry['total']} "
        f"retry_success={retry['retry_success_count']} "
        f"completion_delta_vs_lag={decision['completion_delta_vs_lag_only']} "
        f"rook_losses={retry['rook_losses']} "
        f"repetition_delta={decision['repetition_event_delta_vs_baseline']}"
    )
    print(
        "decision: "
        f"status={decision['status']} "
        f"partial_continue={decision['partial_continue']} "
        f"full_pass={decision['full_pass']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
