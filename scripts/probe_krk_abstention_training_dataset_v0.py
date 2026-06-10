#!/usr/bin/env python3
"""Probe replay-free protected-control abstention labels."""

from __future__ import annotations

import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DATASET = Path("reports/krk_abstention_training_dataset_v0.json")
OUT_JSON = Path("reports/krk_abstention_training_probe_v0.json")
OUT_MD = Path("reports/krk_abstention_training_probe_v0.md")


def _load_json(path: Path) -> dict[str, Any]:
    payload = json.loads((ROOT / path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"expected JSON object: {path}")
    return payload


def _unsafe(row: dict[str, Any]) -> bool:
    return row.get("abstention_label") == "unsafe_owner"


def _key(row: dict[str, Any], keys: tuple[str, ...]) -> tuple[str, ...]:
    return tuple(str(row.get(key)) for key in keys)


def _score_unsafe(train: list[dict[str, Any]], row: dict[str, Any], keys: tuple[str, ...]) -> float:
    global_rate = sum(1 for item in train if _unsafe(item)) / len(train) if train else 0.5
    counts: dict[tuple[str, ...], Counter[str]] = defaultdict(Counter)
    for item in train:
        counts[_key(item, keys)]["unsafe" if _unsafe(item) else "safe"] += 1
    counter = counts.get(_key(row, keys))
    if not counter:
        return global_rate
    total = counter["unsafe"] + counter["safe"]
    return counter["unsafe"] / total if total else global_rate


def _metrics(predictions: list[dict[str, Any]]) -> dict[str, Any]:
    total = len(predictions)
    correct = sum(1 for item in predictions if item["predicted_unsafe"] == item["label_unsafe"])
    tp = sum(1 for item in predictions if item["predicted_unsafe"] and item["label_unsafe"])
    fp = sum(1 for item in predictions if item["predicted_unsafe"] and not item["label_unsafe"])
    tn = sum(1 for item in predictions if not item["predicted_unsafe"] and not item["label_unsafe"])
    fn = sum(1 for item in predictions if not item["predicted_unsafe"] and item["label_unsafe"])
    return {
        "row_count": total,
        "accuracy": correct / total if total else None,
        "unsafe_true_positive": tp,
        "unsafe_false_positive": fp,
        "safe_true_negative": tn,
        "unsafe_false_negative": fn,
        "unsafe_precision": tp / (tp + fp) if tp + fp else None,
        "unsafe_recall": tp / (tp + fn) if tp + fn else None,
        "negative_suppression": tp / (tp + fn) if tp + fn else None,
        "safe_preservation": tn / (tn + fp) if tn + fp else None,
    }


def _leave_state_out(rows: list[dict[str, Any]], keys: tuple[str, ...]) -> dict[str, Any]:
    predictions = []
    for state in sorted({str(row.get("state_id")) for row in rows}):
        test = [row for row in rows if str(row.get("state_id")) == state]
        train = [row for row in rows if str(row.get("state_id")) != state]
        for row in test:
            score = _score_unsafe(train, row, keys)
            predictions.append({
                "state_id": row.get("state_id"),
                "provider_id": row.get("provider_id"),
                "unsafe_score": score,
                "predicted_unsafe": score >= 0.5,
                "label_unsafe": _unsafe(row),
            })
    return _metrics(predictions)


def build_probe() -> dict[str, Any]:
    dataset = _load_json(DATASET)
    if dataset.get("causal_status") != "non_causal_abstention_dataset":
        raise ValueError("abstention dataset must remain non-causal")
    rows = [row for row in dataset.get("rows") or [] if row.get("usable_for_training")]
    specs = {
        "provider_family": ("provider_family",),
        "provider_maturity": ("provider_maturity",),
        "source_stage": ("source_stage",),
        "stage_family": ("source_stage", "provider_family"),
        "family_maturity": ("provider_family", "provider_maturity"),
        "provider_version": ("provider_version",),
    }
    results = {name: _leave_state_out(rows, keys) for name, keys in specs.items()}
    best_name, best_metrics = max(
        results.items(),
        key=lambda item: item[1]["negative_suppression"] if item[1]["negative_suppression"] is not None else -1,
    )
    summary = dataset.get("summary") or {}
    negative_count = (summary.get("label_counts") or {}).get("unsafe_owner", 0)
    under_minimum = (
        len(rows) < int(summary.get("minimum_training_rows_required") or 0)
        or int(negative_count) < int(summary.get("minimum_negative_rows_required") or 0)
    )
    ready = (
        not under_minimum
        and (best_metrics.get("negative_suppression") or 0.0) >= 0.7
        and (best_metrics.get("safe_preservation") or 0.0) >= 0.7
    )
    status = "abstention_signal_runtime_review_ready" if ready else "abstention_signal_underpowered_no_runtime"
    probe = {
        "schema_version": "krk_abstention_training_probe.v0",
        "causal_status": "non_causal_offline_probe",
        "runtime_behavior_changed": False,
        "runtime_defaults_changed": False,
        "runtime_selector_implemented": False,
        "runtime_dtm_or_tablebase_lookup": False,
        "gameplay_topology_mutation": False,
        "stage7_promotion_allowed": False,
        "stage8_training_allowed": False,
        "source_artifact": str(DATASET),
        "summary": {
            "row_count": len(rows),
            "state_count": len({row.get("state_id") for row in rows}),
            "label_counts": summary.get("label_counts"),
            "stage_counts": summary.get("stage_counts"),
            "provider_family_counts": summary.get("provider_family_counts"),
            "under_minimum_requirements": under_minimum,
        },
        "results": results,
        "best_result": {"objective": best_name, **best_metrics},
        "decision": {
            "status": status,
            "recommended_next_step": (
                "collect_more_protected_negative_controls_before_runtime_review"
                if under_minimum
                else "architecture_review_before_runtime_selector"
            ),
            "runtime_test_allowed_next": False,
            "stage7_promotion_allowed": False,
            "stage8_training_allowed": False,
        },
    }
    validate_probe(probe)
    return probe


def validate_probe(probe: dict[str, Any]) -> None:
    for key in (
        "runtime_behavior_changed",
        "runtime_defaults_changed",
        "runtime_selector_implemented",
        "runtime_dtm_or_tablebase_lookup",
        "gameplay_topology_mutation",
        "stage7_promotion_allowed",
        "stage8_training_allowed",
    ):
        if probe.get(key) is not False:
            raise ValueError(f"{key} must be false")


def render_markdown(probe: dict[str, Any]) -> str:
    lines = [
        "# KRK Abstention Training Probe v0",
        "",
        "This offline probe evaluates whether existing protected forced-provider labels can support an abstention-first selector. It does not implement a selector.",
        "",
        "## Summary",
        "",
    ]
    for key, value in probe["summary"].items():
        lines.append(f"- `{key}`: `{value}`")
    lines.extend(["", "## Results", ""])
    for name, metrics in probe["results"].items():
        lines.append(
            f"- `{name}` accuracy=`{metrics['accuracy']}` "
            f"negative_suppression=`{metrics['negative_suppression']}` "
            f"safe_preservation=`{metrics['safe_preservation']}`"
        )
    lines.extend(
        [
            "",
            "## Best Result",
            "",
            f"`{probe['best_result']}`",
            "",
            "## Decision",
            "",
            f"- Status: `{probe['decision']['status']}`",
            f"- Recommended next step: `{probe['decision']['recommended_next_step']}`",
            f"- Runtime test allowed next: `{probe['decision']['runtime_test_allowed_next']}`",
            f"- Stage 7 promotion allowed: `{probe['decision']['stage7_promotion_allowed']}`",
            f"- Stage 8 training allowed: `{probe['decision']['stage8_training_allowed']}`",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> None:
    probe = build_probe()
    (ROOT / OUT_JSON).write_text(json.dumps(probe, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (ROOT / OUT_MD).write_text(render_markdown(probe), encoding="utf-8")
    print(json.dumps(probe["decision"], indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
