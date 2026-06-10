#!/usr/bin/env python3
"""Probe visible-ish selector-objective features over the v1 seed set."""

from __future__ import annotations

import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
MANIFEST = Path("reports/strategy_arbitration/krk_selector_objective_seed_manifest_v1.json")
SEED_PROBE = Path("reports/strategy_arbitration/krk_selector_objective_seed_probe_v1.json")
OUT_JSON = Path("reports/strategy_arbitration/krk_selector_objective_feature_probe_v0.json")
OUT_MD = Path("reports/strategy_arbitration/krk_selector_objective_feature_probe_v0.md")


FEATURE_SETS: dict[str, tuple[str, ...]] = {
    "source_stage": ("source_stage",),
    "selected_provider_family": ("selected_provider_family",),
    "trace_source_profile": ("trace_source_profile",),
    "positive_trace_count_bucket": ("positive_trace_count_bucket",),
    "stage_provider_family": ("source_stage", "selected_provider_family"),
    "stage_provider_trace_source": (
        "source_stage",
        "selected_provider_family",
        "trace_source_profile",
    ),
    "stage_provider_trace_count": (
        "source_stage",
        "selected_provider_family",
        "positive_trace_count_bucket",
    ),
}


def _load(path: Path) -> dict[str, Any]:
    payload = json.loads((ROOT / path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"expected JSON object: {path}")
    return payload


def _target_switch(row: dict[str, Any]) -> bool:
    return row.get("objective_channel") == "candidate_switch_contrast_seed"


def _trace_source_profile(row: dict[str, Any]) -> str:
    return "+".join(sorted(str(item) for item in row.get("trace_sources") or [])) or "none"


def _trace_count_bucket(row: dict[str, Any]) -> str:
    value = int(row.get("positive_trace_provider_candidate_count") or 0)
    if value <= 0:
        return "none"
    if value <= 3:
        return "low"
    if value <= 10:
        return "medium"
    return "high"


def _feature_value(row: dict[str, Any], key: str) -> str:
    if key == "trace_source_profile":
        return _trace_source_profile(row)
    if key == "positive_trace_count_bucket":
        return _trace_count_bucket(row)
    return str(row.get(key) or "")


def _feature_key(row: dict[str, Any], keys: tuple[str, ...]) -> tuple[str, ...]:
    return tuple(_feature_value(row, key) for key in keys)


def _score(train: list[dict[str, Any]], row: dict[str, Any], keys: tuple[str, ...]) -> float:
    if not train:
        return 0.0
    global_rate = sum(1 for item in train if _target_switch(item)) / len(train)
    counts: dict[tuple[str, ...], Counter[str]] = defaultdict(Counter)
    for item in train:
        counts[_feature_key(item, keys)]["switch" if _target_switch(item) else "preserve"] += 1
    counter = counts.get(_feature_key(row, keys))
    if not counter:
        return global_rate
    total = counter["switch"] + counter["preserve"]
    return counter["switch"] / total if total else global_rate


def _metrics(predictions: list[dict[str, Any]]) -> dict[str, Any]:
    tp = sum(1 for item in predictions if item["predicted_switch"] and item["target_switch"])
    fp = sum(1 for item in predictions if item["predicted_switch"] and not item["target_switch"])
    tn = sum(1 for item in predictions if not item["predicted_switch"] and not item["target_switch"])
    fn = sum(1 for item in predictions if not item["predicted_switch"] and item["target_switch"])
    total = len(predictions)
    return {
        "row_count": total,
        "true_positive": tp,
        "false_positive": fp,
        "true_negative": tn,
        "false_negative": fn,
        "accuracy": (tp + tn) / total if total else 0.0,
        "switch_precision": tp / (tp + fp) if tp + fp else None,
        "switch_recall": tp / (tp + fn) if tp + fn else 0.0,
        "preserve_recall": tn / (tn + fp) if tn + fp else 0.0,
        "predictions": predictions,
    }


def _feature_model(
    rows: list[dict[str, Any]],
    model_id: str,
    keys: tuple[str, ...],
    threshold: float,
) -> dict[str, Any]:
    predictions = []
    for state_id in sorted({str(row.get("state_id")) for row in rows}):
        train = [row for row in rows if str(row.get("state_id")) != state_id]
        test = [row for row in rows if str(row.get("state_id")) == state_id]
        for row in test:
            score = _score(train, row, keys)
            predictions.append(
                {
                    "state_id": row.get("state_id"),
                    "source_stage": row.get("source_stage"),
                    "selected_provider": row.get("selected_provider"),
                    "objective_channel": row.get("objective_channel"),
                    "feature_key": list(_feature_key(row, keys)),
                    "score": score,
                    "threshold": threshold,
                    "target_switch": _target_switch(row),
                    "predicted_switch": score >= threshold,
                    "runtime_feature_eligible": True,
                }
            )
    return {
        "model_id": model_id,
        "model_kind": "leave_state_out_feature_model",
        "features": list(keys),
        "threshold": threshold,
        "runtime_feature_eligible": True,
        **_metrics(predictions),
    }


def _offline_semantic_oracle(rows: list[dict[str, Any]]) -> dict[str, Any]:
    predictions = [
        {
            "state_id": row.get("state_id"),
            "source_stage": row.get("source_stage"),
            "selected_provider": row.get("selected_provider"),
            "objective_channel": row.get("objective_channel"),
            "target_switch": _target_switch(row),
            "predicted_switch": row.get("selected_owner_label") == "selected_owner_failed",
            "runtime_feature_eligible": False,
        }
        for row in rows
    ]
    return {
        "model_id": "offline_selected_owner_outcome_oracle",
        "model_kind": "offline_semantic_oracle",
        "runtime_feature_eligible": False,
        "notes": "Uses selected-owner outcome labels; confirms target semantics only.",
        **_metrics(predictions),
    }


def _passes_runtime_review_thresholds(result: dict[str, Any]) -> bool:
    return (
        result.get("runtime_feature_eligible") is True
        and (result.get("switch_recall") or 0.0) >= 0.70
        and (result.get("preserve_recall") or 0.0) >= 0.80
        and (result.get("switch_precision") or 0.0) >= 0.70
    )


def build_payload(
    manifest: dict[str, Any] | None = None,
    seed_probe: dict[str, Any] | None = None,
) -> dict[str, Any]:
    manifest = manifest or _load(MANIFEST)
    seed_probe = seed_probe or _load(SEED_PROBE)
    rows = [
        row
        for row in manifest.get("seed_rows") or []
        if isinstance(row, dict) and not row.get("stage7_training_row")
    ]
    results: dict[str, dict[str, Any]] = {}
    for name, keys in FEATURE_SETS.items():
        for threshold in (0.25, 0.5, 0.75):
            model_id = f"{name}@{threshold}"
            results[model_id] = _feature_model(rows, model_id, keys, threshold)
    results["offline_selected_owner_outcome_oracle"] = _offline_semantic_oracle(rows)
    runtime_results = [
        result for result in results.values() if result.get("runtime_feature_eligible")
    ]
    passing_runtime_results = [
        result for result in runtime_results if _passes_runtime_review_thresholds(result)
    ]
    best_runtime = max(
        runtime_results,
        key=lambda item: (
            item.get("switch_recall") or 0.0,
            item.get("preserve_recall") or 0.0,
            item.get("switch_precision") or 0.0,
            item.get("accuracy") or 0.0,
        ),
        default={},
    )
    target_counts = Counter(str(row.get("objective_channel") or "unknown") for row in rows)
    ready_for_review = bool(passing_runtime_results)
    return {
        "schema_version": "krk_selector_objective_feature_probe.v0",
        "causal_status": "non_causal_feature_probe",
        "runtime_behavior_changed": False,
        "runtime_defaults_changed": False,
        "runtime_selector_implemented": False,
        "runtime_score_changes": False,
        "runtime_direct_routing": False,
        "runtime_dtm_or_tablebase_lookup": False,
        "gameplay_topology_mutation": False,
        "stage7_promotion_allowed": False,
        "stage8_training_allowed": False,
        "source_artifacts": [str(MANIFEST), str(SEED_PROBE)],
        "summary": {
            "seed_row_count": len(rows),
            "target_channel_counts": dict(sorted(target_counts.items())),
            "runtime_feature_model_count": len(runtime_results),
            "runtime_threshold_passing_model_count": len(passing_runtime_results),
            "best_runtime_model": best_runtime.get("model_id"),
            "best_runtime_switch_recall": best_runtime.get("switch_recall"),
            "best_runtime_preserve_recall": best_runtime.get("preserve_recall"),
            "best_runtime_switch_precision": best_runtime.get("switch_precision"),
            "best_runtime_accuracy": best_runtime.get("accuracy"),
            "offline_oracle_accuracy": results[
                "offline_selected_owner_outcome_oracle"
            ].get("accuracy"),
            "selector_training_row_count": (manifest.get("summary") or {}).get(
                "selector_training_row_count"
            ),
            "stage7_training_row_count": (manifest.get("summary") or {}).get(
                "stage7_training_row_count"
            ),
            "seed_probe_status": (seed_probe.get("decision") or {}).get("status"),
        },
        "results": results,
        "interpretation": {
            "selector_feature_probe_ready_for_review": ready_for_review,
            "selector_training_supported": False,
            "runtime_selector_supported": False,
            "offline_semantics_confirmed": results[
                "offline_selected_owner_outcome_oracle"
            ].get("accuracy")
            == 1.0,
            "reason": (
                "The seed set is now large enough to probe visible features, but "
                "simple visible feature keys do not yet constitute selector training "
                "or runtime selector authorization."
            ),
        },
        "decision": {
            "status": (
                "selector_objective_feature_probe_review_ready"
                if ready_for_review
                else "selector_objective_feature_probe_no_runtime_ready_features"
            ),
            "selector_allowed": False,
            "selector_training_allowed": False,
            "runtime_changes_allowed": False,
            "recommended_next_step": (
                "write_selector_feature_probe_review_packet"
                if ready_for_review
                else "collect_more_diverse_joined_trace_ownership_evidence"
            ),
        },
    }


def write_markdown(payload: dict[str, Any]) -> None:
    summary = payload["summary"]
    lines = [
        "# KRK Selector Objective Feature Probe v0",
        "",
        "This non-causal probe tests simple visible feature keys over the v1 selector-objective seed set. It does not train or authorize a selector.",
        "",
        "## Decision",
        "",
        f"- status: `{payload['decision']['status']}`",
        f"- selector_allowed: `{payload['decision']['selector_allowed']}`",
        f"- runtime_changes_allowed: `{payload['decision']['runtime_changes_allowed']}`",
        f"- recommended_next_step: `{payload['decision']['recommended_next_step']}`",
        "",
        "## Summary",
        "",
    ]
    for key, value in summary.items():
        lines.append(f"- {key}: `{value}`")
    lines.extend(["", "## Interpretation", ""])
    for key, value in payload["interpretation"].items():
        lines.append(f"- {key}: `{value}`")
    lines.extend(["", "## Runtime Feature Models", ""])
    for model_id, result in sorted(payload["results"].items()):
        if not result.get("runtime_feature_eligible"):
            continue
        lines.append(
            "- "
            f"`{model_id}` "
            f"switch_recall={result.get('switch_recall')} "
            f"preserve_recall={result.get('preserve_recall')} "
            f"switch_precision={result.get('switch_precision')} "
            f"accuracy={result.get('accuracy')}"
        )
    (ROOT / OUT_MD).write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    payload = build_payload()
    (ROOT / OUT_JSON).write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    write_markdown(payload)
    print(json.dumps(payload["decision"], indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
