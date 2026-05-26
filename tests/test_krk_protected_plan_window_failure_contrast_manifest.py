#!/usr/bin/env python3
"""Tests for protected plan-window failure-contrast manifest and review."""

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
    "write_krk_protected_plan_window_failure_contrast_manifest_v0",
    "scripts/write_krk_protected_plan_window_failure_contrast_manifest_v0.py",
)
_review = _load_module(
    "review_krk_protected_plan_window_failure_contrast_manifest_v0",
    "scripts/review_krk_protected_plan_window_failure_contrast_manifest_v0.py",
)
_readiness = _load_module(
    "validate_krk_protected_plan_window_failure_contrast_execution_readiness_v0",
    "scripts/validate_krk_protected_plan_window_failure_contrast_execution_readiness_v0.py",
)
_output_validation = _load_module(
    "validate_krk_protected_plan_window_failure_contrast_outputs_v0",
    "scripts/validate_krk_protected_plan_window_failure_contrast_outputs_v0.py",
)
_runner = _load_module(
    "run_krk_protected_plan_window_failure_contrast_collection_v0",
    "scripts/run_krk_protected_plan_window_failure_contrast_collection_v0.py",
)
_approval_request = _load_module(
    "write_krk_protected_plan_window_failure_contrast_approval_request_v0",
    "scripts/write_krk_protected_plan_window_failure_contrast_approval_request_v0.py",
)


def _read_report(path: str) -> dict:
    payload = json.loads((ROOT / path).read_text(encoding="utf-8"))
    assert isinstance(payload, dict)
    return payload


def _walk_json(value, path=()):
    if isinstance(value, dict):
        for key, child in value.items():
            yield from _walk_json(child, (*path, str(key)))
    elif isinstance(value, list):
        for index, child in enumerate(value):
            yield from _walk_json(child, (*path, str(index)))
    else:
        yield path, value


def _ready_execution_summary(job_count: int = 1) -> dict:
    return {
        "all_jobs_pass_readiness": True,
        "jobs_passing_readiness": job_count,
        "manifest_fingerprint": "m" * 64,
        "readiness_fingerprint": "r" * 64,
    }


def _approval_receipt(job_count: int = 1) -> dict:
    return {
        "schema_version": _runner.APPROVAL_SCHEMA_VERSION,
        "approval_id": "approve_protected_plan_window_failure_contrast_collection",
        "receipt_path": str(_runner.DEFAULT_APPROVAL_RECEIPT.relative_to(ROOT)),
        "approval_scope": {
            "manifest_fingerprint": "m" * 64,
            "readiness_fingerprint": "r" * 64,
            "job_count": job_count,
            "manifest_status": "protected_plan_window_failure_contrast_manifest_ready_for_review",
            "readiness_status": (
                "protected_plan_window_failure_contrast_execution_ready_pending_explicit_approval"
            ),
        },
        "decision": {
            "status": _runner.APPROVAL_STATUS,
            "single_execution_only": True,
            "runtime_changes_allowed": False,
            "label_run_allowed": False,
            "selector_training_allowed": False,
            "stage7_promotion_allowed": False,
            "stage8_training_allowed": False,
        },
    }


def test_checked_in_reports_preserve_protected_collection_receipt_gate():
    stale_next_step = "explicitly_approve_protected_plan_window_failure_contrast_collection"
    protected_runner = "scripts/run_krk_protected_plan_window_failure_contrast_collection_v0.py"
    forbidden_true_keys = {
        "collection_run_allowed",
        "execution_requested",
        "gameplay_topology_mutation",
        "label_run_allowed",
        "runtime_behavior_changed",
        "runtime_changes_allowed",
        "runtime_defaults_changed",
        "runtime_dtm_or_tablebase_lookup",
        "runtime_selector_implemented",
        "selector_training_allowed",
        "stage7_promotion_allowed",
        "stage8_training_allowed",
        "would_execute",
    }

    for base in (ROOT / "reports", ROOT / "scripts"):
        for path in sorted(base.rglob("*")):
            if path.suffix not in {".json", ".md", ".py"}:
                continue
            text = path.read_text(encoding="utf-8")
            relative_path = path.relative_to(ROOT)
            assert stale_next_step not in text, relative_path
            for line_number, line in enumerate(text.splitlines(), start=1):
                if protected_runner in line and "--execute-reviewed-collection" in line:
                    assert "--approval-receipt" in line, f"{relative_path}:{line_number}"

    for path in sorted((ROOT / "reports").rglob("*.json")):
        payload = json.loads(path.read_text(encoding="utf-8"))
        for json_path, value in _walk_json(payload):
            if json_path and json_path[-1] in forbidden_true_keys:
                assert value is not True, f"{path.relative_to(ROOT)}:{'.'.join(json_path)}"


def test_failure_contrast_manifest_is_bounded_review_only():
    payload = _read_report(
        "reports/strategy_arbitration/krk_protected_plan_window_failure_contrast_manifest_v0.json"
    )

    assert payload["schema_version"] == "krk_protected_plan_window_failure_contrast_manifest.v0"
    assert payload["causal_status"] == "non_causal_collection_manifest"
    assert payload["runtime_behavior_changed"] is False
    assert payload["runtime_defaults_changed"] is False
    assert payload["runtime_selector_implemented"] is False
    assert payload["runtime_score_changes"] is False
    assert payload["runtime_direct_routing"] is False
    assert payload["runtime_dtm_or_tablebase_lookup"] is False
    assert payload["gameplay_topology_mutation"] is False
    assert payload["stage7_promotion_allowed"] is False
    assert payload["stage8_training_allowed"] is False
    assert payload["summary"]["job_count"] == 6
    assert payload["summary"]["max_collection_jobs"] == 6
    assert payload["summary"]["minimum_new_unique_failures_needed"] == 4
    assert payload["summary"]["source_stage_counts"] == {
        "stage4": 2,
        "stage5": 2,
        "stage6": 2,
    }
    assert payload["summary"]["missing_required_source_stages"] == []
    assert payload["summary"]["all_bindings_valid"] is True
    assert payload["summary"]["topology_path_safe"] is True
    assert payload["summary"]["topology_exists"] is True
    assert payload["summary"]["output_paths_valid"] is True
    assert payload["summary"]["forbidden_job_flag_count"] == 0
    assert len(payload["summary"]["manifest_fingerprint"]) == 64
    assert payload["summary"]["selector_training_row_count"] == 0
    assert payload["summary"]["runtime_authorization_row_count"] == 0
    assert payload["summary"]["stage7_training_row_count"] == 0
    assert payload["decision"]["collection_run_allowed"] is False
    assert payload["decision"]["label_run_allowed"] is False
    assert payload["decision"]["runtime_changes_allowed"] is False
    assert payload["decision"]["selector_training_allowed"] is False
    assert payload["decision"]["stage7_promotion_allowed"] is False
    assert payload["decision"]["stage8_training_allowed"] is False
    assert {job["source_stage"] for job in payload["jobs"]} == {"stage4", "stage5", "stage6"}
    for job in payload["jobs"]:
        assert job["horizon"] == 40
        assert job["expected_output_json"].startswith(
            "reports/strategy_arbitration/protected_plan_window_failure_contrasts/"
        )
        assert job["labels_generated"] is False
        assert job["usable_for_selector_training"] is False
        assert job["usable_for_runtime_authorization"] is False
        assert job["stage7_heldout_challenge"] is False
        assert job["active_landmark_label"]
        assert job["execution_binding"]["topology_path"]
        assert job["execution_binding"]["composition_profile"] == "handoff_composition_v1"
        assert job["causal_status"] == "non_causal_collection_manifest_job"


def test_failure_contrast_manifest_review_passes_without_authorizing_collection():
    payload = _read_report(
        "reports/strategy_arbitration/krk_protected_plan_window_failure_contrast_manifest_review_v0.json"
    )

    assert (
        payload["schema_version"]
        == "krk_protected_plan_window_failure_contrast_manifest_review.v0"
    )
    assert payload["causal_status"] == "non_causal_collection_manifest_review"
    assert payload["review_summary"]["job_count"] == 6
    assert payload["review_summary"]["required_stages_present"] is True
    assert (
        payload["review_summary"]["recorded_manifest_fingerprint"]
        == payload["review_summary"]["manifest_fingerprint"]
    )
    assert payload["review_summary"]["manifest_fingerprint_matches"] is True
    assert payload["review_summary"]["violation_count"] == 0
    assert payload["review_summary"]["review_passed"] is True
    assert payload["review_summary"]["collection_run_allowed_now"] is False
    assert payload["review_summary"]["label_run_allowed_now"] is False
    assert payload["review_summary"]["runtime_work_allowed"] is False
    assert (
        payload["decision"]["status"]
        == "protected_plan_window_failure_contrast_manifest_review_passed_pending_explicit_approval"
    )
    assert payload["decision"]["collection_run_allowed"] is False
    assert payload["decision"]["label_run_allowed"] is False
    assert payload["decision"]["runtime_changes_allowed"] is False
    assert payload["decision"]["selector_training_allowed"] is False
    assert payload["decision"]["stage7_promotion_allowed"] is False
    assert payload["decision"]["stage8_training_allowed"] is False


def test_failure_contrast_execution_readiness_is_dry_run_only():
    payload = _read_report(
        "reports/strategy_arbitration/krk_protected_plan_window_failure_contrast_execution_readiness_v0.json"
    )

    assert (
        payload["schema_version"]
        == "krk_protected_plan_window_failure_contrast_execution_readiness.v0"
    )
    assert payload["causal_status"] == "non_causal_collection_execution_readiness"
    assert payload["summary"]["job_count"] == 6
    assert payload["summary"]["jobs_passing_readiness"] == 6
    assert payload["summary"]["all_jobs_pass_readiness"] is True
    assert payload["summary"]["job_readiness_blocker_count"] == 0
    assert payload["summary"]["existing_output_count"] == 0
    assert (
        payload["summary"]["recorded_manifest_fingerprint"]
        == payload["summary"]["manifest_fingerprint"]
    )
    assert (
        payload["summary"]["review_manifest_fingerprint"]
        == payload["summary"]["manifest_fingerprint"]
    )
    assert payload["summary"]["manifest_fingerprints_match"] is True
    assert (
        payload["summary"]["protected_stack_status"]
        == "retry1_protected_stage5_6_stack_adopted_manifest_only"
    )
    assert payload["summary"]["protected_stack_ready"] is True
    assert payload["summary"]["protected_stack_rollback_paths_preserved"] is True
    assert payload["summary"]["protected_stack_active_paths_safe"] is True
    assert payload["summary"]["protected_stack_active_paths_exist"] is True
    assert payload["summary"]["protected_stack_rollback_paths_safe"] is True
    assert payload["summary"]["protected_stack_rollback_paths_exist"] is True
    assert (
        payload["summary"]["protected_stack_rollback_common_paths_distinct"] is True
    )
    assert payload["summary"]["protected_stack_filesystem_snapshots_replaced"] is False
    assert payload["summary"]["protected_stack_hard_blockers"] == []
    assert len(payload["summary"]["readiness_fingerprint"]) == 64
    assert (
        payload["decision"]["status"]
        == "protected_plan_window_failure_contrast_execution_ready_pending_explicit_approval"
    )
    assert payload["decision"]["collection_run_allowed"] is False
    assert payload["decision"]["label_run_allowed"] is False
    assert payload["decision"]["runtime_changes_allowed"] is False
    assert payload["decision"]["selector_training_allowed"] is False
    assert payload["decision"]["stage7_promotion_allowed"] is False
    assert payload["decision"]["stage8_training_allowed"] is False


def test_failure_contrast_output_validation_is_pending_before_collection():
    payload = _read_report(
        "reports/strategy_arbitration/krk_protected_plan_window_failure_contrast_output_validation_v0.json"
    )

    assert (
        payload["schema_version"]
        == "krk_protected_plan_window_failure_contrast_output_validation.v0"
    )
    assert payload["causal_status"] == "non_causal_output_validation"
    assert (
        payload["decision"]["status"]
        == "protected_plan_window_failure_contrast_outputs_validation_pending"
    )
    assert payload["summary"]["job_count"] == 6
    assert payload["summary"]["output_exists_count"] == 0
    assert payload["summary"]["output_valid_count"] == 0
    assert payload["summary"]["all_outputs_valid"] is False
    assert payload["summary"]["unique_failure_candidate_count"] == 0
    assert payload["decision"]["collection_run_allowed"] is False
    assert payload["decision"]["label_run_allowed"] is False
    assert payload["decision"]["runtime_changes_allowed"] is False
    assert payload["decision"]["selector_training_allowed"] is False
    assert payload["decision"]["stage7_promotion_allowed"] is False
    assert payload["decision"]["stage8_training_allowed"] is False


def test_failure_contrast_runner_is_dry_run_ready_without_authorizing_collection():
    payload = _read_report(
        "reports/strategy_arbitration/krk_protected_plan_window_failure_contrast_runner_v0.json"
    )

    assert payload["schema_version"] == "krk_protected_plan_window_failure_contrast_runner.v0"
    assert payload["causal_status"] == "non_causal_collection_runner_wrapper"
    assert (
        payload["decision"]["status"]
        == "protected_plan_window_failure_contrast_runner_dry_run_ready"
    )
    assert (
        payload["decision"]["recommended_next_step"]
        == "obtain_matching_approval_receipt_then_run_with_explicit_execute_flag"
    )
    assert payload["execution_requested"] is False
    assert payload["approval_receipt_path"] == (
        "reports/strategy_arbitration/"
        "krk_protected_plan_window_failure_contrast_collection_approval_v0.json"
    )
    assert payload["summary"]["job_count"] == 6
    assert payload["summary"]["processed_job_count"] == 0
    assert payload["summary"]["executed_job_count"] == 0
    assert payload["summary"]["execution_readiness_jobs_passing"] == 6
    assert len(payload["summary"]["execution_readiness_manifest_fingerprint"]) == 64
    assert len(payload["summary"]["execution_readiness_fingerprint"]) == 64
    assert (
        payload["summary"]["execution_readiness_protected_stack_status"]
        == "retry1_protected_stage5_6_stack_adopted_manifest_only"
    )
    assert payload["summary"]["execution_readiness_protected_stack_ready"] is True
    assert (
        payload["summary"][
            "execution_readiness_protected_stack_rollback_paths_preserved"
        ]
        is True
    )
    assert payload["summary"]["execution_readiness_protected_stack_active_paths_safe"] is True
    assert payload["summary"]["execution_readiness_protected_stack_active_paths_exist"] is True
    assert payload["summary"]["execution_readiness_protected_stack_rollback_paths_safe"] is True
    assert payload["summary"]["execution_readiness_protected_stack_rollback_paths_exist"] is True
    assert (
        payload["summary"][
            "execution_readiness_protected_stack_rollback_common_paths_distinct"
        ]
        is True
    )
    assert (
        payload["summary"][
            "execution_readiness_protected_stack_filesystem_snapshots_replaced"
        ]
        is False
    )
    assert payload["summary"]["execution_readiness_protected_stack_hard_blockers"] == []
    assert payload["summary"]["approval_receipt_required_for_execution"] is True
    assert payload["summary"]["approval_receipt_present"] is False
    assert payload["summary"]["approval_receipt_valid"] is False
    assert "approval_receipt_missing" in payload["summary"]["approval_receipt_blockers"]
    assert payload["summary"]["output_exists_count"] == 0
    assert payload["decision"]["collection_run_allowed"] is False
    assert payload["decision"]["label_run_allowed"] is False
    assert payload["decision"]["runtime_changes_allowed"] is False
    assert payload["decision"]["selector_training_allowed"] is False
    assert payload["decision"]["stage7_promotion_allowed"] is False
    assert payload["decision"]["stage8_training_allowed"] is False
    assert all(row["would_execute"] is False for row in payload["commands"])


def test_failure_contrast_approval_request_is_not_an_approval_receipt():
    payload = _read_report(
        "reports/strategy_arbitration/"
        "krk_protected_plan_window_failure_contrast_approval_request_v0.json"
    )

    assert (
        payload["schema_version"]
        == "krk_protected_plan_window_failure_contrast_approval_request.v0"
    )
    assert payload["causal_status"] == "non_causal_approval_request_packet"
    assert payload["approval_receipt_path"] == (
        "reports/strategy_arbitration/"
        "krk_protected_plan_window_failure_contrast_collection_approval_v0.json"
    )
    assert payload["approval_receipt_created"] is False
    assert payload["approval_receipt_present"] is False
    assert payload["approval_receipt_valid"] is False
    assert payload["approval_receipt_blockers"] == ["approval_receipt_missing"]
    assert payload["summary"]["job_count"] == 6
    assert payload["summary"]["runner_execution_requested"] is False
    assert payload["summary"]["runner_processed_job_count"] == 0
    assert payload["summary"]["runner_executed_job_count"] == 0
    assert payload["summary"]["approval_receipt_required"] is True
    assert (
        payload["summary"]["protected_stack_status"]
        == "retry1_protected_stage5_6_stack_adopted_manifest_only"
    )
    assert payload["summary"]["protected_stack_ready"] is True
    assert payload["summary"]["protected_stack_rollback_paths_preserved"] is True
    assert payload["summary"]["protected_stack_filesystem_snapshots_replaced"] is False
    assert payload["protected_stack_safety"] == {
        "status": "retry1_protected_stage5_6_stack_adopted_manifest_only",
        "ready": True,
        "rollback_paths_preserved": True,
        "active_paths_safe": True,
        "active_paths_exist": True,
        "rollback_paths_safe": True,
        "rollback_paths_exist": True,
        "rollback_common_paths_distinct": True,
        "filesystem_snapshots_replaced": False,
        "hard_blockers": [],
    }
    assert len(payload["summary"]["manifest_fingerprint"]) == 64
    assert len(payload["summary"]["readiness_fingerprint"]) == 64
    required = payload["required_receipt_if_user_approves"]
    assert required["approval_id"] == "approve_protected_plan_window_failure_contrast_collection"
    assert required["receipt_path"] == payload["approval_receipt_path"]
    assert required["approval_scope"]["job_count"] == 6
    assert (
        required["approval_scope"]["manifest_fingerprint"]
        == payload["summary"]["manifest_fingerprint"]
    )
    assert (
        required["approval_scope"]["readiness_fingerprint"]
        == payload["summary"]["readiness_fingerprint"]
    )
    assert required["decision"]["runtime_changes_allowed"] is False
    assert required["decision"]["label_run_allowed"] is False
    assert required["decision"]["selector_training_allowed"] is False
    assert required["decision"]["stage7_promotion_allowed"] is False
    assert required["decision"]["stage8_training_allowed"] is False
    assert payload["decision"]["collection_run_allowed"] is False
    assert payload["decision"]["label_run_allowed"] is False
    assert payload["decision"]["runtime_changes_allowed"] is False
    assert payload["decision"]["selector_training_allowed"] is False
    assert payload["decision"]["stage7_promotion_allowed"] is False
    assert payload["decision"]["stage8_training_allowed"] is False


def test_failure_contrast_approval_request_fixture_tracks_current_scope():
    payload = _approval_request.build_payload(
        manifest={
            "decision": {"status": "protected_plan_window_failure_contrast_manifest_ready_for_review"},
            "summary": {"job_count": 2},
            "jobs": [{"job_id": "a"}, {"job_id": "b"}],
        },
        readiness={
            "decision": {
                "status": (
                    "protected_plan_window_failure_contrast_execution_ready_pending_explicit_approval"
                )
            },
            "summary": {
                "manifest_fingerprint": "m" * 64,
                "readiness_fingerprint": "r" * 64,
            },
        },
        runner={
            "approval_receipt_path": (
                "reports/strategy_arbitration/"
                "krk_protected_plan_window_failure_contrast_collection_approval_v0.json"
            ),
            "execution_requested": False,
            "decision": {"status": "protected_plan_window_failure_contrast_runner_dry_run_ready"},
            "summary": {
                "approval_receipt_present": False,
                "approval_receipt_valid": False,
                "approval_receipt_blockers": ["approval_receipt_missing"],
                "processed_job_count": 0,
                "executed_job_count": 0,
            },
        },
        full_suite_readiness={
            "protected_stack": {
                "status": "fixture_stack_ready",
                "ready": True,
                "rollback_paths_preserved": True,
                "active_stack_path_status": {
                    "all_paths_safe": True,
                    "all_paths_exist": True,
                },
                "rollback_stack_path_status": {
                    "all_paths_safe": True,
                    "all_paths_exist": True,
                },
                "rollback_common_paths_distinct": True,
                "filesystem_snapshots_replaced": False,
            },
            "hard_blockers": [],
        },
    )

    assert payload["approval_receipt_created"] is False
    assert payload["protected_stack_safety"]["status"] == "fixture_stack_ready"
    assert payload["protected_stack_safety"]["rollback_paths_preserved"] is True
    assert payload["required_receipt_if_user_approves"]["approval_scope"] == {
        "manifest_fingerprint": "m" * 64,
        "readiness_fingerprint": "r" * 64,
        "job_count": 2,
        "manifest_status": "protected_plan_window_failure_contrast_manifest_ready_for_review",
        "readiness_status": (
            "protected_plan_window_failure_contrast_execution_ready_pending_explicit_approval"
        ),
    }
    assert payload["decision"]["collection_run_allowed"] is False


def test_failure_contrast_runner_fixture_blocks_without_review(monkeypatch):
    monkeypatch.setattr(
        _runner,
        "_run_execution_readiness",
        lambda _manifest: {
            "decision": {"status": "protected_plan_window_failure_contrast_execution_readiness_blocked"},
            "summary": {"all_jobs_pass_readiness": False, "jobs_passing_readiness": 0},
        },
    )
    monkeypatch.setattr(
        _runner,
        "_run_output_validation",
        lambda: {
            "decision": {"status": "protected_plan_window_failure_contrast_outputs_validation_pending"},
            "summary": {"output_exists_count": 0, "output_valid_count": 0},
            "output_checks": [],
        },
    )
    monkeypatch.setattr(
        _runner,
        "_load",
        lambda _path: {
            "decision": {"status": "protected_plan_window_failure_contrast_manifest_blocked"},
            "jobs": [],
        },
    )

    payload = _runner.build_payload(execute=False)

    assert payload["decision"]["status"] == "protected_plan_window_failure_contrast_runner_blocked"
    assert payload["decision"]["collection_run_allowed"] is False
    assert payload["decision"]["label_run_allowed"] is False
    assert "manifest_not_ready_for_review" in payload["execution_blockers"]


def test_failure_contrast_runner_execute_branch_never_authorizes_label_run(monkeypatch):
    monkeypatch.setattr(
        _runner,
        "_run_execution_readiness",
        lambda _manifest: {
            "decision": {
                "status": (
                    "protected_plan_window_failure_contrast_execution_ready_pending_explicit_approval"
                )
            },
            "summary": _ready_execution_summary(),
        },
    )
    monkeypatch.setattr(_runner, "_load_optional", lambda _path: _approval_receipt())
    monkeypatch.setattr(
        _runner,
        "_run_output_validation",
        lambda: {
            "decision": {
                "status": "protected_plan_window_failure_contrast_outputs_validation_pending"
            },
            "summary": {"output_exists_count": 0, "output_valid_count": 0},
            "output_checks": [],
        },
    )
    monkeypatch.setattr(
        _runner,
        "_load",
        lambda _path: {
            "decision": {
                "status": "protected_plan_window_failure_contrast_manifest_ready_for_review",
                "runtime_changes_allowed": False,
                "stage7_promotion_allowed": False,
                "stage8_training_allowed": False,
            },
            "jobs": [
                {
                    "job_id": "safe",
                    "expected_output_json": (
                        "reports/strategy_arbitration/"
                        "protected_plan_window_failure_contrasts/safe.json"
                    ),
                    "execution_binding": {"topology_path": "pyproject.toml"},
                }
            ],
        },
    )
    monkeypatch.setattr(
        _runner,
        "_run_job",
        lambda _job, **_kwargs: {
            "job_id": "safe",
            "success": True,
            "skipped_existing_output": False,
            "expected_output_json": (
                "reports/strategy_arbitration/"
                "protected_plan_window_failure_contrasts/safe.json"
            ),
        },
    )

    payload = _runner.build_payload(execute=True, run_post_success_refresh=False)

    assert (
        payload["decision"]["status"]
        == "protected_plan_window_failure_contrast_runner_executed_success"
    )
    assert payload["decision"]["collection_run_allowed"] is True
    assert payload["decision"]["label_run_allowed"] is False
    assert payload["decision"]["runtime_changes_allowed"] is False
    assert payload["decision"]["selector_training_allowed"] is False
    assert payload["decision"]["stage7_promotion_allowed"] is False
    assert payload["decision"]["stage8_training_allowed"] is False
    assert payload["summary"]["processed_job_count"] == 1
    assert payload["summary"]["executed_job_count"] == 1
    assert payload["summary"]["stage7_training_row_count"] == 0
    assert payload["summary"]["runtime_authorization_row_count"] == 0


def test_failure_contrast_runner_blocks_nonpositive_timeout(monkeypatch):
    monkeypatch.setattr(
        _runner,
        "_run_execution_readiness",
        lambda _manifest: {
            "decision": {
                "status": (
                    "protected_plan_window_failure_contrast_execution_ready_pending_explicit_approval"
                )
            },
            "summary": _ready_execution_summary(),
        },
    )
    monkeypatch.setattr(
        _runner,
        "_run_output_validation",
        lambda: {
            "decision": {
                "status": "protected_plan_window_failure_contrast_outputs_validation_pending"
            },
            "summary": {"output_exists_count": 0, "output_valid_count": 0},
            "output_checks": [],
        },
    )
    monkeypatch.setattr(
        _runner,
        "_load",
        lambda _path: {
            "decision": {
                "status": "protected_plan_window_failure_contrast_manifest_ready_for_review",
                "runtime_changes_allowed": False,
                "stage7_promotion_allowed": False,
                "stage8_training_allowed": False,
            },
            "jobs": [
                {
                    "job_id": "safe",
                    "expected_output_json": (
                        "reports/strategy_arbitration/"
                        "protected_plan_window_failure_contrasts/safe.json"
                    ),
                    "execution_binding": {"topology_path": "pyproject.toml"},
                }
            ],
        },
    )

    payload = _runner.build_payload(
        execute=True,
        job_timeout_seconds=0,
        run_post_success_refresh=False,
    )

    assert payload["decision"]["status"] == "protected_plan_window_failure_contrast_runner_blocked"
    assert "job_timeout_seconds_must_be_positive" in payload["execution_blockers"]
    assert payload["summary"]["processed_job_count"] == 0
    assert payload["summary"]["executed_job_count"] == 0
    assert payload["decision"]["collection_run_allowed"] is False
    assert payload["decision"]["label_run_allowed"] is False


def test_failure_contrast_runner_blocks_nonpositive_max_jobs(monkeypatch):
    monkeypatch.setattr(
        _runner,
        "_run_execution_readiness",
        lambda _manifest: {
            "decision": {
                "status": (
                    "protected_plan_window_failure_contrast_execution_ready_pending_explicit_approval"
                )
            },
            "summary": _ready_execution_summary(),
        },
    )
    monkeypatch.setattr(
        _runner,
        "_run_output_validation",
        lambda: {
            "decision": {
                "status": "protected_plan_window_failure_contrast_outputs_validation_pending"
            },
            "summary": {"output_exists_count": 0, "output_valid_count": 0},
            "output_checks": [],
        },
    )
    monkeypatch.setattr(
        _runner,
        "_load",
        lambda _path: {
            "decision": {
                "status": "protected_plan_window_failure_contrast_manifest_ready_for_review",
                "runtime_changes_allowed": False,
                "stage7_promotion_allowed": False,
                "stage8_training_allowed": False,
            },
            "jobs": [
                {
                    "job_id": "safe",
                    "expected_output_json": (
                        "reports/strategy_arbitration/"
                        "protected_plan_window_failure_contrasts/safe.json"
                    ),
                    "execution_binding": {"topology_path": "pyproject.toml"},
                }
            ],
        },
    )

    payload = _runner.build_payload(
        execute=True,
        max_jobs=0,
        run_post_success_refresh=False,
    )

    assert payload["decision"]["status"] == "protected_plan_window_failure_contrast_runner_blocked"
    assert "max_jobs_must_be_positive_when_set" in payload["execution_blockers"]
    assert payload["summary"]["processed_job_count"] == 0
    assert payload["summary"]["executed_job_count"] == 0
    assert payload["decision"]["collection_run_allowed"] is False


def test_failure_contrast_runner_blocks_unsafe_output_path(monkeypatch):
    monkeypatch.setattr(
        _runner,
        "_run_execution_readiness",
        lambda _manifest: {
            "decision": {
                "status": (
                    "protected_plan_window_failure_contrast_execution_ready_pending_explicit_approval"
                )
            },
            "summary": _ready_execution_summary(),
        },
    )
    monkeypatch.setattr(
        _runner,
        "_run_output_validation",
        lambda: {
            "decision": {
                "status": "protected_plan_window_failure_contrast_outputs_validation_pending"
            },
            "summary": {"output_exists_count": 0, "output_valid_count": 0},
            "output_checks": [],
        },
    )
    monkeypatch.setattr(
        _runner,
        "_load",
        lambda _path: {
            "decision": {
                "status": "protected_plan_window_failure_contrast_manifest_ready_for_review",
                "runtime_changes_allowed": False,
                "stage7_promotion_allowed": False,
                "stage8_training_allowed": False,
            },
            "jobs": [
                {
                    "job_id": "unsafe",
                    "expected_output_json": "../unsafe.json",
                    "execution_binding": {"topology_path": "pyproject.toml"},
                }
            ],
        },
    )

    payload = _runner.build_payload(execute=True, run_post_success_refresh=False)

    assert payload["decision"]["status"] == "protected_plan_window_failure_contrast_runner_blocked"
    assert "unsafe_expected_output_json" in payload["execution_blockers"]
    assert payload["commands"][0]["output_exists"] is False
    assert payload["commands"][0]["would_execute"] is False
    assert payload["summary"]["processed_job_count"] == 0
    assert payload["decision"]["collection_run_allowed"] is False


def test_failure_contrast_runner_blocks_unsafe_topology_path(monkeypatch):
    monkeypatch.setattr(
        _runner,
        "_run_execution_readiness",
        lambda _manifest: {
            "decision": {
                "status": (
                    "protected_plan_window_failure_contrast_execution_ready_pending_explicit_approval"
                )
            },
            "summary": _ready_execution_summary(),
        },
    )
    monkeypatch.setattr(
        _runner,
        "_run_output_validation",
        lambda: {
            "decision": {
                "status": "protected_plan_window_failure_contrast_outputs_validation_pending"
            },
            "summary": {"output_exists_count": 0, "output_valid_count": 0},
            "output_checks": [],
        },
    )
    monkeypatch.setattr(
        _runner,
        "_load",
        lambda _path: {
            "decision": {
                "status": "protected_plan_window_failure_contrast_manifest_ready_for_review",
                "runtime_changes_allowed": False,
                "stage7_promotion_allowed": False,
                "stage8_training_allowed": False,
            },
            "jobs": [
                {
                    "job_id": "unsafe-topology",
                    "expected_output_json": (
                        "reports/strategy_arbitration/"
                        "protected_plan_window_failure_contrasts/safe.json"
                    ),
                    "execution_binding": {"topology_path": "/tmp/topology.json"},
                }
            ],
        },
    )

    payload = _runner.build_payload(execute=True, run_post_success_refresh=False)

    assert payload["decision"]["status"] == "protected_plan_window_failure_contrast_runner_blocked"
    assert "missing_or_invalid_topology_binding" in payload["execution_blockers"]
    assert payload["summary"]["processed_job_count"] == 0
    assert payload["decision"]["collection_run_allowed"] is False


def test_failure_contrast_runner_blocks_execute_without_approval_receipt(monkeypatch):
    monkeypatch.setattr(
        _runner,
        "_run_execution_readiness",
        lambda _manifest: {
            "decision": {
                "status": (
                    "protected_plan_window_failure_contrast_execution_ready_pending_explicit_approval"
                )
            },
            "summary": _ready_execution_summary(),
        },
    )
    monkeypatch.setattr(
        _runner,
        "_run_output_validation",
        lambda: {
            "decision": {
                "status": "protected_plan_window_failure_contrast_outputs_validation_pending"
            },
            "summary": {"output_exists_count": 0, "output_valid_count": 0},
            "output_checks": [],
        },
    )
    monkeypatch.setattr(
        _runner,
        "_load",
        lambda _path: {
            "decision": {
                "status": "protected_plan_window_failure_contrast_manifest_ready_for_review",
                "runtime_changes_allowed": False,
                "stage7_promotion_allowed": False,
                "stage8_training_allowed": False,
            },
            "jobs": [
                {
                    "job_id": "safe",
                    "expected_output_json": (
                        "reports/strategy_arbitration/"
                        "protected_plan_window_failure_contrasts/safe.json"
                    ),
                    "execution_binding": {"topology_path": "pyproject.toml"},
                }
            ],
        },
    )

    payload = _runner.build_payload(execute=True, run_post_success_refresh=False)

    assert payload["decision"]["status"] == "protected_plan_window_failure_contrast_runner_blocked"
    assert "approval_receipt_missing" in payload["execution_blockers"]
    assert payload["summary"]["approval_receipt_required_for_execution"] is True
    assert payload["summary"]["approval_receipt_present"] is False
    assert payload["summary"]["approval_receipt_valid"] is False
    assert payload["summary"]["processed_job_count"] == 0
    assert payload["decision"]["collection_run_allowed"] is False


def test_failure_contrast_runner_blocks_stale_approval_receipt(monkeypatch):
    monkeypatch.setattr(
        _runner,
        "_run_execution_readiness",
        lambda _manifest: {
            "decision": {
                "status": (
                    "protected_plan_window_failure_contrast_execution_ready_pending_explicit_approval"
                )
            },
            "summary": _ready_execution_summary(),
        },
    )
    stale_receipt = _approval_receipt()
    stale_receipt["approval_scope"] = dict(stale_receipt["approval_scope"])
    stale_receipt["approval_scope"]["readiness_fingerprint"] = "stale"
    monkeypatch.setattr(_runner, "_load_optional", lambda _path: stale_receipt)
    monkeypatch.setattr(
        _runner,
        "_run_output_validation",
        lambda: {
            "decision": {
                "status": "protected_plan_window_failure_contrast_outputs_validation_pending"
            },
            "summary": {"output_exists_count": 0, "output_valid_count": 0},
            "output_checks": [],
        },
    )
    monkeypatch.setattr(
        _runner,
        "_load",
        lambda _path: {
            "decision": {
                "status": "protected_plan_window_failure_contrast_manifest_ready_for_review",
                "runtime_changes_allowed": False,
                "stage7_promotion_allowed": False,
                "stage8_training_allowed": False,
            },
            "jobs": [
                {
                    "job_id": "safe",
                    "expected_output_json": (
                        "reports/strategy_arbitration/"
                        "protected_plan_window_failure_contrasts/safe.json"
                    ),
                    "execution_binding": {"topology_path": "pyproject.toml"},
                }
            ],
        },
    )

    payload = _runner.build_payload(execute=True, run_post_success_refresh=False)

    assert payload["decision"]["status"] == "protected_plan_window_failure_contrast_runner_blocked"
    assert "approval_receipt_readiness_fingerprint_mismatch" in payload["execution_blockers"]
    assert payload["summary"]["approval_receipt_present"] is True
    assert payload["summary"]["approval_receipt_valid"] is False
    assert payload["summary"]["processed_job_count"] == 0
    assert payload["decision"]["collection_run_allowed"] is False


def test_failure_contrast_runner_marks_job_timeout(monkeypatch):
    monkeypatch.setattr(
        _runner,
        "_run_execution_readiness",
        lambda _manifest: {
            "decision": {
                "status": (
                    "protected_plan_window_failure_contrast_execution_ready_pending_explicit_approval"
                )
            },
            "summary": _ready_execution_summary(),
        },
    )
    monkeypatch.setattr(_runner, "_load_optional", lambda _path: _approval_receipt())
    monkeypatch.setattr(
        _runner,
        "_run_output_validation",
        lambda: {
            "decision": {
                "status": "protected_plan_window_failure_contrast_outputs_validation_pending"
            },
            "summary": {"output_exists_count": 0, "output_valid_count": 0},
            "output_checks": [],
        },
    )
    monkeypatch.setattr(
        _runner,
        "_load",
        lambda _path: {
            "decision": {
                "status": "protected_plan_window_failure_contrast_manifest_ready_for_review",
                "runtime_changes_allowed": False,
                "stage7_promotion_allowed": False,
                "stage8_training_allowed": False,
            },
            "jobs": [
                {
                    "job_id": "timeout",
                    "expected_output_json": (
                        "reports/strategy_arbitration/"
                        "protected_plan_window_failure_contrasts/timeout.json"
                    ),
                    "execution_binding": {"topology_path": "pyproject.toml"},
                }
            ],
        },
    )

    def raise_timeout(*_args, **_kwargs):
        raise _runner._JobTimeoutError("fixture timeout")

    monkeypatch.setattr(_runner, "_run_job", raise_timeout)

    payload = _runner.build_payload(
        execute=True,
        job_timeout_seconds=1,
        run_post_success_refresh=False,
    )

    assert (
        payload["decision"]["status"]
        == "protected_plan_window_failure_contrast_runner_executed_with_failures"
    )
    assert payload["summary"]["processed_job_count"] == 1
    assert payload["summary"]["executed_job_count"] == 1
    assert payload["summary"]["failed_job_count"] == 1
    assert payload["summary"]["timed_out_job_count"] == 1
    assert payload["executed_jobs"][0]["timed_out"] is True
    assert payload["executed_jobs"][0]["timeout_seconds"] == 1
    assert payload["executed_jobs"][0]["success"] is False
    assert payload["post_run_refresh"] is None
    assert payload["decision"]["label_run_allowed"] is False
    assert payload["decision"]["runtime_changes_allowed"] is False


def test_failure_contrast_runner_records_unexpected_job_failure(monkeypatch):
    monkeypatch.setattr(
        _runner,
        "_run_execution_readiness",
        lambda _manifest: {
            "decision": {
                "status": (
                    "protected_plan_window_failure_contrast_execution_ready_pending_explicit_approval"
                )
            },
            "summary": _ready_execution_summary(),
        },
    )
    monkeypatch.setattr(_runner, "_load_optional", lambda _path: _approval_receipt())
    monkeypatch.setattr(
        _runner,
        "_run_output_validation",
        lambda: {
            "decision": {
                "status": "protected_plan_window_failure_contrast_outputs_validation_pending"
            },
            "summary": {"output_exists_count": 0, "output_valid_count": 0},
            "output_checks": [],
        },
    )
    monkeypatch.setattr(
        _runner,
        "_load",
        lambda _path: {
            "decision": {
                "status": "protected_plan_window_failure_contrast_manifest_ready_for_review",
                "runtime_changes_allowed": False,
                "stage7_promotion_allowed": False,
                "stage8_training_allowed": False,
            },
            "jobs": [
                {
                    "job_id": "boom",
                    "expected_output_json": (
                        "reports/strategy_arbitration/"
                        "protected_plan_window_failure_contrasts/boom.json"
                    ),
                    "execution_binding": {"topology_path": "pyproject.toml"},
                }
            ],
        },
    )

    def raise_error(*_args, **_kwargs):
        raise ValueError("fixture failure")

    monkeypatch.setattr(_runner, "_run_job", raise_error)

    payload = _runner.build_payload(
        execute=True,
        job_timeout_seconds=1,
        run_post_success_refresh=False,
    )

    assert (
        payload["decision"]["status"]
        == "protected_plan_window_failure_contrast_runner_executed_with_failures"
    )
    assert payload["summary"]["failed_job_count"] == 1
    assert payload["summary"]["timed_out_job_count"] == 0
    assert payload["executed_jobs"][0]["success"] is False
    assert payload["executed_jobs"][0]["error"] == "ValueError"
    assert payload["post_run_refresh"] is None
    assert payload["decision"]["label_run_allowed"] is False
    assert payload["decision"]["stage8_training_allowed"] is False


def test_failure_contrast_manifest_fixture_blocks_missing_stage():
    payload = _manifest.build_payload(
        plan={"summary": {"minimum_new_unique_failures_needed": 4}},
        protected_windows={
            "frames": [
                {
                    "frame_id": "planwin.stage5.a",
                    "source_stage": "stage5",
                    "source_family": "fence_handoff_plan_window",
                    "outcome_bucket": "success",
                    "fen": "8/8/8/8/8/8/8/8 w - - 0 1",
                    "move_uci": "a1a2",
                    "h40_outcome_label": "conversion_positive",
                    "result": "mate",
                }
            ]
        },
    )

    assert payload["decision"]["status"] == "protected_plan_window_failure_contrast_manifest_blocked"
    assert payload["summary"]["all_bindings_valid"] is False
    assert payload["decision"]["collection_run_allowed"] is False


def test_failure_contrast_manifest_review_fixture_rejects_collection_flags():
    payload = _review.build_payload(
        manifest={
            "summary": {"all_bindings_valid": True},
            "collection_constraints": {
                "requires_explicit_approval_before_collection": True,
                "observation_only": True,
                "no_runtime_default_change": True,
                "no_runtime_dtm_or_tablebase": True,
                "no_gameplay_topology_mutation": True,
                "no_stage7_promotion": True,
                "no_stage8_training": True,
            },
            "jobs": [
                {
                    "job_id": "bad",
                    "source_stage": "stage4",
                    "source_family": "wrong_tempo_plan_window",
                    "horizon": 40,
                    "collection_mode": "observation_only_trace_collection_pending_explicit_approval",
                    "labels_generated": True,
                    "usable_for_selector_training": False,
                    "usable_for_runtime_authorization": False,
                    "stage7_heldout_challenge": False,
                }
            ],
        }
    )

    assert payload["decision"]["status"] == "protected_plan_window_failure_contrast_manifest_review_failed"
    assert payload["review_summary"]["violation_count"] > 0
    assert payload["decision"]["collection_run_allowed"] is False
    assert payload["decision"]["runtime_changes_allowed"] is False


def test_failure_contrast_manifest_review_fixture_rejects_unsafe_bindings():
    payload = _review.build_payload(
        manifest={
            "summary": {"all_bindings_valid": True},
            "collection_constraints": {
                "requires_explicit_approval_before_collection": True,
                "observation_only": True,
                "no_runtime_default_change": True,
                "no_runtime_dtm_or_tablebase": True,
                "no_gameplay_topology_mutation": True,
                "no_stage7_promotion": True,
                "no_stage8_training": True,
            },
            "jobs": [
                {
                    "job_id": "unsafe",
                    "source_stage": "stage5",
                    "source_family": "fence_handoff_plan_window",
                    "horizon": 40,
                    "collection_mode": "observation_only_trace_collection_pending_explicit_approval",
                    "expected_output_json": "../unsafe.json",
                    "execution_binding": {"topology_path": "/tmp/topology.json"},
                    "labels_generated": False,
                    "usable_for_selector_training": False,
                    "usable_for_runtime_authorization": False,
                    "stage7_heldout_challenge": False,
                }
            ],
        }
    )

    violations = {row["violation"] for row in payload["review_summary"]["violations"]}
    assert payload["decision"]["status"] == "protected_plan_window_failure_contrast_manifest_review_failed"
    assert "unsafe_expected_output_json" in violations
    assert "missing_or_invalid_topology_binding" in violations
    assert payload["decision"]["collection_run_allowed"] is False


def test_failure_contrast_execution_readiness_fixture_rejects_unsafe_output():
    payload = _readiness.build_payload(
        manifest={
            "summary": {"all_bindings_valid": True},
            "decision": {
                "status": "protected_plan_window_failure_contrast_manifest_ready_for_review"
            },
            "jobs": [
                {
                    "job_id": "bad",
                    "source_stage": "stage4",
                    "source_family": "wrong_tempo_plan_window",
                    "horizon": 40,
                    "collection_mode": "observation_only_trace_collection_pending_explicit_approval",
                    "expected_output_json": "../bad.json",
                    "labels_generated": False,
                    "usable_for_selector_training": False,
                    "usable_for_runtime_authorization": False,
                    "stage7_heldout_challenge": False,
                }
            ],
        },
        review={
            "decision": {
                "status": "protected_plan_window_failure_contrast_manifest_review_passed_pending_explicit_approval"
            }
        },
    )

    assert (
        payload["decision"]["status"]
        == "protected_plan_window_failure_contrast_execution_readiness_blocked"
    )
    assert payload["decision"]["collection_run_allowed"] is False
    assert payload["decision"]["runtime_changes_allowed"] is False


def test_failure_contrast_execution_readiness_fixture_rejects_unsafe_topology():
    payload = _readiness.build_payload(
        manifest={
            "summary": {"all_bindings_valid": True},
            "decision": {
                "status": "protected_plan_window_failure_contrast_manifest_ready_for_review"
            },
            "jobs": [
                {
                    "job_id": "bad-topology",
                    "source_stage": "stage5",
                    "source_family": "fence_handoff_plan_window",
                    "horizon": 40,
                    "collection_mode": "observation_only_trace_collection_pending_explicit_approval",
                    "expected_output_json": (
                        "reports/strategy_arbitration/"
                        "protected_plan_window_failure_contrasts/bad-topology.json"
                    ),
                    "execution_binding": {"topology_path": "/tmp/topology.json"},
                    "labels_generated": False,
                    "usable_for_selector_training": False,
                    "usable_for_runtime_authorization": False,
                    "stage7_heldout_challenge": False,
                }
            ],
        },
        review={
            "decision": {
                "status": "protected_plan_window_failure_contrast_manifest_review_passed_pending_explicit_approval"
            }
        },
    )

    assert (
        payload["decision"]["status"]
        == "protected_plan_window_failure_contrast_execution_readiness_blocked"
    )
    assert "missing_or_invalid_topology_binding" in payload["job_checks"][0]["readiness_blockers"]
    assert payload["decision"]["collection_run_allowed"] is False


def test_failure_contrast_execution_readiness_rejects_stale_manifest_review():
    manifest = _read_report(
        "reports/strategy_arbitration/krk_protected_plan_window_failure_contrast_manifest_v0.json"
    )

    payload = _readiness.build_payload(
        manifest=manifest,
        review={
            "decision": {
                "status": "protected_plan_window_failure_contrast_manifest_review_passed_pending_explicit_approval"
            },
            "review_summary": {"manifest_fingerprint": "stale"},
        },
    )

    assert (
        payload["decision"]["status"]
        == "protected_plan_window_failure_contrast_execution_readiness_blocked"
    )
    assert "manifest_review_fingerprint_mismatch" in payload["summary"][
        "execution_readiness_blockers"
    ]
    assert payload["summary"]["manifest_fingerprints_match"] is False


def test_failure_contrast_execution_readiness_blocks_unsafe_protected_stack():
    manifest = _read_report(
        "reports/strategy_arbitration/krk_protected_plan_window_failure_contrast_manifest_v0.json"
    )
    review = _read_report(
        "reports/strategy_arbitration/"
        "krk_protected_plan_window_failure_contrast_manifest_review_v0.json"
    )

    payload = _readiness.build_payload(
        manifest=manifest,
        review=review,
        full_suite_readiness={
            "protected_stack": {
                "status": "fixture_stack_not_ready",
                "ready": False,
                "rollback_paths_preserved": False,
                "active_stack_path_status": {
                    "all_paths_safe": False,
                    "all_paths_exist": True,
                },
                "rollback_stack_path_status": {
                    "all_paths_safe": True,
                    "all_paths_exist": False,
                },
                "rollback_common_paths_distinct": False,
                "filesystem_snapshots_replaced": True,
            },
            "hard_blockers": ["protected_retry1_stage5_6_stack_not_validated"],
        },
    )

    assert (
        payload["decision"]["status"]
        == "protected_plan_window_failure_contrast_execution_readiness_blocked"
    )
    assert payload["summary"]["protected_stack_status"] == "fixture_stack_not_ready"
    assert payload["summary"]["protected_stack_ready"] is False
    blockers = payload["summary"]["execution_readiness_blockers"]
    assert "protected_stack_not_ready" in blockers
    assert "protected_stack_rollback_paths_not_preserved" in blockers
    assert "protected_stack_active_paths_unsafe" in blockers
    assert "protected_stack_rollback_paths_missing" in blockers
    assert "protected_stack_rollback_common_paths_not_distinct" in blockers
    assert "protected_stack_filesystem_snapshot_replacement_detected" in blockers
    assert "protected_stack_hard_blockers_present" in blockers
    assert payload["decision"]["collection_run_allowed"] is False


def test_failure_contrast_output_validation_fixture_accepts_safe_output(tmp_path, monkeypatch):
    monkeypatch.setattr(_output_validation, "ROOT", tmp_path)
    output = (
        tmp_path
        / "reports/strategy_arbitration/protected_plan_window_failure_contrasts/good.json"
    )
    output.parent.mkdir(parents=True)
    output.write_text(
        json.dumps(
            {
                "schema_version": "krk_protected_plan_window_failure_contrast_output.v0",
                "causal_status": "non_causal_observation_only_collection",
                "job_id": "good",
                "source_stage": "stage5",
                "source_family": "fence_handoff_plan_window",
                "seed_frame_id": "seed.good",
                "horizon": 40,
                "result": "max_plies",
                "h40_outcome_label": "conversion_failure",
                "observation_only": True,
                "runtime_behavior_changed": False,
                "runtime_defaults_changed": False,
                "runtime_selector_implemented": False,
                "runtime_dtm_or_tablebase_lookup": False,
                "gameplay_topology_mutation": False,
                "stage7_promotion_allowed": False,
                "stage8_training_allowed": False,
                "usable_for_selector_training": False,
                "usable_for_runtime_authorization": False,
                "stage7_heldout_challenge": False,
            }
        ),
        encoding="utf-8",
    )

    payload = _output_validation.build_payload(
        manifest={
            "jobs": [
                {
                    "job_id": "good",
                    "source_stage": "stage5",
                    "source_family": "fence_handoff_plan_window",
                    "seed_frame_id": "seed.good",
                    "anchor_move_uci": "a1a2",
                    "expected_output_json": (
                        "reports/strategy_arbitration/"
                        "protected_plan_window_failure_contrasts/good.json"
                    ),
                }
            ]
        }
    )

    assert (
        payload["decision"]["status"]
        == "protected_plan_window_failure_contrast_outputs_valid_ready_for_integration"
    )
    assert payload["summary"]["unique_failure_candidate_count"] == 1
    assert payload["decision"]["label_run_allowed"] is False
    assert payload["decision"]["runtime_changes_allowed"] is False


def test_failure_contrast_output_validation_counts_missing_outputs():
    payload = _output_validation.build_payload(
        manifest={
            "jobs": [
                {
                    "job_id": "missing",
                    "source_stage": "stage5",
                    "source_family": "fence_handoff_plan_window",
                    "seed_frame_id": "seed.missing",
                    "anchor_move_uci": "a1a2",
                    "expected_output_json": (
                        "reports/strategy_arbitration/"
                        "protected_plan_window_failure_contrasts/missing.json"
                    ),
                }
            ]
        }
    )

    assert (
        payload["decision"]["status"]
        == "protected_plan_window_failure_contrast_outputs_validation_pending"
    )
    assert payload["summary"]["output_exists_count"] == 0
    assert payload["summary"]["issue_counts"] == {"output_missing": 1}
    assert payload["output_checks"][0]["issues"] == ["output_missing"]
    assert payload["decision"]["collection_run_allowed"] is False
    assert payload["decision"]["runtime_changes_allowed"] is False


def test_failure_contrast_output_validation_rejects_unsafe_output_path():
    payload = _output_validation.build_payload(
        manifest={
            "jobs": [
                {
                    "job_id": "unsafe",
                    "source_stage": "stage5",
                    "source_family": "fence_handoff_plan_window",
                    "seed_frame_id": "seed.unsafe",
                    "anchor_move_uci": "a1a2",
                    "expected_output_json": "../unsafe.json",
                }
            ]
        }
    )

    assert (
        payload["decision"]["status"]
        == "protected_plan_window_failure_contrast_outputs_validation_pending"
    )
    assert payload["summary"]["output_exists_count"] == 0
    assert payload["summary"]["parse_error_count"] == 0
    assert payload["summary"]["issue_counts"] == {"unsafe_expected_output_json": 1}
    assert payload["output_checks"][0]["output_exists"] is False
    assert payload["output_checks"][0]["issues"] == ["unsafe_expected_output_json"]
    assert payload["decision"]["collection_run_allowed"] is False
    assert payload["decision"]["label_run_allowed"] is False


def test_failure_contrast_output_validation_fixture_rejects_runtime_tainted_output(
    tmp_path, monkeypatch
):
    monkeypatch.setattr(_output_validation, "ROOT", tmp_path)
    output = (
        tmp_path
        / "reports/strategy_arbitration/protected_plan_window_failure_contrasts/bad.json"
    )
    output.parent.mkdir(parents=True)
    output.write_text(
        json.dumps(
            {
                "schema_version": "krk_protected_plan_window_failure_contrast_output.v0",
                "causal_status": "non_causal_observation_only_collection",
                "job_id": "bad",
                "source_stage": "stage5",
                "source_family": "fence_handoff_plan_window",
                "seed_frame_id": "seed.bad",
                "horizon": 40,
                "result": "max_plies",
                "h40_outcome_label": "conversion_failure",
                "observation_only": True,
                "runtime_behavior_changed": True,
                "runtime_defaults_changed": False,
                "runtime_selector_implemented": False,
                "runtime_dtm_or_tablebase_lookup": False,
                "gameplay_topology_mutation": False,
                "stage7_promotion_allowed": False,
                "stage8_training_allowed": False,
                "usable_for_selector_training": False,
                "usable_for_runtime_authorization": False,
                "stage7_heldout_challenge": False,
            }
        ),
        encoding="utf-8",
    )

    payload = _output_validation.build_payload(
        manifest={
            "jobs": [
                {
                    "job_id": "bad",
                    "source_stage": "stage5",
                    "source_family": "fence_handoff_plan_window",
                    "seed_frame_id": "seed.bad",
                    "anchor_move_uci": "a1a2",
                    "expected_output_json": (
                        "reports/strategy_arbitration/"
                        "protected_plan_window_failure_contrasts/bad.json"
                    ),
                }
            ]
        }
    )

    assert (
        payload["decision"]["status"]
        == "protected_plan_window_failure_contrast_outputs_invalid_block_integration"
    )
    assert payload["summary"]["output_valid_count"] == 0
    assert payload["decision"]["label_run_allowed"] is False
    assert payload["decision"]["runtime_changes_allowed"] is False
