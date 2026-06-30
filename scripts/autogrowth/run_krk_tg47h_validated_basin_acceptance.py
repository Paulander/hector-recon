#!/usr/bin/env python3
"""Run TG47h validated foundation-basin acceptance audit."""

from __future__ import annotations

import argparse
import json

from recon_lite_chess.autogrowth import (
    ValidatedBasinAcceptanceConfig,
    run_validated_basin_acceptance,
)


DEFAULT_OUTPUT_DIR = "reports/autogrowth/clean_slate_krk/tg47h_validated_basin_acceptance"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--max-positions", type=int, default=None)
    parser.add_argument("--selected-second-move-cap", type=int, default=3)
    parser.add_argument("--oracle-first-move-cap", type=int, default=3)
    parser.add_argument("--oracle-second-move-cap", type=int, default=3)
    args = parser.parse_args()

    output_dir = args.output_dir
    config = ValidatedBasinAcceptanceConfig(
        output_dir=output_dir,
        output_path=f"{output_dir}/krk_tg47h_validated_basin_acceptance.json",
        markdown_path=f"{output_dir}/krk_tg47h_validated_basin_acceptance.md",
        audit_trace_path=f"{output_dir}/pools/tg47h_validated_handoff_audit.jsonl.gz",
        quarantine_path=f"{output_dir}/pools/tg47h_false_basin_quarantine.jsonl.gz",
        max_positions=args.max_positions,
        selected_second_move_cap=args.selected_second_move_cap,
        oracle_first_move_cap=args.oracle_first_move_cap,
        oracle_second_move_cap=args.oracle_second_move_cap,
    )
    result = run_validated_basin_acceptance(config=config)
    print(json.dumps(result.decision, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
