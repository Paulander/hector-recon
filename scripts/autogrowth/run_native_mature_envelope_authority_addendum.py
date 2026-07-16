#!/usr/bin/env python3
from __future__ import annotations

import json

from recon_lite_chess.autogrowth.native_mature_envelope_authority_addendum import (
    run_native_mature_envelope_authority_addendum,
)


if __name__ == "__main__":
    result = run_native_mature_envelope_authority_addendum()
    print(json.dumps({
        "passed": result["passed"],
        "output": (
            "reports/autogrowth/native_authority/"
            "native_mature_envelope_authority_addendum.json"
        ),
        "full_frame_hash": result["full_frame_input_parity"]["natural_sha256"],
        "connected_action": (
            result["mature_envelope_authority"]["decisions"]["connected_action"]
        ),
    }, sort_keys=True))
