#!/usr/bin/env python3
"""Probe replay-free abstention context features."""

from __future__ import annotations

import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DATASET = Path("reports/krk_abstention_context_feature_dataset_v0.json")
OUT_JSON = Path("reports/krk_abstention_context_feature_probe_v0.json")
OUT_MD = Path("reports/krk_abstention_context_feature_probe_v0.md")


def _load_json(root: Path, path: Path) -> dict[str, Any]:
    payload = json.loads((root / path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"expected JSON object: {path}")
    return payload


def _unsafe(row: dict[str, Any]) -> bool:
    return row.get("label") == "unsafe_owner" or row.get("label_unsafe") is True


def _feature_value(row: dict[str, Any], key: str) -> str:
    if "." not in key:
        return str(row.get(key))
    value: Any = row
    for part in key.split("."):
        if not isinstance(value, dict):
            return "None"
        value = value.get(part)
    if isinstance(value, list):
        return "+".join(str(item) for item in value) if value else "none"
    return str(value)


def _score_unsafe(train: list[dict[str, Any]], row: dict[str, Any], keys: tuple[str, ...]) -> float:
    global_rate = sum(1 for item in train if _unsafe(item)) / len(train) if train else 0.5
    counts: dict[tuple[str, ...], Counter[str]] = defaultdict(Counter)
    for item in train:
        bucket = tuple(_feature_value(item, key) for key in keys)
        counts[bucket]["unsafe" if _unsafe(item) else "safe"] += 1
    row_bucket = tuple(_feature_value(row, key) for key in keys)
    counter = counts.get(row_bucket)
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
            unsafe_score = _score_unsafe(train, row, keys)
            predictions.append({
                "state_id": row.get("state_id"),
                "provider_id": row.get("provider_id"),
                "keys": keys,
                "unsafe_score": unsafe_score,
                "predicted_unsafe": unsafe_score >= 0.5,
                "label_unsafe": _unsafe(row),
            })
    return _metrics(predictions)


def _feature_stats(rows: list[dict[str, Any]], key: str) -> dict[str, Any]:
    counts: dict[str, Counter[str]] = defaultdict(Counter)
    for row in rows:
        value = _feature_value(row, key)
        counts[value]["unsafe" if _unsafe(row) else "safe"] += 1
    return {
        value: {
            "safe": counter["safe"],
            "unsafe": counter["unsafe"],
            "unsafe_rate": counter["unsafe"] / (counter["safe"] + counter["unsafe"]),
        }
        for value, counter in sorted(counts.items())
    }


def validate_probe(payload: dict[str, Any]) -> None:
    for key in (
        "runtime_behavior_changed",
        "runtime_defaults_changed",
        "runtime_selector_implemented",
        "runtime_dtm_or_tablebase_lookup",
        "gameplay_topology_mutation",
        "stage7_promotion_allowed",
        "stage8_training_allowed",
    ):
        if payload.get(key) is not False:
            raise ValueError(f"{key} must be false")
    if payload["decision"]["runtime_test_allowed_next"] is not False:
        raise ValueError("context feature probe must not authorize runtime testing")


def build_probe(root: Path = ROOT) -> dict[str, Any]:
    dataset = _load_json(root, DATASET)
    if dataset.get("causal_status") != "non_causal_context_feature_dataset":
        raise ValueError("context feature dataset must remain non-causal")
    rows = [
        row
        for row in dataset.get("rows") or []
        if row.get("usable_for_training") is True and row.get("source_stage") != "stage7"
    ]
    objective_specs: dict[str, tuple[str, ...]] = {
        "provider_family": ("provider_family",),
        "stage_provider_family": ("source_stage", "provider_family"),
        "edge_bucket_provider_family": ("terminal_space_context.black_king_edge_bucket", "provider_family"),
        "box_relevance_provider_family": ("terminal_space_context.box_area_relevance", "provider_family"),
        "king_support_provider_family": ("terminal_space_context.white_king_support_bucket", "provider_family"),
        "monitor_signature_provider_family": ("monitor_context.monitor_signature", "provider_family"),
        "repair_monitor_provider_family": ("monitor_context.has_repair_needed_monitor", "provider_family"),
        "proposal_match_provider_family": ("proposal_context.matched_proposal", "provider_family"),
        "label_source_provider_family": ("label_source_kind", "provider_family"),
        "context_combo_provider_family": (
            "source_stage",
            "terminal_space_context.black_king_edge_bucket",
            "terminal_space_context.box_area_relevance",
            "monitor_context.has_repair_needed_monitor",
            "provider_family",
        ),
    }
    results = {
        name: {"features": keys, **_leave_state_out(rows, keys)}
        for name, keys in objective_specs.items()
    }
    baseline = results["provider_family"]
    best_name, best_metrics = max(
        results.items(),
        key=lambda item: (
            item[1]["negative_suppression"] if item[1]["negative_suppression"] is not None else -1.0,
            item[1]["safe_preservation"] if item[1]["safe_preservation"] is not None else -1.0,
        ),
    )
    best_negative = best_metrics.get("negative_suppression") or 0.0
    best_safe = best_metrics.get("safe_preservation") or 0.0
    baseline_negative = baseline.get("negative_suppression") or 0.0
    context_improved = best_negative > baseline_negative
    ready = best_negative >= 0.7 and best_safe >= 0.7
    if ready:
        status = "context_abstention_signal_review_ready_runtime_still_blocked"
        recommended = "architecture_review_before_any_default_off_runtime_selector"
    elif context_improved:
        status = "context_features_help_but_runtime_blocked"
        recommended = "refine_context_labels_or_features_non_causal_only"
    else:
        status = "context_features_do_not_improve_abstention_no_runtime"
        recommended = "architecture_review_before_collecting_more_context_features"

    feature_stats = {
        key: _feature_stats(rows, key)
        for key in (
            "terminal_space_context.black_king_edge_bucket",
            "terminal_space_context.box_area_relevance",
            "terminal_space_context.white_king_support_bucket",
            "monitor_context.monitor_signature",
            "monitor_context.has_repair_needed_monitor",
            "proposal_context.matched_proposal",
            "label_source_kind",
        )
    }
    payload = {
        "schema_version": "krk_abstention_context_feature_probe.v0",
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
            "label_counts": dict(Counter(str(row.get("label")) for row in rows)),
            "stage_counts": dict(Counter(str(row.get("source_stage")) for row in rows)),
            "baseline_negative_suppression": baseline.get("negative_suppression"),
            "best_negative_suppression": best_metrics.get("negative_suppression"),
            "best_safe_preservation": best_metrics.get("safe_preservation"),
            "context_improved_negative_suppression": context_improved,
        },
        "results": results,
        "best_result": {"objective": best_name, **best_metrics},
        "feature_stats": feature_stats,
        "decision": {
            "status": status,
            "recommended_next_step": recommended,
            "runtime_test_allowed_next": False,
            "stage7_promotion_allowed": False,
            "stage8_training_allowed": False,
        },
    }
    validate_probe(payload)
    return payload


def render_markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# KRK Abstention Context Feature Probe v0",
        "",
        "This offline probe tests whether replay-free state context improves abstention labels over provider-family provenance. It does not implement a runtime selector.",
        "",
        "## Summary",
        "",
    ]
    for key, value in payload["summary"].items():
        lines.append(f"- `{key}`: `{value}`")
    lines.extend(["", "## Results", ""])
    for name, metrics in payload["results"].items():
        lines.append(
            f"- `{name}` negative_suppression=`{metrics['negative_suppression']}` "
            f"safe_preservation=`{metrics['safe_preservation']}` accuracy=`{metrics['accuracy']}`"
        )
    lines.extend([
        "",
        "## Best Result",
        "",
        f"`{payload['best_result']}`",
        "",
        "## Decision",
        "",
        f"- Status: `{payload['decision']['status']}`",
        f"- Recommended next step: `{payload['decision']['recommended_next_step']}`",
        f"- Runtime test allowed next: `{payload['decision']['runtime_test_allowed_next']}`",
        f"- Stage 7 promotion allowed: `{payload['decision']['stage7_promotion_allowed']}`",
        f"- Stage 8 training allowed: `{payload['decision']['stage8_training_allowed']}`",
        "",
    ])
    return "\n".join(lines)


def main() -> None:
    payload = build_probe()
    (ROOT / OUT_JSON).write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (ROOT / OUT_MD).write_text(render_markdown(payload), encoding="utf-8")
    print(json.dumps(payload["decision"], indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
