#!/usr/bin/env python3
"""Plan a bounded protected hard-negative provider label expansion.

This remains an offline data-quality slice. It selects protected Stage 4/5/6
state/provider pairs that are underrepresented in the current hard-negative
selector evidence. Stage 7 is deliberately excluded.
"""

from __future__ import annotations

import hashlib
import json
from collections import Counter
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
RANKED_FRAMES = Path("reports/krk_ranked_strategy_proposal_frames_v1.json")
CAPACITY_FRAMES = Path("reports/krk_protected_provider_coverage_frames_v0.json")
HARD_NEGATIVE_ABLATION = Path("reports/krk_hard_negative_selector_feature_ablation_v0.json")
STATE_LOCAL_CONTRAST = Path("reports/krk_state_local_contrast_labels_v2.json")
MISSING_PROVIDER_LABELS = Path("reports/krk_protected_missing_provider_capacity_labels_v0.json")
OUT_JSON = Path("reports/krk_balanced_hard_negative_label_plan_v0.json")
OUT_MD = Path("reports/krk_balanced_hard_negative_label_plan_v0.md")


PROVIDER_CANDIDATES_BY_STAGE = {
    "stage4": [
        "krk.stage0_basin",
        "krk.drive_to_edge",
        "krk.fence_established",
        "krk.edge_trap_close",
        "krk.edge_trap_wrong_tempo",
        "krk.edge_trap_enemy_between",
    ],
    "stage5": [
        "krk.drive_to_edge",
        "krk.stage0_basin",
        "krk.fence_established",
        "krk.edge_trap_close",
        "krk.edge_trap_wrong_tempo",
        "krk.edge_trap_enemy_between",
    ],
    "stage6": [
        "krk.edge_trap_close",
        "krk.edge_trap_wrong_tempo",
        "krk.edge_trap_enemy_between",
        "krk.fence_established",
        "krk.stage0_basin",
        "krk.drive_to_edge",
    ],
}

MAX_JOBS = 12
MIN_JOBS_BY_STAGE = {"stage4": 3, "stage5": 5, "stage6": 3}


def _load(path: Path) -> dict[str, Any]:
    payload = json.loads((ROOT / path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"expected JSON object: {path}")
    return payload


def _job_id(frame_id: str, provider_id: str) -> str:
    digest = hashlib.sha1(f"{frame_id}|{provider_id}|balanced_hard_negative_v0".encode("utf-8")).hexdigest()[:12]
    return f"job.krk.balanced_hard_negative.{digest}"


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


def _result_label(row: dict[str, Any]) -> str | None:
    result = row.get("forced_result") or row.get("result")
    if result == "mate":
        return "positive"
    if result == "max_plies":
        return "hard_negative"
    capacity = row.get("capacity_label")
    if capacity == "positive_capacity":
        return "positive"
    if capacity == "negative_capacity":
        return "hard_negative"
    contrast = row.get("contrast_label")
    if contrast in {"positive", "negative"}:
        return str(contrast)
    return None


def _existing_pairs(*payloads: dict[str, Any]) -> set[tuple[str, str]]:
    pairs: set[tuple[str, str]] = set()
    for payload in payloads:
        for row in payload.get("rows") or payload.get("labels") or []:
            state_id = row.get("state_id")
            provider_id = row.get("provider_id")
            if state_id and provider_id and row.get("source_stage") != "stage7":
                pairs.add((str(state_id), str(provider_id)))
    return pairs


def _known_negative_counts(*payloads: dict[str, Any]) -> Counter[str]:
    counts: Counter[str] = Counter()
    for payload in payloads:
        for row in payload.get("rows") or payload.get("labels") or []:
            if row.get("source_stage") == "stage7":
                continue
            if _result_label(row) in {"negative", "hard_negative"}:
                stage = str(row.get("source_stage") or "unknown")
                provider = str(row.get("provider_id") or "unknown")
                counts[f"stage:{stage}"] += 1
                counts[f"provider:{_provider_family(provider)}"] += 1
                counts[f"stage_provider:{stage}:{_provider_family(provider)}"] += 1
    return counts


def _frame_groups(ranked: dict[str, Any]) -> list[dict[str, Any]]:
    groups: dict[str, list[dict[str, Any]]] = {}
    for row in ranked.get("rows") or []:
        if row.get("source_stage") == "stage7":
            continue
        groups.setdefault(str(row.get("frame_id")), []).append(row)
    frames = []
    for frame_id, rows in groups.items():
        first = rows[0]
        frames.append(
            {
                "frame_id": frame_id,
                "state_id": first.get("state_id"),
                "source_stage": first.get("source_stage"),
                "active_landmark_label": first.get("active_landmark_label"),
                "fen": first.get("fen"),
                "existing_runtime_providers": sorted({str(row.get("provider_id")) for row in rows}),
                "known_frame_outcomes": sorted({str(row.get("frame_outcome") or "unknown") for row in rows}),
            }
        )
    return frames


def build_plan() -> dict[str, Any]:
    ranked = _load(RANKED_FRAMES)
    capacity = _load(CAPACITY_FRAMES)
    ablation = _load(HARD_NEGATIVE_ABLATION)
    contrast = _load(STATE_LOCAL_CONTRAST)
    missing = _load(MISSING_PROVIDER_LABELS)
    if ranked.get("causal_status") != "non_causal_ranked_frame_dataset":
        raise ValueError("ranked frames must remain non-causal")
    if capacity.get("causal_status") != "non_causal_capacity_frame_dataset":
        raise ValueError("capacity frames must remain non-causal")
    if ablation.get("causal_status") != "non_causal_feature_ablation":
        raise ValueError("hard-negative ablation must remain non-causal")
    labeled_pairs = _existing_pairs(capacity, contrast, missing)
    negative_counts = _known_negative_counts(capacity, contrast, missing)
    candidates = []
    for frame in _frame_groups(ranked):
        stage = str(frame.get("source_stage") or "")
        if stage == "stage7":
            continue
        for provider_id in PROVIDER_CANDIDATES_BY_STAGE.get(stage, []):
            state_id = str(frame.get("state_id") or "")
            if (state_id, provider_id) in labeled_pairs:
                continue
            family = _provider_family(provider_id)
            priority = (
                negative_counts[f"stage_provider:{stage}:{family}"],
                negative_counts[f"provider:{family}"],
                negative_counts[f"stage:{stage}"],
                0 if provider_id not in frame["existing_runtime_providers"] else 1,
                str(frame["frame_id"]),
                provider_id,
            )
            candidates.append((priority, frame, provider_id))
    candidates.sort(key=lambda item: item[0])
    jobs = []
    used_states_by_stage: Counter[str] = Counter()
    used_families: Counter[str] = Counter()
    deferred = []

    def maybe_add_job(frame: dict[str, Any], provider_id: str) -> bool:
        stage = str(frame.get("source_stage"))
        family = _provider_family(provider_id)
        # Keep the first pass broad: at most two jobs per source state, and
        # avoid spending the small label budget on one provider family.
        state_key = str(frame.get("state_id"))
        if used_states_by_stage[f"{stage}:{state_key}"] >= 2:
            return False
        if used_families[f"{stage}:{family}"] >= 3:
            return False
        jobs.append(
            {
                "schema_version": "krk_balanced_hard_negative_label_job.v0",
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
                "known_frame_outcomes": frame.get("known_frame_outcomes"),
                "purpose": "collect_balanced_protected_hard_negative_or_positive_capacity_label",
                "label_semantics": "forced_provider_capacity_not_runtime_ownership",
                "stage7_training_row": False,
                "causal_status": "non_causal_label_plan",
            }
        )
        used_states_by_stage[f"{stage}:{state_key}"] += 1
        used_families[f"{stage}:{family}"] += 1
        return True

    for _priority, frame, provider_id in candidates:
        stage = str(frame.get("source_stage"))
        if sum(1 for job in jobs if job["source_stage"] == stage) < MIN_JOBS_BY_STAGE.get(stage, 0):
            maybe_add_job(frame, provider_id)
        else:
            deferred.append((frame, provider_id))
        if len(jobs) >= MAX_JOBS:
            break
    for frame, provider_id in deferred:
        if len(jobs) >= MAX_JOBS:
            break
        maybe_add_job(frame, provider_id)
    payload = {
        "schema_version": "krk_balanced_hard_negative_label_plan.v0",
        "causal_status": "non_causal_label_plan",
        "runtime_behavior_changed": False,
        "runtime_defaults_changed": False,
        "runtime_selector_implemented": False,
        "runtime_candidate_generator_implemented": False,
        "runtime_dtm_or_tablebase_lookup": False,
        "gameplay_topology_mutation": False,
        "stage7_promotion_allowed": False,
        "stage8_training_allowed": False,
        "source_artifacts": [
            str(RANKED_FRAMES),
            str(CAPACITY_FRAMES),
            str(HARD_NEGATIVE_ABLATION),
            str(STATE_LOCAL_CONTRAST),
            str(MISSING_PROVIDER_LABELS),
        ],
        "label_budget": {
            "max_jobs": MAX_JOBS,
            "horizon": 40,
            "trace_failures_only": True,
            "diagnostic_caches": True,
            "stage7_jobs": 0,
            "expensive_sweeps_allowed": False,
        },
        "existing_negative_balance": dict(sorted(negative_counts.items())),
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
            "status": "balanced_hard_negative_label_plan_ready",
            "recommended_next_step": "bind_and_review_balanced_hard_negative_execution_manifest",
            "runtime_work_allowed": False,
            "selector_training_allowed": False,
        },
        "blocked_actions": [
            "runtime selector changes",
            "selector training",
            "Stage 7 repair or promotion",
            "Stage 8 training",
            "runtime DTM/tablebase use",
            "gameplay topology mutation",
        ],
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
    for job in payload.get("jobs") or []:
        if job.get("causal_status") != "non_causal_label_plan":
            raise ValueError("jobs must remain non-causal")
        if job.get("stage7_training_row"):
            raise ValueError("no Stage 7 training rows allowed")


def render_markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# KRK Balanced Hard-Negative Label Plan v0",
        "",
        "Bounded non-causal plan to improve protected hard-negative label balance before any selector training or runtime work.",
        "",
        "## Summary",
        "",
    ]
    for key, value in payload["summary"].items():
        lines.append(f"- `{key}`: `{value}`")
    lines.extend(["", "## Label Budget", ""])
    for key, value in payload["label_budget"].items():
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
