#!/usr/bin/env python3
"""Mine M4 triplet candidates from KRK autogrowth traces."""

from __future__ import annotations

import argparse
from pathlib import Path

from recon_lite_chess.autogrowth import CandidateMiningConfig, mine_triplet_candidates_from_artifact


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--trace",
        type=Path,
        default=Path("reports/autogrowth/krk_autogrowth_m4_traces.json"),
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("reports/autogrowth/krk_autogrowth_m4_candidates.json"),
    )
    parser.add_argument("--min-support", type=int, default=3)
    parser.add_argument("--max-candidates", type=int, default=12)
    parser.add_argument(
        "--smoke",
        action="store_true",
        help="Use the smoke trace artifact and write a smoke candidate artifact.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    trace = (
        Path("reports/autogrowth/krk_autogrowth_m4_traces_smoke.json")
        if args.smoke and args.trace == Path("reports/autogrowth/krk_autogrowth_m4_traces.json")
        else args.trace
    )
    output = (
        Path("reports/autogrowth/krk_autogrowth_m4_candidates_smoke.json")
        if args.smoke and args.output == Path("reports/autogrowth/krk_autogrowth_m4_candidates.json")
        else args.output
    )
    result = mine_triplet_candidates_from_artifact(
        trace,
        config=CandidateMiningConfig(
            min_support=args.min_support,
            max_candidates=args.max_candidates,
            source_trace_path=str(trace),
        ),
    )
    path = result.write_json(output)
    payload = result.to_dict()
    print(f"wrote {path}")
    print(f"trace_digest={payload['trace_digest']}")
    print(
        "summary: "
        f"candidates={payload['summary']['candidate_count']} "
        f"selected={payload['summary']['selected_candidate_key']} "
        f"ready_for_m5={payload['summary']['ready_for_m5_sandbox']} "
        f"behavior_change_applied={payload['summary']['behavior_change_applied']}"
    )
    if payload["candidates"]:
        top = payload["candidates"][0]
        evidence = top["evidence"]
        print(
            "top: "
            f"key={top['candidate_key']} "
            f"support={evidence['support_count']} "
            f"positions={evidence['position_count']} "
            f"credit={evidence['mean_candidate_credit']:.4f} "
            f"positive={evidence['positive_credit_count']} "
            f"negative={evidence['negative_credit_count']}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
