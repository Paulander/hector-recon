#!/usr/bin/env python3
"""Tests for reviewed additional Stage 7 clean sampling manifest."""

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


_manifest = _load_module(
    "write_stage7_additional_clean_sampling_manifest_v0",
    "scripts/write_stage7_additional_clean_sampling_manifest_v0.py",
)
_runner = _load_module(
    "run_stage7_additional_clean_sampling_jobs_v0",
    "scripts/run_stage7_additional_clean_sampling_jobs_v0.py",
)
_output_validation = _load_module(
    "validate_stage7_additional_clean_sampling_outputs_v0",
    "scripts/validate_stage7_additional_clean_sampling_outputs_v0.py",
)


def _read_report(path: str) -> dict:
    payload = json.loads((ROOT / path).read_text(encoding="utf-8"))
    assert isinstance(payload, dict)
    return payload


def test_stage7_additional_clean_sampling_manifest_is_review_only():
    payload = _read_report(
        "reports/structural_candidates/stage7_additional_clean_sampling_manifest_v0.json"
    )

    assert payload["schema_version"] == "stage7_additional_clean_sampling_manifest.v0"
    assert payload["causal_status"] == "non_causal_label_manifest_review_only"
    assert payload["runtime_behavior_changed"] is False
    assert payload["runtime_defaults_changed"] is False
    assert payload["runtime_selector_implemented"] is False
    assert payload["runtime_score_changes"] is False
    assert payload["runtime_direct_routing"] is False
    assert payload["runtime_dtm_or_tablebase_lookup"] is False
    assert payload["hidden_python_controller"] is False
    assert payload["gameplay_topology_mutation"] is False
    assert payload["stage7_promotion_allowed"] is False
    assert payload["stage8_training_allowed"] is False
    assert payload["review_basis"]["success_gap"] == 0
    assert payload["review_basis"]["highest_yield_prior_job_ids"] == [
        "stage7.diverse_clean.edge_fence_deep.seed107.samples8.h40"
    ]
    assert payload["summary"]["job_count"] == 0
    assert payload["summary"]["max_total_samples"] == 0
    assert payload["summary"]["candidate_job_count_if_gap_reopens"] == 4
    assert payload["summary"]["topology_exists"] is True
    assert payload["summary"]["label_run_allowed_by_this_manifest"] is False
    assert payload["summary"]["stage7_training_row_count"] == 0
    assert payload["summary"]["runtime_authorization_row_count"] == 0
    assert (
        payload["decision"]["status"]
        == "stage7_additional_clean_sampling_manifest_not_applicable_success_gate_closed"
    )
    assert (
        payload["decision"]["recommended_next_step"]
        == "rerun_passive_sequence_policy_gate_stack"
    )
    assert payload["decision"]["runtime_changes_allowed"] is False
    assert payload["decision"]["selector_training_allowed"] is False
    assert payload["decision"]["stage7_promotion_allowed"] is False
    assert payload["decision"]["stage8_training_allowed"] is False
    assert payload["jobs"] == []


def test_stage7_additional_clean_sampling_manifest_fixture_uses_review_gap():
    payload = _manifest.build_payload(
        active_stack={
            "active_protected_stack": {
                "stage6_drive_overlay": {
                    "topology": "snapshots/krk_triplet_pipeline/clean_retrain_checkpoint_v0_retry1/stage6_overlay_composed/topology/krk_entry_topology.json"
                }
            }
        },
        label_distribution_review={
            "summary": {
                "success_gap": 1,
                "unique_new_success_key_count_vs_pre_run": 2,
                "duplicate_playout_count": 50,
            },
            "followup_sampling_guidance": {
                "highest_yield_job_ids": ["fixture.edge"],
                "reuse_same_manifest_without_overwrite_expected_to_help": False,
            },
            "decision": {"status": "ready"},
        },
    )

    assert payload["review_basis"]["success_gap"] == 1
    assert payload["summary"]["job_count"] == 4
    assert payload["summary"]["max_total_samples"] == 32
    assert (
        payload["decision"]["status"]
        == "stage7_additional_clean_sampling_manifest_ready_pending_explicit_approval"
    )
    assert payload["decision"]["implementation_authorized_by_this_manifest"] is False
    for job in payload["jobs"]:
        command = job["command"]
        assert job["samples"] == 8
        assert job["playout_max_plies"] == 40
        assert job["source_stage_names"] == ["Edge_Fence_Deep"]
        assert job["runtime_work_allowed"] is False
        assert job["stage7_training_row"] is False
        for flag in job["forbidden_flags"]:
            assert flag not in command


def test_stage7_additional_clean_sampling_manifest_fixture_closes_without_gap():
    payload = _manifest.build_payload(
        active_stack={
            "active_protected_stack": {
                "stage6_drive_overlay": {
                    "topology": "snapshots/krk_triplet_pipeline/clean_retrain_checkpoint_v0_retry1/stage6_overlay_composed/topology/krk_entry_topology.json"
                }
            }
        },
        label_distribution_review={
            "summary": {
                "success_gap": 0,
                "unique_new_success_key_count_vs_pre_run": 2,
                "duplicate_playout_count": 50,
            },
            "followup_sampling_guidance": {
                "highest_yield_job_ids": ["fixture.edge"],
                "reuse_same_manifest_without_overwrite_expected_to_help": False,
            },
            "decision": {"status": "ready"},
        },
    )

    assert payload["review_basis"]["success_gap"] == 0
    assert payload["summary"]["job_count"] == 0
    assert payload["summary"]["max_total_samples"] == 0
    assert payload["summary"]["candidate_job_count_if_gap_reopens"] == 4
    assert (
        payload["decision"]["status"]
        == "stage7_additional_clean_sampling_manifest_not_applicable_success_gate_closed"
    )
    assert payload["decision"]["implementation_authorized_by_this_manifest"] is False
    rendered = _manifest.write_markdown(payload)
    assert "not applicable because the Stage 7 clean success-control gate is closed" in rendered
    assert "remaining Stage 7 clean success-control gap" not in rendered


def test_stage7_additional_clean_sampling_runner_defaults_to_dry_run():
    payload = _runner.build_payload(execute=False, run_post_success_refresh=False)

    assert payload["schema_version"] == "stage7_additional_clean_sampling_runner.v0"
    assert payload["execution_requested"] is False
    assert payload["summary"]["dry_run"] is True
    assert payload["summary"]["job_count"] == 0
    assert payload["summary"]["processed_job_count"] == 0
    assert payload["summary"]["executed_job_count"] == 0
    assert payload["summary"]["stage7_training_row_count"] == 0
    assert payload["summary"]["runtime_authorization_row_count"] == 0
    assert payload["hidden_python_controller"] is False
    assert payload["summary"]["output_validation_status"] == (
        "stage7_additional_clean_sampling_outputs_not_applicable_success_gate_closed"
    )
    assert (
        payload["decision"]["status"]
        == "stage7_additional_clean_sampling_runner_not_applicable_success_gate_closed"
    )
    assert payload["decision"]["label_run_allowed"] is False
    assert payload["decision"]["runtime_changes_allowed"] is False
    assert payload["decision"]["stage7_promotion_allowed"] is False
    assert payload["decision"]["stage8_training_allowed"] is False
    for command in payload["commands"]:
        assert command["would_execute"] is False


def test_stage7_additional_clean_sampling_output_validation_accepts_outputs():
    payload = _read_report(
        "reports/structural_candidates/stage7_additional_clean_sampling_output_validation_v0.json"
    )

    assert payload["schema_version"] == "stage7_additional_clean_sampling_output_validation.v0"
    assert payload["causal_status"] == "non_causal_output_validation"
    assert payload["runtime_behavior_changed"] is False
    assert payload["runtime_defaults_changed"] is False
    assert payload["runtime_selector_implemented"] is False
    assert payload["runtime_score_changes"] is False
    assert payload["runtime_direct_routing"] is False
    assert payload["runtime_dtm_or_tablebase_lookup"] is False
    assert payload["hidden_python_controller"] is False
    assert payload["gameplay_topology_mutation"] is False
    assert payload["stage7_promotion_allowed"] is False
    assert payload["stage8_training_allowed"] is False
    assert payload["summary"]["job_count"] == 0
    assert payload["summary"]["output_exists_count"] == 0
    assert payload["summary"]["output_valid_count"] == 0
    assert payload["summary"]["stage7_training_row_count"] == 0
    assert payload["summary"]["runtime_authorization_row_count"] == 0
    assert (
        payload["decision"]["status"]
        == "stage7_additional_clean_sampling_outputs_not_applicable_success_gate_closed"
    )
    assert payload["decision"]["label_run_allowed"] is False
    assert payload["decision"]["runtime_changes_allowed"] is False
    assert payload["decision"]["stage7_promotion_allowed"] is False
    assert payload["decision"]["stage8_training_allowed"] is False
