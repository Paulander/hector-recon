#!/usr/bin/env python3
"""Bind v1 balanced hard-negative jobs for reviewed execution."""

from __future__ import annotations

import importlib.util
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "build_krk_balanced_hard_negative_execution_manifest_v0.py"
SPEC = importlib.util.spec_from_file_location("_balanced_manifest_v0", SCRIPT)
assert SPEC is not None and SPEC.loader is not None
module = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(module)

module.PLAN = Path("reports/krk_balanced_hard_negative_label_plan_v1.json")
module.OUT_JSON = Path("reports/krk_balanced_hard_negative_execution_manifest_v1.json")
module.OUT_MD = Path("reports/krk_balanced_hard_negative_execution_manifest_v1.md")


if __name__ == "__main__":
    module.main()
