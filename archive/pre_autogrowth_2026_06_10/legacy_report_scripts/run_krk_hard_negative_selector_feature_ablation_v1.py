#!/usr/bin/env python3
"""Run expanded offline hard-negative selector feature ablation."""

from __future__ import annotations

import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
TARGETS = Path("reports/krk_hard_negative_selector_target_dataset_v1.json")
OUT_JSON = Path("reports/krk_hard_negative_selector_feature_ablation_v1.json")
OUT_MD = Path("reports/krk_hard_negative_selector_feature_ablation_v1.md")


def _load(path: Path) -> dict[str, Any]:
    payload = json.loads((ROOT / path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"expected JSON object: {path}")
    return payload


def _label_positive(row: dict[str, Any]) -> bool | None:
    target = row.get("target_kind")
    if target == "positive_capacity_context":
        return True
    if target == "hard_negative_capacity":
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
    if not isinstance(value, int):
        return "missing"
    if value == 0:
        return "edge"
    if value == 1:
        return "near_edge"
    return "centerish"


def _reply_count_bucket(value: Any) -> str:
    if not isinstance(value, int):
        return "missing"
    if value <= 3:
        return "low"
    if value <= 8:
        return "medium"
    return "high"


def _feature_value(row: dict[str, Any], key: str) -> str:
    if key == "white_king_distance_delta_bucket":
        return _delta_bucket(row.get("white_king_distance_delta"))
    if key == "rook_distance_delta_bucket":
        return _delta_bucket(row.get("rook_distance_delta"))
    if key == "black_king_edge_bucket":
        return _edge_bucket(row.get("black_king_edge_distance"))
    if key == "black_king_reply_count_bucket":
        return _reply_count_bucket(row.get("black_king_legal_reply_count_after"))
    if key in (
        "king_moves_toward_black",
        "rook_moves_toward_black",
        "rook_same_file_as_black_after",
        "rook_same_rank_as_black_after",
    ):
        return str(bool(row.get(key)))
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


def _metrics(rows: list[dict[str, Any]], keys: tuple[str, ...], threshold: float) -> dict[str, Any]:
    predictions = []
    for state_id in sorted({str(row.get("state_id")) for row in rows}):
        train = [row for row in rows if str(row.get("state_id")) != state_id]
        test = [row for row in rows if str(row.get("state_id")) == state_id]
        for row in test:
            label = _label_positive(row)
            if label is None:
                continue
            score = _score(train, row, keys)
            predictions.append(
                {
                    "state_id": row.get("state_id"),
                    "source_stage": row.get("source_stage"),
                    "provider_id": row.get("provider_id"),
                    "provider_family": row.get("provider_family"),
                    "target_kind": row.get("target_kind"),
                    "score": score,
                    "threshold": threshold,
                    "predicted_positive": score >= threshold,
                    "label_positive": label,
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


def build_ablation() -> dict[str, Any]:
    targets = _load(TARGETS)
    if targets.get("causal_status") != "non_causal_target_dataset":
        raise ValueError("targets must remain non-causal")
    if not (targets.get("decision") or {}).get("offline_benchmark_allowed"):
        raise ValueError("offline benchmark must be explicitly allowed by target dataset")
    rows = [row for row in targets.get("rows") or [] if _label_positive(row) is not None]
    specs = {
        "provider_family": ("provider_family",),
        "stage_provider_family": ("source_stage", "provider_family"),
        "provider_piece": ("provider_family", "forced_piece_type"),
        "provider_piece_king_delta": ("provider_family", "forced_piece_type", "white_king_distance_delta_bucket"),
        "provider_piece_rook_delta": ("provider_family", "forced_piece_type", "rook_distance_delta_bucket"),
        "stage_provider_piece_delta": (
            "source_stage",
            "provider_family",
            "forced_piece_type",
            "white_king_distance_delta_bucket",
            "rook_distance_delta_bucket",
        ),
        "stage_provider_edge_reply": (
            "source_stage",
            "provider_family",
            "black_king_edge_bucket",
            "black_king_reply_count_bucket",
        ),
        "provider_alignment_flags": (
            "provider_family",
            "king_moves_toward_black",
            "rook_moves_toward_black",
            "rook_same_file_as_black_after",
            "rook_same_rank_as_black_after",
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
    underpowered = (
        len({row.get("state_id") for row in rows}) < 12
        or len(rows) < 30
        or sum(1 for row in rows if _label_positive(row) is False) < 12
    )
    status = "hard_negative_feature_ablation_still_not_runtime_ready"
    recommendation = "collect_more_balanced_protected_hard_negatives_or_review_label_semantics"
    if (best.get("negative_suppression") or 0.0) > 0.0 and (best.get("positive_recall") or 0.0) >= 0.7:
        status = "hard_negative_feature_ablation_promising_underpowered"
        recommendation = "review_promising_offline_signal_before_any_selector_training"
    payload = {
        "schema_version": "krk_hard_negative_selector_feature_ablation.v1",
        "causal_status": "non_causal_feature_ablation",
        "runtime_behavior_changed": False,
        "runtime_defaults_changed": False,
        "runtime_selector_implemented": False,
        "runtime_candidate_generator_implemented": False,
        "runtime_terminals_added": False,
        "runtime_dtm_or_tablebase_lookup": False,
        "gameplay_topology_mutation": False,
        "stage7_promotion_allowed": False,
        "stage8_training_allowed": False,
        "source_artifacts": [str(TARGETS)],
        "summary": {
            "row_count": len(rows),
            "state_count": len({row.get("state_id") for row in rows}),
            "positive_context_count": sum(1 for row in rows if _label_positive(row)),
            "hard_negative_count": sum(1 for row in rows if _label_positive(row) is False),
            "hard_negative_state_count": len(
                {row.get("state_id") for row in rows if _label_positive(row) is False}
            ),
            "stage7_row_count": sum(1 for row in rows if row.get("source_stage") == "stage7"),
            "underpowered": underpowered,
        },
        "results": results,
        "best_result": {"objective": best_name, **{k: v for k, v in best.items() if k != "predictions"}},
        "interpretation": {
            "primary": "This remains an offline feature ablation; no selector training or runtime use is authorized.",
            "evidence_delta": "The balanced label run adds protected negative diversity, but runtime work still requires a reviewed, robust suppression/preservation signal.",
        },
        "decision": {
            "status": status,
            "recommended_next_step": recommendation,
            "runtime_work_allowed": False,
            "selector_training_allowed": False,
            "stage7_promotion_allowed": False,
            "stage8_training_allowed": False,
        },
    }
    validate_ablation(payload)
    return payload


def validate_ablation(payload: dict[str, Any]) -> None:
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
        "# KRK Hard-Negative Selector Feature Ablation v1",
        "",
        "Expanded offline ablation after balanced protected hard-negative label collection.",
        "",
        "## Summary",
        "",
    ]
    for key, value in payload["summary"].items():
        lines.append(f"- `{key}`: `{value}`")
    lines.extend(["", "## Results", ""])
    for name, result in payload["results"].items():
        lines.append(
            f"- `{name}` accuracy=`{result['accuracy']}` recall=`{result['positive_recall']}` "
            f"negative_suppression=`{result['negative_suppression']}`"
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
    payload = build_ablation()
    (ROOT / OUT_JSON).write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (ROOT / OUT_MD).write_text(render_markdown(payload), encoding="utf-8")
    print(json.dumps(payload["decision"], indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
