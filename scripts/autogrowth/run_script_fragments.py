#!/usr/bin/env python3
"""Run M16 local SCRIPT fragment/generalization checkpoint."""

from __future__ import annotations

import argparse
from pathlib import Path

from recon_lite_chess.autogrowth import ScriptFragmentConfig, run_script_fragment_experiment


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
    parser.add_argument("--eta-m3", type=float, default=0.08)
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("reports/autogrowth/krk_autogrowth_m16_script_fragments.json"),
    )
    parser.add_argument("--smoke", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    output = (
        Path("reports/autogrowth/krk_autogrowth_m16_script_fragments_smoke.json")
        if args.smoke and args.output == Path("reports/autogrowth/krk_autogrowth_m16_script_fragments.json")
        else args.output
    )
    result = run_script_fragment_experiment(
        config=ScriptFragmentConfig(
            seed=args.seed,
            train_count=20 if args.smoke else args.train_count,
            heldout_weakness_count=5 if args.smoke else args.heldout_weakness_count,
            heldout_broader_count=5 if args.smoke else args.heldout_broader_count,
            min_support=args.min_support,
            max_candidates=min(args.max_candidates, 4) if args.smoke else args.max_candidates,
            horizon=int(args.horizon),
            min_sequence_credit=float(args.min_sequence_credit),
            activation_max_distance=float(args.activation_max_distance),
            eta_m3=float(args.eta_m3),
        )
    )
    path = result.write_json(output)
    payload = result.to_dict()
    heldout = payload["arms"]["fragment_script"]["heldout_all"]
    train = payload["arms"]["fragment_script"]["train_replay"]
    decision = payload["decision"]
    print(f"wrote {path}")
    print(f"dataset_digest={payload['dataset']['digest']}")
    print(
        "script_fragments: "
        f"candidates={payload['generation_summary']['fragment_candidate_count']} "
        f"features={','.join(payload['generation_summary']['fragment_feature_names'])}"
    )
    print(
        "activation: "
        f"train_starts={train['script_start_count']} "
        f"heldout_starts={heldout['script_start_count']} "
        f"heldout_steps={heldout['script_step_count']} "
        f"heldout_complete={heldout['script_complete_count']}"
    )
    print(
        "heldout: "
        f"mates={heldout['mates']}/{heldout['total']} "
        f"rook_loss={heldout['rook_losses']} "
        f"decision={decision['status']} "
        f"partial_curriculum_ready={decision['partial_curriculum_ready']} "
        f"broad_curriculum_ready={decision['broad_curriculum_ready']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
