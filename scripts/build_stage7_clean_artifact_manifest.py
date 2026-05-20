#!/usr/bin/env python3
"""Classify Stage 7 artifacts for clean-control recovery."""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
PLAN = Path("reports/structural_candidates/stage7_clean_control_collection_plan_v0.json")
OUT_JSON = Path("reports/structural_candidates/stage7_clean_artifact_manifest_v0.json")
OUT_MD = Path("reports/structural_candidates/stage7_clean_artifact_manifest_v0.md")

GENERATED_ARTIFACT_NAMES = {
    OUT_JSON.name,
    "stage7_clean_sequence_control_recovery_v0.json",
}


REPAIR_NAME_MARKERS = (
    "adapter",
    "support",
    "king_tempo",
    "drive_repair",
    "candidate_move_layer",
    "plan_capsule",
    "plan_capsule_enabled",
    "plan_capsule_owned",
    "post_king_tempo",
    "post_box_on",
    "learned_overlay",
    "frozen_model",
    "repair",
    "sandbox",
)


def _load_json(path: Path) -> dict[str, Any] | None:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None
    return payload if isinstance(payload, dict) else None


def _bool_enabled_flags(payload: dict[str, Any]) -> list[str]:
    flags = []
    for key, value in payload.items():
        if not isinstance(value, bool) or value is not True:
            continue
        lower = key.lower()
        if lower in {"diagnostic_caches_enabled"}:
            continue
        # Handoff composition v1 uses successor/stagnation/post-break mechanics as
        # protected baseline behavior; they are not by themselves Stage 7 repairs.
        if lower.startswith(("successor_", "stagnation_", "post_break_")):
            continue
        if lower.endswith("_enabled") or lower.startswith("enable_") or "sandbox" in lower:
            flags.append(key)
    return sorted(flags)


def _positive_support_fields(payload: dict[str, Any]) -> list[str]:
    fields = []
    for key, value in payload.items():
        lower = key.lower()
        if (
            lower.endswith("_count")
            or lower.endswith("_counts")
            or "count_by" in lower
            or "by_outcome" in lower
            or "selected_by" in lower
        ):
            continue
        if lower.startswith(("successor_", "stagnation_", "post_break_")):
            continue
        if not any(marker in lower for marker in ("support", "bonus", "penalty")):
            continue
        if isinstance(value, (int, float)) and value > 0:
            fields.append(key)
    return sorted(fields)


def _runtime_test_activity_fields(payload: dict[str, Any]) -> list[str]:
    fields = []
    runtime_markers = (
        "krk_two_stage_abstention",
        "krk_strategy_arbiter_sandbox",
        "candidate_move_role",
        "plan_capsule",
        "stage7_post_box_frozen_model_candidate",
    )
    activity_markers = (
        "supported_suggestion_count",
        "selected_supported_count",
        "penalized_count",
        "selected_penalized_count",
    )
    for key, value in payload.items():
        lower = key.lower()
        if not any(marker in lower for marker in runtime_markers):
            continue
        if not any(marker in lower for marker in activity_markers):
            continue
        if isinstance(value, bool):
            continue
        if isinstance(value, (int, float)) and value > 0:
            fields.append(key)
    return sorted(fields)


def _label(payload: dict[str, Any]) -> str | None:
    value = payload.get("label")
    return str(value) if value is not None else None


def _has_box_handoff_packets(payload: dict[str, Any]) -> bool:
    for packet in payload.get("handoff_packets") or []:
        if not isinstance(packet, dict):
            continue
        terms = packet.get("evidence_terms") or {}
        if terms.get("label") == "box_shrink":
            return True
    return False


def _has_outcome_payload(payload: dict[str, Any]) -> bool:
    return isinstance(payload.get("playouts"), dict) or bool(payload.get("handoff_packets"))


def _classify(path: Path, payload: dict[str, Any]) -> dict[str, Any]:
    name = path.name.lower()
    enabled_flags = _bool_enabled_flags(payload)
    positive_support = _positive_support_fields(payload)
    runtime_activity = _runtime_test_activity_fields(payload)
    marker_hits = [marker for marker in REPAIR_NAME_MARKERS if marker in name]
    explicit_runtime_enabled_name = "abstention_stage7_enabled" in name
    has_default_off_marker = "default_off" in name or "baseline" in name
    label = _label(payload)
    has_box_context = label == "box_shrink" or _has_box_handoff_packets(payload) or "stage7" in name
    has_outcomes = _has_outcome_payload(payload)

    has_stage7_repair_flags = any(flag.lower().startswith("stage7_") for flag in enabled_flags)
    has_current_profile_baseline_marker = has_default_off_marker and not has_stage7_repair_flags

    if not has_outcomes:
        classification = "metadata_or_design_only"
    elif has_current_profile_baseline_marker and has_box_context and not marker_hits:
        classification = "clean_current_profile_candidate"
    elif (
        enabled_flags
        or positive_support
        or runtime_activity
        or explicit_runtime_enabled_name
        or (marker_hits and not has_default_off_marker)
    ):
        classification = "repair_sandbox_sourced"
    elif has_default_off_marker and has_box_context:
        classification = "clean_default_off_candidate"
    elif label == "box_shrink" and not marker_hits:
        classification = "clean_baseline_candidate"
    else:
        classification = "ambiguous_needs_manual_review"

    return {
        "artifact": str(path.relative_to(ROOT)),
        "classification": classification,
        "label": label,
        "has_box_context": has_box_context,
        "has_outcomes": has_outcomes,
        "playouts": payload.get("playouts"),
        "total": payload.get("total"),
        "enabled_flags": enabled_flags,
        "positive_support_or_bonus_fields": positive_support,
        "runtime_test_activity_fields": runtime_activity,
        "filename_repair_markers": marker_hits,
        "explicit_runtime_enabled_name": explicit_runtime_enabled_name,
        "default_off_or_baseline_marker": has_default_off_marker,
        "candidate_for_clean_control_recovery": classification in {
            "clean_default_off_candidate",
            "clean_baseline_candidate",
            "clean_current_profile_candidate",
        },
    }


def build_manifest() -> dict[str, Any]:
    # Ensure the plan exists and is parseable before producing a manifest.
    _load_json(ROOT / PLAN)
    rows = []
    candidate_paths = [
        *sorted((ROOT / "reports").glob("*stage7*.json")),
        *sorted((ROOT / "reports/structural_candidates").glob("stage7*.json")),
    ]
    seen_paths: set[Path] = set()
    for path in candidate_paths:
        if path in seen_paths:
            continue
        seen_paths.add(path)
        if path.name in GENERATED_ARTIFACT_NAMES:
            continue
        if "stage8" in path.name.lower():
            continue
        payload = _load_json(path)
        if payload is None:
            continue
        rows.append(_classify(path, payload))
    counts = Counter(row["classification"] for row in rows)
    clean_count = sum(1 for row in rows if row["candidate_for_clean_control_recovery"])
    status = "clean_artifact_manifest_ready" if clean_count else "no_clean_replay_free_artifacts_found"
    next_step = (
        "recover_clean_sequence_controls_from_manifest_candidates"
        if clean_count
        else "bounded_clean_h40_label_job_or_architecture_review"
    )
    return {
        "schema_version": "stage7_clean_artifact_manifest.v0",
        "causal_status": "non_causal_replay_free_manifest",
        "runtime_behavior_changed": False,
        "runtime_defaults_changed": False,
        "runtime_selector_implemented": False,
        "runtime_dtm_or_tablebase_lookup": False,
        "gameplay_topology_mutation": False,
        "stage7_promotion_allowed": False,
        "stage8_training_allowed": False,
        "source_artifacts": [str(PLAN)],
        "rows": rows,
        "summary": {
            "artifact_count": len(rows),
            "classification_counts": dict(counts),
            "clean_candidate_count": clean_count,
            "repair_sandbox_sourced_count": counts.get("repair_sandbox_sourced", 0),
            "ambiguous_count": counts.get("ambiguous_needs_manual_review", 0),
        },
        "decision": {
            "status": status,
            "recommended_next_step": next_step,
            "runtime_work_allowed": False,
        },
    }


def render_markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# Stage 7 Clean Artifact Manifest v0",
        "",
        f"Status: `{payload['decision']['status']}`",
        "",
        "Replay-free classification of existing Stage 7 artifacts for clean-control recovery.",
        "",
        "## Summary",
        "",
    ]
    for key, value in payload["summary"].items():
        lines.append(f"- {key}: `{value}`")
    lines.extend(["", "## Clean Candidates", ""])
    for row in payload["rows"]:
        if row["candidate_for_clean_control_recovery"]:
            lines.append(f"- `{row['artifact']}`: `{row['classification']}`, playouts=`{row.get('playouts')}`")
    lines.extend(["", "## Ambiguous", ""])
    for row in payload["rows"]:
        if row["classification"] == "ambiguous_needs_manual_review":
            lines.append(f"- `{row['artifact']}`")
    lines.extend(["", f"Next step: `{payload['decision']['recommended_next_step']}`", ""])
    return "\n".join(lines)


def main() -> None:
    payload = build_manifest()
    (ROOT / OUT_JSON).write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (ROOT / OUT_MD).write_text(render_markdown(payload), encoding="utf-8")


if __name__ == "__main__":
    main()
