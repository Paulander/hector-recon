#!/usr/bin/env python3
"""Run TG26t shared atom utility voting checkpoint."""

from __future__ import annotations

import argparse
from pathlib import Path

from recon_lite_chess.autogrowth import (
    SharedAtomUtilityVotingConfig,
    run_shared_atom_utility_voting,
)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=Path("reports/autogrowth/krk_autogrowth_tg26t_shared_atom_utility_voting.json"))
    parser.add_argument("--train-count", type=int, default=12)
    parser.add_argument("--heldout-count", type=int, default=6)
    parser.add_argument("--max-ticks", type=int, default=30)
    parser.add_argument("--max-samples", type=int, default=24)
    parser.add_argument("--max-candidates-per-move", type=int, default=1)
    parser.add_argument("--max-shared-atom-candidates-per-choice", type=int, default=3)
    parser.add_argument("--shared-atom-min-overlap", type=int, default=6)
    parser.add_argument("--min-vote-score", type=float, default=-10000.0)
    parser.add_argument("--soft-quorum-min-positive-atoms", type=int, default=3)
    parser.add_argument("--smoke", action="store_true")
    args = parser.parse_args()

    output = (
        Path("reports/autogrowth/krk_autogrowth_tg26t_shared_atom_utility_voting_smoke.json")
        if args.smoke and args.output == Path("reports/autogrowth/krk_autogrowth_tg26t_shared_atom_utility_voting.json")
        else args.output
    )
    cfg = SharedAtomUtilityVotingConfig(
        train_count=4 if args.smoke else args.train_count,
        heldout_count=2 if args.smoke else args.heldout_count,
        max_ticks=args.max_ticks,
        max_samples=args.max_samples,
        max_candidates_per_move=args.max_candidates_per_move,
        max_shared_atom_candidates_per_choice=2 if args.smoke else args.max_shared_atom_candidates_per_choice,
        shared_atom_min_overlap=args.shared_atom_min_overlap,
        min_vote_score=args.min_vote_score,
        soft_quorum_min_positive_atoms=args.soft_quorum_min_positive_atoms,
        equivalence_count=1 if args.smoke else 4,
    )
    result = run_shared_atom_utility_voting(config=cfg)
    path = result.write_json(output)
    decision = result.to_dict()["decision"]
    print(f"wrote {path}")
    for key in (
        "baseline_prototype_accuracy",
        "shared_hard_overlap_accuracy",
        "shared_weighted_vote_accuracy",
        "shared_action_atom_score_accuracy",
        "shared_contrastive_credit_accuracy",
        "soft_quorum_accuracy",
    ):
        print(key, decision[key])
    print("null_count_per_arm", decision["null_count_per_arm"])
    print("scheduler_equivalence_mismatches", decision["scheduler_equivalence_mismatches"])
    print("checkpoint_pass", decision["checkpoint_pass"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
