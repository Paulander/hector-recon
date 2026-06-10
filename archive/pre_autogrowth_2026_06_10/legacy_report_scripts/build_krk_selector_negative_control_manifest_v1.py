#!/usr/bin/env python3
"""Identify replay-free negative protected selector controls."""

from __future__ import annotations

import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
FEATURES = Path("reports/krk_selector_provenance_feature_dataset_v0.json")
OUT_JSON = Path("reports/krk_selector_negative_control_manifest_v1.json")
OUT_MD = Path("reports/krk_selector_negative_control_manifest_v1.md")


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


def _select_negative_controls(rows: list[dict[str, Any]], per_stage: int = 4) -> list[dict[str, Any]]:
    selected: list[dict[str, Any]] = []
    by_stage: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        if (
            row.get("target_kind") == "selected_playout_success"
            and row.get("usable_for_training")
            and row.get("label") == "negative"
            and row.get("source_stage") in {"stage4", "stage5", "stage6"}
        ):
            by_stage[str(row.get("source_stage"))].append(row)
    for stage in ["stage4", "stage5", "stage6"]:
        seen: set[tuple[str, str]] = set()
        for row in by_stage.get(stage, []):
            key = (str(row.get("state_id")), str(row.get("provider_id")))
            if key in seen:
                continue
            seen.add(key)
            selected.append({
                "schema_version": "krk_selector_negative_control.v1",
                "causal_status": "non_causal_negative_control",
                "state_id": row.get("state_id"),
                "frame_id": row.get("frame_id"),
                "source_stage": row.get("source_stage"),
                "active_landmark_label": row.get("active_landmark_label"),
                "provider_id": row.get("provider_id"),
                "provider_family": row.get("provider_family"),
                "provider_maturity": row.get("provider_maturity"),
                "move_uci": row.get("move_uci"),
                "label": "negative",
                "label_source": row.get("label_source"),
                "target_kind": "selected_playout_success",
                "stage7_training_row": False,
            })
            if sum(1 for item in selected if item["source_stage"] == stage) >= per_stage:
                break
    return selected


def build_manifest() -> dict[str, Any]:
    rows = _load_json(FEATURES).get("rows", []) or []
    controls = _select_negative_controls(rows)
    return {
        "schema_version": "krk_selector_negative_control_manifest.v1",
        "causal_status": "non_causal_negative_control_manifest",
        "runtime_behavior_changed": False,
        "runtime_defaults_changed": False,
        "runtime_arbiter_implemented": False,
        "source_artifact": str(FEATURES),
        "control_count": len(controls),
        "stage_counts": dict(sorted(Counter(item["source_stage"] for item in controls).items())),
        "provider_counts": dict(sorted(Counter(str(item.get("provider_id")) for item in controls).items())),
        "controls": controls,
        "decision": {
            "status": "negative_protected_controls_identified_replay_free",
            "runtime_arbiter_allowed": False,
            "selector_sandbox_ready": False,
            "recommended_next_step": "build_balanced_replay_free_selector_label_dataset",
        },
    }


def write_markdown(payload: dict[str, Any]) -> None:
    lines = [
        "# KRK Selector Negative Control Manifest v1",
        "",
        "This manifest identifies replay-free negative protected-control examples from existing selector labels.",
        "",
        "## Summary",
        "",
        f"- Controls: `{payload['control_count']}`",
        f"- Stage counts: `{payload['stage_counts']}`",
        f"- Provider counts: `{payload['provider_counts']}`",
        f"- Runtime arbiter allowed: `{payload['decision']['runtime_arbiter_allowed']}`",
        f"- Selector sandbox ready: `{payload['decision']['selector_sandbox_ready']}`",
        "",
        "## Controls",
        "",
    ]
    for item in payload["controls"]:
        lines.append(
            f"- `{item['state_id']}` stage=`{item['source_stage']}` "
            f"provider=`{item['provider_id']}` landmark=`{item['active_landmark_label']}`"
        )
    lines.extend([
        "",
        "## Decision",
        "",
        f"Status: `{payload['decision']['status']}`",
        f"Recommended next step: `{payload['decision']['recommended_next_step']}`",
    ])
    (ROOT / OUT_MD).write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    payload = build_manifest()
    (ROOT / OUT_JSON).write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_markdown(payload)


if __name__ == "__main__":
    main()
