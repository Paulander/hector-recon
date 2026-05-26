#!/usr/bin/env python3
"""Tests for protected plan-window failure-contrast integration."""

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


_integration = _load_module(
    "integrate_krk_protected_plan_window_failure_contrasts_v0",
    "scripts/integrate_krk_protected_plan_window_failure_contrasts_v0.py",
)


def _read_report() -> dict:
    payload = json.loads(
        (
            ROOT
            / "reports/strategy_arbitration/"
            "krk_protected_plan_window_failure_contrast_integration_v0.json"
        ).read_text(encoding="utf-8")
    )
    assert isinstance(payload, dict)
    return payload


def _plan(existing: int = 1, needed: int = 4) -> dict:
    return {
        "summary": {
            "unique_failure_count": existing,
            "minimum_new_unique_failures_needed": needed,
        },
        "collection_units": [
            {
                "unit_id": "protected_plan_window_failure_contrast_minimum",
                "minimum_required_unique_failures": existing + needed,
            }
        ],
    }


def _manifest(job_count: int = 4) -> dict:
    jobs = []
    stages = ["stage5", "stage6", "stage4", "stage5"]
    families = [
        "fence_handoff_plan_window",
        "drive_to_edge_plan_window",
        "wrong_tempo_plan_window",
        "fence_handoff_plan_window",
    ]
    for index in range(job_count):
        jobs.append(
            {
                "job_id": f"job.{index}",
                "source_stage": stages[index % len(stages)],
                "source_family": families[index % len(families)],
                "seed_frame_id": f"frame.{index}",
                "anchor_move_uci": f"a{index + 1}a{index + 2}",
            }
        )
    return {"jobs": jobs}


def _validation(status: str, valid_count: int) -> dict:
    return {
        "summary": {
            "output_exists_count": valid_count,
            "output_valid_count": valid_count,
            "unique_failure_candidate_count": valid_count,
            "current_gate_status": "krk_control_plane_waiting_on_explicit_gate_choice",
            "current_control_plane_approval_option_ids": [
                "approve_protected_plan_window_failure_contrast_collection"
            ],
            "protected_failure_contrast_collection_option_available": True,
            "protected_failure_contrast_collection_command_available": True,
            "protected_failure_contrast_collection_option_id": (
                "approve_protected_plan_window_failure_contrast_collection"
            ),
            "protected_failure_contrast_collection_blocked_by_option_id": None,
        },
        "output_checks": [
            {
                "job_id": f"job.{index}",
                "valid": True,
                "result": "max_plies",
                "h40_outcome_label": "conversion_failure",
            }
            for index in range(valid_count)
        ],
        "decision": {"status": status},
    }


def test_failure_contrast_integration_pending_before_outputs():
    payload = _read_report()

    assert (
        payload["schema_version"]
        == "krk_protected_plan_window_failure_contrast_integration.v0"
    )
    assert payload["causal_status"] == "non_causal_failure_contrast_integration"
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
    assert (
        payload["decision"]["status"]
        == "protected_plan_window_failure_contrast_integration_pending_outputs"
    )
    assert payload["summary"]["validation_status"] == (
        "protected_plan_window_failure_contrast_outputs_validation_pending"
    )
    assert payload["summary"]["output_exists_count"] == 0
    assert payload["summary"]["output_valid_count"] == 0
    assert payload["summary"]["integrated_new_failure_count"] == 0
    assert payload["summary"]["existing_unique_failure_count"] == 1
    assert payload["summary"]["minimum_new_unique_failures_needed"] == 4
    assert payload["summary"]["integration_ready"] is False
    assert payload["summary"]["stage7_training_row_count"] == 0
    assert payload["summary"]["selector_training_row_count"] == 0
    assert payload["summary"]["runtime_authorization_row_count"] == 0
    assert (
        "approve_protected_plan_window_failure_contrast_collection"
        in payload["summary"]["current_control_plane_approval_option_ids"]
    )
    assert (
        payload["summary"]["protected_failure_contrast_collection_option_available"]
        is True
    )
    assert (
        payload["summary"]["protected_failure_contrast_collection_command_available"]
        is True
    )
    assert (
        payload["summary"]["protected_failure_contrast_collection_option_id"]
        == "approve_protected_plan_window_failure_contrast_collection"
    )
    assert (
        payload["summary"]["protected_failure_contrast_collection_blocked_by_option_id"]
        is None
    )
    assert payload["integrated_failure_contrasts"] == []
    assert payload["decision"]["collection_run_allowed"] is False
    assert payload["decision"]["label_run_allowed"] is False
    assert payload["decision"]["runtime_changes_allowed"] is False
    assert payload["decision"]["selector_training_allowed"] is False
    assert payload["decision"]["stage7_promotion_allowed"] is False
    assert payload["decision"]["stage8_training_allowed"] is False


def test_failure_contrast_integration_fixture_ready_after_four_valid_unique_failures():
    payload = _integration.build_payload(
        plan=_plan(existing=1, needed=4),
        manifest=_manifest(job_count=4),
        output_validation=_validation(
            "protected_plan_window_failure_contrast_outputs_valid_ready_for_integration",
            valid_count=4,
        ),
    )

    assert (
        payload["decision"]["status"]
        == "protected_plan_window_failure_contrast_integration_ready_for_passive_benchmark_refresh"
    )
    assert payload["summary"]["existing_unique_failure_count"] == 1
    assert payload["summary"]["integrated_new_failure_count"] == 4
    assert payload["summary"]["projected_unique_failure_count"] == 5
    assert payload["summary"]["integration_ready"] is True
    assert len(payload["integrated_failure_contrasts"]) == 4
    assert {row["h40_outcome_label"] for row in payload["integrated_failure_contrasts"]} == {
        "conversion_failure"
    }
    assert payload["decision"]["runtime_changes_allowed"] is False
    assert payload["decision"]["label_run_allowed"] is False
    assert payload["decision"]["stage8_training_allowed"] is False


def test_failure_contrast_integration_fixture_blocks_invalid_outputs():
    payload = _integration.build_payload(
        plan=_plan(existing=1, needed=4),
        manifest=_manifest(job_count=4),
        output_validation=_validation(
            "protected_plan_window_failure_contrast_outputs_invalid_block_integration",
            valid_count=4,
        ),
    )

    assert (
        payload["decision"]["status"]
        == "protected_plan_window_failure_contrast_integration_blocked_invalid_outputs"
    )
    assert payload["summary"]["integration_ready"] is False
    assert payload["summary"]["integrated_new_failure_count"] == 0
    assert payload["summary"]["projected_unique_failure_count"] == 1
    assert payload["summary"]["skipped_counts"][
        "validation_status_not_ready_for_integration"
    ] == 4
    assert payload["integrated_failure_contrasts"] == []
    assert payload["decision"]["label_run_allowed"] is False
    assert payload["decision"]["runtime_changes_allowed"] is False


def test_failure_contrast_integration_routes_pending_outputs_missing_collection_option_to_gate_review():
    output_validation = _validation(
        (
            "protected_plan_window_failure_contrast_outputs_validation_pending_"
            "protected_failure_contrast_control_plane_gate_review"
        ),
        valid_count=0,
    )
    output_validation["summary"][
        "protected_failure_contrast_collection_option_available"
    ] = False
    output_validation["summary"][
        "protected_failure_contrast_collection_command_available"
    ] = False
    output_validation["summary"][
        "protected_failure_contrast_collection_option_id"
    ] = None
    output_validation["summary"][
        "protected_failure_contrast_collection_blocked_by_option_id"
    ] = "review_protected_plan_window_failure_contrast_execution_readiness"

    payload = _integration.build_payload(
        plan=_plan(existing=1, needed=4),
        manifest=_manifest(job_count=4),
        output_validation=output_validation,
    )

    assert (
        payload["decision"]["status"]
        == "protected_plan_window_failure_contrast_integration_pending_outputs_"
        "protected_failure_contrast_control_plane_gate_review"
    )
    assert (
        payload["decision"]["recommended_next_step"]
        == "review_current_control_plane_gate_for_protected_failure_contrast_collection"
    )
    assert (
        payload["summary"]["protected_failure_contrast_collection_option_available"]
        is False
    )
    assert (
        payload["summary"]["protected_failure_contrast_collection_command_available"]
        is False
    )
    assert (
        payload["summary"][
            "protected_failure_contrast_collection_blocked_by_option_id"
        ]
        == "review_protected_plan_window_failure_contrast_execution_readiness"
    )
    assert payload["summary"]["integrated_new_failure_count"] == 0
    assert payload["decision"]["collection_run_allowed"] is False
    assert payload["decision"]["label_run_allowed"] is False
    assert payload["decision"]["runtime_changes_allowed"] is False
