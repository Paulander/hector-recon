"""Fixed six/twelve split-budget comparison; unchanged learner and recorder."""
from dataclasses import replace
import argparse
import json
import os
from pathlib import Path
import pickle
import random
import resource
import signal
import sys
import time

import run_recursive_retention as lab

CAPS = (6, 12)
SOURCE_HASHES = {
    4: "3c834c402b63aea15034af96c5011ee8447a48d7b0b0d1c8e914a792e44152ec",
    5: "661efa100b6627fcd63b69b3d595915ba319f30bb808da9f62f5ef852cb0ee40",
    6: "8804a94c6d5229b6d5963925e867fcde77d8e1484e15ec72bed5b602fac0a78c",
}


def schedule(seed):
    rng = random.Random(f"recursive-budget:{seed}")
    a = [i for i, row in enumerate(lab.ROWS) if not row[2]]
    b = [i for i, row in enumerate(lab.ROWS) if row[2]]
    result = []
    for block in range(6):
        rows = a * 2 + b * 14 if block < 3 else a * 14 + b * 2
        rng.shuffle(rows)
        result.extend(rows)
    return result


def fork(parent, cap):
    assert cap in CAPS
    child = pickle.loads(pickle.dumps(parent, protocol=5))
    child.recursive_config = replace(child.recursive_config, max_splits=cap)
    verify_fork(parent, child, cap)
    return child


def verify_fork(parent, child, cap):
    assert child.recursive_config == replace(parent.recursive_config, max_splits=cap)
    # Sets can serialize in different orders after restoring equal contents.
    # Compare values, all graph indexes/metadata and RNG state; load_actor also
    # verifies the required weight aliases and distinct child weights.
    assert vars(parent).keys() == vars(child).keys()
    for name in vars(parent):
        if name == "recursive_config":
            continue
        left, right = getattr(parent, name), getattr(child, name)
        if name in ("rng", "proposal_rng", "exploration_rng"):
            left, right = left.getstate(), right.getstate()
        elif name == "graph":
            left, right = vars(left), vars(right)
        assert left == right, f"fork changed actor state: {name}"


def check_anchor(actor):
    assert actor.completed == 1024
    assert actor.config == lab.DevelopmentConfig(max_conditions=24)
    assert actor.recursive_config == lab.RecursiveConfig(role="ranked")


def saved_anchor(source, seed):
    directory = source / f"seed-{seed}/ranked/block-000896"
    path = directory / "checkpoint.pkl.gz"
    payload = path.read_bytes()
    manifest = json.loads((directory / "complete.json").read_text())
    assert lab.digest(payload) == SOURCE_HASHES[seed] == manifest["files"]["checkpoint.pkl.gz"]
    for relative, expected in json.loads((source / "source.json").read_text()).items():
        assert lab.digest((lab.ROOT / relative).read_bytes()) == expected, relative
    actor = lab.load_actor(path)
    check_anchor(actor)
    return actor, payload


def fresh_anchor(directory, seed):
    """Independent seeds: the same earlier A/B/A schedule, guided arm only."""
    prefix, continuation = lab.schedule(seed)
    initial = lab.RecursiveDevelopment(seed=seed, config=lab.DevelopmentConfig(max_conditions=16),
                                      recursive_config=lab.RecursiveConfig(role="flat"))
    actor = initial
    d = directory / "fresh-prefix"
    d.mkdir()
    previous = lab.save_actor(actor, d / "start.pkl.gz")
    for offset in (0, 128):
        actor, previous, _ = lab.train_block(actor, prefix[offset:offset + 128],
            d / f"block-{offset:06d}", previous, do_evaluate=offset == 128)
    parent = actor
    actor = pickle.loads(pickle.dumps(parent, protocol=5))
    actor.config = replace(actor.config, max_conditions=24)
    actor.recursive_config = replace(actor.recursive_config, role="ranked")
    lab.verify_fork(parent, actor, "ranked")
    d = directory / "fresh-guided"
    d.mkdir()
    previous = lab.save_actor(actor, d / "start.pkl.gz")
    for offset in range(0, 768, 128):
        actor, previous, evaluation = lab.train_block(actor, continuation[offset:offset + 128],
            d / f"block-{256 + offset:06d}", previous)
        print(json.dumps({"seed": seed, "stage": "fresh-anchor", "episode": actor.completed,
                          "correct": evaluation["correct"]}), flush=True)
    check_anchor(actor)
    return actor, (d / "block-000896/checkpoint.pkl.gz").read_bytes()


def solved(evaluation):
    return {r["row"] for r in evaluation["rows"] if r["reward"] > 0}


def transitions(evaluations):
    initial = solved(evaluations[0])
    previous = initial
    ever_lost = set()
    rows = []
    for result in evaluations[1:]:
        current = solved(result)
        ever_lost |= initial - current
        rows.append({"episode": result["episode"], "correct": result["correct"],
                     "contexts": result["context_correct"],
                     "gained_from_previous": sorted(current - previous),
                     "lost_from_previous": sorted(previous - current),
                     "gained_from_start": sorted(current - initial),
                     "lost_from_start": sorted(initial - current)})
        previous = current
    middle = solved(evaluations[3])
    learned_b = {i for i in middle - initial if lab.ROWS[i][2]}
    return {"milestones": rows, "initial_successes": len(initial),
            "initial_successes_never_lost_at_measurements": len(initial - ever_lost),
            "new_b_at_middle": sorted(learned_b),
            "new_b_retained_at_end": sorted(learned_b & previous)}


def verify_run(out, *, re_evaluate=False, source_root=lab.ROOT):
    protocol = json.loads((out / "protocol.json").read_text())
    for relative, expected in json.loads((out / "source.json").read_text()).items():
        assert lab.digest((source_root / relative).read_bytes()) == expected, relative
    counts = dict(training=0, evaluation=0, blocks=0, checkpoints=0, verification_actions=0)
    for seed in protocol["seeds"]:
        d = out / f"seed-{seed}"
        anchor = lab.load_actor(d / "anchor.pkl.gz")
        check_anchor(anchor)
        meta = json.loads((d / "anchor.json").read_text())
        assert lab.digest((d / "anchor.pkl.gz").read_bytes()) == meta["sha256"]
        counts["checkpoints"] += 1
        if protocol["mode"] == "saved":
            assert meta["sha256"] == SOURCE_HASHES[seed]
            counts["evaluation"] += 16
            if re_evaluate:
                assert lab.evaluate(anchor) == meta["evaluation"]
                counts["verification_actions"] += 16
        else:
            prefix, continuation = lab.schedule(seed)
            for stage, start, order in (("fresh-prefix", 0, prefix), ("fresh-guided", 256, continuation)):
                stage_dir = d / stage
                actor = lab.load_actor(stage_dir / "start.pkl.gz")
                if stage == "fresh-prefix":
                    expected = lab.RecursiveDevelopment(seed=seed, config=lab.DevelopmentConfig(max_conditions=16),
                                                       recursive_config=lab.RecursiveConfig(role="flat"))
                    verify_fork(expected, actor, 6)
                else:
                    lab.verify_fork(lab.load_actor(d / "fresh-prefix/block-000128/checkpoint.pkl.gz"), actor, "ranked")
                counts["checkpoints"] += 1
                verify_blocks(stage_dir, order, start, counts, re_evaluate)
            final_dir = d / "fresh-guided/block-000896"
            assert (d / "anchor.pkl.gz").read_bytes() == (final_dir / "checkpoint.pkl.gz").read_bytes()
            assert meta["evaluation"] == json.loads((final_dir / "evaluation.json").read_text())
        order = schedule(seed)
        assert json.loads((d / "schedule.json").read_text()) == order
        rngs = []
        for cap in CAPS:
            arm_dir = d / f"cap-{cap}"
            actor = lab.load_actor(arm_dir / "start.pkl.gz")
            verify_fork(anchor, actor, cap)
            counts["checkpoints"] += 1
            rngs.append(verify_blocks(arm_dir, order, 1024, counts, re_evaluate))
        assert rngs[0] == rngs[1], "paired exploration draws diverged"
    n = len(protocol["seeds"])
    fresh = protocol["mode"] == "fresh"
    assert counts["training"] == n * (2560 if fresh else 1536)
    assert counts["evaluation"] == n * (304 if fresh else 208)
    assert counts["blocks"] == n * (20 if fresh else 12)
    assert counts["checkpoints"] == n * (25 if fresh else 15)
    assert len(list(out.rglob("complete.json"))) == counts["blocks"]
    return counts


def verify_blocks(directory, order, start, counts, re_evaluate):
    previous = lab.digest((directory / "start.pkl.gz").read_bytes())
    expected_dirs = []
    for offset in range(0, len(order), 128):
        d = directory / f"block-{start + offset:06d}"
        expected_dirs.append(d.name)
        manifest = lab.verify_block(d, order[offset:offset + 128], start + offset, previous)
        previous = manifest["files"]["checkpoint.pkl.gz"]
        counts["blocks"] += 1
        counts["checkpoints"] += 1
        counts["training"] += manifest["training_records"]
        counts["evaluation"] += manifest["evaluation_records"]
        actor = lab.load_actor(d / "checkpoint.pkl.gz")
        if re_evaluate and manifest["evaluation_records"]:
            assert lab.evaluate(actor) == json.loads((d / "evaluation.json").read_text())
            counts["verification_actions"] += 16
    assert sorted(p.name for p in directory.glob("block-*")) == expected_dirs
    return actor.exploration_rng.getstate()


def limits(seconds):
    if hasattr(os, "sched_getaffinity"):
        os.sched_setaffinity(0, {min(os.sched_getaffinity(0))})
    if sys.platform != "darwin":
        resource.setrlimit(resource.RLIMIT_AS, (2 * 1024**3, 2 * 1024**3))
    resource.setrlimit(resource.RLIMIT_CPU, (seconds + 2, seconds + 5))
    resource.setrlimit(resource.RLIMIT_FSIZE, (64 * 1024**2, 64 * 1024**2))
    def expired(_sig, _frame):
        raise TimeoutError("fixed whole-run wall limit reached")
    signal.signal(signal.SIGALRM, expired)
    signal.alarm(seconds)


def run(args):
    limits(args.wall_seconds)
    out = args.output
    out.mkdir(parents=True, exist_ok=False)
    started = time.monotonic()
    mode = "saved" if args.source else "fresh"
    report = dict(status="running", mode=mode, seeds=args.seeds, arms=[],
                  wall_cap_seconds=args.wall_seconds)
    lab.json_once(out / "protocol.json", report)
    paths = {Path(__file__).resolve(), lab.ROOT / "docs/autogrowth/RECURSIVE_SPLIT_BUDGET.md",
             lab.ROOT / "scripts/autogrowth/guard_recursive_budget.py"}
    paths.update(Path(m.__file__).resolve() for m in tuple(sys.modules.values())
                 if getattr(m, "__file__", None) and Path(m.__file__).suffix == ".py"
                 and Path(m.__file__).resolve().is_relative_to(lab.ROOT))
    hashes = {}
    for path in sorted(paths):
        relative = path.relative_to(lab.ROOT)
        hashes[relative.as_posix()] = lab.digest(path.read_bytes())
        copy_path = out / "source-snapshot" / relative
        copy_path.parent.mkdir(parents=True, exist_ok=True)
        lab.write_once(copy_path, path.read_bytes())
    lab.json_once(out / "source.json", hashes)
    try:
        for seed in args.seeds:
            d = out / f"seed-{seed}"
            d.mkdir()
            actor, payload = saved_anchor(args.source, seed) if args.source else fresh_anchor(d, seed)
            initial = lab.evaluate(actor) if args.source else json.loads((d / "fresh-guided/block-000896/evaluation.json").read_text())
            lab.write_once(d / "anchor.pkl.gz", payload)
            lab.json_once(d / "anchor.json", {"sha256": lab.digest(payload), "evaluation": initial})
            order = schedule(seed)
            lab.json_once(d / "schedule.json", order)
            for cap in CAPS:
                child = fork(actor, cap)
                arm_dir = d / f"cap-{cap}"
                arm_dir.mkdir()
                previous = lab.save_actor(child, arm_dir / "start.pkl.gz")
                arm = dict(seed=seed, cap=cap, initial=initial, evaluations=[], structures=[])
                report["arms"].append(arm)
                for offset in range(0, 768, 128):
                    child, previous, result = lab.train_block(child, order[offset:offset + 128],
                        arm_dir / f"block-{1024 + offset:06d}", previous)
                    arm["evaluations"].append(result)
                    arm["structures"].append(lab.summarize_actor(child))
                    print(json.dumps({"seed": seed, "cap": cap, "episode": child.completed,
                                      "contexts": result["context_correct"], "splits": len(child.splits),
                                      "elapsed_seconds": round(time.monotonic() - started, 1)}), flush=True)
                arm["retention"] = transitions([initial, *arm["evaluations"]])
                lab.json_once(arm_dir / "results.json", arm)
        report["verification"] = verify_run(out)
        report["status"] = "complete"
    except BaseException as error:
        report.update(status="incomplete", error=f"{type(error).__name__}: {error}")
        raise
    finally:
        signal.alarm(0)
        report["elapsed_seconds"] = time.monotonic() - started
        rss = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
        report["max_rss_kib"] = rss / 1024 if sys.platform == "darwin" else rss
        lab.json_once(out / "result.json", report)
    return report


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--source", type=Path)
    parser.add_argument("--seeds", type=int, nargs=3, required=True)
    parser.add_argument("--wall-seconds", type=int, default=600)
    parser.add_argument("--verify", action="store_true")
    args = parser.parse_args()
    if not 1 <= args.wall_seconds <= 600:
        parser.error("wall limit must be 1..600 seconds")
    if tuple(args.seeds) != ((4, 5, 6) if args.source else (7, 8, 9)):
        parser.error("declared seeds: saved 4/5/6, independent fresh 7/8/9")
    if args.verify:
        limits(min(args.wall_seconds, 120))
        print(json.dumps(verify_run(args.output, re_evaluate=True)), flush=True)
    else:
        run(args)
