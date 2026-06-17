#!/usr/bin/env python3
"""Run TG26s shared feature atom substrate checkpoint."""

from __future__ import annotations

import argparse
from pathlib import Path

from recon_lite_chess.autogrowth import (
    SharedFeatureAtomConfig,
    run_shared_feature_atom_experiment,
)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=Path("reports/autogrowth/krk_autogrowth_tg26s_shared_feature_atoms.json"))
    parser.add_argument("--train-count", type=int, default=40)
    parser.add_argument("--heldout-count", type=int, default=20)
    parser.add_argument("--train-repetitions", type=int, default=1)
    parser.add_argument("--max-ticks", type=int, default=30)
    parser.add_argument("--max-samples", type=int, default=16)
    parser.add_argument("--shared-atom-min-overlap", type=int, default=6)
    parser.add_argument("--max-candidates-per-move", type=int, default=1)
    parser.add_argument("--max-shared-atom-candidates-per-choice", type=int, default=6)
    parser.add_argument("--smoke", action="store_true")
    args = parser.parse_args()

    output = (
        Path("reports/autogrowth/krk_autogrowth_tg26s_shared_feature_atoms_smoke.json")
        if args.smoke and args.output == Path("reports/autogrowth/krk_autogrowth_tg26s_shared_feature_atoms.json")
        else args.output
    )
    config = SharedFeatureAtomConfig(
        train_count=4 if args.smoke else args.train_count,
        heldout_count=2 if args.smoke else args.heldout_count,
        train_repetitions=args.train_repetitions,
        max_ticks=args.max_ticks,
        max_samples=args.max_samples,
        shared_atom_min_overlap=args.shared_atom_min_overlap,
        max_candidates_per_move=args.max_candidates_per_move,
        max_shared_atom_candidates_per_choice=3 if args.smoke else args.max_shared_atom_candidates_per_choice,
        equivalence_count=2 if args.smoke else 6,
    )
    result = run_shared_feature_atom_experiment(config=config)
    path = result.write_json(output)
    payload = result.to_dict()
    decision = payload["decision"]
    print(f"wrote {path}")
    print("baseline_prototype_accuracy", decision["baseline_prototype_accuracy"])
    print("shared_atom_accuracy", decision["shared_atom_accuracy"])
    print("shared_projection_accuracy", decision["shared_projection_accuracy"])
    print("post_prune_accuracy", decision["post_prune_accuracy"])
    print("null_selection_count_by_arm", decision["null_selection_count_by_arm"])
    print("shared_atom_count", decision["shared_atom_count"])
    print("reused_atom_count", decision["reused_atom_count"])
    print("scheduler_mismatches", decision["scheduler_equivalence_mismatch_count"])
    print("checkpoint_pass", decision["checkpoint_pass"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
