"""Run TG26k cumulative curated replay curriculum checkpoint."""

from __future__ import annotations

import argparse
from pathlib import Path

from recon_lite_chess.autogrowth import (
    CuratedReplayCurriculumConfig,
    run_curated_replay_curriculum,
)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--output",
        default="reports/autogrowth/krk_autogrowth_tg26k_curated_replay_curriculum.json",
    )
    parser.add_argument("--train-repetitions", type=int, default=5)
    parser.add_argument("--replay-repetitions", type=int, default=2)
    parser.add_argument("--max-samples", type=int, default=32)
    parser.add_argument("--no-symmetries", action="store_true")
    args = parser.parse_args()

    result = run_curated_replay_curriculum(
        config=CuratedReplayCurriculumConfig(
            train_repetitions=args.train_repetitions,
            replay_repetitions=args.replay_repetitions,
            max_samples=args.max_samples,
            include_symmetries=not args.no_symmetries,
        )
    )
    output = result.write_json(Path(args.output))
    payload = result.to_dict()
    final = payload["final_evaluation"]
    print(f"wrote {output}")
    print(
        "mate1",
        final["mate1"]["correct_count"],
        "/",
        final["mate1"]["position_count"],
    )
    print(
        "mate2",
        final["mate2"]["conversion_count"],
        "/",
        final["mate2"]["position_count"],
    )
    print("checkpoint_pass", payload["decision"]["checkpoint_pass"])
    print("m4_mate2", payload["decision"]["m4_mate2_consolidation_event_count"])


if __name__ == "__main__":
    main()
