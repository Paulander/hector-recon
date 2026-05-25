#!/usr/bin/env python3
"""Tests for the KRK full-suite unblocker packet."""

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


_packet = _load_module(
    "write_krk_full_suite_unblocker_packet_v0",
    "scripts/write_krk_full_suite_unblocker_packet_v0.py",
)


def _read_report() -> dict:
    payload = json.loads((ROOT / "reports/krk_full_suite_unblocker_packet_v0.json").read_text())
    assert isinstance(payload, dict)
    return payload


def test_unblocker_packet_identifies_primary_gate_without_authorizing_it():
    payload = _read_report()

    assert payload["schema_version"] == "krk_full_suite_unblocker_packet.v0"
    assert payload["causal_status"] == "non_causal_approval_packet"
    assert (
        payload["decision"]["status"]
        == "krk_suite_primary_unblocker_ready_pending_explicit_label_approval"
    )
    assert payload["decision"]["label_run_allowed"] is False
    assert payload["decision"]["runtime_changes_allowed"] is False
    assert payload["decision"]["stage7_promotion_allowed"] is False
    assert payload["decision"]["stage8_training_allowed"] is False

    primary = payload["primary_unblocker"]
    assert primary["id"] == "stage7_diverse_clean_label_execution"
    assert primary["approval_required"] is True
    assert primary["implementation_allowed_by_this_packet"] is False
    assert primary["status"] == "ready_pending_explicit_approval"
    assert primary["scope"]["resume_safe"] is True
    assert primary["scope"]["skip_existing_outputs_by_default"] is True
    assert primary["scope"]["invalid_existing_outputs_block_without_overwrite"] is True
    assert primary["scope"]["execution_readiness_recomputed_live"] is True
    assert primary["scope"]["stage7_training_rows"] == 0
    assert primary["scope"]["stage7_promotion_allowed"] is False
    assert primary["scope"]["stage8_training_allowed"] is False
    assert (
        payload["current_state"]["stage7_output_validation_status"]
        == "stage7_diverse_clean_sampling_outputs_validation_pending"
    )
    assert payload["current_state"]["stage7_execution_readiness_source"] == "live_recomputed"
    assert (
        payload["current_state"]["stage7_execution_readiness_status"]
        == "stage7_diverse_clean_sampling_execution_ready_pending_explicit_approval"
    )
    assert payload["current_state"]["stage7_execution_readiness_jobs_passing"] == 8
    assert payload["current_state"]["stage7_invalid_existing_output_count"] == 0
    assert payload["current_state"]["stage7_overwrite_existing_outputs"] is False
    assert payload["current_state"]["stage7_processed_job_count"] == 0
    assert payload["current_state"]["stage7_executed_job_count"] == 0
    assert payload["current_state"]["stage7_skipped_existing_output_count"] == 0


def test_unblocker_packet_keeps_stage4_as_secondary_gate():
    payload = _read_report()
    secondary = payload["secondary_unblocker"]

    assert secondary["id"] == "stage4_first_move_contrast_sandbox"
    assert secondary["status"] == "stage4_caveat_unblocker_ready_pending_explicit_runtime_approval"
    assert secondary["approval_required"] is True
    assert secondary["implementation_allowed_by_this_packet"] is False


def test_unblocker_packet_writer_mentions_exact_command_but_still_blocks_execution():
    payload = _packet.build_payload()
    rendered = _packet.write_markdown(payload)

    assert "--execute-reviewed-label-run --refresh-after-run" in rendered
    assert "resume_safe: `True`" in rendered
    assert "invalid_existing_outputs_block_without_overwrite: `True`" in rendered
    assert "implementation_allowed_by_this_packet: `False`" in rendered
    assert payload["primary_unblocker"]["implementation_allowed_by_this_packet"] is False
