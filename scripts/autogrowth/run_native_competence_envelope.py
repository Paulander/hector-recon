#!/usr/bin/env python3
from __future__ import annotations
import json
from recon_lite_chess.autogrowth.native_competence_envelope_experiment import (
    CompetenceExperimentConfig, run_touched_competence_envelope,
)

def main() -> int:
    result=run_touched_competence_envelope(CompetenceExperimentConfig())
    print(json.dumps({
        "passed":result.get("passed"),
        "stage":result.get("stage"),
        "binding_boundary":result.get("binding_boundary"),
        "output":CompetenceExperimentConfig().output,
    },sort_keys=True))
    return 0

if __name__=="__main__":
    raise SystemExit(main())
