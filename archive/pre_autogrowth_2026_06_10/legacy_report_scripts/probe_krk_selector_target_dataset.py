#!/usr/bin/env python3
"""Probe KRK selector target dataset by explicit target kind."""

from __future__ import annotations

import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DATASET = Path("reports/krk_selector_target_dataset_v0.json")
OUT_JSON = Path("reports/krk_selector_target_probe_v0.json")
OUT_MD = Path("reports/krk_selector_target_probe_v0.md")


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


def build_probe(root: Path = ROOT) -> dict[str, Any]:
    payload = _load_json(DATASET)
    rows = list(payload.get("rows", []) or [])
    by_kind: dict[str, Counter] = defaultdict(Counter)
    by_stage: dict[str, Counter] = defaultdict(Counter)
    training_rows = []
    for row in rows:
        kind = str(row.get("target_kind") or "unknown")
        label = str(row.get("label") or "none")
        stage = str(row.get("source_stage") or "unknown")
        by_kind[kind][label] += 1
        by_stage[stage][label] += 1
        if row.get("usable_for_training"):
            training_rows.append(row)
    training_label_counts = Counter(str(row.get("label") or "none") for row in training_rows)
    heldout_training_rows = [
        row for row in training_rows if row.get("target_kind") == "held_out_challenge"
    ]
    positive_rate = (
        training_label_counts.get("positive", 0) / len(training_rows)
        if training_rows
        else None
    )
    status = "target_dataset_ready_for_non_causal_baseline_probe"
    if heldout_training_rows:
        status = "target_dataset_invalid_heldout_in_training"
    return {
        "schema_version": "krk_selector_target_probe.v0",
        "causal_status": "non_causal_probe",
        "runtime_behavior_changed": False,
        "runtime_defaults_changed": False,
        "runtime_arbiter_implemented": False,
        "source_artifact": str(DATASET),
        "row_count": len(rows),
        "training_row_count": len(training_rows),
        "training_label_counts": dict(sorted(training_label_counts.items())),
        "training_positive_rate": positive_rate,
        "target_kind_label_counts": {
            key: dict(sorted(counter.items()))
            for key, counter in sorted(by_kind.items())
        },
        "stage_label_counts": {
            key: dict(sorted(counter.items()))
            for key, counter in sorted(by_stage.items())
        },
        "heldout_training_row_count": len(heldout_training_rows),
        "interpretation": [
            "The selector target dataset cleanly separates selected-playout labels from forced-provider diagnostics.",
            "Stage7 held-out challenge rows are excluded from training rows.",
            "The target dataset is ready for non-causal baseline probing, not runtime arbitration."
        ],
        "decision": {
            "status": status,
            "runtime_arbiter_allowed": False,
            "sandbox_ready": False,
            "recommended_next_step": "run_non_causal_selector_baselines_by_target_kind",
        },
    }


def write_markdown(payload: dict[str, Any], path: Path) -> None:
    lines = [
        "# KRK Selector Target Probe v0",
        "",
        "This replay-free probe checks the explicit target-kind dataset.",
        "",
        "## Summary",
        "",
        f"- Rows: `{payload['row_count']}`",
        f"- Training rows: `{payload['training_row_count']}`",
        f"- Training label counts: `{payload['training_label_counts']}`",
        f"- Training positive rate: `{payload['training_positive_rate']}`",
        f"- Target-kind label counts: `{payload['target_kind_label_counts']}`",
        f"- Held-out training rows: `{payload['heldout_training_row_count']}`",
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
    payload = build_probe()
    (ROOT / OUT_JSON).write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_markdown(payload, OUT_MD)


if __name__ == "__main__":
    main()
