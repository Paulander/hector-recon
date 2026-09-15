"""Offline arithmetic attribution. Never calls observe, grows an actor or fits it."""
import argparse
from collections import defaultdict
from functools import lru_cache
from fractions import Fraction
import hashlib
import json
import math
from pathlib import Path
import os
import resource
import signal

import numpy as np
from scipy.optimize import linprog

from run_recursive_retention import ROWS, load_actor, evaluate, json_once


@lru_cache(None)
def value(expression, row, action):
    if expression.operator == "read":
        i, expected = expression.atom
        return (*ROWS[row], bool(action))[i] == expected
    if expression.operator == "true":
        return True
    children = [value(c, row, action) for c in expression.children]
    return {"and": all(children), "or": any(children), "xor": sum(children) == 1}[expression.operator]


def target(row):
    x, y, z, _ = ROWS[row]
    return int(y if z else x)


def difference(expression, row):
    correct = target(row)
    return int(value(expression, row, correct)) - int(value(expression, row, 1 - correct))


def coordinates(expression):
    if expression.operator == "read":
        return {expression.atom[0]}
    return set().union(*(coordinates(c) for c in expression.children))


def capacity(actor):
    identities = list(actor.conditions)
    matrix = np.array([[difference(actor.expressions[cid], row) for cid in identities]
                       for row in range(16)], dtype=float)
    # option:1 wins an exact tie, as in FormalReConEngine. Uniform scaling
    # allows margin >=1 for rows requiring option:0, >=0 for option:1.
    threshold = np.array([1 - target(row) for row in range(16)])
    fit = linprog(np.zeros(len(identities)), A_ub=-matrix, b_ub=-threshold,
                  bounds=[(None, None)] * len(identities), method="highs",
                  options={"time_limit": 10})
    answer = {"status": fit.status, "message": fit.message,
              "joint_perfect_ranking_feasible": bool(fit.success)}
    if fit.success:
        margins = matrix @ fit.x
        assert np.min(margins - threshold) > -1e-7
        answer.update(identities=identities, offline_witness=fit.x.tolist(), margins=margins.tolist())
    elif fit.status != 2:
        raise RuntimeError(f"capacity test inconclusive: {fit.message}")
    return answer


def capacity_trajectory(directory):
    paths = [directory / "start.pkl.gz", *sorted(directory.glob("block-*/checkpoint.pkl.gz"))]
    timeline = []
    for path in paths:
        actor = load_actor(path)
        timeline.append({"episode": actor.completed, **capacity(actor)})
    final = load_actor(paths[-1])
    ids = list(final.conditions)
    matrix = [[difference(final.expressions[cid], row) for cid in ids] for row in range(16)]
    threshold = [1 - target(row) for row in range(16)]
    certificate = None
    if not timeline[-1]["joint_perfect_ranking_feasible"]:
        # A nonnegative combination of required inequalities gives 0 >= c>0.
        # Rationalize and verify exactly, not just with the LP solver's tolerance.
        fit = linprog(-np.array(threshold), A_eq=np.vstack((np.array(matrix).T, np.ones(16))),
                      b_eq=np.array([0] * len(ids) + [1]), bounds=[(0, None)] * 16,
                      method="highs", options={"time_limit": 10})
        assert fit.success
        factors = [Fraction(float(x)).limit_denominator(1000000) for x in fit.x]
        assert all(x >= 0 for x in factors) and sum(factors) == 1
        assert all(sum(factors[row] * matrix[row][col] for row in range(16)) == 0 for col in range(len(ids)))
        contradiction = sum(factors[row] * threshold[row] for row in range(16))
        assert contradiction > 0
        certificate = {"weighted_required_margin": str(contradiction),
                       "rows": [{"row": row, "state": ROWS[row], "correct_action": target(row),
                                 "factor": str(factor), "required_margin": threshold[row],
                                 "coefficients": matrix[row]} for row, factor in enumerate(factors) if factor],
                       "condition_ids": ids, "exact_rational_verification": True}
    return {"timeline": timeline, "final_infeasibility_certificate": certificate}


def split_options(actor, *, before_last=False):
    """Hypothetical matrices only: no actor mutation or fitted policy execution."""
    last = actor.splits[-1]
    ids = set(actor.conditions)
    seen = actor.seen
    if before_last:
        ids = (ids - set(last["children"])) | {last["parent"]}
        seen = seen - {actor.expressions[cid] for cid in last["children"]}
    choices = []
    for (cid, index), evidence in actor.evidence.items():
        if cid not in ids:
            continue
        score = evidence.score(actor.recursive_config.min_support)
        context = actor.contexts[index]
        children = actor._split_expressions(cid, context)
        if (score is None or max(c.depth for c in children) > actor.recursive_config.max_depth
                or any(c in seen for c in children)):
            continue
        exprs = [actor.expressions[j] for j in sorted(ids - {cid})] + list(children)
        matrix = np.array([[difference(ex, row) for ex in exprs] for row in range(16)])
        fit = linprog(np.zeros(len(exprs)), A_ub=-matrix,
                      b_ub=-np.array([1 - target(row) for row in range(16)]),
                      bounds=[(None, None)] * len(exprs), method="highs", options={"time_limit": 2})
        assert fit.status in (0, 2)
        if fit.success:
            assert np.min(matrix @ fit.x - np.array([1 - target(row) for row in range(16)])) >= -1e-7
        choices.append({"source": cid, "context_index": index, "context": repr(context),
                        "score": score, "support": [evidence.n0, evidence.n1],
                        "permits_joint_perfect_ranking": bool(fit.success)})
    choices.sort(key=lambda c: (-c["score"], c["source"], c["context_index"]))
    if before_last:
        assert choices[0]["source"] == last["parent"] and choices[0]["context"] == repr(last["context"])
    return choices


def loss_accounting(directory, attributed, row, start):
    actor = load_actor(directory / "block-000896/checkpoint.pkl.gz")
    records = [json.loads(line) for p in sorted(directory.glob("block-*/training.jsonl"))
               for line in p.read_text().splitlines()]
    credit = math.fsum(.3 * (r["reward"] - r["prediction"]) / (1 + len(r["active"]))
                      * sum(difference(actor.expressions[cid], row) for cid in r["active"])
                      for r in records if r["event"] >= start)
    pruning = math.fsum(-float(h["condition"].weight) * difference(h["expression"], row)
                       for h in actor.history if h["reason"] == "weak" and h["episode"] > start)
    margins = {int(k): v for k, v in attributed["margins"].items()}
    before, after = margins[start][row], margins[1024][row]
    assert abs(after - before - credit - pruning) < 1e-10
    crossings = [c for c in attributed["loss_crossings"] if c["row"] == row and c["event"] >= start]
    return {"seed": attributed["seed"], "row": row, "from_episode": start,
            "initial_margin": before, "final_margin": after, "credit_change": credit,
            "pruning_change": pruning, "first_strict_crossing": crossings[0],
            "last_strict_crossing": crossings[-1]}


def attribute(directory, seed):
    initial = load_actor(directory / "start.pkl.gz")
    final = load_actor(directory / "block-000896/checkpoint.pkl.gz")
    expressions = final.expressions
    weights = {cid: float(c.weight) for cid, c in initial.conditions.items()}
    bias = float(initial.bias)
    histories, splits, births = defaultdict(list), defaultdict(list), defaultdict(list)
    all_conditions = {h["condition"].identity: h["condition"] for h in final.history}
    all_conditions.update(final.conditions)
    for h in final.history:
        if h["episode"] > 256:
            histories[h["episode"]].append(h)
    for split in final.splits:
        splits[split["episode"]].append(split)
    for cid, condition in all_conditions.items():
        if condition.born > 256:
            births[condition.born].append(cid)
    gaps = []
    crossings = []
    checkpoints = []
    snapshots = {}
    def margins():
        return [math.fsum(w * difference(expressions[cid], row) for cid, w in weights.items())
                for row in range(16)]
    def crossing(before, after, event, stage, record, contributors):
        for row, (old, new) in enumerate(zip(before, after)):
            if old > 1e-9 and new < -1e-9:
                crossings.append({"row": row, "event": event, "stage": stage,
                    "before": old, "after": new, "training_row": record["row"],
                    "training_context": int(ROWS[record["row"]][2]), "reward": record["reward"],
                    "contributors": [{"id": cid, "generation": final.generation[cid],
                        "margin_change": change * difference(expressions[cid], row),
                        "expression": repr(expressions[cid])} for cid, change in contributors
                        if difference(expressions[cid], row)]})
    snapshots[256] = margins()
    records_count = 0
    for block in sorted(directory.glob("block-*")):
        manifest = json.loads((block / "complete.json").read_text())
        for name, sha in manifest["files"].items():
            assert hashlib.sha256((block / name).read_bytes()).hexdigest() == sha
        for line in (block / "training.jsonl").read_text().splitlines():
            r = json.loads(line)
            event, row = r["event"], r["row"]
            assert event == 256 + records_count
            records_count += 1
            active = r["active"]
            actual = int(r["action"] == "act-b")
            assert set(active) == {cid for cid in weights if value(expressions[cid], row, actual)}
            prediction = bias + math.fsum(weights[cid] for cid in active)
            gaps.append(abs(prediction - r["prediction"]))
            assert abs(prediction - r["prediction"]) < 1e-10
            if r["contexts"] is not None:
                assert r["contexts"] == [value(c, row, actual) for c in final.contexts]
            before = margins()
            delta = .3 * (r["reward"] - r["prediction"]) / (1 + len(active))
            for cid, old, new in zip(active, r["weights_before"], r["weights_after"]):
                assert abs(weights[cid] - old) < 1e-10
                weights[cid] += delta
                assert abs(weights[cid] - new) < 1e-10
            bias += delta
            after_credit = margins()
            crossing(before, after_credit, event, "credit", r, [(cid, delta) for cid in active])
            retired = []
            for h in histories[event + 1]:
                cid = h["condition"].identity
                assert abs(weights[cid] - float(h["condition"].weight)) < 1e-10
                if h["reason"] == "weak":
                    retired.append((cid, -weights.pop(cid)))
            after_pruning = margins()
            crossing(after_credit, after_pruning, event, "pruning", r, retired)
            split_children = set()
            for split in splits[event + 1]:
                inherited = weights.pop(split["parent"])
                assert abs(inherited - split["inherited_weight"]) < 1e-10
                for cid in split["children"]:
                    weights[cid] = inherited
                    split_children.add(cid)
            for cid in births[event + 1]:
                if cid not in split_children:
                    weights[cid] = 0.0
            after = margins()
            assert max(abs(a - b) for a, b in zip(after_pruning, after)) < 1e-10, "split changed a score margin"
        saved = load_actor(block / "checkpoint.pkl.gz")
        assert weights.keys() == saved.conditions.keys()
        errors = [abs(weights[cid] - float(c.weight)) for cid, c in saved.conditions.items()]
        assert max(errors, default=0) < 1e-10 and abs(bias - float(saved.bias)) < 1e-10
        recorded = json.loads((block / "evaluation.json").read_text())
        assert evaluate(saved) == recorded
        actual_margins = margins()
        for item in recorded["rows"]:
            m = actual_margins[item["row"]]
            if abs(m) > 1e-9:
                assert (m > 0) == (item["reward"] > 0)
        snapshots[saved.completed] = actual_margins
        checkpoints.append({"episode": saved.completed, "max_weight_error": max(errors, default=0)})
    assert records_count == 768
    return {"seed": seed, "records_verified": records_count,
            "frozen_evaluation_actions": len(checkpoints) * 16,
            "max_prediction_error": max(gaps), "checkpoints": checkpoints,
            "margins": snapshots, "loss_crossings": crossings,
            "capacity": capacity(final),
            "splits": [{**s, "context": repr(s["context"]),
                        "context_coordinates": sorted(coordinates(s["context"]))} for s in final.splits]}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--details-from", type=Path,
                        help="reuse an existing attribution for LP/accounting details, with no repeated actions")
    args = parser.parse_args()
    os.sched_setaffinity(0, {min(os.sched_getaffinity(0))})
    resource.setrlimit(resource.RLIMIT_AS, (2 * 1024**3, 2 * 1024**3))
    signal.alarm(90)
    if args.details_from:
        previous = json.loads(args.details_from.read_text())
        actors = {a["seed"]: a for a in previous["actors"]}
        seed4 = load_actor(args.run / "seed-4/ranked/block-000896/checkpoint.pkl.gz")
        result = {"status": "complete", "training_actions": 0, "evaluation_actions": 0,
                  "capacity": {str(s): capacity_trajectory(args.run / f"seed-{s}/ranked") for s in (4, 5, 6)},
                  "before_last_split": split_options(seed4, before_last=True),
                  "hypothetical_seventh_split": split_options(seed4),
                  "loss_accounting": [loss_accounting(args.run / f"seed-{s}/ranked", actors[s], row, start)
                                      for s, row, start in ((4, 5, 256), (6, 6, 640), (6, 7, 640))]}
        json_once(args.output, result)
        print("Offline details completed; zero training or evaluation actions.")
        raise SystemExit(0)
    result = {"status": "complete", "training_actions": 0,
              "actors": [attribute(args.run / f"seed-{s}/ranked", s) for s in (4, 5, 6)]}
    json_once(args.output, result)
    print(json.dumps({"actors": [{"seed": a["seed"], "prediction_error": a["max_prediction_error"],
        "capacity": a["capacity"]["joint_perfect_ranking_feasible"], "crossings": len(a["loss_crossings"])} for a in result["actors"]]}))
