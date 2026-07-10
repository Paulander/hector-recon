from __future__ import annotations

import argparse
import json

from recon_lite_chess.autogrowth.krk_preregistered_closure import (
    ClosureConfig,
    PoolCapacityError,
    generate_fresh_pools,
    run_krk_preregistered_closure,
)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Run the single preregistered v1 KRK ecological closure."
    )
    parser.add_argument(
        "--output-dir",
        default="reports/autogrowth/krk_preregistered_closure",
    )
    parser.add_argument("--generate-only", action="store_true")
    parser.add_argument("--force-pools", action="store_true")
    args = parser.parse_args()
    config = ClosureConfig(output_dir=args.output_dir)
    if args.generate_only:
        try:
            manifest = generate_fresh_pools(config=config, force=args.force_pools)
        except PoolCapacityError as exc:
            print(str(exc))
            raise SystemExit(2) from None
        print(json.dumps({"splits": manifest["splits"]}, sort_keys=True))
        return
    result = run_krk_preregistered_closure(config=config)
    print(
        json.dumps(
            {
                "measurement_gate": result["measurement_gate"]["passed"],
                "coverage_gate": result["coverage_gate"]["adequate_by_topology"],
                "validation_freeze_gate": result["validation"]["freeze_gate_passed"],
                "final_test_touch_count": result["final_test"]["touch_count"],
                "interpretation": result["interpretation"],
            },
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
