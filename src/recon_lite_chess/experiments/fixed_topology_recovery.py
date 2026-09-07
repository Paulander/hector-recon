"""Paired recovery: normal lifecycle versus fixed shared condition definitions.

Laboratory-only controls. Both arms keep edge learning and receive only actual
scalar outcomes. Recovery exploration uses a separate, matched internal RNG so
birth proposals cannot shift subsequent exploration draws.
"""
import argparse
from concurrent.futures import ProcessPoolExecutor
import copy
from dataclasses import asdict
import hashlib
import json
import multiprocessing
from pathlib import Path
import random
import time

import chess

from recon_lite_chess.coach.pools import load_split, orbit_key
from recon_lite_chess.coach.runner import source_identity
from recon_lite_chess.coach.terminal import SCHEMA
from . import trial_usefulness as prior

digest = prior.digest
train = prior.train
MODES = ("normal", "fixed")


class RecoveryControl:
    """An experimental switch, not a learned growth or retention mechanism."""
    def __init__(self, *, recovery_after, seed=1, **kwargs):
        if recovery_after < 1:
            raise ValueError("positive completed-history boundary required")
        super().__init__(seed=seed, **kwargs)
        self.recovery_after = recovery_after
        self.hold_topology = False
        self.recovery_rng = random.Random(f"recovery-exploration:{seed}")

    def act(self, port, *, event_id, learn):
        if not learn or self.completed < self.recovery_after:
            return super().act(port, event_id=event_id, learn=learn)
        birth_rng = self.rng
        self.rng = self.recovery_rng
        try:
            return super().act(port, event_id=event_id, learn=learn)
        finally:
            self.rng = birth_rng

    def _birth(self):
        # Outcome N completes the shared prefix, including its ordinary birth.
        if not (self.hold_topology and self.completed > self.recovery_after):
            super()._birth()

    def _prune(self):
        if not (self.hold_topology and self.completed > self.recovery_after):
            super()._prune()


class RecoveryTrial(RecoveryControl, prior.prior.TrialOrganism):
    pass


class RecoveryProbe(RecoveryControl, prior.UsefulnessOrganism):
    pass


def control_digest(o):
    return digest({"after": o.recovery_after, "hold": o.hold_topology,
                   "rng": o.recovery_rng.getstate()})


def representation_digest(o):
    """Shared definitions/history identities; extra binding replicas are allowed."""
    def definition(c):
        return c.identity, c.operator, c.atoms, c.born, c.state.name
    return digest({"live": [definition(c) for c in o.conditions.values()],
                   "retired": [definition(c) for c in o.retired_conditions.values()],
                   "next_condition": o.next_condition, "pruned": o.pruned})


def weight_digest(o):
    return digest({"bias": asdict(o.bias),
                   "live": [(c.identity, asdict(c.weight)) for c in o.conditions.values()]})


def evaluate(o, fens, *, deadline):
    before = control_digest(o)
    result = prior.evaluate(o, fens, deadline=deadline)
    if control_digest(o) != before:
        raise RuntimeError("evaluation changed recovery control state")
    return result


def save(path, value):
    with Path(path).open("x") as stream:
        json.dump(value, stream, indent=2)


def run_seed(task):
    seed, spec, fens, validation, wall_seconds, output = task
    started, pairs = time.monotonic(), {}
    deadline = started + wall_seconds
    after, stop = spec["after_episode"], spec["recovery_after"]
    for name, (role, probe) in prior.ARMS.items():
        cls = RecoveryProbe if probe else RecoveryTrial
        kwargs = {"seed": seed, "recovery_after": stop,
                  "config": prior.prior.DevelopmentConfig(**spec["actor_config"]),
                  "shadow_config": prior.prior.residual_shadow.ShadowConfig(**spec["shadow_config"]),
                  "trial_config": prior.prior.mechanism.TrialConfig(role, after)}
        if probe:
            kwargs["usefulness_config"] = prior.mechanism.UsefulnessConfig(**spec["usefulness_config"])
        o = cls(**kwargs)
        prefix = train(o, fens, spec["order"][:after], start_event=0, deadline=deadline)
        history = digest(o.shadow.report())
        if digest([asdict(d) for d in o.shadow.definitions]) != digest(spec["definitions"]):
            raise RuntimeError("candidate plan changed")
        if pairs and (prefix != pairs["none"]["prefix_training"]
                      or history != pairs["none"]["shadow"]["history_digest"]):
            raise RuntimeError("control changed the common prefix")
        suffix = train(o, fens, spec["order"][after:stop], start_event=after, deadline=deadline)
        before = {"learned_digest": prior.prior.learned_digest(o),
                  "use_history_digest": prior.use_digest(o), "lifecycle": prior.lifecycle(o),
                  "representation_digest": representation_digest(o), "weight_digest": weight_digest(o),
                  "control_digest": control_digest(o)}
        pair = {"prefix_training": prefix, "suffix_training": suffix, "before_recovery": before,
                "decision": dict(o.trial_decision), "shadow": prior.prior.shadow_experiment.public_shadow_report(o),
                "arms": {}}
        for mode in MODES:
            arm_started = time.monotonic()
            actor = copy.deepcopy(o)  # Copies experience; it does not create more actual moves.
            actor.hold_topology = mode == "fixed"
            recovered = train(actor, fens, spec["order"][stop:], start_event=stop, deadline=deadline)
            if prior.use_digest(actor) != before["use_history_digest"]:
                raise RuntimeError("recovery changed completed probe history")
            if digest(actor.shadow.report()) != history or actor.shadow.observations != after:
                raise RuntimeError("recovery changed frozen shadow history")
            same = representation_digest(actor) == before["representation_digest"]
            if mode == "fixed" and not same:
                raise RuntimeError("fixed recovery changed shared topology/history identities")
            if probe and not actor.use_enabled:
                raise RuntimeError("recovery failed to restore normal trial access")
            report, actions = evaluate(actor, validation, deadline=deadline)
            result = {"recovery_training": recovered, "after_recovery": prior.lifecycle(actor),
                      "representation_unchanged": same, "weights_changed": weight_digest(actor) != before["weight_digest"],
                      "probe_history_unchanged": True, "live_counts": dict(actor.live_counts),
                      "evaluation": report, "learned_digest": prior.prior.learned_digest(actor),
                      "control_digest": control_digest(actor),
                      "exploration_rng_digest": digest(actor.recovery_rng.getstate()),
                      "structure": {"physical_vertices": len(actor.graph.nodes), "physical_edges": len(actor.graph.edges)}}
            if probe:
                result["usefulness"] = actor.usefulness_report() | {"history_digest": prior.use_digest(actor)}
            if role != "none":
                state = control_digest(actor)
                result["ablation"] = prior.ablation(actor, validation, report, actions, deadline=deadline)
                if control_digest(actor) != state:
                    raise RuntimeError("ablation changed recovery state")
            result["seconds"] = round(time.monotonic() - arm_started, 3)
            pair["arms"][mode] = result
            save(Path(output).with_name(f"seed-{seed}-{name}-{mode}.json"),
                 {"seed": seed, "role": name, "mode": mode,
                  "shared_history": {k: v for k, v in pair.items() if k != "arms"}, "result": result})
            print(json.dumps({"seed": seed, "role": name, "mode": mode,
                              "recovery_mates": recovered["mates"], "validation_mates": report["mates"],
                              "pruned": actor.pruned, "representation_unchanged": same}), flush=True)
        if pair["arms"]["normal"]["exploration_rng_digest"] != pair["arms"]["fixed"]["exploration_rng_digest"]:
            raise RuntimeError("paired recovery exploration streams diverged")
        if (prior.prior.learned_digest(o) != before["learned_digest"]
                or control_digest(o) != before["control_digest"] or prior.use_digest(o) != before["use_history_digest"]):
            raise RuntimeError("recovery modified the shared source organism")
        pair["exploration_streams_match"] = True
        pairs[name] = pair
    if time.monotonic() >= deadline:
        raise TimeoutError("seed budget expired")
    result = {"seed": seed, "pairs": pairs, "seconds": round(time.monotonic() - started, 3)}
    save(output, result)
    return result


def summarize(results):
    return [{"seed": s["seed"], "roles": {
        role: {"normal": pair["arms"]["normal"]["evaluation"]["mates"],
               "fixed": pair["arms"]["fixed"]["evaluation"]["mates"],
               "fixed_minus_normal": pair["arms"]["fixed"]["evaluation"]["mates"]
                                     - pair["arms"]["normal"]["evaluation"]["mates"]}
        for role, pair in s["pairs"].items()}} for s in results]


def run(args):
    if (not args.seeds or len(set(args.seeds)) != len(args.seeds)
            or min(args.workers, args.wall_seconds, args.recovery) < 1):
        raise ValueError("positive budgets and unique seeds required")
    actor = prior.prior.DevelopmentConfig(max_conditions=args.conditions)
    shadow = prior.prior.residual_shadow.ShadowConfig(candidates=args.candidates,
                         discovery_episodes=args.discovery, min_support=args.min_support)
    trial = prior.prior.mechanism.TrialConfig("ranked", args.after_episode)
    use = prior.mechanism.UsefulnessConfig(args.window, args.probability)
    if trial.after_episode <= shadow.discovery_episodes:
        raise ValueError("attachment requires a prospective interval")
    fens, train_hash = load_split(args.pool, "train")
    validation, validation_hash = load_split(args.pool, "validation")
    if not fens or not validation:
        raise ValueError("nonempty pools required")
    train_orbits = {orbit_key(chess.Board(fen)) for fen in fens}
    validation_orbits = {orbit_key(chess.Board(fen)) for fen in validation}
    if train_orbits & validation_orbits:
        raise ValueError("training and validation symmetry orbits overlap")
    stop = args.after_episode + args.window
    plans = {str(seed): {"actor_config": asdict(actor), "shadow_config": asdict(shadow),
                        "usefulness_config": asdict(use), "after_episode": args.after_episode,
                        "recovery_after": stop, "recovery_episodes": args.recovery,
                        "order": prior.schedule_indices(len(fens), stop + args.recovery, seed),
                        "definitions": [asdict(d) for d in prior.prior.residual_shadow.random_definitions(
                            SCHEMA, seed=seed, count=args.candidates)]} for seed in args.seeds}
    modules = {"use_experiment": prior, "trial_usefulness": prior.mechanism,
               "live_trial": prior.prior.mechanism, "residual_shadow": prior.prior.residual_shadow,
               "prior_experiment": prior.prior, "shadow_experiment": prior.prior.shadow_experiment,
               "shared_helpers": prior.prior.mate_one_attribution}
    source = {"runtime": source_identity(), "runner_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}
    source.update({f"{name}_sha256": hashlib.sha256(Path(module.__file__).read_bytes()).hexdigest()
                   for name, module in modules.items()})
    manifest = {"schema": "fixed_topology_recovery.v1", "seeds": args.seeds, "roles": prior.ARMS,
                "modes": MODES, "plans": plans, "source": source,
                "workers": args.workers, "wall_seconds_per_seed": args.wall_seconds,
                "train_sha256": train_hash, "validation_sha256": validation_hash,
                "train_count": len(fens), "validation_count": len(validation),
                "train_orbits": len(train_orbits), "validation_orbits": len(validation_orbits),
                "training_moves": len(args.seeds) * 5 * (stop + 2 * args.recovery),
                "validation_moves_including_ablations": len(args.seeds) * 18 * len(validation),
                "experience_per_final_actor": stop + args.recovery,
                "final_test_opened": False, "validation_is_development": True,
                "limits": ["Shared prefixes are played once and cloned; copied history is not new experience.",
                           "Both recovery modes use separate matching exploration RNGs; compare these contemporaneous modes.",
                           "Old mixed-RNG final scores are historical references, not the primary control.",
                           "Fixed shared definitions still permit replicas for newly encountered legal bindings.",
                           "The intervention holds birth and pruning jointly; it does not separate their effects.",
                           "Holding topology is a laboratory control, not a default learner or causal maturity policy."]}
    args.output.mkdir(parents=True, exist_ok=False)
    save(args.output / "manifest.json", manifest)
    tasks = [(seed, plans[str(seed)], fens, validation, args.wall_seconds,
              str(args.output / f"seed-{seed}.json")) for seed in args.seeds]
    try:
        if args.workers == 1:
            results = [run_seed(t) for t in tasks]
        else:
            with ProcessPoolExecutor(max_workers=min(args.workers, len(tasks)),
                                     mp_context=multiprocessing.get_context("spawn")) as executor:
                results = list(executor.map(run_seed, tasks))
        result = {"status": "complete", "manifest_digest": digest(manifest),
                  "comparisons": summarize(results), "results": results}
        save(args.output / "summary.json", result)
    except Exception as error:
        save(args.output / "failure.json", {"status": "incomplete", "error": str(error)})
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
    parser.add_argument("--window", type=int, default=128)
    parser.add_argument("--recovery", type=int, default=128)
    parser.add_argument("--probability", type=float, default=0.5)
    parser.add_argument("--min-support", type=int, default=4)
    parser.add_argument("--workers", type=int, default=1)
    parser.add_argument("--wall-seconds", type=int, default=2400)
    print(json.dumps(run(parser.parse_args())["comparisons"], indent=2))


if __name__ == "__main__":
    main()
