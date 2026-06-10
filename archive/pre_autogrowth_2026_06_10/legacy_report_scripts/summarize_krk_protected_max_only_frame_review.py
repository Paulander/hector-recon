#!/usr/bin/env python3
"""Review protected strategy frames with no labeled converting provider."""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
FILTERED = Path("reports/krk_control_plane_filtered_frames_v0.json")
BASELINE = Path("reports/krk_control_plane_strategy_arbitration_baseline_v1.json")
OUT_JSON = Path("reports/krk_protected_max_only_frame_review_v0.json")
OUT_MD = Path("reports/krk_protected_max_only_frame_review_v0.md")


def _load(path: Path) -> dict[str, Any]:
    payload = json.loads((ROOT / path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"expected JSON object: {path}")
    return payload


def _proposal_result(proposal: dict[str, Any]) -> str:
    label = proposal.get("known_outcome_label") or {}
    if not isinstance(label, dict):
        return "unknown"
    result = label.get("result") or label.get("playout_result")
    return str(result) if result in {"mate", "max_plies", "draw", "stagnation"} else "unknown"


def build_review() -> dict[str, Any]:
    filtered = _load(FILTERED)
    baseline = _load(BASELINE)
    frames = [
        frame
        for frame in filtered.get("frames") or []
        if "strategy_arbitration_benchmark" in (frame.get("filter_metadata") or {}).get("benchmark_roles", [])
    ]
    max_only = []
    mate_available = []
    for frame in frames:
        labels = [_proposal_result(proposal) for proposal in frame.get("strategy_proposal_frames") or []]
        known = [label for label in labels if label in {"mate", "max_plies"}]
        if "mate" in known:
            mate_available.append(frame)
        elif known and all(label == "max_plies" for label in known):
            provider_counts = Counter(
                str(proposal.get("provider_id") or "unknown")
                for proposal in frame.get("strategy_proposal_frames") or []
                if _proposal_result(proposal) == "max_plies"
            )
            max_only.append(
                {
                    "frame_id": frame.get("frame_id"),
                    "state_id": frame.get("state_id"),
                    "source_stage": frame.get("source_stage"),
                    "active_landmark_label": frame.get("active_landmark_label"),
                    "outcome": frame.get("outcome"),
                    "max_only_provider_counts": dict(provider_counts),
                    "proposal_count": len(frame.get("strategy_proposal_frames") or []),
                    "fen": frame.get("fen"),
                }
            )
    by_stage = Counter(str(row.get("source_stage")) for row in max_only)
    provider_counts = Counter()
    for row in max_only:
        provider_counts.update(row["max_only_provider_counts"])
    return {
        "schema_version": "krk_protected_max_only_frame_review.v0",
        "causal_status": "non_causal_artifact_review",
        "runtime_behavior_changed": False,
        "runtime_defaults_changed": False,
        "runtime_selector_implemented": False,
        "runtime_dtm_or_tablebase_lookup": False,
        "gameplay_topology_mutation": False,
        "stage7_promotion_allowed": False,
        "stage8_training_allowed": False,
        "source_artifacts": [str(FILTERED), str(BASELINE)],
        "summary": {
            "strategy_benchmark_frame_count": len(frames),
            "frames_with_labeled_mate_provider": len(mate_available),
            "frames_with_only_labeled_max_plies_providers": len(max_only),
            "max_only_by_stage": dict(by_stage),
            "max_only_provider_counts": dict(provider_counts),
            "baseline_selected_status": (baseline.get("decision") or {}).get("selected_status"),
            "runtime_work_allowed": False,
        },
        "max_only_frames": max_only,
        "interpretation": [
            "The protected strategy selector can only choose among materialized/labeled provider proposals.",
            "Current selectors recover mate when a labeled converting provider is present, but half of protected benchmark frames have no labeled mate provider.",
            "This makes the next broader bottleneck a missing-provider / continuation-capacity / label-coverage problem, not a selector-score problem.",
        ],
        "decision": {
            "status": "protected_max_only_frames_block_runtime_selector",
            "recommended_next_step": "define_protected_missing_provider_capacity_audit",
            "runtime_work_allowed": False,
        },
    }


def render_markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# KRK Protected Max-Only Frame Review v0",
        "",
        f"Status: `{payload['decision']['status']}`",
        "",
        "Replay-free review of protected strategy-arbitration frames that have no labeled converting provider proposal.",
        "",
        "## Summary",
        "",
    ]
    for key, value in payload["summary"].items():
        lines.append(f"- {key}: `{value}`")
    lines.extend(["", "## Interpretation", ""])
    for item in payload["interpretation"]:
        lines.append(f"- {item}")
    lines.extend(["", "## Max-Only Frames", ""])
    for row in payload["max_only_frames"]:
        lines.append(
            f"- `{row['frame_id']}` stage=`{row['source_stage']}` label=`{row['active_landmark_label']}` "
            f"providers=`{row['max_only_provider_counts']}`"
        )
    lines.extend(["", f"Recommended next step: `{payload['decision']['recommended_next_step']}`", ""])
    return "\n".join(lines)


def main() -> None:
    payload = build_review()
    (ROOT / OUT_JSON).write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (ROOT / OUT_MD).write_text(render_markdown(payload), encoding="utf-8")


if __name__ == "__main__":
    main()
