"""Bounded non-chess lab. The actor receives measurements and actual reward only."""
from dataclasses import asdict, replace
import argparse
import gzip
import hashlib
import inspect
import itertools
import json
import os
from pathlib import Path
import pickle
import random
import resource
import signal
import sys
import time

from recon_lite_chess.coach.interface import Feedback
from recon_lite_hector.learning.terminal_development import Coordinate, DevelopmentConfig
from recon_lite_hector.learning.recursive_context import RecursiveConfig, RecursiveDevelopment

BOOL = (False, True)
ROWS = tuple(itertools.product(BOOL, repeat=4))
ROOT = Path(__file__).resolve().parents[2]


class BooleanEnvironment:
    schema = tuple(Coordinate(f"coordinate-{i}", BOOL) for i in range(5))

    def __init__(self, row):
        self._row = row
        self._executed = None

    def bindings(self):
        assert inspect.currentframe().f_back.f_code.co_name == "_catalog"
        return ("act-a", "act-b")

    def measure(self, coordinate, binding):
        assert inspect.currentframe().f_back.f_code.co_name == "_reader"
        return (*self._row, binding == "act-b")[coordinate]

    def execute(self, binding):
        assert inspect.currentframe().f_back.f_code.co_name == "_actuator"
        assert self._executed is None and binding in ("act-a", "act-b")
        self._executed = binding

    def outcome(self):
        # Environment-only task: choose x when z is false, y when z is true.
        # The fourth state bit is irrelevant. No phase/context label is sent.
        x, y, z, _noise = self._row
        assert self._executed is not None
        target = y if z else x
        return 1 if (self._executed == "act-b") == target else -1


def atomic_json(path, value):
    temp = path.with_suffix(path.suffix + ".tmp")
    temp.write_text(json.dumps(value, indent=2, default=repr) + "\n")
    temp.replace(path)


def checkpoint(actor, path):
    payload = pickle.dumps(actor, protocol=5)
    with gzip.open(path, "wb") as stream:
        stream.write(payload)
    restored = pickle.loads(payload)
    assert restored.completed == actor.completed
    assert restored.conditions == actor.conditions
    for cid, c in restored.conditions.items():
        from recon_lite.graph import LinkType
        for slot in range(restored.slots):
            assert restored.graph.edge_by_key[(f"gate:{slot}:{cid}", f"option:{slot}", LinkType.SUR)].w is c.weight
    return restored


def schedule(seed):
    rng = random.Random(f"recursive-lab:{seed}")
    first = [i for i, row in enumerate(ROWS) if not row[2]]
    second = [i for i, row in enumerate(ROWS) if row[2]]
    prefix = first * 32
    rng.shuffle(prefix)
    continuation = []
    for block in range(6):
        unit = first * 2 + second * 14 if block < 4 else list(range(16)) * 8
        rng.shuffle(unit)
        continuation.extend(unit)
    return prefix, continuation


def evaluate(actor, directory, counters):
    before = (actor.completed, actor.rng.getstate(), actor.proposal_rng.getstate(),
              actor.exploration_rng.getstate(), dict(actor.evidence))
    rows = []
    for index, row in enumerate(ROWS):
        atomic_json(directory / "pending.json", {"kind": "evaluation", "episode": actor.completed, "row": index})
        env = BooleanEnvironment(row)
        action = actor.act(env, event_id=-1, learn=False)
        reward = env.outcome()
        counters["evaluation"] += 1
        rows.append({"row": index, "context": int(row[2]), "action": action, "reward": reward})
    assert before == (actor.completed, actor.rng.getstate(), actor.proposal_rng.getstate(),
                      actor.exploration_rng.getstate(), actor.evidence)
    (directory / "pending.json").unlink()
    return {"episode": actor.completed, "correct": sum(r["reward"] > 0 for r in rows),
            "context_correct": [sum(r["reward"] > 0 and r["context"] == c for r in rows) for c in (0, 1)],
            "rows": rows}


def train(actor, order, directory, counters):
    with (directory / "training-actions.jsonl").open("a") as stream:
        for index in order:
            event = actor.completed
            atomic_json(directory / "pending.json", {"kind": "training", "event": event, "row": index})
            env = BooleanEnvironment(ROWS[index])
            action = actor.act(env, event_id=event, learn=True)
            reward = env.outcome()
            actor.observe(Feedback(event, action, reward))
            stream.write(json.dumps({"event": event, "row": index, "action": action, "reward": reward}) + "\n")
            stream.flush()
            counters["training"] += 1
            (directory / "pending.json").unlink()


def summarize_actor(actor):
    return {"weighted_contributions": len(actor.conditions),
            "expression_definitions": len(actor.expression_ids),
            "physical_nodes": len(actor.graph.nodes), "pruned": actor.pruned,
            "max_depth": max((actor.expressions[cid].depth for cid in actor.conditions), default=0),
            "max_generation": max((actor.generation[cid] for cid in actor.conditions), default=0),
            "splits": actor.splits,
            "exploration_rng_digest": hashlib.sha256(repr(actor.exploration_rng.getstate()).encode()).hexdigest()}


def run(args):
    out = Path(args.output)
    out.mkdir(parents=True, exist_ok=False)
    started = time.monotonic()
    counters = {"training": 0, "evaluation": 0}
    report = {"status": "running", "seeds": [1, 2, 3], "arms": [], "counters": counters,
              "planned_training": 7680, "planned_evaluation": 912, "wall_seconds": args.wall_seconds}
    if hasattr(os, "sched_getaffinity"):
        os.sched_setaffinity(0, {min(os.sched_getaffinity(0))})
    resource.setrlimit(resource.RLIMIT_AS, (2 * 1024**3, 2 * 1024**3))
    def expired(_sig, _frame):
        raise TimeoutError("fixed whole-run wall limit reached")
    signal.signal(signal.SIGALRM, expired)
    signal.alarm(args.wall_seconds)
    atomic_json(out / "status.json", report)
    source_files = [Path(__file__).resolve(), ROOT / "src/recon_lite_hector/learning/recursive_context.py",
                    ROOT / "src/recon_lite_hector/learning/terminal_development.py",
                    ROOT / "src/recon_lite_hector/nodes/stem_cell.py",
                    ROOT / "src/recon_lite_chess/coach/interface.py"]
    # Bind actual imported repository dependencies, not unrelated old experiments.
    source_files.extend(Path(m.__file__).resolve() for m in tuple(sys.modules.values())
                        if getattr(m, "__file__", None)
                        and Path(m.__file__).resolve().is_relative_to(ROOT)
                        and Path(m.__file__).suffix == ".py")
    atomic_json(out / "source.json", {p.relative_to(ROOT).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
                                     for p in sorted(set(source_files))})
    try:
        for seed in report["seeds"]:
            prefix, continuation = schedule(seed)
            prefix_dir = out / f"seed-{seed}" / "prefix"
            prefix_dir.mkdir(parents=True)
            actor = RecursiveDevelopment(seed=seed, config=DevelopmentConfig(max_conditions=16),
                                         recursive_config=RecursiveConfig(role="flat"))
            train(actor, prefix, prefix_dir, counters)
            initial = evaluate(actor, prefix_dir, counters)
            actor = checkpoint(actor, prefix_dir / "checkpoint-256.pkl.gz")
            atomic_json(prefix_dir / "evaluation.json", initial)
            for role in ("flat", "random", "ranked"):
                directory = out / f"seed-{seed}" / role
                directory.mkdir()
                child = pickle.loads(pickle.dumps(actor))
                child.config = replace(child.config, max_conditions=24)
                child.recursive_config = replace(child.recursive_config, role=role)
                arm = {"seed": seed, "role": role, "initial": initial, "evaluations": []}
                report["arms"].append(arm)
                for offset in range(0, 768, 128):
                    train(child, continuation[offset:offset + 128], directory, counters)
                    child = checkpoint(child, directory / f"checkpoint-{child.completed}.pkl.gz")
                    result = evaluate(child, directory, counters)
                    arm["evaluations"].append(result)
                    arm["structure"] = summarize_actor(child)
                    atomic_json(directory / "results.json", arm)
                    atomic_json(out / "status.json", report)
                    print(json.dumps({"seed": seed, "role": role, "episode": child.completed,
                                      "correct": result["correct"], "contexts": result["context_correct"],
                                      "splits": len(child.splits)}), flush=True)
            paired = report["arms"][-3:]
            assert len({a["structure"]["exploration_rng_digest"] for a in paired}) == 1
        assert counters == {"training": report["planned_training"], "evaluation": report["planned_evaluation"]}
        report["status"] = "complete"
    except BaseException as error:
        report.update(status="incomplete", error=f"{type(error).__name__}: {error}")
        raise
    finally:
        signal.alarm(0)
        report["elapsed_seconds"] = time.monotonic() - started
        report["max_rss_kib"] = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
        atomic_json(out / "status.json", report)
    return report


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", required=True)
    parser.add_argument("--wall-seconds", type=int, default=600)
    args = parser.parse_args()
    if not 1 <= args.wall_seconds <= 600:
        parser.error("whole-run wall limit must be 1..600 seconds")
    run(args)
