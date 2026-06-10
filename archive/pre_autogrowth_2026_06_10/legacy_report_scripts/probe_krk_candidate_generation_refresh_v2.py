#!/usr/bin/env python3
"""Probe non-causal KRK candidate-generation refresh options from dataset v2."""

from __future__ import annotations

import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Callable


ROOT = Path(__file__).resolve().parents[1]
DATASET = Path("reports/strategy_arbitration/krk_strategy_sequence_dataset_v2.json")
QUALITY = Path("reports/strategy_arbitration/krk_strategy_sequence_dataset_v2_quality_probe.json")
OUT_JSON = Path("reports/strategy_arbitration/krk_candidate_generation_refresh_probe_v2.json")
OUT_MD = Path("reports/strategy_arbitration/krk_candidate_generation_refresh_probe_v2.md")


def _load(path: Path) -> dict[str, Any]:
    payload = json.loads((ROOT / path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"expected JSON object: {path}")
    return payload


def capacity_rows(dataset: dict[str, Any]) -> list[dict[str, Any]]:
    rows = []
    for row in dataset.get("rows") or []:
        if not isinstance(row, dict):
            continue
        if row.get("stage7_challenge_row"):
            continue
        if row.get("evidence_channel") != "validated_provider_capacity":
            continue
        if row.get("capacity_label") in {"positive_capacity", "negative_capacity"}:
            rows.append(row)
    return rows


def _metrics(rows: list[dict[str, Any]], predicate: Callable[[dict[str, Any]], bool]) -> dict[str, Any]:
    positives = [row for row in rows if row.get("capacity_label") == "positive_capacity"]
    negatives = [row for row in rows if row.get("capacity_label") == "negative_capacity"]
    predicted = [row for row in rows if predicate(row)]
    tp = sum(1 for row in predicted if row.get("capacity_label") == "positive_capacity")
    fp = sum(1 for row in predicted if row.get("capacity_label") == "negative_capacity")
    fn = len(positives) - tp
    tn = len(negatives) - fp
    recall = tp / len(positives) if positives else 0.0
    precision = tp / (tp + fp) if (tp + fp) else 0.0
    negative_suppression = tn / len(negatives) if negatives else 0.0
    return {
        "row_count": len(rows),
        "positive_count": len(positives),
        "negative_count": len(negatives),
        "predicted_count": len(predicted),
        "true_positive": tp,
        "false_positive": fp,
        "false_negative": fn,
        "true_negative": tn,
        "positive_recall": recall,
        "positive_precision": precision,
        "negative_suppression": negative_suppression,
        "balanced_recall_risk": (recall + negative_suppression) / 2,
    }


def _family_rates(rows: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    by_family: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        by_family[str(row.get("candidate_strategy_family") or "unknown")].append(row)
    rates = {}
    for family, items in by_family.items():
        positives = sum(1 for row in items if row.get("capacity_label") == "positive_capacity")
        negatives = sum(1 for row in items if row.get("capacity_label") == "negative_capacity")
        total = positives + negatives
        rates[family] = {
            "support": total,
            "positive": positives,
            "negative": negatives,
            "positive_rate": positives / total if total else 0.0,
        }
    return rates


def _stage_family_rates(rows: list[dict[str, Any]]) -> dict[tuple[str, str], dict[str, Any]]:
    by_key: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        key = (
            str(row.get("source_stage") or "unknown"),
            str(row.get("candidate_strategy_family") or "unknown"),
        )
        by_key[key].append(row)
    rates = {}
    for key, items in by_key.items():
        positives = sum(1 for row in items if row.get("capacity_label") == "positive_capacity")
        negatives = sum(1 for row in items if row.get("capacity_label") == "negative_capacity")
        total = positives + negatives
        rates[key] = {
            "support": total,
            "positive": positives,
            "negative": negatives,
            "positive_rate": positives / total if total else 0.0,
        }
    return rates


def _policy_metrics(rows: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    family_rates = _family_rates(rows)
    stage_family_rates = _stage_family_rates(rows)
    positive_majority_families = {
        family for family, stats in family_rates.items() if stats["positive_rate"] >= 0.5
    }
    pure_positive_families = {
        family
        for family, stats in family_rates.items()
        if stats["support"] >= 2 and stats["negative"] == 0
    }
    positive_majority_stage_families = {
        key for key, stats in stage_family_rates.items() if stats["positive_rate"] >= 0.5
    }
    pure_positive_stage_families = {
        key
        for key, stats in stage_family_rates.items()
        if stats["support"] >= 2 and stats["negative"] == 0
    }
    return {
        "emit_all_capacity_candidates": _metrics(rows, lambda _row: True),
        "family_positive_rate_at_least_half": _metrics(
            rows,
            lambda row: str(row.get("candidate_strategy_family") or "unknown")
            in positive_majority_families,
        ),
        "family_pure_positive_with_support_2": _metrics(
            rows,
            lambda row: str(row.get("candidate_strategy_family") or "unknown")
            in pure_positive_families,
        ),
        "stage_family_positive_rate_at_least_half": _metrics(
            rows,
            lambda row: (
                str(row.get("source_stage") or "unknown"),
                str(row.get("candidate_strategy_family") or "unknown"),
            )
            in positive_majority_stage_families,
        ),
        "stage_family_pure_positive_with_support_2": _metrics(
            rows,
            lambda row: (
                str(row.get("source_stage") or "unknown"),
                str(row.get("candidate_strategy_family") or "unknown"),
            )
            in pure_positive_stage_families,
        ),
        "oracle_positive_capacity_ceiling": _metrics(
            rows,
            lambda row: row.get("capacity_label") == "positive_capacity",
        ),
    }


def _leave_stage_out(rows: list[dict[str, Any]]) -> dict[str, Any]:
    stages = sorted({str(row.get("source_stage") or "unknown") for row in rows})
    fold_results: dict[str, dict[str, Any]] = {}
    all_test_rows: list[tuple[dict[str, Any], bool]] = []
    for stage in stages:
        train = [row for row in rows if str(row.get("source_stage") or "unknown") != stage]
        test = [row for row in rows if str(row.get("source_stage") or "unknown") == stage]
        family_rates = _family_rates(train)
        selected = {
            family for family, stats in family_rates.items() if stats["positive_rate"] >= 0.5
        }
        fold_results[stage] = _metrics(
            test,
            lambda row, selected=selected: str(row.get("candidate_strategy_family") or "unknown")
            in selected,
        )
        for row in test:
            all_test_rows.append(
                (
                    row,
                    str(row.get("candidate_strategy_family") or "unknown") in selected,
                )
            )
    rows_only = [row for row, _pred in all_test_rows]
    pred_by_id = {id(row): pred for row, pred in all_test_rows}
    aggregate = _metrics(rows_only, lambda row: pred_by_id[id(row)])
    return {
        "fold_count": len(stages),
        "folds": fold_results,
        "aggregate": aggregate,
    }


def build_payload(
    dataset: dict[str, Any] | None = None,
    quality: dict[str, Any] | None = None,
) -> dict[str, Any]:
    dataset = dataset or _load(DATASET)
    quality = quality or _load(QUALITY)
    rows = capacity_rows(dataset)
    policy_metrics = _policy_metrics(rows)
    leave_stage = _leave_stage_out(rows)
    best_name, best = max(
        (
            (name, metrics)
            for name, metrics in policy_metrics.items()
            if not name.startswith("oracle")
        ),
        key=lambda item: (item[1]["balanced_recall_risk"], item[1]["positive_recall"]),
    )
    candidate_generation_supported = (
        best["positive_recall"] >= 0.7
        and best["negative_suppression"] >= 0.5
        and leave_stage["aggregate"]["positive_recall"] >= 0.5
    )
    return {
        "schema_version": "krk_candidate_generation_refresh_probe.v2",
        "causal_status": "non_causal_candidate_generation_probe",
        "runtime_behavior_changed": False,
        "runtime_defaults_changed": False,
        "runtime_selector_implemented": False,
        "runtime_score_changes": False,
        "runtime_direct_routing": False,
        "runtime_dtm_or_tablebase_lookup": False,
        "gameplay_topology_mutation": False,
        "stage7_promotion_allowed": False,
        "stage8_training_allowed": False,
        "source_artifacts": [str(DATASET), str(QUALITY)],
        "summary": {
            "capacity_row_count": len(rows),
            "capacity_label_counts": dict(
                sorted(Counter(row.get("capacity_label") for row in rows).items())
            ),
            "source_stage_counts": dict(
                sorted(Counter(row.get("source_stage") for row in rows).items())
            ),
            "candidate_family_counts": dict(
                sorted(Counter(row.get("candidate_strategy_family") for row in rows).items())
            ),
            "best_non_oracle_policy": best_name,
            "best_non_oracle_metrics": best,
            "leave_stage_out_aggregate": leave_stage["aggregate"],
            "dataset_v2_quality_status": (quality.get("decision") or {}).get("status"),
        },
        "family_rates": _family_rates(rows),
        "stage_family_rates": {
            f"{stage}|{family}": stats
            for (stage, family), stats in _stage_family_rates(rows).items()
        },
        "policy_metrics": policy_metrics,
        "leave_stage_out": leave_stage,
        "interpretation": {
            "candidate_generation_refresh_supported": candidate_generation_supported,
            "selector_supported": False,
            "capacity_labels_are_not_ownership_labels": True,
            "stage7_training_allowed": False,
            "risk": (
                "Candidate-generation recall can be improved from protected capacity "
                "labels, but negative-capacity candidates remain present and must not "
                "be converted into ownership labels."
            ),
        },
        "decision": {
            "status": (
                "candidate_generation_refresh_supported_selector_blocked"
                if candidate_generation_supported
                else "candidate_generation_refresh_underpowered_selector_blocked"
            ),
            "selector_allowed": False,
            "guardrails_allowed": False,
            "promotion_allowed": False,
            "recommended_next_step": (
                "design_candidate_generation_training_refresh_non_causal"
                if candidate_generation_supported
                else "collect_more_protected_capacity_or_explicit_ownership_labels"
            ),
        },
    }


def write_markdown(payload: dict[str, Any]) -> None:
    summary = payload["summary"]
    lines = [
        "# KRK Candidate-Generation Refresh Probe v2",
        "",
        "This probe evaluates non-causal candidate-generation policies over protected capacity rows from dataset v2. It is not selector training.",
        "",
        "## Decision",
        "",
        f"- status: `{payload['decision']['status']}`",
        f"- selector_allowed: `{payload['decision']['selector_allowed']}`",
        f"- recommended_next_step: `{payload['decision']['recommended_next_step']}`",
        "",
        "## Summary",
        "",
        f"- capacity_row_count: {summary['capacity_row_count']}",
        f"- capacity_label_counts: `{summary['capacity_label_counts']}`",
        f"- source_stage_counts: `{summary['source_stage_counts']}`",
        f"- candidate_family_counts: `{summary['candidate_family_counts']}`",
        f"- best_non_oracle_policy: `{summary['best_non_oracle_policy']}`",
        f"- best_non_oracle_metrics: `{summary['best_non_oracle_metrics']}`",
        f"- leave_stage_out_aggregate: `{summary['leave_stage_out_aggregate']}`",
        "",
        "## Policies",
        "",
    ]
    for name, metrics in payload["policy_metrics"].items():
        lines.append(
            f"- `{name}`: recall=`{metrics['positive_recall']:.3f}` "
            f"precision=`{metrics['positive_precision']:.3f}` "
            f"negative_suppression=`{metrics['negative_suppression']:.3f}` "
            f"balanced=`{metrics['balanced_recall_risk']:.3f}`"
        )
    lines.extend(
        [
            "",
            "## Boundary",
            "",
            "These are candidate-generation recall/risk policies. Capacity labels remain offline evidence and are not ownership-selector labels.",
        ]
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
