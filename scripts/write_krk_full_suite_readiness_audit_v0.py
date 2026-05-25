#!/usr/bin/env python3
"""Write a compact KRK full-suite readiness audit from existing artifacts.

This audit is intentionally non-causal. It joins the current protected-stack,
control-plane, Stage 7, and sequence-policy gate artifacts into a single
machine-checkable status report for the broader "working KRK suite" milestone.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
OUT_JSON = ROOT / "reports/krk_full_suite_readiness_audit_v0.json"
OUT_MD = ROOT / "reports/krk_full_suite_readiness_audit_v0.md"

SOURCES = {
    "current_brief": "reports/current_agent_brief.md",
    "control_plane_gate": "reports/krk_current_control_plane_gate_v0.json",
    "active_protected_stack": "reports/krk_active_protected_stack_v0.json",
    "clean_stack_validation": "reports/krk_clean_stack_post_replacement_validation_v0.json",
    "preservation_checks": "reports/krk_clean_retrain_retry1_preservation_checks_v0.json",
    "sequence_pipeline_refresh": (
        "reports/strategy_arbitration/krk_sequence_policy_pipeline_refresh_v0.json"
    ),
    "sequence_benchmark": "reports/strategy_arbitration/krk_sequence_policy_benchmark_v0.json",
    "stage7_sampling_runner": (
        "reports/structural_candidates/stage7_diverse_clean_sampling_runner_v0.json"
    ),
    "stage7_sampling_integration": (
        "reports/structural_candidates/stage7_diverse_clean_sampling_integration_v0.json"
    ),
}


FORBIDDEN_FLAGS = {
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


def load_json(relative: str) -> dict[str, Any]:
    path = ROOT / relative
    if not path.exists():
        return {"_missing": True, "_path": relative}
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise TypeError(f"{relative} must contain a JSON object")
    return data


def flag_value(payload: dict[str, Any], key: str) -> Any:
    if key in payload:
        return payload[key]
    invariants = payload.get("invariants")
    if isinstance(invariants, dict) and key in invariants:
        return invariants[key]
    return None


def artifact_ok(payload: dict[str, Any]) -> bool:
    return payload.get("_missing") is not True


def boundary_status(payloads: dict[str, dict[str, Any]]) -> dict[str, Any]:
    violations: list[dict[str, Any]] = []
    checked = 0
    for name, payload in payloads.items():
        if not artifact_ok(payload):
            continue
        for key, expected in FORBIDDEN_FLAGS.items():
            value = flag_value(payload, key)
            if value is None:
                continue
            checked += 1
            if value is not expected:
                violations.append(
                    {
                        "artifact": SOURCES[name],
                        "field": key,
                        "expected": expected,
                        "actual": value,
                    }
                )

    return {
        "checked_flag_count": checked,
        "violation_count": len(violations),
        "violations": violations,
        "runtime_defaults_changed": False,
        "runtime_behavior_changed": False,
        "runtime_selector_implemented": False,
        "runtime_dtm_or_tablebase_lookup": False,
        "gameplay_topology_mutation": False,
        "stage7_promotion_allowed": False,
        "stage8_training_allowed": False,
    }


def build_payload() -> dict[str, Any]:
    payloads = {name: load_json(path) for name, path in SOURCES.items() if path.endswith(".json")}

    active = payloads["active_protected_stack"]
    clean = payloads["clean_stack_validation"]
    preservation = payloads["preservation_checks"]
    pipeline = payloads["sequence_pipeline_refresh"]
    benchmark = payloads["sequence_benchmark"]
    runner = payloads["stage7_sampling_runner"]
    integration = payloads["stage7_sampling_integration"]
    gate = payloads["control_plane_gate"]

    boundaries = boundary_status(payloads)
    stage7_summary = integration.get("summary", {})
    sequence_summary = pipeline.get("summary", {})
    benchmark_preflight = benchmark.get("preflight", {})

    protected_stack_validated = (
        active.get("decision", {}).get("clean_stack_adopted") is True
        and clean.get("decision", {}).get("clean_stack_adopted_and_validated") is True
        and preservation.get("decision", {}).get("m1_m4_preservation_passed") is True
        and preservation.get("decision", {}).get("kpk_kqk_bridge_preservation_passed") is True
        and clean.get("validation", {}).get("stage5_conversion_preservation_guardrail", {}).get("passed")
        is True
        and clean.get("validation", {}).get("stage6_drive_h40_historical_bonus", {}).get("passed")
        is True
    )

    stage7_success_controls = int(stage7_summary.get("combined_success_controls", 0) or 0)
    stage7_success_required = int(stage7_summary.get("success_controls_required", 5) or 5)
    stage7_success_ready = stage7_success_controls >= stage7_success_required

    sequence_ready = bool(sequence_summary.get("sequence_policy_inputs_ready")) and bool(
        benchmark.get("decision", {}).get("benchmark_executed_as_ready")
    )

    stage_status = {
        "stage1": {
            "status": "protected_component_from_current_brief",
            "ready_for_current_suite": True,
        },
        "stage4": {
            "status": "mostly_clean_with_h40_caveat",
            "ready_for_current_suite": False,
            "blocker": "stage4 h40 caveat remains separate guardrail/control debt",
        },
        "stage5": {
            "status": "protected_retry1_stack_validated",
            "ready_for_current_suite": protected_stack_validated,
        },
        "stage6": {
            "status": "protected_retry1_overlay_validated",
            "ready_for_current_suite": protected_stack_validated,
        },
        "stage7": {
            "status": "held_out_challenge_quarantined",
            "ready_for_promotion": False,
            "success_controls": stage7_success_controls,
            "success_controls_required": stage7_success_required,
            "success_controls_ready": stage7_success_ready,
            "sampling_runner_status": runner.get("decision", {}).get("status"),
            "sampling_outputs_status": integration.get("decision", {}).get("status"),
        },
        "stage8": {
            "status": "blocked",
            "ready_for_training": False,
            "blocker": "Stage 7 remains quarantined and sequence-policy benchmark is not ready",
        },
    }

    blockers: list[str] = []
    if not protected_stack_validated:
        blockers.append("protected_retry1_stage5_6_stack_not_validated")
    if not stage7_success_ready:
        blockers.append("stage7_clean_success_controls_missing")
    if not sequence_ready:
        blockers.append("sequence_policy_benchmark_not_ready")
    if boundaries["violation_count"]:
        blockers.append("hard_invariant_violation_detected")

    if not blockers:
        decision_status = "krk_suite_readiness_ready_for_next_runtime_or_training_review"
        next_step = "prepare_explicit_runtime_or_training_review_packet"
    else:
        decision_status = "krk_suite_readiness_blocked_pending_stage7_clean_success_controls"
        next_step = "explicitly_approve_stage7_diverse_clean_sampling_or_choose_stage4_sandbox_gate"

    return {
        "schema_version": "krk_full_suite_readiness_audit.v0",
        "causal_status": "non_causal_readiness_audit",
        "source_artifacts": SOURCES,
        "protected_stack": {
            "status": active.get("status"),
            "clean_stack_adopted": active.get("decision", {}).get("clean_stack_adopted"),
            "filesystem_snapshots_replaced": active.get("decision", {}).get(
                "filesystem_snapshots_replaced"
            ),
            "clean_stack_adopted_and_validated": clean.get("decision", {}).get(
                "clean_stack_adopted_and_validated"
            ),
            "stage5_conversion_preservation_passed": clean.get("validation", {})
            .get("stage5_conversion_preservation_guardrail", {})
            .get("passed"),
            "stage6_drive_validation_passed": clean.get("validation", {})
            .get("stage6_drive_h40_historical_bonus", {})
            .get("passed"),
            "m1_m4_preservation_passed": preservation.get("decision", {}).get(
                "m1_m4_preservation_passed"
            ),
            "kpk_kqk_bridge_preservation_passed": preservation.get("decision", {}).get(
                "kpk_kqk_bridge_preservation_passed"
            ),
            "ready": protected_stack_validated,
        },
        "stage_status": stage_status,
        "sequence_policy": {
            "pipeline_status": pipeline.get("decision", {}).get("status"),
            "benchmark_status": benchmark.get("decision", {}).get("status"),
            "input_row_count": benchmark_preflight.get("row_count"),
            "inputs_ready": sequence_summary.get("sequence_policy_inputs_ready"),
            "benchmark_ready": benchmark.get("decision", {}).get("benchmark_executed_as_ready"),
            "stage7_heldout_row_count": benchmark_preflight.get("stage7_heldout_row_count"),
            "selector_training_row_count": benchmark_preflight.get("selector_training_row_count"),
            "runtime_authorization_row_count": benchmark_preflight.get(
                "runtime_authorization_row_count"
            ),
        },
        "stage7_sampling_gate": {
            "runner_status": runner.get("decision", {}).get("status"),
            "runner_dry_run": runner.get("summary", {}).get("dry_run"),
            "runner_job_count": runner.get("summary", {}).get("job_count"),
            "executed_job_count": runner.get("summary", {}).get("executed_job_count"),
            "integration_status": integration.get("decision", {}).get("status"),
            "outputs_present_count": stage7_summary.get("outputs_present_count"),
            "combined_success_controls": stage7_success_controls,
            "success_controls_required": stage7_success_required,
            "combined_failure_controls": stage7_summary.get("combined_failure_controls"),
            "failure_controls_required": stage7_summary.get("failure_controls_required"),
            "success_controls_ready": stage7_success_ready,
            "label_run_allowed_by_artifact": runner.get("decision", {}).get("label_run_allowed"),
        },
        "runtime_and_training_boundaries": boundaries,
        "current_control_plane_gate": {
            "status": gate.get("decision", {}).get("status"),
            "label_run_allowed": gate.get("decision", {}).get("label_run_allowed"),
            "runtime_changes_allowed": gate.get("decision", {}).get("runtime_changes_allowed"),
            "selector_training_allowed": gate.get("decision", {}).get(
                "selector_training_allowed"
            ),
            "stage7_promotion_allowed": gate.get("decision", {}).get("stage7_promotion_allowed"),
            "stage8_training_allowed": gate.get("decision", {}).get("stage8_training_allowed"),
        },
        "blockers": blockers,
        "approval_gates": {
            "stage7_diverse_clean_label_execution": {
                "ready_for_explicit_approval": runner.get("decision", {}).get("status")
                == "stage7_diverse_clean_sampling_runner_dry_run_ready",
                "current_artifact_allows_execution": False,
                "why": "The runner is dry-run ready, but execution requires explicit approval because it creates new Stage 7 h40 labels.",
            },
            "stage4_first_move_contrast_sandbox": {
                "ready_for_explicit_approval": True,
                "current_artifact_allows_implementation": False,
                "why": "Stage 4 has a separate runtime-review-ready gate, but implementation still requires explicit sandbox approval.",
            },
            "stage8_training": {
                "ready_for_explicit_approval": False,
                "why": "Stage 7 is still quarantined and sequence-policy benchmark is blocked.",
            },
        },
        "decision": {
            "status": decision_status,
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
    protected = payload["protected_stack"]
    stage7 = payload["stage7_sampling_gate"]
    sequence = payload["sequence_policy"]
    decision = payload["decision"]
    lines = [
        "# KRK Full Suite Readiness Audit v0",
        "",
        "## Decision",
        "",
        f"- status: `{decision['status']}`",
        f"- recommended_next_step: `{decision['recommended_next_step']}`",
        f"- runtime_changes_allowed: `{str(decision['runtime_changes_allowed']).lower()}`",
        f"- label_run_allowed: `{str(decision['label_run_allowed']).lower()}`",
        f"- selector_training_allowed: `{str(decision['selector_training_allowed']).lower()}`",
        f"- stage7_promotion_allowed: `{str(decision['stage7_promotion_allowed']).lower()}`",
        f"- stage8_training_allowed: `{str(decision['stage8_training_allowed']).lower()}`",
        "",
        "## Protected Stack",
        "",
        f"- active status: `{protected['status']}`",
        f"- clean_stack_adopted: `{protected['clean_stack_adopted']}`",
        f"- filesystem_snapshots_replaced: `{protected['filesystem_snapshots_replaced']}`",
        f"- clean_stack_adopted_and_validated: `{protected['clean_stack_adopted_and_validated']}`",
        f"- stage5_conversion_preservation_passed: `{protected['stage5_conversion_preservation_passed']}`",
        f"- stage6_drive_validation_passed: `{protected['stage6_drive_validation_passed']}`",
        f"- m1_m4_preservation_passed: `{protected['m1_m4_preservation_passed']}`",
        f"- kpk_kqk_bridge_preservation_passed: `{protected['kpk_kqk_bridge_preservation_passed']}`",
        "",
        "## Stage Status",
        "",
    ]
    for stage, status in payload["stage_status"].items():
        lines.append(f"- `{stage}`: `{status['status']}`")
    lines.extend(
        [
            "",
            "## Stage 7 Sampling Gate",
            "",
            f"- runner_status: `{stage7['runner_status']}`",
            f"- runner_dry_run: `{stage7['runner_dry_run']}`",
            f"- runner_job_count: `{stage7['runner_job_count']}`",
            f"- executed_job_count: `{stage7['executed_job_count']}`",
            f"- integration_status: `{stage7['integration_status']}`",
            f"- outputs_present_count: `{stage7['outputs_present_count']}`",
            f"- combined_success_controls: `{stage7['combined_success_controls']}`",
            f"- success_controls_required: `{stage7['success_controls_required']}`",
            f"- success_controls_ready: `{stage7['success_controls_ready']}`",
            "",
            "## Sequence Policy",
            "",
            f"- pipeline_status: `{sequence['pipeline_status']}`",
            f"- benchmark_status: `{sequence['benchmark_status']}`",
            f"- input_row_count: `{sequence['input_row_count']}`",
            f"- inputs_ready: `{sequence['inputs_ready']}`",
            f"- benchmark_ready: `{sequence['benchmark_ready']}`",
            f"- selector_training_row_count: `{sequence['selector_training_row_count']}`",
            "",
            "## Blockers",
            "",
        ]
    )
    for blocker in payload["blockers"]:
        lines.append(f"- `{blocker}`")
    if not payload["blockers"]:
        lines.append("- none")
    lines.extend(
        [
            "",
            "## Approval Gates",
            "",
        ]
    )
    for gate, details in payload["approval_gates"].items():
        lines.append(f"- `{gate}`: {details['why']}")
    lines.extend(
        [
            "",
            "## Boundary Check",
            "",
            f"- checked_flag_count: `{payload['runtime_and_training_boundaries']['checked_flag_count']}`",
            f"- violation_count: `{payload['runtime_and_training_boundaries']['violation_count']}`",
        ]
    )
    return "\n".join(lines) + "\n"


def main() -> None:
    payload = build_payload()
    OUT_JSON.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    OUT_MD.write_text(write_markdown(payload), encoding="utf-8")
    print(f"wrote {OUT_JSON.relative_to(ROOT)}")
    print(f"wrote {OUT_MD.relative_to(ROOT)}")
    print(payload["decision"]["status"])


if __name__ == "__main__":
    main()
