#!/usr/bin/env python3
from __future__ import annotations

import json

from recon_lite_chess.autogrowth.native_competence_envelope_v3b_seed_robustness import (
    run_v3b_seed_robustness,
)


if __name__ == "__main__":
    result = run_v3b_seed_robustness()
    print(json.dumps({
        "stage": result["stage"],
        "completed_seed_count": result["completed_seed_count"],
        "cohort_counts": result["cohort_counts"],
        "adjudication": result["adjudication"],
        "passed_integrity": result["passed_integrity"],
        "next_action": result["next_action"],
    }, indent=2, sort_keys=True))
