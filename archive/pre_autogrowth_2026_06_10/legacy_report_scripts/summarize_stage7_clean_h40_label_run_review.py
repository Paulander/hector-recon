#!/usr/bin/env python3
"""Review the bounded clean Stage 7 h40 label run."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
MANIFEST = Path("reports/structural_candidates/stage7_clean_h40_label_manifest_v0.json")
RUN = Path("reports/structural_candidates/stage7_clean_h40_label_run_seed17_10_h40.json")
RECOVERY = Path("reports/structural_candidates/stage7_clean_sequence_control_recovery_v0.json")
OUT_JSON = Path("reports/structural_candidates/stage7_clean_h40_label_run_review_v0.json")
OUT_MD = Path("reports/structural_candidates/stage7_clean_h40_label_run_review_v0.md")


def _load(path: Path) -> dict[str, Any]:
    payload = json.loads((ROOT / path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"expected JSON object: {path}")
    return payload


def build_review() -> dict[str, Any]:
    manifest = _load(MANIFEST)
    run = _load(RUN)
    recovery = _load(RECOVERY)
    playouts = dict(run.get("playouts", {}) or {})
    enabled_flags = sorted(
        key for key, value in run.items()
        if isinstance(value, bool)
        and value is True
        and (
            key.startswith("stage7_")
            or key.startswith("enable_")
            or key.startswith("krk_strategy_arbiter")
            or key.startswith("krk_two_stage_abstention")
        )
    )
    recovered_sources = recovery.get("summary", {}).get("source_artifact_counts") or {}
    recovered_from_run = int(recovered_sources.get(str(RUN), 0) or 0)
    success_count = int(playouts.get("mate", 0) or 0)
    max_plies_count = int(playouts.get("max_plies", 0) or 0)
    novel_success_gap_closed = bool(
        recovery.get("acceptance", {}).get("clean_sequence_success_controls_met") is True
    )
    if recovered_from_run == 0 and success_count > 0:
        status = "bounded_label_run_no_novel_clean_success_controls"
        next_step = "review_sampling_diversity_or_architecture_boundary_before_more_labels"
    elif novel_success_gap_closed:
        status = "bounded_label_run_closed_clean_success_gap"
        next_step = "build_clean_selected_path_dataset_and_source_bias_audit"
    else:
        status = "bounded_label_run_clean_gap_still_open"
        next_step = "review_before_additional_label_jobs"
    return {
        "schema_version": "stage7_clean_h40_label_run_review.v0",
        "causal_status": "non_causal_label_run_review",
        "runtime_behavior_changed": False,
        "runtime_defaults_changed": False,
        "runtime_selector_implemented": False,
        "runtime_dtm_or_tablebase_lookup": False,
        "gameplay_topology_mutation": False,
        "stage7_promotion_allowed": False,
        "stage8_training_allowed": False,
        "source_artifacts": [str(MANIFEST), str(RUN), str(RECOVERY)],
        "run": {
            "artifact": str(RUN),
            "total": run.get("total"),
            "playouts": playouts,
            "one_ply_status_counts": run.get("one_ply_status_counts"),
            "conversion_status_counts": run.get("conversion_status_counts"),
            "semantic_alignment_status_counts": run.get("semantic_alignment_status_counts"),
            "shadow_candidate_count": run.get("shadow_candidate_count"),
            "enabled_stage7_or_runtime_flags": enabled_flags,
        },
        "recovery_after_run": {
            "control_count": recovery.get("summary", {}).get("control_count"),
            "role_counts": recovery.get("summary", {}).get("role_counts"),
            "source_artifact_counts": recovered_sources,
            "controls_recovered_from_run": recovered_from_run,
            "clean_success_gap_closed": novel_success_gap_closed,
        },
        "summary": {
            "run_mate_count": success_count,
            "run_max_plies_count": max_plies_count,
            "recovered_from_run": recovered_from_run,
            "enabled_stage7_or_runtime_flag_count": len(enabled_flags),
            "no_runtime_repair_flags_detected": len(enabled_flags) == 0,
            "label_job_added_novel_controls": recovered_from_run > 0,
        },
        "decision": {
            "status": status,
            "recommended_next_step": next_step,
            "runtime_work_allowed": False,
        },
    }


def render_markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# Stage 7 Clean h40 Label Run Review v0",
        "",
        f"Status: `{payload['decision']['status']}`",
        "",
        "Review of the single bounded current-default Stage 7 h40 label job.",
        "",
        "## Summary",
        "",
    ]
    for key, value in payload["summary"].items():
        lines.append(f"- {key}: `{value}`")
    lines.extend(
        [
            "",
            "## Run",
            "",
            f"- total: `{payload['run']['total']}`",
            f"- playouts: `{payload['run']['playouts']}`",
            f"- shadow_candidate_count: `{payload['run']['shadow_candidate_count']}`",
            f"- enabled_stage7_or_runtime_flags: `{payload['run']['enabled_stage7_or_runtime_flags']}`",
            "",
            "## Recovery After Run",
            "",
        ]
    )
    for key, value in payload["recovery_after_run"].items():
        lines.append(f"- {key}: `{value}`")
    lines.extend(["", f"Next step: `{payload['decision']['recommended_next_step']}`", ""])
    return "\n".join(lines)


def main() -> None:
    payload = build_review()
    (ROOT / OUT_JSON).write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (ROOT / OUT_MD).write_text(render_markdown(payload), encoding="utf-8")


if __name__ == "__main__":
    main()
