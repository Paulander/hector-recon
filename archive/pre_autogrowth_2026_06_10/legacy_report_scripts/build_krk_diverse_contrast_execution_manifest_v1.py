#!/usr/bin/env python3
"""Build a bounded execution manifest for diverse KRK contrast labels."""

from __future__ import annotations

import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
PLAN = Path("reports/krk_diverse_contrast_label_plan_v1.json")
RANKED_FRAMES = Path("reports/krk_ranked_strategy_proposal_frames_v1.json")
OUT_JSON = Path("reports/krk_diverse_contrast_execution_manifest_v1.json")
OUT_MD = Path("reports/krk_diverse_contrast_execution_manifest_v1.md")

TOPOLOGY = Path(
    "snapshots/krk_triplet_pipeline/adaptive_krk_stage6_drive_overlay_composed/topology/krk_entry_topology.json"
)
STAGE5_CHECKPOINT = Path(
    "snapshots/krk_triplet_pipeline/adaptive_krk_stage5_fence_clean/baseline/best_by_stage/fence_established.pkl"
)
STAGE6_CHECKPOINT = Path(
    "snapshots/krk_triplet_pipeline/adaptive_krk_stage6_drive_profile_king_support/baseline/best_by_stage/drive_to_edge.pkl"
)

PROFILE_SETTINGS = {
    "successor_affordance_layer_enabled": True,
    "successor_role_license_enabled": True,
    "successor_role_scoped_move_shape_enabled": True,
    "successor_role_scoped_move_shape_bonus": 0.05,
    "stagnation_breaker_enabled": True,
    "stagnation_breaker_bonus": 0.5,
    "post_break_continuation_enabled": True,
    "post_break_continuation_bonus": 0.25,
    "successor_stage0_drift_penalty": 6.0,
}


def _load_json(path: Path) -> dict[str, Any]:
    payload = json.loads((ROOT / path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"expected JSON object: {path}")
    return payload


def _job_id(state_id: str, provider_id: str, move_uci: str) -> str:
    raw = f"{state_id}|{provider_id}|{move_uci}|diverse_v1".encode("utf-8")
    return "job.krk.diverse_contrast." + hashlib.sha1(raw).hexdigest()[:12]


def _provider_version(provider_id: str) -> str:
    if provider_id == "krk.drive_to_edge":
        return "stage6_overlay_v1"
    return "stage5_validated_v1" if provider_id != "krk.stage0_basin" else "stage0_foundation_v1"


def _source_checkpoint(provider_id: str) -> str:
    return str(STAGE6_CHECKPOINT if provider_id == "krk.drive_to_edge" else STAGE5_CHECKPOINT)


def _binding(provider_id: str) -> dict[str, Any]:
    return {
        "topology_path": str(TOPOLOGY),
        "topology_version": "stage6_overlay_composed_v1",
        "composition_profile": "handoff_composition_v1",
        "provider_version": _provider_version(provider_id),
        "topology_component": "stage6_overlay_composed_with_stage5_frozen_provider_pack",
        "source_checkpoint": _source_checkpoint(provider_id),
        "execution_mode": "force_provider_first_white_move_then_release",
        "black_policy": "adversarial",
        "max_ticks": 200,
        "suggestion_limit": 10,
        "early_stop_stable_suggestions": 3,
        "enable_diagnostic_caches": True,
        "trace_mode": "failures_only",
        "profile_settings": dict(PROFILE_SETTINGS),
    }


def _stage_stratum(stage: str) -> str:
    return {
        "stage4": "protected_stage4_wrong_tempo",
        "stage5": "protected_stage5_fence",
        "stage6": "protected_stage6_drive",
        "stage7": "stage7_challenge_eval_only",
    }.get(stage, "unknown")


def _allowed_family(stage: str, family: str | None) -> bool:
    allowed = {
        "stage4": {"stage0_basin", "edge_trap", "fence_established"},
        "stage5": {"stage0_basin", "edge_trap", "fence_established", "drive_to_edge"},
        "stage6": {"stage0_basin", "drive_to_edge", "edge_trap", "fence_established"},
        "stage7": {"stage0_basin", "drive_to_edge", "edge_trap", "fence_established"},
    }
    return str(family) in allowed.get(stage, set())


def _select_rows(
    rows: list[dict[str, Any]], *, max_states: int | None, stage: str
) -> list[dict[str, Any]]:
    by_state: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        if row.get("source_stage") == stage and _allowed_family(stage, row.get("provider_family")):
            by_state[str(row.get("state_id"))].append(row)

    # Prefer states with multiple provider families, then known outcomes, then stable state id.
    ordered_states = sorted(
        by_state,
        key=lambda state: (
            -len({item.get("provider_family") for item in by_state[state]}),
            0 if any(item.get("frame_outcome") != "unknown" for item in by_state[state]) else 1,
            state,
        ),
    )
    if max_states is not None:
        ordered_states = ordered_states[:max_states]
    selected = []
    for state in ordered_states:
        seen_families = set()
        for row in sorted(
            by_state[state],
            key=lambda item: (
                int(item.get("global_raw_score_rank") or 999),
                str(item.get("provider_id")),
            ),
        ):
            family = row.get("provider_family")
            if family in seen_families:
                continue
            seen_families.add(family)
            selected.append(row)
    return selected


def build_manifest() -> dict[str, Any]:
    plan = _load_json(PLAN)
    ranked = _load_json(RANKED_FRAMES)
    if plan.get("causal_status") != "non_causal_label_plan":
        raise ValueError("diverse contrast plan must remain non-causal")
    if ranked.get("causal_status") != "non_causal_ranked_frame_dataset":
        raise ValueError("ranked frames must remain non-causal")

    rows = list(ranked.get("rows") or [])
    budget = int((plan.get("label_budget") or {}).get("max_forced_provider_labels") or 24)
    target_states_by_stage = {
        str(item.get("stratum_id") or ""): int(item.get("target_state_count") or 0)
        for item in plan.get("strata") or []
    }
    selected: list[dict[str, Any]] = []
    # Stage 4 wrong-tempo labels can be much slower than the other strata in
    # the forced-provider harness because the diagnostic stratum label maps to
    # edge_trap_wrong_tempo reward evaluation. Keep this first diverse slice
    # bounded by deferring Stage 4 until a targeted runner exists.
    deferred_stages = {"stage4"}
    for stage in ("stage4", "stage5", "stage6"):
        if stage in deferred_stages:
            continue
        target = target_states_by_stage.get(_stage_stratum(stage)) or None
        selected.extend(_select_rows(rows, max_states=target, stage=stage))
    selected = selected[:budget]
    if len(selected) < budget:
        target = target_states_by_stage.get(_stage_stratum("stage7")) or 2
        selected.extend(_select_rows(rows, max_states=target, stage="stage7")[: budget - len(selected)])

    jobs = []
    seen_jobs = set()
    for row in selected[:budget]:
        provider_id = str(row.get("provider_id") or "")
        move_uci = str(row.get("move_uci") or "")
        state_id = str(row.get("state_id") or "")
        if not provider_id or not move_uci or not state_id:
            continue
        job_key = (state_id, provider_id, move_uci)
        if job_key in seen_jobs:
            continue
        seen_jobs.add(job_key)
        binding = _binding(provider_id)
        jobs.append({
            "schema_version": "krk_diverse_contrast_label_job.v1",
            "job_id": _job_id(state_id, provider_id, move_uci),
            "causal_status": "non_causal_label_job",
            "labels_generated": False,
            "runtime_behavior_changed": False,
            "frame_id": row.get("frame_id"),
            "state_id": state_id,
            "source_stage": row.get("source_stage"),
            "stratum_id": _stage_stratum(str(row.get("source_stage"))),
            "active_landmark_label": row.get("active_landmark_label"),
            "fen": row.get("fen"),
            "provider_id": provider_id,
            "provider_family": row.get("provider_family"),
            "provider_maturity": row.get("provider_maturity"),
            "provider_local_rank": row.get("provider_local_rank"),
            "normalized_score": row.get("normalized_score"),
            "global_raw_score_rank": row.get("global_raw_score_rank"),
            "move_uci": move_uci,
            "frame_outcome": row.get("frame_outcome"),
            "horizon": 40,
            "trace_mode": "failures_only",
            "diagnostic_caches_required": True,
            "stage7_challenge_row": bool(row.get("stage7_challenge_row")),
            "usable_for_training": not bool(row.get("stage7_challenge_row")),
            "target_label_semantics": "forced_provider_state_local_contrast",
            "execution_binding": binding,
        })

    missing_paths = []
    for job in jobs:
        binding = job["execution_binding"]
        for key in ("topology_path", "source_checkpoint"):
            path = ROOT / binding[key]
            if not path.exists():
                missing_paths.append(str(path))

    summary = {
        "job_count": len(jobs),
        "stage7_eval_only_job_count": sum(1 for job in jobs if job["stage7_challenge_row"]),
        "training_job_count": sum(1 for job in jobs if job["usable_for_training"]),
        "job_count_by_stage": dict(Counter(str(job["source_stage"]) for job in jobs)),
        "job_count_by_provider_family": dict(Counter(str(job["provider_family"]) for job in jobs)),
        "selected_state_count": len({job["state_id"] for job in jobs}),
        "missing_path_count": len(missing_paths),
        "missing_paths": sorted(set(missing_paths)),
        "all_bindings_valid": not missing_paths,
        "deferred_stages_due_to_runtime_risk": sorted(deferred_stages),
    }
    manifest = {
        "schema_version": "krk_diverse_contrast_execution_manifest.v1",
        "causal_status": "non_causal_execution_manifest",
        "runtime_behavior_changed": False,
        "runtime_defaults_changed": False,
        "runtime_arbiter_implemented": False,
        "runtime_terminals_added": False,
        "runtime_dtm_or_tablebase_lookup": False,
        "gameplay_topology_mutation": False,
        "labels_generated_in_this_slice": False,
        "stage7_promotion_allowed": False,
        "stage8_training_allowed": False,
        "source_artifacts": [str(PLAN), str(RANKED_FRAMES)],
        "binding_summary": summary,
        "jobs": jobs,
        "decision": {
            "status": "diverse_contrast_execution_manifest_ready" if not missing_paths else "missing_bindings",
            "recommended_next_step": (
                "run_diverse_contrast_labels_v1" if not missing_paths else "resolve_missing_bindings"
            ),
            "runtime_test_allowed_next": False,
            "stage7_promotion_allowed": False,
            "stage8_training_allowed": False,
        },
        "blocked_next_steps": [
            "runtime_selector",
            "stage7_repair",
            "stage7_promotion",
            "stage8_training",
            "runtime_dtm_or_tablebase",
            "gameplay_topology_mutation",
        ],
    }
    validate_manifest(manifest)
    return manifest


def validate_manifest(manifest: dict[str, Any]) -> None:
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
        if manifest.get(key) is not False:
            raise ValueError(f"{key} must be false")
    for job in manifest.get("jobs") or []:
        if job.get("causal_status") != "non_causal_label_job":
            raise ValueError("jobs must remain non-causal")
        if job.get("stage7_challenge_row") and job.get("usable_for_training"):
            raise ValueError("Stage7 jobs must be eval-only")


def render_markdown(manifest: dict[str, Any]) -> str:
    summary = manifest["binding_summary"]
    lines = [
        "# KRK Diverse Contrast Execution Manifest v1",
        "",
        "This non-causal manifest binds the bounded diverse contrast-label jobs. It does not run labels or change runtime behavior.",
        "",
        "## Summary",
        "",
    ]
    for key, value in summary.items():
        lines.append(f"- `{key}`: `{value}`")
    lines.extend(["", "## Jobs", ""])
    for job in manifest["jobs"]:
        lines.append(
            f"- `{job['job_id']}` stage=`{job['source_stage']}` stratum=`{job['stratum_id']}` "
            f"state=`{job['state_id']}` provider=`{job['provider_id']}` move=`{job['move_uci']}` "
            f"stage7_eval=`{job['stage7_challenge_row']}`"
        )
    lines.extend(
        [
            "",
            "## Decision",
            "",
            f"- Status: `{manifest['decision']['status']}`",
            f"- Recommended next step: `{manifest['decision']['recommended_next_step']}`",
            f"- Runtime test allowed next: `{manifest['decision']['runtime_test_allowed_next']}`",
            f"- Stage 7 promotion allowed: `{manifest['decision']['stage7_promotion_allowed']}`",
            f"- Stage 8 training allowed: `{manifest['decision']['stage8_training_allowed']}`",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> None:
    manifest = build_manifest()
    (ROOT / OUT_JSON).write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (ROOT / OUT_MD).write_text(render_markdown(manifest), encoding="utf-8")
    print(json.dumps(manifest["decision"], indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
