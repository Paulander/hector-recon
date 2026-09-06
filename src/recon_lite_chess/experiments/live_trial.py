"""Fixed ranked/random/no-addition actual-play test of one live TRIAL."""
import argparse
from collections import Counter, defaultdict
from concurrent.futures import ProcessPoolExecutor
import copy
from dataclasses import asdict
import hashlib
import json
import multiprocessing
from pathlib import Path
import statistics
import time

import chess

from recon_lite_hector.learning import live_trial as mechanism, residual_shadow
from recon_lite_hector.learning.terminal_development import DevelopmentConfig
from recon_lite_chess.coach.exercise import play_mate_one
from recon_lite_chess.coach.pools import load_split, orbit_key
from recon_lite_chess.coach.runner import source_identity
from recon_lite_chess.coach.terminal import SCHEMA
from . import mate_one_attribution, residual_shadow as shadow_experiment
from .mate_one_attribution import digest, schedule_indices

ROLES = ("none", "ranked", "random")


class TrialOrganism(mechanism.TrialDevelopment):
    embodiment = "typed_feature_terminals_v1"


def learned_digest(o):
    """Ignore transient request states and allocation of additional binding slots."""
    return digest({"config": asdict(o.config), "trial_config": asdict(o.trial_config),
                   "bias": asdict(o.bias),
                   "conditions": [asdict(c) | {"state": c.state.name} for c in o.conditions.values()],
                   "retired": [asdict(c) | {"state": c.state.name} for c in o.retired_conditions.values()],
                   "completed": o.completed, "last_event": o.last_event, "pending": o.pending,
                   "next_condition": o.next_condition, "pruned": o.pruned, "rng": o.rng.getstate(),
                   "shadow": None if o.shadow is None else o.shadow.report(),
                   "trial_decision": o.trial_decision, "live_counts": o.live_counts})


def train(o, fens, order, *, start_event, deadline):
    """Only ordinary opaque coach interactions; no graph-dependent scheduling."""
    counts, transcript = Counter(), hashlib.sha256()
    for event, index in enumerate(order, start=start_event):
        if time.monotonic() >= deadline:
            raise TimeoutError("seed budget expired; no shortened comparison")
        attempt = play_mate_one(o, fens[index], event_id=event, learn=True)
        if attempt.real_moves != 1 or attempt.reason in ("illegal_action", "no_action"):
            raise RuntimeError("every exercise must execute exactly one legal move")
        counts["attempts"] += 1
        counts["real_moves"] += attempt.real_moves
        counts["mates"] += int(attempt.reason == "checkmate")
        transcript.update(json.dumps((event, attempt.action, attempt.reward, attempt.reason)).encode())
    return dict(counts) | {"action_outcome_digest": transcript.hexdigest()}


def evaluate(o, fens, *, deadline):
    """Read-only evaluation; action tokens exist only for offline paired counts."""
    before = learned_digest(o)
    outcomes, actions, orbits = [], [], defaultdict(list)
    for event, fen in enumerate(fens):
        if time.monotonic() >= deadline:
            raise TimeoutError("seed budget expired; no shortened evaluation")
        attempt = play_mate_one(o, fen, event_id=event, learn=False)
        if attempt.real_moves != 1 or attempt.reason in ("illegal_action", "no_action"):
            raise RuntimeError("evaluation must execute exactly one legal move")
        outcome = int(attempt.reason == "checkmate")
        outcomes.append(outcome)
        actions.append(attempt.action)
        orbits[orbit_key(chess.Board(fen))].append(outcome)
    if learned_digest(o) != before:
        raise RuntimeError("evaluation changed learned state")
    report = {"mates": sum(outcomes), "count": len(outcomes),
              "success_rate": statistics.mean(outcomes), "outcomes": outcomes,
              "orbit_macro_success_rate": statistics.mean(sum(v) / len(v) for v in orbits.values()),
              "orbit_count": len(orbits), "orbits_all_solved": sum(all(v) for v in orbits.values()),
              "action_digest": digest(actions), "learned_state_unchanged": True}
    return report, actions


def ablation(o, fens, normal, actions, *, deadline):
    """Offline clone intervention, never feedback or a maturity decision."""
    before = learned_digest(o)
    masked = copy.deepcopy(o)
    c = masked.trial_condition
    live = c is not None and c.identity in masked.conditions
    if live:
        c.weight.fast = c.weight.slow = 0.0
    result, masked_actions = evaluate(masked, fens, deadline=deadline)
    if learned_digest(o) != before:
        raise RuntimeError("ablation changed original actor")
    return {"trial_was_live": live, "evaluation": result,
            "action_changes": sum(a != b for a, b in zip(actions, masked_actions)),
            "mates_lost_when_masked": sum(a > b for a, b in zip(normal["outcomes"], result["outcomes"])),
            "mates_gained_when_masked": sum(a < b for a, b in zip(normal["outcomes"], result["outcomes"])),
            "net_trial_mates": normal["mates"] - result["mates"]}


def run_seed(task):
    seed, spec, fens, validation, wall_seconds, output = task
    deadline = time.monotonic() + wall_seconds
    arms = {}
    after = spec["after_episode"]
    for role in ROLES:
        started = time.monotonic()
        o = TrialOrganism(seed=seed, config=DevelopmentConfig(**spec["actor_config"]),
                          shadow_config=residual_shadow.ShadowConfig(**spec["shadow_config"]),
                          trial_config=mechanism.TrialConfig(role, after))
        prefix = train(o, fens, spec["order"][:after], start_event=0, deadline=deadline)
        history = digest(o.shadow.report())
        if digest([asdict(d) for d in o.shadow.definitions]) != digest(spec["definitions"]):
            raise RuntimeError("candidate plan changed")
        if arms and (prefix != arms["none"]["prefix_training"]
                     or history != arms["none"]["shadow"]["history_digest"]):
            raise RuntimeError("trial role changed pre-attachment behavior or evidence")
        suffix = train(o, fens, spec["order"][after:], start_event=after, deadline=deadline)
        if digest(o.shadow.report()) != history or o.shadow.observations != after:
            raise RuntimeError("shadow evidence was updated after live attachment")
        report, actions = evaluate(o, validation, deadline=deadline)
        c = o.trial_condition
        result = {"prefix_training": prefix, "suffix_training": suffix,
                  "decision": dict(o.trial_decision), "live_counts": dict(o.live_counts),
                  "trial_state": None if c is None else c.state.name,
                  "shadow": shadow_experiment.public_shadow_report(o),
                  "structure": {"live_conditions": len(o.conditions),
                                "retired_conditions": len(o.retired_conditions),
                                "physical_vertices": len(o.graph.nodes),
                                "physical_edges": len(o.graph.edges)},
                  "evaluation": report, "learned_digest": learned_digest(o)}
        if role != "none":
            result["ablation"] = ablation(o, validation, report, actions, deadline=deadline)
        result["seconds"] = round(time.monotonic() - started, 3)
        arms[role] = result
        print(json.dumps({"seed": seed, "role": role, "decision": result["decision"]["status"],
                          "suffix_mates": suffix["mates"], "validation_mates": report["mates"],
                          "seconds": result["seconds"]}), flush=True)
    if time.monotonic() >= deadline:
        raise TimeoutError("seed budget expired")
    result = {"seed": seed, "prefix_behavior_and_history_identical": True, "arms": arms}
    with Path(output).open("x") as stream:
        json.dump(result, stream, indent=2)
    return result


def summarize(results):
    rows = []
    for result in results:
        arms = result["arms"]
        mates = {role: arms[role]["evaluation"]["mates"] for role in ROLES}
        rows.append({"seed": result["seed"], "validation_mates": mates,
                     "ranked_minus_none": mates["ranked"] - mates["none"],
                     "random_minus_none": mates["random"] - mates["none"],
                     "ranked_minus_random": mates["ranked"] - mates["random"],
                     "same_nominee": (arms["ranked"]["decision"].get("source_index") is not None
                         and arms["ranked"]["decision"].get("source_index")
                         == arms["random"]["decision"].get("source_index"))})
    return {"paired_seeds": rows,
            "mean_ranked_minus_none": statistics.mean(r["ranked_minus_none"] for r in rows),
            "mean_random_minus_none": statistics.mean(r["random_minus_none"] for r in rows),
            "mean_ranked_minus_random": statistics.mean(r["ranked_minus_random"] for r in rows)}


def run(args):
    if (not args.seeds or len(set(args.seeds)) != len(args.seeds)
            or min(args.workers, args.wall_seconds, args.suffix) < 1):
        raise ValueError("positive budgets and unique seeds required")
    actor_config = DevelopmentConfig(max_conditions=args.conditions)
    shadow_config = residual_shadow.ShadowConfig(candidates=args.candidates,
                         discovery_episodes=args.discovery, min_support=args.min_support)
    trial_config = mechanism.TrialConfig("ranked", args.after_episode)
    if trial_config.after_episode <= shadow_config.discovery_episodes:
        raise ValueError("attachment requires a prospective interval after discovery")
    fens, train_hash = load_split(args.pool, "train")
    validation, validation_hash = load_split(args.pool, "validation")
    if not fens or not validation:
        raise ValueError("nonempty training and validation pools required")
    train_orbits = {orbit_key(chess.Board(fen)) for fen in fens}
    validation_orbits = {orbit_key(chess.Board(fen)) for fen in validation}
    if train_orbits & validation_orbits:
        raise ValueError("training and validation symmetry orbits overlap")
    episodes = args.after_episode + args.suffix
    plans = {str(seed): {"actor_config": asdict(actor_config), "shadow_config": asdict(shadow_config),
                        "after_episode": args.after_episode,
                        "order": schedule_indices(len(fens), episodes, seed),
                        "definitions": [asdict(d) for d in residual_shadow.random_definitions(
                            SCHEMA, seed=seed, count=shadow_config.candidates)]} for seed in args.seeds}
    modules = {"live_trial": mechanism, "residual_shadow": residual_shadow,
               "shadow_experiment": shadow_experiment, "shared_helpers": mate_one_attribution}
    source = {"runtime": source_identity(),
              "runner_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}
    source.update({f"{name}_sha256": hashlib.sha256(Path(module.__file__).read_bytes()).hexdigest()
                   for name, module in modules.items()})
    manifest = {"schema": "live_trial_experiment.v1", "seeds": args.seeds, "roles": ROLES,
                "episodes_per_arm": episodes, "workers": args.workers,
                "wall_seconds_per_seed": args.wall_seconds, "plans": plans, "source": source,
                "train_sha256": train_hash, "validation_sha256": validation_hash,
                "train_count": len(fens), "validation_count": len(validation),
                "train_orbits": len(train_orbits), "validation_orbits": len(validation_orbits),
                "training_moves": len(args.seeds) * 3 * episodes,
                "validation_moves_including_ablations": len(args.seeds) * 5 * len(validation),
                "final_test_opened": False, "validation_is_development": True,
                "limits": ["One TRIAL, not general growth regulation or causal maturity.",
                           "Retained historical prediction evidence is not live participation.",
                           "Ablation is immediate dependence, not counterfactual retraining.",
                           "Repeated prefixes and viewed development seeds are not independent confirmation."]}
    args.output.mkdir(parents=True, exist_ok=False)
    with (args.output / "manifest.json").open("x") as stream:
        json.dump(manifest, stream, indent=2)
    tasks = [(seed, plans[str(seed)], fens, validation, args.wall_seconds,
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
    parser.add_argument("--after-episode", type=int, default=128)
    parser.add_argument("--suffix", type=int, default=128)
    parser.add_argument("--min-support", type=int, default=4)
    parser.add_argument("--workers", type=int, default=1)
    parser.add_argument("--wall-seconds", type=int, default=1200)
    print(json.dumps(run(parser.parse_args())["comparisons"], indent=2))


if __name__ == "__main__":
    main()
