"""Five-arm actual-play experiment for internal randomized TRIAL access."""
import argparse
from concurrent.futures import ProcessPoolExecutor
import copy
from dataclasses import asdict
import hashlib
import json
import multiprocessing
from pathlib import Path
import time

import chess

from recon_lite_hector.learning import trial_usefulness as mechanism
from recon_lite_chess.coach.pools import load_split, orbit_key
from recon_lite_chess.coach.runner import source_identity
from recon_lite_chess.coach.terminal import SCHEMA
from . import live_trial as prior
from .mate_one_attribution import digest, schedule_indices

ARMS = {"none": ("none", False), "ranked": ("ranked", False),
        "random": ("random", False), "probe_ranked": ("ranked", True),
        "probe_random": ("random", True)}
train = prior.train  # The same opaque coach loop and action-bound feedback.


class UsefulnessOrganism(mechanism.UsefulnessDevelopment):
    embodiment = "typed_feature_terminals_v1"


def use_digest(o):
    if not isinstance(o, mechanism.UsefulnessDevelopment):
        return None
    return digest({"config": asdict(o.usefulness_config), "rng": o.use_rng.getstate(),
                   "pending": o.use_pending, "outcomes": [asdict(r) for r in o.use_outcomes]})


def evaluate(o, fens, *, deadline):
    before = use_digest(o)
    result = prior.evaluate(o, fens, deadline=deadline)
    if use_digest(o) != before:
        raise RuntimeError("evaluation changed trial-use evidence or randomness")
    return result


def ablation(o, fens, normal, actions, *, deadline):
    before = prior.learned_digest(o), use_digest(o)
    clone = copy.deepcopy(o)
    c = clone.trial_condition
    live = c is not None and c.identity in clone.conditions
    if live:
        c.weight.fast = c.weight.slow = 0.0
    result, masked_actions = evaluate(clone, fens, deadline=deadline)
    if (prior.learned_digest(o), use_digest(o)) != before:
        raise RuntimeError("ablation changed the original actor or its use history")
    return {"trial_was_live": live, "evaluation": result,
            "action_changes": sum(a != b for a, b in zip(actions, masked_actions)),
            "mates_lost_when_masked": sum(a > b for a, b in zip(normal["outcomes"], result["outcomes"])),
            "mates_gained_when_masked": sum(a < b for a, b in zip(normal["outcomes"], result["outcomes"])),
            "net_trial_mates": normal["mates"] - result["mates"]}


def run_seed(task):
    seed, spec, fens, validation, wall_seconds, output = task
    deadline = time.monotonic() + wall_seconds
    after, arms = spec["after_episode"], {}
    for name, (role, probe) in ARMS.items():
        started = time.monotonic()
        kwargs = {"seed": seed, "config": prior.DevelopmentConfig(**spec["actor_config"]),
                  "shadow_config": prior.residual_shadow.ShadowConfig(**spec["shadow_config"]),
                  "trial_config": prior.mechanism.TrialConfig(role, after)}
        o = (UsefulnessOrganism(**kwargs, usefulness_config=mechanism.UsefulnessConfig(**spec["usefulness_config"]))
             if probe else prior.TrialOrganism(**kwargs))
        prefix = train(o, fens, spec["order"][:after], start_event=0, deadline=deadline)
        history = digest(o.shadow.report())
        if digest([asdict(d) for d in o.shadow.definitions]) != digest(spec["definitions"]):
            raise RuntimeError("candidate plan changed")
        if arms and (prefix != arms["none"]["prefix_training"]
                     or history != arms["none"]["shadow"]["history_digest"]):
            raise RuntimeError("probe changed pre-attachment behavior or evidence")
        suffix = train(o, fens, spec["order"][after:], start_event=after, deadline=deadline)
        if digest(o.shadow.report()) != history or o.shadow.observations != after:
            raise RuntimeError("frozen shadow history changed")
        report, actions = evaluate(o, validation, deadline=deadline)
        c = o.trial_condition
        result = {"prefix_training": prefix, "suffix_training": suffix,
                  "decision": dict(o.trial_decision), "live_counts": dict(o.live_counts),
                  "trial_state": None if c is None else c.state.name,
                  "shadow": prior.shadow_experiment.public_shadow_report(o),
                  "structure": {"live_conditions": len(o.conditions),
                                "retired_conditions": len(o.retired_conditions),
                                "physical_vertices": len(o.graph.nodes), "physical_edges": len(o.graph.edges)},
                  "evaluation": report, "learned_digest": prior.learned_digest(o)}
        if probe:
            use = o.usefulness_report()
            if use["groups"]["disabled"]["participations"]:
                raise RuntimeError("disabled trial received actual participation credit")
            result["usefulness"] = use | {"history_digest": use_digest(o)}
        if role != "none":
            result["ablation"] = ablation(o, validation, report, actions, deadline=deadline)
        result["seconds"] = round(time.monotonic() - started, 3)
        arms[name] = result
        print(json.dumps({"seed": seed, "arm": name, "status": result["decision"]["status"],
                          "suffix_mates": suffix["mates"], "validation_mates": report["mates"],
                          "use_reward_difference": result.get("usefulness", {}).get("mean_reward_difference"),
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
        mates = {name: a["evaluation"]["mates"] for name, a in arms.items()}
        rows.append({"seed": result["seed"], "validation_mates": mates,
                     "probe_ranked_minus_always": mates["probe_ranked"] - mates["ranked"],
                     "probe_random_minus_always": mates["probe_random"] - mates["random"],
                     "usefulness": {role: arms[f"probe_{role}"]["usefulness"] for role in ("ranked", "random")}})
    return {"paired_seeds": rows, "automatic_selection_from_usefulness": False}


def run(args):
    if (not args.seeds or len(set(args.seeds)) != len(args.seeds)
            or min(args.workers, args.wall_seconds, args.suffix) < 1):
        raise ValueError("positive budgets and unique seeds required")
    actor_config = prior.DevelopmentConfig(max_conditions=args.conditions)
    shadow_config = prior.residual_shadow.ShadowConfig(candidates=args.candidates,
                         discovery_episodes=args.discovery, min_support=args.min_support)
    trial_config = prior.mechanism.TrialConfig("ranked", args.after_episode)
    use_config = mechanism.UsefulnessConfig(args.window, args.probability)
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
                        "usefulness_config": asdict(use_config), "after_episode": args.after_episode,
                        "order": schedule_indices(len(fens), episodes, seed),
                        "definitions": [asdict(d) for d in prior.residual_shadow.random_definitions(
                            SCHEMA, seed=seed, count=shadow_config.candidates)]} for seed in args.seeds}
    modules = {"trial_usefulness": mechanism, "live_trial": prior.mechanism,
               "residual_shadow": prior.residual_shadow, "prior_experiment": prior,
               "shadow_experiment": prior.shadow_experiment, "shared_helpers": prior.mate_one_attribution}
    source = {"runtime": source_identity(),
              "runner_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}
    source.update({f"{name}_sha256": hashlib.sha256(Path(module.__file__).read_bytes()).hexdigest()
                   for name, module in modules.items()})
    manifest = {"schema": "trial_usefulness_experiment.v1", "seeds": args.seeds, "arms": ARMS,
                "episodes_per_arm": episodes, "workers": args.workers,
                "wall_seconds_per_seed": args.wall_seconds, "plans": plans, "source": source,
                "train_sha256": train_hash, "validation_sha256": validation_hash,
                "train_count": len(fens), "validation_count": len(validation),
                "train_orbits": len(train_orbits), "validation_orbits": len(validation_orbits),
                "training_moves": len(args.seeds) * 5 * episodes,
                "validation_moves_including_ablations": len(args.seeds) * 9 * len(validation),
                "final_test_opened": False, "validation_is_development": True,
                "limits": ["Usefulness evidence is not used for automatic selection or maturity.",
                           "All assigned outcomes enter the estimate, not only activations.",
                           "Adaptive access value is not lifetime topology value or final ablation effect.",
                           "Reused development seeds and a short window do not establish reliable superiority."]}
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
    parser.add_argument("--window", type=int, default=128)
    parser.add_argument("--probability", type=float, default=0.5)
    parser.add_argument("--min-support", type=int, default=4)
    parser.add_argument("--workers", type=int, default=1)
    parser.add_argument("--wall-seconds", type=int, default=1200)
    print(json.dumps(run(parser.parse_args())["comparisons"], indent=2))


if __name__ == "__main__":
    main()
