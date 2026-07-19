#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json

from recon_lite_chess.autogrowth.native_mature_cell_falsification import (
    generate_control_manifest,
    generate_instrument_repair_manifest,
    run_package,
)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=("manifest", "repair-manifest", "run"))
    parser.add_argument("--preregistration-commit")
    parser.add_argument("--repair-commit")
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
    elif args.mode == "repair-manifest":
        if not args.repair_commit:
            parser.error("repair-manifest mode requires --repair-commit")
        result = generate_instrument_repair_manifest(args.repair_commit)
        summary = {
            "manifest_payload_sha256": result["manifest_payload_sha256"],
            "abort_result_sha256": result["abort_result_sha256"],
            "abort_organism_index_sha256": result["abort_organism_index"][
                "index_sha256"
            ],
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
