"""Offline row-level acquisition/retention summary; never imported by a learner."""
import argparse
import json
from pathlib import Path

from run_recursive_retention import ROWS, ROLES, SEEDS, json_once


def solved(evaluation, context=None):
    return {r["row"] for r in evaluation["rows"] if r["reward"] > 0
            and (context is None or r["context"] == context)}


def transition(before, after, context=None):
    old, new = solved(before, context), solved(after, context)
    return {"retained": sorted(old & new), "gained": sorted(new - old), "lost": sorted(old - new)}


def analyze(out):
    result = json.loads((out / "result.json").read_text())
    assert result["status"] == "complete", "incomplete runs cannot supply the complete comparison"
    report = {"source": str(out), "arms": [], "aggregates": {}}
    for arm in result["arms"]:
        prefix, middle, final = arm["initial"], arm["evaluations"][2], arm["evaluations"][-1]
        assert [prefix["episode"], middle["episode"], final["episode"]] == [256, 640, 1024]
        newly_learned_b = solved(middle, 1) - solved(prefix, 1)
        row = {"seed": arm["seed"], "role": arm["role"],
               "prefix": prefix["context_correct"], "middle": middle["context_correct"],
               "final": final["context_correct"],
               "first_shift_A": transition(prefix, middle, 0),
               "first_shift_B": transition(prefix, middle, 1),
               "return_A": transition(middle, final, 0),
               "return_B": transition(middle, final, 1),
               "prefix_to_final": transition(prefix, final),
               "new_B_retained_on_return": sorted(newly_learned_b & solved(final, 1)),
               "new_B_lost_on_return": sorted(newly_learned_b - solved(final, 1)),
               "consecutive_transitions": [], "final_structure": arm["structures"][-1]}
        previous = prefix
        for evaluation in arm["evaluations"]:
            row["consecutive_transitions"].append({"from": previous["episode"], "to": evaluation["episode"],
                                                  **transition(previous, evaluation)})
            previous = evaluation
        report["arms"].append(row)
    for role in ROLES:
        rows = [r for r in report["arms"] if r["role"] == role]
        aggregate = {name: [sum(r[name][c] for r in rows) for c in (0, 1)]
                     for name in ("prefix", "middle", "final")}
        for phase in ("first_shift_A", "first_shift_B", "return_A", "return_B", "prefix_to_final"):
            aggregate[phase] = {measure: sum(len(r[phase][measure]) for r in rows)
                                for measure in ("retained", "gained", "lost")}
        for measure in ("new_B_retained_on_return", "new_B_lost_on_return"):
            aggregate[measure] = sum(len(r[measure]) for r in rows)
        report["aggregates"][role] = aggregate
    return report


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    report = analyze(args.run)
    json_once(args.output, report)
    print(json.dumps({"aggregates": report["aggregates"], "arms": [
        {key: row[key] for key in ("seed", "role", "prefix", "middle", "final")}
        for row in report["arms"]]}, indent=2))
