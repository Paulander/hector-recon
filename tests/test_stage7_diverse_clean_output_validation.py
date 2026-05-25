#!/usr/bin/env python3
"""Tests for passive Stage 7 diverse-clean output validation."""

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


_validation = _load_module(
    "validate_stage7_diverse_clean_sampling_outputs_v0",
    "scripts/validate_stage7_diverse_clean_sampling_outputs_v0.py",
)


def _read_report() -> dict:
    payload = json.loads(
        (
            ROOT
            / "reports/structural_candidates/stage7_diverse_clean_sampling_output_validation_v0.json"
        ).read_text()
    )
    assert isinstance(payload, dict)
    return payload


def test_stage7_diverse_clean_output_validation_waits_for_outputs():
    payload = _read_report()

    assert payload["schema_version"] == "stage7_diverse_clean_sampling_output_validation.v0"
    assert payload["causal_status"] == "non_causal_output_validation"
    assert payload["runtime_behavior_changed"] is False
    assert payload["runtime_selector_implemented"] is False
    assert payload["runtime_score_changes"] is False
    assert payload["runtime_direct_routing"] is False
    assert payload["runtime_dtm_or_tablebase_lookup"] is False
    assert payload["gameplay_topology_mutation"] is False
    assert payload["stage7_promotion_allowed"] is False
    assert payload["stage8_training_allowed"] is False
    assert payload["summary"]["job_count"] == 8
    assert payload["summary"]["output_exists_count"] == 0
    assert payload["summary"]["output_valid_count"] == 0
    assert payload["summary"]["stage7_training_row_count"] == 0
    assert payload["summary"]["selector_training_row_count"] == 0
    assert payload["summary"]["runtime_authorization_row_count"] == 0
    assert (
        payload["decision"]["status"]
        == "stage7_diverse_clean_sampling_outputs_validation_pending"
    )
    assert payload["decision"]["label_run_allowed"] is False
    assert payload["decision"]["runtime_changes_allowed"] is False
    assert payload["decision"]["stage7_promotion_allowed"] is False
    assert payload["decision"]["stage8_training_allowed"] is False


def test_stage7_diverse_clean_output_validation_fixture_accepts_valid_outputs(
    tmp_path, monkeypatch
):
    out_a = tmp_path / "a.json"
    out_b = tmp_path / "b.json"
    payload = {
        "handoff_packets": [
            {
                "phase": "post_opponent_reply",
                "evidence_terms": {
                    "label": "box_shrink",
                    "fen": "8/8/8/8/8/8/8/8 w - - 0 1",
                    "move": "a1a2",
                },
            },
            {
                "phase": "playout_summary",
                "evidence_terms": {
                    "label": "box_shrink",
                    "fen": "8/8/8/8/8/8/8/8 w - - 0 1",
                    "move": "a1a2",
                    "playout_result": "mate",
                    "plies": 20,
                    "max_plies": 40,
                },
            },
        ]
    }
    out_a.write_text(json.dumps(payload), encoding="utf-8")
    out_b.write_text(json.dumps(payload), encoding="utf-8")
    monkeypatch.setattr(_validation, "ROOT", tmp_path)

    result = _validation.build_payload(
        manifest={
            "jobs": [
                {
                    "job_id": "a",
                    "json_output": "a.json",
                    "playout_max_plies": 40,
                },
                {
                    "job_id": "b",
                    "json_output": "b.json",
                    "playout_max_plies": 40,
                },
            ]
        }
    )

    assert (
        result["decision"]["status"]
        == "stage7_diverse_clean_sampling_outputs_valid_ready_for_integration"
    )
    assert result["summary"]["output_exists_count"] == 2
    assert result["summary"]["output_valid_count"] == 2
    assert result["summary"]["all_outputs_valid"] is True
    assert result["summary"]["stage7_training_row_count"] == 0
    assert result["decision"]["runtime_changes_allowed"] is False


def test_stage7_diverse_clean_output_validation_fixture_rejects_bad_horizon(
    tmp_path, monkeypatch
):
    out = tmp_path / "bad.json"
    out.write_text(
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
                            "plies": 41,
                            "max_plies": 40,
                        },
                    }
                ]
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(_validation, "ROOT", tmp_path)

    result = _validation.build_payload(
        manifest={
            "jobs": [
                {
                    "job_id": "bad",
                    "json_output": "bad.json",
                    "playout_max_plies": 40,
                }
            ]
        }
    )

    assert (
        result["decision"]["status"]
        == "stage7_diverse_clean_sampling_outputs_invalid_block_integration"
    )
    assert result["summary"]["issue_counts"]["mate_after_manifest_horizon"] == 1
    assert result["summary"]["all_outputs_valid"] is False
    assert result["decision"]["label_run_allowed"] is False
