"""Run Stockfish validation for curated KRK mate-in-two claims."""

from __future__ import annotations

import argparse
from pathlib import Path

from recon_lite_chess.autogrowth.curated_stockfish_validation import (
    CuratedStockfishValidationConfig,
    default_stockfish_path,
    run_curated_stockfish_validation,
)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--stockfish-path", default=default_stockfish_path())
    parser.add_argument("--depth", type=int, default=16)
    parser.add_argument("--no-symmetries", action="store_true")
    parser.add_argument(
        "--output",
        default="reports/autogrowth/krk_autogrowth_tg26j_stockfish_mate2_validation.json",
    )
    args = parser.parse_args()
    if not args.stockfish_path:
        raise SystemExit("Stockfish not found. Pass --stockfish-path or set STOCKFISH_PATH.")

    result = run_curated_stockfish_validation(
        config=CuratedStockfishValidationConfig(
            stockfish_path=args.stockfish_path,
            depth=args.depth,
            include_symmetries=not args.no_symmetries,
        )
    )
    output = result.write_json(Path(args.output))
    payload = result.to_dict()
    print(f"wrote {output}")
    print("engine", payload["engine"])
    print("total", payload["summary"]["total_claim_entries"])
    print("stockfish", payload["summary"]["stockfish_classification_counts"])
    print("exact", payload["summary"]["exact_classification_counts"])
    print(
        "strict stockfish+exact mate2",
        payload["summary"]["strict_stockfish_and_exact_mate_in_2_count"],
    )


if __name__ == "__main__":
    main()
