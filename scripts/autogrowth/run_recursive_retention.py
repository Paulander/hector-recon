"""Fixed A -> mostly B -> mostly A lab; no changes to the recursive learner.

Completed blocks are write-once journals bound to their saved actors. No resume
or retry path exists. A partial block is evidence of unfinished work, not success.
"""
from dataclasses import replace
import argparse
import gzip
import hashlib
import json
import math
import os
from pathlib import Path
import pickle
import random
import resource
import signal
import sys
import time

from run_recursive_context import (
    BooleanEnvironment, ROWS, ROOT, summarize_actor,
    Feedback, DevelopmentConfig, RecursiveConfig, RecursiveDevelopment,
)
from recon_lite.graph import LinkType, NodeType

SEEDS = (4, 5, 6)
ROLES = ("flat", "random", "ranked")


def digest(data):
    return hashlib.sha256(data).hexdigest()


def encoded(value):
    return (json.dumps(value, sort_keys=True, default=repr) + "\n").encode()


def sync_directory(path):
    fd = os.open(path, os.O_RDONLY | os.O_DIRECTORY)
    try:
        os.fsync(fd)
    finally:
        os.close(fd)


def write_once(path, data):
    """Exclusive creation: an existing payload is never replaced."""
    with path.open("xb") as stream:
        stream.write(data)
        stream.flush()
        os.fsync(stream.fileno())
    sync_directory(path.parent)
    return digest(data)


def json_once(path, value):
    return write_once(path, encoded(value))


def save_actor(actor, path):
    return write_once(path, gzip.compress(pickle.dumps(actor, protocol=5), mtime=0))


def load_actor(path):
    actor = pickle.loads(gzip.decompress(path.read_bytes()))
    assert not actor.pending and actor.context_pending is None
    if actor.schema is not None:
        actor.graph.validate_formal_pairs()
    for nid, node in actor.graph.nodes.items():
        if node.ntype == NodeType.TERMINAL:
            assert not actor.graph.children(nid)
        elif node.meta.get("recursive_expression") or nid.startswith("gate:"):
            assert len(actor.graph.all_parents(nid)) == 1
    for cid, condition in actor.conditions.items():
        for slot in range(actor.slots):
            assert actor.graph.edge_by_key[(f"gate:{slot}:{cid}", f"option:{slot}", LinkType.SUR)].w is condition.weight
    assert len({id(c.weight) for c in actor.conditions.values()}) == len(actor.conditions)
    return actor


def schedule(seed):
    rng = random.Random(f"recursive-retention:{seed}")
    a = [i for i, row in enumerate(ROWS) if not row[2]]
    b = [i for i, row in enumerate(ROWS) if row[2]]
    prefix = a * 32
    rng.shuffle(prefix)
    continuation = []
    for block in range(6):
        unit = a * 2 + b * 14 if block < 3 else a * 14 + b * 2
        rng.shuffle(unit)
        continuation.extend(unit)
    return prefix, continuation


def verify_fork(parent, child, role):
    assert child.config == replace(parent.config, max_conditions=24)
    assert child.recursive_config == replace(parent.recursive_config, role=role)
    excluded = {"config", "recursive_config", "graph", "rng", "proposal_rng", "exploration_rng"}
    assert vars(parent).keys() == vars(child).keys()
    for name in vars(parent).keys() - excluded:
        assert getattr(parent, name) == getattr(child, name), name
    for name in ("rng", "proposal_rng", "exploration_rng"):
        assert getattr(parent, name).getstate() == getattr(child, name).getstate()
    def edges(actor):
        return [(e.src, e.dst, e.ltype, float(e.w)) for e in actor.graph.edges]
    assert edges(parent) == edges(child)


def evaluate(saved_actor):
    # Evaluation always uses a disposable clone. The training actor cannot change.
    actor = pickle.loads(pickle.dumps(saved_actor, protocol=5))
    rows = []
    for index, row in enumerate(ROWS):
        env = BooleanEnvironment(row)
        action = actor.act(env, event_id=-1, learn=False)
        rows.append({"row": index, "context": int(row[2]), "action": action,
                     "reward": env.outcome()})
    return {"episode": saved_actor.completed,
            "correct": sum(r["reward"] > 0 for r in rows),
            "context_correct": [sum(r["reward"] > 0 and r["context"] == c for r in rows) for c in (0, 1)],
            "rows": rows}


def train_block(actor, order, directory, previous_hash, *, do_evaluate=True):
    start = actor.completed
    directory.mkdir()
    json_once(directory / "intent.json", {"start": start, "stop": start + len(order),
              "order": list(order), "previous_checkpoint_sha256": previous_hash,
              "evaluate": do_evaluate})
    records = []
    # Keep the growing crash breadcrumb permanently. Completed evidence is a
    # separate write-once copy; it never depends on unlink/rename visibility.
    with (directory / "progress.jsonl").open("xb") as stream:
        for row in order:
            event = actor.completed
            env = BooleanEnvironment(ROWS[row])
            action = actor.act(env, event_id=event, learn=True)
            reward = env.outcome()
            _, _, prediction, active = actor.pending[-1]
            weights = [actor.conditions[cid].weight for cid in active]
            before = [float(w) for w in weights]
            contexts = None if actor.context_pending is None else actor.context_pending[3]
            actor.observe(Feedback(event, action, reward))
            record = {"event": event, "row": row, "action": action, "reward": reward,
                      "prediction": prediction, "active": active, "contexts": contexts,
                      "weights_before": before, "weights_after": [float(w) for w in weights]}
            records.append(encoded(record))
            stream.write(records[-1])
            stream.flush()
            os.fsync(stream.fileno())
    write_once(directory / "training.jsonl", b"".join(records))
    checkpoint_hash = save_actor(actor, directory / "checkpoint.pkl.gz")
    restored = load_actor(directory / "checkpoint.pkl.gz")
    assert restored.completed == start + len(order)
    evaluation = evaluate(restored) if do_evaluate else None
    if evaluation is not None:
        json_once(directory / "evaluation.json", evaluation)
    files = ["intent.json", "training.jsonl", "checkpoint.pkl.gz"]
    if evaluation is not None:
        files.append("evaluation.json")
    manifest = {"start": start, "stop": restored.completed,
                "training_records": len(order), "evaluation_records": 16 if do_evaluate else 0,
                "files": {name: digest((directory / name).read_bytes()) for name in files}}
    json_once(directory / "complete.json", manifest)
    verify_block(directory, order, start, previous_hash)
    return restored, checkpoint_hash, evaluation


def verify_block(directory, order, start, previous_hash):
    manifest = json.loads((directory / "complete.json").read_text())
    assert not list(directory.glob("*.partial*")), "unsealed journal"
    for name, expected in manifest["files"].items():
        assert digest((directory / name).read_bytes()) == expected, f"hash mismatch: {name}"
    assert (directory / "training.jsonl").read_bytes().startswith((directory / "progress.jsonl").read_bytes()), "contradictory progress copy"
    intent = json.loads((directory / "intent.json").read_text())
    assert intent["previous_checkpoint_sha256"] == previous_hash
    assert intent["order"] == list(order)
    assert manifest["start"] == intent["start"] == start
    assert manifest["stop"] == intent["stop"] == start + len(order)
    records = [json.loads(line) for line in (directory / "training.jsonl").read_text().splitlines()]
    assert len(records) == manifest["training_records"] == len(order)
    for event, row, record in zip(range(start, start + len(order)), order, records):
        assert (record["event"], record["row"]) == (event, row)
        assert record["action"] in ("act-a", "act-b")
        x, y, z, _ = ROWS[row]
        assert record["reward"] == (1 if (record["action"] == "act-b") == (y if z else x) else -1)
        delta = .3 * (record["reward"] - record["prediction"]) / (1 + len(record["active"]))
        assert len(record["weights_before"]) == len(record["weights_after"]) == len(record["active"])
        assert all(math.isclose(after - before, delta, abs_tol=2e-12)
                   for before, after in zip(record["weights_before"], record["weights_after"]))
    actor = load_actor(directory / "checkpoint.pkl.gz")
    assert actor.completed == start + len(order)
    assert manifest["evaluation_records"] == (16 if intent["evaluate"] else 0)
    if intent["evaluate"]:
        evaluation = json.loads((directory / "evaluation.json").read_text())
        assert evaluation["episode"] == actor.completed
        assert [r["row"] for r in evaluation["rows"]] == list(range(16))
    return manifest


def verify_run(out, *, re_evaluate=False):
    counts = {"training": 0, "evaluation": 0, "checkpoints": 0, "blocks": 0,
              "verification_actions": 0}
    for relative, expected in json.loads((out / "source.json").read_text()).items():
        assert digest((ROOT / relative).read_bytes()) == expected, relative
    for seed in SEEDS:
        prefix, continuation = schedule(seed)
        assert json.loads((out / f"seed-{seed}" / "schedule.json").read_text()) == {
            "prefix": prefix, "continuation": continuation}
        pair_digests = []
        for role in ("prefix", *ROLES):
            directory = out / f"seed-{seed}" / role
            start_path = directory / "start.pkl.gz"
            start_hash = digest(start_path.read_bytes())
            start_record = json.loads((directory / "start.json").read_text())
            assert start_record["sha256"] == start_hash
            actor = load_actor(start_path)
            assert actor.completed == (0 if role == "prefix" else 256)
            if role != "prefix":
                parent_path = out / f"seed-{seed}/prefix/block-000128/checkpoint.pkl.gz"
                assert start_record["source_prefix_checkpoint_sha256"] == digest(parent_path.read_bytes())
                verify_fork(load_actor(parent_path), actor, role)
            counts["checkpoints"] += 1
            order = prefix if role == "prefix" else continuation
            start = actor.completed
            expected_dirs = []
            for offset in range(0, len(order), 128):
                block = directory / f"block-{start + offset:06d}"
                expected_dirs.append(block.name)
                manifest = verify_block(block, order[offset:offset + 128], start + offset, start_hash)
                counts["training"] += manifest["training_records"]
                counts["evaluation"] += manifest["evaluation_records"]
                counts["checkpoints"] += 1
                counts["blocks"] += 1
                start_hash = manifest["files"]["checkpoint.pkl.gz"]
                actor = load_actor(block / "checkpoint.pkl.gz")
                if re_evaluate and manifest["evaluation_records"]:
                    assert evaluate(actor) == json.loads((block / "evaluation.json").read_text())
                    counts["verification_actions"] += 16
            assert sorted(p.name for p in directory.glob("block-*")) == expected_dirs
            if role != "prefix":
                pair_digests.append(summarize_actor(actor)["exploration_rng_digest"])
        assert len(set(pair_digests)) == 1, "paired exploration draws diverged"
    assert not list(out.rglob("*.partial*"))
    assert counts["training"] == 7680 and counts["evaluation"] == 912
    assert counts["blocks"] == 60 and counts["checkpoints"] == 72
    return counts


def run(out, wall_seconds):
    out.mkdir(parents=True, exist_ok=False)
    start = time.monotonic()
    os.sched_setaffinity(0, {min(os.sched_getaffinity(0))})
    resource.setrlimit(resource.RLIMIT_AS, (2 * 1024**3, 2 * 1024**3))
    resource.setrlimit(resource.RLIMIT_FSIZE, (64 * 1024**2, 64 * 1024**2))
    def expired(_sig, _frame):
        raise TimeoutError("fixed whole-run wall limit reached")
    signal.signal(signal.SIGALRM, expired)
    signal.alarm(wall_seconds)
    report = {"status": "running", "seeds": SEEDS, "arms": [],
              "planned_training": 7680, "planned_evaluation": 912,
              "wall_cap_seconds": wall_seconds, "address_space_cap_gib": 2, "cpu_cores": 1}
    json_once(out / "protocol.json", report)
    paths = {Path(__file__).resolve(), ROOT / "docs/autogrowth/RECURSIVE_RETENTION.md",
             ROOT / "docs/autogrowth/RECURSIVE_RETENTION_RECORDER_CORRECTION.md"}
    paths.update(Path(m.__file__).resolve() for m in tuple(sys.modules.values())
                 if getattr(m, "__file__", None) and Path(m.__file__).suffix == ".py"
                 and Path(m.__file__).resolve().is_relative_to(ROOT))
    json_once(out / "source.json", {p.relative_to(ROOT).as_posix(): digest(p.read_bytes()) for p in sorted(paths)})
    try:
        for seed in SEEDS:
            prefix, continuation = schedule(seed)
            seed_dir = out / f"seed-{seed}"
            seed_dir.mkdir()
            json_once(seed_dir / "schedule.json", {"prefix": prefix, "continuation": continuation})
            actor = RecursiveDevelopment(seed=seed, config=DevelopmentConfig(max_conditions=16),
                                         recursive_config=RecursiveConfig(role="flat"))
            directory = seed_dir / "prefix"
            directory.mkdir()
            previous = save_actor(actor, directory / "start.pkl.gz")
            json_once(directory / "start.json", {"sha256": previous})
            for offset in (0, 128):
                actor, previous, initial = train_block(actor, prefix[offset:offset + 128],
                    directory / f"block-{offset:06d}", previous, do_evaluate=offset == 128)
            print(json.dumps({"seed": seed, "role": "prefix", "episode": 256,
                              "contexts": initial["context_correct"]}), flush=True)
            for role in ROLES:
                child = pickle.loads(pickle.dumps(actor, protocol=5))
                child.config = replace(child.config, max_conditions=24)
                child.recursive_config = replace(child.recursive_config, role=role)
                verify_fork(actor, child, role)
                directory = seed_dir / role
                directory.mkdir()
                previous = save_actor(child, directory / "start.pkl.gz")
                json_once(directory / "start.json", {"sha256": previous,
                          "source_prefix_checkpoint_sha256": digest((seed_dir / "prefix/block-000128/checkpoint.pkl.gz").read_bytes())})
                arm = {"seed": seed, "role": role, "initial": initial, "evaluations": [], "structures": []}
                report["arms"].append(arm)
                for offset in range(0, 768, 128):
                    child, previous, result = train_block(child, continuation[offset:offset + 128],
                        directory / f"block-{256 + offset:06d}", previous)
                    arm["evaluations"].append(result)
                    arm["structures"].append(summarize_actor(child))
                    print(json.dumps({"seed": seed, "role": role, "episode": child.completed,
                                      "contexts": result["context_correct"], "splits": len(child.splits),
                                      "elapsed_seconds": round(time.monotonic() - start, 1)}), flush=True)
                json_once(directory / "results.json", arm)
        report["verification"] = verify_run(out)
        report["status"] = "complete"
    except BaseException as error:
        report.update(status="incomplete", error=f"{type(error).__name__}: {error}")
        raise
    finally:
        signal.alarm(0)
        report["elapsed_seconds"] = time.monotonic() - start
        report["max_rss_kib"] = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
        json_once(out / "result.json", report)
    return report


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--wall-seconds", type=int, default=600)
    parser.add_argument("--verify", action="store_true")
    args = parser.parse_args()
    if not 1 <= args.wall_seconds <= 600:
        parser.error("wall limit must be 1..600 seconds")
    if args.verify:
        # Separate, bounded read-only verification; never resumes training.
        os.sched_setaffinity(0, {min(os.sched_getaffinity(0))})
        resource.setrlimit(resource.RLIMIT_AS, (2 * 1024**3, 2 * 1024**3))
        signal.alarm(min(args.wall_seconds, 120))
        print(json.dumps(verify_run(args.output, re_evaluate=True)), flush=True)
    else:
        run(args.output, args.wall_seconds)
