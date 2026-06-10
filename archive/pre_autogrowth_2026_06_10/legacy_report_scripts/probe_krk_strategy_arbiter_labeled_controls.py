#!/usr/bin/env python3
"""Probe labeled KRK strategy-arbiter observation controls replay-free."""

from __future__ import annotations

import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
CONTROLS = Path("reports/krk_strategy_arbiter_labeled_observation_controls_v0.json")
OUT_JSON = Path("reports/krk_strategy_arbiter_labeled_controls_probe_v0.json")
OUT_MD = Path("reports/krk_strategy_arbiter_labeled_controls_probe_v0.md")


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


def build_probe(root: Path = ROOT) -> dict[str, Any]:
    payload = _load_json(CONTROLS)
    records = list(payload.get("records", []) or [])
    label_counts = Counter(str(record.get("selected_label") or "unknown") for record in records)
    stage_label_counts: dict[str, Counter] = defaultdict(Counter)
    for record in records:
        stage_label_counts[str(record.get("source_stage") or "unknown")][
            str(record.get("selected_label") or "unknown")
        ] += 1
    labeled = [
        record for record in records
        if str(record.get("selected_label") or "unknown") in {"positive", "negative"}
    ]
    positive_rate = (
        label_counts.get("positive", 0) / len(labeled)
        if labeled
        else None
    )
    negative_rate = (
        label_counts.get("negative", 0) / len(labeled)
        if labeled
        else None
    )
    stage7_unknown = stage_label_counts.get("stage7", Counter()).get("unknown", 0)
    status = "labeled_controls_mixed_no_sandbox"
    if positive_rate is not None and positive_rate >= 0.9 and stage7_unknown == 0:
        status = "labeled_controls_promising_requires_architecture_review"
    return {
        "schema_version": "krk_strategy_arbiter_labeled_controls_probe.v0",
        "causal_status": "non_causal_probe",
        "runtime_behavior_changed": False,
        "runtime_defaults_changed": False,
        "runtime_arbiter_implemented": False,
        "source_artifact": str(CONTROLS),
        "record_count": len(records),
        "labeled_record_count": len(labeled),
        "selected_label_counts": dict(sorted(label_counts.items())),
        "stage_label_counts": {
            stage: dict(sorted(counter.items()))
            for stage, counter in sorted(stage_label_counts.items())
        },
        "selected_positive_rate_on_labeled_controls": positive_rate,
        "selected_negative_rate_on_labeled_controls": negative_rate,
        "stage7_unknown_count": stage7_unknown,
        "interpretation": [
            "Trace-only observations now have context and provider summaries.",
            "Protected labeled controls are mixed under current raw selection.",
            "Stage7 rows remain unlabeled held-out challenge cases.",
            "This does not justify a runtime arbiter or Stage7 repair."
        ],
        "decision": {
            "status": status,
            "runtime_arbiter_allowed": False,
            "sandbox_ready": False,
            "recommended_next_step": "architecture_review_for_control_plane_selector_objective_or_more_labels",
        },
    }


def write_markdown(payload: dict[str, Any], path: Path) -> None:
    lines = [
        "# KRK Strategy Arbiter Labeled Controls Probe v0",
        "",
        "This is a replay-free probe over labeled trace-only observation controls.",
        "",
        "## Summary",
        "",
        f"- Records: `{payload['record_count']}`",
        f"- Labeled controls: `{payload['labeled_record_count']}`",
        f"- Selected label counts: `{payload['selected_label_counts']}`",
        f"- Stage label counts: `{payload['stage_label_counts']}`",
        f"- Positive rate on labeled controls: `{payload['selected_positive_rate_on_labeled_controls']}`",
        f"- Negative rate on labeled controls: `{payload['selected_negative_rate_on_labeled_controls']}`",
        f"- Stage7 unknown count: `{payload['stage7_unknown_count']}`",
        "",
        "## Interpretation",
        "",
    ]
    lines.extend(f"- {item}" for item in payload["interpretation"])
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
