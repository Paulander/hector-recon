#!/usr/bin/env python3
"""Tests for passive Stage 7 diverse-clean label distribution review."""

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


_review = _load_module(
    "review_stage7_diverse_clean_label_distribution_v0",
    "scripts/review_stage7_diverse_clean_label_distribution_v0.py",
)


def _read_report() -> dict:
    payload = json.loads(
        (
            ROOT
            / "reports/structural_candidates/stage7_diverse_clean_label_distribution_review_v0.json"
        ).read_text(encoding="utf-8")
    )
    assert isinstance(payload, dict)
    return payload


def test_stage7_label_distribution_review_reports_closed_success_gap():
    payload = _read_report()

    assert payload["schema_version"] == "stage7_diverse_clean_label_distribution_review.v0"
    assert payload["causal_status"] == "non_causal_label_distribution_review"
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

    summary = payload["summary"]
    assert summary["validation_status"] == (
        "stage7_diverse_clean_sampling_outputs_valid_ready_for_integration"
    )
    assert summary["job_count"] == 8
    assert summary["raw_playout_count"] == 64
    assert summary["raw_result_counts"] == {"mate": 24, "max_plies": 40}
    assert summary["unique_output_success_key_count"] == 4
    assert summary["unique_new_success_key_count_vs_pre_run"] == 2
    assert summary["success_controls"] == 11
    assert summary["success_controls_required"] == 5
    assert summary["success_gap"] == 0
    assert summary["stage7_training_row_count"] == 0
    assert summary["selector_training_row_count"] == 0
    assert summary["runtime_authorization_row_count"] == 0

    assert "label_distribution_duplicate_dominated" in payload["findings"]
    assert (
        "stage7.diverse_clean.edge_fence_deep.seed107.samples8.h40"
        in payload["followup_sampling_guidance"]["highest_yield_job_ids"]
    )
    assert payload["followup_sampling_guidance"][
        "minimum_additional_unique_success_controls_needed"
    ] == 0
    assert payload["followup_sampling_guidance"][
        "requires_explicit_approval_before_any_label_execution"
    ] is True
    assert (
        payload["decision"]["status"]
        == "stage7_label_distribution_review_success_gate_closed"
    )
    assert payload["decision"]["label_run_allowed"] is False
    assert payload["decision"]["runtime_changes_allowed"] is False
    assert payload["decision"]["stage7_promotion_allowed"] is False
    assert payload["decision"]["stage8_training_allowed"] is False


def test_stage7_label_distribution_review_fixture_detects_closed_gap(tmp_path, monkeypatch):
    output = tmp_path / "out.json"
    output.write_text(
        json.dumps(
            {
                "handoff_packets": [
                    {
                        "phase": "playout_summary",
                        "evidence_terms": {
                            "label": "box_shrink",
                            "fen": "8/8/8/8/8/8/8/8 w - - 0 1",
                            "move": "a1a2",
                            "playout_result": "mate",
                            "plies": 12,
                            "max_plies": 40,
                        },
                    }
                ]
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(_review, "ROOT", tmp_path)

    payload = _review.build_payload(
        manifest={
            "jobs": [
                {
                    "job_id": "fixture.job",
                    "json_output": "out.json",
                    "source_stage_names": ["Edge_Fence_Deep"],
                }
            ]
        },
        output_validation={
            "decision": {
                "status": "stage7_diverse_clean_sampling_outputs_valid_ready_for_integration"
            }
        },
        integration={
            "summary": {
                "combined_success_controls": 5,
                "success_controls_required": 5,
            }
        },
        clean_recovery={
            "controls": [
                {
                    "fen": "8/8/8/8/8/8/8/8 w - - 0 1",
                    "move_uci": "a1a2",
                    "result": "mate",
                    "source_artifact": "reports/structural_candidates/stage7_diverse_clean_fixture.json",
                }
            ]
        },
    )

    assert payload["summary"]["success_gap"] == 0
    assert payload["decision"]["status"] == "stage7_label_distribution_review_success_gate_closed"
    assert payload["decision"]["label_run_allowed"] is False
    assert payload["decision"]["stage8_training_allowed"] is False
