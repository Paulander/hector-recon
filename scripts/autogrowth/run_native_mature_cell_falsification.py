#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json

from recon_lite_chess.autogrowth.native_mature_cell_falsification import (
    generate_control_manifest,
    run_package,
)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=("manifest", "run"))
    parser.add_argument("--preregistration-commit")
    parser.add_argument("--max-workers", type=int, default=4)
    args = parser.parse_args()
    if args.mode == "manifest":
        if not args.preregistration_commit:
            parser.error("manifest mode requires --preregistration-commit")
        result = generate_control_manifest(args.preregistration_commit)
        summary = {
            "manifest_payload_sha256": result["manifest_payload_sha256"],
            "organism_count": result["organism_count"],
        }
    else:
        result = run_package(max_workers=args.max_workers)
        summary = {
            "stage": result["stage"],
            "integrity_passed": result["integrity_passed"],
            "mechanism_passed": result["mechanism_passed"],
            "scientific_passed": result["scientific_passed"],
            "adjudication": result.get("adjudication"),
        }
    print(json.dumps(summary, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
