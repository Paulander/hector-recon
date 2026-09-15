"""Resolve the recorded post-run pickle-set-order assertion without more training."""
import argparse
import ast
import json
from pathlib import Path

import run_recursive_budget as budget


def verify(out):
    report = json.loads((out / "result.json").read_text())
    assert report["status"] == "incomplete"
    assert report["error"] == "AssertionError: fork changed actor state"
    hashes = json.loads((out / "source.json").read_text())
    runner = "scripts/autogrowth/run_recursive_budget.py"
    for relative, expected in hashes.items():
        assert budget.lab.digest((out / "source-snapshot" / relative).read_bytes()) == expected
        if relative != runner:
            assert budget.lab.digest((budget.lab.ROOT / relative).read_bytes()) == expected, relative
    before = ast.parse((out / "source-snapshot" / runner).read_text())
    after = ast.parse((budget.lab.ROOT / runner).read_text())
    assert len(before.body) == len(after.body)
    changed = []
    for old, new in zip(before.body, after.body):
        if ast.dump(old) != ast.dump(new):
            assert isinstance(old, ast.FunctionDef) and isinstance(new, ast.FunctionDef)
            assert old.name == new.name and old.name in ("verify_fork", "verify_run")
            changed.append(old.name)
    assert set(changed) == {"verify_fork", "verify_run"}
    counts = budget.verify_run(out, re_evaluate=True, source_root=out / "source-snapshot")
    return {"status": "verified_complete_after_verifier_correction",
            "original_status": report["status"], "original_error": report["error"],
            "changed_runner_functions": changed,
            "original_runner_sha256": hashes[runner],
            "verification_runner_sha256": budget.lab.digest((budget.lab.ROOT / runner).read_bytes()),
            "verification": counts, "new_training_actions": 0,
            "note": "Equal seen-expression sets serialized in different orders; compare their values. Original report and all payloads are unchanged."}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run", type=Path, required=True)
    args = parser.parse_args()
    budget.limits(120)
    result = verify(args.run)
    budget.lab.json_once(args.run / "independent-verification.json", result)
    print(json.dumps(result), flush=True)
