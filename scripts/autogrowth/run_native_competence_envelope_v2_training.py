#!/usr/bin/env python3
from __future__ import annotations

import json

from recon_lite_chess.autogrowth.native_competence_envelope_v2_training import (
    OUTPUT,
    run_touched_competence_envelope_v2_training,
)


if __name__ == "__main__":
    result = run_touched_competence_envelope_v2_training()
    print(json.dumps({
        "passed": result["passed"],
        "stage": result["stage"],
        "binding_boundary": result.get("binding_boundary"),
        "output": OUTPUT,
        "admission": result["admission"]["counts_before_gates"],
        "connected_final_states": (
            result.get("arms", {})
            .get("connected", {})
            .get("final_state_histogram")
        ),
        "pure_patterns": (
            result.get("post_run_laboratory_diagnostic", {})
            .get("pure_pattern_count")
        ),
    }, sort_keys=True))
