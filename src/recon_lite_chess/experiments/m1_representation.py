"""Offline representation diagnosis. Never imported by an organism or coach.

Alternative-action grades and mathematical comparisons are laboratory data only.
No diagnostic weights, actions, or labels are installed in any actor.
"""
import argparse
from collections import defaultdict
import gzip
import json
import math
from pathlib import Path
import pickle
import time

import chess
import numpy as np
import scipy
from scipy.optimize import linprog

from recon_lite.graph import Node, NodeType
from recon_lite_hector.learning.terminal_development import _reader
from recon_lite_chess.coach.exercise import play_mate_one
from recon_lite_chess.coach.pools import load_split
from recon_lite_chess.coach.terminal import ChessFeaturePort
from . import ordinary_m1 as prior


def expired(deadline):
    if time.monotonic() >= deadline:
        raise TimeoutError("diagnostic budget expired; no shortened complete report")


def gate_value(condition, vector):
    matches = [vector[i] == expected for i, expected in condition.atoms]
    if condition.operator == "and":
        return int(all(matches))
    if condition.operator == "or":
        return int(any(matches))
    if condition.operator == "xor":
        return int(sum(matches) == 1)  # Formal SCRIPT semantics: exactly one.
    raise ValueError("unsupported diagnostic condition grammar")


def terminal_vectors(port):
    """Lab observes all coordinates using the existing leaf reader function.

    This diagnostic coverage is never installed in the trained actor.
    """
    bindings = port.bindings()
    vectors = []
    for slot in range(len(bindings)):
        values = []
        for index, coordinate in enumerate(port.schema):
            node = Node("lab-reader", NodeType.TERMINAL, predicate=_reader,
                        meta={"slot": slot, "atom": (index, coordinate.values[0])})
            _reader(node, {"port": port, "schema": port.schema, "bindings": bindings})
            values.append(node.meta["reading"])
        vectors.append(tuple(values))
    return bindings, vectors


def laboratory_rows(fens, *, deadline, counts=None):
    """Grade each legal alternative once on an isolated environment copy.

    These are counted laboratory transitions, not training experience.
    """
    rows = []
    for fen in fens:
        expired(deadline)
        bindings, vectors = terminal_vectors(ChessFeaturePort(chess.Board(fen)))
        wins = []
        for binding in bindings:
            board = chess.Board(fen)
            board.push_uci(binding)
            if counts is not None:
                counts["laboratory_transitions"] += 1
            wins.append(int(board.is_checkmate()))
        if not any(wins):
            raise ValueError("declared M1 exercise has no winning action")
        rows.append({"fen": fen, "bindings": bindings, "vectors": vectors, "wins": wins})
    return rows


def alias_summary(rows, signatures):
    """A local upper bound, respecting the existing reverse-lexical slot tie.

    If no signature class's tie-winning representative mates, no weights on
    those signatures can solve this row. The bound need not be attainable by one
    global set of linear weights across all rows.
    """
    mixed_rows = impossible = 0
    for row, matrix in zip(rows, signatures):
        groups = defaultdict(list)
        for slot, signature in enumerate(matrix):
            groups[tuple(signature)].append(slot)
        mixed_rows += any(len({row["wins"][i] for i in slots}) > 1 for slots in groups.values())
        representatives = [max(slots, key=lambda i: f"option:{i}") for slots in groups.values()]
        impossible += not any(row["wins"][i] for i in representatives)
    return {"rows_with_win_loss_alias": mixed_rows, "unavoidable_failures_with_existing_tie": impossible,
            "local_signature_upper_bound_mates": len(rows)-impossible}


def ranking_feasibility(rows, matrices, *, deadline):
    """Offline existence check; fitted coefficients are discarded, never returned.

    All wins above all failures is sufficient. With multiple winning actions,
    infeasibility does not rule out a policy that prefers just one of them.
    Strict ranking also excludes policies relying on favorable exact ties.
    """
    expired(deadline)
    constraints = []
    for row, matrix in zip(rows, matrices):
        x = np.asarray(matrix, dtype=float)
        for win in (i for i, y in enumerate(row["wins"]) if y):
            for loss in (i for i, y in enumerate(row["wins"]) if not y):
                constraints.append(x[loss]-x[win])
    width = len(matrices[0][0])
    if not constraints:
        return {"strict_all_winners_rankable": True, "constraints": 0, "fitted_weights_discarded": True}
    if not width:
        return {"strict_all_winners_rankable": False, "constraints": len(constraints), "empty_representation": True}
    a = np.asarray(constraints)
    result = linprog(np.zeros(width), A_ub=a, b_ub=-np.ones(len(a)),
                     bounds=(None, None), method="highs", options={"time_limit": max(.001, deadline-time.monotonic())})
    if result.status not in (0, 2):
        raise RuntimeError(f"inconclusive feasibility solver: {result.message}")
    verified = result.status == 0
    if verified and not np.all(a @ result.x <= -1 + 1e-7):
        raise RuntimeError("solver certificate failed direct margin check")
    return {"strict_all_winners_rankable": verified, "constraints": len(constraints),
            "rows_with_multiple_winners": sum(sum(r["wins"]) > 1 for r in rows),
            "fitted_weights_discarded": True}


def inspect_actor(actor, rows, *, deadline, counts=None):
    before = prior.actor_digest(actor)
    conditions = list(actor.conditions.values())
    atoms = sorted({atom for c in conditions for atom in c.atoms})
    gate_matrices, atom_matrices = [], []
    outcomes, actions = [], []
    failures_below_winning_score = failures_tied = 0
    for event, row in enumerate(rows):
        expired(deadline)
        matrix = [tuple(gate_value(c, v) for c in conditions) for v in row["vectors"]]
        gate_matrices.append(matrix)
        atom_matrices.append([tuple(int(v[i] == expected) for i, expected in atoms) for v in row["vectors"]])
        scores = [math.fsum([float(actor.bias), *(float(c.weight)*x for c, x in zip(conditions, values))])
                  for values in matrix]
        predicted = max(range(len(scores)), key=lambda i: (scores[i], f"option:{i}"))
        if counts is not None:
            counts["actor_actions_started"] += 1
        attempt = play_mate_one(actor, row["fen"], event_id=event, learn=False)
        if counts is not None:
            counts["actor_evaluation_moves"] += attempt.real_moves
        chosen = row["bindings"].index(attempt.action)
        if attempt.real_moves != 1 or chosen != predicted:
            raise RuntimeError("formal choice differs from declared gate/weight calculation")
        for slot, expected in enumerate(scores):
            actual = actor.graph.nodes[f"option:{slot}"].activation.value
            if not math.isclose(actual, expected, rel_tol=1e-12, abs_tol=1e-12):
                raise RuntimeError("formal support differs from declared gate/weight calculation")
        won = int(attempt.reason == "checkmate")
        if won != row["wins"][chosen]:
            raise RuntimeError("laboratory and exercise outcome differ")
        outcomes.append(won); actions.append(attempt.action)
        if not won:
            winning_score = max(s for s, y in zip(scores, row["wins"]) if y)
            failures_tied += scores[chosen] == winning_score
            failures_below_winning_score += winning_score < scores[chosen]
    if prior.actor_digest(actor) != before:
        raise RuntimeError("diagnosis changed learned state")
    return {"mates": sum(outcomes), "rows": len(rows), "outcomes": outcomes,
            "action_digest": prior.digest(actions), "learned_state_unchanged": True,
            "formal_support_and_choice_match": True, "live_conditions": len(conditions), "distinct_atoms": len(atoms),
            "failures_tied_with_best_win": failures_tied,
            "failures_with_win_scored_lower": failures_below_winning_score,
            "raw_schema": alias_summary(rows, [r["vectors"] for r in rows]),
            "readers": alias_summary(rows, atom_matrices),
            "gates": alias_summary(rows, gate_matrices),
            "strict_gate_ranking": ranking_feasibility(rows, gate_matrices, deadline=deadline)}


def restore_actor(reference, previous, private, seed, role, event):
    """Restore our trusted evaluated payload after source/transport verification."""
    if reference["manifest"]["source"] != prior.sources():
        raise ValueError("checkpoint runtime/source differs")
    name = f"seed-{seed}-{role}-{event}.json"
    if prior.sha(previous/name) != reference["artifact_hashes"][name]:
        raise ValueError("historical endpoint record hash differs")
    record = prior.read(previous/name)
    entry = next(e for e in reference["private_checkpoint_hashes"] if e["sha256"] == record["checkpoint_sha256"])
    path = (private/entry["path"]).resolve()
    if not path.is_relative_to(private.resolve()) or prior.sha(path) != entry["sha256"]:
        raise ValueError("checkpoint path/transport differs")
    with gzip.open(path, "rb") as stream:
        payload = pickle.load(stream)
    if (payload["source"] != reference["manifest"]["source"]
            or payload["manifest_digest"] != prior.digest(reference["manifest"])):
        raise ValueError("checkpoint payload source/experiment differs")
    state = payload["state"]; actor = state["organism"]
    if (state["seed"] != seed or state["role_index"] != prior.ROLES.index(role)
            or state["next_event"] != event or actor.completed != event or actor.pending or actor.hold_topology):
        raise ValueError("checkpoint actor/progress differs")
    observed = prior.snapshot(actor)
    if any(observed[k] != record["result"][k] for k in observed):
        raise ValueError("checkpoint state differs from evaluated actor")
    return actor, entry["sha256"]


def run(args):
    if args.wall_seconds <= 0:
        raise ValueError("positive diagnostic time budget required")
    reference = prior.read(args.reference)
    if reference["status"] != "complete" or reference["manifest"]["source"] != prior.sources():
        raise ValueError("complete source-matched reference required")
    splits, hashes, alternatives = {}, {}, {}
    for name in ("train", "validation"):
        splits[name], hashes[name] = load_split(args.pool, name)
        if hashes[name] != reference["manifest"][name+"_sha256"]:
            raise ValueError("pool differs from saved experiment")
        alternatives[name] = sum(chess.Board(f).legal_moves.count() for f in splits[name])
    actors = [(seed, role, event) for seed in (2, 3) for role in ("none", "ranked") for event in (384, 1024)]
    manifest = {"schema": "m1_representation.v1", "source": prior.sources(),
                "diagnostic_sha256": prior.sha(__file__), "scipy": scipy.__version__,
                "reference_sha256": prior.sha(args.reference), "actors": actors, "pool_hashes": hashes,
                "laboratory_transitions": sum(alternatives.values()),
                "actor_evaluation_moves": len(actors)*sum(map(len, splits.values())),
                "training_moves": 0, "wall_seconds": args.wall_seconds,
                "final_test_opened": False, "diagnostic_data_enters_actor": False,
                "alternatives_per_split": alternatives,
                "limits": ["Signature bounds use the existing reverse-lexical slot tiebreak; they need not be attainable globally.",
                           "Strict all-winners ranking is sufficient, not necessary for policies using favorable ties or just one of several wins.",
                           "Offline fitted coefficients are discarded and are never installed in actors."]}
    args.output.mkdir(parents=True, exist_ok=False)
    prior.atomic_json(args.output/"manifest.json", manifest)
    started = time.monotonic(); deadline = started + args.wall_seconds
    counts = {"laboratory_transitions": 0, "actor_actions_started": 0, "actor_evaluation_moves": 0}
    results = []
    try:
        data = {name: laboratory_rows(fens, deadline=deadline, counts=counts) for name, fens in splits.items()}
        for seed, role, event in actors:
            actor, checkpoint_hash = restore_actor(reference, args.previous, args.private, seed, role, event)
            before = prior.actor_digest(actor)
            reports = {name: inspect_actor(actor, rows, deadline=deadline, counts=counts) for name, rows in data.items()}
            old = next(s for s in reference["results"] if s["seed"] == seed)["roles"][role]["milestones"][str(event)]["evaluation"]
            if any(reports["validation"][k] != old[k] for k in ("mates", "outcomes", "action_digest")):
                raise RuntimeError("historical development behavior differs")
            if prior.actor_digest(actor) != before:
                raise RuntimeError("actor changed across diagnostic splits")
            result = {"seed": seed, "role": role, "event": event, "checkpoint_sha256": checkpoint_hash,
                      "historical_behavior_matches": True, "reports": reports}
            results.append(result)
            prior.atomic_json(args.output/f"seed-{seed}-{role}-{event}.json", result)
            print(json.dumps({"seed": seed, "role": role, "event": event,
                              "mates": reports["validation"]["mates"], "gates": reports["validation"]["gates"]}), flush=True)
        assert counts["laboratory_transitions"] == manifest["laboratory_transitions"]
        assert counts["actor_evaluation_moves"] == counts["actor_actions_started"] == manifest["actor_evaluation_moves"]
        expired(deadline)
        result = {"status": "complete", "manifest": manifest, "actual_counts": counts,
                  "wall_seconds": time.monotonic()-started, "results": results}
        prior.atomic_json(args.output/"summary.json", result)
    except BaseException as error:
        prior.atomic_json(args.output/"failure.json", {"status": "incomplete", "error": str(error),
                          "completed_counts": counts,
                          "possible_unreturned_actor_moves": counts["actor_actions_started"]-counts["actor_evaluation_moves"]})
        raise
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("pool", "reference", "previous", "private", "output"):
        parser.add_argument("--"+name, type=Path, required=True)
    parser.add_argument("--wall-seconds", type=int, default=1200)
    print(json.dumps({"status": run(parser.parse_args())["status"]}))


if __name__ == "__main__":
    main()
