#!/usr/bin/env python3
"""Merge forced-provider control labels into a separate evidence artifact."""

from __future__ import annotations

import argparse
import copy
import json
from pathlib import Path
from typing import Any


FILTERED_FRAMES = Path("reports/krk_control_plane_filtered_frames_v0.json")
CONTROL_LABELS = Path("reports/krk_forced_provider_control_labels_v0.json")


def _load_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"expected JSON object: {path}")
    return payload


def build_augmented(repo_root: Path) -> dict[str, Any]:
    filtered = _load_json(repo_root / FILTERED_FRAMES)
    labels = _load_json(repo_root / CONTROL_LABELS)
    if filtered.get("causal_status") != "non_causal_filtered_frame_export":
        raise ValueError("filtered frames must remain non-causal")
    if labels.get("causal_status") != "non_causal_label_run":
        raise ValueError("control labels must remain non-causal")
    frames = copy.deepcopy(filtered.get("frames") or [])
    frame_by_id = {frame.get("frame_id"): frame for frame in frames if isinstance(frame, dict)}
    attached = 0
    missing = []
    for label in labels.get("labels") or []:
        frame = frame_by_id.get(label.get("frame_id"))
        if not frame:
            missing.append(label.get("job_id"))
            continue
        proposals = frame.setdefault("strategy_proposal_frames", [])
        match = None
        for proposal in proposals:
            if proposal.get("provider_id") == label.get("provider_id") and proposal.get("move_uci") == label.get("requested_reference_move"):
                match = proposal
                break
        if match is None:
            match = {
                "schema_version": "strategy_proposal_frame.v1",
                "causal_status": "non_causal",
                "provider_id": label.get("provider_id"),
                "skill_id": label.get("provider_id"),
                "move_uci": label.get("requested_reference_move"),
            }
            proposals.append(match)
        match["forced_control_outcome_label"] = {
            "schema_version": "krk_forced_provider_control_label_ref.v0",
            "causal_status": "non_causal_outcome_label",
            "job_id": label.get("job_id"),
            "source": "forced_provider_control_label",
            "result": label.get("result"),
            "plies": label.get("plies"),
            "horizon": label.get("horizon"),
            "forced_first_move": label.get("forced_first_move"),
            "forced_successor_available": label.get("forced_successor_available"),
            "topology_version": label.get("topology_version"),
            "composition_profile": label.get("composition_profile"),
        }
        attached += 1
    augmented = {
        **filtered,
        "schema_version": "krk_control_plane_filtered_frames_with_forced_controls.v0",
        "causal_status": "non_causal_augmented_frame_export",
        "runtime_behavior_changed": False,
        "runtime_defaults_changed": False,
        "runtime_arbiter_implemented": False,
        "runtime_terminals_added": False,
        "runtime_dtm_or_tablebase_lookup": False,
        "gameplay_topology_mutation": False,
        "stage7_promotion_allowed": False,
        "stage8_training_allowed": False,
        "source_artifacts": [str(FILTERED_FRAMES), str(CONTROL_LABELS)],
        "summary": {
            "frame_count": len(frames),
            "forced_control_labels_attached": attached,
            "missing_label_job_ids": missing,
        },
        "frames": frames,
    }
    return augmented


def render_markdown(payload: dict[str, Any]) -> str:
    summary = payload["summary"]
    return "\n".join(
        [
            "# KRK Control Plane Frames With Forced Controls v0",
            "",
            "This replay-free artifact attaches forced-provider control labels to a copy of the filtered frames. It does not change the source filtered frames or runtime behavior.",
            "",
            f"- Frame count: `{summary['frame_count']}`",
            f"- Forced control labels attached: `{summary['forced_control_labels_attached']}`",
            f"- Missing label job IDs: `{summary['missing_label_job_ids']}`",
            "",
        ]
    )


def write_outputs(payload: dict[str, Any], report_root: Path) -> None:
    report_root.mkdir(parents=True, exist_ok=True)
    (report_root / "krk_control_plane_filtered_frames_with_forced_controls_v0.json").write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    (report_root / "krk_control_plane_filtered_frames_with_forced_controls_v0.md").write_text(
        render_markdown(payload), encoding="utf-8"
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=Path("."))
    parser.add_argument("--report-root", type=Path, default=Path("reports"))
    args = parser.parse_args()
    repo_root = args.repo_root.resolve()
    report_root = args.report_root
    if not report_root.is_absolute():
        report_root = repo_root / report_root
    payload = build_augmented(repo_root)
    write_outputs(payload, report_root)
    print(json.dumps(payload["summary"], indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
