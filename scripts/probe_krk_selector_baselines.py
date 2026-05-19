#!/usr/bin/env python3
"""Non-causal baseline probes for KRK selector target labels."""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DATASET = Path("reports/krk_selector_target_dataset_v0.json")
OUT_JSON = Path("reports/krk_selector_baseline_probe_v0.json")
OUT_MD = Path("reports/krk_selector_baseline_probe_v0.md")


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


def _label(row: dict[str, Any]) -> str:
    return str(row.get("label") or "none")


def _majority_label(rows: list[dict[str, Any]], *, default: str = "negative") -> str:
    counts = Counter(_label(row) for row in rows)
    if not counts:
        return default
    return sorted(counts.items(), key=lambda item: (-item[1], item[0]))[0][0]


def _leave_one_out_prior(rows: list[dict[str, Any]], key: str) -> dict[str, Any]:
    correct = 0
    predictions = []
    for index, row in enumerate(rows):
        train = [other for i, other in enumerate(rows) if i != index]
        matching = [
            other for other in train
            if str(other.get(key) or "") == str(row.get(key) or "")
        ]
        pred = _majority_label(matching, default=_majority_label(train))
        actual = _label(row)
        if pred == actual:
            correct += 1
        predictions.append({
            "state_id": row.get("state_id"),
            "key": str(row.get(key) or ""),
            "predicted": pred,
            "actual": actual,
        })
    return {
        "key": key,
        "accuracy": correct / len(rows) if rows else None,
        "correct": correct,
        "total": len(rows),
        "predictions": predictions,
    }


def build_probe(root: Path = ROOT) -> dict[str, Any]:
    payload = _load_json(DATASET)
    rows = [
        row for row in payload.get("rows", []) or []
        if row.get("target_kind") == "selected_playout_success"
        and row.get("usable_for_training")
        and row.get("label") in {"positive", "negative"}
    ]
    label_counts = Counter(_label(row) for row in rows)
    majority = _majority_label(rows)
    majority_accuracy = (
        label_counts.get(majority, 0) / len(rows)
        if rows
        else None
    )
    baselines = [
        {
            "name": "majority_label",
            "prediction": majority,
            "accuracy": majority_accuracy,
            "correct": label_counts.get(majority, 0),
            "total": len(rows),
        },
        {"name": "provider_prior_loo", **_leave_one_out_prior(rows, "provider_id")},
        {"name": "stage_prior_loo", **_leave_one_out_prior(rows, "source_stage")},
        {"name": "active_landmark_prior_loo", **_leave_one_out_prior(rows, "active_landmark_label")},
    ]
    best = max(
        baselines,
        key=lambda item: float(item.get("accuracy") if item.get("accuracy") is not None else -1.0),
    ) if baselines else None
    status = "selector_baselines_need_richer_features"
    if best and float(best.get("accuracy") or 0.0) >= 0.8:
        status = "simple_selector_baseline_promising_non_causal"
    return {
        "schema_version": "krk_selector_baseline_probe.v0",
        "causal_status": "non_causal_probe",
        "runtime_behavior_changed": False,
        "runtime_defaults_changed": False,
        "runtime_arbiter_implemented": False,
        "source_artifact": str(DATASET),
        "target_kind": "selected_playout_success",
        "row_count": len(rows),
        "label_counts": dict(sorted(label_counts.items())),
        "baselines": baselines,
        "best_baseline": {
            "name": best.get("name") if best else None,
            "accuracy": best.get("accuracy") if best else None,
        },
        "decision": {
            "status": status,
            "runtime_arbiter_allowed": False,
            "sandbox_ready": False,
            "recommended_next_step": "join_selector_targets_with_observation_features_non_causal",
        },
    }


def write_markdown(payload: dict[str, Any], path: Path) -> None:
    lines = [
        "# KRK Selector Baseline Probe v0",
        "",
        "This non-causal probe evaluates simple baselines for `selected_playout_success` labels.",
        "",
        "## Summary",
        "",
        f"- Rows: `{payload['row_count']}`",
        f"- Label counts: `{payload['label_counts']}`",
        f"- Best baseline: `{payload['best_baseline']}`",
        "",
        "## Baselines",
        "",
    ]
    for baseline in payload["baselines"]:
        lines.append(
            f"- `{baseline['name']}` accuracy=`{baseline.get('accuracy')}` "
            f"correct=`{baseline.get('correct')}` total=`{baseline.get('total')}`"
        )
    lines.extend([
        "",
        "## Decision",
        "",
        f"Status: `{payload['decision']['status']}`",
        f"Sandbox ready: `{payload['decision']['sandbox_ready']}`",
        f"Runtime arbiter allowed: `{payload['decision']['runtime_arbiter_allowed']}`",
        f"Recommended next step: `{payload['decision']['recommended_next_step']}`",
    ])
    (ROOT / path).write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    payload = build_probe()
    (ROOT / OUT_JSON).write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_markdown(payload, OUT_MD)


if __name__ == "__main__":
    main()
