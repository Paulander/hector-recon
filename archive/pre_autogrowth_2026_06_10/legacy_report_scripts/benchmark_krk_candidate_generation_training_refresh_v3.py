#!/usr/bin/env python3
"""Benchmark offline KRK candidate-generation training refresh options for v3.

This script treats protected forced-provider capacity labels as candidate
generation labels only. It does not create selector labels, runtime routing, or
score changes.
"""

from __future__ import annotations

import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Callable


ROOT = Path(__file__).resolve().parents[1]
DATASET = Path("reports/strategy_arbitration/krk_strategy_sequence_dataset_v3.json")
DESIGN = Path(
    "reports/strategy_arbitration/krk_candidate_generation_training_refresh_design_v3.json"
)
OUT_JSON = Path(
    "reports/strategy_arbitration/krk_candidate_generation_training_refresh_benchmark_v3.json"
)
OUT_MD = Path(
    "reports/strategy_arbitration/krk_candidate_generation_training_refresh_benchmark_v3.md"
)

POSITIVE = "positive_capacity"
NEGATIVE = "negative_capacity"


def _load(path: Path) -> dict[str, Any]:
    payload = json.loads((ROOT / path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"expected JSON object: {path}")
    return payload


def _runtime_false_block() -> dict[str, bool]:
    return {
        "runtime_behavior_changed": False,
        "runtime_defaults_changed": False,
        "runtime_selector_implemented": False,
        "runtime_score_changes": False,
        "runtime_direct_routing": False,
        "runtime_dtm_or_tablebase_lookup": False,
        "gameplay_topology_mutation": False,
        "stage7_promotion_allowed": False,
        "stage8_training_allowed": False,
    }


def _key(row: dict[str, Any], fields: tuple[str, ...]) -> tuple[str, ...]:
    return tuple(str(row.get(field) or "") for field in fields)


def _capacity_rows(dataset: dict[str, Any]) -> list[dict[str, Any]]:
    rows = []
    for row in dataset.get("rows") or []:
        if not isinstance(row, dict):
            continue
        if row.get("stage7_challenge_row"):
            continue
        if row.get("evidence_channel") != "validated_provider_capacity":
            continue
        if row.get("capacity_label") not in {POSITIVE, NEGATIVE}:
            continue
        rows.append(row)
    return rows


def _trace_rows(dataset: dict[str, Any]) -> list[dict[str, Any]]:
    rows = []
    for row in dataset.get("rows") or []:
        if not isinstance(row, dict):
            continue
        if row.get("stage7_challenge_row"):
            continue
        if row.get("evidence_channel") != "runtime_observation_trace_feature":
            continue
        rows.append(row)
    return rows


def _selector_training_row_count(dataset: dict[str, Any]) -> int:
    return sum(
        1
        for row in dataset.get("rows") or []
        if isinstance(row, dict) and row.get("usable_for_selector_training_v3")
    )


def _stage7_training_row_count(dataset: dict[str, Any]) -> int:
    return sum(
        1
        for row in dataset.get("rows") or []
        if isinstance(row, dict)
        and row.get("stage7_challenge_row")
        and (
            row.get("usable_for_candidate_generation_training_v3")
            or row.get("usable_for_selector_training_v3")
        )
    )


def _metrics(
    rows: list[dict[str, Any]],
    predicate: Callable[[dict[str, Any]], bool],
) -> dict[str, Any]:
    positives = [row for row in rows if row.get("capacity_label") == POSITIVE]
    negatives = [row for row in rows if row.get("capacity_label") == NEGATIVE]
    predicted = [row for row in rows if predicate(row)]
    tp = sum(1 for row in predicted if row.get("capacity_label") == POSITIVE)
    fp = sum(1 for row in predicted if row.get("capacity_label") == NEGATIVE)
    fn = len(positives) - tp
    tn = len(negatives) - fp
    positive_recall = tp / len(positives) if positives else 0.0
    positive_precision = tp / (tp + fp) if tp + fp else 0.0
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
        "positive_capacity_recall": positive_recall,
        "positive_precision": positive_precision,
        "negative_capacity_suppression": negative_suppression,
        "balanced_recall_risk": (positive_recall + negative_suppression) / 2,
    }


def _rate_table(
    rows: list[dict[str, Any]],
    fields: tuple[str, ...],
) -> dict[tuple[str, ...], dict[str, Any]]:
    by_key: dict[tuple[str, ...], list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        by_key[_key(row, fields)].append(row)
    table = {}
    for key, items in by_key.items():
        positives = sum(1 for row in items if row.get("capacity_label") == POSITIVE)
        negatives = sum(1 for row in items if row.get("capacity_label") == NEGATIVE)
        support = positives + negatives
        table[key] = {
            "support": support,
            "positive": positives,
            "negative": negatives,
            "positive_rate": positives / support if support else 0.0,
        }
    return table


def _selected_keys(
    rows: list[dict[str, Any]],
    fields: tuple[str, ...],
    *,
    min_support: int,
    min_positive_rate: float,
    max_negative: int | None = None,
) -> set[tuple[str, ...]]:
    selected = set()
    for key, stats in _rate_table(rows, fields).items():
        if stats["support"] < min_support:
            continue
        if stats["positive_rate"] < min_positive_rate:
            continue
        if max_negative is not None and stats["negative"] > max_negative:
            continue
        selected.add(key)
    return selected


def _trace_key_sets(trace_rows: list[dict[str, Any]]) -> dict[str, set[tuple[str, ...]]]:
    specs = {
        "trace_exact": ("fen", "candidate_provider_id", "candidate_move_uci"),
        "trace_state_provider": ("fen", "candidate_provider_id"),
        "trace_stage_family": ("source_stage", "candidate_strategy_family"),
        "trace_provider": ("candidate_provider_id",),
        "trace_active_family": ("active_landmark_label", "candidate_strategy_family"),
    }
    return {name: {_key(row, fields) for row in trace_rows} for name, fields in specs.items()}


def _policy_predicates(
    train_rows: list[dict[str, Any]],
    trace_sets: dict[str, set[tuple[str, ...]]],
) -> dict[str, Callable[[dict[str, Any]], bool]]:
    family_majority = _selected_keys(
        train_rows,
        ("candidate_strategy_family",),
        min_support=1,
        min_positive_rate=0.5,
    )
    provider_majority = _selected_keys(
        train_rows,
        ("candidate_provider_id",),
        min_support=1,
        min_positive_rate=0.5,
    )
    stage_family_pure = _selected_keys(
        train_rows,
        ("source_stage", "candidate_strategy_family"),
        min_support=2,
        min_positive_rate=1.0,
        max_negative=0,
    )
    active_family_pure = _selected_keys(
        train_rows,
        ("active_landmark_label", "candidate_strategy_family"),
        min_support=2,
        min_positive_rate=1.0,
        max_negative=0,
    )
    stage_active_family_pure = _selected_keys(
        train_rows,
        ("source_stage", "active_landmark_label", "candidate_strategy_family"),
        min_support=2,
        min_positive_rate=1.0,
        max_negative=0,
    )
    stage_family_rate_75 = _selected_keys(
        train_rows,
        ("source_stage", "candidate_strategy_family"),
        min_support=2,
        min_positive_rate=0.75,
    )

    return {
        "emit_all_capacity_candidates": lambda _row: True,
        "trace_exact_context": lambda row: _key(
            row,
            ("fen", "candidate_provider_id", "candidate_move_uci"),
        )
        in trace_sets["trace_exact"],
        "trace_state_provider_context": lambda row: _key(
            row,
            ("fen", "candidate_provider_id"),
        )
        in trace_sets["trace_state_provider"],
        "trace_stage_family_context": lambda row: _key(
            row,
            ("source_stage", "candidate_strategy_family"),
        )
        in trace_sets["trace_stage_family"],
        "trace_provider_context": lambda row: _key(row, ("candidate_provider_id",))
        in trace_sets["trace_provider"],
        "trace_active_family_context": lambda row: _key(
            row,
            ("active_landmark_label", "candidate_strategy_family"),
        )
        in trace_sets["trace_active_family"],
        "learned_family_positive_rate_at_least_half": lambda row: _key(
            row,
            ("candidate_strategy_family",),
        )
        in family_majority,
        "learned_provider_positive_rate_at_least_half": lambda row: _key(
            row,
            ("candidate_provider_id",),
        )
        in provider_majority,
        "learned_stage_family_pure_positive_support_2": lambda row: _key(
            row,
            ("source_stage", "candidate_strategy_family"),
        )
        in stage_family_pure,
        "learned_active_family_pure_positive_support_2": lambda row: _key(
            row,
            ("active_landmark_label", "candidate_strategy_family"),
        )
        in active_family_pure,
        "learned_stage_active_family_pure_positive_support_2": lambda row: _key(
            row,
            ("source_stage", "active_landmark_label", "candidate_strategy_family"),
        )
        in stage_active_family_pure,
        "learned_stage_family_positive_rate_at_least_0_75": lambda row: _key(
            row,
            ("source_stage", "candidate_strategy_family"),
        )
        in stage_family_rate_75,
        "hybrid_trace_stage_family_or_learned_stage_family_pure": lambda row: (
            _key(row, ("source_stage", "candidate_strategy_family"))
            in trace_sets["trace_stage_family"]
            or _key(row, ("source_stage", "candidate_strategy_family"))
            in stage_family_pure
        ),
        "oracle_positive_capacity_ceiling": lambda row: row.get("capacity_label") == POSITIVE,
    }


def _policy_metrics(
    rows: list[dict[str, Any]],
    trace_rows: list[dict[str, Any]],
) -> dict[str, dict[str, Any]]:
    trace_sets = _trace_key_sets(trace_rows)
    predicates = _policy_predicates(rows, trace_sets)
    return {name: _metrics(rows, predicate) for name, predicate in predicates.items()}


def _leave_out(
    rows: list[dict[str, Any]],
    trace_rows: list[dict[str, Any]],
    field: str,
) -> dict[str, Any]:
    values = sorted({str(row.get(field) or "unknown") for row in rows})
    trace_sets = _trace_key_sets(trace_rows)
    fold_results = {}
    joined: list[tuple[dict[str, Any], dict[str, bool]]] = []
    for value in values:
        train = [row for row in rows if str(row.get(field) or "unknown") != value]
        test = [row for row in rows if str(row.get(field) or "unknown") == value]
        predicates = _policy_predicates(train, trace_sets)
        fold_results[value] = {name: _metrics(test, pred) for name, pred in predicates.items()}
        for row in test:
            joined.append((row, {name: pred(row) for name, pred in predicates.items()}))

    aggregates = {}
    if joined:
        rows_only = [row for row, _predictions in joined]
        for policy_name in joined[0][1]:
            prediction_by_id = {id(row): preds[policy_name] for row, preds in joined}
            aggregates[policy_name] = _metrics(
                rows_only,
                lambda row, prediction_by_id=prediction_by_id: prediction_by_id[id(row)],
            )
    return {
        "field": field,
        "fold_count": len(values),
        "folds": fold_results,
        "aggregate": aggregates,
    }


def _best_policy(
    policy_metrics: dict[str, dict[str, Any]],
    leave_stage_out: dict[str, Any],
) -> tuple[str, dict[str, Any], dict[str, Any]]:
    candidates = [
        (name, metrics)
        for name, metrics in policy_metrics.items()
        if not name.startswith("oracle")
    ]
    best_name, best_metrics = max(
        candidates,
        key=lambda item: (
            item[1]["balanced_recall_risk"],
            item[1]["positive_capacity_recall"],
            item[1]["positive_precision"],
        ),
    )
    leave_stage_metrics = leave_stage_out["aggregate"].get(best_name, {})
    return best_name, best_metrics, leave_stage_metrics


def _meets_thresholds(
    *,
    metrics: dict[str, Any],
    leave_stage_metrics: dict[str, Any],
    thresholds: dict[str, Any],
    selector_rows: int,
    stage7_training_rows: int,
) -> bool:
    return (
        metrics.get("positive_capacity_recall", 0.0)
        >= thresholds.get("positive_capacity_recall", 1.0)
        and metrics.get("negative_capacity_suppression", 0.0)
        >= thresholds.get("negative_capacity_suppression", 1.0)
        and leave_stage_metrics.get("positive_capacity_recall", 0.0)
        >= thresholds.get("leave_stage_out_positive_capacity_recall", 1.0)
        and selector_rows == thresholds.get("selector_training_rows", 0)
        and stage7_training_rows == thresholds.get("stage7_training_rows", 0)
    )


def _compact_rates(rows: list[dict[str, Any]], fields: tuple[str, ...]) -> dict[str, Any]:
    table = _rate_table(rows, fields)
    return {
        "|".join(key): stats
        for key, stats in sorted(table.items(), key=lambda item: ("|".join(item[0])))
    }


def build_payload(
    dataset: dict[str, Any] | None = None,
    design: dict[str, Any] | None = None,
) -> dict[str, Any]:
    dataset = dataset or _load(DATASET)
    design = design or _load(DESIGN)
    rows = _capacity_rows(dataset)
    trace_rows = _trace_rows(dataset)
    selector_rows = _selector_training_row_count(dataset)
    stage7_training_rows = _stage7_training_row_count(dataset)
    metrics_by_policy = _policy_metrics(rows, trace_rows)
    leave_stage = _leave_out(rows, trace_rows, "source_stage")
    leave_family = _leave_out(rows, trace_rows, "candidate_strategy_family")
    best_name, best_metrics, best_leave_stage = _best_policy(metrics_by_policy, leave_stage)
    thresholds = design.get("readiness_thresholds_for_future_runtime_review") or {}
    thresholds_met = _meets_thresholds(
        metrics=best_metrics,
        leave_stage_metrics=best_leave_stage,
        thresholds=thresholds,
        selector_rows=selector_rows,
        stage7_training_rows=stage7_training_rows,
    )
    status = (
        "candidate_generation_training_refresh_v3_benchmark_passed_runtime_review_needed"
        if thresholds_met
        else "candidate_generation_training_refresh_v3_benchmark_runtime_blocked"
    )
    recommended_next_step = (
        "write_candidate_generation_refresh_runtime_review_packet_only"
        if thresholds_met
        else "collect_more_cross_stage_candidate_generation_context_or_revisit_features"
    )
    return {
        "schema_version": "krk_candidate_generation_training_refresh_benchmark.v3",
        "causal_status": "non_causal_candidate_generation_training_benchmark",
        **_runtime_false_block(),
        "source_artifacts": [str(DATASET), str(DESIGN)],
        "label_semantics": {
            "capacity_labels_are_candidate_generation_labels_only": True,
            "capacity_labels_are_not_selector_or_ownership_labels": True,
            "runtime_trace_rows_are_context_features_only": True,
            "stage7_rows_are_held_out_challenge_only": True,
        },
        "summary": {
            "capacity_row_count": len(rows),
            "positive_capacity_count": sum(1 for row in rows if row.get("capacity_label") == POSITIVE),
            "negative_capacity_count": sum(1 for row in rows if row.get("capacity_label") == NEGATIVE),
            "runtime_trace_feature_row_count": len(trace_rows),
            "selector_training_row_count": selector_rows,
            "stage7_training_row_count": stage7_training_rows,
            "source_stage_counts": dict(
                sorted(Counter(str(row.get("source_stage") or "unknown") for row in rows).items())
            ),
            "candidate_strategy_family_counts": dict(
                sorted(
                    Counter(
                        str(row.get("candidate_strategy_family") or "unknown")
                        for row in rows
                    ).items()
                )
            ),
            "best_policy": best_name,
            "best_policy_metrics": best_metrics,
            "best_policy_leave_stage_out_metrics": best_leave_stage,
            "thresholds_met": thresholds_met,
        },
        "thresholds": thresholds,
        "policy_metrics": metrics_by_policy,
        "leave_stage_out": leave_stage,
        "leave_family_out": leave_family,
        "rate_tables": {
            "family": _compact_rates(rows, ("candidate_strategy_family",)),
            "provider": _compact_rates(rows, ("candidate_provider_id",)),
            "stage_family": _compact_rates(rows, ("source_stage", "candidate_strategy_family")),
            "active_family": _compact_rates(
                rows,
                ("active_landmark_label", "candidate_strategy_family"),
            ),
        },
        "interpretation": {
            "candidate_generation_refresh_supported_for_review": thresholds_met,
            "selector_supported": False,
            "guardrails_allowed": False,
            "runtime_implementation_allowed_by_this_artifact": False,
            "risk": (
                "This benchmark can support a future candidate-generation runtime review, "
                "but it still does not create ownership labels. Any future runtime source "
                "must remain default-off, observation/candidate-generation scoped, and "
                "must not select or score candidates."
            ),
        },
        "decision": {
            "status": status,
            "selector_allowed": False,
            "runtime_implementation_allowed_by_this_artifact": False,
            "guardrails_allowed": False,
            "promotion_allowed": False,
            "recommended_next_step": recommended_next_step,
        },
    }


def write_markdown(payload: dict[str, Any]) -> None:
    summary = payload["summary"]
    lines = [
        "# KRK Candidate-Generation Training Refresh Benchmark v3",
        "",
        "This offline benchmark evaluates candidate-generation policies over protected forced-provider capacity labels. It does not train or authorize a selector.",
        "",
        "## Decision",
        "",
        f"- status: `{payload['decision']['status']}`",
        f"- runtime_implementation_allowed_by_this_artifact: `{payload['decision']['runtime_implementation_allowed_by_this_artifact']}`",
        f"- selector_allowed: `{payload['decision']['selector_allowed']}`",
        f"- recommended_next_step: `{payload['decision']['recommended_next_step']}`",
        "",
        "## Summary",
        "",
        f"- capacity_row_count: `{summary['capacity_row_count']}`",
        f"- positive_capacity_count: `{summary['positive_capacity_count']}`",
        f"- negative_capacity_count: `{summary['negative_capacity_count']}`",
        f"- runtime_trace_feature_row_count: `{summary['runtime_trace_feature_row_count']}`",
        f"- selector_training_row_count: `{summary['selector_training_row_count']}`",
        f"- stage7_training_row_count: `{summary['stage7_training_row_count']}`",
        f"- best_policy: `{summary['best_policy']}`",
        f"- best_policy_metrics: `{summary['best_policy_metrics']}`",
        f"- best_policy_leave_stage_out_metrics: `{summary['best_policy_leave_stage_out_metrics']}`",
        f"- thresholds_met: `{summary['thresholds_met']}`",
        "",
        "## Policy Metrics",
        "",
    ]
    for name, metrics in payload["policy_metrics"].items():
        lines.append(
            f"- `{name}`: recall=`{metrics['positive_capacity_recall']:.3f}` "
            f"precision=`{metrics['positive_precision']:.3f}` "
            f"negative_suppression=`{metrics['negative_capacity_suppression']:.3f}` "
            f"balanced=`{metrics['balanced_recall_risk']:.3f}`"
        )
    lines.extend(
        [
            "",
            "## Boundary",
            "",
            "Capacity labels are candidate-generation labels only. Runtime trace rows are context features only. Stage 7 remains held out. This artifact does not authorize runtime implementation, selector training, score changes, routing, guardrails, promotion, or Stage 8 training.",
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
