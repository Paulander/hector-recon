#!/usr/bin/env python3
"""Refresh sequence-policy artifacts after protected failure-contrast integration.

This passive refresh runs after protected failure-contrast output validation
and integration. It lets future explicitly approved collection outputs flow
into benchmark inputs and review without changing runtime behavior, training
selectors, promoting Stage 7, or training Stage 8.
"""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
INTEGRATION = (
    ROOT
    / "reports/strategy_arbitration/"
    "krk_protected_plan_window_failure_contrast_integration_v0.json"
)
OUTPUT_JSON = (
    ROOT
    / "reports/strategy_arbitration/"
    "krk_sequence_policy_after_protected_failure_contrast_refresh_v0.json"
)
OUTPUT_MD = (
    ROOT
    / "reports/strategy_arbitration/"
    "krk_sequence_policy_after_protected_failure_contrast_refresh_v0.md"
)

SCHEMA_VERSION = "krk_sequence_policy_after_protected_failure_contrast_refresh.v0"

COMMON_FALSE_FLAGS = {
    "runtime_behavior_changed": False,
    "runtime_defaults_changed": False,
    "runtime_selector_implemented": False,
    "runtime_score_changes": False,
    "runtime_direct_routing": False,
    "runtime_dtm_or_tablebase_lookup": False,
    "gameplay_topology_mutation": False,
    "stage7_promotion_allowed": False,
    "stage8_training_allowed": False,
}

BOUNDARY_FIELDS = (
    "runtime_changes_allowed",
    "label_run_allowed",
    "selector_training_allowed",
    "stage7_promotion_allowed",
    "stage8_training_allowed",
)

STEPS = [
    {
        "step_id": "sequence_policy_inputs",
        "script": "scripts/assemble_krk_sequence_policy_benchmark_inputs_v0.py",
        "output_json": "reports/strategy_arbitration/krk_sequence_policy_benchmark_inputs_v0.json",
    },
    {
        "step_id": "sequence_policy_input_probe",
        "script": "scripts/probe_krk_sequence_policy_inputs_v0.py",
        "output_json": "reports/strategy_arbitration/krk_sequence_policy_input_probe_v0.json",
    },
    {
        "step_id": "sequence_policy_benchmark",
        "script": "scripts/run_krk_sequence_policy_benchmark_v0.py",
        "output_json": "reports/strategy_arbitration/krk_sequence_policy_benchmark_v0.json",
    },
    {
        "step_id": "sequence_policy_benchmark_review",
        "script": "scripts/review_krk_sequence_policy_benchmark_v0.py",
        "output_json": "reports/strategy_arbitration/krk_sequence_policy_benchmark_review_v0.json",
    },
]


def _load_module(path: Path):
    spec = importlib.util.spec_from_file_location(path.stem, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load script module: {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _load(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise TypeError(f"{path} must contain a JSON object")
    return data


def _load_relative(path: str) -> dict[str, Any]:
    return _load(ROOT / path)


def build_payload() -> dict[str, Any]:
    integration = _load(INTEGRATION)
    step_results = []
    for step in STEPS:
        module = _load_module(ROOT / step["script"])
        if not hasattr(module, "main"):
            raise RuntimeError(f"script has no main(): {step['script']}")
        module.main()
        output = _load_relative(step["output_json"])
        decision = output.get("decision") or {}
        step_results.append(
            {
                "step_id": step["step_id"],
                "script": step["script"],
                "output_json": step["output_json"],
                "decision_status": decision.get("status"),
                "runtime_changes_allowed": bool(decision.get("runtime_changes_allowed", False)),
                "label_run_allowed": bool(decision.get("label_run_allowed", False)),
                "selector_training_allowed": bool(
                    decision.get("selector_training_allowed", False)
                ),
                "stage7_promotion_allowed": bool(decision.get("stage7_promotion_allowed", False)),
                "stage8_training_allowed": bool(decision.get("stage8_training_allowed", False)),
            }
        )

    inputs = _load_relative("reports/strategy_arbitration/krk_sequence_policy_benchmark_inputs_v0.json")
    benchmark = _load_relative("reports/strategy_arbitration/krk_sequence_policy_benchmark_v0.json")
    review = _load_relative("reports/strategy_arbitration/krk_sequence_policy_benchmark_review_v0.json")
    integration_summary = integration.get("summary") or {}
    input_summary = inputs.get("summary") or {}
    boundary_violations = [
        {"step_id": result["step_id"], "field": field, "script": result["script"]}
        for result in step_results
        for field in BOUNDARY_FIELDS
        if result[field]
    ]
    all_boundaries_preserved = not boundary_violations
    integration_ready = bool(integration_summary.get("integration_ready"))
    protected_failure_rows = int(input_summary.get("protected_failure_contrast_row_count") or 0)
    status = (
        "sequence_policy_after_protected_failure_contrast_refresh_blocked_boundary_violation"
        if not all_boundaries_preserved
        else "sequence_policy_after_protected_failure_contrast_refresh_ready_for_review"
        if integration_ready and protected_failure_rows > 0
        else "sequence_policy_after_protected_failure_contrast_refresh_waiting_on_integration_outputs"
    )
    return {
        "schema_version": SCHEMA_VERSION,
        "causal_status": "non_causal_post_failure_contrast_sequence_policy_refresh",
        **COMMON_FALSE_FLAGS,
        "source_artifacts": [
            "reports/strategy_arbitration/krk_protected_plan_window_failure_contrast_integration_v0.json",
            "reports/strategy_arbitration/krk_sequence_policy_benchmark_inputs_v0.json",
            "reports/strategy_arbitration/krk_sequence_policy_benchmark_v0.json",
            "reports/strategy_arbitration/krk_sequence_policy_benchmark_review_v0.json",
        ],
        "source_scripts": [step["script"] for step in STEPS],
        "step_results": step_results,
        "summary": {
            "all_boundaries_preserved": all_boundaries_preserved,
            "boundary_violation_count": len(boundary_violations),
            "boundary_violations": boundary_violations,
            "integration_status": integration.get("decision", {}).get("status"),
            "integration_ready": integration_ready,
            "integrated_new_failure_count": integration_summary.get(
                "integrated_new_failure_count"
            ),
            "protected_failure_contrast_row_count": protected_failure_rows,
            "sequence_policy_input_row_count": input_summary.get("row_count"),
            "sequence_policy_benchmark_status": benchmark.get("decision", {}).get("status"),
            "sequence_policy_benchmark_review_status": review.get("decision", {}).get("status"),
            "stage7_training_row_count": 0,
            "selector_training_row_count": input_summary.get("selector_training_row_count"),
            "runtime_authorization_row_count": input_summary.get(
                "runtime_authorization_row_count"
            ),
        },
        "decision": {
            "status": status,
            "recommended_next_step": (
                "inspect_post_protected_failure_contrast_refresh_boundary_violation"
                if not all_boundaries_preserved
                else
                "review_non_causal_sequence_policy_benchmark_with_protected_failure_contrasts"
                if integration_ready and protected_failure_rows > 0
                else "explicitly_approve_protected_plan_window_failure_contrast_collection"
            ),
            "runtime_changes_allowed": False,
            "label_run_allowed": False,
            "selector_allowed": False,
            "selector_training_allowed": False,
            "stage7_promotion_allowed": False,
            "stage8_training_allowed": False,
        },
    }


def write_markdown(payload: dict[str, Any]) -> str:
    summary = payload["summary"]
    decision = payload["decision"]
    lines = [
        "# KRK Sequence Policy After Protected Failure Contrast Refresh v0",
        "",
        f"Status: `{decision['status']}`",
        "",
        "This passive refresh consumes integrated protected failure contrasts when available. It does not execute collection, change runtime behavior, train selectors, promote Stage 7, or train Stage 8.",
        "",
        "## Summary",
        "",
    ]
    for key, value in summary.items():
        lines.append(f"- {key}: `{value}`")
    lines.extend(["", "## Steps", ""])
    for result in payload["step_results"]:
        lines.append(
            f"- `{result['step_id']}` status=`{result['decision_status']}` labels=`{result['label_run_allowed']}` runtime=`{result['runtime_changes_allowed']}`"
        )
    lines.extend(
        [
            "",
            "## Decision",
            "",
            f"- recommended_next_step: `{decision['recommended_next_step']}`",
            "- runtime_changes_allowed: `false`",
            "- label_run_allowed: `false`",
            "- selector_training_allowed: `false`",
            "- Stage 7 promotion and Stage 8 training remain blocked.",
        ]
    )
    return "\n".join(lines) + "\n"


def main() -> None:
    payload = build_payload()
    OUTPUT_JSON.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    OUTPUT_MD.write_text(write_markdown(payload), encoding="utf-8")
    print(f"wrote {OUTPUT_JSON.relative_to(ROOT)}")
    print(f"wrote {OUTPUT_MD.relative_to(ROOT)}")
    print(payload["decision"]["status"])


if __name__ == "__main__":
    main()
