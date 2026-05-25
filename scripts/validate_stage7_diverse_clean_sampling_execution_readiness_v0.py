#!/usr/bin/env python3
"""Validate Stage 7 diverse clean sampling execution readiness without running it."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "reports/structural_candidates/stage7_diverse_clean_sampling_manifest_v0.json"
OUTPUT_JSON = ROOT / "reports/structural_candidates/stage7_diverse_clean_sampling_execution_readiness_v0.json"
OUTPUT_MD = ROOT / "reports/structural_candidates/stage7_diverse_clean_sampling_execution_readiness_v0.md"

SCHEMA_VERSION = "stage7_diverse_clean_sampling_execution_readiness.v0"

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


def _command_has_forbidden_flags(command: list[str], forbidden_flags: list[str]) -> list[str]:
    return [flag for flag in forbidden_flags if flag in command]


def _validate_job(job: dict[str, Any]) -> dict[str, Any]:
    command = list(job.get("command") or [])
    script = command[2] if len(command) >= 3 and command[:2] == ["uv", "run"] else None
    if script == "python" and len(command) >= 4:
        script = command[3]
    output = job.get("json_output")
    topology = job.get("topology")
    forbidden_hits = _command_has_forbidden_flags(command, job.get("forbidden_flags") or [])
    return {
        "job_id": job.get("job_id"),
        "source_stage_names": job.get("source_stage_names") or [],
        "samples": job.get("samples"),
        "playout_max_plies": job.get("playout_max_plies"),
        "command_shape_valid": command[:3] == ["uv", "run", "python"],
        "script": script,
        "script_exists": bool(script) and (ROOT / str(script)).exists(),
        "topology": topology,
        "topology_exists": bool(topology) and (ROOT / str(topology)).exists(),
        "json_output": output,
        "json_output_exists": bool(output) and (ROOT / str(output)).exists(),
        "forbidden_flag_hits": forbidden_hits,
        "runtime_work_allowed": bool(job.get("runtime_work_allowed")),
        "stage7_training_row": bool(job.get("stage7_training_row")),
        "stage7_promotion_allowed": bool(job.get("stage7_promotion_allowed")),
        "stage8_training_allowed": bool(job.get("stage8_training_allowed")),
        "passes_readiness_checks": (
            command[:3] == ["uv", "run", "python"]
            and bool(script)
            and (ROOT / str(script)).exists()
            and bool(topology)
            and (ROOT / str(topology)).exists()
            and int(job.get("samples") or 0) <= 8
            and int(job.get("playout_max_plies") or 0) == 40
            and not forbidden_hits
            and not bool(job.get("runtime_work_allowed"))
            and not bool(job.get("stage7_training_row"))
            and not bool(job.get("stage7_promotion_allowed"))
            and not bool(job.get("stage8_training_allowed"))
        ),
    }


def build_payload(*, manifest: dict[str, Any] | None = None) -> dict[str, Any]:
    manifest = manifest or _load(MANIFEST)
    job_checks = [_validate_job(job) for job in manifest.get("jobs") or []]
    all_jobs_pass = all(job["passes_readiness_checks"] for job in job_checks)
    no_existing_outputs = not any(job["json_output_exists"] for job in job_checks)
    manifest_blocks_execution = (
        manifest.get("decision", {}).get("implementation_authorized_by_this_manifest") is False
        and manifest.get("summary", {}).get("label_run_allowed_by_this_manifest") is False
    )
    ready_pending_approval = all_jobs_pass and manifest_blocks_execution
    return {
        "schema_version": SCHEMA_VERSION,
        "causal_status": "non_causal_execution_readiness_check",
        **COMMON_FALSE_FLAGS,
        "source_artifacts": [
            "reports/structural_candidates/stage7_diverse_clean_sampling_manifest_v0.json"
        ],
        "summary": {
            "job_count": len(job_checks),
            "jobs_passing_readiness": sum(1 for job in job_checks if job["passes_readiness_checks"]),
            "all_jobs_pass_readiness": all_jobs_pass,
            "max_total_samples": sum(int(job.get("samples") or 0) for job in job_checks),
            "max_horizon": max((int(job.get("playout_max_plies") or 0) for job in job_checks), default=0),
            "output_exists_count": sum(1 for job in job_checks if job["json_output_exists"]),
            "no_existing_outputs": no_existing_outputs,
            "manifest_blocks_execution": manifest_blocks_execution,
            "execution_authorized_by_this_report": False,
            "stage7_training_row_count": sum(1 for job in job_checks if job["stage7_training_row"]),
        },
        "job_checks": job_checks,
        "decision": {
            "status": (
                "stage7_diverse_clean_sampling_execution_ready_pending_explicit_approval"
                if ready_pending_approval
                else "stage7_diverse_clean_sampling_execution_readiness_failed"
            ),
            "recommended_next_step": (
                "explicitly_approve_or_reject_stage7_diverse_clean_label_run"
                if ready_pending_approval
                else "repair_stage7_diverse_clean_sampling_manifest"
            ),
            "execution_authorized_by_this_report": False,
            "runtime_changes_allowed": False,
            "label_run_allowed": False,
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
        "# Stage 7 Diverse Clean Sampling Execution Readiness v0",
        "",
        f"Status: `{decision['status']}`",
        "",
        "This is a dry-run readiness check only. It validates the reviewed commands and boundaries, but it does not execute labels or authorize execution.",
        "",
        "## Summary",
        "",
    ]
    for key, value in summary.items():
        lines.append(f"- {key}: `{value}`")
    lines.extend(["", "## Job Checks", ""])
    for job in payload["job_checks"]:
        lines.append(
            f"- `{job['job_id']}` passes=`{job['passes_readiness_checks']}` sources=`{job['source_stage_names']}` output_exists=`{job['json_output_exists']}`"
        )
    lines.extend(
        [
            "",
            "## Decision",
            "",
            f"- recommended_next_step: `{decision['recommended_next_step']}`",
            "- execution_authorized_by_this_report: `false`",
            "- runtime_changes_allowed: `false`",
            "- label_run_allowed: `false`",
            "- Stage 7 promotion and Stage 8 training remain blocked.",
        ]
    )
    return "\n".join(lines) + "\n"


def main() -> None:
    payload = build_payload()
    OUTPUT_JSON.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    OUTPUT_MD.write_text(write_markdown(payload), encoding="utf-8")
    print(
        json.dumps(
            {
                "decision": payload["decision"]["status"],
                "job_count": payload["summary"]["job_count"],
                "jobs_passing_readiness": payload["summary"]["jobs_passing_readiness"],
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
