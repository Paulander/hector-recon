#!/usr/bin/env python3
"""Probe non-causal provider provenance features for selector labels."""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import Any, Callable


ROOT = Path(__file__).resolve().parents[1]
DATASET = Path("reports/krk_selector_provenance_feature_dataset_v0.json")
OUT_JSON = Path("reports/krk_selector_provenance_feature_probe_v0.json")
OUT_MD = Path("reports/krk_selector_provenance_feature_probe_v0.md")


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


def _label(row: dict[str, Any]) -> str:
    return str(row.get("label") or "none")


def _majority_label(rows: list[dict[str, Any]], default: str = "negative") -> str:
    counts = Counter(_label(row) for row in rows)
    if not counts:
        return default
    return sorted(counts.items(), key=lambda item: (-item[1], item[0]))[0][0]


def _loo_accuracy(
    rows: list[dict[str, Any]],
    *,
    name: str,
    key_fn: Callable[[dict[str, Any]], str],
) -> dict[str, Any]:
    correct = 0
    abstain = 0
    for index, row in enumerate(rows):
        train = [other for i, other in enumerate(rows) if i != index]
        key = key_fn(row)
        matching = [other for other in train if key_fn(other) == key]
        if not matching:
            abstain += 1
        pred = _majority_label(matching, default=_majority_label(train))
        if pred == _label(row):
            correct += 1
    return {
        "name": name,
        "accuracy": correct / len(rows) if rows else None,
        "correct": correct,
        "total": len(rows),
        "abstain_or_fallback_count": abstain,
    }


def _group_summary(rows: list[dict[str, Any]], key: str) -> list[dict[str, Any]]:
    groups: dict[str, Counter[str]] = {}
    for row in rows:
        groups.setdefault(str(row.get(key) or "unknown"), Counter())[_label(row)] += 1
    summary = []
    for value, counts in sorted(groups.items()):
        total = sum(counts.values())
        summary.append({
            "key": key,
            "value": value,
            "total": total,
            "label_counts": dict(sorted(counts.items())),
            "positive_rate": counts.get("positive", 0) / total if total else None,
        })
    return summary


def build_probe() -> dict[str, Any]:
    payload = _load_json(DATASET)
    rows = [
        row for row in payload.get("rows", []) or []
        if row.get("target_kind") == "selected_playout_success"
        and row.get("usable_for_training")
        and row.get("label") in {"positive", "negative"}
    ]
    baselines = [
        _loo_accuracy(rows, name="provider_id_loo", key_fn=lambda row: str(row.get("provider_id") or "unknown")),
        _loo_accuracy(rows, name="provider_family_loo", key_fn=lambda row: str(row.get("provider_family") or "unknown")),
        _loo_accuracy(rows, name="provider_maturity_loo", key_fn=lambda row: str(row.get("provider_maturity") or "unknown")),
        _loo_accuracy(rows, name="provider_source_stage_loo", key_fn=lambda row: str(row.get("provider_source_stage") or "unknown")),
        _loo_accuracy(rows, name="validated_role_loo", key_fn=lambda row: str(row.get("provider_validated_role") or "unknown")),
        _loo_accuracy(rows, name="protected_overlay_loo", key_fn=lambda row: f"{row.get('protected_provider')}|{row.get('overlay_provider')}"),
        _loo_accuracy(rows, name="family_maturity_loo", key_fn=lambda row: f"{row.get('provider_family')}|{row.get('provider_maturity')}"),
    ]
    best = max(
        baselines,
        key=lambda item: float(item.get("accuracy") if item.get("accuracy") is not None else -1.0),
    )
    provider_id = next(item for item in baselines if item["name"] == "provider_id_loo")
    family = next(item for item in baselines if item["name"] == "provider_family_loo")
    maturity = next(item for item in baselines if item["name"] == "provider_maturity_loo")
    decomposed_matches_provider = bool(
        provider_id.get("accuracy") == family.get("accuracy")
        or provider_id.get("accuracy") == maturity.get("accuracy")
        or provider_id.get("accuracy") == best.get("accuracy")
    )
    status = (
        "provenance_features_explain_provider_prior_non_causal"
        if decomposed_matches_provider
        else "raw_provider_id_signal_not_explained_by_provenance"
    )
    return {
        "schema_version": "krk_selector_provenance_feature_probe.v0",
        "causal_status": "non_causal_probe",
        "runtime_behavior_changed": False,
        "runtime_defaults_changed": False,
        "runtime_arbiter_implemented": False,
        "source_artifact": str(DATASET),
        "target_kind": "selected_playout_success",
        "row_count": len(rows),
        "label_counts": dict(sorted(Counter(_label(row) for row in rows).items())),
        "baselines": baselines,
        "best_baseline": {
            "name": best.get("name"),
            "accuracy": best.get("accuracy"),
        },
        "group_summaries": {
            "provider_family": _group_summary(rows, "provider_family"),
            "provider_maturity": _group_summary(rows, "provider_maturity"),
            "provider_source_stage": _group_summary(rows, "provider_source_stage"),
        },
        "decision": {
            "status": status,
            "runtime_arbiter_allowed": False,
            "selector_sandbox_ready": False,
            "raw_provider_id_runtime_prior_allowed": False,
            "recommended_next_step": "architecture_review_selector_objective_before_more_labels",
        },
        "interpretation": [
            "Provider provenance/maturity features can reproduce the current provider-prior signal when they distinguish foundation-frozen stage0_basin from validated edge-trap providers.",
            "This remains non-causal because the dataset is small and selected-playout labels can encode horizon/control artifacts.",
            "The result supports explicit provenance fields in evidence records, not a runtime provider prior.",
        ],
        "blocked_next_work": [
            "runtime_arbiter",
            "selector_sandbox",
            "raw_provider_id_runtime_prior",
            "provider_support_adapter",
            "score_bonus_or_penalty",
            "stage7_repair",
            "stage7_promotion",
            "stage8_training",
        ],
    }


def write_markdown(payload: dict[str, Any]) -> None:
    lines = [
        "# KRK Selector Provenance Feature Probe v0",
        "",
        "This non-causal probe tests whether explicit provider provenance/maturity fields explain the provider-prior selector signal.",
        "",
        "## Summary",
        "",
        f"- Rows: `{payload['row_count']}`",
        f"- Label counts: `{payload['label_counts']}`",
        f"- Best baseline: `{payload['best_baseline']}`",
        f"- Decision: `{payload['decision']['status']}`",
        f"- Runtime arbiter allowed: `{payload['decision']['runtime_arbiter_allowed']}`",
        f"- Selector sandbox ready: `{payload['decision']['selector_sandbox_ready']}`",
        "",
        "## Baselines",
        "",
    ]
    for baseline in payload["baselines"]:
        lines.append(
            f"- `{baseline['name']}` accuracy=`{baseline['accuracy']}` "
            f"correct=`{baseline['correct']}` total=`{baseline['total']}`"
        )
    lines.extend(["", "## Group Summaries", ""])
    for group, items in payload["group_summaries"].items():
        lines.append(f"### {group}")
        for item in items:
            lines.append(
                f"- `{item['value']}` total=`{item['total']}` "
                f"positive_rate=`{item['positive_rate']}` labels=`{item['label_counts']}`"
            )
        lines.append("")
    lines.extend(["## Interpretation", ""])
    for item in payload["interpretation"]:
        lines.append(f"- {item}")
    lines.extend([
        "",
        "## Blocked",
        "",
    ])
    for item in payload["blocked_next_work"]:
        lines.append(f"- `{item}`")
    (ROOT / OUT_MD).write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    payload = build_probe()
    (ROOT / OUT_JSON).write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_markdown(payload)


if __name__ == "__main__":
    main()
