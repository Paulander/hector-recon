#!/usr/bin/env python3
from __future__ import annotations

import json

from recon_lite_chess.autogrowth.native_competence_envelope_v3_training import (
    run_touched_competence_envelope_v3_training,
)


if __name__ == "__main__":
    result = run_touched_competence_envelope_v3_training()
    print(json.dumps({
        "passed": result["passed"],
        "stage": result["stage"],
        "binding_boundary": result.get("binding_boundary"),
        "admission": result["admission"]["counts_before_gates"],
        "parity_mismatch_count": result["admission"]["parity_mismatch_count"],
        "next_action": result["next_action"],
    }, indent=2, sort_keys=True))
