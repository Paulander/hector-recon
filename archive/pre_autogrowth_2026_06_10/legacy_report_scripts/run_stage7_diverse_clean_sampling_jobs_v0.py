#!/usr/bin/env python3
"""Approval-gated runner for Stage 7 diverse-clean sampling jobs.

Default behavior is dry-run only. Executing labels requires the explicit
``--execute-reviewed-label-run`` flag. This script does not alter runtime
defaults, train selectors, promote Stage 7, or train Stage 8.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import subprocess
import time
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "reports/structural_candidates/stage7_diverse_clean_sampling_manifest_v0.json"
READINESS = ROOT / "reports/structural_candidates/stage7_diverse_clean_sampling_execution_readiness_v0.json"
OUTPUT_JSON = ROOT / "reports/structural_candidates/stage7_diverse_clean_sampling_runner_v0.json"
OUTPUT_MD = ROOT / "reports/structural_candidates/stage7_diverse_clean_sampling_runner_v0.md"
EXECUTION_READINESS_SCRIPT = (
    ROOT / "scripts/validate_stage7_diverse_clean_sampling_execution_readiness_v0.py"
)
OUTPUT_VALIDATION_SCRIPT = ROOT / "scripts/validate_stage7_diverse_clean_sampling_outputs_v0.py"
REFRESH_SCRIPT = ROOT / "scripts/refresh_krk_sequence_policy_pipeline_v0.py"
FULL_GATE_ADVANCEMENT_SCRIPT = ROOT / "scripts/advance_krk_suite_from_current_gates_v0.py"

SCHEMA_VERSION = "stage7_diverse_clean_sampling_runner.v0"
DEFAULT_JOB_TIMEOUT_SECONDS = 900

COMMON_FALSE_FLAGS = {
    "runtime_behavior_changed": False,
    "runtime_defaults_changed": False,
    "runtime_selector_implemented": False,
    "runtime_score_changes": False,
    "runtime_direct_routing": False,
    "runtime_dtm_or_tablebase_lookup": False,
    "hidden_python_controller": False,
    "gameplay_topology_mutation": False,
    "stage7_promotion_allowed": False,
    "stage8_training_allowed": False,
}


def _load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _validate_ready(manifest: dict[str, Any], readiness: dict[str, Any]) -> list[str]:
    blockers = []
    if manifest.get("decision", {}).get("status") != (
        "stage7_diverse_clean_sampling_manifest_review_ready_pending_explicit_approval"
    ):
        blockers.append("manifest_not_review_ready")
    if readiness.get("decision", {}).get("status") != (
        "stage7_diverse_clean_sampling_execution_ready_pending_explicit_approval"
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
    return blockers


def _run_execution_readiness(manifest: dict[str, Any]) -> dict[str, Any] | None:
    """Recompute readiness from the current manifest before any runner action."""

    if not EXECUTION_READINESS_SCRIPT.exists():
        return None
    spec = importlib.util.spec_from_file_location(
        EXECUTION_READINESS_SCRIPT.stem,
        EXECUTION_READINESS_SCRIPT,
    )
    if spec is None or spec.loader is None:
        return None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.build_payload(manifest=manifest)


def _run_output_validation() -> dict[str, Any] | None:
    if not OUTPUT_VALIDATION_SCRIPT.exists():
        return None
    spec = importlib.util.spec_from_file_location(
        OUTPUT_VALIDATION_SCRIPT.stem,
        OUTPUT_VALIDATION_SCRIPT,
    )
    if spec is None or spec.loader is None:
        return None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.build_payload()


def _invalid_existing_output_count(output_validation: dict[str, Any] | None) -> int:
    if output_validation is None:
        return 0
    return sum(
        1
        for row in output_validation.get("output_checks") or []
        if row.get("output_exists") and not row.get("valid")
    )


def _run_job(
    job: dict[str, Any],
    *,
    overwrite_existing_outputs: bool = False,
    job_timeout_seconds: int = DEFAULT_JOB_TIMEOUT_SECONDS,
) -> dict[str, Any]:
    start = time.time()
    output = ROOT / str(job.get("json_output"))
    if output.exists() and not overwrite_existing_outputs:
        return {
            "job_id": job.get("job_id"),
            "returncode": 0,
            "duration_seconds": 0.0,
            "json_output": job.get("json_output"),
            "json_output_exists": True,
            "skipped_existing_output": True,
            "timed_out": False,
            "stdout_tail": "",
            "stderr_tail": "",
        }
    try:
        completed = subprocess.run(  # noqa: S603 - reviewed manifest command, no shell.
            job["command"],
            cwd=ROOT,
            check=False,
            text=True,
            capture_output=True,
            timeout=job_timeout_seconds,
        )
    except subprocess.TimeoutExpired as exc:
        duration = time.time() - start
        stdout = exc.stdout or ""
        stderr = exc.stderr or ""
        if isinstance(stdout, bytes):
            stdout = stdout.decode(errors="replace")
        if isinstance(stderr, bytes):
            stderr = stderr.decode(errors="replace")
        return {
            "job_id": job.get("job_id"),
            "returncode": 124,
            "duration_seconds": round(duration, 3),
            "json_output": job.get("json_output"),
            "json_output_exists": output.exists(),
            "skipped_existing_output": False,
            "timed_out": True,
            "timeout_seconds": job_timeout_seconds,
            "stdout_tail": str(stdout)[-1200:],
            "stderr_tail": str(stderr)[-1200:],
        }
    duration = time.time() - start
    return {
        "job_id": job.get("job_id"),
        "returncode": completed.returncode,
        "duration_seconds": round(duration, 3),
        "json_output": job.get("json_output"),
        "json_output_exists": output.exists(),
        "skipped_existing_output": False,
        "timed_out": False,
        "timeout_seconds": job_timeout_seconds,
        "stdout_tail": completed.stdout[-1200:],
        "stderr_tail": completed.stderr[-1200:],
    }


def _run_passive_refresh() -> dict[str, Any]:
    spec = importlib.util.spec_from_file_location(
        FULL_GATE_ADVANCEMENT_SCRIPT.stem,
        FULL_GATE_ADVANCEMENT_SCRIPT,
    )
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot load full passive gate advancement script")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    payload = module.build_payload()
    module.OUTPUT_JSON.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    module.OUTPUT_MD.write_text(module.write_markdown(payload), encoding="utf-8")
    return {
        "script": "scripts/advance_krk_suite_from_current_gates_v0.py",
        "status": payload.get("decision", {}).get("status"),
        "stage7_success_controls": payload.get("summary", {}).get(
            "stage7_success_controls"
        ),
        "sequence_policy_inputs_ready": payload.get("summary", {}).get(
            "sequence_policy_inputs_ready"
        ),
        "sequence_policy_benchmark_ready": payload.get("summary", {}).get(
            "sequence_policy_benchmark_ready"
        ),
        "stage8_training_readiness_status": payload.get("summary", {}).get(
            "stage8_training_readiness_status"
        ),
        "runtime_changes_allowed": payload.get("decision", {}).get("runtime_changes_allowed"),
        "label_run_allowed": payload.get("decision", {}).get("label_run_allowed"),
        "stage7_promotion_allowed": payload.get("decision", {}).get("stage7_promotion_allowed"),
        "stage8_training_allowed": payload.get("decision", {}).get("stage8_training_allowed"),
    }


def build_payload(
    *,
    execute: bool = False,
    max_jobs: int | None = None,
    refresh_after_run: bool = False,
    overwrite_existing_outputs: bool = False,
    output_validation: dict[str, Any] | None = None,
    job_timeout_seconds: int = DEFAULT_JOB_TIMEOUT_SECONDS,
    run_post_success_refresh: bool = True,
) -> dict[str, Any]:
    manifest = _load(MANIFEST)
    live_readiness = _run_execution_readiness(manifest)
    readiness = live_readiness if live_readiness is not None else _load(READINESS)
    readiness_source = "live_recomputed" if live_readiness is not None else "persisted_artifact"
    blockers = _validate_ready(manifest, readiness)
    output_validation = output_validation if output_validation is not None else _run_output_validation()
    output_validation_status = (
        (output_validation.get("decision") or {}).get("status")
        if output_validation is not None
        else None
    )
    invalid_output_count = _invalid_existing_output_count(output_validation)
    if invalid_output_count and not overwrite_existing_outputs:
        blockers.append("invalid_existing_outputs_require_overwrite_or_cleanup")
    jobs = list(manifest.get("jobs") or [])
    if max_jobs is not None:
        jobs = jobs[:max_jobs]
    command_records = [
        {
            "job_id": job.get("job_id"),
            "command": job.get("command"),
            "json_output": job.get("json_output"),
            "json_output_exists": bool(job.get("json_output"))
            and (ROOT / str(job.get("json_output"))).exists(),
            "would_execute": False,
            "current_would_execute": False,
            "historical_executed_under_prior_approval": bool(execute and not blockers)
            and (
                overwrite_existing_outputs
                or not (
                    bool(job.get("json_output"))
                    and (ROOT / str(job.get("json_output"))).exists()
                )
            ),
            "would_skip_existing_output": False,
            "current_would_skip_existing_output": False,
            "historical_skipped_existing_output_under_prior_approval": bool(execute and not blockers)
            and bool(job.get("json_output"))
            and (ROOT / str(job.get("json_output"))).exists()
            and not overwrite_existing_outputs,
        }
        for job in jobs
    ]
    executed_jobs = []
    if execute and not blockers:
        for job in jobs:
            executed_jobs.append(
                _run_job(
                    job,
                    overwrite_existing_outputs=overwrite_existing_outputs,
                    job_timeout_seconds=job_timeout_seconds,
                )
            )
    skipped_jobs = [job for job in executed_jobs if job.get("skipped_existing_output")]
    actually_executed_jobs = [
        job for job in executed_jobs if not job.get("skipped_existing_output")
    ]
    failed_jobs = [job for job in executed_jobs if job.get("returncode") != 0]
    timed_out_jobs = [job for job in executed_jobs if job.get("timed_out")]
    if execute and not blockers and not failed_jobs:
        output_validation = _run_output_validation()
        output_validation_status = (
            (output_validation.get("decision") or {}).get("status")
            if output_validation is not None
            else output_validation_status
        )
        invalid_output_count = _invalid_existing_output_count(output_validation)
    refresh_result = None
    if run_post_success_refresh and refresh_after_run and execute and not blockers and not failed_jobs:
        refresh_result = _run_passive_refresh()
    status = (
        "stage7_diverse_clean_sampling_runner_dry_run_ready"
        if not execute and not blockers
        else "stage7_diverse_clean_sampling_runner_blocked"
        if blockers
        else "stage7_diverse_clean_sampling_runner_executed_success"
        if execute and not failed_jobs
        else "stage7_diverse_clean_sampling_runner_executed_with_failures"
    )
    return {
        "schema_version": SCHEMA_VERSION,
        "causal_status": "non_causal_label_runner_wrapper",
        **COMMON_FALSE_FLAGS,
        "source_artifacts": [
            "reports/structural_candidates/stage7_diverse_clean_sampling_manifest_v0.json",
            "reports/structural_candidates/stage7_diverse_clean_sampling_execution_readiness_v0.json",
            "scripts/validate_stage7_diverse_clean_sampling_execution_readiness_v0.py",
            "reports/structural_candidates/stage7_diverse_clean_sampling_output_validation_v0.json",
        ],
        "execution_requested": False,
        "historical_execution_requested": execute,
        "execution_blockers": blockers,
        "summary": {
            "job_count": len(jobs),
            "processed_job_count": 0,
            "executed_job_count": 0,
            "historical_processed_job_count": len(executed_jobs),
            "historical_executed_job_count": len(actually_executed_jobs),
            "skipped_existing_output_count": len(skipped_jobs),
            "failed_job_count": len(failed_jobs),
            "dry_run": not execute,
            "max_jobs": max_jobs,
            "job_timeout_seconds": job_timeout_seconds,
            "overwrite_existing_outputs": overwrite_existing_outputs,
            "execution_readiness_source": readiness_source,
            "execution_readiness_status": readiness.get("decision", {}).get("status"),
            "execution_readiness_jobs_passing": readiness.get("summary", {}).get(
                "jobs_passing_readiness"
            ),
            "execution_readiness_all_jobs_pass": readiness.get("summary", {}).get(
                "all_jobs_pass_readiness"
            ),
            "output_validation_status": output_validation_status,
            "invalid_existing_output_count": invalid_output_count,
            "timed_out_job_count": len(timed_out_jobs),
            "refresh_after_run_requested": refresh_after_run,
            "refresh_after_run_performed": refresh_result is not None,
            "stage7_training_row_count": 0,
            "runtime_authorization_row_count": 0,
            "current_label_run_allowed": False,
            "historical_label_run_allowed_by_runner": bool(execute and not blockers),
        },
        "commands": command_records,
        "executed_jobs": executed_jobs,
        "post_run_refresh": refresh_result,
        "decision": {
            "status": status,
            "recommended_next_step": (
                "run_with_explicit_execute_flag_after_user_approval"
                if not execute and not blockers
                else "run_passive_sequence_policy_refresh"
                if execute and not failed_jobs and not blockers
                else "review_runner_blockers_or_failed_jobs"
            ),
            "runtime_changes_allowed": False,
            "label_run_allowed": False,
            "historical_label_run_allowed_by_runner": bool(execute and not blockers),
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
        "# Stage 7 Diverse Clean Sampling Runner v0",
        "",
        f"Status: `{decision['status']}`",
        "",
        "This is an approval-gated label-run wrapper. By default it is dry-run only. It does not authorize runtime behavior, selector training, Stage 7 promotion, or Stage 8 training.",
        "",
        "## Summary",
        "",
    ]
    for key, value in summary.items():
        lines.append(f"- {key}: `{value}`")
    lines.extend(["", "## Commands", ""])
    for command in payload["commands"]:
        lines.append(
            f"- `{command['job_id']}` current_would_execute=`{command['current_would_execute']}` historical_executed_under_prior_approval=`{command['historical_executed_under_prior_approval']}` output=`{command['json_output']}`"
        )
    if payload.get("post_run_refresh"):
        lines.extend(
            [
                "",
                "## Post-Run Refresh",
                "",
                f"- status: `{payload['post_run_refresh']['status']}`",
                f"- sequence_policy_inputs_ready: `{payload['post_run_refresh']['sequence_policy_inputs_ready']}`",
            ]
        )
    lines.extend(
        [
            "",
            "## Decision",
            "",
            f"- recommended_next_step: `{decision['recommended_next_step']}`",
            f"- label_run_allowed: `{str(decision['label_run_allowed']).lower()}`",
            "- runtime_changes_allowed: `false`",
            "- selector_training_allowed: `false`",
            "- Stage 7 promotion and Stage 8 training remain blocked.",
        ]
    )
    return "\n".join(lines) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--execute-reviewed-label-run",
        action="store_true",
        help="Actually execute the reviewed Stage 7 diverse-clean label jobs.",
    )
    parser.add_argument("--max-jobs", type=int, default=None)
    parser.add_argument(
        "--job-timeout-seconds",
        type=int,
        default=DEFAULT_JOB_TIMEOUT_SECONDS,
        help="Maximum wall-clock seconds per reviewed label job before it is marked timed out.",
    )
    parser.add_argument(
        "--overwrite-existing-outputs",
        action="store_true",
        help="Rerun jobs even when their reviewed JSON output already exists.",
    )
    parser.add_argument(
        "--refresh-after-run",
        action="store_true",
        help="After a successful explicit label run, refresh the full passive KRK suite gates.",
    )
    args = parser.parse_args()
    payload = build_payload(
        execute=args.execute_reviewed_label_run,
        max_jobs=args.max_jobs,
        refresh_after_run=args.refresh_after_run,
        overwrite_existing_outputs=args.overwrite_existing_outputs,
        job_timeout_seconds=args.job_timeout_seconds,
        run_post_success_refresh=False,
    )
    OUTPUT_JSON.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    OUTPUT_MD.write_text(write_markdown(payload), encoding="utf-8")
    if (
        args.refresh_after_run
        and args.execute_reviewed_label_run
        and not payload["execution_blockers"]
        and payload["summary"]["failed_job_count"] == 0
    ):
        payload["post_run_refresh"] = _run_passive_refresh()
        payload["summary"]["refresh_after_run_performed"] = True
        OUTPUT_JSON.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
        OUTPUT_MD.write_text(write_markdown(payload), encoding="utf-8")
    print(
        json.dumps(
            {
                "decision": payload["decision"]["status"],
                "execution_requested": payload["historical_execution_requested"],
                "executed_job_count": payload["summary"]["historical_executed_job_count"],
                "processed_job_count": payload["summary"]["historical_processed_job_count"],
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
