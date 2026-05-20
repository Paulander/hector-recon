#!/usr/bin/env python3
"""Probe geometry-augmented selector features on protected capacity rows."""

from __future__ import annotations

import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
GEOMETRY = Path("reports/krk_capacity_geometry_feature_audit_v0.json")
NEGATIVE_EVIDENCE = Path("reports/krk_selector_negative_suppression_evidence_v0.json")
OUT_JSON = Path("reports/krk_geometry_augmented_selector_feature_probe_v0.json")
OUT_MD = Path("reports/krk_geometry_augmented_selector_feature_probe_v0.md")


def _load(path: Path) -> dict[str, Any]:
    payload = json.loads((ROOT / path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"expected JSON object: {path}")
    return payload


def _label_positive(row: dict[str, Any]) -> bool | None:
    label = row.get("capacity_label")
    if label == "positive_capacity":
        return True
    if label == "negative_capacity":
        return False
    return None


def _delta_bucket(value: Any) -> str:
    if not isinstance(value, (int, float)):
        return "missing"
    if value < 0:
        return "improves"
    if value > 0:
        return "worsens"
    return "same"


def _edge_bucket(value: Any) -> str:
    if value == 0:
        return "edge"
    if value == 1:
        return "near_edge"
    if isinstance(value, (int, float)):
        return "interior"
    return "missing"


def _feature_value(row: dict[str, Any], key: str) -> str:
    if key == "white_king_distance_delta_bucket":
        return _delta_bucket(row.get("white_king_distance_delta"))
    if key == "rook_distance_delta_bucket":
        return _delta_bucket(row.get("rook_distance_delta"))
    if key == "black_king_edge_bucket":
        return _edge_bucket(row.get("black_king_edge_distance"))
    return str(row.get(key))


def _feature_key(row: dict[str, Any], keys: tuple[str, ...]) -> tuple[str, ...]:
    return tuple(_feature_value(row, key) for key in keys)


def _score(train: list[dict[str, Any]], row: dict[str, Any], keys: tuple[str, ...]) -> float:
    labeled = [item for item in train if _label_positive(item) is not None]
    global_positive = sum(1 for item in labeled if _label_positive(item))
    global_rate = global_positive / len(labeled) if labeled else 0.5
    counts: dict[tuple[str, ...], Counter[str]] = defaultdict(Counter)
    for item in labeled:
        label = _label_positive(item)
        if label is None:
            continue
        counts[_feature_key(item, keys)]["positive" if label else "negative"] += 1
    counter = counts.get(_feature_key(row, keys))
    if not counter:
        return global_rate
    total = counter["positive"] + counter["negative"]
    return counter["positive"] / total if total else global_rate


def _metrics(rows: list[dict[str, Any]], keys: tuple[str, ...]) -> dict[str, Any]:
    predictions = []
    for state_id in sorted({str(row.get("state_id")) for row in rows}):
        train = [row for row in rows if str(row.get("state_id")) != state_id]
        test = [row for row in rows if str(row.get("state_id")) == state_id]
        for row in test:
            label = _label_positive(row)
            if label is None:
                continue
            score = _score(train, row, keys)
            predictions.append({
                "state_id": row.get("state_id"),
                "provider_id": row.get("provider_id"),
                "capacity_label": row.get("capacity_label"),
                "score": score,
                "predicted_positive": score >= 0.5,
                "label_positive": label,
                "feature_key": list(_feature_key(row, keys)),
            })
    tp = sum(1 for item in predictions if item["predicted_positive"] and item["label_positive"])
    fp = sum(1 for item in predictions if item["predicted_positive"] and not item["label_positive"])
    tn = sum(1 for item in predictions if not item["predicted_positive"] and not item["label_positive"])
    fn = sum(1 for item in predictions if not item["predicted_positive"] and item["label_positive"])
    total = len(predictions)
    return {
        "row_count": total,
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
    geometry = _load(GEOMETRY)
    negative_evidence = _load(NEGATIVE_EVIDENCE)
    if geometry.get("causal_status") != "non_causal_feature_audit":
        raise ValueError("geometry audit must remain non-causal")
    if negative_evidence.get("causal_status") != "non_causal_evidence_audit":
        raise ValueError("negative evidence must remain non-causal")
    rows = [row for row in geometry.get("rows") or [] if _label_positive(row) is not None]
    specs = {
        "provider_family": ("provider_family",),
        "stage_provider_family": ("source_stage", "provider_family"),
        "provider_piece": ("provider_family", "forced_piece_type"),
        "provider_piece_king_delta": (
            "provider_family",
            "forced_piece_type",
            "white_king_distance_delta_bucket",
        ),
        "provider_piece_rook_delta": (
            "provider_family",
            "forced_piece_type",
            "rook_distance_delta_bucket",
        ),
        "stage_provider_piece_delta": (
            "source_stage",
            "provider_family",
            "forced_piece_type",
            "white_king_distance_delta_bucket",
            "rook_distance_delta_bucket",
        ),
        "edge_stage_provider_piece_delta": (
            "black_king_edge_bucket",
            "source_stage",
            "provider_family",
            "forced_piece_type",
            "white_king_distance_delta_bucket",
            "rook_distance_delta_bucket",
        ),
    }
    results = {name: _metrics(rows, keys) for name, keys in specs.items()}
    best_name, best_metrics = max(
        results.items(),
        key=lambda item: (
            item[1]["negative_suppression"] if item[1]["negative_suppression"] is not None else -1,
            item[1]["accuracy"] if item[1]["accuracy"] is not None else -1,
        ),
    )
    underpowered = len({row.get("state_id") for row in rows}) < 10 or len(rows) < 30
    status = "geometry_augmented_features_underpowered"
    recommendation = "collect_more_protected_capacity_rows_or_design_hard_negative_labels"
    if (best_metrics.get("negative_suppression") or 0.0) > 0.0:
        status = "geometry_augmented_features_improve_negative_suppression_underpowered"
        recommendation = "expand_geometry_feature_benchmark_before_runtime"
    if (best_metrics.get("negative_suppression") or 0.0) >= 0.7 and not underpowered:
        status = "geometry_augmented_features_promising_for_review"
        recommendation = "review_geometry_augmented_selector_sandbox_requirements"
    payload = {
        "schema_version": "krk_geometry_augmented_selector_feature_probe.v0",
        "causal_status": "non_causal_feature_probe",
        "runtime_behavior_changed": False,
        "runtime_defaults_changed": False,
        "runtime_selector_implemented": False,
        "runtime_candidate_generator_implemented": False,
        "runtime_terminals_added": False,
        "runtime_dtm_or_tablebase_lookup": False,
        "gameplay_topology_mutation": False,
        "stage7_promotion_allowed": False,
        "stage8_training_allowed": False,
        "source_artifacts": [str(GEOMETRY), str(NEGATIVE_EVIDENCE)],
        "summary": {
            "row_count": len(rows),
            "state_count": len({row.get("state_id") for row in rows}),
            "positive_count": sum(1 for row in rows if row.get("capacity_label") == "positive_capacity"),
            "negative_count": sum(1 for row in rows if row.get("capacity_label") == "negative_capacity"),
            "stage7_row_count": sum(1 for row in rows if row.get("source_stage") == "stage7"),
            "underpowered": underpowered,
        },
        "results": results,
        "best_result": {"objective": best_name, **{k: v for k, v in best_metrics.items() if k != "predictions"}},
        "interpretation": {
            "primary": (
                "Geometry features can be benchmarked, but the current protected capacity set is still too small "
                "for runtime conclusions."
            ),
            "directed_fix_class": "expand protected hard-negative capacity evidence and geometry-aware selector scoring non-causally",
        },
        "decision": {
            "status": status,
            "recommended_next_step": recommendation,
            "runtime_work_allowed": False,
            "candidate_generator_runtime_allowed": False,
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
        "# KRK Geometry-Augmented Selector Feature Probe v0",
        "",
        "This non-causal probe evaluates whether simple geometry terms improve protected capacity-label selection.",
        "",
        "## Summary",
        "",
    ]
    for key, value in payload["summary"].items():
        lines.append(f"- `{key}`: `{value}`")
    lines.extend(["", "## Results", ""])
    for name, result in payload["results"].items():
        lines.append(
            f"- `{name}` accuracy=`{result['accuracy']}` precision=`{result['positive_precision']}` "
            f"recall=`{result['positive_recall']}` negative_suppression=`{result['negative_suppression']}`"
        )
    lines.extend(["", "## Best Result", "", f"`{payload['best_result']}`", "", "## Interpretation", ""])
    for key, value in payload["interpretation"].items():
        lines.append(f"- `{key}`: `{value}`")
    lines.extend(["", "## Decision", ""])
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
