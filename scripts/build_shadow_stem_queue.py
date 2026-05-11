#!/usr/bin/env python3
"""Build an offline priority queue from shadow stem candidates."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from recon_lite_chess.routing import build_shadow_stem_queue_from_files


def main() -> int:
    parser = argparse.ArgumentParser(description="Build a shadow stem candidate queue")
    parser.add_argument("inputs", nargs="+", type=Path,
                        help="Diagnostic JSON files or shadow-candidate JSONL files")
    parser.add_argument("--output", type=Path, default=None)
    parser.add_argument("--limit", type=int, default=0,
                        help="If >0, only keep this many queue items in the output")
    args = parser.parse_args()

    queue = build_shadow_stem_queue_from_files(args.inputs).to_dict()
    if args.limit > 0:
        queue["queue"] = queue["queue"][:args.limit]
    content = json.dumps(queue, indent=2) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(content, encoding="utf-8")
    else:
        print(content, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
