#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json

from recon_lite_chess.autogrowth.native_competence_envelope_formal_or_corrected_replication import (
    run_corrected_replication,
    run_repair_replay,
)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "mode",
        choices=("replay", "replicate", "all"),
        default="all",
        nargs="?",
    )
    parser.add_argument("--max-workers", type=int, default=4)
    args = parser.parse_args()
    summary = {}
    if args.mode in {"replay", "all"}:
        replay = run_repair_replay(max_workers=args.max_workers)
        summary["repair_replay"] = {
            "stage": replay["stage"],
            "passed": replay["passed"],
            "observed": replay["observed"],
        }
        if not replay["passed"]:
            print(json.dumps(summary, indent=2, sort_keys=True))
            return
    if args.mode in {"replicate", "all"}:
        result = run_corrected_replication(max_workers=args.max_workers)
        summary["corrected_replication"] = {
            "stage": result["stage"],
            "passed": result["passed"],
            "cohort_counts": result.get("cohort_counts"),
            "adjudication": result.get("adjudication"),
            "corrected_validation_opened": result.get(
                "corrected_validation_opened", False
            ),
        }
    print(json.dumps(summary, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
