#!/usr/bin/env python3
"""Plan bounded forced-provider control labels for KRK arbitration evidence.

This script creates non-causal label jobs only. It does not run playouts, force
providers at runtime, train models, mutate topology, or change defaults.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter
from pathlib import Path
from typing import Any


FILTERED_FRAMES = Path("reports/krk_control_plane_filtered_frames_v0.json")
STRATIFIED_PROBE = Path("reports/krk_strategy_arbiter_stratified_probe_v2.json")


def _load_json(root: Path, relative_path: Path) -> dict[str, Any]:
    payload = json.loads((root / relative_path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"expected JSON object: {relative_path}")
    return payload


def _result(label: dict[str, Any]) -> str:
    value = label.get("result") or label.get("playout_result")
    return str(value) if value in {"mate", "max_plies", "draw", "stagnation"} else "unknown"


def _semantics(label: dict[str, Any]) -> str:
    if label.get("source") == "forced_provider_result":
        return "forced_provider_outcome"
    if "playout_result" in label:
        if label.get("selected") is True:
            return "selected_provider_playout"
        if label.get("selected") is False:
            return "same_move_unselected_provider_playout"
        return "playout_without_selection_flag"
    if "result" in label:
        return "result_without_source"
    return "unknown"


def _benchmark_frames(payload: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        frame
        for frame in payload.get("frames") or []
        if "strategy_arbitration_benchmark" in (frame.get("filter_metadata") or {}).get("benchmark_roles", [])
    ]


def _job_id(frame_id: str, provider_id: str, move_uci: str) -> str:
    raw = f"{frame_id}|{provider_id}|{move_uci}".encode("utf-8")
    return "job.krk.forced_provider_control." + hashlib.sha1(raw).hexdigest()[:12]


def build_plan(repo_root: Path, *, max_jobs: int = 12, max_jobs_per_stage: int = 6) -> dict[str, Any]:
    filtered = _load_json(repo_root, FILTERED_FRAMES)
    stratified = _load_json(repo_root, STRATIFIED_PROBE)
    if filtered.get("causal_status") != "non_causal_filtered_frame_export":
        raise ValueError("filtered frames must remain non-causal")
    if stratified.get("causal_status") != "non_causal_probe":
        raise ValueError("stratified probe must remain non-causal")

    jobs = []
    stage_counts: Counter[str] = Counter()
    result_counts: Counter[str] = Counter()
    seen: set[tuple[str, str, str]] = set()
    target_stages = {"stage5", "stage6"}
    for frame in _benchmark_frames(filtered):
        stage = str(frame.get("source_stage") or "")
        if stage not in target_stages or stage_counts[stage] >= max_jobs_per_stage:
            continue
        proposals = frame.get("strategy_proposal_frames") or []
        # Prefer selected-provider labels first, then same-move unselected labels to
        # cover both semantics found in the risk review.
        proposals = sorted(
            proposals,
            key=lambda proposal: (
                0
                if _semantics(proposal.get("known_outcome_label") or {}) == "selected_provider_playout"
                else 1,
                str(proposal.get("provider_id") or ""),
            ),
        )
        for proposal in proposals:
            if len(jobs) >= max_jobs or stage_counts[stage] >= max_jobs_per_stage:
                break
            provider_id = str(proposal.get("provider_id") or "")
            move_uci = str(proposal.get("move_uci") or "")
            if not provider_id or not move_uci:
                continue
            key = (str(frame.get("frame_id") or ""), provider_id, move_uci)
            if key in seen:
                continue
            seen.add(key)
            label = proposal.get("known_outcome_label") or {}
            if not isinstance(label, dict):
                label = {}
            current_result = _result(label)
            current_semantics = _semantics(label)
            jobs.append(
                {
                    "schema_version": "krk_forced_provider_control_label_job.v0",
                    "job_id": _job_id(str(frame.get("frame_id") or ""), provider_id, move_uci),
                    "causal_status": "non_causal_label_job",
                    "labels_generated": False,
                    "runtime_behavior_changed": False,
                    "frame_id": frame.get("frame_id"),
                    "state_id": frame.get("state_id"),
                    "source_stage": stage,
                    "active_landmark_label": frame.get("active_landmark_label"),
                    "fen": frame.get("fen"),
                    "provider_id": provider_id,
                    "move_uci": move_uci,
                    "current_label_result": current_result,
                    "current_label_semantics": current_semantics,
                    "target_label_semantics": "forced_provider_outcome",
                    "horizon": 40,
                    "trace_mode": "failures_only",
                    "diagnostic_caches_required": True,
                    "purpose": "Make protected Stage5/6 labels comparable to forced Stage7 provider labels before any arbiter sandbox.",
                }
            )
            stage_counts[stage] += 1
            result_counts[current_result] += 1

    plan = {
        "schema_version": "krk_forced_provider_control_label_plan.v0",
        "causal_status": "non_causal_label_plan",
        "runtime_behavior_changed": False,
        "runtime_defaults_changed": False,
        "runtime_arbiter_implemented": False,
        "runtime_terminals_added": False,
        "runtime_dtm_or_tablebase_lookup": False,
        "gameplay_topology_mutation": False,
        "labels_generated_in_this_slice": False,
        "stage7_promotion_allowed": False,
        "stage8_training_allowed": False,
        "source_artifacts": [str(FILTERED_FRAMES), str(STRATIFIED_PROBE)],
        "reason": "Stratified probe v2 found selected protected-control labels promising but forced Stage7 labels weak/sparse.",
        "job_selection": {
            "target_stages": sorted(target_stages),
            "max_jobs": max_jobs,
            "max_jobs_per_stage": max_jobs_per_stage,
            "selected_job_count": len(jobs),
            "selected_job_count_by_stage": dict(stage_counts),
            "current_label_result_counts": dict(result_counts),
        },
        "jobs": jobs,
        "acceptance_for_future_label_run": [
            "no_runtime_behavior_change",
            "no_stage7_promotion",
            "no_stage8_training",
            "no_runtime_dtm_or_tablebase",
            "no_exhaustive_legal_first_sweeps",
            "forced_provider_labels_are_non_causal_outcome_labels",
            "run_stops_if_projected_to_hours",
        ],
        "post_label_decision_gate": [
            "rerun stratified arbiter probe with protected forced-provider controls",
            "if forced-control hit rates remain weak, do not implement arbiter sandbox",
            "if forced-control and Stage7 forced strata separate cleanly, prepare a default-off equivalence-only sandbox skeleton review",
        ],
        "recommended_next_step": "run_bounded_forced_provider_control_labels_if_runner_available",
        "blocked_next_steps": [
            "runtime_arbiter",
            "runtime_internal_terminal",
            "stage7_promotion",
            "stage8_training",
            "runtime_dtm_or_tablebase",
            "gameplay_topology_mutation",
        ],
    }
    validate_plan(plan)
    return plan


def validate_plan(plan: dict[str, Any]) -> None:
    if plan.get("causal_status") != "non_causal_label_plan":
        raise ValueError("plan must remain non-causal")
    for key in (
        "runtime_behavior_changed",
        "runtime_defaults_changed",
        "runtime_arbiter_implemented",
        "runtime_terminals_added",
        "runtime_dtm_or_tablebase_lookup",
        "gameplay_topology_mutation",
        "labels_generated_in_this_slice",
        "stage7_promotion_allowed",
        "stage8_training_allowed",
    ):
        if plan.get(key) is not False:
            raise ValueError(f"{key} must be false")
    for job in plan.get("jobs") or []:
        if job.get("causal_status") != "non_causal_label_job":
            raise ValueError("jobs must remain non-causal")
        if job.get("labels_generated") is not False:
            raise ValueError("jobs must not claim generated labels")


def render_markdown(plan: dict[str, Any]) -> str:
    selection = plan["job_selection"]
    lines = [
        "# KRK Forced Provider Control Label Plan v0",
        "",
        "This is a non-causal job plan. It does not run labels, force providers "
        "during gameplay, implement an arbiter, change defaults, promote Stage 7, "
        "or train Stage 8.",
        "",
        "## Rationale",
        "",
        plan["reason"],
        "",
        "## Job Selection",
        "",
        f"- Target stages: `{selection['target_stages']}`",
        f"- Selected jobs: `{selection['selected_job_count']}`",
        f"- Jobs by stage: `{selection['selected_job_count_by_stage']}`",
        f"- Current label result counts: `{selection['current_label_result_counts']}`",
        "",
        "## Jobs",
        "",
    ]
    for job in plan["jobs"]:
        lines.append(
            f"- `{job['job_id']}` stage=`{job['source_stage']}` provider=`{job['provider_id']}` "
            f"move=`{job['move_uci']}` current=`{job['current_label_semantics']}:{job['current_label_result']}`"
        )
    lines.extend(
        [
            "",
            "## Acceptance For Future Label Run",
            "",
        ]
    )
    lines.extend(f"- `{item}`" for item in plan["acceptance_for_future_label_run"])
    lines.extend(
        [
            "",
            "## Recommended Next Step",
            "",
            f"`{plan['recommended_next_step']}`",
            "",
        ]
    )
    return "\n".join(lines)


def write_outputs(plan: dict[str, Any], report_root: Path) -> None:
    report_root.mkdir(parents=True, exist_ok=True)
    (report_root / "krk_forced_provider_control_label_plan_v0.json").write_text(
        json.dumps(plan, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    (report_root / "krk_forced_provider_control_label_plan_v0.md").write_text(
        render_markdown(plan), encoding="utf-8"
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=Path("."))
    parser.add_argument("--report-root", type=Path, default=Path("reports"))
    parser.add_argument("--max-jobs", type=int, default=12)
    parser.add_argument("--max-jobs-per-stage", type=int, default=6)
    args = parser.parse_args()

    repo_root = args.repo_root.resolve()
    report_root = args.report_root
    if not report_root.is_absolute():
        report_root = repo_root / report_root
    plan = build_plan(
        repo_root,
        max_jobs=args.max_jobs,
        max_jobs_per_stage=args.max_jobs_per_stage,
    )
    write_outputs(plan, report_root)
    print(json.dumps(plan["job_selection"], indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
