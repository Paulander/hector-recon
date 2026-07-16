from __future__ import annotations

import importlib.util
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts/autogrowth/run_virtual_frame_child_response_canary.py"
ARTIFACT = ROOT / "reports/autogrowth/virtual_frame_child_response_canary_v3_20260716.json"


def _module():
    spec = importlib.util.spec_from_file_location("virtual_frame_canary", SCRIPT)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_virtual_frame_child_response_canary_is_deterministic_and_complete() -> None:
    module = _module()
    first = module.run_canary()
    second = module.run_canary()
    assert first == second
    assert first["all_checks_pass"] is True
    assert all(first["checks"].values())
    assert first["baseline"]["selected_action"] == "advance"
    assert first["controls"]["shuffled_child_response"]["selected_action"] == "stall"
    assert first["baseline"]["real_actuator_calls"] == ["advance"]
    assert first["controls"]["dream_state_leakage"]["rolled_back"] is True
    assert first["controls"]["self_credit_attempt"]["effect_attempts"][0]["operation"] == "set_maturity"


def test_committed_canary_artifact_matches_live_deterministic_result() -> None:
    module = _module()
    assert json.loads(ARTIFACT.read_text()) == module.run_canary()
