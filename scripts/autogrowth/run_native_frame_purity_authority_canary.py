#!/usr/bin/env python3
from __future__ import annotations
import json
from recon_lite_chess.autogrowth.native_frame_purity_authority_canary import (
    OUTPUT,run_native_frame_purity_authority_canary,
)
def main()->int:
    result=run_native_frame_purity_authority_canary()
    print(json.dumps({"passed":result["passed"],"counts":result["counts_before_gates"],"output":OUTPUT},sort_keys=True))
    return 0
if __name__=="__main__": raise SystemExit(main())
