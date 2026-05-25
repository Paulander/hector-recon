#!/usr/bin/env python3
"""Tests for the KRK full-suite readiness audit."""

import importlib.util
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def _load_module(name: str, relative: str):
    spec = importlib.util.spec_from_file_location(name, ROOT / relative)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


_audit = _load_module(
    "write_krk_full_suite_readiness_audit_v0",
    "scripts/write_krk_full_suite_readiness_audit_v0.py",
)


def _read_report() -> dict:
    payload = json.loads((ROOT / "reports/krk_full_suite_readiness_audit_v0.json").read_text())
    assert isinstance(payload, dict)
    return payload


def test_full_suite_readiness_artifact_preserves_boundaries():
    payload = _read_report()

    assert payload["schema_version"] == "krk_full_suite_readiness_audit.v0"
    assert payload["causal_status"] == "non_causal_readiness_audit"
    assert payload["decision"]["runtime_changes_allowed"] is False
    assert payload["decision"]["label_run_allowed"] is False
    assert payload["decision"]["selector_allowed"] is False
    assert payload["decision"]["selector_training_allowed"] is False
    assert payload["decision"]["stage7_promotion_allowed"] is False
    assert payload["decision"]["stage8_training_allowed"] is False

    boundaries = payload["runtime_and_training_boundaries"]
    assert boundaries["violation_count"] == 0
    assert boundaries["runtime_behavior_changed"] is False
    assert boundaries["runtime_selector_implemented"] is False
    assert boundaries["runtime_dtm_or_tablebase_lookup"] is False
    assert boundaries["gameplay_topology_mutation"] is False


def test_full_suite_readiness_identifies_current_gate():
    payload = _read_report()

    assert payload["protected_stack"]["ready"] is True
    assert payload["protected_stack"]["clean_stack_adopted"] is True
    assert payload["protected_stack"]["clean_stack_adopted_and_validated"] is True
    assert payload["protected_stack"]["m1_m4_preservation_passed"] is True
    assert payload["protected_stack"]["kpk_kqk_bridge_preservation_passed"] is True

    stage7 = payload["stage7_sampling_gate"]
    assert stage7["runner_status"] == "stage7_diverse_clean_sampling_runner_dry_run_ready"
    assert stage7["executed_job_count"] == 0
    assert stage7["output_validation_status"] == (
        "stage7_diverse_clean_sampling_outputs_validation_pending"
    )
    assert stage7["invalid_existing_output_count"] == 0
    assert stage7["overwrite_existing_outputs"] is False
    assert stage7["success_controls_ready"] is False
    assert stage7["combined_success_controls"] < stage7["success_controls_required"]

    stage4 = payload["stage_status"]["stage4"]
    assert (
        stage4["status"]
        == "stage4_caveat_unblocker_ready_pending_explicit_runtime_approval"
    )
    assert stage4["ready_for_explicit_runtime_approval"] is True
    assert stage4["implementation_allowed_by_current_artifact"] is False

    assert (
        payload["decision"]["status"]
        == "krk_suite_readiness_blocked_pending_stage7_clean_success_controls"
    )
    assert "stage7_clean_success_controls_missing" in payload["blockers"]
    assert "sequence_policy_benchmark_not_ready" in payload["blockers"]


def test_full_suite_readiness_writer_helpers_are_deterministic():
    payload = _audit.build_payload()
    rendered = _audit.write_markdown(payload)

    assert payload["decision"]["runtime_changes_allowed"] is False
    assert payload["stage_status"]["stage7"]["ready_for_promotion"] is False
    assert payload["stage_status"]["stage7"]["sampling_runner_invalid_existing_output_count"] == 0
    assert payload["stage_status"]["stage8"]["ready_for_training"] is False
    assert (
        payload["approval_gates"]["stage4_first_move_contrast_sandbox"]["status"]
        == "stage4_caveat_unblocker_ready_pending_explicit_runtime_approval"
    )
    assert "krk_suite_readiness_blocked_pending_stage7_clean_success_controls" in rendered
    assert "label_run_allowed: `false`" in rendered
