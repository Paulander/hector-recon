#!/usr/bin/env python3
"""Approval-gated runner wrapper for the additional Stage 7 clean sampling manifest."""

from __future__ import annotations

import argparse
import importlib.util
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RUNNER_SCRIPT = ROOT / "scripts/run_stage7_diverse_clean_sampling_jobs_v0.py"
MANIFEST = ROOT / "reports/structural_candidates/stage7_additional_clean_sampling_manifest_v0.json"
OUTPUT_VALIDATION_SCRIPT = ROOT / "scripts/validate_stage7_additional_clean_sampling_outputs_v0.py"
OUTPUT_JSON = ROOT / "reports/structural_candidates/stage7_additional_clean_sampling_runner_v0.json"
OUTPUT_MD = ROOT / "reports/structural_candidates/stage7_additional_clean_sampling_runner_v0.md"


def _load_runner():
    spec = importlib.util.spec_from_file_location(RUNNER_SCRIPT.stem, RUNNER_SCRIPT)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load runner script: {RUNNER_SCRIPT}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


runner = _load_runner()
ORIGINAL_VALIDATE_READY = runner._validate_ready

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


def _load(path: Path) -> dict:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise TypeError(f"{path} must contain a JSON object")
    return data


def _validate_ready(manifest: dict, readiness: dict) -> list[str]:
    blockers = ORIGINAL_VALIDATE_READY(manifest, readiness)
    if (
        "manifest_not_review_ready" in blockers
        and manifest.get("decision", {}).get("status")
        == "stage7_additional_clean_sampling_manifest_ready_pending_explicit_approval"
    ):
        blockers.remove("manifest_not_review_ready")
    return blockers


def build_payload(
    *,
    execute: bool = False,
    max_jobs: int | None = None,
    refresh_after_run: bool = False,
    overwrite_existing_outputs: bool = False,
    job_timeout_seconds: int = runner.DEFAULT_JOB_TIMEOUT_SECONDS,
    run_post_success_refresh: bool = True,
) -> dict:
    manifest = _load(MANIFEST)
    if (
        (manifest.get("decision") or {}).get("status")
        == "stage7_additional_clean_sampling_manifest_not_applicable_success_gate_closed"
    ):
        return {
            "schema_version": "stage7_additional_clean_sampling_runner.v0",
            "causal_status": "non_causal_label_runner_wrapper",
            **COMMON_FALSE_FLAGS,
            "source_artifacts": [
                "reports/structural_candidates/stage7_additional_clean_sampling_manifest_v0.json",
                "scripts/run_stage7_additional_clean_sampling_jobs_v0.py",
            ],
            "execution_requested": bool(execute),
            "execution_blockers": ["stage7_success_gate_closed_no_additional_labels_allowed"],
            "commands": [],
            "executed_jobs": [],
            "post_run_refresh": None,
            "summary": {
                "dry_run": not execute,
                "job_count": 0,
                "max_jobs": max_jobs,
                "processed_job_count": 0,
                "executed_job_count": 0,
                "failed_job_count": 0,
                "timed_out_job_count": 0,
                "skipped_existing_output_count": 0,
                "invalid_existing_output_count": 0,
                "job_timeout_seconds": job_timeout_seconds,
                "overwrite_existing_outputs": overwrite_existing_outputs,
                "refresh_after_run_requested": refresh_after_run,
                "refresh_after_run_performed": False,
                "execution_readiness_status": "not_applicable_stage7_success_gate_closed",
                "execution_readiness_source": "manifest_closed_success_gate",
                "execution_readiness_all_jobs_pass": False,
                "execution_readiness_jobs_passing": 0,
                "output_validation_status": (
                    "stage7_additional_clean_sampling_outputs_not_applicable_success_gate_closed"
                ),
                "stage7_training_row_count": 0,
                "runtime_authorization_row_count": 0,
            },
            "decision": {
                "status": (
                    "stage7_additional_clean_sampling_runner_not_applicable_success_gate_closed"
                ),
                "recommended_next_step": "rerun_passive_sequence_policy_gate_stack",
                "runtime_changes_allowed": False,
                "label_run_allowed": False,
                "selector_allowed": False,
                "selector_training_allowed": False,
                "stage7_promotion_allowed": False,
                "stage8_training_allowed": False,
            },
        }

    original_manifest = runner.MANIFEST
    original_validate_ready = runner._validate_ready
    original_output_validation_script = runner.OUTPUT_VALIDATION_SCRIPT
    try:
        runner.MANIFEST = MANIFEST
        runner._validate_ready = _validate_ready
        runner.OUTPUT_VALIDATION_SCRIPT = OUTPUT_VALIDATION_SCRIPT
        payload = runner.build_payload(
            execute=execute,
            max_jobs=max_jobs,
            refresh_after_run=refresh_after_run,
            overwrite_existing_outputs=overwrite_existing_outputs,
            job_timeout_seconds=job_timeout_seconds,
            run_post_success_refresh=run_post_success_refresh,
        )
    finally:
        runner.MANIFEST = original_manifest
        runner._validate_ready = original_validate_ready
        runner.OUTPUT_VALIDATION_SCRIPT = original_output_validation_script
    payload["schema_version"] = "stage7_additional_clean_sampling_runner.v0"
    payload["source_artifacts"] = [
        "reports/structural_candidates/stage7_additional_clean_sampling_manifest_v0.json",
        "scripts/run_stage7_additional_clean_sampling_jobs_v0.py",
    ]
    status = payload["decision"].get("status")
    if isinstance(status, str):
        payload["decision"]["status"] = status.replace(
            "stage7_diverse_clean_sampling", "stage7_additional_clean_sampling"
        )
    return payload


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Approval-gated runner for Stage 7 additional clean sampling jobs"
    )
    parser.add_argument(
        "--execute-reviewed-label-run",
        action="store_true",
        help="Execute reviewed label jobs. Requires explicit user approval before use.",
    )
    parser.add_argument("--max-jobs", type=int, default=None)
    parser.add_argument("--refresh-after-run", action="store_true")
    parser.add_argument("--overwrite-existing-outputs", action="store_true")
    parser.add_argument(
        "--job-timeout-seconds",
        type=int,
        default=runner.DEFAULT_JOB_TIMEOUT_SECONDS,
    )
    args, _unknown = parser.parse_known_args()

    payload = build_payload(
        execute=args.execute_reviewed_label_run,
        max_jobs=args.max_jobs,
        refresh_after_run=args.refresh_after_run,
        overwrite_existing_outputs=args.overwrite_existing_outputs,
        job_timeout_seconds=args.job_timeout_seconds,
    )
    OUTPUT_JSON.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    OUTPUT_MD.write_text(runner.write_markdown(payload), encoding="utf-8")
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
