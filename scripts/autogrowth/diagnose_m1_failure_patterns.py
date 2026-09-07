"""Run the isolated M1 failure-pattern diagnostic from a checkout."""
import os
from pathlib import Path
import sys

if os.environ.get("PYTHONHASHSEED") != "0":
    os.environ["PYTHONHASHSEED"] = "0"
    os.execv(sys.executable, [sys.executable, *sys.argv])
for name in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS"):
    os.environ.setdefault(name, "1")
ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT/"src"), str(ROOT/"libs/recon-lite/src")]

from recon_lite_chess.experiments.m1_failure_patterns import main

if __name__ == "__main__":
    main()
