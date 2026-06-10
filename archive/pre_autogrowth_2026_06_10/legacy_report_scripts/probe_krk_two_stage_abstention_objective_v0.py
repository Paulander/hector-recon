#!/usr/bin/env python3
"""Probe a two-stage abstention objective without implementing runtime behavior."""

from __future__ import annotations

import json
import sys
from collections import Counter
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))

import probe_krk_abstention_context_feature_dataset_v0 as context_probe  # noqa: E402


ROOT = Path(__file__).resolve().parents[1]
DATASET = Path("reports/krk_abstention_context_feature_dataset_v0.json")
LABEL_REVIEW = Path("reports/krk_abstention_safe_preservation_label_review_v0.json")
OUT_JSON = Path("reports/krk_two_stage_abstention_objective_probe_v0.json")
OUT_MD = Path("reports/krk_two_stage_abstention_objective_probe_v0.md")


UNSAFE_SPECS: dict[str, tuple[str, ...]] = {
    "king_support_provider_family": ("terminal_space_context.white_king_support_bucket", "provider_family"),
    "monitor_signature_provider_family": ("monitor_context.monitor_signature", "provider_family"),
    "repair_monitor_provider_family": ("monitor_context.has_repair_needed_monitor", "provider_family"),
}
PRESERVE_SPECS: dict[str, tuple[str, ...]] = {
    "provider_family": ("provider_family",),
    "support_provider_family": ("terminal_space_context.white_king_support_bucket", "provider_family"),
    "monitor_provider_family": ("monitor_context.monitor_signature", "provider_family"),
    "repair_monitor_provider_family": ("monitor_context.has_repair_needed_monitor", "provider_family"),
}
UNSAFE_THRESHOLDS = (0.45, 0.5, 0.55, 0.6)
PRESERVE_THRESHOLDS = (0.5, 0.6, 0.7, 0.8)


def _load_json(root: Path, path: Path) -> dict[str, Any]:
    payload = json.loads((root / path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"expected JSON object: {path}")
    return payload


def _unsafe(row: dict[str, Any]) -> bool:
    return row.get("label") == "unsafe_owner" or row.get("label_unsafe") is True


def _predict_rows(
    rows: list[dict[str, Any]],
    unsafe_keys: tuple[str, ...],
    preserve_keys: tuple[str, ...],
    unsafe_threshold: float,
    preserve_threshold: float,
) -> list[dict[str, Any]]:
    predictions = []
    for state in sorted({str(row.get("state_id")) for row in rows}):
        test = [row for row in rows if str(row.get("state_id")) == state]
        train = [row for row in rows if str(row.get("state_id")) != state]
        for row in test:
            unsafe_score = context_probe._score_unsafe(train, row, unsafe_keys)
            preserve_score = 1.0 - context_probe._score_unsafe(train, row, preserve_keys)
            predicted_unsafe = unsafe_score >= unsafe_threshold and preserve_score < preserve_threshold
            label_unsafe = _unsafe(row)
            predictions.append({
                "state_id": row.get("state_id"),
                "source_stage": row.get("source_stage"),
                "provider_id": row.get("provider_id"),
                "provider_family": row.get("provider_family"),
                "label_source_kind": row.get("label_source_kind"),
                "unsafe_score": unsafe_score,
                "preserve_score": preserve_score,
                "predicted_unsafe": predicted_unsafe,
                "label_unsafe": label_unsafe,
                "error_type": (
                    "false_positive_safe_owner_rejected"
                    if predicted_unsafe and not label_unsafe
                    else "false_negative_unsafe_owner_allowed"
                    if not predicted_unsafe and label_unsafe
                    else "true_positive_unsafe_owner_rejected"
                    if predicted_unsafe and label_unsafe
                    else "true_negative_safe_owner_allowed"
                ),
            })
    return predictions


def _probe_spec(
    rows: list[dict[str, Any]],
    unsafe_name: str,
    unsafe_keys: tuple[str, ...],
    preserve_name: str,
    preserve_keys: tuple[str, ...],
    unsafe_threshold: float,
    preserve_threshold: float,
) -> dict[str, Any]:
    predictions = _predict_rows(rows, unsafe_keys, preserve_keys, unsafe_threshold, preserve_threshold)
    metrics = context_probe._metrics(predictions)
    errors = Counter(item["error_type"] for item in predictions)
    return {
        "objective_id": f"{unsafe_name}__preserve_{preserve_name}__u{unsafe_threshold:g}_p{preserve_threshold:g}",
        "unsafe_features": unsafe_keys,
        "preserve_features": preserve_keys,
        "unsafe_threshold": unsafe_threshold,
        "preserve_threshold": preserve_threshold,
        **metrics,
        "error_counts": dict(errors),
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
        raise ValueError("two-stage abstention probe must not authorize runtime tests directly")


def build_probe(root: Path = ROOT) -> dict[str, Any]:
    dataset = _load_json(root, DATASET)
    review = _load_json(root, LABEL_REVIEW)
    if dataset.get("causal_status") != "non_causal_context_feature_dataset":
        raise ValueError("context feature dataset must remain non-causal")
    if review.get("causal_status") != "non_causal_architecture_review":
        raise ValueError("safe-preservation review must remain non-causal")

    rows = [
        row
        for row in dataset.get("rows") or []
        if row.get("usable_for_training") is True and row.get("source_stage") != "stage7"
    ]
    results = []
    for unsafe_name, unsafe_keys in UNSAFE_SPECS.items():
        for preserve_name, preserve_keys in PRESERVE_SPECS.items():
            for unsafe_threshold in UNSAFE_THRESHOLDS:
                for preserve_threshold in PRESERVE_THRESHOLDS:
                    results.append(_probe_spec(
                        rows,
                        unsafe_name,
                        unsafe_keys,
                        preserve_name,
                        preserve_keys,
                        unsafe_threshold,
                        preserve_threshold,
                    ))
    best = max(
        results,
        key=lambda result: (
            result["negative_suppression"] if result["negative_suppression"] is not None else -1.0,
            result["safe_preservation"] if result["safe_preservation"] is not None else -1.0,
            result["accuracy"] if result["accuracy"] is not None else -1.0,
        ),
    )
    threshold_passing = [
        result for result in results
        if (result.get("negative_suppression") or 0.0) >= 0.7
        and (result.get("safe_preservation") or 0.0) >= 0.75
    ]
    best_passing = max(
        threshold_passing,
        key=lambda result: (
            result["safe_preservation"] if result["safe_preservation"] is not None else -1.0,
            result["negative_suppression"] if result["negative_suppression"] is not None else -1.0,
            result["accuracy"] if result["accuracy"] is not None else -1.0,
        ),
        default=None,
    )
    status = (
        "two_stage_abstention_signal_present_runtime_review_required"
        if best_passing
        else "two_stage_abstention_signal_insufficient_runtime_blocked"
    )
    payload = {
        "schema_version": "krk_two_stage_abstention_objective_probe.v0",
        "causal_status": "non_causal_offline_probe",
        "runtime_behavior_changed": False,
        "runtime_defaults_changed": False,
        "runtime_selector_implemented": False,
        "runtime_dtm_or_tablebase_lookup": False,
        "gameplay_topology_mutation": False,
        "stage7_promotion_allowed": False,
        "stage8_training_allowed": False,
        "source_artifacts": [str(DATASET), str(LABEL_REVIEW)],
        "summary": {
            "row_count": len(rows),
            "state_count": len({row.get("state_id") for row in rows}),
            "label_counts": dict(Counter(str(row.get("label")) for row in rows)),
            "stage_counts": dict(Counter(str(row.get("source_stage")) for row in rows)),
            "objective_count": len(results),
            "threshold_passing_objective_count": len(threshold_passing),
            "runtime_review_thresholds": {
                "minimum_negative_suppression": 0.7,
                "minimum_safe_preservation": 0.75,
            },
        },
        "best_by_negative_suppression": best,
        "best_threshold_passing_result": best_passing,
        "top_results": sorted(
            results,
            key=lambda result: (
                result["safe_preservation"] if result["safe_preservation"] is not None else -1.0,
                result["negative_suppression"] if result["negative_suppression"] is not None else -1.0,
            ),
            reverse=True,
        )[:10],
        "decision": {
            "status": status,
            "recommended_next_step": (
                "architecture_review_before_default_off_runtime_selector"
                if best_passing
                else "refine_two_stage_abstention_labels_non_causal"
            ),
            "runtime_test_allowed_next": False,
            "stage7_promotion_allowed": False,
            "stage8_training_allowed": False,
        },
    }
    validate_probe(payload)
    return payload


def render_markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# KRK Two-Stage Abstention Objective Probe v0",
        "",
        "This offline probe evaluates whether an abstention objective can first preserve safe owners and then suppress unsafe owners. It does not implement a runtime selector.",
        "",
        "## Summary",
        "",
    ]
    for key, value in payload["summary"].items():
        lines.append(f"- `{key}`: `{value}`")
    lines.extend(["", "## Best Threshold-Passing Result", ""])
    lines.append(f"`{payload['best_threshold_passing_result']}`")
    lines.extend(["", "## Best By Negative Suppression", ""])
    lines.append(f"`{payload['best_by_negative_suppression']}`")
    lines.extend(["", "## Decision", ""])
    lines.append(f"- Status: `{payload['decision']['status']}`")
    lines.append(f"- Recommended next step: `{payload['decision']['recommended_next_step']}`")
    lines.append(f"- Runtime test allowed next: `{payload['decision']['runtime_test_allowed_next']}`")
    lines.append(f"- Stage 7 promotion allowed: `{payload['decision']['stage7_promotion_allowed']}`")
    lines.append(f"- Stage 8 training allowed: `{payload['decision']['stage8_training_allowed']}`")
    lines.append("")
    return "\n".join(lines)


def main() -> None:
    payload = build_probe()
    (ROOT / OUT_JSON).write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (ROOT / OUT_MD).write_text(render_markdown(payload), encoding="utf-8")
    print(json.dumps(payload["decision"], indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
