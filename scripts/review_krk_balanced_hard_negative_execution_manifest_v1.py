#!/usr/bin/env python3
"""Review v1 balanced hard-negative execution manifest before labels."""

from __future__ import annotations

import importlib.util
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "review_krk_balanced_hard_negative_execution_manifest_v0.py"
SPEC = importlib.util.spec_from_file_location("_balanced_review_v0", SCRIPT)
assert SPEC is not None and SPEC.loader is not None
module = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(module)

module.MANIFEST = Path("reports/krk_balanced_hard_negative_execution_manifest_v1.json")
module.OUT_JSON = Path("reports/krk_balanced_hard_negative_execution_manifest_review_v1.json")
module.OUT_MD = Path("reports/krk_balanced_hard_negative_execution_manifest_review_v1.md")


if __name__ == "__main__":
    module.main()
