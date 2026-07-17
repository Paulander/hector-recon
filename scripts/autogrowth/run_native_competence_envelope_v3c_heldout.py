#!/usr/bin/env python3
from __future__ import annotations

import json

from recon_lite_chess.autogrowth.native_competence_envelope_v3c_heldout import (
    run_v3c,
)


if __name__ == "__main__":
    result = run_v3c()
    summary = {
        "stage": result["stage"],
        "interpretation": result["interpretation"],
        "binding_boundary": result["binding_boundary"],
        "regression_inference_opened": result["regression_inference_opened"],
        "validation_admission": result["validation"]["admission"]["passed"],
        "validation_verdicts": result["validation"].get("verdicts"),
        "regression_admission": (
            None if result["regression"] is None
            else result["regression"]["admission"]["passed"]
        ),
        "regression_verdicts": (
            None if result["regression"] is None
            else result["regression"].get("verdicts")
        ),
        "passed": result["passed"],
    }
    print(json.dumps(summary, indent=2, sort_keys=True))
