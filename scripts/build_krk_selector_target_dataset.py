#!/usr/bin/env python3
"""Build replay-free KRK selector target dataset with explicit target kinds."""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
FRAMES = Path("reports/krk_control_plane_filtered_frames_with_forced_controls_v0.json")
SEMANTICS = Path("reports/krk_selector_objective_label_semantics_v0.json")
OUT_JSON = Path("reports/krk_selector_target_dataset_v0.json")
OUT_MD = Path("reports/krk_selector_target_dataset_v0.md")


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


def _label_from_result(result: str | None) -> str | None:
    if result == "mate":
        return "positive"
    if result in {"max_plies", "draw", "no_move", "illegal_move"}:
        return "negative"
    return None


def build_dataset(root: Path = ROOT) -> dict[str, Any]:
    frames_payload = _load_json(FRAMES)
    semantics = _load_json(SEMANTICS)
    rows: list[dict[str, Any]] = []
    for frame in frames_payload.get("frames", []) or []:
        state_id = str(frame.get("state_id") or "")
        source_stage = str(frame.get("source_stage") or "unknown")
        if source_stage == "stage7":
            rows.append({
                "schema_version": "krk_selector_target_example.v0",
                "causal_status": "non_causal_target_label",
                "target_kind": "held_out_challenge",
                "split": "held_out_challenge",
                "state_id": state_id,
                "frame_id": frame.get("frame_id"),
                "source_stage": source_stage,
                "active_landmark_label": frame.get("active_landmark_label"),
                "fen": frame.get("fen"),
                "provider_id": None,
                "move_uci": None,
                "label": None,
                "label_source": "stage7_challenge_status",
                "usable_for_training": False,
            })
            continue
        for proposal in frame.get("strategy_proposal_frames", []) or []:
            if not isinstance(proposal, dict):
                continue
            provider = proposal.get("provider_id") or proposal.get("skill_id")
            move = proposal.get("move_uci")
            known = proposal.get("known_outcome_label")
            if isinstance(known, dict):
                label = _label_from_result(known.get("playout_result"))
                if label:
                    rows.append({
                        "schema_version": "krk_selector_target_example.v0",
                        "causal_status": "non_causal_target_label",
                        "target_kind": "selected_playout_success",
                        "split": "candidate_training_or_eval",
                        "state_id": state_id,
                        "frame_id": frame.get("frame_id"),
                        "source_stage": source_stage,
                        "active_landmark_label": frame.get("active_landmark_label"),
                        "fen": frame.get("fen"),
                        "provider_id": provider,
                        "move_uci": move,
                        "label": label,
                        "raw_result": known.get("playout_result"),
                        "plies": known.get("plies"),
                        "selected": bool(known.get("selected", False)),
                        "label_source": "known_outcome_label.playout_result",
                        "usable_for_training": True,
                    })
            forced = proposal.get("forced_control_outcome_label")
            if isinstance(forced, dict):
                label = _label_from_result(forced.get("result"))
                if label:
                    rows.append({
                        "schema_version": "krk_selector_target_example.v0",
                        "causal_status": "non_causal_target_label",
                        "target_kind": "forced_provider_conversion",
                        "split": "diagnostic_capacity_only",
                        "state_id": state_id,
                        "frame_id": frame.get("frame_id"),
                        "source_stage": source_stage,
                        "active_landmark_label": frame.get("active_landmark_label"),
                        "fen": frame.get("fen"),
                        "provider_id": provider,
                        "move_uci": move,
                        "label": label,
                        "raw_result": forced.get("result"),
                        "plies": forced.get("plies"),
                        "selected": None,
                        "label_source": "forced_control_outcome_label.result",
                        "usable_for_training": False,
                    })
    target_counts = Counter(str(row.get("target_kind")) for row in rows)
    label_counts = Counter(str(row.get("label") or "none") for row in rows)
    split_counts = Counter(str(row.get("split")) for row in rows)
    training_rows = [
        row for row in rows if bool(row.get("usable_for_training"))
    ]
    return {
        "schema_version": "krk_selector_target_dataset.v0",
        "causal_status": "non_causal_target_dataset",
        "runtime_behavior_changed": False,
        "runtime_defaults_changed": False,
        "runtime_arbiter_implemented": False,
        "source_artifacts": [str(FRAMES), str(SEMANTICS)],
        "label_semantics_version": semantics.get("schema_version"),
        "row_count": len(rows),
        "training_row_count": len(training_rows),
        "target_kind_counts": dict(sorted(target_counts.items())),
        "label_counts": dict(sorted(label_counts.items())),
        "split_counts": dict(sorted(split_counts.items())),
        "stage7_training_rows": sum(
            1 for row in training_rows if row.get("source_stage") == "stage7"
        ),
        "rows": rows,
        "decision": {
            "status": "selector_target_dataset_built",
            "runtime_arbiter_allowed": False,
            "sandbox_ready": False,
            "recommended_next_step": "probe_selector_targets_by_target_kind_replay_free",
        },
    }


def write_markdown(payload: dict[str, Any], path: Path) -> None:
    lines = [
        "# KRK Selector Target Dataset v0",
        "",
        "This replay-free dataset maps existing labels into explicit selector target kinds.",
        "",
        "## Summary",
        "",
        f"- Rows: `{payload['row_count']}`",
        f"- Training rows: `{payload['training_row_count']}`",
        f"- Target kind counts: `{payload['target_kind_counts']}`",
        f"- Label counts: `{payload['label_counts']}`",
        f"- Split counts: `{payload['split_counts']}`",
        f"- Stage7 training rows: `{payload['stage7_training_rows']}`",
        "",
        "## Decision",
        "",
        f"Status: `{payload['decision']['status']}`",
        f"Runtime arbiter allowed: `{payload['decision']['runtime_arbiter_allowed']}`",
        f"Sandbox ready: `{payload['decision']['sandbox_ready']}`",
        f"Recommended next step: `{payload['decision']['recommended_next_step']}`",
    ]
    (ROOT / path).write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    payload = build_dataset()
    (ROOT / OUT_JSON).write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_markdown(payload, OUT_MD)


if __name__ == "__main__":
    main()
