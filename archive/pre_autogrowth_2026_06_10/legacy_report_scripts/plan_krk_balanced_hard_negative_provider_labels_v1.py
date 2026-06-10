#!/usr/bin/env python3
"""Plan a second bounded protected hard-negative provider label expansion."""

from __future__ import annotations

import hashlib
import json
from collections import Counter
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
RANKED_FRAMES = Path("reports/krk_ranked_strategy_proposal_frames_v1.json")
TARGETS_V1 = Path("reports/krk_hard_negative_selector_target_dataset_v1.json")
BALANCED_LABELS_V0 = Path("reports/krk_balanced_hard_negative_labels_v0.json")
ABLATION_V1 = Path("reports/krk_hard_negative_selector_feature_ablation_v1.json")
OUT_JSON = Path("reports/krk_balanced_hard_negative_label_plan_v1.json")
OUT_MD = Path("reports/krk_balanced_hard_negative_label_plan_v1.md")


PROVIDERS = [
    "krk.stage0_basin",
    "krk.drive_to_edge",
    "krk.fence_established",
    "krk.edge_trap_close",
    "krk.edge_trap_wrong_tempo",
    "krk.edge_trap_enemy_between",
]
MAX_JOBS = 12


def _load(path: Path) -> dict[str, Any]:
    payload = json.loads((ROOT / path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"expected JSON object: {path}")
    return payload


def _provider_family(provider_id: str) -> str:
    if "stage0_basin" in provider_id:
        return "stage0_basin"
    if "drive_to_edge" in provider_id:
        return "drive_to_edge"
    if "fence_established" in provider_id:
        return "fence_established"
    if "edge_trap" in provider_id:
        return "edge_trap"
    return provider_id.rsplit(".", 1)[-1]


def _job_id(frame_id: str, provider_id: str) -> str:
    digest = hashlib.sha1(f"{frame_id}|{provider_id}|balanced_hard_negative_v1".encode("utf-8")).hexdigest()[:12]
    return f"job.krk.balanced_hard_negative.v1.{digest}"


def _labeled_pairs(*payloads: dict[str, Any]) -> set[tuple[str, str]]:
    pairs: set[tuple[str, str]] = set()
    for payload in payloads:
        for row in payload.get("rows") or payload.get("labels") or []:
            if row.get("source_stage") == "stage7":
                continue
            state_id = row.get("state_id")
            provider_id = row.get("provider_id")
            if state_id and provider_id:
                pairs.add((str(state_id), str(provider_id)))
    return pairs


def _frame_groups(ranked: dict[str, Any]) -> list[dict[str, Any]]:
    grouped: dict[str, list[dict[str, Any]]] = {}
    for row in ranked.get("rows") or []:
        if row.get("source_stage") != "stage7":
            grouped.setdefault(str(row.get("state_id")), []).append(row)
    frames = []
    for _state_id, rows in grouped.items():
        first = rows[0]
        frames.append(
            {
                "frame_id": first.get("frame_id"),
                "state_id": first.get("state_id"),
                "source_stage": first.get("source_stage"),
                "active_landmark_label": first.get("active_landmark_label"),
                "fen": first.get("fen"),
                "existing_runtime_providers": sorted({str(row.get("provider_id")) for row in rows}),
            }
        )
    return frames


def _priority(frame: dict[str, Any], provider_id: str) -> tuple[int, int, int, str, str]:
    stage = str(frame.get("source_stage"))
    family = _provider_family(provider_id)
    # v1 specifically probes mismatched/underrepresented families that are more
    # likely to become hard negatives than the already-converting protected labels.
    target_stage_family = {
        ("stage6", "edge_trap"): 0,
        ("stage6", "fence_established"): 1,
        ("stage4", "drive_to_edge"): 2,
        ("stage4", "fence_established"): 3,
        ("stage5", "drive_to_edge"): 4,
        ("stage5", "edge_trap"): 5,
    }.get((stage, family), 9)
    absent_from_runtime = 0 if provider_id not in frame.get("existing_runtime_providers", []) else 1
    return (target_stage_family, absent_from_runtime, len(frame.get("existing_runtime_providers", [])), stage, provider_id)


def build_plan() -> dict[str, Any]:
    ranked = _load(RANKED_FRAMES)
    targets = _load(TARGETS_V1)
    labels_v0 = _load(BALANCED_LABELS_V0)
    ablation = _load(ABLATION_V1)
    if ranked.get("causal_status") != "non_causal_ranked_frame_dataset":
        raise ValueError("ranked frames must remain non-causal")
    if targets.get("causal_status") != "non_causal_target_dataset":
        raise ValueError("targets must remain non-causal")
    if labels_v0.get("causal_status") != "non_causal_label_run":
        raise ValueError("prior labels must remain non-causal")
    if ablation.get("causal_status") != "non_causal_feature_ablation":
        raise ValueError("ablation must remain non-causal")
    labeled = _labeled_pairs(targets, labels_v0)
    candidates = []
    for frame in _frame_groups(ranked):
        if frame.get("source_stage") == "stage7":
            continue
        for provider_id in PROVIDERS:
            if (str(frame.get("state_id")), provider_id) not in labeled:
                candidates.append((_priority(frame, provider_id), frame, provider_id))
    candidates.sort(key=lambda item: item[0])
    jobs = []
    used_states: Counter[str] = Counter()
    used_stage_family: Counter[str] = Counter()
    for _prio, frame, provider_id in candidates:
        stage = str(frame.get("source_stage"))
        family = _provider_family(provider_id)
        if used_states[str(frame.get("state_id"))] >= 2:
            continue
        if used_stage_family[f"{stage}:{family}"] >= 4:
            continue
        jobs.append(
            {
                "schema_version": "krk_balanced_hard_negative_label_job.v1",
                "job_id": _job_id(str(frame.get("frame_id")), provider_id),
                "frame_id": frame.get("frame_id"),
                "state_id": frame.get("state_id"),
                "source_stage": stage,
                "active_landmark_label": frame.get("active_landmark_label"),
                "fen": frame.get("fen"),
                "provider_id": provider_id,
                "provider_family": family,
                "horizon": 40,
                "existing_runtime_providers": frame.get("existing_runtime_providers"),
                "purpose": "second_pass_collect_underrepresented_protected_hard_negative_capacity_label",
                "label_semantics": "forced_provider_capacity_not_runtime_ownership",
                "stage7_training_row": False,
                "causal_status": "non_causal_label_plan",
            }
        )
        used_states[str(frame.get("state_id"))] += 1
        used_stage_family[f"{stage}:{family}"] += 1
        if len(jobs) >= MAX_JOBS:
            break
    payload = {
        "schema_version": "krk_balanced_hard_negative_label_plan.v1",
        "causal_status": "non_causal_label_plan",
        "runtime_behavior_changed": False,
        "runtime_defaults_changed": False,
        "runtime_selector_implemented": False,
        "runtime_candidate_generator_implemented": False,
        "runtime_dtm_or_tablebase_lookup": False,
        "gameplay_topology_mutation": False,
        "stage7_promotion_allowed": False,
        "stage8_training_allowed": False,
        "source_artifacts": [str(RANKED_FRAMES), str(TARGETS_V1), str(BALANCED_LABELS_V0), str(ABLATION_V1)],
        "label_budget": {
            "max_jobs": MAX_JOBS,
            "horizon": 40,
            "trace_failures_only": True,
            "diagnostic_caches": True,
            "stage7_jobs": 0,
            "expensive_sweeps_allowed": False,
        },
        "jobs": jobs,
        "summary": {
            "job_count": len(jobs),
            "source_state_count": len({job["state_id"] for job in jobs}),
            "stage_counts": dict(Counter(str(job["source_stage"]) for job in jobs)),
            "provider_family_counts": dict(Counter(str(job["provider_family"]) for job in jobs)),
            "stage7_jobs": sum(1 for job in jobs if job.get("source_stage") == "stage7"),
            "runtime_work_allowed": False,
        },
        "decision": {
            "status": "balanced_hard_negative_label_plan_v1_ready",
            "recommended_next_step": "bind_and_review_balanced_hard_negative_execution_manifest_v1",
            "runtime_work_allowed": False,
            "selector_training_allowed": False,
        },
    }
    validate_plan(payload)
    return payload


def validate_plan(payload: dict[str, Any]) -> None:
    for key in (
        "runtime_behavior_changed",
        "runtime_defaults_changed",
        "runtime_selector_implemented",
        "runtime_candidate_generator_implemented",
        "runtime_dtm_or_tablebase_lookup",
        "gameplay_topology_mutation",
        "stage7_promotion_allowed",
        "stage8_training_allowed",
    ):
        if payload.get(key) is not False:
            raise ValueError(f"{key} must be false")
    if payload["summary"]["stage7_jobs"] != 0:
        raise ValueError("Stage 7 jobs must remain excluded")
    if len(payload.get("jobs") or []) > MAX_JOBS:
        raise ValueError("label plan exceeds bounded budget")


def render_markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# KRK Balanced Hard-Negative Label Plan v1",
        "",
        "Second bounded non-causal pass focused on underrepresented protected hard-negative provider families.",
        "",
        "## Summary",
        "",
    ]
    for key, value in payload["summary"].items():
        lines.append(f"- `{key}`: `{value}`")
    lines.extend(["", "## Jobs", ""])
    for job in payload["jobs"]:
        lines.append(
            f"- `{job['job_id']}` stage=`{job['source_stage']}` state=`{job['state_id']}` "
            f"provider=`{job['provider_id']}` family=`{job['provider_family']}`"
        )
    lines.extend(["", "## Decision", ""])
    for key, value in payload["decision"].items():
        lines.append(f"- `{key}`: `{value}`")
    lines.append("")
    return "\n".join(lines)


def main() -> None:
    payload = build_plan()
    (ROOT / OUT_JSON).write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (ROOT / OUT_MD).write_text(render_markdown(payload), encoding="utf-8")
    print(json.dumps(payload["summary"], indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
