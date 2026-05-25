#!/usr/bin/env python3
"""Tests for reviewed Stage 7 diverse clean sampling manifest."""

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
    "write_stage7_diverse_clean_sampling_manifest_v0",
    "scripts/write_stage7_diverse_clean_sampling_manifest_v0.py",
)
_readiness = _load_module(
    "validate_stage7_diverse_clean_sampling_execution_readiness_v0",
    "scripts/validate_stage7_diverse_clean_sampling_execution_readiness_v0.py",
)
_integration = _load_module(
    "integrate_stage7_diverse_clean_sampling_results_v0",
    "scripts/integrate_stage7_diverse_clean_sampling_results_v0.py",
)
_runner = _load_module(
    "run_stage7_diverse_clean_sampling_jobs_v0",
    "scripts/run_stage7_diverse_clean_sampling_jobs_v0.py",
)


def _read_report(path: str) -> dict:
    payload = json.loads((ROOT / path).read_text(encoding="utf-8"))
    assert isinstance(payload, dict)
    return payload


def test_stage7_diverse_clean_sampling_manifest_requires_approval():
    payload = _read_report(
        "reports/structural_candidates/stage7_diverse_clean_sampling_manifest_v0.json"
    )

    assert payload["schema_version"] == "stage7_diverse_clean_sampling_manifest.v0"
    assert payload["causal_status"] == "non_causal_label_manifest_review_only"
    assert payload["runtime_behavior_changed"] is False
    assert payload["runtime_selector_implemented"] is False
    assert payload["runtime_score_changes"] is False
    assert payload["runtime_direct_routing"] is False
    assert payload["runtime_dtm_or_tablebase_lookup"] is False
    assert payload["gameplay_topology_mutation"] is False
    assert payload["stage7_promotion_allowed"] is False
    assert payload["stage8_training_allowed"] is False
    assert (
        payload["decision"]["status"]
        == "stage7_diverse_clean_sampling_manifest_review_ready_pending_explicit_approval"
    )
    assert payload["decision"]["implementation_authorized_by_this_manifest"] is False
    assert payload["decision"]["runtime_changes_allowed"] is False
    assert payload["decision"]["stage7_promotion_allowed"] is False
    assert payload["decision"]["stage8_training_allowed"] is False
    assert payload["summary"]["job_count"] == 8
    assert payload["summary"]["max_total_samples"] == 64
    assert payload["summary"]["topology_exists"] is True
    assert payload["summary"]["label_run_allowed_by_this_manifest"] is False
    assert payload["summary"]["stage7_training_row_count"] == 0


def test_stage7_diverse_clean_sampling_jobs_are_bounded_and_clean():
    payload = _read_report(
        "reports/structural_candidates/stage7_diverse_clean_sampling_manifest_v0.json"
    )

    forbidden_flags = set(payload["jobs"][0]["forbidden_flags"])
    assert "--enable-stage7-king-tempo" in forbidden_flags
    assert "--enable-candidate-move-layer" in forbidden_flags
    for job in payload["jobs"]:
        command = job["command"]
        assert job["samples"] == 8
        assert job["playout_max_plies"] == 40
        assert job["runtime_work_allowed"] is False
        assert job["stage7_training_row"] is False
        assert job["stage7_promotion_allowed"] is False
        assert job["stage8_training_allowed"] is False
        for flag in job["forbidden_flags"]:
            assert flag not in command
        assert "--label" in command
        assert command[command.index("--label") + 1] == "box_shrink"
        assert "--source-stage-names" in command
        assert "--playout-max-plies" in command
        assert command[command.index("--playout-max-plies") + 1] == "40"


def test_stage7_diverse_clean_sampling_manifest_fixture_uses_active_topology():
    active_stack = {
        "active_protected_stack": {
            "stage6_drive_overlay": {
                "topology": "snapshots/krk_triplet_pipeline/clean_retrain_checkpoint_v0_retry1/stage6_overlay_composed/topology/krk_entry_topology.json"
            }
        }
    }
    recovery = {
        "acceptance": {"clean_sequence_success_controls_required": 5},
        "summary": {
            "role_counts": {
                "clean_sequence_success_control": 2,
                "clean_sequence_hard_negative": 8,
            }
        },
    }
    sampling_review = {"summary": {"sampling_overlap_detected": True}}

    payload = _manifest.build_payload(
        active_stack=active_stack,
        recovery=recovery,
        sampling_review=sampling_review,
    )

    assert payload["summary"]["job_count"] == 8
    assert payload["summary"]["label_run_allowed_by_this_manifest"] is False
    assert payload["jobs"][0]["topology"] == active_stack["active_protected_stack"]["stage6_drive_overlay"]["topology"]
    assert payload["current_gap"]["clean_sequence_success_controls_have"] == 2
    assert payload["current_gap"]["clean_sequence_hard_negatives_have"] == 8
    assert payload["decision"]["implementation_authorized_by_this_manifest"] is False


def test_stage7_diverse_clean_sampling_execution_readiness_still_requires_approval():
    payload = _read_report(
        "reports/structural_candidates/stage7_diverse_clean_sampling_execution_readiness_v0.json"
    )

    assert payload["schema_version"] == "stage7_diverse_clean_sampling_execution_readiness.v0"
    assert payload["causal_status"] == "non_causal_execution_readiness_check"
    assert payload["runtime_behavior_changed"] is False
    assert payload["runtime_selector_implemented"] is False
    assert payload["runtime_score_changes"] is False
    assert payload["runtime_direct_routing"] is False
    assert payload["runtime_dtm_or_tablebase_lookup"] is False
    assert payload["gameplay_topology_mutation"] is False
    assert payload["stage7_promotion_allowed"] is False
    assert payload["stage8_training_allowed"] is False
    assert payload["summary"]["job_count"] == 8
    assert payload["summary"]["jobs_passing_readiness"] == 8
    assert payload["summary"]["all_jobs_pass_readiness"] is True
    assert payload["summary"]["max_total_samples"] == 64
    assert payload["summary"]["max_horizon"] == 40
    assert payload["summary"]["manifest_blocks_execution"] is True
    assert payload["summary"]["execution_authorized_by_this_report"] is False
    assert payload["summary"]["stage7_training_row_count"] == 0
    assert (
        payload["decision"]["status"]
        == "stage7_diverse_clean_sampling_execution_ready_pending_explicit_approval"
    )
    assert payload["decision"]["execution_authorized_by_this_report"] is False
    assert payload["decision"]["runtime_changes_allowed"] is False
    assert payload["decision"]["label_run_allowed"] is False
    assert payload["decision"]["stage7_promotion_allowed"] is False
    assert payload["decision"]["stage8_training_allowed"] is False


def test_stage7_diverse_clean_sampling_readiness_fixture_detects_forbidden_flag():
    manifest = {
        "decision": {"implementation_authorized_by_this_manifest": False},
        "summary": {"label_run_allowed_by_this_manifest": False},
        "jobs": [
            {
                "job_id": "bad",
                "command": [
                    "uv",
                    "run",
                    "python",
                    "scripts/test_krk_landmark_progress.py",
                    "--enable-stage7-plan-capsule",
                ],
                "forbidden_flags": ["--enable-stage7-plan-capsule"],
                "topology": "reports/current_agent_brief.md",
                "json_output": "reports/nonexistent_stage7_test_output.json",
                "samples": 8,
                "playout_max_plies": 40,
            }
        ],
    }

    payload = _readiness.build_payload(manifest=manifest)

    assert payload["summary"]["all_jobs_pass_readiness"] is False
    assert payload["job_checks"][0]["forbidden_flag_hits"] == ["--enable-stage7-plan-capsule"]
    assert payload["decision"]["status"] == "stage7_diverse_clean_sampling_execution_readiness_failed"
    assert payload["decision"]["label_run_allowed"] is False


def test_stage7_diverse_clean_sampling_integration_waits_for_outputs():
    payload = _read_report(
        "reports/structural_candidates/stage7_diverse_clean_sampling_integration_v0.json"
    )

    assert payload["schema_version"] == "stage7_diverse_clean_sampling_integration.v0"
    assert payload["causal_status"] == "non_causal_post_label_integration"
    assert payload["runtime_behavior_changed"] is False
    assert payload["runtime_selector_implemented"] is False
    assert payload["runtime_score_changes"] is False
    assert payload["runtime_direct_routing"] is False
    assert payload["runtime_dtm_or_tablebase_lookup"] is False
    assert payload["gameplay_topology_mutation"] is False
    assert payload["stage7_promotion_allowed"] is False
    assert payload["stage8_training_allowed"] is False
    assert payload["summary"]["job_count"] == 8
    assert payload["summary"]["outputs_present_count"] == 0
    assert payload["summary"]["combined_success_controls"] == 2
    assert payload["summary"]["success_controls_met"] is False
    assert payload["summary"]["stage7_training_row_count"] == 0
    assert payload["summary"]["selector_training_row_count"] == 0
    assert payload["summary"]["runtime_authorization_row_count"] == 0
    assert payload["decision"]["status"] == "stage7_diverse_clean_sampling_outputs_pending"
    assert payload["decision"]["runtime_changes_allowed"] is False
    assert payload["decision"]["label_run_allowed"] is False
    assert payload["decision"]["selector_training_allowed"] is False


def test_stage7_diverse_clean_sampling_integration_fixture_closes_success_gap(tmp_path, monkeypatch):
    output = tmp_path / "out.json"
    output.write_text(
        json.dumps(
            {
                "handoff_packets": [
                    {
                        "phase": "post_opponent_reply",
                        "evidence_terms": {
                            "label": "box_shrink",
                            "fen": "8/8/8/8/8/8/8/8 w - - 0 1",
                            "move": "a1a2",
                            "successor_selected_skill": "krk.edge_trap_close",
                            "successor_skills": {
                                "krk.edge_trap_close": {"best_move": "a2a8"}
                            },
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
                    {
                        "phase": "post_opponent_reply",
                        "evidence_terms": {
                            "label": "box_shrink",
                            "fen": "8/8/8/8/8/8/8/7K w - - 0 1",
                            "move": "h1h2",
                            "successor_selected_skill": "krk.stage0_basin",
                            "successor_skills": {
                                "krk.stage0_basin": {"best_move": "h2h8"}
                            },
                        },
                    },
                    {
                        "phase": "playout_summary",
                        "evidence_terms": {
                            "label": "box_shrink",
                            "fen": "8/8/8/8/8/8/8/7K w - - 0 1",
                            "move": "h1h2",
                            "playout_result": "mate",
                            "plies": 21,
                            "max_plies": 40,
                        },
                    },
                    {
                        "phase": "post_opponent_reply",
                        "evidence_terms": {
                            "label": "box_shrink",
                            "fen": "8/8/8/8/8/8/K7/8 w - - 0 1",
                            "move": "a2a3",
                            "successor_selected_skill": "krk.stage0_basin",
                            "successor_skills": {
                                "krk.stage0_basin": {"best_move": "a3a8"}
                            },
                        },
                    },
                    {
                        "phase": "playout_summary",
                        "evidence_terms": {
                            "label": "box_shrink",
                            "fen": "8/8/8/8/8/8/K7/8 w - - 0 1",
                            "move": "a2a3",
                            "playout_result": "mate",
                            "plies": 22,
                            "max_plies": 40,
                        },
                    },
                ]
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(_integration, "ROOT", tmp_path)
    manifest = {
        "jobs": [
            {
                "job_id": "fixture.job",
                "json_output": "out.json",
                "source_stage_names": ["Box_Small"],
            }
        ]
    }
    base_controls = {
        "acceptance": {
            "clean_sequence_success_controls_required": 5,
            "clean_sequence_hard_negatives_required": 5,
        },
        "controls": [
            {"control_role": "clean_sequence_success_control"},
            {"control_role": "clean_sequence_success_control"},
            *[{"control_role": "clean_sequence_hard_negative"} for _ in range(8)],
        ],
    }

    payload = _integration.build_payload(manifest=manifest, base_controls=base_controls)

    assert (
        payload["decision"]["status"]
        == "stage7_diverse_clean_sampling_integration_success_controls_met"
    )
    assert payload["summary"]["combined_success_controls"] == 5
    assert payload["summary"]["success_controls_met"] is True
    assert payload["decision"]["label_run_allowed"] is False


def test_stage7_diverse_clean_sampling_integration_blocks_invalid_validated_outputs():
    manifest = {
        "jobs": [
            {
                "job_id": "fixture.bad",
                "json_output": "bad.json",
                "source_stage_names": ["Box_Small"],
            }
        ]
    }
    base_controls = {
        "acceptance": {
            "clean_sequence_success_controls_required": 5,
            "clean_sequence_hard_negatives_required": 5,
        },
        "controls": [
            {"control_role": "clean_sequence_success_control"},
            {"control_role": "clean_sequence_success_control"},
            *[{"control_role": "clean_sequence_hard_negative"} for _ in range(8)],
        ],
    }
    output_validation = {
        "summary": {
            "output_exists_count": 1,
            "all_outputs_present": False,
            "stage7_training_row_count": 0,
        },
        "output_checks": [
            {
                "job_id": "fixture.bad",
                "json_output": "bad.json",
                "output_exists": True,
                "valid": False,
                "issues": {"mate_after_manifest_horizon": 1},
            }
        ],
        "decision": {
            "status": "stage7_diverse_clean_sampling_outputs_invalid_block_integration",
            "runtime_changes_allowed": False,
            "label_run_allowed": False,
            "stage7_promotion_allowed": False,
            "stage8_training_allowed": False,
        },
    }

    payload = _integration.build_payload(
        manifest=manifest,
        base_controls=base_controls,
        output_validation=output_validation,
    )

    assert (
        payload["decision"]["status"]
        == "stage7_diverse_clean_sampling_integration_blocked_invalid_outputs"
    )
    assert payload["summary"]["validation_blocks_integration"] is True
    assert payload["summary"]["new_control_count"] == 0
    assert payload["new_controls"] == []
    assert payload["summary"]["stage7_training_row_count"] == 0
    assert payload["summary"]["selector_training_row_count"] == 0
    assert payload["summary"]["runtime_authorization_row_count"] == 0
    assert payload["decision"]["runtime_changes_allowed"] is False
    assert payload["decision"]["label_run_allowed"] is False
    assert payload["decision"]["stage7_promotion_allowed"] is False
    assert payload["decision"]["stage8_training_allowed"] is False


def test_stage7_diverse_clean_sampling_runner_defaults_to_dry_run():
    payload = _read_report(
        "reports/structural_candidates/stage7_diverse_clean_sampling_runner_v0.json"
    )

    assert payload["schema_version"] == "stage7_diverse_clean_sampling_runner.v0"
    assert payload["causal_status"] == "non_causal_label_runner_wrapper"
    assert payload["runtime_behavior_changed"] is False
    assert payload["runtime_selector_implemented"] is False
    assert payload["runtime_score_changes"] is False
    assert payload["runtime_direct_routing"] is False
    assert payload["runtime_dtm_or_tablebase_lookup"] is False
    assert payload["gameplay_topology_mutation"] is False
    assert payload["stage7_promotion_allowed"] is False
    assert payload["stage8_training_allowed"] is False
    assert payload["execution_requested"] is False
    assert payload["summary"]["dry_run"] is True
    assert payload["summary"]["job_count"] == 8
    assert payload["summary"]["processed_job_count"] == 0
    assert payload["summary"]["executed_job_count"] == 0
    assert payload["summary"]["refresh_after_run_requested"] is False
    assert payload["summary"]["refresh_after_run_performed"] is False
    assert payload["summary"]["stage7_training_row_count"] == 0
    assert payload["summary"]["runtime_authorization_row_count"] == 0
    assert payload["post_run_refresh"] is None
    assert payload["decision"]["status"] == "stage7_diverse_clean_sampling_runner_dry_run_ready"
    assert payload["decision"]["label_run_allowed"] is False
    assert payload["decision"]["runtime_changes_allowed"] is False
    assert payload["decision"]["selector_training_allowed"] is False
    assert payload["decision"]["stage7_promotion_allowed"] is False
    assert payload["decision"]["stage8_training_allowed"] is False
    for command in payload["commands"]:
        assert command["would_execute"] is False


def test_stage7_diverse_clean_sampling_runner_blocks_when_readiness_fails():
    manifest = {
        "decision": {
            "status": "stage7_diverse_clean_sampling_manifest_review_ready_pending_explicit_approval",
            "runtime_changes_allowed": False,
            "stage7_promotion_allowed": False,
            "stage8_training_allowed": False,
        },
        "jobs": [
            {
                "job_id": "fixture.job",
                "command": ["uv", "run", "python", "scripts/test_krk_landmark_progress.py"],
                "json_output": "reports/fixture.json",
            }
        ],
    }
    readiness = {
        "decision": {"status": "stage7_diverse_clean_sampling_execution_readiness_failed"},
        "summary": {"all_jobs_pass_readiness": False},
    }

    blockers = _runner._validate_ready(manifest, readiness)
    assert "execution_readiness_not_ready" in blockers
    payload = _runner.build_payload(execute=False, max_jobs=1)
    assert payload["summary"]["executed_job_count"] == 0
    assert payload["commands"][0]["would_execute"] is False


def test_stage7_diverse_clean_sampling_runner_refresh_requires_execution():
    payload = _runner.build_payload(
        execute=False,
        max_jobs=1,
        refresh_after_run=True,
    )

    assert payload["summary"]["executed_job_count"] == 0
    assert payload["summary"]["refresh_after_run_requested"] is True
    assert payload["summary"]["refresh_after_run_performed"] is False
    assert payload["post_run_refresh"] is None
    assert payload["decision"]["label_run_allowed"] is False


def test_stage7_diverse_clean_sampling_runner_skips_existing_outputs_by_default(
    tmp_path, monkeypatch
):
    existing_output = tmp_path / "existing.json"
    existing_output.write_text(json.dumps({"handoff_packets": []}), encoding="utf-8")
    manifest_path = tmp_path / "manifest.json"
    readiness_path = tmp_path / "readiness.json"
    manifest_path.write_text(
        json.dumps(
            {
                "decision": {
                    "status": "stage7_diverse_clean_sampling_manifest_review_ready_pending_explicit_approval",
                    "runtime_changes_allowed": False,
                    "stage7_promotion_allowed": False,
                    "stage8_training_allowed": False,
                },
                "summary": {"label_run_allowed_by_this_manifest": False},
                "jobs": [
                    {
                        "job_id": "fixture.existing",
                        "command": ["uv", "run", "python", "scripts/should_not_run.py"],
                        "json_output": "existing.json",
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    readiness_path.write_text(
        json.dumps(
            {
                "decision": {
                    "status": "stage7_diverse_clean_sampling_execution_ready_pending_explicit_approval"
                },
                "summary": {"all_jobs_pass_readiness": True},
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(_runner, "ROOT", tmp_path)
    monkeypatch.setattr(_runner, "MANIFEST", manifest_path)
    monkeypatch.setattr(_runner, "READINESS", readiness_path)

    payload = _runner.build_payload(execute=True, max_jobs=1)

    assert payload["summary"]["processed_job_count"] == 1
    assert payload["summary"]["executed_job_count"] == 0
    assert payload["summary"]["skipped_existing_output_count"] == 1
    assert payload["summary"]["failed_job_count"] == 0
    assert payload["summary"]["overwrite_existing_outputs"] is False
    assert payload["commands"][0]["would_execute"] is False
    assert payload["commands"][0]["would_skip_existing_output"] is True
    assert payload["executed_jobs"][0]["skipped_existing_output"] is True
    assert payload["decision"]["runtime_changes_allowed"] is False
    assert payload["decision"]["stage7_promotion_allowed"] is False
    assert payload["decision"]["stage8_training_allowed"] is False


def test_stage7_diverse_clean_sampling_runner_blocks_invalid_existing_outputs_without_overwrite(
    tmp_path, monkeypatch
):
    existing_output = tmp_path / "bad.json"
    existing_output.write_text(json.dumps({"handoff_packets": []}), encoding="utf-8")
    manifest_path = tmp_path / "manifest.json"
    readiness_path = tmp_path / "readiness.json"
    manifest_path.write_text(
        json.dumps(
            {
                "decision": {
                    "status": "stage7_diverse_clean_sampling_manifest_review_ready_pending_explicit_approval",
                    "runtime_changes_allowed": False,
                    "stage7_promotion_allowed": False,
                    "stage8_training_allowed": False,
                },
                "summary": {"label_run_allowed_by_this_manifest": False},
                "jobs": [
                    {
                        "job_id": "fixture.bad",
                        "command": ["uv", "run", "python", "scripts/should_not_run.py"],
                        "json_output": "bad.json",
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    readiness_path.write_text(
        json.dumps(
            {
                "decision": {
                    "status": "stage7_diverse_clean_sampling_execution_ready_pending_explicit_approval"
                },
                "summary": {"all_jobs_pass_readiness": True},
            }
        ),
        encoding="utf-8",
    )
    output_validation = {
        "output_checks": [
            {
                "job_id": "fixture.bad",
                "json_output": "bad.json",
                "output_exists": True,
                "valid": False,
            }
        ],
        "decision": {
            "status": "stage7_diverse_clean_sampling_outputs_invalid_block_integration"
        },
    }
    monkeypatch.setattr(_runner, "ROOT", tmp_path)
    monkeypatch.setattr(_runner, "MANIFEST", manifest_path)
    monkeypatch.setattr(_runner, "READINESS", readiness_path)

    payload = _runner.build_payload(
        execute=True,
        max_jobs=1,
        output_validation=output_validation,
    )

    assert (
        "invalid_existing_outputs_require_overwrite_or_cleanup"
        in payload["execution_blockers"]
    )
    assert payload["summary"]["invalid_existing_output_count"] == 1
    assert payload["summary"]["processed_job_count"] == 0
    assert payload["summary"]["executed_job_count"] == 0
    assert payload["commands"][0]["would_execute"] is False
    assert payload["decision"]["status"] == "stage7_diverse_clean_sampling_runner_blocked"
    assert payload["decision"]["label_run_allowed"] is False
