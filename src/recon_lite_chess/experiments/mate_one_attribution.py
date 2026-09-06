"""Offline attribution of representation/timing using the ordinary opaque coach.

Plans and schedule are frozen before play. The training loop does not inspect
organisms; structure inspection happens only after training. No final-test API.
"""
import argparse
from collections import Counter, defaultdict
from concurrent.futures import ProcessPoolExecutor
from dataclasses import asdict
import hashlib
import json
import multiprocessing
from pathlib import Path
import random
import statistics
import time

import chess

from recon_lite_hector.benchmarks.terminal_attribution import (
    ARMS, AttributionDevelopment, Proposal, make_plans,
)
from recon_lite_chess.coach.exercise import play_mate_one
from recon_lite_chess.coach.pools import load_split, orbit_key
from recon_lite_chess.coach.runner import source_identity
from recon_lite_chess.coach.terminal import SCHEMA


class AttributionOrganism(AttributionDevelopment):
    embodiment = "typed_feature_terminals_v1"


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True).encode()).hexdigest()


def schedule_indices(size, episodes, seed):
    if size < 1 or episodes < 1:
        raise ValueError("schedule needs a nonempty pool and positive episodes")
    rng = random.Random(f"schedule:{seed}")
    order = []
    while len(order) < episodes:
        batch = list(range(size))
        rng.shuffle(batch)
        order.extend(batch)
    return tuple(order[:episodes])


def train_arm(organism, fens, order, *, deadline):
    """Coach sees only actual actions/outcomes; not weights, plan or topology."""
    counts = Counter()
    for event, index in enumerate(order):
        if time.monotonic() >= deadline:
            raise TimeoutError("arm budget expired; incomplete arms are not compared")
        attempt = play_mate_one(organism, fens[index], event_id=event, learn=True)
        counts["attempts"] += 1
        counts["real_moves"] += attempt.real_moves
        counts["mates"] += int(attempt.reason == "checkmate")
        if attempt.real_moves != 1 or attempt.reason in ("illegal_action", "no_action"):
            raise RuntimeError("invalid behavior: every M1 attempt must execute one legal move")
    return dict(counts)


def evaluate_arm(organism, fens, *, deadline):
    outcomes, orbits, actions = [], defaultdict(list), []
    for event, fen in enumerate(fens):
        if time.monotonic() >= deadline:
            raise TimeoutError("arm budget expired; incomplete arms are not compared")
        attempt = play_mate_one(organism, fen, event_id=event, learn=False)
        if attempt.real_moves != 1:
            raise RuntimeError("evaluation failed to execute one legal move")
        outcome = int(attempt.reason == "checkmate")
        outcomes.append(outcome)
        actions.append(attempt.action)
        orbits[orbit_key(chess.Board(fen))].append(outcome)
    rates = [sum(rows) / len(rows) for rows in orbits.values()]
    return {"mates": sum(outcomes), "count": len(outcomes),
            "success_rate": statistics.mean(outcomes),
            "orbit_macro_success_rate": statistics.mean(rates),
            "orbits_all_solved": sum(all(rows) for rows in orbits.values()),
            "orbit_count": len(orbits), "outcomes": outcomes,
            "action_digest": digest(actions),
            "by_orbit": {key: {"mates": sum(rows), "count": len(rows)}
                         for key, rows in sorted(orbits.items())}}


def learned_digest(organism):
    # Persistent learning identity, not transient request states or pickle bytes.
    return digest({"conditions": [asdict(c) | {"state": c.state.name}
                                  for c in organism.conditions.values()],
                   "bias": asdict(organism.bias), "rng": organism.rng.getstate(),
                   "completed": organism.completed, "pending": organism.pending,
                   "pruned": organism.pruned, "next_condition": organism.next_condition,
                   "last_event": organism.last_event, "plan": [asdict(p) for p in organism.plan]})


def _plans_from_json(rows):
    return tuple(Proposal(tuple((i, value) for i, value in p["atoms"]),
                          p["operator"], p["after_episode"]) for p in rows)


def run_seed(task):
    """One seed's three arms; called identically in sequential/parallel runs."""
    seed, spec, train, validation, wall_seconds, output = task
    mixed, atomic = (_plans_from_json(spec[name]) for name in ("mixed", "atomic"))
    arms = {}
    for arm in ARMS:
        started = time.monotonic()
        deadline = started + wall_seconds
        organism = AttributionOrganism(SCHEMA, seed=seed, arm=arm, mixed=mixed, atomic=atomic)
        training = train_arm(organism, train, spec["order"], deadline=deadline)
        # All inspection below is offline, after the fixed amount of play.
        expected = atomic if arm == "atomic_only" else mixed
        actual = [(c.operator, c.atoms) for c in organism.conditions.values()]
        if actual != [(p.operator, p.atoms) for p in expected] or organism.pruned:
            raise RuntimeError("representation parity failed")
        before = learned_digest(organism)
        validation_result = evaluate_arm(organism, validation, deadline=deadline)
        if learned_digest(organism) != before:
            raise RuntimeError("evaluation altered learned state")
        readers = {atom for c in organism.conditions.values() for atom in c.atoms}
        arms[arm] = {"training": training, "validation": validation_result,
                     "learned_state_digest": before,
                     "representation_digest": digest(actual),
                     "structure": {"condition_weights": len(actual),
                                   "reader_definitions": len(readers),
                                   "condition_reader_links": sum(len(c.atoms)
                                                                 for c in organism.conditions.values()),
                                   "binding_slots": organism.slots,
                                   "physical_vertices": len(organism.graph.nodes),
                                   "physical_edges": len(organism.graph.edges)},
                     "seconds": round(time.monotonic() - started, 3)}
        print(json.dumps({"seed": seed, "arm": arm,
                          "training_mates": training["mates"],
                          "validation_mates": validation_result["mates"]}), flush=True)
    if arms["online_random"]["representation_digest"] != arms["fixed_random"]["representation_digest"]:
        raise RuntimeError("mixed arms ended with different representations")
    result = {"seed": seed, "arms": arms}
    with Path(output).open("x") as stream:
        json.dump(result, stream, indent=2)
    return result


def summarize(results):
    comparisons = {}
    for left, right in (("online_random", "fixed_random"), ("fixed_random", "atomic_only")):
        pairs = []
        for result in results:
            a, b = (result["arms"][arm]["validation"] for arm in (left, right))
            pairs.append({"seed": result["seed"],
                          "row_rate_difference": a["success_rate"] - b["success_rate"],
                          "orbit_macro_difference": a["orbit_macro_success_rate"] - b["orbit_macro_success_rate"],
                          "left_only_successes": sum(x and not y for x, y in zip(a["outcomes"], b["outcomes"])),
                          "right_only_successes": sum(y and not x for x, y in zip(a["outcomes"], b["outcomes"]))})
        differences = [p["row_rate_difference"] for p in pairs]
        comparisons[f"{left}_minus_{right}"] = {
            "paired_seeds": pairs, "mean_row_rate_difference": statistics.mean(differences),
            "seed_difference_stdev": statistics.stdev(differences) if len(pairs) > 1 else None,
        }
    return comparisons


def run(args):
    if (args.episodes < 1 or args.wall_seconds < 1 or args.workers < 1
            or not args.seeds or len(set(args.seeds)) != len(args.seeds)):
        raise ValueError("positive budgets and unique seeds required")
    # Deliberately never load test.txt, even to verify its hash.
    train, train_hash = load_split(args.pool, "train")
    validation, validation_hash = load_split(args.pool, "validation")
    if not train or not validation:
        raise ValueError("training and validation pools must be nonempty")
    train_orbits = {orbit_key(chess.Board(fen)) for fen in train}
    validation_orbits = {orbit_key(chess.Board(fen)) for fen in validation}
    if train_orbits & validation_orbits:
        raise ValueError("training and validation overlap by symmetry orbit")
    plans = {}
    for seed in args.seeds:
        mixed, atomic = make_plans(SCHEMA, seed=seed, count=args.conditions, episodes=args.episodes)
        order = schedule_indices(len(train), args.episodes, seed)
        plans[str(seed)] = {"mixed": [asdict(p) for p in mixed],
                            "atomic": [asdict(p) for p in atomic], "order": order,
                            "order_digest": digest(order)}
    from recon_lite_hector.benchmarks import terminal_attribution
    source = {"production": source_identity(),
              "control_sha256": hashlib.sha256(Path(terminal_attribution.__file__).read_bytes()).hexdigest(),
              "runner_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}
    manifest = {"schema": "m1_growth_attribution.v1", "source": source,
                "episodes_per_arm": args.episodes, "conditions_per_arm": args.conditions,
                "seeds": args.seeds, "workers": args.workers,
                "wall_seconds_per_arm": args.wall_seconds,
                "train_sha256": train_hash, "validation_sha256": validation_hash,
                "train_count": len(train), "validation_count": len(validation),
                "validation_orbits": len(validation_orbits), "plans": plans,
                "pruning": "disabled equally in all arms", "final_test_opened": False,
                "limits": ["Engineering attribution, not adaptive-growth confirmation.",
                           "Equal independent weight budgets and episodes, not equal compute or reader coverage.",
                           "Online/fixed mixed arms share final definitions and exploration RNG, not outcomes.",
                           "Atomic-only at 80 conditions exhausts this schema's atomic vocabulary.",
                           "Different active feature counts also change normalized-update denominators."]}
    args.output.mkdir(parents=True, exist_ok=False)
    # Write before any training/outcomes. Existing outputs are never overwritten.
    with (args.output / "manifest.json").open("x") as stream:
        json.dump(manifest, stream, indent=2)
    tasks = [(seed, plans[str(seed)], train, validation, args.wall_seconds,
              str(args.output / f"seed-{seed}.json")) for seed in args.seeds]
    try:
        if args.workers == 1:
            results = [run_seed(task) for task in tasks]
        else:
            with ProcessPoolExecutor(max_workers=min(args.workers, len(tasks)),
                                     mp_context=multiprocessing.get_context("spawn")) as executor:
                results = list(executor.map(run_seed, tasks))
        result = {"status": "complete", "manifest_digest": digest(manifest),
                  "comparisons": summarize(results), "results": results}
        with (args.output / "summary.json").open("x") as stream:
            json.dump(result, stream, indent=2)
    except Exception as error:
        with (args.output / "failure.json").open("x") as stream:
            json.dump({"status": "incomplete", "error": str(error)}, stream)
        raise
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pool", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--seeds", type=int, nargs="+", default=[1, 2, 3])
    parser.add_argument("--episodes", type=int, default=128)
    parser.add_argument("--conditions", type=int, default=80)
    parser.add_argument("--workers", type=int, default=1)
    parser.add_argument("--wall-seconds", type=int, default=600,
                        help="per-arm safety bound; incomplete arms are never compared")
    result = run(parser.parse_args())
    print(json.dumps(result["comparisons"], indent=2))


if __name__ == "__main__":
    main()
