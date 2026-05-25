#!/usr/bin/env python3
"""Refresh the passive KRK sequence-policy evidence pipeline.

This orchestration script never runs Stage 7 labels, implements runtime
behavior, trains selectors, promotes Stage 7, or trains Stage 8. It only
recomputes the passive artifacts that become meaningful after separately
approved diverse-clean label outputs appear.
"""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
OUTPUT_JSON = ROOT / "reports/strategy_arbitration/krk_sequence_policy_pipeline_refresh_v0.json"
OUTPUT_MD = ROOT / "reports/strategy_arbitration/krk_sequence_policy_pipeline_refresh_v0.md"

SCHEMA_VERSION = "krk_sequence_policy_pipeline_refresh.v0"

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


STEPS = [
    {
        "step_id": "stage7_diverse_clean_integration",
        "script": "scripts/integrate_stage7_diverse_clean_sampling_results_v0.py",
        "output_json": "reports/structural_candidates/stage7_diverse_clean_sampling_integration_v0.json",
    },
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
        "step_id": "current_control_plane_gate",
        "script": "scripts/write_krk_current_control_plane_gate_v0.py",
        "output_json": "reports/krk_current_control_plane_gate_v0.json",
    },
]


def _load_module(path: Path):
    spec = importlib.util.spec_from_file_location(path.stem, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load script module: {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _load_json(path: str | Path) -> dict[str, Any]:
    full = ROOT / path if isinstance(path, str) else path
    return json.loads(full.read_text(encoding="utf-8"))


def run_refresh() -> dict[str, Any]:
    step_results = []
    for step in STEPS:
        module = _load_module(ROOT / step["script"])
        if not hasattr(module, "main"):
            raise RuntimeError(f"script has no main(): {step['script']}")
        module.main()
        output = _load_json(step["output_json"])
        step_results.append(
            {
                "step_id": step["step_id"],
                "script": step["script"],
                "output_json": step["output_json"],
                "decision_status": (output.get("decision") or {}).get("status"),
                "runtime_changes_allowed": bool(
                    (output.get("decision") or {}).get("runtime_changes_allowed", False)
                ),
                "label_run_allowed": bool(
                    (output.get("decision") or {}).get("label_run_allowed", False)
                ),
                "stage7_promotion_allowed": bool(
                    (output.get("decision") or {}).get("stage7_promotion_allowed", False)
                ),
                "stage8_training_allowed": bool(
                    (output.get("decision") or {}).get("stage8_training_allowed", False)
                ),
            }
        )

    integration = _load_json("reports/structural_candidates/stage7_diverse_clean_sampling_integration_v0.json")
    inputs = _load_json("reports/strategy_arbitration/krk_sequence_policy_benchmark_inputs_v0.json")
    benchmark = _load_json("reports/strategy_arbitration/krk_sequence_policy_benchmark_v0.json")
    gate = _load_json("reports/krk_current_control_plane_gate_v0.json")
    benchmark_ready = bool(inputs.get("summary", {}).get("benchmark_input_ready"))
    all_boundaries_preserved = all(
        not result["runtime_changes_allowed"]
        and not result["label_run_allowed"]
        and not result["stage7_promotion_allowed"]
        and not result["stage8_training_allowed"]
        for result in step_results
    )
    return {
        "schema_version": SCHEMA_VERSION,
        "causal_status": "non_causal_passive_pipeline_refresh",
        **COMMON_FALSE_FLAGS,
        "source_scripts": [step["script"] for step in STEPS],
        "step_results": step_results,
        "summary": {
            "step_count": len(step_results),
            "all_boundaries_preserved": all_boundaries_preserved,
            "stage7_outputs_present_count": integration.get("summary", {}).get(
                "outputs_present_count", 0
            ),
            "stage7_success_controls": inputs.get("summary", {}).get(
                "stage7_clean_success_controls", 0
            ),
            "stage7_success_controls_required": inputs.get("summary", {}).get(
                "stage7_clean_success_controls_required", 5
            ),
            "sequence_policy_inputs_ready": benchmark_ready,
            "sequence_policy_benchmark_status": benchmark.get("decision", {}).get("status"),
            "current_gate_status": gate.get("decision", {}).get("status"),
        },
        "decision": {
            "status": (
                "sequence_policy_pipeline_refreshed_ready_for_non_causal_benchmark_review"
                if benchmark_ready
                else "sequence_policy_pipeline_refreshed_still_blocked_by_stage7_success_controls"
            ),
            "recommended_next_step": (
                "review_non_causal_sequence_policy_benchmark"
                if benchmark_ready
                else "run_explicitly_approved_stage7_diverse_clean_label_jobs"
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
        "# KRK Sequence-Policy Pipeline Refresh v0",
        "",
        f"Status: `{decision['status']}`",
        "",
        "This passive refresh reruns integration, input assembly, probe, benchmark, and gate artifacts. It does not execute labels, train, route, promote Stage 7, or train Stage 8.",
        "",
        "## Summary",
        "",
    ]
    for key, value in summary.items():
        lines.append(f"- {key}: `{value}`")
    lines.extend(["", "## Steps", ""])
    for result in payload["step_results"]:
        lines.append(
            f"- `{result['step_id']}` status=`{result['decision_status']}` runtime=`{result['runtime_changes_allowed']}` labels=`{result['label_run_allowed']}`"
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
    payload = run_refresh()
    OUTPUT_JSON.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    OUTPUT_MD.write_text(write_markdown(payload), encoding="utf-8")
    print(
        json.dumps(
            {
                "decision": payload["decision"]["status"],
                "stage7_success_controls": payload["summary"]["stage7_success_controls"],
                "sequence_policy_inputs_ready": payload["summary"][
                    "sequence_policy_inputs_ready"
                ],
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
