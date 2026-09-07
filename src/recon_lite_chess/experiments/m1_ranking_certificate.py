"""Offline follow-up: exact tie-aware ranking and elementary contradictions.

Unique winning actions are required. Comparison coefficients are discarded;
neither this module nor its reports are inputs to an organism.
"""
import argparse
import json
from pathlib import Path
import time

import numpy as np
from scipy.optimize import linprog

from . import m1_representation as diagnosis


def certificate(rows, matrices, *, deadline):
    requirements = {}
    for row, matrix in zip(rows, matrices):
        winners = [i for i, win in enumerate(row["wins"]) if win]
        if len(winners) != 1:
            raise ValueError("exact certificate requires one winning action per row")
        win = winners[0]
        for loss in range(len(matrix)):
            if loss == win:
                continue
            difference = tuple(a-b for a, b in zip(matrix[win], matrix[loss]))
            # A favorable tie needs >=0; an unfavorable tie needs >0. For this
            # finite homogeneous system all positive margins can be scaled to 1.
            strict = int(f"option:{loss}" > f"option:{win}")
            requirements[difference] = max(strict, requirements.get(difference, 0))
    witnesses = []
    seen = set()
    for delta, margin in requirements.items():
        opposite = tuple(-v for v in delta)
        if opposite in requirements and margin+requirements[opposite] > 0 and delta not in seen:
            witnesses.append({"delta": list(delta), "opposite_delta": list(opposite),
                              "minimum_margins": [margin, requirements[opposite]]})
            seen.update((delta, opposite))
    a = -np.asarray(list(requirements), dtype=float)
    b = -np.asarray(list(requirements.values()), dtype=float)
    result = linprog(np.zeros(a.shape[1]), A_ub=a, b_ub=b, bounds=(None, None), method="highs",
                     options={"time_limit": max(.001, deadline-time.monotonic())})
    diagnosis.expired(deadline)
    if result.status not in (0, 2):
        raise RuntimeError("inconclusive tie-aware feasibility result")
    feasible = result.status == 0
    if feasible:
        if witnesses or not np.all(a@result.x <= b+1e-7):
            raise RuntimeError("invalid feasibility result")
        for row, matrix in zip(rows, matrices):
            scores = np.asarray(matrix, dtype=float)@result.x
            selected = max(range(len(scores)), key=lambda i: (scores[i], f"option:{i}"))
            if not row["wins"][selected]:
                raise RuntimeError("numerical solution did not reproduce winning choices")
    return {"perfect_fixed_weight_policy_exists": feasible, "unique_requirements": len(requirements),
            "opposing_constraint_pairs": len(witnesses),
            "elementary_contradiction": witnesses[0] if witnesses else None,
            "solver_independent_impossibility_witness": bool(witnesses),
            "fitted_weights_discarded": True}


def run(args):
    reference = diagnosis.prior.read(args.reference)
    original = diagnosis.prior.read(args.diagnostic/"summary.json")
    if original["status"] != "complete" or original["manifest"]["source"] != diagnosis.prior.sources():
        raise ValueError("completed source-matched diagnostic required")
    splits = {}
    for name in ("train", "validation"):
        splits[name], sha = diagnosis.load_split(args.pool, name)
        if sha != original["manifest"]["pool_hashes"][name]:
            raise ValueError("pool differs")
    manifest = {"schema": "m1_ranking_certificate.v1", "posthoc": True,
                "source": diagnosis.prior.sources(), "certificate_sha256": diagnosis.prior.sha(__file__),
                "diagnostic_sha256": diagnosis.prior.sha(diagnosis.__file__),
                "original_report_sha256": diagnosis.prior.sha(args.diagnostic/"summary.json"),
                "laboratory_transitions": 7039, "actor_evaluation_moves": 0, "training_moves": 0,
                "wall_seconds": 180, "final_test_opened": False}
    args.output.mkdir(parents=True, exist_ok=False)
    diagnosis.prior.atomic_json(args.output/"manifest.json", manifest)
    deadline = time.monotonic()+180
    counts = {"laboratory_transitions": 0}
    results = []
    try:
        data = {name: diagnosis.laboratory_rows(fens, deadline=deadline, counts=counts) for name, fens in splits.items()}
        for old in original["results"]:
            seed, role, event = old["seed"], old["role"], old["event"]
            actor, checkpoint_hash = diagnosis.restore_actor(reference, args.previous, args.private, seed, role, event)
            before = diagnosis.prior.actor_digest(actor)
            reports = {}
            for name, rows in data.items():
                matrices = [[tuple(diagnosis.gate_value(c, v) for c in actor.conditions.values())
                             for v in row["vectors"]] for row in rows]
                reports[name] = certificate(rows, matrices, deadline=deadline)
            if diagnosis.prior.actor_digest(actor) != before:
                raise RuntimeError("offline feasibility changed actor")
            results.append({"seed": seed, "role": role, "event": event, "checkpoint_sha256": checkpoint_hash,
                            "learned_state_unchanged": True, "reports": reports})
        assert counts["laboratory_transitions"] == manifest["laboratory_transitions"]
        diagnosis.expired(deadline)
        result = {"status": "complete", "manifest": manifest, "actual_counts": counts, "results": results}
        diagnosis.prior.atomic_json(args.output/"summary.json", result)
    except BaseException as error:
        diagnosis.prior.atomic_json(args.output/"failure.json", {"status": "incomplete", "error": str(error), "counts": counts})
        raise
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("pool", "reference", "previous", "private", "diagnostic", "output"):
        parser.add_argument("--"+name, type=Path, required=True)
    print(json.dumps({"status": run(parser.parse_args())["status"]}))
