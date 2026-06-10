#!/usr/bin/env python3
"""Non-causal feature baseline probes for KRK selector targets."""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import Any, Callable


ROOT = Path(__file__).resolve().parents[1]
DATASET = Path("reports/krk_selector_feature_dataset_v0.json")
OUT_JSON = Path("reports/krk_selector_feature_baseline_probe_v0.json")
OUT_MD = Path("reports/krk_selector_feature_baseline_probe_v0.md")


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


def _label(row: dict[str, Any]) -> str:
    return str(row.get("label") or "none")


def _majority_label(rows: list[dict[str, Any]], default: str = "negative") -> str:
    counts = Counter(_label(row) for row in rows)
    if not counts:
        return default
    return sorted(counts.items(), key=lambda item: (-item[1], item[0]))[0][0]


def _loo_key_accuracy(
    rows: list[dict[str, Any]],
    *,
    name: str,
    key_fn: Callable[[dict[str, Any]], str],
) -> dict[str, Any]:
    correct = 0
    for index, row in enumerate(rows):
        train = [other for i, other in enumerate(rows) if i != index]
        key = key_fn(row)
        matching = [other for other in train if key_fn(other) == key]
        pred = _majority_label(matching, default=_majority_label(train))
        if pred == _label(row):
            correct += 1
    return {
        "name": name,
        "accuracy": correct / len(rows) if rows else None,
        "correct": correct,
        "total": len(rows),
    }


def _best_term_for_row(row: dict[str, Any], train: list[dict[str, Any]]) -> str | None:
    terms = list(row.get("source_terms", []) or [])
    best_term = None
    best_score = (-1, -1.0, "")
    for term in terms:
        matching = [other for other in train if term in set(other.get("source_terms", []) or [])]
        if len(matching) < 2:
            continue
        counts = Counter(_label(other) for other in matching)
        label, count = sorted(counts.items(), key=lambda item: (-item[1], item[0]))[0]
        purity = count / len(matching)
        score = (len(matching), purity, label)
        if score > best_score:
            best_score = score
            best_term = term
    return best_term


def _loo_best_term_accuracy(rows: list[dict[str, Any]]) -> dict[str, Any]:
    correct = 0
    used_terms = Counter()
    for index, row in enumerate(rows):
        train = [other for i, other in enumerate(rows) if i != index]
        term = _best_term_for_row(row, train)
        if term is None:
            pred = _majority_label(train)
        else:
            matching = [other for other in train if term in set(other.get("source_terms", []) or [])]
            pred = _majority_label(matching, default=_majority_label(train))
            used_terms[term] += 1
        if pred == _label(row):
            correct += 1
    return {
        "name": "best_source_term_loo",
        "accuracy": correct / len(rows) if rows else None,
        "correct": correct,
        "total": len(rows),
        "used_terms": dict(used_terms.most_common(10)),
    }


def _loo_provider_term_accuracy(rows: list[dict[str, Any]]) -> dict[str, Any]:
    correct = 0
    fallback_count = 0
    for index, row in enumerate(rows):
        train = [other for i, other in enumerate(rows) if i != index]
        provider = str(row.get("provider_id") or "")
        row_terms = set(row.get("source_terms", []) or [])
        matching = [
            other for other in train
            if str(other.get("provider_id") or "") == provider
            and bool(row_terms.intersection(set(other.get("source_terms", []) or [])))
        ]
        if not matching:
            fallback_count += 1
            matching = [other for other in train if str(other.get("provider_id") or "") == provider]
        pred = _majority_label(matching, default=_majority_label(train))
        if pred == _label(row):
            correct += 1
    return {
        "name": "provider_shared_term_backoff_loo",
        "accuracy": correct / len(rows) if rows else None,
        "correct": correct,
        "total": len(rows),
        "fallback_count": fallback_count,
    }


def _term_summary(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    by_term: dict[str, Counter] = {}
    for row in rows:
        for term in set(row.get("source_terms", []) or []):
            by_term.setdefault(term, Counter())[_label(row)] += 1
    summary = []
    for term, counts in by_term.items():
        total = sum(counts.values())
        if total < 3:
            continue
        positive = counts.get("positive", 0)
        negative = counts.get("negative", 0)
        summary.append({
            "term": term,
            "total": total,
            "positive": positive,
            "negative": negative,
            "positive_rate": positive / total if total else None,
        })
    summary.sort(key=lambda item: (-abs(float(item["positive_rate"] or 0.0) - 0.5), -item["total"], item["term"]))
    return summary[:12]


def build_probe(root: Path = ROOT) -> dict[str, Any]:
    payload = _load_json(DATASET)
    rows = [
        row for row in payload.get("rows", []) or []
        if row.get("target_kind") == "selected_playout_success"
        and row.get("usable_for_training")
        and row.get("label") in {"positive", "negative"}
    ]
    label_counts = Counter(_label(row) for row in rows)
    baselines = [
        {
            "name": "majority_label",
            "accuracy": max(label_counts.values()) / len(rows) if rows else None,
            "correct": max(label_counts.values()) if rows else 0,
            "total": len(rows),
        },
        _loo_key_accuracy(rows, name="provider_prior_loo", key_fn=lambda row: str(row.get("provider_id") or "")),
        _loo_key_accuracy(rows, name="stage_prior_loo", key_fn=lambda row: str(row.get("source_stage") or "")),
        _loo_key_accuracy(rows, name="provider_stage_prior_loo", key_fn=lambda row: f"{row.get('provider_id')}|{row.get('source_stage')}"),
        _loo_key_accuracy(rows, name="provider_selected_match_loo", key_fn=lambda row: f"{row.get('provider_id')}|{row.get('selected_provider_matches_target')}"),
        _loo_best_term_accuracy(rows),
        _loo_provider_term_accuracy(rows),
    ]
    best = max(
        baselines,
        key=lambda item: float(item.get("accuracy") if item.get("accuracy") is not None else -1.0),
    ) if baselines else None
    provider_prior = next(item for item in baselines if item["name"] == "provider_prior_loo")
    feature_improved = bool(
        best
        and provider_prior.get("accuracy") is not None
        and best.get("accuracy") is not None
        and float(best["accuracy"]) > float(provider_prior["accuracy"])
    )
    status = (
        "observation_features_improve_non_causal_baseline"
        if feature_improved
        else "provider_prior_remains_best_non_causal_baseline"
    )
    return {
        "schema_version": "krk_selector_feature_baseline_probe.v0",
        "causal_status": "non_causal_probe",
        "runtime_behavior_changed": False,
        "runtime_defaults_changed": False,
        "runtime_arbiter_implemented": False,
        "source_artifact": str(DATASET),
        "target_kind": "selected_playout_success",
        "row_count": len(rows),
        "label_counts": dict(sorted(label_counts.items())),
        "baselines": baselines,
        "best_baseline": {
            "name": best.get("name") if best else None,
            "accuracy": best.get("accuracy") if best else None,
        },
        "feature_improved_over_provider_prior": feature_improved,
        "term_summary": _term_summary(rows),
        "decision": {
            "status": status,
            "runtime_arbiter_allowed": False,
            "sandbox_ready": False,
            "recommended_next_step": "architecture_review_before_selector_sandbox_or_more_control_labels",
        },
    }


def write_markdown(payload: dict[str, Any], path: Path) -> None:
    lines = [
        "# KRK Selector Feature Baseline Probe v0",
        "",
        "This non-causal probe checks whether trace-only observation features improve selector target prediction.",
        "",
        "## Summary",
        "",
        f"- Rows: `{payload['row_count']}`",
        f"- Label counts: `{payload['label_counts']}`",
        f"- Best baseline: `{payload['best_baseline']}`",
        f"- Feature improved over provider prior: `{payload['feature_improved_over_provider_prior']}`",
        "",
        "## Baselines",
        "",
    ]
    for baseline in payload["baselines"]:
        lines.append(
            f"- `{baseline['name']}` accuracy=`{baseline.get('accuracy')}` "
            f"correct=`{baseline.get('correct')}` total=`{baseline.get('total')}`"
        )
    lines.extend([
        "",
        "## Term Summary",
        "",
    ])
    for item in payload["term_summary"]:
        lines.append(
            f"- `{item['term']}` total=`{item['total']}` positive_rate=`{item['positive_rate']}`"
        )
    lines.extend([
        "",
        "## Decision",
        "",
        f"Status: `{payload['decision']['status']}`",
        f"Sandbox ready: `{payload['decision']['sandbox_ready']}`",
        f"Runtime arbiter allowed: `{payload['decision']['runtime_arbiter_allowed']}`",
        f"Recommended next step: `{payload['decision']['recommended_next_step']}`",
    ])
    (ROOT / path).write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    payload = build_probe()
    (ROOT / OUT_JSON).write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_markdown(payload, OUT_MD)


if __name__ == "__main__":
    main()
