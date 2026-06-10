#!/usr/bin/env python3
"""Recover replay-free successful Stage 7 post-box sequence controls."""

from __future__ import annotations

import json
import hashlib
from collections import Counter
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DATASET_V0 = Path("reports/structural_candidates/stage7_selected_path_target_dataset_v0.json")
OUT_CONTROLS_JSON = Path("reports/structural_candidates/stage7_post_box_sequence_control_recovery_v0.json")
OUT_CONTROLS_MD = Path("reports/structural_candidates/stage7_post_box_sequence_control_recovery_v0.md")
OUT_DATASET_JSON = Path("reports/structural_candidates/stage7_selected_path_target_dataset_v1.json")
OUT_DATASET_MD = Path("reports/structural_candidates/stage7_selected_path_target_dataset_v1.md")


def _load(path: Path) -> dict[str, Any]:
    payload = json.loads((ROOT / path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"expected JSON object: {path}")
    return payload


def _stage7_artifact_paths() -> list[Path]:
    root = ROOT / "reports/structural_candidates"
    return sorted(
        path for path in root.glob("stage7*.json")
        if "stage8" not in path.name.lower()
    )


def _recover_controls(limit: int = 16) -> list[dict[str, Any]]:
    controls = []
    seen: set[tuple[str, str, int]] = set()
    for path in _stage7_artifact_paths():
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            continue
        for packet in payload.get("handoff_packets") or []:
            if not isinstance(packet, dict):
                continue
            terms = packet.get("evidence_terms") or {}
            if packet.get("phase") != "playout_summary":
                continue
            if terms.get("label") != "box_shrink" or terms.get("playout_result") != "mate":
                continue
            plies = terms.get("plies")
            if not isinstance(plies, int) or plies <= 1 or plies > 40:
                continue
            fen = terms.get("fen")
            move = terms.get("move")
            if not fen or not move:
                continue
            key = (str(fen), str(move), int(plies))
            if key in seen:
                continue
            seen.add(key)
            state_digest = hashlib.sha1("|".join(str(item) for item in key).encode("utf-8")).hexdigest()[:12]
            controls.append({
                "schema_version": "stage7_post_box_sequence_control.v0",
                "state_id": f"recovered.{state_digest}",
                "fen": fen,
                "move_uci": move,
                "plies": plies,
                "semantic_alignment_status": terms.get("semantic_alignment_status"),
                "failure_classes": terms.get("failure_classes") or [],
                "source_artifact": str(path.relative_to(ROOT)),
                "source_phase": packet.get("phase"),
                "source_status": packet.get("status"),
                "source_observed_outcome": packet.get("observed_outcome"),
                "control_quality": "sandbox_sourced_replay_free_success_control",
                "causal_status": "non_causal_replay_free_label",
            })
            if len(controls) >= limit:
                return controls
    return controls


def build_recovery() -> dict[str, Any]:
    controls = _recover_controls()
    return {
        "schema_version": "stage7_post_box_sequence_control_recovery.v0",
        "causal_status": "non_causal_replay_free_recovery",
        "runtime_behavior_changed": False,
        "runtime_defaults_changed": False,
        "runtime_selector_implemented": False,
        "runtime_score_changes": False,
        "runtime_direct_routing": False,
        "runtime_dtm_or_tablebase_lookup": False,
        "hidden_python_controller": False,
        "gameplay_topology_mutation": False,
        "stage7_promotion_allowed": False,
        "stage8_training_allowed": False,
        "controls": controls,
        "summary": {
            "control_count": len(controls),
            "source_artifact_counts": dict(Counter(row["source_artifact"] for row in controls)),
            "plies_counts": dict(Counter(str(row["plies"]) for row in controls)),
            "semantic_alignment_counts": dict(Counter(str(row.get("semantic_alignment_status")) for row in controls)),
            "usable_for_offline_benchmark": len(controls) >= 2,
            "usable_for_runtime_authorization": False,
            "caveat": "controls are recovered from prior Stage 7 sandbox artifacts and must be held out from runtime authorization claims",
        },
    }


def build_dataset_v1(recovery: dict[str, Any]) -> dict[str, Any]:
    base = _load(DATASET_V0)
    rows = list(base.get("rows") or [])
    for control in recovery.get("controls") or []:
        rows.append({
            "schema_version": "stage7_selected_path_target_row.v1",
            "target_id": "stage7.selected_path.sequence_continuation_gap.v0",
            "row_role": "stage7_sequence_success_control_recovered",
            "state_id": control.get("state_id"),
            "source_stage": "stage7",
            "active_landmark_label": "box_shrink",
            "selected_provider": "unknown_recovered_success_path",
            "selected_provider_family": "unknown_recovered_success_path",
            "selected_move": control.get("move_uci"),
            "target_provider": "unknown_recovered_success_path",
            "outcome": "mate",
            "label": "sequence_continuation_success_recovered",
            "features": {
                "plies_to_mate": control.get("plies"),
                "semantic_alignment_status": control.get("semantic_alignment_status"),
                "control_quality": control.get("control_quality"),
                "source_artifact": control.get("source_artifact"),
            },
            "causal_status": "non_causal_replay_free_label",
        })
    role_counts = Counter(row["row_role"] for row in rows)
    target_counts = Counter(row["target_id"] for row in rows)
    sequence_controls = role_counts.get("stage7_sequence_success_control_recovered", 0)
    payload = {
        **base,
        "schema_version": "stage7_selected_path_target_dataset.v1",
        "source_artifacts": list(base.get("source_artifacts") or []) + [str(OUT_CONTROLS_JSON)],
        "rows": rows,
        "summary": {
            "row_count": len(rows),
            "target_counts": dict(target_counts),
            "row_role_counts": dict(role_counts),
            "ownership_target_minimally_trainable": base["summary"]["ownership_target_minimally_trainable"],
            "sequence_target_minimally_trainable": sequence_controls >= 2,
            "benchmark_underpowered": False if sequence_controls >= 2 else True,
            "sequence_controls_recovered": sequence_controls,
            "sequence_control_caveat": "sandbox_sourced_controls_offline_only",
        },
        "decision": {
            "status": (
                "split_target_dataset_ready_for_offline_probe_with_sandbox_sourced_sequence_controls"
                if sequence_controls >= 2
                else "sequence_target_underpowered"
            ),
            "recommended_next_step": "run_non_causal_split_target_probe_only",
            "blocked_runtime_work": [
                "runtime arbiter",
                "abstention penalty tuning",
                "Stage 7 promotion",
                "Stage 8 training",
                "causal internal terminals",
            ],
        },
    }
    return payload


def _render_recovery_md(payload: dict[str, Any]) -> str:
    lines = [
        "# Stage 7 Post-Box Sequence Control Recovery v0",
        "",
        f"Recovered controls: `{payload['summary']['control_count']}`",
        "",
        "These controls are replay-free labels from existing Stage 7 sandbox artifacts. They are usable for offline benchmark construction only, not runtime authorization.",
        "",
        "## Source Artifacts",
        "",
    ]
    for source, count in payload["summary"]["source_artifact_counts"].items():
        lines.append(f"- `{source}`: `{count}`")
    lines.extend(["", "## Caveat", "", payload["summary"]["caveat"], ""])
    return "\n".join(lines)


def _render_dataset_md(payload: dict[str, Any]) -> str:
    lines = [
        "# Stage 7 Selected Path Target Dataset v1",
        "",
        f"Status: `{payload['decision']['status']}`",
        "",
        "The v1 dataset adds replay-free successful post-box sequence controls recovered from prior Stage 7 sandbox artifacts. These controls are offline-only and do not authorize runtime behavior.",
        "",
        "## Summary",
        "",
    ]
    for key, value in payload["summary"].items():
        lines.append(f"- {key}: `{value}`")
    lines.extend([
        "",
        f"Recommended next step: `{payload['decision']['recommended_next_step']}`",
        "",
        "Blocked runtime work:",
        "",
    ])
    for item in payload["decision"]["blocked_runtime_work"]:
        lines.append(f"- `{item}`")
    lines.append("")
    return "\n".join(lines)


def main() -> None:
    recovery = build_recovery()
    dataset = build_dataset_v1(recovery)
    (ROOT / OUT_CONTROLS_JSON).write_text(json.dumps(recovery, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (ROOT / OUT_CONTROLS_MD).write_text(_render_recovery_md(recovery), encoding="utf-8")
    (ROOT / OUT_DATASET_JSON).write_text(json.dumps(dataset, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (ROOT / OUT_DATASET_MD).write_text(_render_dataset_md(dataset), encoding="utf-8")


if __name__ == "__main__":
    main()
