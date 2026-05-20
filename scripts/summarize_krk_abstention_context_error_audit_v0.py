#!/usr/bin/env python3
"""Summarize false-positive/false-negative patterns in the abstention context probe."""

from __future__ import annotations

import json
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))

import probe_krk_abstention_context_feature_dataset_v0 as probe  # noqa: E402


ROOT = Path(__file__).resolve().parents[1]
DATASET = Path("reports/krk_abstention_context_feature_dataset_v0.json")
PROBE = Path("reports/krk_abstention_context_feature_probe_v0.json")
OUT_JSON = Path("reports/krk_abstention_context_error_audit_v0.json")
OUT_MD = Path("reports/krk_abstention_context_error_audit_v0.md")


def _load_json(root: Path, path: Path) -> dict[str, Any]:
    payload = json.loads((root / path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"expected JSON object: {path}")
    return payload


def _unsafe(row: dict[str, Any]) -> bool:
    return row.get("label") == "unsafe_owner" or row.get("label_unsafe") is True


def _predictions(rows: list[dict[str, Any]], keys: tuple[str, ...]) -> list[dict[str, Any]]:
    predictions = []
    for state in sorted({str(row.get("state_id")) for row in rows}):
        test = [row for row in rows if str(row.get("state_id")) == state]
        train = [row for row in rows if str(row.get("state_id")) != state]
        for row in test:
            unsafe_score = probe._score_unsafe(train, row, keys)
            label_unsafe = _unsafe(row)
            predicted_unsafe = unsafe_score >= 0.5
            predictions.append({
                "state_id": row.get("state_id"),
                "source_stage": row.get("source_stage"),
                "active_landmark_label": row.get("active_landmark_label"),
                "provider_id": row.get("provider_id"),
                "provider_family": row.get("provider_family"),
                "move_uci": row.get("move_uci"),
                "label": row.get("label"),
                "label_source_kind": row.get("label_source_kind"),
                "forced_result": row.get("forced_result"),
                "unsafe_score": unsafe_score,
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
                "terminal_context": row.get("terminal_space_context") or {},
                "monitor_signature": (row.get("monitor_context") or {}).get("monitor_signature"),
                "has_repair_needed_monitor": (row.get("monitor_context") or {}).get("has_repair_needed_monitor"),
                "matched_proposal": (row.get("proposal_context") or {}).get("matched_proposal"),
            })
    return predictions


def _counter_by(items: list[dict[str, Any]], key: str) -> dict[str, int]:
    return dict(Counter(str(item.get(key)) for item in items))


def _nested_counter(items: list[dict[str, Any]], key_path: tuple[str, ...]) -> dict[str, int]:
    counts: Counter[str] = Counter()
    for item in items:
        value: Any = item
        for key in key_path:
            if not isinstance(value, dict):
                value = None
                break
            value = value.get(key)
        counts[str(value)] += 1
    return dict(counts)


def _examples(items: list[dict[str, Any]], limit: int = 8) -> list[dict[str, Any]]:
    return [
        {
            "state_id": item.get("state_id"),
            "source_stage": item.get("source_stage"),
            "provider_id": item.get("provider_id"),
            "move_uci": item.get("move_uci"),
            "label": item.get("label"),
            "label_source_kind": item.get("label_source_kind"),
            "unsafe_score": item.get("unsafe_score"),
            "support_bucket": (item.get("terminal_context") or {}).get("white_king_support_bucket"),
            "monitor_signature": item.get("monitor_signature"),
        }
        for item in items[:limit]
    ]


def validate_audit(payload: dict[str, Any]) -> None:
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
        raise ValueError("error audit must not authorize runtime testing")


def build_audit(root: Path = ROOT) -> dict[str, Any]:
    dataset = _load_json(root, DATASET)
    probe_payload = _load_json(root, PROBE)
    if dataset.get("causal_status") != "non_causal_context_feature_dataset":
        raise ValueError("context feature dataset must remain non-causal")
    if probe_payload.get("causal_status") != "non_causal_offline_probe":
        raise ValueError("context feature probe must remain non-causal")

    rows = [
        row
        for row in dataset.get("rows") or []
        if row.get("usable_for_training") is True and row.get("source_stage") != "stage7"
    ]
    best = probe_payload.get("best_result") or {}
    features = tuple(str(feature) for feature in best.get("features") or ())
    if not features:
        raise ValueError("probe best result must include features")
    predictions = _predictions(rows, features)
    by_type: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for item in predictions:
        by_type[item["error_type"]].append(item)

    false_positives = by_type["false_positive_safe_owner_rejected"]
    false_negatives = by_type["false_negative_unsafe_owner_allowed"]
    true_positives = by_type["true_positive_unsafe_owner_rejected"]
    true_negatives = by_type["true_negative_safe_owner_allowed"]
    summary = {
        "row_count": len(predictions),
        "best_objective": best.get("objective"),
        "best_features": list(features),
        "false_positive_count": len(false_positives),
        "false_negative_count": len(false_negatives),
        "true_positive_count": len(true_positives),
        "true_negative_count": len(true_negatives),
        "negative_suppression": best.get("negative_suppression"),
        "safe_preservation": best.get("safe_preservation"),
    }
    error_patterns = {
        "false_positive_by_stage": _counter_by(false_positives, "source_stage"),
        "false_positive_by_provider_family": _counter_by(false_positives, "provider_family"),
        "false_positive_by_label_source_kind": _counter_by(false_positives, "label_source_kind"),
        "false_positive_by_support_bucket": _nested_counter(false_positives, ("terminal_context", "white_king_support_bucket")),
        "false_positive_by_monitor_signature": _counter_by(false_positives, "monitor_signature"),
        "false_negative_by_stage": _counter_by(false_negatives, "source_stage"),
        "false_negative_by_provider_family": _counter_by(false_negatives, "provider_family"),
        "false_negative_by_label_source_kind": _counter_by(false_negatives, "label_source_kind"),
        "false_negative_by_support_bucket": _nested_counter(false_negatives, ("terminal_context", "white_king_support_bucket")),
        "false_negative_by_monitor_signature": _counter_by(false_negatives, "monitor_signature"),
    }
    diagnosis = [
        "Context features substantially improve unsafe-owner recall, but they over-reject safe owners.",
        "The strongest feature uses white-king support bucket plus provider family; this is useful evidence but not a safe runtime abstention rule.",
        "Safe-preservation misses the runtime-review threshold, so any runtime selector remains blocked.",
    ]
    if false_positives:
        diagnosis.append("False positives should be analyzed before collecting more labels: the current objective suppresses too many known-safe owners.")
    payload = {
        "schema_version": "krk_abstention_context_error_audit.v0",
        "causal_status": "non_causal_error_audit",
        "runtime_behavior_changed": False,
        "runtime_defaults_changed": False,
        "runtime_selector_implemented": False,
        "runtime_dtm_or_tablebase_lookup": False,
        "gameplay_topology_mutation": False,
        "stage7_promotion_allowed": False,
        "stage8_training_allowed": False,
        "source_artifacts": [str(DATASET), str(PROBE)],
        "summary": summary,
        "error_patterns": error_patterns,
        "examples": {
            "false_positives": _examples(false_positives),
            "false_negatives": _examples(false_negatives),
            "true_positives": _examples(true_positives),
            "true_negatives": _examples(true_negatives),
        },
        "diagnosis": diagnosis,
        "decision": {
            "status": "context_signal_overrejects_safe_owners_runtime_blocked",
            "recommended_next_step": "non_causal_safe_preservation_label_semantics_review",
            "runtime_test_allowed_next": False,
            "stage7_promotion_allowed": False,
            "stage8_training_allowed": False,
        },
    }
    validate_audit(payload)
    return payload


def render_markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# KRK Abstention Context Error Audit v0",
        "",
        "This replay-free audit explains why the context-feature abstention probe remains blocked. It does not implement a runtime selector.",
        "",
        "## Summary",
        "",
    ]
    for key, value in payload["summary"].items():
        lines.append(f"- `{key}`: `{value}`")
    lines.extend(["", "## Diagnosis", ""])
    for item in payload["diagnosis"]:
        lines.append(f"- {item}")
    lines.extend(["", "## Error Patterns", ""])
    for key, value in payload["error_patterns"].items():
        lines.append(f"- `{key}`: `{value}`")
    lines.extend(["", "## Decision", ""])
    lines.append(f"- Status: `{payload['decision']['status']}`")
    lines.append(f"- Recommended next step: `{payload['decision']['recommended_next_step']}`")
    lines.append(f"- Runtime test allowed next: `{payload['decision']['runtime_test_allowed_next']}`")
    lines.append(f"- Stage 7 promotion allowed: `{payload['decision']['stage7_promotion_allowed']}`")
    lines.append(f"- Stage 8 training allowed: `{payload['decision']['stage8_training_allowed']}`")
    lines.append("")
    return "\n".join(lines)


def main() -> None:
    payload = build_audit()
    (ROOT / OUT_JSON).write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (ROOT / OUT_MD).write_text(render_markdown(payload), encoding="utf-8")
    print(json.dumps(payload["decision"], indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
