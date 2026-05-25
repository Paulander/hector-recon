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
REFRESH_SCRIPT = ROOT / "scripts/refresh_krk_sequence_policy_pipeline_v0.py"

SCHEMA_VERSION = "stage7_diverse_clean_sampling_runner.v0"

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


def _run_job(job: dict[str, Any], *, overwrite_existing_outputs: bool = False) -> dict[str, Any]:
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
            "stdout_tail": "",
            "stderr_tail": "",
        }
    completed = subprocess.run(  # noqa: S603 - reviewed manifest command, no shell.
        job["command"],
        cwd=ROOT,
        check=False,
        text=True,
        capture_output=True,
    )
    duration = time.time() - start
    return {
        "job_id": job.get("job_id"),
        "returncode": completed.returncode,
        "duration_seconds": round(duration, 3),
        "json_output": job.get("json_output"),
        "json_output_exists": output.exists(),
        "skipped_existing_output": False,
        "stdout_tail": completed.stdout[-1200:],
        "stderr_tail": completed.stderr[-1200:],
    }


def _run_passive_refresh() -> dict[str, Any]:
    spec = importlib.util.spec_from_file_location(REFRESH_SCRIPT.stem, REFRESH_SCRIPT)
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot load passive refresh script")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    payload = module.run_refresh()
    module.OUTPUT_JSON.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    module.OUTPUT_MD.write_text(module.write_markdown(payload), encoding="utf-8")
    return {
        "script": "scripts/refresh_krk_sequence_policy_pipeline_v0.py",
        "status": payload.get("decision", {}).get("status"),
        "stage7_success_controls": payload.get("summary", {}).get("stage7_success_controls"),
        "sequence_policy_inputs_ready": payload.get("summary", {}).get(
            "sequence_policy_inputs_ready"
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
) -> dict[str, Any]:
    manifest = _load(MANIFEST)
    readiness = _load(READINESS)
    blockers = _validate_ready(manifest, readiness)
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
            "would_execute": bool(execute and not blockers)
            and (
                overwrite_existing_outputs
                or not (
                    bool(job.get("json_output"))
                    and (ROOT / str(job.get("json_output"))).exists()
                )
            ),
            "would_skip_existing_output": bool(execute and not blockers)
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
                _run_job(job, overwrite_existing_outputs=overwrite_existing_outputs)
            )
    skipped_jobs = [job for job in executed_jobs if job.get("skipped_existing_output")]
    failed_jobs = [job for job in executed_jobs if job.get("returncode") != 0]
    refresh_result = None
    if refresh_after_run and execute and not blockers and not failed_jobs:
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
        ],
        "execution_requested": execute,
        "execution_blockers": blockers,
        "summary": {
            "job_count": len(jobs),
            "executed_job_count": len(executed_jobs),
            "skipped_existing_output_count": len(skipped_jobs),
            "failed_job_count": len(failed_jobs),
            "dry_run": not execute,
            "max_jobs": max_jobs,
            "overwrite_existing_outputs": overwrite_existing_outputs,
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
                "run_with_explicit_execute_flag_after_user_approval"
                if not execute and not blockers
                else "run_passive_sequence_policy_refresh"
                if execute and not failed_jobs and not blockers
                else "review_runner_blockers_or_failed_jobs"
            ),
            "runtime_changes_allowed": False,
            "label_run_allowed": bool(execute and not blockers),
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
            f"- `{command['job_id']}` would_execute=`{command['would_execute']}` skip_existing=`{command.get('would_skip_existing_output', False)}` output=`{command['json_output']}`"
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
        "--overwrite-existing-outputs",
        action="store_true",
        help="Rerun jobs even when their reviewed JSON output already exists.",
    )
    parser.add_argument(
        "--refresh-after-run",
        action="store_true",
        help="After a successful explicit label run, refresh passive sequence-policy artifacts.",
    )
    args = parser.parse_args()
    payload = build_payload(
        execute=args.execute_reviewed_label_run,
        max_jobs=args.max_jobs,
        refresh_after_run=args.refresh_after_run,
        overwrite_existing_outputs=args.overwrite_existing_outputs,
    )
    OUTPUT_JSON.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    OUTPUT_MD.write_text(write_markdown(payload), encoding="utf-8")
    print(
        json.dumps(
            {
                "decision": payload["decision"]["status"],
                "execution_requested": payload["execution_requested"],
                "executed_job_count": payload["summary"]["executed_job_count"],
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
