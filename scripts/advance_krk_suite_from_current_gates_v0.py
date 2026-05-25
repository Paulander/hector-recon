#!/usr/bin/env python3
"""Advance passive KRK-suite gates from the current artifact state.

This script is a safe continuation harness. It never runs Stage 7 labels,
implements runtime behavior, trains selectors, promotes Stage 7, or trains
Stage 8. It only reruns the passive integration/benchmark/readiness artifacts
that can become unblocked after separately approved outputs appear.
"""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
OUTPUT_JSON = ROOT / "reports/krk_suite_gate_advancement_v0.json"
OUTPUT_MD = ROOT / "reports/krk_suite_gate_advancement_v0.md"

SCHEMA_VERSION = "krk_suite_gate_advancement.v0"

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


PASSIVE_STEPS = [
    {
        "step_id": "stage7_diverse_clean_output_validation",
        "script": "scripts/validate_stage7_diverse_clean_sampling_outputs_v0.py",
        "output_json": "reports/structural_candidates/stage7_diverse_clean_sampling_output_validation_v0.json",
    },
    {
        "step_id": "stage4_caveat_unblocker_packet",
        "script": "scripts/write_krk_stage4_caveat_unblocker_packet_v0.py",
        "output_json": "reports/krk_stage4_caveat_unblocker_packet_v0.json",
    },
    {
        "step_id": "sequence_policy_pipeline_refresh",
        "script": "scripts/refresh_krk_sequence_policy_pipeline_v0.py",
        "output_json": "reports/strategy_arbitration/krk_sequence_policy_pipeline_refresh_v0.json",
    },
    {
        "step_id": "sequence_policy_benchmark_review",
        "script": "scripts/review_krk_sequence_policy_benchmark_v0.py",
        "output_json": "reports/strategy_arbitration/krk_sequence_policy_benchmark_review_v0.json",
    },
    {
        "step_id": "full_suite_readiness_audit",
        "script": "scripts/write_krk_full_suite_readiness_audit_v0.py",
        "output_json": "reports/krk_full_suite_readiness_audit_v0.json",
    },
    {
        "step_id": "full_suite_unblocker_packet",
        "script": "scripts/write_krk_full_suite_unblocker_packet_v0.py",
        "output_json": "reports/krk_full_suite_unblocker_packet_v0.json",
    },
    {
        "step_id": "stage8_training_readiness_review",
        "script": "scripts/review_krk_stage8_training_readiness_v0.py",
        "output_json": "reports/krk_stage8_training_readiness_review_v0.json",
    },
    {
        "step_id": "stage7_post_label_outcome_review",
        "script": "scripts/review_krk_stage7_post_label_outcome_v0.py",
        "output_json": "reports/krk_stage7_post_label_outcome_review_v0.json",
    },
]


def _load_module(path: Path):
    spec = importlib.util.spec_from_file_location(path.stem, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load script module: {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _load_json(relative: str) -> dict[str, Any]:
    data = json.loads((ROOT / relative).read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise TypeError(f"{relative} must contain a JSON object")
    return data


def _run_script(script: str) -> dict[str, Any]:
    module = _load_module(ROOT / script)
    if not hasattr(module, "main"):
        raise RuntimeError(f"script has no main(): {script}")
    module.main()
    return {"script": script, "ran": True}


def build_payload() -> dict[str, Any]:
    step_results: list[dict[str, Any]] = []
    for step in PASSIVE_STEPS:
        _run_script(step["script"])
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
                "selector_training_allowed": bool(
                    (output.get("decision") or {}).get("selector_training_allowed", False)
                ),
                "stage7_promotion_allowed": bool(
                    (output.get("decision") or {}).get("stage7_promotion_allowed", False)
                ),
                "stage8_training_allowed": bool(
                    (output.get("decision") or {}).get("stage8_training_allowed", False)
                ),
            }
        )

    readiness = _load_json("reports/krk_full_suite_readiness_audit_v0.json")
    unblocker = _load_json("reports/krk_full_suite_unblocker_packet_v0.json")
    stage4_unblocker = _load_json("reports/krk_stage4_caveat_unblocker_packet_v0.json")
    output_validation = _load_json(
        "reports/structural_candidates/stage7_diverse_clean_sampling_output_validation_v0.json"
    )
    pipeline = _load_json("reports/strategy_arbitration/krk_sequence_policy_pipeline_refresh_v0.json")
    benchmark = _load_json("reports/strategy_arbitration/krk_sequence_policy_benchmark_v0.json")
    benchmark_review = _load_json(
        "reports/strategy_arbitration/krk_sequence_policy_benchmark_review_v0.json"
    )
    stage8_review = _load_json("reports/krk_stage8_training_readiness_review_v0.json")
    post_label_review = _load_json("reports/krk_stage7_post_label_outcome_review_v0.json")

    all_boundaries_preserved = all(
        not result["runtime_changes_allowed"]
        and not result["label_run_allowed"]
        and not result["selector_training_allowed"]
        and not result["stage7_promotion_allowed"]
        and not result["stage8_training_allowed"]
        for result in step_results
    )
    benchmark_ready = bool(benchmark.get("decision", {}).get("benchmark_executed_as_ready"))
    stage7_ready = bool(
        readiness.get("stage7_sampling_gate", {}).get("success_controls_ready")
    )

    if benchmark_ready:
        status = "krk_suite_passive_advancement_ready_for_sequence_policy_review"
        next_step = "review_non_causal_sequence_policy_benchmark_results"
    elif not stage7_ready:
        status = "krk_suite_passive_advancement_blocked_pending_stage7_label_outputs"
        next_step = "explicitly_approve_stage7_diverse_clean_label_execution"
    else:
        status = "krk_suite_passive_advancement_blocked_pending_manual_review"
        next_step = "inspect_sequence_policy_pipeline_refresh"

    return {
        "schema_version": SCHEMA_VERSION,
        "causal_status": "non_causal_passive_gate_advancement",
        **COMMON_FALSE_FLAGS,
        "source_scripts": [step["script"] for step in PASSIVE_STEPS],
        "step_results": step_results,
        "summary": {
            "all_boundaries_preserved": all_boundaries_preserved,
            "stage7_output_validation_status": output_validation.get("decision", {}).get(
                "status"
            ),
            "stage7_output_valid_count": output_validation.get("summary", {}).get(
                "output_valid_count"
            ),
            "stage4_caveat_unblocker_status": stage4_unblocker.get("decision", {}).get(
                "status"
            ),
            "stage7_success_controls": readiness.get("stage7_sampling_gate", {}).get(
                "combined_success_controls"
            ),
            "stage7_success_controls_required": readiness.get("stage7_sampling_gate", {}).get(
                "success_controls_required"
            ),
            "stage7_success_controls_ready": stage7_ready,
            "sequence_policy_inputs_ready": pipeline.get("summary", {}).get(
                "sequence_policy_inputs_ready"
            ),
            "sequence_policy_benchmark_ready": benchmark_ready,
            "sequence_policy_benchmark_review_status": benchmark_review.get("decision", {}).get(
                "status"
            ),
            "readiness_status": readiness.get("decision", {}).get("status"),
            "unblocker_status": unblocker.get("decision", {}).get("status"),
            "stage8_training_readiness_status": stage8_review.get("decision", {}).get(
                "status"
            ),
            "stage7_post_label_outcome_status": post_label_review.get("decision", {}).get(
                "status"
            ),
            "stage7_post_label_outcome_next_step": post_label_review.get("decision", {}).get(
                "recommended_next_step"
            ),
        },
        "decision": {
            "status": status,
            "recommended_next_step": next_step,
            "runtime_changes_allowed": False,
            "label_run_allowed": False,
            "selector_allowed": False,
            "selector_training_allowed": False,
            "stage7_promotion_allowed": False,
            "stage8_training_allowed": False,
        },
    }


def write_markdown(payload: dict[str, Any]) -> str:
    decision = payload["decision"]
    summary = payload["summary"]
    lines = [
        "# KRK Suite Gate Advancement v0",
        "",
        f"Status: `{decision['status']}`",
        "",
        "This passive advancement reruns the safe post-label integration, sequence-policy, readiness, and unblocker artifacts. It never executes labels, changes runtime behavior, trains selectors, promotes Stage 7, or trains Stage 8.",
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
    OUTPUT_JSON.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    OUTPUT_MD.write_text(write_markdown(payload), encoding="utf-8")
    print(f"wrote {OUTPUT_JSON.relative_to(ROOT)}")
    print(f"wrote {OUTPUT_MD.relative_to(ROOT)}")
    print(payload["decision"]["status"])


if __name__ == "__main__":
    main()
