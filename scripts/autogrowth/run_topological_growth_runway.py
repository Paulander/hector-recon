#!/usr/bin/env python3
"""Run TG17 topological-growth runway inventory and triplet-chain assay."""

from __future__ import annotations

import argparse
from pathlib import Path

from recon_lite_chess.autogrowth import TopologicalGrowthRunwayConfig, run_topological_growth_runway


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seed", type=int, default=20260610)
    parser.add_argument("--train-count", type=int, default=200)
    parser.add_argument("--heldout-weakness-count", type=int, default=100)
    parser.add_argument("--heldout-broader-count", type=int, default=100)
    parser.add_argument("--min-support", type=int, default=1)
    parser.add_argument("--max-candidates", type=int, default=12)
    parser.add_argument("--horizon", type=int, default=40)
    parser.add_argument("--min-sequence-credit", type=float, default=0.10)
    parser.add_argument("--activation-max-distance", type=float, default=0.5)
    parser.add_argument("--chain-max-distance", type=float, default=1.5)
    parser.add_argument("--max-chain-edges", type=int, default=24)
    parser.add_argument("--eta-m3", type=float, default=0.08)
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("reports/autogrowth/krk_autogrowth_tg17_triplet_chain_runway.json"),
    )
    parser.add_argument("--smoke", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    output = (
        Path("reports/autogrowth/krk_autogrowth_tg17_triplet_chain_runway_smoke.json")
        if args.smoke and args.output == Path("reports/autogrowth/krk_autogrowth_tg17_triplet_chain_runway.json")
        else args.output
    )
    result = run_topological_growth_runway(
        config=TopologicalGrowthRunwayConfig(
            seed=args.seed,
            train_count=20 if args.smoke else args.train_count,
            heldout_weakness_count=5 if args.smoke else args.heldout_weakness_count,
            heldout_broader_count=5 if args.smoke else args.heldout_broader_count,
            min_support=args.min_support,
            max_candidates=min(args.max_candidates, 4) if args.smoke else args.max_candidates,
            horizon=int(args.horizon),
            min_sequence_credit=float(args.min_sequence_credit),
            activation_max_distance=float(args.activation_max_distance),
            chain_max_distance=float(args.chain_max_distance),
            max_chain_edges=int(args.max_chain_edges),
            eta_m3=float(args.eta_m3),
        )
    )
    path = result.write_json(output)
    payload = result.to_dict()
    decision = payload["curriculum_decision"]
    chain = payload["triplet_chain_view"]
    fragment = payload["current_fragment_result"]["decision"]
    heldout = payload["current_fragment_result"]["arms"]["fragment_script"]["heldout_all"]
    print(f"wrote {path}")
    print(f"dataset_digest={payload['dataset']['digest']}")
    print(
        "legacy_inventory: "
        f"ready_controls={decision['legacy_ready_control_runs']} "
        f"entries={len(payload['legacy_predefined_topology_inventory'])}"
    )
    print(
        "triplet_chains: "
        f"triplets={len(chain['triplets'])} "
        f"edges={chain['chain_edge_count']} "
        f"chainable={chain['chainable']}"
    )
    print(
        "fragment_curriculum: "
        f"partial={fragment['partial_curriculum_ready']} "
        f"broad={fragment['broad_curriculum_ready']} "
        f"heldout_starts={heldout['script_start_count']} "
        f"heldout_mates={heldout['mates']}/{heldout['total']} "
        f"rook_loss={heldout['rook_losses']}"
    )
    print(
        "decision: "
        f"status={decision['status']} "
        f"bounded_partial_curriculum_allowed={decision['bounded_partial_curriculum_allowed']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
