#!/usr/bin/env python3
"""Portable entry point without installing the repository's Torch dependency."""

import os
from pathlib import Path
import sys

if os.environ.get("PYTHONHASHSEED") != "0":
    os.environ["PYTHONHASHSEED"] = "0"
    os.execv(sys.executable, [sys.executable, *sys.argv])
for name in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS"):
    os.environ.setdefault(name, "1")
root = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(root / "src"), str(root / "libs/recon-lite/src")]

from recon_lite_chess.coach.runner import main

if __name__ == "__main__":
    main()
