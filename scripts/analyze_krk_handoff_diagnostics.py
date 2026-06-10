#!/usr/bin/env python3
"""Analyze KRK handoff diagnostic JSON files.

This is intentionally offline and non-causal: it reads diagnostic traces and
shadow-candidate logs, then emits a compact JSON or Markdown report.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from recon_lite_chess.routing import analyze_handoff_files


def main() -> int:
    parser = argparse.ArgumentParser(description="Analyze KRK handoff diagnostics")
    parser.add_argument("diagnostics", nargs="+", type=Path,
                        help="Diagnostic JSON files emitted by test_krk_landmark_progress.py")
    parser.add_argument("--shadow-candidates", nargs="*", type=Path, default=[],
                        help="Optional shadow-candidate JSONL files")
    parser.add_argument("--format", choices=["markdown", "json"], default="markdown")
    parser.add_argument("--output", type=Path, default=None)
    args = parser.parse_args()

    analysis = analyze_handoff_files(args.diagnostics, shadow_paths=args.shadow_candidates)
    if args.format == "json":
        content = json.dumps(analysis.to_dict(), indent=2) + "\n"
    else:
        content = analysis.to_markdown()

    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(content, encoding="utf-8")
    else:
        print(content, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
