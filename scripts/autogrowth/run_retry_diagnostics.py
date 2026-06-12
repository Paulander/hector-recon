#!/usr/bin/env python3
"""Run TG22 retry-event diagnostics."""

from __future__ import annotations

import argparse
from pathlib import Path

from recon_lite_chess.autogrowth import RetryDiagnosticsConfig, run_retry_diagnostics


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
    parser.add_argument("--retry-edge-min-support", type=int, default=1)
    parser.add_argument("--retry-edge-bonus", type=float, default=1.25)
    parser.add_argument("--max-event-records", type=int, default=200)
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("reports/autogrowth/krk_autogrowth_tg22_retry_diagnostics.json"),
    )
    parser.add_argument("--smoke", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    default_output = Path("reports/autogrowth/krk_autogrowth_tg22_retry_diagnostics.json")
    output = (
        Path("reports/autogrowth/krk_autogrowth_tg22_retry_diagnostics_smoke.json")
        if args.smoke and args.output == default_output
        else args.output
    )
    result = run_retry_diagnostics(
        config=RetryDiagnosticsConfig(
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
            retry_edge_min_support=int(args.retry_edge_min_support),
            retry_edge_bonus=float(args.retry_edge_bonus),
            max_event_records=int(args.max_event_records),
        )
    )
    path = result.write_json(output)
    payload = result.to_dict()
    decision = payload["decision"]
    summary = payload["trace_summary"]
    print(f"wrote {path}")
    print(f"dataset_digest={payload['dataset']['digest']}")
    print(
        "retry_diagnostics: "
        f"candidates={len(payload['candidates'])} "
        f"edges={payload['triplet_chain_view']['chain_edge_count']} "
        f"learned_retry_edges={payload['retry_edges']['learned_edge_count']} "
        f"event_count={summary['event_count']} "
        f"comparisons={summary['comparison_count']}"
    )
    print(
        "diagnosis: "
        f"finding={decision['finding']} "
        f"edge_changed_choice={summary['edge_changed_choice_count']} "
        f"edge_bonus_hits={summary['edge_bonus_hit_comparison_count']} "
        f"no_local_sibling={summary['no_local_sibling_count']} "
        f"completion_events={summary['retry_event_led_to_completion_count']}"
    )
    print(f"next: {decision['next_recommended_checkpoint']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
