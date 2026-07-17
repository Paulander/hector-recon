#!/usr/bin/env python3
from __future__ import annotations

import json

from recon_lite_chess.autogrowth.deterministic_native_activation_closure import (
    run_deterministic_native_activation_closure,
)


if __name__ == "__main__":
    result = run_deterministic_native_activation_closure()
    print(json.dumps({
        "passed": result["passed"],
        "counts": result["counts_before_gates"],
        "mismatch_count": result["field_level_mismatch_count"],
        "next_action": result["next_action"],
    }, indent=2, sort_keys=True))
