"""Bounded actual-play experiment for an internal shadow nomination mechanism."""
import argparse
from collections import Counter
from concurrent.futures import ProcessPoolExecutor
from dataclasses import asdict
import hashlib
import json
import multiprocessing
from pathlib import Path
import statistics
import time

from recon_lite_hector.learning import residual_shadow as mechanism
from recon_lite_hector.learning.terminal_development import DevelopmentConfig
from recon_lite_chess.coach.exercise import play_mate_one
from recon_lite_chess.coach.pools import load_split
from recon_lite_chess.coach.runner import source_identity
from recon_lite_chess.coach.terminal import SCHEMA, TerminalOrganism
from .mate_one_attribution import digest, schedule_indices


class ShadowOrganism(mechanism.ShadowDevelopment):
    embodiment = "typed_feature_terminals_v1"


def actor_digest(organism):
    """Offline actor identity; excludes shadow history and transient node states."""
    return digest({"config": asdict(organism.config), "bias": asdict(organism.bias),
                   "conditions": [asdict(c) | {"state": c.state.name} for c in organism.conditions.values()],
                   "retired": [asdict(c) | {"state": c.state.name} for c in organism.retired_conditions.values()],
                   "completed": organism.completed, "last_event": organism.last_event,
                   "pending": organism.pending, "next_condition": organism.next_condition,
                   "pruned": organism.pruned, "rng": organism.rng.getstate(),
                   "nodes": [nid for nid in organism.graph.nodes if not nid.startswith("shadow:")],
                   "edges": [(e.src, e.dst, str(e.ltype), float(e.w)) for e in organism.graph.edges
                             if not e.src.startswith("shadow:") and not e.dst.startswith("shadow:")]})


def train(organism, fens, order, *, deadline):
    """Opaque coach records only actual submitted actions and observed outcomes."""
    counts, transcript = Counter(), hashlib.sha256()
    for event, index in enumerate(order):
        if time.monotonic() >= deadline:
            raise TimeoutError("seed pair budget expired; no shortened comparison")
        attempt = play_mate_one(organism, fens[index], event_id=event, learn=True)
        if attempt.real_moves != 1 or attempt.reason in ("illegal_action", "no_action"):
            raise RuntimeError("every exercise must execute exactly one legal move")
        counts["attempts"] += 1
        counts["real_moves"] += attempt.real_moves
        counts["mates"] += int(attempt.reason == "checkmate")
        transcript.update(json.dumps((event, attempt.action, attempt.reward, attempt.reason)).encode())
    return dict(counts) | {"action_outcome_digest": transcript.hexdigest()}


def public_shadow_report(organism):
    # No raw boards/actions, live weights or trained checkpoints in public output.
    book = organism.shadow
    nomination = None if book.nomination is None else {
        k: v for k, v in book.nomination.items() if not k.endswith("initial_weight")}
    return {"nomination_status": book.nomination_status, "nomination": nomination,
            "prospective": dict(book.prospective), "candidate_definitions": len(book.definitions),
            "candidate_reader_definitions": len({atom for d in book.definitions for atom in d.atoms}),
            "candidate_reader_links": sum(len(d.atoms) for d in book.definitions),
            "history_digest": digest(book.report())}


def run_seed(task):
    seed, spec, fens, wall_seconds, output = task
    started = time.monotonic()
    deadline = started + wall_seconds
    config = DevelopmentConfig(**spec["actor_config"])
    shadow_config = mechanism.ShadowConfig(**spec["shadow_config"])
    arms, actors = {}, {}
    for name in ("control", "shadow"):
        begin = time.monotonic()
        organism = (TerminalOrganism(seed=seed, config=config) if name == "control" else
                    ShadowOrganism(seed=seed, config=config, shadow_config=shadow_config))
        training = train(organism, fens, spec["order"], deadline=deadline)
        # Scientific inspection begins only after each fixed training run.
        arms[name] = {"training": training, "actor_digest": actor_digest(organism),
                      "structure": {"live_conditions": len(organism.conditions),
                                    "physical_vertices": len(organism.graph.nodes),
                                    "physical_edges": len(organism.graph.edges)},
                      "seconds": round(time.monotonic() - begin, 3)}
        actors[name] = organism
        print(json.dumps({"seed": seed, "arm": name, "mates": training["mates"]}), flush=True)
    if arms["control"]["training"] != arms["shadow"]["training"]:
        raise RuntimeError("shadow changed actual behavior")
    if arms["control"]["actor_digest"] != arms["shadow"]["actor_digest"]:
        raise RuntimeError("shadow changed learned actor state")
    book = actors["shadow"].shadow
    if digest([asdict(d) for d in book.definitions]) != digest(spec["definitions"]):
        raise RuntimeError("candidate plan changed")
    if book.observations != len(spec["order"]):
        raise RuntimeError("shadow missed actual outcomes")
    expected_count = 0 if book.nomination is None else len(spec["order"]) - shadow_config.discovery_episodes
    if book.prospective["count"] != expected_count:
        raise RuntimeError("prospective prefix/suffix accounting failed")
    if time.monotonic() >= deadline:
        raise TimeoutError("seed pair budget expired")
    result = {"seed": seed, "arms": arms, "shadow": public_shadow_report(actors["shadow"]),
              "behavior_and_actor_unchanged": True}
    with Path(output).open("x") as stream:
        json.dump(result, stream, indent=2)
    return result


def summarize(results):
    pairs, unavailable = [], []
    for result in results:
        report = result["shadow"]
        e = report["prospective"]
        if e["count"] == 0:
            unavailable.append({"seed": result["seed"], "reason": report["nomination_status"]})
            continue
        n = e["count"]
        pairs.append({"seed": result["seed"], "prospective_actions": n,
                      "base_mse": e["base_squared_error"] / n,
                      "ranked_mse": e["ranked_squared_error"] / n,
                      "random_mse": e["random_squared_error"] / n,
                      "ranked_gain_vs_base": (e["base_squared_error"] - e["ranked_squared_error"]) / n,
                      "random_gain_vs_base": (e["base_squared_error"] - e["random_squared_error"]) / n,
                      "ranked_gain_vs_random": (e["random_squared_error"] - e["ranked_squared_error"]) / n,
                      "same_nominee": report["nomination"]["ranked"] == report["nomination"]["random"]})
    gains = [p["ranked_gain_vs_random"] for p in pairs]
    return {"paired_seeds": pairs, "unavailable": unavailable,
            "mean_ranked_gain_vs_random": statistics.mean(gains) if gains else None,
            "seed_gain_stdev": statistics.stdev(gains) if len(gains) > 1 else None}


def run(args):
    if (not args.seeds or len(set(args.seeds)) != len(args.seeds)
            or min(args.workers, args.wall_seconds, args.prospective) < 1):
        raise ValueError("positive budgets and unique seeds required")
    actor_config = DevelopmentConfig(max_conditions=args.conditions)
    shadow_config = mechanism.ShadowConfig(candidates=args.candidates, discovery_episodes=args.discovery,
                                           min_support=args.min_support)
    episodes = args.discovery + args.prospective
    # This experiment does not read validation.txt or test.txt.
    fens, train_hash = load_split(args.pool, "train")
    if not fens:
        raise ValueError("nonempty training pool required")
    plans = {}
    for seed in args.seeds:
        plans[str(seed)] = {"actor_config": asdict(actor_config), "shadow_config": asdict(shadow_config),
                            "order": schedule_indices(len(fens), episodes, seed),
                            "definitions": [asdict(d) for d in mechanism.random_definitions(
                                SCHEMA, seed=seed, count=shadow_config.candidates)]}
    from . import mate_one_attribution
    manifest = {"schema": "residual_shadow_experiment.v1", "seeds": args.seeds,
                "episodes_per_arm": episodes, "workers": args.workers,
                "wall_seconds_per_seed_pair": args.wall_seconds,
                "train_sha256": train_hash, "train_count": len(fens), "plans": plans,
                "validation_opened": False, "final_test_opened": False,
                "source": {"runtime": source_identity(),
                           "mechanism_sha256": hashlib.sha256(Path(mechanism.__file__).read_bytes()).hexdigest(),
                           "runner_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                           "shared_experiment_helpers_sha256": hashlib.sha256(Path(mate_one_attribution.__file__).read_bytes()).hexdigest()},
                "limits": ["Internal nomination only; shadows cannot act or earn maturity.",
                           "Prospective prediction error on actual chosen actions, not counterfactual behavior.",
                           "Matched arity/operator/support bin, not exact activation count or compute.",
                           "Three short development seeds do not establish superiority or mastery."]}
    args.output.mkdir(parents=True, exist_ok=False)
    with (args.output / "manifest.json").open("x") as stream:
        json.dump(manifest, stream, indent=2)
    tasks = [(seed, plans[str(seed)], fens, args.wall_seconds,
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
    parser.add_argument("--seeds", nargs="+", type=int, default=[1, 2, 3])
    parser.add_argument("--conditions", type=int, default=32)
    parser.add_argument("--candidates", type=int, default=64)
    parser.add_argument("--discovery", type=int, default=64)
    parser.add_argument("--prospective", type=int, default=64)
    parser.add_argument("--min-support", type=int, default=4)
    parser.add_argument("--workers", type=int, default=1)
    parser.add_argument("--wall-seconds", type=int, default=600)
    print(json.dumps(run(parser.parse_args())["comparisons"], indent=2))


if __name__ == "__main__":
    main()
