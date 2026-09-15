"""Offline capacity/retention summary. Never fits weights into an actor."""
import argparse
import json
from pathlib import Path

from attribute_recursive_retention import capacity_trajectory
from run_recursive_budget import limits, lab


def analyze(out):
    result = json.loads((out / "result.json").read_text())
    if result["status"] != "complete":
        audit = json.loads((out / "independent-verification.json").read_text())
        assert audit["status"] == "verified_complete_after_verifier_correction"
    arms = []
    for arm in result["arms"]:
        directory = out / f"seed-{arm['seed']}/cap-{arm['cap']}"
        initial = lab.load_actor(directory / "start.pkl.gz")
        final = lab.load_actor(directory / "block-001664/checkpoint.pkl.gz")
        topology = lab.summarize_actor(final)
        arms.append({"seed": arm["seed"], "cap": arm["cap"],
                     "initial": arm["initial"]["context_correct"],
                     "middle": arm["evaluations"][2]["context_correct"],
                     "final": arm["evaluations"][-1]["context_correct"],
                     "correct_timeline": [arm["initial"]["correct"], *[e["correct"] for e in arm["evaluations"]]],
                     "retention": arm["retention"], "topology": topology,
                     "new_splits": len(final.splits) - len(initial.splits),
                     "new_prunings": final.pruned - initial.pruned,
                     "new_shallow_births": final.next_condition - initial.next_condition
                         - 2 * (len(final.splits) - len(initial.splits)),
                     "capacity": capacity_trajectory(directory)})
    return {"mode": result["mode"], "actual_training_actions": 0,
            "actual_evaluation_actions": 0, "arms": arms,
            "note": "All LP witnesses are offline; no actor receives fitted weights or selected candidates."}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    limits(120)
    lab.json_once(args.output, analyze(args.run))
