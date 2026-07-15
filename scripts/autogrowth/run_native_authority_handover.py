#!/usr/bin/env python3
"""Build retired R0 organism and run bounded native authority development."""
from __future__ import annotations

import argparse

from recon_lite_chess.autogrowth.native_authority_lab import (
    NativeAuthorityLabConfig,
    build_retired_r0_organism,
    load_retired_r0_build,
    run_retired_handover_development,
)


def main() -> int:
    defaults = NativeAuthorityLabConfig()
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-artifact", default=defaults.source_artifact)
    parser.add_argument("--organism", default=defaults.organism_path)
    parser.add_argument("--build-report", default=defaults.build_report_path)
    parser.add_argument("--result", default=defaults.result_path)
    parser.add_argument("--train-rows", type=int, default=defaults.train_rows)
    parser.add_argument("--evaluation-rows", type=int, default=defaults.evaluation_rows)
    parser.add_argument("--train-epochs", type=int, default=defaults.train_epochs)
    parser.add_argument("--shuffle-seed", type=int, default=defaults.shuffle_seed)
    parser.add_argument("--build-only", action="store_true")
    parser.add_argument("--reuse-organism", action="store_true")
    args = parser.parse_args()
    config = NativeAuthorityLabConfig(
        source_artifact=args.source_artifact,
        organism_path=args.organism,
        build_report_path=args.build_report,
        result_path=args.result,
        train_rows=args.train_rows,
        evaluation_rows=args.evaluation_rows,
        train_epochs=args.train_epochs,
        shuffle_seed=args.shuffle_seed,
    )
    build = (
        load_retired_r0_build(config)
        if args.reuse_organism
        else build_retired_r0_organism(config)
    )
    print("R0 organism", config.organism_path)
    print("R0 parity", build.report["serialization_parity"]["all_equal"])
    if args.build_only:
        return 0
    result = run_retired_handover_development(build, config)
    print("development result", config.result_path)
    print("passed", result["passed"], "boundary", result["binding_boundary"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
