#!/usr/bin/env python3
"""Portable entry point for the offline matched growth comparison."""
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

from recon_lite_chess.experiments.mate_one_attribution import main

if __name__ == "__main__":
    main()
