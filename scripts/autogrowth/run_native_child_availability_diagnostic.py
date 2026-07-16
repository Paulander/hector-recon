#!/usr/bin/env python3
"""Run the retired native R0 child-availability diagnostic."""
from __future__ import annotations

import argparse

from recon_lite_chess.autogrowth.native_child_availability_diagnostic import (
    AvailabilityDiagnosticConfig,
    run_retired_availability_diagnostic,
)


def main() -> int:
    defaults = AvailabilityDiagnosticConfig()
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-artifact", default=defaults.source_artifact)
    parser.add_argument("--organism", default=defaults.organism_path)
    parser.add_argument("--build-report", default=defaults.build_report_path)
    parser.add_argument("--output", default=defaults.output_path)
    parser.add_argument("--r1-row-index", type=int, default=defaults.r1_row_index)
    parser.add_argument("--shuffle-seed", type=int, default=defaults.shuffle_seed)
    args = parser.parse_args()
    config = AvailabilityDiagnosticConfig(
        source_artifact=args.source_artifact, organism_path=args.organism,
        build_report_path=args.build_report, output_path=args.output,
        r1_row_index=args.r1_row_index, shuffle_seed=args.shuffle_seed,
    )
    result = run_retired_availability_diagnostic(config)
    print("wrote", config.output_path)
    print("policy_success_sufficient", result["policy_success_diagnostic_sufficient"])
    print("selected", result["mask_results"]["policy_success"]["selected_parent_action"])
    print("gates", result["gates"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
