#!/usr/bin/env python3
"""Tests for replay-free Stage 7 clean success backfill audit."""

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
    "audit_stage7_clean_success_control_backfill_v0",
    "scripts/audit_stage7_clean_success_control_backfill_v0.py",
)


def _read_report() -> dict:
    payload = json.loads(
        (
            ROOT / "reports/structural_candidates/stage7_clean_success_backfill_audit_v0.json"
        ).read_text(encoding="utf-8")
    )
    assert isinstance(payload, dict)
    return payload


def test_stage7_clean_success_backfill_audit_preserves_boundaries():
    payload = _read_report()

    assert payload["schema_version"] == "stage7_clean_success_backfill_audit.v0"
    assert payload["causal_status"] == "non_causal_replay_free_backfill_audit"
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
    assert payload["decision"]["runtime_changes_allowed"] is False
    assert payload["decision"]["label_run_allowed"] is False
    assert payload["decision"]["selector_training_allowed"] is False
    assert payload["decision"]["stage7_promotion_allowed"] is False
    assert payload["decision"]["stage8_training_allowed"] is False


def test_stage7_clean_success_backfill_audit_reports_closed_gate():
    payload = _read_report()
    summary = payload["summary"]

    assert (
        payload["decision"]["status"]
        == "stage7_clean_success_backfill_available"
    )
    assert summary["current_clean_success_controls"] == 11
    assert summary["clean_success_controls_required"] == 5
    assert summary["manifest_unique_success_controls"] == 11
    assert summary["eligible_new_success_controls"] == 0
    assert summary["can_close_success_gate_replay_free"] is True
    assert summary["sandbox_sourced_post_box_success_controls"] > 0
    assert summary["sandbox_sourced_controls_usable_for_clean_gate"] is False
    assert payload["clean_success_key_audit"]["raw_row_count"] > summary[
        "manifest_unique_success_controls"
    ]


def test_stage7_clean_success_backfill_fixture_can_detect_available_key(tmp_path):
    manifest = {
        "rows": [
            {
                "artifact": "fixture.json",
                "candidate_for_clean_control_recovery": True,
                "classification": "clean_fixture_candidate",
                "default_off_or_baseline_marker": True,
            }
        ]
    }
    clean_recovery = {
        "acceptance": {"clean_sequence_success_controls_required": 1},
        "controls": [],
    }
    post_box_recovery = {"controls": []}

    fixture_artifact = {
        "handoff_packets": [
            {
                "phase": "playout_summary",
                "evidence_terms": {
                    "label": "box_shrink",
                    "fen": "8/8/8/8/8/8/8/K1kR4 w - - 0 1",
                    "move": "d1d8",
                    "playout_result": "mate",
                    "plies": 1,
                    "max_plies": 40,
                },
            }
        ]
    }

    original_root = _audit.ROOT
    try:
        (tmp_path / "fixture.json").write_text(
            json.dumps(fixture_artifact),
            encoding="utf-8",
        )
        _audit.ROOT = tmp_path
        payload = _audit.build_payload(
            manifest=manifest,
            clean_recovery=clean_recovery,
            post_box_recovery=post_box_recovery,
        )
    finally:
        _audit.ROOT = original_root

    assert payload["summary"]["eligible_new_success_controls"] == 1
    assert payload["summary"]["can_close_success_gate_replay_free"] is True
    assert payload["decision"]["status"] == "stage7_clean_success_backfill_available"
