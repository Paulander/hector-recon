#!/usr/bin/env python3
"""Approval-gated protected plan-window failure-contrast collection runner.

Default behavior is dry-run only. Executing observation collection requires the
explicit ``--execute-reviewed-collection`` flag. The runner writes non-causal
h40 observation outputs from the reviewed manifest and never changes runtime
defaults, trains selectors, promotes Stage 7, or trains Stage 8.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import random
import signal
import sys
import time
from pathlib import Path
from typing import Any

import chess


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT / "scripts") not in sys.path:
    sys.path.insert(0, str(ROOT / "scripts"))

import test_krk_landmark_progress as diag  # noqa: E402
from recon_lite.engine import ReConEngine  # noqa: E402


MANIFEST = (
    ROOT
    / "reports/strategy_arbitration/krk_protected_plan_window_failure_contrast_manifest_v0.json"
)
READINESS = (
    ROOT
    / "reports/strategy_arbitration/"
    "krk_protected_plan_window_failure_contrast_execution_readiness_v0.json"
)
DEFAULT_APPROVAL_RECEIPT = (
    ROOT
    / "reports/strategy_arbitration/"
    "krk_protected_plan_window_failure_contrast_collection_approval_v0.json"
)
OUTPUT_VALIDATION_SCRIPT = (
    ROOT / "scripts/validate_krk_protected_plan_window_failure_contrast_outputs_v0.py"
)
EXECUTION_READINESS_SCRIPT = (
    ROOT
    / "scripts/validate_krk_protected_plan_window_failure_contrast_execution_readiness_v0.py"
)
FULL_GATE_ADVANCEMENT_SCRIPT = ROOT / "scripts/advance_krk_suite_from_current_gates_v0.py"
OUTPUT_JSON = (
    ROOT
    / "reports/strategy_arbitration/krk_protected_plan_window_failure_contrast_runner_v0.json"
)
OUTPUT_MD = (
    ROOT
    / "reports/strategy_arbitration/krk_protected_plan_window_failure_contrast_runner_v0.md"
)

SCHEMA_VERSION = "krk_protected_plan_window_failure_contrast_runner.v0"
OUTPUT_SCHEMA_VERSION = "krk_protected_plan_window_failure_contrast_output.v0"
APPROVAL_SCHEMA_VERSION = (
    "krk_protected_plan_window_failure_contrast_collection_approval.v0"
)
APPROVAL_STATUS = "approved_for_single_bounded_observation_collection"
DEFAULT_JOB_TIMEOUT_SECONDS = 900
OUTPUT_ROOT = Path("reports/strategy_arbitration/protected_plan_window_failure_contrasts")
APPROVAL_RECEIPT_ROOT = Path("reports/strategy_arbitration")

COMMON_FALSE_FLAGS = {
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


class _JobTimeoutError(TimeoutError):
    """Raised when one bounded collection job exceeds its approved wall clock."""


def _raise_job_timeout(_signum: int, _frame: Any) -> None:
    raise _JobTimeoutError("protected failure-contrast job timed out")


def _load(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise TypeError(f"{path} must contain a JSON object")
    return data


def _load_optional(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    return _load(path)


def _safe_relative(path_value: Any, *, required_root: Path | None = None) -> bool:
    if not isinstance(path_value, str) or not path_value:
        return False
    path = Path(path_value)
    if path.is_absolute() or ".." in path.parts:
        return False
    if required_root is None:
        return True
    return path.parts[: len(required_root.parts)] == required_root.parts


def _approval_receipt_path(path_value: str | None) -> Path:
    path_text = path_value or str(DEFAULT_APPROVAL_RECEIPT.relative_to(ROOT))
    if not _safe_relative(path_text, required_root=APPROVAL_RECEIPT_ROOT):
        raise ValueError("unsafe_approval_receipt_path")
    return ROOT / path_text


def _safe_output_path(job: dict[str, Any]) -> Path:
    output = job.get("expected_output_json")
    if not _safe_relative(output, required_root=OUTPUT_ROOT):
        raise ValueError("unsafe_expected_output_json")
    return ROOT / str(output)


def _safe_output_exists(job: dict[str, Any]) -> bool:
    try:
        return _safe_output_path(job).exists()
    except ValueError:
        return False


def _load_module(path: Path):
    spec = importlib.util.spec_from_file_location(path.stem, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load script module: {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _stable_seed(*parts: Any) -> int:
    text = "|".join(str(part) for part in parts)
    return int(hashlib.sha1(text.encode("utf-8")).hexdigest()[:8], 16)


def _settings(binding: dict[str, Any]) -> dict[str, Any]:
    return binding.get("profile_settings") or {}


def _load_graph_engine(topology_path: str, cache: dict[str, tuple[Any, ReConEngine]]):
    if topology_path not in cache:
        graph = diag.build_graph_from_topology(ROOT / topology_path)
        cache[topology_path] = (graph, ReConEngine(graph))
    return cache[topology_path]


def _selected_provider(move_details: dict[str, Any]) -> str | None:
    suggestion = diag._selected_engine_suggestion(move_details)
    if not suggestion:
        return None
    return diag._skill_id_for_suggestion(suggestion)


def _choose_initial(graph: Any, engine: ReConEngine, board: chess.Board, job: dict[str, Any]) -> dict[str, Any]:
    binding = job.get("execution_binding") or {}
    settings = _settings(binding)
    return diag.choose_move_details(
        graph,
        engine,
        board,
        max_ticks=int(binding.get("max_ticks") or 200),
        stage_filter=None,
        suggestion_limit=int(binding.get("suggestion_limit") or 10),
        successor_affordance_layer_enabled=bool(settings.get("successor_affordance_layer_enabled")),
        successor_role_license_enabled=bool(settings.get("successor_role_license_enabled")),
        successor_role_scoped_move_shape_enabled=bool(
            settings.get("successor_role_scoped_move_shape_enabled")
        ),
        successor_role_scoped_move_shape_bonus=float(
            settings.get("successor_role_scoped_move_shape_bonus") or 0.0
        ),
        stagnation_breaker_enabled=bool(settings.get("stagnation_breaker_enabled")),
        stagnation_breaker_bonus=float(settings.get("stagnation_breaker_bonus") or 0.0),
        post_break_continuation_enabled=bool(settings.get("post_break_continuation_enabled")),
        post_break_continuation_bonus=float(settings.get("post_break_continuation_bonus") or 0.0),
        successor_stage0_drift_penalty=float(settings.get("successor_stage0_drift_penalty") or 0.0),
        early_stop_stable_suggestions=int(binding.get("early_stop_stable_suggestions") or 0),
        active_landmark_label=str(job.get("active_landmark_label") or ""),
        enable_diagnostic_caches=bool(binding.get("enable_diagnostic_caches")),
    )


def _run_playout(
    graph: Any,
    engine: ReConEngine,
    board: chess.Board,
    job: dict[str, Any],
    *,
    trace: bool,
) -> dict[str, Any]:
    binding = job.get("execution_binding") or {}
    settings = _settings(binding)
    horizon = int(job.get("horizon") or 40)
    return diag.play_to_mate(
        graph,
        engine,
        board,
        random.Random(_stable_seed("protected_failure_contrast", job.get("job_id"))),
        str(job.get("active_landmark_label") or "protected_plan_window"),
        None,
        horizon,
        str(binding.get("black_policy") or "adversarial"),
        trace=trace,
        trace_max_plies=horizon if trace else None,
        max_ticks=int(binding.get("max_ticks") or 200),
        suggestion_limit=int(binding.get("suggestion_limit") or 10),
        successor_affordance_layer_enabled=bool(settings.get("successor_affordance_layer_enabled")),
        successor_role_license_enabled=bool(settings.get("successor_role_license_enabled")),
        successor_role_scoped_move_shape_enabled=bool(
            settings.get("successor_role_scoped_move_shape_enabled")
        ),
        successor_role_scoped_move_shape_bonus=float(
            settings.get("successor_role_scoped_move_shape_bonus") or 0.0
        ),
        stagnation_breaker_enabled=bool(settings.get("stagnation_breaker_enabled")),
        stagnation_breaker_bonus=float(settings.get("stagnation_breaker_bonus") or 0.0),
        post_break_continuation_enabled=bool(settings.get("post_break_continuation_enabled")),
        post_break_continuation_bonus=float(settings.get("post_break_continuation_bonus") or 0.0),
        successor_stage0_drift_penalty=float(settings.get("successor_stage0_drift_penalty") or 0.0),
        early_stop_stable_suggestions=int(binding.get("early_stop_stable_suggestions") or 0),
        enable_diagnostic_caches=bool(binding.get("enable_diagnostic_caches")),
    )


def _label(result: Any) -> str:
    return "conversion_positive" if result == "mate" else "conversion_failure"


def _run_job(
    job: dict[str, Any],
    *,
    cache: dict[str, tuple[Any, ReConEngine]],
    overwrite_existing_outputs: bool,
) -> dict[str, Any]:
    output_path = _safe_output_path(job)
    if output_path.exists() and not overwrite_existing_outputs:
        return {
            "job_id": job.get("job_id"),
            "expected_output_json": job.get("expected_output_json"),
            "output_exists": True,
            "skipped_existing_output": True,
            "success": True,
            "duration_seconds": 0.0,
        }
    binding = job.get("execution_binding") or {}
    topology_path = str(binding.get("topology_path") or "")
    graph, engine = _load_graph_engine(topology_path, cache)
    board = chess.Board(str(job.get("seed_fen") or ""))
    start = time.perf_counter()
    initial = _choose_initial(graph, engine, board, job)
    selected_move = initial.get("move")
    selected_provider = _selected_provider(initial)
    result = _run_playout(graph, engine, board.copy(stack=False), job, trace=False)
    if result.get("result") != "mate":
        result = _run_playout(graph, engine, board.copy(stack=False), job, trace=True)
    duration = round(time.perf_counter() - start, 6)
    output = {
        "schema_version": OUTPUT_SCHEMA_VERSION,
        "causal_status": "non_causal_observation_only_collection",
        "job_id": job.get("job_id"),
        "source_stage": job.get("source_stage"),
        "source_family": job.get("source_family"),
        "seed_frame_id": job.get("seed_frame_id"),
        "seed_fen": job.get("seed_fen"),
        "anchor_move_uci": job.get("anchor_move_uci"),
        "active_landmark_label": job.get("active_landmark_label"),
        "horizon": int(job.get("horizon") or 40),
        "selected_move": selected_move,
        "selected_provider": selected_provider,
        "result": result.get("result"),
        "plies": result.get("plies"),
        "h40_outcome_label": _label(result.get("result")),
        "final_fen": result.get("final_fen"),
        "trace_included": "trace" in result,
        "stagnation_summary": result.get("stagnation_summary"),
        "observation_only": True,
        **COMMON_FALSE_FLAGS,
        "usable_for_selector_training": False,
        "usable_for_runtime_authorization": False,
        "stage7_heldout_challenge": False,
        "stage7_training_row_count": 0,
        "runtime_authorization_row_count": 0,
    }
    if "trace" in result:
        output["trace"] = diag._compact_playout_trace(result.get("trace") or [])
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(output, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return {
        "job_id": job.get("job_id"),
        "expected_output_json": job.get("expected_output_json"),
        "output_exists": output_path.exists(),
        "skipped_existing_output": False,
        "success": output_path.exists(),
        "duration_seconds": duration,
        "result": output.get("result"),
        "h40_outcome_label": output.get("h40_outcome_label"),
    }


def _run_job_with_timeout(
    job: dict[str, Any],
    *,
    cache: dict[str, tuple[Any, ReConEngine]],
    overwrite_existing_outputs: bool,
    timeout_seconds: int,
) -> dict[str, Any]:
    previous_handler = signal.getsignal(signal.SIGALRM)
    signal.signal(signal.SIGALRM, _raise_job_timeout)
    signal.setitimer(signal.ITIMER_REAL, float(timeout_seconds))
    start = time.perf_counter()
    try:
        return _run_job(
            job,
            cache=cache,
            overwrite_existing_outputs=overwrite_existing_outputs,
        )
    except _JobTimeoutError:
        return {
            "job_id": job.get("job_id"),
            "expected_output_json": job.get("expected_output_json"),
            "output_exists": _safe_output_exists(job),
            "skipped_existing_output": False,
            "success": False,
            "timed_out": True,
            "timeout_seconds": timeout_seconds,
            "duration_seconds": round(time.perf_counter() - start, 6),
            "error": "job_timeout",
        }
    except Exception as exc:
        return {
            "job_id": job.get("job_id"),
            "expected_output_json": job.get("expected_output_json"),
            "output_exists": _safe_output_exists(job),
            "skipped_existing_output": False,
            "success": False,
            "timed_out": False,
            "duration_seconds": round(time.perf_counter() - start, 6),
            "error": type(exc).__name__,
        }
    finally:
        signal.setitimer(signal.ITIMER_REAL, 0.0)
        signal.signal(signal.SIGALRM, previous_handler)


def _run_execution_readiness(manifest: dict[str, Any]) -> dict[str, Any]:
    module = _load_module(EXECUTION_READINESS_SCRIPT)
    return module.build_payload(manifest=manifest)


def _run_output_validation() -> dict[str, Any]:
    module = _load_module(OUTPUT_VALIDATION_SCRIPT)
    return module.build_payload()


def _approval_receipt_blockers(
    *,
    receipt: dict[str, Any] | None,
    receipt_path: Path,
    manifest: dict[str, Any],
    readiness: dict[str, Any],
    job_count: int,
) -> list[str]:
    blockers: list[str] = []
    if receipt is None:
        return ["approval_receipt_missing"]
    if receipt.get("schema_version") != APPROVAL_SCHEMA_VERSION:
        blockers.append("approval_receipt_schema_version_invalid")
    if receipt.get("approval_id") != "approve_protected_plan_window_failure_contrast_collection":
        blockers.append("approval_receipt_approval_id_invalid")
    if receipt.get("decision", {}).get("status") != APPROVAL_STATUS:
        blockers.append("approval_receipt_status_not_approved")
    if receipt.get("decision", {}).get("single_execution_only") is not True:
        blockers.append("approval_receipt_must_be_single_execution_only")
    if receipt.get("decision", {}).get("runtime_changes_allowed") is not False:
        blockers.append("approval_receipt_must_not_allow_runtime_changes")
    if receipt.get("decision", {}).get("label_run_allowed") is not False:
        blockers.append("approval_receipt_must_not_allow_label_run")
    if receipt.get("decision", {}).get("selector_training_allowed") is not False:
        blockers.append("approval_receipt_must_not_allow_selector_training")
    if receipt.get("decision", {}).get("stage7_promotion_allowed") is not False:
        blockers.append("approval_receipt_must_not_allow_stage7_promotion")
    if receipt.get("decision", {}).get("stage8_training_allowed") is not False:
        blockers.append("approval_receipt_must_not_allow_stage8_training")

    expected_manifest_fingerprint = readiness.get("summary", {}).get("manifest_fingerprint")
    expected_readiness_fingerprint = readiness.get("summary", {}).get("readiness_fingerprint")
    approval_scope = receipt.get("approval_scope") or {}
    if approval_scope.get("manifest_fingerprint") != expected_manifest_fingerprint:
        blockers.append("approval_receipt_manifest_fingerprint_mismatch")
    if approval_scope.get("readiness_fingerprint") != expected_readiness_fingerprint:
        blockers.append("approval_receipt_readiness_fingerprint_mismatch")
    if int(approval_scope.get("job_count") or 0) != job_count:
        blockers.append("approval_receipt_job_count_mismatch")
    if approval_scope.get("manifest_status") != manifest.get("decision", {}).get("status"):
        blockers.append("approval_receipt_manifest_status_mismatch")
    if (
        approval_scope.get("readiness_status")
        != readiness.get("decision", {}).get("status")
    ):
        blockers.append("approval_receipt_readiness_status_mismatch")
    expected_receipt_path = str(receipt_path.relative_to(ROOT))
    if receipt.get("receipt_path") not in {None, expected_receipt_path}:
        blockers.append("approval_receipt_path_mismatch")
    return blockers


def _invalid_existing_output_count(output_validation: dict[str, Any] | None) -> int:
    if output_validation is None:
        return 0
    return sum(
        1
        for row in output_validation.get("output_checks") or []
        if row.get("output_exists") and not row.get("valid")
    )


def _run_passive_refresh() -> dict[str, Any]:
    module = _load_module(FULL_GATE_ADVANCEMENT_SCRIPT)
    payload = module.build_payload()
    module.OUTPUT_JSON.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    module.OUTPUT_MD.write_text(module.write_markdown(payload), encoding="utf-8")
    return {
        "script": "scripts/advance_krk_suite_from_current_gates_v0.py",
        "status": payload.get("decision", {}).get("status"),
        "runtime_changes_allowed": payload.get("decision", {}).get("runtime_changes_allowed"),
        "label_run_allowed": payload.get("decision", {}).get("label_run_allowed"),
        "stage7_promotion_allowed": payload.get("decision", {}).get("stage7_promotion_allowed"),
        "stage8_training_allowed": payload.get("decision", {}).get("stage8_training_allowed"),
    }


def _validate_ready(
    manifest: dict[str, Any],
    readiness: dict[str, Any],
    output_validation: dict[str, Any] | None,
    *,
    overwrite_existing_outputs: bool,
    job_timeout_seconds: int,
    max_jobs: int | None,
) -> list[str]:
    blockers: list[str] = []
    if job_timeout_seconds <= 0:
        blockers.append("job_timeout_seconds_must_be_positive")
    if max_jobs is not None and max_jobs <= 0:
        blockers.append("max_jobs_must_be_positive_when_set")
    if manifest.get("decision", {}).get("status") != (
        "protected_plan_window_failure_contrast_manifest_ready_for_review"
    ):
        blockers.append("manifest_not_ready_for_review")
    if readiness.get("decision", {}).get("status") != (
        "protected_plan_window_failure_contrast_execution_ready_pending_explicit_approval"
    ):
        blockers.append("execution_readiness_not_ready")
    if not readiness.get("summary", {}).get("all_jobs_pass_readiness"):
        blockers.append("not_all_jobs_pass_readiness")
    if manifest.get("decision", {}).get("runtime_changes_allowed"):
        blockers.append("manifest_allows_runtime_changes")
    if manifest.get("decision", {}).get("stage7_promotion_allowed"):
        blockers.append("manifest_allows_stage7_promotion")
    if manifest.get("decision", {}).get("stage8_training_allowed"):
        blockers.append("manifest_allows_stage8_training")
    for job in manifest.get("jobs") or []:
        if not _safe_relative(job.get("expected_output_json"), required_root=OUTPUT_ROOT):
            blockers.append("unsafe_expected_output_json")
            break
        binding = job.get("execution_binding") or {}
        topology_path = str(binding.get("topology_path") or "")
        if (
            not _safe_relative(topology_path)
            or not topology_path
            or not (ROOT / topology_path).exists()
        ):
            blockers.append("missing_or_invalid_topology_binding")
            break
    if _invalid_existing_output_count(output_validation) and not overwrite_existing_outputs:
        blockers.append("invalid_existing_outputs_require_overwrite_or_cleanup")
    return blockers


def build_payload(
    *,
    execute: bool = False,
    max_jobs: int | None = None,
    refresh_after_run: bool = False,
    overwrite_existing_outputs: bool = False,
    job_timeout_seconds: int = DEFAULT_JOB_TIMEOUT_SECONDS,
    run_post_success_refresh: bool = True,
    approval_receipt_path: str | None = None,
) -> dict[str, Any]:
    manifest = _load(MANIFEST)
    readiness = _run_execution_readiness(manifest)
    output_validation = _run_output_validation()
    blockers = _validate_ready(
        manifest,
        readiness,
        output_validation,
        overwrite_existing_outputs=overwrite_existing_outputs,
        job_timeout_seconds=job_timeout_seconds,
        max_jobs=max_jobs,
    )
    jobs = list(manifest.get("jobs") or [])
    if max_jobs is not None:
        jobs = jobs[:max_jobs]
    receipt_path_error = None
    try:
        receipt_path = _approval_receipt_path(approval_receipt_path)
        approval_receipt = _load_optional(receipt_path)
    except ValueError as exc:
        receipt_path = DEFAULT_APPROVAL_RECEIPT
        approval_receipt = None
        receipt_path_error = str(exc)
    approval_blockers = []
    if receipt_path_error is not None:
        approval_blockers.append(receipt_path_error)
    approval_blockers.extend(
        _approval_receipt_blockers(
            receipt=approval_receipt,
            receipt_path=receipt_path,
            manifest=manifest,
            readiness=readiness,
            job_count=len(jobs),
        )
    )
    if execute:
        blockers.extend(approval_blockers)
    command_records = []
    for job in jobs:
        output_exists = _safe_output_exists(job)
        command_records.append(
            {
                "job_id": job.get("job_id"),
                "expected_output_json": job.get("expected_output_json"),
                "output_exists": output_exists,
                "would_execute": bool(execute and not blockers)
                and (overwrite_existing_outputs or not output_exists),
                "would_skip_existing_output": bool(execute and not blockers)
                and output_exists
                and not overwrite_existing_outputs,
            }
        )

    executed_jobs: list[dict[str, Any]] = []
    if execute and not blockers:
        cache: dict[str, tuple[Any, ReConEngine]] = {}
        for job in jobs:
            executed_jobs.append(
                _run_job_with_timeout(
                    job,
                    cache=cache,
                    overwrite_existing_outputs=overwrite_existing_outputs,
                    timeout_seconds=job_timeout_seconds,
                )
            )
    failed_jobs = [job for job in executed_jobs if not job.get("success")]
    skipped_jobs = [job for job in executed_jobs if job.get("skipped_existing_output")]
    actually_executed_jobs = [
        job for job in executed_jobs if not job.get("skipped_existing_output")
    ]
    timed_out_jobs = [job for job in executed_jobs if job.get("timed_out")]
    if execute and not blockers and not failed_jobs:
        output_validation = _run_output_validation()
    refresh_result = None
    if run_post_success_refresh and refresh_after_run and execute and not blockers and not failed_jobs:
        refresh_result = _run_passive_refresh()

    status = (
        "protected_plan_window_failure_contrast_runner_dry_run_ready"
        if not execute and not blockers
        else "protected_plan_window_failure_contrast_runner_blocked"
        if blockers
        else "protected_plan_window_failure_contrast_runner_executed_success"
        if execute and not failed_jobs
        else "protected_plan_window_failure_contrast_runner_executed_with_failures"
    )
    return {
        "schema_version": SCHEMA_VERSION,
        "causal_status": "non_causal_collection_runner_wrapper",
        **COMMON_FALSE_FLAGS,
        "source_artifacts": [
            "reports/strategy_arbitration/krk_protected_plan_window_failure_contrast_manifest_v0.json",
            "reports/strategy_arbitration/krk_protected_plan_window_failure_contrast_execution_readiness_v0.json",
            "reports/strategy_arbitration/krk_protected_plan_window_failure_contrast_output_validation_v0.json",
        ],
        "approval_receipt_path": str(receipt_path.relative_to(ROOT)),
        "execution_requested": execute,
        "execution_blockers": blockers,
        "summary": {
            "job_count": len(jobs),
            "processed_job_count": len(executed_jobs),
            "executed_job_count": len(actually_executed_jobs),
            "skipped_existing_output_count": len(skipped_jobs),
            "failed_job_count": len(failed_jobs),
            "timed_out_job_count": len(timed_out_jobs),
            "dry_run": not execute,
            "max_jobs": max_jobs,
            "job_timeout_seconds": job_timeout_seconds,
            "overwrite_existing_outputs": overwrite_existing_outputs,
            "execution_readiness_status": readiness.get("decision", {}).get("status"),
            "execution_readiness_jobs_passing": readiness.get("summary", {}).get(
                "jobs_passing_readiness"
            ),
            "execution_readiness_manifest_fingerprint": readiness.get("summary", {}).get(
                "manifest_fingerprint"
            ),
            "execution_readiness_fingerprint": readiness.get("summary", {}).get(
                "readiness_fingerprint"
            ),
            "execution_readiness_all_jobs_pass": readiness.get("summary", {}).get(
                "all_jobs_pass_readiness"
            ),
            "approval_receipt_required_for_execution": True,
            "approval_receipt_present": approval_receipt is not None,
            "approval_receipt_valid": not approval_blockers,
            "approval_receipt_blockers": approval_blockers,
            "output_validation_status": output_validation.get("decision", {}).get("status"),
            "output_exists_count": output_validation.get("summary", {}).get("output_exists_count"),
            "output_valid_count": output_validation.get("summary", {}).get("output_valid_count"),
            "invalid_existing_output_count": _invalid_existing_output_count(output_validation),
            "refresh_after_run_requested": refresh_after_run,
            "refresh_after_run_performed": refresh_result is not None,
            "stage7_training_row_count": 0,
            "runtime_authorization_row_count": 0,
        },
        "commands": command_records,
        "executed_jobs": executed_jobs,
        "post_run_refresh": refresh_result,
        "decision": {
            "status": status,
            "recommended_next_step": (
                "obtain_matching_approval_receipt_then_run_with_explicit_execute_flag"
                if not execute and not blockers
                else "run_passive_sequence_policy_refresh"
                if execute and not failed_jobs and not blockers
                else "review_runner_blockers_or_failed_jobs"
            ),
            "collection_run_allowed": bool(execute and not blockers),
            "label_run_allowed": False,
            "runtime_changes_allowed": False,
            "selector_allowed": False,
            "selector_training_allowed": False,
            "stage7_promotion_allowed": False,
            "stage8_training_allowed": False,
        },
    }


def write_markdown(payload: dict[str, Any]) -> str:
    summary = payload["summary"]
    decision = payload["decision"]
    lines = [
        "# KRK Protected Plan-Window Failure Contrast Runner v0",
        "",
        f"Status: `{decision['status']}`",
        "",
        "Default mode is dry-run only. Executing collection requires explicit user approval, the `--execute-reviewed-collection` flag, and a matching approval receipt. Runtime defaults, selector training, Stage 7 promotion, and Stage 8 training remain blocked.",
        "",
        "## Summary",
        "",
    ]
    for key, value in summary.items():
        lines.append(f"- {key}: `{value}`")
    lines.extend(["", "## Jobs", ""])
    for row in payload["commands"]:
        lines.append(
            f"- `{row['job_id']}` output_exists=`{row['output_exists']}` would_execute=`{row['would_execute']}` would_skip_existing=`{row['would_skip_existing_output']}`"
        )
    lines.extend(
        [
            "",
            "## Decision",
            "",
            f"- recommended_next_step: `{decision['recommended_next_step']}`",
            f"- collection_run_allowed: `{decision['collection_run_allowed']}`",
            f"- label_run_allowed: `{decision['label_run_allowed']}`",
            "- runtime_changes_allowed: `false`",
            "- selector_training_allowed: `false`",
            "- Stage 7 promotion and Stage 8 training remain blocked.",
        ]
    )
    return "\n".join(lines) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Approval-gated protected plan-window failure-contrast collection runner"
    )
    parser.add_argument(
        "--execute-reviewed-collection",
        action="store_true",
        help="Execute reviewed observation collection. Requires explicit user approval before use.",
    )
    parser.add_argument("--max-jobs", type=int, default=None)
    parser.add_argument("--refresh-after-run", action="store_true")
    parser.add_argument("--overwrite-existing-outputs", action="store_true")
    parser.add_argument("--job-timeout-seconds", type=int, default=DEFAULT_JOB_TIMEOUT_SECONDS)
    parser.add_argument(
        "--approval-receipt",
        default=str(DEFAULT_APPROVAL_RECEIPT.relative_to(ROOT)),
        help="Relative path to the explicit approval receipt required for execution.",
    )
    args, _unknown = parser.parse_known_args()

    payload = build_payload(
        execute=args.execute_reviewed_collection,
        max_jobs=args.max_jobs,
        refresh_after_run=args.refresh_after_run,
        overwrite_existing_outputs=args.overwrite_existing_outputs,
        job_timeout_seconds=args.job_timeout_seconds,
        approval_receipt_path=args.approval_receipt,
    )
    OUTPUT_JSON.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    OUTPUT_MD.write_text(write_markdown(payload), encoding="utf-8")
    print(
        json.dumps(
            {
                "decision": payload["decision"]["status"],
                "execution_requested": payload["execution_requested"],
                "processed_job_count": payload["summary"]["processed_job_count"],
                "executed_job_count": payload["summary"]["executed_job_count"],
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
