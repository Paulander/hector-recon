"""Run TG26j curated KRK terminal curriculum checkpoint."""

from __future__ import annotations

import argparse
from pathlib import Path

from recon_lite_chess.autogrowth import (
    CuratedTerminalCurriculumConfig,
    run_curated_terminal_curriculum,
)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--output",
        default="reports/autogrowth/krk_autogrowth_tg26j_curated_terminal_curriculum.json",
    )
    parser.add_argument("--train-repetitions", type=int, default=3)
    parser.add_argument("--max-samples", type=int, default=24)
    args = parser.parse_args()

    result = run_curated_terminal_curriculum(
        config=CuratedTerminalCurriculumConfig(
            train_repetitions=args.train_repetitions,
            max_samples=args.max_samples,
        )
    )
    output = result.write_json(Path(args.output))
    payload = result.to_dict()
    print(f"wrote {output}")
    print(
        "original Mate2 conversion",
        payload["original_position_run"]["mate2"]["evaluation"]["conversion_count"],
        "/",
        payload["original_position_run"]["mate2"]["evaluation"]["position_count"],
    )
    print(
        "symmetry Mate2 conversion",
        payload["symmetry_expanded_run"]["mate2"]["evaluation"]["conversion_count"],
        "/",
        payload["symmetry_expanded_run"]["mate2"]["evaluation"]["position_count"],
    )
    print("symmetry interference", payload["interpretation"]["symmetry_interference_flag"])


if __name__ == "__main__":
    main()
