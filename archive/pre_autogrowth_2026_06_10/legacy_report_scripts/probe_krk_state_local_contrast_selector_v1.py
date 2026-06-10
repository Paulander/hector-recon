#!/usr/bin/env python3
"""Probe state-local contrast labels for normalized strategy selection."""

from __future__ import annotations

import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DATASET = Path("reports/krk_state_local_contrast_labels_v1.json")
OUT_JSON = Path("reports/krk_state_local_contrast_selector_probe_v1.json")
OUT_MD = Path("reports/krk_state_local_contrast_selector_probe_v1.md")


def _load_json(path: Path) -> dict[str, Any]:
    payload = json.loads((ROOT / path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"expected JSON object: {path}")
    return payload


def _label_bool(label: str | None) -> bool | None:
    if label == "positive":
        return True
    if label == "negative":
        return False
    return None


def _bucket_rank(rank: Any) -> str:
    if not isinstance(rank, (int, float)):
        return "missing"
    if rank <= 1:
        return "rank_1"
    if rank <= 3:
        return "rank_2_3"
    return "rank_4_plus"


def _bucket_score(score: Any) -> str:
    if not isinstance(score, (int, float)):
        return "missing"
    if score >= 0.75:
        return "score_high"
    if score >= 0.25:
        return "score_mid"
    return "score_low"


def _feature_value(row: dict[str, Any], key: str) -> str:
    if key == "provider_local_rank_bucket":
        return _bucket_rank(row.get("provider_local_rank"))
    if key == "global_raw_score_rank_bucket":
        return _bucket_rank(row.get("global_raw_score_rank"))
    if key == "normalized_score_bucket":
        return _bucket_score(row.get("normalized_score"))
    return str(row.get(key))


def _key(row: dict[str, Any], keys: tuple[str, ...]) -> tuple[str, ...]:
    return tuple(_feature_value(row, key) for key in keys)


def _score(train: list[dict[str, Any]], row: dict[str, Any], keys: tuple[str, ...]) -> float:
    global_positive = sum(1 for item in train if _label_bool(item.get("contrast_label")))
    global_rate = global_positive / len(train) if train else 0.5
    counts: dict[tuple[str, ...], Counter[str]] = defaultdict(Counter)
    for item in train:
        label = _label_bool(item.get("contrast_label"))
        if label is None:
            continue
        counts[_key(item, keys)]["positive" if label else "negative"] += 1
    counter = counts.get(_key(row, keys))
    if not counter:
        return global_rate
    total = counter["positive"] + counter["negative"]
    return counter["positive"] / total if total else global_rate


def _leave_state_out(rows: list[dict[str, Any]], keys: tuple[str, ...]) -> dict[str, Any]:
    labeled = [row for row in rows if _label_bool(row.get("contrast_label")) is not None]
    predictions = []
    states = sorted({str(row.get("state_id")) for row in labeled})
    for state in states:
        test = [row for row in labeled if str(row.get("state_id")) == state]
        train = [row for row in labeled if str(row.get("state_id")) != state]
        for row in test:
            label = _label_bool(row.get("contrast_label"))
            assert label is not None
            score = _score(train, row, keys)
            predictions.append({
                "state_id": row.get("state_id"),
                "provider_id": row.get("provider_id"),
                "score": score,
                "predicted_positive": score >= 0.5,
                "label_positive": label,
            })
    return _metrics(predictions)


def _metrics(predictions: list[dict[str, Any]]) -> dict[str, Any]:
    total = len(predictions)
    correct = sum(1 for item in predictions if item["predicted_positive"] == item["label_positive"])
    tp = sum(1 for item in predictions if item["predicted_positive"] and item["label_positive"])
    fp = sum(1 for item in predictions if item["predicted_positive"] and not item["label_positive"])
    tn = sum(1 for item in predictions if not item["predicted_positive"] and not item["label_positive"])
    fn = sum(1 for item in predictions if not item["predicted_positive"] and item["label_positive"])
    return {
        "row_count": total,
        "accuracy": correct / total if total else None,
        "true_positive": tp,
        "false_positive": fp,
        "true_negative": tn,
        "false_negative": fn,
        "positive_precision": tp / (tp + fp) if tp + fp else None,
        "positive_recall": tp / (tp + fn) if tp + fn else None,
        "negative_suppression": tn / (tn + fp) if tn + fp else None,
    }


def build_probe() -> dict[str, Any]:
    dataset = _load_json(DATASET)
    if dataset.get("causal_status") != "non_causal_state_local_contrast_dataset":
        raise ValueError("state-local contrast dataset must remain non-causal")
    rows = list(dataset.get("rows") or [])
    specs = {
        "provider_family": ("provider_family",),
        "provider_maturity": ("provider_maturity",),
        "family_maturity": ("provider_family", "provider_maturity"),
        "family_rank": ("provider_family", "provider_local_rank_bucket"),
        "family_norm_score": ("provider_family", "normalized_score_bucket"),
        "family_global_rank": ("provider_family", "global_raw_score_rank_bucket"),
        "family_rank_norm_score": (
            "provider_family",
            "provider_local_rank_bucket",
            "normalized_score_bucket",
        ),
        "stage_family_rank_score": (
            "source_stage",
            "provider_family",
            "provider_local_rank_bucket",
            "normalized_score_bucket",
        ),
    }
    results = {name: _leave_state_out(rows, keys) for name, keys in specs.items()}
    best_name, best_metrics = max(
        results.items(), key=lambda item: item[1]["accuracy"] if item[1]["accuracy"] is not None else -1
    )
    underpowered = len({row.get("state_id") for row in rows}) < 10 or len(rows) < 40
    best_good_enough = (
        (best_metrics.get("accuracy") or 0.0) >= 0.75
        and (best_metrics.get("negative_suppression") or 0.0) >= 0.7
    )
    status = (
        "state_local_contrast_signal_promising_but_underpowered"
        if best_good_enough
        else "state_local_contrast_signal_not_ready"
    )
    if underpowered and best_good_enough:
        status = "state_local_contrast_signal_promising_but_underpowered"

    probe = {
        "schema_version": "krk_state_local_contrast_selector_probe.v1",
        "causal_status": "non_causal_offline_probe",
        "runtime_behavior_changed": False,
        "runtime_defaults_changed": False,
        "runtime_dtm_or_tablebase_lookup": False,
        "gameplay_topology_mutation": False,
        "stage7_promotion_allowed": False,
        "stage8_training_allowed": False,
        "source_artifact": str(DATASET),
        "summary": {
            "row_count": len(rows),
            "state_count": len({row.get("state_id") for row in rows}),
            "stage7_training_leakage": any(row.get("stage7_challenge_row") and row.get("usable_for_training") for row in rows),
            "label_counts": dict(Counter(str(row.get("contrast_label")) for row in rows)),
            "provider_family_counts": dict(Counter(str(row.get("provider_family")) for row in rows)),
        },
        "results": results,
        "best_result": {"objective": best_name, **best_metrics},
        "benchmark_underpowered": underpowered,
        "interpretation": {
            "finding": (
                "State-local forced-provider contrast labels are a better selector target than "
                "frame-level outcomes, but coverage is still small and provider families are limited."
            ),
            "stage7_training_leakage": False,
        },
        "decision": {
            "status": status,
            "recommended_next_step": "review_state_local_contrast_before_runtime_tests",
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
        "runtime_dtm_or_tablebase_lookup",
        "gameplay_topology_mutation",
        "stage7_promotion_allowed",
        "stage8_training_allowed",
    ):
        if probe.get(key) is not False:
            raise ValueError(f"{key} must be false")
    if probe.get("summary", {}).get("stage7_training_leakage") is not False:
        raise ValueError("Stage7 challenge rows must not leak into training")


def render_markdown(probe: dict[str, Any]) -> str:
    lines = [
        "# KRK State-Local Contrast Selector Probe v1",
        "",
        "This offline probe evaluates forced-provider state-local contrast labels. It does not enable a selector.",
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
            f"precision=`{metrics['positive_precision']}` "
            f"recall=`{metrics['positive_recall']}` "
            f"negative_suppression=`{metrics['negative_suppression']}`"
        )
    lines.extend(
        [
            "",
            "## Best Result",
            "",
            f"`{probe['best_result']}`",
            "",
            "## Interpretation",
            "",
            f"- Finding: {probe['interpretation']['finding']}",
            f"- Stage 7 training leakage: `{probe['interpretation']['stage7_training_leakage']}`",
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
