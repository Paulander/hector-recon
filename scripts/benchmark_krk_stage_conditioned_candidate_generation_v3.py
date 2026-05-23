#!/usr/bin/env python3
"""Benchmark non-causal stage-conditioned KRK candidate generation."""

from __future__ import annotations

import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Callable


ROOT = Path(__file__).resolve().parents[1]
DATASET = Path(
    "reports/strategy_arbitration/krk_strategy_sequence_dataset_v2_cross_stage_capacity_merged.json"
)
SCOPE_REVIEW = Path(
    "reports/strategy_arbitration/krk_candidate_generation_stage_conditioned_scope_review_v3.json"
)
OUT_JSON = Path(
    "reports/strategy_arbitration/krk_stage_conditioned_candidate_generation_benchmark_v3.json"
)
OUT_MD = Path(
    "reports/strategy_arbitration/krk_stage_conditioned_candidate_generation_benchmark_v3.md"
)


def _load(path: Path) -> dict[str, Any]:
    payload = json.loads((ROOT / path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"expected JSON object: {path}")
    return payload


def _capacity_rows(dataset: dict[str, Any]) -> list[dict[str, Any]]:
    rows = []
    for row in dataset.get("rows") or []:
        if not isinstance(row, dict):
            continue
        if row.get("stage7_challenge_row"):
            continue
        if row.get("evidence_channel") != "validated_provider_capacity":
            continue
        if row.get("capacity_label") not in {"positive_capacity", "negative_capacity"}:
            continue
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
    negative_suppression = tn / len(negatives) if negatives else 1.0
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


def _positive_cells(scope_review: dict[str, Any]) -> set[tuple[str, str]]:
    cells: set[tuple[str, str]] = set()
    for stage, scope in (scope_review.get("stage_scopes") or {}).items():
        for family in scope.get("positive_scope_families") or []:
            cells.add((str(stage), str(family)))
    return cells


def _stage_metrics(
    rows: list[dict[str, Any]], predicate: Callable[[dict[str, Any]], bool]
) -> dict[str, dict[str, Any]]:
    by_stage: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        by_stage[str(row.get("source_stage") or "unknown")].append(row)
    return {stage: _metrics(items, predicate) for stage, items in sorted(by_stage.items())}


def build_payload(
    dataset: dict[str, Any] | None = None,
    scope_review: dict[str, Any] | None = None,
) -> dict[str, Any]:
    dataset = dataset or _load(DATASET)
    scope_review = scope_review or _load(SCOPE_REVIEW)
    rows = _capacity_rows(dataset)
    positive_cells = _positive_cells(scope_review)
    global_positive_families = {
        family
        for family, counts in _family_counts(rows).items()
        if counts["positive"] >= counts["negative"]
    }
    policies: dict[str, Callable[[dict[str, Any]], bool]] = {
        "emit_all_capacity_candidates": lambda _row: True,
        "global_family_positive_rate_at_least_half": (
            lambda row: str(row.get("candidate_strategy_family") or "unknown")
            in global_positive_families
        ),
        "stage_conditioned_positive_scope": (
            lambda row: (
                str(row.get("source_stage") or "unknown"),
                str(row.get("candidate_strategy_family") or "unknown"),
            )
            in positive_cells
        ),
        "stage5_6_positive_scope_only": (
            lambda row: str(row.get("source_stage") or "unknown") in {"stage5", "stage6"}
            and (
                str(row.get("source_stage") or "unknown"),
                str(row.get("candidate_strategy_family") or "unknown"),
            )
            in positive_cells
        ),
    }
    policy_metrics = {name: _metrics(rows, predicate) for name, predicate in policies.items()}
    by_stage = {
        name: _stage_metrics(rows, predicate) for name, predicate in policies.items()
    }
    best = policy_metrics["stage_conditioned_positive_scope"]
    stage5_6_rows = [
        row for row in rows if str(row.get("source_stage") or "unknown") in {"stage5", "stage6"}
    ]
    stage5_6 = _metrics(stage5_6_rows, policies["stage5_6_positive_scope_only"])
    stage4 = by_stage["stage_conditioned_positive_scope"].get("stage4") or {}
    stage5_6_promising = (
        stage5_6.get("positive_recall", 0.0) >= 0.7
        and stage5_6.get("negative_suppression", 0.0) >= 0.8
    )
    stage4_blocked = stage4.get("positive_recall", 0.0) < 0.7
    return {
        "schema_version": "krk_stage_conditioned_candidate_generation_benchmark.v3",
        "causal_status": "non_causal_benchmark",
        "runtime_behavior_changed": False,
        "runtime_defaults_changed": False,
        "runtime_selector_implemented": False,
        "runtime_score_changes": False,
        "runtime_direct_routing": False,
        "runtime_dtm_or_tablebase_lookup": False,
        "gameplay_topology_mutation": False,
        "stage7_promotion_allowed": False,
        "stage8_training_allowed": False,
        "source_artifacts": [str(DATASET), str(SCOPE_REVIEW)],
        "summary": {
            "capacity_row_count": len(rows),
            "capacity_label_counts": dict(
                sorted(Counter(row.get("capacity_label") for row in rows).items())
            ),
            "source_stage_counts": dict(
                sorted(Counter(row.get("source_stage") for row in rows).items())
            ),
            "positive_scope_cells": [f"{stage}|{family}" for stage, family in sorted(positive_cells)],
            "stage7_readiness_training_row_count": 0,
            "best_policy": "stage_conditioned_positive_scope",
            "best_policy_metrics": best,
            "stage5_6_positive_scope_metrics": stage5_6,
            "stage4_positive_scope_metrics": stage4,
        },
        "policy_metrics": policy_metrics,
        "stage_metrics": by_stage,
        "interpretation": {
            "stage_conditioned_candidate_generation_supported": bool(
                best["positive_recall"] >= 0.7 and best["negative_suppression"] >= 0.8
            ),
            "stage5_6_scope_promising": stage5_6_promising,
            "stage4_scope_blocked_without_companion_terms": stage4_blocked,
            "selector_supported": False,
            "runtime_refresh_supported_now": False,
            "capacity_labels_are_not_ownership_labels": True,
        },
        "decision": {
            "status": (
                "stage_conditioned_candidate_generation_stage5_6_promising_stage4_blocked"
                if stage5_6_promising and stage4_blocked
                else "stage_conditioned_candidate_generation_benchmark_inconclusive"
            ),
            "selector_allowed": False,
            "runtime_candidate_generator_refresh_allowed": False,
            "guardrails_allowed": False,
            "promotion_allowed": False,
            "recommended_next_step": "stage5_6_candidate_generation_refresh_review_packet_or_stage4_companion_audit",
        },
    }


def _family_counts(rows: list[dict[str, Any]]) -> dict[str, dict[str, int]]:
    counts: dict[str, dict[str, int]] = defaultdict(lambda: {"positive": 0, "negative": 0})
    for row in rows:
        family = str(row.get("candidate_strategy_family") or "unknown")
        if row.get("capacity_label") == "positive_capacity":
            counts[family]["positive"] += 1
        elif row.get("capacity_label") == "negative_capacity":
            counts[family]["negative"] += 1
    return dict(counts)


def write_markdown(payload: dict[str, Any]) -> None:
    summary = payload["summary"]
    lines = [
        "# KRK Stage-Conditioned Candidate-Generation Benchmark v3",
        "",
        "This benchmark evaluates candidate-generation policies scoped by protected stage/family cells. It does not train or implement runtime behavior.",
        "",
        "## Decision",
        "",
        f"- status: `{payload['decision']['status']}`",
        f"- selector_allowed: `{payload['decision']['selector_allowed']}`",
        f"- runtime_candidate_generator_refresh_allowed: `{payload['decision']['runtime_candidate_generator_refresh_allowed']}`",
        f"- recommended_next_step: `{payload['decision']['recommended_next_step']}`",
        "",
        "## Summary",
        "",
        f"- capacity_row_count: {summary['capacity_row_count']}",
        f"- capacity_label_counts: `{summary['capacity_label_counts']}`",
        f"- source_stage_counts: `{summary['source_stage_counts']}`",
        f"- positive_scope_cells: `{summary['positive_scope_cells']}`",
        f"- best_policy_metrics: `{summary['best_policy_metrics']}`",
        f"- stage5_6_positive_scope_metrics: `{summary['stage5_6_positive_scope_metrics']}`",
        f"- stage4_positive_scope_metrics: `{summary['stage4_positive_scope_metrics']}`",
        "",
        "## Policy Metrics",
        "",
    ]
    for name, metrics in payload["policy_metrics"].items():
        lines.append(
            f"- `{name}`: recall=`{metrics['positive_recall']:.3f}` "
            f"precision=`{metrics['positive_precision']:.3f}` "
            f"negative_suppression=`{metrics['negative_suppression']:.3f}` "
            f"balanced=`{metrics['balanced_recall_risk']:.3f}`"
        )
    lines.extend(["", "## Interpretation", ""])
    for key, value in payload["interpretation"].items():
        lines.append(f"- {key}: `{value}`")
    lines.extend(
        [
            "",
            "## Boundary",
            "",
            "This is candidate-generation evidence only. It cannot select, suppress, score, route, promote Stage 7, or train Stage 8.",
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
