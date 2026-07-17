#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json

from recon_lite_chess.autogrowth.native_competence_envelope_v3b_seed_robustness import (
    generate_seed_manifest,
)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--preregistration-commit", required=True)
    parser.add_argument("--output")
    args = parser.parse_args()
    kwargs = {} if args.output is None else {"output": args.output}
    result = generate_seed_manifest(
        args.preregistration_commit,
        **kwargs,
    )
    print(json.dumps({
        "seed_count": result["seed_count"],
        "seed_list_sha256": result["seed_list_sha256"],
        "minimum_seed": min(row["seed"] for row in result["seeds"]),
    }, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
