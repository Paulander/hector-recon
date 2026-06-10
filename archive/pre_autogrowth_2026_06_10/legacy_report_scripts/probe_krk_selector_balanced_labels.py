#!/usr/bin/env python3
"""Probe replay-free balanced selector labels with simple non-causal baselines."""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import Any, Callable


ROOT = Path(__file__).resolve().parents[1]
DATASET = Path("reports/krk_selector_balanced_label_dataset_v1.json")
OUT_JSON = Path("reports/krk_selector_balanced_label_probe_v1.json")
OUT_MD = Path("reports/krk_selector_balanced_label_probe_v1.md")


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


def _label(row: dict[str, Any]) -> str:
    return str(row.get("label") or "none")


def _majority(rows: list[dict[str, Any]], default: str = "negative") -> str:
    counts = Counter(_label(row) for row in rows)
    if not counts:
        return default
    return sorted(counts.items(), key=lambda item: (-item[1], item[0]))[0][0]


def _loo(rows: list[dict[str, Any]], name: str, key_fn: Callable[[dict[str, Any]], str]) -> dict[str, Any]:
    correct = 0
    fallback = 0
    for idx, row in enumerate(rows):
        train = [other for i, other in enumerate(rows) if i != idx]
        key = key_fn(row)
        matching = [other for other in train if key_fn(other) == key]
        if not matching:
            fallback += 1
        pred = _majority(matching, default=_majority(train))
        if pred == _label(row):
            correct += 1
    return {
        "name": name,
        "accuracy": correct / len(rows) if rows else None,
        "correct": correct,
        "total": len(rows),
        "fallback_count": fallback,
    }


def build_probe() -> dict[str, Any]:
    rows = [
        row for row in _load_json(DATASET).get("rows", []) or []
        if row.get("label") in {"positive", "negative"}
    ]
    label_counts = Counter(_label(row) for row in rows)
    baselines = [
        _loo(rows, "provider_id_loo", lambda row: str(row.get("provider_id") or "unknown")),
        _loo(rows, "provider_family_loo", lambda row: str(row.get("provider_family") or "unknown")),
        _loo(rows, "provider_maturity_loo", lambda row: str(row.get("provider_maturity") or "unknown")),
        _loo(rows, "active_landmark_loo", lambda row: str(row.get("active_landmark_label") or "unknown")),
        _loo(rows, "source_stage_loo", lambda row: str(row.get("source_stage") or "unknown")),
        _loo(rows, "provider_family_landmark_loo", lambda row: f"{row.get('provider_family')}|{row.get('active_landmark_label')}"),
        _loo(rows, "provider_maturity_landmark_loo", lambda row: f"{row.get('provider_maturity')}|{row.get('active_landmark_label')}"),
    ]
    best = max(baselines, key=lambda item: float(item.get("accuracy") or -1.0))
    high_accuracy = bool(best.get("accuracy") is not None and float(best["accuracy"]) >= 0.75)
    return {
        "schema_version": "krk_selector_balanced_label_probe.v1",
        "causal_status": "non_causal_probe",
        "runtime_behavior_changed": False,
        "runtime_defaults_changed": False,
        "runtime_arbiter_implemented": False,
        "source_artifact": str(DATASET),
        "row_count": len(rows),
        "label_counts": dict(sorted(label_counts.items())),
        "baselines": baselines,
        "best_baseline": {
            "name": best.get("name"),
            "accuracy": best.get("accuracy"),
        },
        "decision": {
            "status": (
                "balanced_labels_support_non_causal_selector_signal"
                if high_accuracy
                else "balanced_labels_no_strong_selector_signal"
            ),
            "runtime_arbiter_allowed": False,
            "selector_sandbox_ready": False,
            "recommended_next_step": "architecture_review_before_any_selector_sandbox",
        },
        "interpretation": [
            "Balanced replay-free labels are suitable for a small non-causal signal check.",
            "A high score here is not sandbox evidence because the dataset is small and constructed from existing controls.",
            "Runtime arbiter work remains blocked pending architecture review and guardrail criteria.",
        ],
    }


def write_markdown(payload: dict[str, Any]) -> None:
    lines = [
        "# KRK Selector Balanced Label Probe v1",
        "",
        "This non-causal probe checks simple selector signals on the replay-free balanced label dataset.",
        "",
        "## Summary",
        "",
        f"- Rows: `{payload['row_count']}`",
        f"- Label counts: `{payload['label_counts']}`",
        f"- Best baseline: `{payload['best_baseline']}`",
        f"- Decision: `{payload['decision']['status']}`",
        f"- Runtime arbiter allowed: `{payload['decision']['runtime_arbiter_allowed']}`",
        f"- Selector sandbox ready: `{payload['decision']['selector_sandbox_ready']}`",
        "",
        "## Baselines",
        "",
    ]
    for baseline in payload["baselines"]:
        lines.append(
            f"- `{baseline['name']}` accuracy=`{baseline['accuracy']}` "
            f"correct=`{baseline['correct']}` total=`{baseline['total']}`"
        )
    lines.extend(["", "## Interpretation", ""])
    for item in payload["interpretation"]:
        lines.append(f"- {item}")
    (ROOT / OUT_MD).write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    payload = build_probe()
    (ROOT / OUT_JSON).write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_markdown(payload)


if __name__ == "__main__":
    main()
