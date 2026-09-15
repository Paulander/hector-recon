"""Offline reconstruction of seed 4 cap12's final 128 recorded updates.

No actor act/observe/refine calls; no fitted weights or new environment outcomes.
"""
from collections import defaultdict
import argparse
import hashlib
import json
import math
from pathlib import Path

from attribute_recursive_retention import ROWS, difference, target, value
from run_recursive_budget import limits, lab


def signature(expression):
    return tuple(value(expression, row, action) for row in range(16) for action in (0, 1))


def equivalent_rows(expression):
    return [{"row": row, "action": action} for row in range(16) for action in (0, 1)
            if value(expression, row, action)]


def attribute(run):
    resolution = json.loads((run / "independent-verification.json").read_text())
    assert resolution["status"] == "verified_complete_after_verifier_correction"
    directory = run / "seed-4/cap-12"
    before_dir, block = directory / "block-001536", directory / "block-001664"
    for d in (before_dir, block):
        manifest = json.loads((d / "complete.json").read_text())
        for name, expected in manifest["files"].items():
            assert hashlib.sha256((d / name).read_bytes()).hexdigest() == expected
    first = lab.load_actor(before_dir / "checkpoint.pkl.gz")
    last = lab.load_actor(block / "checkpoint.pkl.gz")
    assert first.completed == 1664 and last.completed == 1792
    records = [json.loads(line) for line in (block / "training.jsonl").read_text().splitlines()]
    assert len(records) == 128
    assert [r["event"] for r in records] == list(range(1664, 1792))
    assert json.loads((block / "intent.json").read_text())["previous_checkpoint_sha256"] == lab.digest((before_dir / "checkpoint.pkl.gz").read_bytes())
    expressions = last.expressions
    weights = {cid: float(c.weight) for cid, c in first.conditions.items()}
    bias = float(first.bias)
    histories = defaultdict(list)
    splits = defaultdict(list)
    for h in last.history:
        if 1664 < h["episode"] <= 1792:
            histories[h["episode"]].append(h)
    for s in last.splits:
        if 1664 < s["episode"] <= 1792:
            splits[s["episode"]].append(s)
    all_conditions = {h["condition"].identity: h["condition"] for h in last.history}
    all_conditions.update(last.conditions)
    births = defaultdict(list)
    for cid, condition in all_conditions.items():
        if 1664 < condition.born <= 1792:
            births[condition.born].append(cid)

    def margins():
        return [math.fsum(w * difference(expressions[cid], row) for cid, w in weights.items())
                for row in range(16)]

    def snapshot():
        return {str(cid): w for cid, w in weights.items()}

    def correct(margin, row):
        if abs(margin) < 1e-10:
            return None  # Near ties are explicitly inconclusive, not rounded wins.
        return margin > 0

    initial_margins = margins()
    stage_totals = {name: [0.0] * 16 for name in ("credit", "pruning", "growth")}
    credit_groups = defaultdict(lambda: {"count": 0, "margin_changes": [0.0] * 16})
    by_contributor = defaultdict(lambda: defaultdict(float))
    stages = []
    losses = []
    recoveries = []
    max_prediction_error = 0.0
    participation = defaultdict(lambda: defaultdict(int))
    for r in records:
        actual = int(r["action"] == "act-b")
        row = r["row"]
        assert r["reward"] == (1 if actual == target(row) else -1)
        active = r["active"]
        assert set(active) == {cid for cid in weights if value(expressions[cid], row, actual)}
        assert r["contexts"] == [value(c, row, actual) for c in last.contexts]
        prediction = bias + math.fsum(weights[cid] for cid in active)
        error = abs(prediction - r["prediction"])
        max_prediction_error = max(error, max_prediction_error)
        assert error < 1e-10
        before = margins()
        before_weights = snapshot()
        delta = first.config.learning_rate * (r["reward"] - r["prediction"]) / (1 + len(active))
        group = f"{'B' if ROWS[row][2] else 'A'} reward {r['reward']:+d}"
        credit_groups[group]["count"] += 1
        for cid, old, new in zip(active, r["weights_before"], r["weights_after"]):
            assert abs(weights[cid] - old) < 1e-10
            weights[cid] += delta
            assert abs(weights[cid] - new) < 1e-10
            by_contributor[cid][group] += delta
            participation[cid][group] += 1
        bias += delta
        after_credit = margins()
        for i in range(16):
            change = after_credit[i] - before[i]
            stage_totals["credit"][i] += change
            credit_groups[group]["margin_changes"][i] += change
        pruning = []
        for h in histories[r["event"] + 1]:
            cid = h["condition"].identity
            assert abs(weights[cid] - float(h["condition"].weight)) < 1e-10
            if h["reason"] == "weak":
                pruning.append({"id": cid, "removed_weight": weights.pop(cid)})
        after_pruning = margins()
        for i in range(16):
            stage_totals["pruning"][i] += after_pruning[i] - after_credit[i]
        new_children = set()
        for s in splits[r["event"] + 1]:
            inherited = weights.pop(s["parent"])
            assert abs(inherited - s["inherited_weight"]) < 1e-10
            for cid in s["children"]:
                weights[cid] = inherited
                new_children.add(cid)
        for cid in births[r["event"] + 1]:
            if cid not in new_children:
                weights[cid] = 0.0
        after = margins()
        for i in range(16):
            stage_totals["growth"][i] += after[i] - after_pruning[i]
        assert max(abs(a - b) for a, b in zip(after, after_pruning)) < 1e-10
        step = {"event": r["event"], "training_row": row, "state": ROWS[row],
                "action": r["action"], "reward": r["reward"], "prediction": prediction,
                "active": active, "delta": delta, "pruning": pruning,
                "margins_before": before, "margins_after_credit": after_credit,
                "margins_after_pruning": after_pruning, "margins_after": after}
        stages.append(step)
        for stage, left, right in (("credit", before, after_credit),
                                   ("pruning", after_credit, after_pruning),
                                   ("growth", after_pruning, after)):
            for i in range(16):
                old, new = correct(left[i], i), correct(right[i], i)
                if old is not None and new is not None and old != new:
                    crossing = {"row": i, "stage": stage, "event": r["event"],
                                "before": left[i], "after": right[i], "record": step,
                                "weights_before": before_weights,
                                "contributors": [{"id": cid, "margin_change": delta * difference(expressions[cid], i)}
                                    for cid in active if difference(expressions[cid], i)] if stage == "credit" else pruning}
                    (losses if old else recoveries).append(crossing)
    final_margins = margins()
    assert weights.keys() == last.conditions.keys()
    max_weight_error = max(abs(weights[cid] - float(c.weight)) for cid, c in last.conditions.items())
    assert max_weight_error < 1e-10 and abs(bias - float(last.bias)) < 1e-10
    assert max(abs(final_margins[i] - initial_margins[i] - sum(v[i] for v in stage_totals.values())) for i in range(16)) < 1e-10
    for d, ms in ((before_dir, initial_margins), (block, final_margins)):
        ev = json.loads((d / "evaluation.json").read_text())
        for item in ev["rows"]:
            assert abs(ms[item["row"]]) > 1e-10
            assert (ms[item["row"]] > 0) == (item["reward"] > 0)
    aliases = defaultdict(list)
    for cid in first.conditions:
        aliases[signature(expressions[cid])].append(cid)
    definitions = {}
    for cid in set(first.conditions) | set(last.conditions):
        definitions[str(cid)] = {"expression": repr(expressions[cid]),
                                "true_cells": equivalent_rows(expressions[cid]),
                                "generation": last.generation[cid],
                                "initial_weight": float(first.conditions[cid].weight) if cid in first.conditions else None,
                                "final_weight": float(last.conditions[cid].weight) if cid in last.conditions else None,
                                "credit_by_group": dict(by_contributor[cid]),
                                "participation_by_group": dict(participation[cid])}
    return {"status": "complete", "seed": 4, "cap": 12, "start": 1664, "stop": 1792,
            "recorded_updates_reconstructed": len(records), "new_training_actions": 0,
            "new_evaluation_actions": 0, "max_prediction_error": max_prediction_error,
            "max_endpoint_weight_error": max_weight_error,
            "initial_margins": initial_margins, "final_margins": final_margins,
            "stage_margin_changes": stage_totals, "credit_by_group": dict(credit_groups),
            "initial_functional_aliases": [ids for ids in aliases.values() if len(ids) > 1],
            "definitions": definitions, "strict_losses": losses, "strict_recoveries": recoveries,
            "updates": stages,
            "input_sha256": {str(p.relative_to(run)): lab.digest(p.read_bytes()) for p in
                [before_dir / "checkpoint.pkl.gz", before_dir / "evaluation.json",
                 block / "checkpoint.pkl.gz", block / "evaluation.json", block / "training.jsonl"]}}


def details(run, recorded):
    """Explain known contributors and reconstruct the final nomination ordering."""
    assert recorded["recorded_updates_reconstructed"] == 128
    d = run / "seed-4/cap-12"
    first = lab.load_actor(d / "block-001536/checkpoint.pkl.gz")
    last = lab.load_actor(d / "block-001664/checkpoint.pkl.gz")
    for row in (6, 7):
        expected = {31: -1, 33: 1, 35: -1}
        actual = {cid: difference(first.expressions[cid], row) for cid in first.conditions
                  if difference(first.expressions[cid], row)}
        assert expected == actual
    # Exact equivalence over every Boolean state/action cell, not a sampled alias.
    for row in range(16):
        x, y, z, _ = ROWS[row]
        for action in (0, 1):
            broad = not x and y and not action
            specific = not x and y and z and bool(action)
            assert value(first.expressions[31], row, action) == broad
            assert value(first.expressions[35], row, action) == broad
            assert value(first.expressions[33], row, action) == specific
    split = last.splits[-1]
    assert split["episode"] == 1792
    ids = (set(last.conditions) - set(split["children"])) | {split["parent"]}
    seen = last.seen - {last.expressions[cid] for cid in split["children"]}
    choices = []
    for (cid, i), evidence in last.evidence.items():
        if cid not in ids:
            continue
        score = evidence.score(last.recursive_config.min_support)
        children = last._split_expressions(cid, last.contexts[i])
        if (score is not None and max(c.depth for c in children) <= last.recursive_config.max_depth
                and all(c not in seen for c in children)):
            choices.append({"source": cid, "context_index": i, "score": score,
                            "context": repr(last.contexts[i]), "n0": evidence.n0, "n1": evidence.n1,
                            "mean_residual0": evidence.sum0 / evidence.n0,
                            "mean_residual1": evidence.sum1 / evidence.n1})
    choices.sort(key=lambda c: (-c["score"], c["source"], c["context_index"]))
    assert choices[0]["source"] == split["parent"]
    assert choices[0]["context"] == repr(split["context"])
    assert abs(choices[0]["score"] - split["score"]) < 1e-10
    # Nomination records exist before refinement; no new experiences or nominations
    # are supplied to the actor by reconstructing this ordering.
    return {"new_training_actions": 0, "new_evaluation_actions": 0,
            "equivalences_verified_cells": 32,
            "broad_a_ids": [31, 35], "specific_b_id": 33,
            "margin_formula_before_final_split": "w33 - w31 - w35",
            "final_split_margin_addition": float(last.conditions[39].weight) - float(last.conditions[38].weight),
            "final_nomination_order": choices,
            "note": "Ranking reconstructs the actual final decision. It does not prove that an alternative split would have learned or retained the desired policy."}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--details-from", type=Path)
    args = parser.parse_args()
    limits(90)
    if args.details_from:
        result = details(args.run, json.loads(args.details_from.read_text()))
        lab.json_once(args.output, result)
        print("Verified exact branch functions and final nomination ordering; zero new actions.")
        raise SystemExit(0)
    result = attribute(args.run)
    lab.json_once(args.output, result)
    print(json.dumps({"updates": result["recorded_updates_reconstructed"],
                      "prediction_error": result["max_prediction_error"],
                      "target_initial_margin": result["initial_margins"][6],
                      "target_final_margin": result["final_margins"][6],
                      "loss_events": sorted({c["event"] for c in result["strict_losses"] if c["row"] in (6, 7)})}))
