#!/usr/bin/env python3
"""Run TG47g frozen-foundation handoff reachability audit."""

from __future__ import annotations

import argparse
import json

from recon_lite_chess.autogrowth import HandoffReachabilityAuditConfig, run_handoff_reachability_audit


DEFAULT_OUTPUT_DIR = "reports/autogrowth/clean_slate_krk/tg47g_handoff_reachability_audit"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--max-positions", type=int, default=None)
    parser.add_argument("--selected-second-move-cap", type=int, default=3)
    parser.add_argument("--oracle-first-move-cap", type=int, default=3)
    parser.add_argument("--oracle-second-move-cap", type=int, default=3)
    args = parser.parse_args()

    output_dir = args.output_dir
    config = HandoffReachabilityAuditConfig(
        output_dir=output_dir,
        output_path=f"{output_dir}/krk_tg47g_handoff_reachability_audit.json",
        markdown_path=f"{output_dir}/krk_tg47g_handoff_reachability_audit.md",
        audit_trace_path=f"{output_dir}/pools/tg47g_handoff_audit.jsonl.gz",
        boundary_failure_path=f"{output_dir}/pools/tg47g_boundary_failures.jsonl.gz",
        max_positions=args.max_positions,
        selected_second_move_cap=args.selected_second_move_cap,
        oracle_first_move_cap=args.oracle_first_move_cap,
        oracle_second_move_cap=args.oracle_second_move_cap,
    )
    result = run_handoff_reachability_audit(config=config)
    print(json.dumps(result.decision, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
