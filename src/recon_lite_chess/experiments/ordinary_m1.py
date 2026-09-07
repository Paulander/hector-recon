"""Fixed-endpoint ordinary M1 experience, with private resumable checkpoints.

No new learner policy. Only trusted checkpoints created by this runner may be
loaded. Checkpoint boundaries and evaluations depend on the declared schedule.
"""
import argparse
from concurrent.futures import ProcessPoolExecutor
import copy
import gzip
import hashlib
import json
import multiprocessing
import os
from pathlib import Path
import pickle
import time
import uuid

import chess

from recon_lite_chess.coach.pools import load_split, orbit_key
from recon_lite_chess.coach.runner import source_identity
from . import fixed_topology_recovery as prior

ROLES = ("none", "ranked", "random")
train = prior.train  # The unchanged opaque coach.
digest = prior.digest


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def read(path):
    return json.loads(Path(path).read_text())


def atomic_json(path, value):
    path = Path(path)
    temporary = path.with_name(path.name + ".tmp")
    with temporary.open("w") as stream:
        json.dump(value, stream, indent=2)
        stream.write("\n")
        stream.flush()
        os.fsync(stream.fileno())
    temporary.replace(path)


def sources():
    old = prior.prior
    modules = {"fixed_recovery": prior, "use_experiment": old,
               "trial_usefulness": old.mechanism, "live_trial": old.prior.mechanism,
               "residual_shadow": old.prior.residual_shadow, "prior_experiment": old.prior,
               "shadow_experiment": old.prior.shadow_experiment,
               "shared_helpers": old.prior.mate_one_attribution}
    return json.loads(json.dumps({"runtime": source_identity(), "runner_sha256": sha(__file__),
            "modules": {name: sha(module.__file__) for name, module in modules.items()}}))


def actor_digest(o):
    return digest((prior.prior.prior.learned_digest(o), prior.control_digest(o)))


def save_checkpoint(directory, state, manifest):
    """Immutable payload first, atomic pointer second; preserve older boundaries."""
    o = state["organism"]
    if o is not None and (o.pending or o.completed != state["next_event"]):
        raise RuntimeError("checkpoint needs completed action-bound feedback")
    name = f"checkpoint-{state['role_index']}-{state['next_event']:06d}-{uuid.uuid4().hex[:8]}.pkl.gz"
    path = directory / name
    temporary = path.with_suffix(".tmp")
    with temporary.open("wb") as raw:
        with gzip.GzipFile(filename="", mode="wb", fileobj=raw, compresslevel=1, mtime=0) as stream:
            pickle.dump({"manifest_digest": digest(manifest), "source": manifest["source"],
                         "state": state}, stream, protocol=pickle.HIGHEST_PROTOCOL)
        raw.flush()
        os.fsync(raw.fileno())
    temporary.replace(path)
    pointer = {"schema": "ordinary_m1.checkpoint.v1", "file": name, "sha256": sha(path),
               "manifest_digest": digest(manifest), "source": manifest["source"],
               "seed": state["seed"], "role_index": state["role_index"],
               "next_event": state["next_event"],
               "actor_digest": None if o is None else actor_digest(o)}
    atomic_json(directory / "latest.json", pointer)
    return pointer


def load_checkpoint(directory, manifest, seed):
    pointer = read(directory / "latest.json")
    if (pointer["schema"] != "ordinary_m1.checkpoint.v1"
            or pointer["manifest_digest"] != digest(manifest)
            or pointer["source"] != sources() or pointer["source"] != manifest["source"]):
        raise ValueError("checkpoint source/runtime or experiment differs")
    name = pointer["file"]
    if Path(name).name != name or pointer["seed"] != seed:
        raise ValueError("checkpoint path or seed differs")
    path = directory / name
    if sha(path) != pointer["sha256"]:
        raise ValueError("checkpoint transport hash mismatch")
    with gzip.open(path, "rb") as stream:
        payload = pickle.load(stream)
    state = payload["state"]
    if payload["manifest_digest"] != digest(manifest) or payload["source"] != manifest["source"]:
        raise ValueError("checkpoint payload identity differs")
    o = state["organism"]
    if (state["seed"] != seed or state["role_index"] != pointer["role_index"]
            or state["next_event"] != pointer["next_event"]
            or (o is not None and (o.pending or o.completed != state["next_event"]
                                  or actor_digest(o) != pointer["actor_digest"] or o.hold_topology))):
        raise ValueError("checkpoint progress or actor differs")
    return state


def new_actor(seed, role, spec):
    return prior.RecoveryTrial(seed=seed, recovery_after=spec["recovery_after"],
        config=prior.prior.prior.DevelopmentConfig(**spec["actor_config"]),
        shadow_config=prior.prior.prior.residual_shadow.ShadowConfig(**spec["shadow_config"]),
        trial_config=prior.prior.prior.mechanism.TrialConfig(role, spec["after_episode"]))


def snapshot(o):
    return {"learned_digest": prior.prior.prior.learned_digest(o),
            "control_digest": prior.control_digest(o), "lifecycle": prior.prior.lifecycle(o),
            "live_counts": dict(o.live_counts), "decision": dict(o.trial_decision),
            "shadow_history_digest": digest(o.shadow.report()),
            "exploration_rng_digest": digest(o.recovery_rng.getstate()),
            "structure": {"physical_vertices": len(o.graph.nodes), "physical_edges": len(o.graph.edges)}}


def evaluate(o, validation, *, role, deadline):
    before = actor_digest(o)
    report, actions = prior.evaluate(o, validation, deadline=deadline)
    result = {"evaluation": report}
    if role != "none":
        result["ablation"] = prior.prior.ablation(o, validation, report, actions, deadline=deadline)
    if actor_digest(o) != before:
        raise RuntimeError("evaluation changed learned state")
    return snapshot(o) | result


def verify_anchor(state, reference):
    """Offline reproducibility gate; no answer or score is supplied to the actor."""
    blocks = state["blocks"]
    for block, key in zip(blocks[:3], ("prefix_training", "suffix_training", "recovery_training")):
        expected = reference[key] if key != "recovery_training" else reference["arms"]["normal"][key]
        if block["training"] != expected:
            raise RuntimeError("historical action/outcome anchor differs")
    current = state["milestones"][str(state["next_event"])]; old = reference["arms"]["normal"]
    for key in ("learned_digest", "control_digest", "evaluation", "ablation", "live_counts", "structure"):
        if current.get(key) != old.get(key):
            raise RuntimeError(f"historical anchor differs: {key}")
    if (current["lifecycle"] != old["after_recovery"] or current["decision"] != reference["decision"]
            or current["shadow_history_digest"] != reference["shadow_history_digest"]
            or state["boundary_digest"] != reference["before_recovery"]["learned_digest"]):
        raise RuntimeError("historical evidence anchor differs")


def publish_milestone(state, directory, output, role, event):
    atomic_json(output / f"seed-{state['seed']}-{role}-{event}.json",
                {"seed": state["seed"], "role": role, "event": event, "anchor_matches": True,
                 "result": state["milestones"][str(event)],
                 "checkpoint_sha256": read(directory / "latest.json")["sha256"]})


def run_seed(task):
    seed, manifest, fens, validation, references, private, output = task
    private, output = Path(private), Path(output)
    directory = private / f"seed-{seed}"
    directory.mkdir(exist_ok=True)
    lock = directory / "run.lock"
    try:
        lock.mkdir()
    except FileExistsError as error:
        raise RuntimeError("seed is locked; confirm its old process stopped before removing the lock") from error
    try:
        return _run_seed(seed, manifest, fens, validation, references, directory, output)
    finally:
        lock.rmdir()


def _run_seed(seed, manifest, fens, validation, references, directory, output):
    clock = directory / "budget.json"
    if not clock.exists():
        atomic_json(clock, {"deadline_utc": time.time() + manifest["wall_seconds_per_seed"],
                            "manifest_digest": digest(manifest)})
    budget = read(clock)
    if budget["manifest_digest"] != digest(manifest):
        raise ValueError("seed budget belongs to a different experiment")
    deadline = time.monotonic() + budget["deadline_utc"] - time.time()
    state = (load_checkpoint(directory, manifest, seed) if (directory / "latest.json").exists() else
             {"seed": seed, "role_index": 0, "next_event": 0, "organism": None,
              "blocks": [], "milestones": {}, "results": {}, "last_unit": None,
              "boundary_digest": None, "completed_utc": None})
    pending = directory / "pending.json"
    if pending.exists():
        interrupted = read(pending)
        interrupted["already_committed"] = state["last_unit"] == interrupted["id"]
        interrupted["extra_moves_upper_bound"] = 0 if interrupted["already_committed"] else interrupted["max_moves"]
        # Append immutable interruption evidence; never claim replayed moves vanish.
        atomic_json(output / f"interruption-{seed}-{uuid.uuid4().hex}.json", interrupted)
        if interrupted["already_committed"] and interrupted["kind"] == "evaluation":
            publish_milestone(state, directory, output, interrupted["role"], interrupted["event"])
        pending.unlink()
    spec = manifest["plans"][str(seed)]
    anchor, endpoint = manifest["anchor"], manifest["episodes"]
    while state["role_index"] < len(ROLES):
        if (output / "STOP").exists():
            save_checkpoint(directory, state, manifest)
            return {"seed": seed, "status": "paused"}
        if time.monotonic() >= deadline:
            raise TimeoutError("original seed time cap expired; resume does not reset it")
        role = ROLES[state["role_index"]]
        if state["organism"] is None:
            state["organism"] = new_actor(seed, role, spec)
            save_checkpoint(directory, state, manifest)
        o, event = state["organism"], state["next_event"]
        if event in (anchor, endpoint) and str(event) not in state["milestones"]:
            unit = {"id": f"{role}:evaluate:{event}", "kind": "evaluation", "role": role, "event": event,
                    "max_moves": len(validation) * (1 if role == "none" else 2)}
            atomic_json(pending, unit)
            state["milestones"][str(event)] = evaluate(o, validation, role=role, deadline=deadline)
            if event == anchor:
                verify_anchor(state, references[role])
            state["last_unit"] = unit["id"]
            save_checkpoint(directory, state, manifest)
            if event == anchor:
                restored = load_checkpoint(directory, manifest, seed)
                if actor_digest(restored["organism"]) != actor_digest(o):
                    raise RuntimeError("anchor checkpoint changed learned state")
                state = restored
            publish_milestone(state, directory, output, role, event)
            pending.unlink()
            print(json.dumps({"seed": seed, "role": role, "event": event,
                              "mates": state["milestones"][str(event)]["evaluation"]["mates"]}), flush=True)
        elif event == endpoint:
            state["results"][role] = {"blocks": state["blocks"], "milestones": state["milestones"], "anchor_matches": True}
            atomic_json(output / f"seed-{seed}-{role}.json", state["results"][role])
            state.update(role_index=state["role_index"] + 1, next_event=0, organism=None,
                         blocks=[], milestones={}, boundary_digest=None)
            if state["role_index"] == len(ROLES):
                state["completed_utc"] = time.time()
                if state["completed_utc"] >= budget["deadline_utc"]:
                    raise TimeoutError("seed completed after its original time cap")
            save_checkpoint(directory, state, manifest)
        else:
            stop = next((b for b in (spec["after_episode"], spec["recovery_after"], anchor) if event < b),
                        min(endpoint, event + manifest["continuation_block"]))
            unit = {"id": f"{role}:train:{event}:{stop}", "kind": "training", "max_moves": stop-event}
            atomic_json(pending, unit)
            result = train(o, fens, spec["order"][event:stop], start_event=event, deadline=deadline)
            state["blocks"].append({"start": event, "end": stop, "training": result})
            state["next_event"] = stop
            if stop == spec["recovery_after"]:
                state["boundary_digest"] = prior.prior.prior.learned_digest(o)
            if stop > spec["after_episode"] and digest(o.shadow.report()) != references[role]["shadow_history_digest"]:
                raise RuntimeError("frozen hypothesis history changed")
            state["last_unit"] = unit["id"]
            save_checkpoint(directory, state, manifest)
            pending.unlink()
            print(json.dumps({"seed": seed, "role": role, "training_completed": stop}), flush=True)
    if state["completed_utc"] is None or state["completed_utc"] >= budget["deadline_utc"]:
        raise TimeoutError("seed has no completion within its original time cap")
    result = {"seed": seed, "status": "complete", "roles": state["results"],
              "wall_seconds": round(state["completed_utc"] - budget["deadline_utc"] + manifest["wall_seconds_per_seed"], 3)}
    atomic_json(output / f"seed-{seed}.json", result)
    return result


def run(args):
    if (not args.seeds or len(set(args.seeds)) != len(args.seeds)
            or min(args.workers, args.wall_seconds, args.continuation_block) < 1):
        raise ValueError("positive budgets and unique seeds required")
    reference = read(args.reference)
    if reference["status"] != "complete":
        raise ValueError("complete historical reference required")
    old, source = reference["manifest"], sources()
    if source["runtime"] != old["source"]["runtime"] or source["modules"]["fixed_recovery"] != old["source"]["runner_sha256"]:
        raise ValueError("historical runtime or recovery implementation differs")
    for name, value in source["modules"].items():
        if name != "fixed_recovery" and value != old["source"][name + "_sha256"]:
            raise ValueError("historical dependency differs")
    anchor = old["experience_per_final_actor"]
    if args.episodes <= anchor:
        raise ValueError("endpoint must exceed historical anchor")
    fens, train_hash = load_split(args.pool, "train")
    validation, validation_hash = load_split(args.pool, "validation")
    if (train_hash, validation_hash) != (old["train_sha256"], old["validation_sha256"]):
        raise ValueError("historical pools differ")
    if not fens or not validation or {orbit_key(chess.Board(f)) for f in fens} & {orbit_key(chess.Board(f)) for f in validation}:
        raise ValueError("nonempty disjoint symmetry orbits required")
    plans, references = {}, {s["seed"]: s["roles"] for s in reference["results"]}
    for seed in args.seeds:
        spec = copy.deepcopy(old["plans"][str(seed)])
        order = list(prior.prior.schedule_indices(len(fens), args.episodes, seed))
        if order[:anchor] != spec["order"]:
            raise ValueError("historical schedule differs")
        spec["order"] = order
        plans[str(seed)] = spec
    manifest = {"schema": "ordinary_m1.v1", "seeds": args.seeds, "roles": ROLES,
                "plans": plans, "source": source, "reference_sha256": sha(args.reference),
                "anchor": anchor, "anchor_checkpoint_reload": True,
                "episodes": args.episodes, "continuation_block": args.continuation_block,
                "workers": args.workers, "wall_seconds_per_seed": args.wall_seconds,
                "train_sha256": train_hash, "validation_sha256": validation_hash,
                "training_moves": len(args.seeds) * len(ROLES) * args.episodes,
                "validation_moves": len(args.seeds) * 6 * len(validation),
                "ablation_moves": len(args.seeds) * 4 * len(validation),
                "final_test_opened": False, "validation_is_development": True,
                "limits": ["Always-enabled roles only; unchanged reward, features, credit and lifecycle.",
                           "Private checkpoints contain trained state; only aggregate results/hashes are public.",
                           "Original absolute seed deadline persists across resume; downtime counts.",
                           "Interrupted uncommitted units may replay; extra moves are reported as bounded uncertainty.",
                           "Fixed endpoints only; no best-checkpoint selection or automatic retries."]}
    # Normalize JSON tuples before comparisons across fresh processes.
    manifest = json.loads(json.dumps(manifest))
    if args.resume:
        if (read(args.output / "manifest.json") != manifest or not args.private.is_dir()
                or read(args.private / "manifest.json") != {"manifest_digest": digest(manifest)}):
            raise ValueError("resume protocol/source or private directory differs")
    else:
        args.output.mkdir(parents=True, exist_ok=False)
        args.private.mkdir(parents=True, exist_ok=False, mode=0o700)
        atomic_json(args.output / "manifest.json", manifest)
        atomic_json(args.private / "manifest.json", {"manifest_digest": digest(manifest)})
    if (args.output / "summary.json").exists():
        raise FileExistsError("experiment already complete")
    tasks = [(seed, manifest, fens, validation, references[seed], str(args.private), str(args.output)) for seed in args.seeds]
    try:
        if args.workers == 1:
            results = [run_seed(t) for t in tasks]
        else:
            with ProcessPoolExecutor(max_workers=min(args.workers, len(tasks)), mp_context=multiprocessing.get_context("spawn")) as executor:
                results = list(executor.map(run_seed, tasks))
        if any(r["status"] != "complete" for r in results):
            return {"status": "paused", "results": results}
        interruptions = [read(p) for p in sorted(args.output.glob("interruption-*.json"))]
        nominal = sum(manifest[k] for k in ("training_moves", "validation_moves", "ablation_moves"))
        result = {"status": "complete", "manifest_digest": digest(manifest), "results": results,
                  "interruptions": interruptions, "actual_moves_lower_bound": nominal,
                  "actual_moves_upper_bound": nominal + sum(r["extra_moves_upper_bound"] for r in interruptions)}
        atomic_json(args.output / "summary.json", result)
    except Exception as error:
        atomic_json(args.output / f"failure-{uuid.uuid4().hex}.json", {"status": "incomplete", "error": str(error)})
        raise
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("pool", "reference", "output", "private"):
        parser.add_argument("--" + name, type=Path, required=True)
    parser.add_argument("--seeds", nargs="+", type=int, default=[1, 2, 3])
    parser.add_argument("--episodes", type=int, default=1024)
    parser.add_argument("--continuation-block", type=int, default=128)
    parser.add_argument("--workers", type=int, default=3)
    parser.add_argument("--wall-seconds", type=int, default=3000)
    parser.add_argument("--resume", action="store_true")
    result = run(parser.parse_args())
    print(json.dumps({"status": result["status"]}))


if __name__ == "__main__":
    main()
