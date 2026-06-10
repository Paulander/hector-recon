#!/usr/bin/env python3
"""Probe whether replay-free stratified selector labels are usable."""

from __future__ import annotations

import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DATASET = Path("reports/krk_selector_stratified_label_dataset_v1.json")
OUT_JSON = Path("reports/krk_selector_stratified_label_balance_probe_v1.json")
OUT_MD = Path("reports/krk_selector_stratified_label_balance_probe_v1.md")


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


def build_probe() -> dict[str, Any]:
    payload = _load_json(DATASET)
    rows = payload.get("rows", []) or []
    label_counts = Counter(str(row.get("label") or "none") for row in rows)
    by_stage: dict[str, Counter[str]] = defaultdict(Counter)
    by_target: dict[str, Counter[str]] = defaultdict(Counter)
    by_provider: dict[str, Counter[str]] = defaultdict(Counter)
    for row in rows:
        label = str(row.get("label") or "none")
        by_stage[str(row.get("source_stage") or "unknown")][label] += 1
        by_target[str(row.get("target_kind") or "unknown")][label] += 1
        by_provider[str(row.get("provider_id") or "unknown")][label] += 1
    positive = label_counts.get("positive", 0)
    negative = label_counts.get("negative", 0)
    underbalanced = positive < 3 or negative < 3
    status = (
        "stratified_labels_underbalanced_no_selector_probe"
        if underbalanced
        else "stratified_labels_ready_for_non_causal_selector_probe"
    )
    return {
        "schema_version": "krk_selector_stratified_label_balance_probe.v1",
        "causal_status": "non_causal_probe",
        "runtime_behavior_changed": False,
        "runtime_defaults_changed": False,
        "runtime_arbiter_implemented": False,
        "source_artifact": str(DATASET),
        "row_count": len(rows),
        "label_counts": dict(sorted(label_counts.items())),
        "by_stage": {key: dict(sorted(value.items())) for key, value in sorted(by_stage.items())},
        "by_target_kind": {key: dict(sorted(value.items())) for key, value in sorted(by_target.items())},
        "by_provider": {key: dict(sorted(value.items())) for key, value in sorted(by_provider.items())},
        "underbalanced": underbalanced,
        "decision": {
            "status": status,
            "runtime_arbiter_allowed": False,
            "selector_sandbox_ready": False,
            "recommended_next_step": (
                "collect_or_identify_negative_protected_controls"
                if underbalanced
                else "run_non_causal_stratified_selector_probe"
            ),
        },
        "interpretation": [
            "Replay-free planned labels are mostly positive protected-control examples.",
            "They are useful as guardrail-positive evidence but are not balanced enough to train or evaluate a selector.",
            "No runtime arbiter or sandbox is justified from this label set.",
        ] if underbalanced else [
            "Replay-free planned labels have enough positive and negative support for a small non-causal probe.",
            "Runtime arbiter and sandbox work remain blocked until that probe is reviewed.",
        ],
    }


def write_markdown(payload: dict[str, Any]) -> None:
    lines = [
        "# KRK Selector Stratified Label Balance Probe v1",
        "",
        "This non-causal probe checks whether replay-free stratified labels are balanced enough for selector evaluation.",
        "",
        "## Summary",
        "",
        f"- Rows: `{payload['row_count']}`",
        f"- Label counts: `{payload['label_counts']}`",
        f"- Underbalanced: `{payload['underbalanced']}`",
        f"- Decision: `{payload['decision']['status']}`",
        f"- Runtime arbiter allowed: `{payload['decision']['runtime_arbiter_allowed']}`",
        f"- Selector sandbox ready: `{payload['decision']['selector_sandbox_ready']}`",
        "",
        "## Breakdown",
        "",
        f"- By stage: `{payload['by_stage']}`",
        f"- By target kind: `{payload['by_target_kind']}`",
        f"- By provider: `{payload['by_provider']}`",
        "",
        "## Interpretation",
        "",
    ]
    for item in payload["interpretation"]:
        lines.append(f"- {item}")
    lines.extend([
        "",
        "## Recommended Next Step",
        "",
        f"`{payload['decision']['recommended_next_step']}`",
    ])
    (ROOT / OUT_MD).write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    payload = build_probe()
    (ROOT / OUT_JSON).write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_markdown(payload)


if __name__ == "__main__":
    main()
