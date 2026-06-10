#!/usr/bin/env python3
"""Probe recovered ownership-selection labels non-causally."""

from __future__ import annotations

import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
OWNERSHIP = Path("reports/krk_ownership_selection_label_dataset_v0.json")
OUT_JSON = Path("reports/krk_ownership_selection_feature_probe_v0.json")
OUT_MD = Path("reports/krk_ownership_selection_feature_probe_v0.md")


def _load(path: Path) -> dict[str, Any]:
    payload = json.loads((ROOT / path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"expected JSON object: {path}")
    return payload


def _positive(row: dict[str, Any]) -> bool:
    return row.get("target_label") == "selected_owner_converted" or row.get("owner_positive") is True


def _score_bucket(value: Any) -> str:
    if not isinstance(value, (int, float)):
        return "missing"
    if value >= 1_000_000:
        return "mate_like"
    if value >= 10:
        return "high"
    if value >= 0:
        return "nonnegative"
    return "negative"


def _count_bucket(value: Any) -> str:
    if not isinstance(value, int):
        return "missing"
    if value <= 1:
        return "one"
    if value <= 3:
        return "few"
    return "many"


def _term_flag(row: dict[str, Any], term: str) -> str:
    return str(term in set(row.get("source_terms") or []))


def _feature_value(row: dict[str, Any], key: str) -> str:
    if key == "raw_score_bucket":
        return _score_bucket(row.get("target_provider_best_raw_score"))
    if key == "unique_provider_bucket":
        return _count_bucket(row.get("unique_provider_count"))
    if key == "summary_count_bucket":
        return _count_bucket(row.get("target_provider_summary_count"))
    if key.startswith("term:"):
        return _term_flag(row, key.split(":", 1)[1])
    return str(row.get(key))


def _feature_key(row: dict[str, Any], keys: tuple[str, ...]) -> tuple[str, ...]:
    return tuple(_feature_value(row, key) for key in keys)


def _score(train: list[dict[str, Any]], row: dict[str, Any], keys: tuple[str, ...]) -> float:
    global_rate = sum(1 for item in train if _positive(item)) / len(train) if train else 0.5
    counts: dict[tuple[str, ...], Counter[str]] = defaultdict(Counter)
    for item in train:
        counts[_feature_key(item, keys)]["positive" if _positive(item) else "negative"] += 1
    counter = counts.get(_feature_key(row, keys))
    if not counter:
        return global_rate
    total = counter["positive"] + counter["negative"]
    return counter["positive"] / total if total else global_rate


def _metrics(rows: list[dict[str, Any]], keys: tuple[str, ...], threshold: float) -> dict[str, Any]:
    predictions = []
    for state_id in sorted({str(row.get("state_id")) for row in rows}):
        train = [row for row in rows if str(row.get("state_id")) != state_id]
        test = [row for row in rows if str(row.get("state_id")) == state_id]
        for row in test:
            score = _score(train, row, keys)
            predictions.append(
                {
                    "state_id": row.get("state_id"),
                    "provider_id": row.get("provider_id"),
                    "score": score,
                    "threshold": threshold,
                    "predicted_positive": score >= threshold,
                    "label_positive": _positive(row),
                    "feature_key": list(_feature_key(row, keys)),
                }
            )
    tp = sum(1 for item in predictions if item["predicted_positive"] and item["label_positive"])
    fp = sum(1 for item in predictions if item["predicted_positive"] and not item["label_positive"])
    tn = sum(1 for item in predictions if not item["predicted_positive"] and not item["label_positive"])
    fn = sum(1 for item in predictions if not item["predicted_positive"] and item["label_positive"])
    total = len(predictions)
    return {
        "row_count": total,
        "threshold": threshold,
        "true_positive": tp,
        "false_positive": fp,
        "true_negative": tn,
        "false_negative": fn,
        "accuracy": (tp + tn) / total if total else None,
        "positive_precision": tp / (tp + fp) if tp + fp else None,
        "positive_recall": tp / (tp + fn) if tp + fn else None,
        "negative_suppression": tn / (tn + fp) if tn + fp else None,
        "predictions": predictions,
    }


def build_probe() -> dict[str, Any]:
    ownership = _load(OWNERSHIP)
    if ownership.get("causal_status") != "non_causal_ownership_label_dataset":
        raise ValueError("ownership labels must remain non-causal")
    rows = [row for row in ownership.get("rows") or [] if row.get("source_stage") != "stage7"]
    specs = {
        "provider_family": ("provider_family",),
        "stage_provider_family": ("source_stage", "provider_family"),
        "landmark_provider_family": ("active_landmark_label", "provider_family"),
        "raw_score_bucket": ("raw_score_bucket",),
        "provider_family_raw_score": ("provider_family", "raw_score_bucket"),
        "provider_family_summary_count": ("provider_family", "summary_count_bucket"),
        "provider_family_unique_count": ("provider_family", "unique_provider_bucket"),
        "edge_terms_provider_family": (
            "provider_family",
            "term:enemy_king_near_edge",
            "term:fence_exists",
            "term:wrong_tempo_detected",
        ),
    }
    thresholds = (0.5, 0.6, 0.75)
    results = {
        f"{name}@{threshold}": {"features": list(keys), **_metrics(rows, keys, threshold)}
        for name, keys in specs.items()
        for threshold in thresholds
    }
    best_name, best = max(
        results.items(),
        key=lambda item: (
            item[1]["negative_suppression"] if item[1]["negative_suppression"] is not None else -1,
            item[1]["positive_recall"] if item[1]["positive_recall"] is not None else -1,
            item[1]["accuracy"] if item[1]["accuracy"] is not None else -1,
        ),
    )
    underpowered = len(rows) < 30 or sum(1 for row in rows if not _positive(row)) < 10
    status = "ownership_selection_signal_underpowered"
    if (best.get("negative_suppression") or 0) >= 0.5 and (best.get("positive_recall") or 0) >= 0.7:
        status = "ownership_selection_probe_promising_underpowered"
    payload = {
        "schema_version": "krk_ownership_selection_feature_probe.v0",
        "causal_status": "non_causal_offline_probe",
        "runtime_behavior_changed": False,
        "runtime_defaults_changed": False,
        "runtime_selector_implemented": False,
        "runtime_candidate_generator_implemented": False,
        "runtime_terminals_added": False,
        "runtime_dtm_or_tablebase_lookup": False,
        "gameplay_topology_mutation": False,
        "stage7_promotion_allowed": False,
        "stage8_training_allowed": False,
        "source_artifacts": [str(OWNERSHIP)],
        "summary": {
            "row_count": len(rows),
            "state_count": len({row.get("state_id") for row in rows}),
            "positive_owner_count": sum(1 for row in rows if _positive(row)),
            "negative_owner_count": sum(1 for row in rows if not _positive(row)),
            "source_stage_counts": dict(Counter(str(row.get("source_stage")) for row in rows)),
            "provider_family_counts": dict(Counter(str(row.get("provider_family")) for row in rows)),
            "stage7_row_count": sum(1 for row in rows if row.get("source_stage") == "stage7"),
            "underpowered": underpowered,
        },
        "results": results,
        "best_result": {"objective": best_name, **{key: value for key, value in best.items() if key != "predictions"}},
        "decision": {
            "status": status,
            "recommended_next_step": "review_split_objective_readiness_with_recovered_ownership_labels",
            "runtime_work_allowed": False,
            "selector_training_allowed": False,
            "stage7_promotion_allowed": False,
            "stage8_training_allowed": False,
        },
    }
    validate_probe(payload)
    return payload


def validate_probe(payload: dict[str, Any]) -> None:
    for key in (
        "runtime_behavior_changed",
        "runtime_defaults_changed",
        "runtime_selector_implemented",
        "runtime_candidate_generator_implemented",
        "runtime_terminals_added",
        "runtime_dtm_or_tablebase_lookup",
        "gameplay_topology_mutation",
        "stage7_promotion_allowed",
        "stage8_training_allowed",
    ):
        if payload.get(key) is not False:
            raise ValueError(f"{key} must be false")
    if payload["summary"]["stage7_row_count"] != 0:
        raise ValueError("Stage 7 rows must remain excluded")
    if payload["decision"]["selector_training_allowed"] is not False:
        raise ValueError("selector training remains blocked")


def render_markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# KRK Ownership Selection Feature Probe v0",
        "",
        "Non-causal probe over recovered normal-routing ownership-selection labels.",
        "",
        "## Summary",
        "",
    ]
    for key, value in payload["summary"].items():
        lines.append(f"- `{key}`: `{value}`")
    lines.extend(["", "## Best Result", "", f"`{payload['best_result']}`", "", "## Decision", ""])
    for key, value in payload["decision"].items():
        lines.append(f"- `{key}`: `{value}`")
    lines.append("")
    return "\n".join(lines)


def main() -> None:
    payload = build_probe()
    (ROOT / OUT_JSON).write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (ROOT / OUT_MD).write_text(render_markdown(payload), encoding="utf-8")
    print(json.dumps(payload["decision"], indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
