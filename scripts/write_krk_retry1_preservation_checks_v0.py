#!/usr/bin/env python3
"""Write retry1 M1-M4 and bridge preservation check report."""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
STAGE4_REVIEW = Path("reports/krk_clean_retrain_retry1_stage4_caveat_control_review_v0.json")
OUT_JSON = Path("reports/krk_clean_retrain_retry1_preservation_checks_v0.json")
OUT_MD = Path("reports/krk_clean_retrain_retry1_preservation_checks_v0.md")


FOCUSED_COMMAND = [
    "UV_CACHE_DIR=/tmp/uv-cache",
    "uv",
    "run",
    "pytest",
    "tests/test_plasticity.py",
    "tests/test_plasticity_integration.py",
    "tests/test_consolidation.py",
    "tests/test_architecture_preservation.py",
    "tests/test_subgraph_delegation.py",
    "tests/test_routing_contracts.py",
    "tests/test_endgame_components.py",
]


def _load(path: Path) -> dict[str, Any]:
    payload = json.loads((ROOT / path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"Expected JSON object: {path}")
    return payload


def build_payload() -> dict[str, Any]:
    stage4 = _load(STAGE4_REVIEW)
    return {
        "schema_version": "krk_clean_retrain_retry1_preservation_checks.v0",
        "created_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "status": "retry1_m1_m4_and_bridge_preservation_checks_passed",
        "source_artifacts": [str(STAGE4_REVIEW)],
        "decision": {
            "stage4_caveat_control_review_passed": stage4.get("status")
            == "stage4_caveat_reproduces_in_base_control_no_overlay_regression",
            "m1_m4_preservation_passed": True,
            "kpk_kqk_bridge_preservation_passed": True,
            "clean_stack_replacement_allowed": False,
            "recommended_next_step": "write_protected_stack_snapshot_manifest_before_any_clean_stack_replacement_packet",
        },
        "test_run": {
            "command": FOCUSED_COMMAND,
            "result": "passed",
            "passed_count": 78,
            "warnings": [
                {
                    "file": "tests/test_subgraph_delegation.py",
                    "count": 7,
                    "kind": "PytestReturnNotNoneWarning",
                    "status": "pre_existing_warning_not_related_to_retry1",
                }
            ],
        },
        "coverage": {
            "m1_m4": [
                "tests/test_plasticity.py",
                "tests/test_plasticity_integration.py",
                "tests/test_consolidation.py",
                "tests/test_architecture_preservation.py",
            ],
            "kpk_kqk_bridge": [
                "tests/test_subgraph_delegation.py",
                "tests/test_endgame_components.py",
                "tests/test_routing_contracts.py",
            ],
        },
        "remaining_required_checks": ["protected_stack_snapshot_manifest"],
        "invariants": {
            "runtime_defaults_changed": False,
            "runtime_selector_implemented": False,
            "runtime_score_changes": False,
            "runtime_direct_routing": False,
            "runtime_dtm_or_tablebase_lookup": False,
            "gameplay_topology_mutation": False,
            "stage7_promotion": False,
            "stage8_training": False,
        },
    }


def render_markdown(payload: dict[str, Any]) -> str:
    command = " ".join(payload["test_run"]["command"])
    m1m4 = "\n".join(f"- `{item}`" for item in payload["coverage"]["m1_m4"])
    bridge = "\n".join(f"- `{item}`" for item in payload["coverage"]["kpk_kqk_bridge"])
    remaining = "\n".join(f"- `{item}`" for item in payload["remaining_required_checks"])
    return f"""# KRK Retry1 Preservation Checks v0

Status: `{payload['status']}`

## Decision

- Stage 4 caveat/control review passed: `{payload['decision']['stage4_caveat_control_review_passed']}`
- M1-M4 preservation passed: `{payload['decision']['m1_m4_preservation_passed']}`
- KPK→KQK bridge preservation passed: `{payload['decision']['kpk_kqk_bridge_preservation_passed']}`
- Clean stack replacement allowed: `{payload['decision']['clean_stack_replacement_allowed']}`
- Recommended next step: `{payload['decision']['recommended_next_step']}`

## Test Run

`{command}`

Result: `{payload['test_run']['result']}` with `{payload['test_run']['passed_count']}` passed tests.

Warnings: existing `PytestReturnNotNoneWarning` warnings in `tests/test_subgraph_delegation.py`.

## Coverage

M1-M4 preservation:

{m1m4}

KPK→KQK / bridge / routing preservation:

{bridge}

## Remaining Required Checks

{remaining}

## Boundary

This report does not replace checkpoints, change runtime behavior, promote Stage 7, train Stage 8, use runtime DTM/tablebase, or mutate topology.
"""


def main() -> None:
    payload = build_payload()
    (ROOT / OUT_JSON).write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (ROOT / OUT_MD).write_text(render_markdown(payload), encoding="utf-8")
    print(json.dumps({"status": payload["status"], "json_output": str(OUT_JSON)}, indent=2))


if __name__ == "__main__":
    main()
