#!/usr/bin/env python3
"""Replay-free scan for protected selected-provider diversity evidence."""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
PLAN = Path("reports/krk_selected_provider_diversity_evidence_plan_v0.json")
FRAMES = Path("reports/krk_control_plane_filtered_frames_with_forced_controls_v0.json")
BALANCED = Path("reports/krk_selector_balanced_label_dataset_v1.json")
OUT_JSON = Path("reports/krk_selected_provider_diversity_replay_free_scan_v0.json")
OUT_MD = Path("reports/krk_selected_provider_diversity_replay_free_scan_v0.md")


def _load_json(path: Path) -> dict[str, Any]:
    payload = json.loads((ROOT / path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"expected JSON object: {path}")
    return payload


def _provider_family(provider_id: str) -> str:
    if provider_id.startswith("krk.edge_trap"):
        return "edge_trap"
    if provider_id == "krk.stage0_basin":
        return "stage0_basin"
    return provider_id.removeprefix("krk.")


def _label_result(label: dict[str, Any]) -> str:
    value = label.get("result") or label.get("playout_result") or label.get("label")
    return str(value) if value else "unknown"


def build_scan() -> dict[str, Any]:
    plan = _load_json(PLAN)
    frames = _load_json(FRAMES)
    balanced = _load_json(BALANCED)
    if plan.get("causal_status") != "non_causal_design_plan":
        raise ValueError("plan must remain non-causal")
    if frames.get("causal_status") != "non_causal_augmented_frame_export":
        raise ValueError("frames must remain non-causal")
    if balanced.get("causal_status") != "non_causal_balanced_label_dataset":
        raise ValueError("balanced labels must remain non-causal")

    selected_records: list[dict[str, Any]] = []
    seen: set[tuple[str, str, str]] = set()
    for frame in frames.get("frames") or []:
        stage = str(frame.get("source_stage") or "")
        if stage not in {"stage4", "stage5", "stage6"}:
            continue
        for proposal in frame.get("strategy_proposal_frames") or []:
            label = proposal.get("known_outcome_label") or {}
            if not isinstance(label, dict) or label.get("selected") is not True:
                continue
            provider_id = str(proposal.get("provider_id") or "")
            state_id = str(frame.get("state_id") or "")
            key = (state_id, provider_id, "frame_selected")
            if not provider_id or key in seen:
                continue
            seen.add(key)
            selected_records.append(
                {
                    "schema_version": "krk_selected_provider_record.v0",
                    "causal_status": "non_causal_selected_provider_evidence",
                    "state_id": state_id,
                    "source_stage": stage,
                    "active_landmark_label": frame.get("active_landmark_label"),
                    "provider_id": provider_id,
                    "provider_family": _provider_family(provider_id),
                    "move_uci": proposal.get("move_uci"),
                    "result": _label_result(label),
                    "source_artifact": str(FRAMES),
                }
            )
    for row in balanced.get("rows") or []:
        stage = str(row.get("source_stage") or "")
        target_kind = str(row.get("target_kind") or "")
        if stage not in {"stage4", "stage5", "stage6"} or target_kind != "guardrail_safe_selected_playout":
            continue
        provider_id = str(row.get("provider_id") or "")
        state_id = str(row.get("state_id") or "")
        key = (state_id, provider_id, "balanced_selected")
        if not provider_id or key in seen:
            continue
        seen.add(key)
        selected_records.append(
            {
                "schema_version": "krk_selected_provider_record.v0",
                "causal_status": "non_causal_selected_provider_evidence",
                "state_id": state_id,
                "source_stage": stage,
                "active_landmark_label": row.get("active_landmark_label"),
                "provider_id": provider_id,
                "provider_family": _provider_family(provider_id),
                "move_uci": row.get("move_uci"),
                "result": row.get("label"),
                "source_artifact": str(BALANCED),
            }
        )

    family_counts = Counter(record["provider_family"] for record in selected_records)
    stage_counts = Counter(record["source_stage"] for record in selected_records)
    result_counts = Counter(record["result"] for record in selected_records)
    total = len(selected_records)
    max_dominance = max(family_counts.values()) / total if total else 1.0
    distinct_families = len(family_counts)
    satisfied = distinct_families >= 3 and max_dominance <= 0.7
    scan = {
        "schema_version": "krk_selected_provider_diversity_replay_free_scan.v0",
        "causal_status": "non_causal_scan",
        "runtime_behavior_changed": False,
        "runtime_defaults_changed": False,
        "runtime_arbiter_implemented": False,
        "runtime_terminals_added": False,
        "runtime_dtm_or_tablebase_lookup": False,
        "gameplay_topology_mutation": False,
        "labels_generated_in_this_slice": False,
        "stage7_promotion_allowed": False,
        "stage8_training_allowed": False,
        "source_artifacts": [str(PLAN), str(FRAMES), str(BALANCED)],
        "summary": {
            "selected_record_count": total,
            "selected_provider_family_counts": dict(sorted(family_counts.items())),
            "selected_stage_counts": dict(sorted(stage_counts.items())),
            "selected_result_counts": dict(sorted(result_counts.items())),
            "distinct_selected_provider_families": distinct_families,
            "max_selected_provider_family_dominance": round(max_dominance, 4),
            "stage7_records": 0,
        },
        "records": selected_records,
        "decision": {
            "status": (
                "selected_provider_diversity_replay_free_satisfied"
                if satisfied
                else "selected_provider_diversity_replay_free_insufficient"
            ),
            "runtime_arbiter_allowed": False,
            "selector_sandbox_ready": False,
            "recommended_next_step": (
                "architecture_review_before_selector_sandbox"
                if satisfied
                else "design_bounded_protected_sampling_manifest_for_selected_provider_diversity"
            ),
        },
        "blocked_next_steps": [
            "runtime_arbiter",
            "selector_sandbox",
            "stage7_repair",
            "stage7_promotion",
            "stage8_training",
            "runtime_dtm_or_tablebase",
            "gameplay_topology_mutation",
        ],
    }
    validate_scan(scan)
    return scan


def validate_scan(scan: dict[str, Any]) -> None:
    if scan.get("causal_status") != "non_causal_scan":
        raise ValueError("scan must remain non-causal")
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
        if scan.get(key) is not False:
            raise ValueError(f"{key} must be false")
    if scan["summary"]["stage7_records"] != 0:
        raise ValueError("Stage 7 records must remain excluded")


def render_markdown(scan: dict[str, Any]) -> str:
    summary = scan["summary"]
    lines = [
        "# KRK Selected Provider Diversity Replay-Free Scan v0",
        "",
        "This scan uses existing protected artifacts only. It does not run labels, "
        "sample new states, implement a selector, promote Stage 7, or train Stage 8.",
        "",
        "## Summary",
        "",
        f"- Selected records: `{summary['selected_record_count']}`",
        f"- Provider family counts: `{summary['selected_provider_family_counts']}`",
        f"- Stage counts: `{summary['selected_stage_counts']}`",
        f"- Result counts: `{summary['selected_result_counts']}`",
        f"- Distinct selected provider families: `{summary['distinct_selected_provider_families']}`",
        f"- Max selected provider family dominance: `{summary['max_selected_provider_family_dominance']}`",
        f"- Stage 7 records: `{summary['stage7_records']}`",
        "",
        "## Decision",
        "",
        f"- Status: `{scan['decision']['status']}`",
        f"- Recommended next step: `{scan['decision']['recommended_next_step']}`",
        "- Runtime arbiter and selector sandbox remain blocked.",
        "",
    ]
    return "\n".join(lines)


def main() -> None:
    scan = build_scan()
    (ROOT / OUT_JSON).write_text(json.dumps(scan, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (ROOT / OUT_MD).write_text(render_markdown(scan), encoding="utf-8")
    print(json.dumps(scan["summary"], indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
