#!/usr/bin/env python3
"""Run TG48a2 same-side/hard-decoy diagnostic."""

from __future__ import annotations

import argparse
import json

from recon_lite_chess.autogrowth import (
    TG48a2SameSideDiagnosticConfig,
    run_tg48a2_same_side_diagnostic,
)


DEFAULT_OUTPUT_DIR = "reports/autogrowth/clean_slate_krk/tg48a2_same_side_diagnostic"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--seed", type=int, default=20260701)
    parser.add_argument("--same-side-count", type=int, default=48)
    parser.add_argument("--max-generation-attempts", type=int, default=250_000)
    parser.add_argument("--top-rejected-affordance-count", type=int, default=20)
    args = parser.parse_args()

    output_dir = args.output_dir
    config = TG48a2SameSideDiagnosticConfig(
        output_dir=output_dir,
        output_path=f"{output_dir}/krk_tg48a2_same_side_diagnostic.json",
        markdown_path=f"{output_dir}/krk_tg48a2_same_side_diagnostic.md",
        hard_decoy_relabel_path=f"{output_dir}/pools/tg48a2_hard_decoy_relabel_audit.jsonl.gz",
        hard_decoy_markdown_path=f"{output_dir}/tg48a2_hard_decoy_relabel_audit.md",
        same_side_slice_path=f"{output_dir}/pools/tg48a2_same_side_slice.jsonl.gz",
        same_side_markdown_path=f"{output_dir}/tg48a2_same_side_slice.md",
        terminal_precision_path=f"{output_dir}/pools/tg48a2_terminal_precision_audit.jsonl.gz",
        seed=args.seed,
        same_side_count=args.same_side_count,
        max_generation_attempts=args.max_generation_attempts,
        top_rejected_affordance_count=args.top_rejected_affordance_count,
    )
    result = run_tg48a2_same_side_diagnostic(config=config)
    print(json.dumps(result.decision, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
