#!/usr/bin/env python3
"""Plan a protected missing-provider/capacity audit for max-only frames."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
MAX_ONLY_REVIEW = Path("reports/krk_protected_max_only_frame_review_v0.json")
OUT_JSON = Path("reports/krk_protected_missing_provider_capacity_audit_plan_v0.json")
OUT_MD = Path("reports/krk_protected_missing_provider_capacity_audit_plan_v0.md")


PROVIDER_CANDIDATES_BY_STAGE = {
    "stage4": [
        "krk.stage0_basin",
        "krk.edge_trap_close",
        "krk.edge_trap_wrong_tempo",
        "krk.edge_trap_enemy_between",
        "krk.fence_established",
    ],
    "stage5": [
        "krk.stage0_basin",
        "krk.edge_trap_close",
        "krk.edge_trap_wrong_tempo",
        "krk.edge_trap_enemy_between",
        "krk.fence_established",
    ],
    "stage6": [
        "krk.stage0_basin",
        "krk.drive_to_edge",
        "krk.fence_established",
        "krk.edge_trap_close",
    ],
}


def _load(path: Path) -> dict[str, Any]:
    payload = json.loads((ROOT / path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"expected JSON object: {path}")
    return payload


def _job_id(frame_id: str, provider_id: str) -> str:
    digest = hashlib.sha1(f"{frame_id}|{provider_id}".encode("utf-8")).hexdigest()[:12]
    return f"job.krk.protected_missing_provider.{digest}"


def build_plan() -> dict[str, Any]:
    review = _load(MAX_ONLY_REVIEW)
    jobs = []
    seen_jobs: set[tuple[str, str]] = set()
    for frame in review.get("max_only_frames") or []:
        stage = str(frame.get("source_stage") or "")
        if stage == "stage7":
            continue
        existing = set((frame.get("max_only_provider_counts") or {}).keys())
        candidates = [provider for provider in PROVIDER_CANDIDATES_BY_STAGE.get(stage, []) if provider not in existing]
        for provider_id in candidates[:3]:
            key = (str(frame.get("frame_id")), provider_id)
            if key in seen_jobs:
                continue
            seen_jobs.add(key)
            jobs.append(
                {
                    "schema_version": "krk_protected_missing_provider_capacity_job.v0",
                    "job_id": _job_id(str(frame.get("frame_id")), provider_id),
                    "frame_id": frame.get("frame_id"),
                    "state_id": frame.get("state_id"),
                    "source_stage": stage,
                    "active_landmark_label": frame.get("active_landmark_label"),
                    "fen": frame.get("fen"),
                    "provider_id": provider_id,
                    "horizon": 40,
                    "purpose": "test_whether_unlabeled_validated_provider_can_convert_max_only_frame",
                    "stage7_training_row": False,
                    "causal_status": "non_causal_label_plan",
                }
            )
    return {
        "schema_version": "krk_protected_missing_provider_capacity_audit_plan.v0",
        "causal_status": "non_causal_label_plan",
        "runtime_behavior_changed": False,
        "runtime_defaults_changed": False,
        "runtime_selector_implemented": False,
        "runtime_dtm_or_tablebase_lookup": False,
        "gameplay_topology_mutation": False,
        "stage7_promotion_allowed": False,
        "stage8_training_allowed": False,
        "source_artifacts": [str(MAX_ONLY_REVIEW)],
        "label_budget": {
            "max_frames": 12,
            "max_jobs": 36,
            "horizon": 40,
            "trace_failures_only": True,
            "diagnostic_caches": True,
            "stage7_jobs": 0,
        },
        "jobs": jobs[:36],
        "summary": {
            "job_count": min(len(jobs), 36),
            "source_frame_count": len({job["frame_id"] for job in jobs[:36]}),
            "provider_counts": {
                provider: sum(1 for job in jobs[:36] if job["provider_id"] == provider)
                for provider in sorted({job["provider_id"] for job in jobs[:36]})
            },
            "stage_counts": {
                stage: sum(1 for job in jobs[:36] if job["source_stage"] == stage)
                for stage in sorted({job["source_stage"] for job in jobs[:36]})
            },
            "runtime_work_allowed": False,
        },
        "decision": {
            "status": "protected_missing_provider_capacity_audit_plan_ready",
            "recommended_next_step": "review_manifest_before_any_label_execution",
            "runtime_work_allowed": False,
        },
        "blocked_actions": [
            "execute labels without review",
            "runtime selector changes",
            "Stage 7 repair or promotion",
            "Stage 8 training",
            "runtime DTM/tablebase use",
            "gameplay topology mutation",
        ],
    }


def render_markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# KRK Protected Missing-Provider Capacity Audit Plan v0",
        "",
        f"Status: `{payload['decision']['status']}`",
        "",
        "This is a non-causal label plan for protected Stage 4/5/6 frames that currently have only max-plies provider labels.",
        "",
        "## Summary",
        "",
    ]
    for key, value in payload["summary"].items():
        lines.append(f"- {key}: `{value}`")
    lines.extend(["", "## Label Budget", ""])
    for key, value in payload["label_budget"].items():
        lines.append(f"- {key}: `{value}`")
    lines.extend(["", "## Jobs", ""])
    for job in payload["jobs"]:
        lines.append(
            f"- `{job['job_id']}` frame=`{job['frame_id']}` stage=`{job['source_stage']}` provider=`{job['provider_id']}`"
        )
    lines.extend(["", "## Blocked Actions", ""])
    for item in payload["blocked_actions"]:
        lines.append(f"- `{item}`")
    lines.extend(["", f"Recommended next step: `{payload['decision']['recommended_next_step']}`", ""])
    return "\n".join(lines)


def main() -> None:
    payload = build_plan()
    (ROOT / OUT_JSON).write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (ROOT / OUT_MD).write_text(render_markdown(payload), encoding="utf-8")


if __name__ == "__main__":
    main()
