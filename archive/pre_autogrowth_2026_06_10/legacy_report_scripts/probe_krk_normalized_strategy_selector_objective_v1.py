#!/usr/bin/env python3
"""Offline probe for the KRK normalized selector objective.

The probe uses existing labeled artifacts only. It intentionally does not run
playouts, train a runtime model, or enable a selector.
"""

from __future__ import annotations

import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
OBJECTIVE_PLAN = Path("reports/krk_normalized_strategy_selector_objective_v1.json")
BALANCED_DATASET = Path("reports/krk_selector_balanced_label_dataset_v1.json")
PROVENANCE_DATASET = Path("reports/krk_selector_provenance_feature_dataset_v0.json")
OUT_JSON = Path("reports/krk_normalized_strategy_selector_objective_probe_v1.json")
OUT_MD = Path("reports/krk_normalized_strategy_selector_objective_probe_v1.md")


Label = str
Row = dict[str, Any]


def _load_json(path: Path) -> dict[str, Any]:
    payload = json.loads((ROOT / path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"expected JSON object: {path}")
    return payload


def _label_bool(label: Any) -> bool | None:
    if label == "positive":
        return True
    if label == "negative":
        return False
    return None


def _row_key(row: Row, keys: tuple[str, ...]) -> tuple[str, ...]:
    return tuple(str(row.get(key)) for key in keys)


def _provider_local_rank(row: Row) -> int | None:
    value = row.get("provider_local_rank", row.get("target_provider_best_rank"))
    return int(value) if isinstance(value, (int, float)) else None


def _raw_score(row: Row) -> float | None:
    value = row.get("normalized_score", row.get("target_provider_best_raw_score"))
    return float(value) if isinstance(value, (int, float)) else None


def _rank_bucket(rank: int | None) -> str:
    if rank is None:
        return "missing"
    if rank <= 1:
        return "rank_1"
    if rank <= 3:
        return "rank_2_3"
    return "rank_4_plus"


def _score_bucket(score: float | None) -> str:
    if score is None:
        return "missing"
    if score >= 0.75:
        return "score_high"
    if score >= 0.25:
        return "score_mid"
    return "score_low"


def _augment_rows(rows: list[Row]) -> list[Row]:
    raw_by_provider: dict[str, list[float]] = defaultdict(list)
    for row in rows:
        provider = str(row.get("provider_id"))
        score = _raw_score(row)
        if score is not None:
            raw_by_provider[provider].append(score)

    ranges = {}
    for provider, values in raw_by_provider.items():
        ranges[provider] = (min(values), max(values))

    augmented = []
    for row in rows:
        copy = dict(row)
        rank = _provider_local_rank(row)
        raw = _raw_score(row)
        provider = str(row.get("provider_id"))
        normalized = None
        if raw is not None and provider in ranges:
            low, high = ranges[provider]
            normalized = 0.5 if high == low else (raw - low) / (high - low)
        copy["provider_local_rank"] = rank
        copy["normalized_score"] = normalized
        copy["provider_local_rank_bucket"] = _rank_bucket(rank)
        copy["normalized_score_bucket"] = _score_bucket(normalized)
        augmented.append(copy)
    return augmented


def _positive_rate(rows: list[Row], keys: tuple[str, ...] | None = None) -> dict[tuple[str, ...], float]:
    counts: dict[tuple[str, ...], Counter[str]] = defaultdict(Counter)
    for row in rows:
        label = _label_bool(row.get("label"))
        if label is None:
            continue
        key = _row_key(row, keys) if keys else ("__global__",)
        counts[key]["positive" if label else "negative"] += 1
    rates = {}
    for key, counter in counts.items():
        total = counter["positive"] + counter["negative"]
        rates[key] = counter["positive"] / total if total else 0.5
    return rates


def _score_row(
    *,
    train_rows: list[Row],
    row: Row,
    feature_keys: tuple[str, ...],
    global_rate: float,
) -> float:
    rates = _positive_rate(train_rows, feature_keys)
    return rates.get(_row_key(row, feature_keys), global_rate)


def _evaluate_loo(rows: list[Row], feature_keys: tuple[str, ...]) -> dict[str, Any]:
    labeled = [row for row in rows if _label_bool(row.get("label")) is not None]
    predictions = []
    for index, row in enumerate(labeled):
        train_rows = labeled[:index] + labeled[index + 1 :]
        global_rate = _positive_rate(train_rows).get(("__global__",), 0.5)
        score = _score_row(
            train_rows=train_rows,
            row=row,
            feature_keys=feature_keys,
            global_rate=global_rate,
        )
        label = _label_bool(row.get("label"))
        assert label is not None
        predictions.append({
            "state_id": row.get("state_id"),
            "provider_id": row.get("provider_id"),
            "feature_key": list(feature_keys),
            "score": score,
            "predicted_positive": score >= 0.5,
            "label_positive": label,
        })
    return _classification_metrics(predictions)


def _classification_metrics(predictions: list[dict[str, Any]]) -> dict[str, Any]:
    total = len(predictions)
    correct = sum(1 for item in predictions if item["predicted_positive"] == item["label_positive"])
    true_positive = sum(
        1
        for item in predictions
        if item["predicted_positive"] is True and item["label_positive"] is True
    )
    false_positive = sum(
        1
        for item in predictions
        if item["predicted_positive"] is True and item["label_positive"] is False
    )
    true_negative = sum(
        1
        for item in predictions
        if item["predicted_positive"] is False and item["label_positive"] is False
    )
    false_negative = sum(
        1
        for item in predictions
        if item["predicted_positive"] is False and item["label_positive"] is True
    )
    positive_precision = true_positive / (true_positive + false_positive) if true_positive + false_positive else None
    positive_recall = true_positive / (true_positive + false_negative) if true_positive + false_negative else None
    negative_suppression = true_negative / (true_negative + false_positive) if true_negative + false_positive else None
    return {
        "row_count": total,
        "accuracy": correct / total if total else None,
        "true_positive": true_positive,
        "false_positive": false_positive,
        "true_negative": true_negative,
        "false_negative": false_negative,
        "positive_precision": positive_precision,
        "positive_recall": positive_recall,
        "negative_suppression": negative_suppression,
        "predictions": predictions,
    }


def _summarize_rows(rows: list[Row]) -> dict[str, Any]:
    return {
        "row_count": len(rows),
        "label_counts": dict(Counter(str(row.get("label")) for row in rows)),
        "provider_family_counts": dict(Counter(str(row.get("provider_family")) for row in rows)),
        "target_kind_counts": dict(Counter(str(row.get("target_kind")) for row in rows)),
        "stage7_training_rows": sum(1 for row in rows if row.get("stage7_training_row") is True),
        "heldout_stage7_rows": sum(1 for row in rows if row.get("held_out_challenge") is True),
    }


def _missing_required_fields(rows: list[Row]) -> dict[str, int]:
    required = ("provider_local_rank", "normalized_score")
    return {
        key: sum(1 for row in rows if row.get(key) is None)
        for key in required
    }


def build_probe() -> dict[str, Any]:
    objective = _load_json(OBJECTIVE_PLAN)
    balanced = _load_json(BALANCED_DATASET)
    provenance = _load_json(PROVENANCE_DATASET)

    if objective.get("decision", {}).get("status") != "normalized_selector_objective_design_ready_for_offline_probe":
        raise ValueError("normalized objective design must be ready before probing")

    balanced_rows = _augment_rows(list(balanced.get("rows") or []))
    provenance_rows = _augment_rows(list(provenance.get("rows") or []))
    provenance_labeled = [
        row
        for row in provenance_rows
        if _label_bool(row.get("label")) is not None and row.get("held_out_challenge") is not True
    ]
    heldout_stage7 = [row for row in provenance_rows if row.get("held_out_challenge") is True]

    baseline_specs = {
        "provider_family": ("provider_family",),
        "provider_maturity": ("provider_maturity",),
        "family_maturity": ("provider_family", "provider_maturity"),
        "family_maturity_target_kind": ("provider_family", "provider_maturity", "target_kind"),
        "source_stage_family": ("source_stage", "provider_family"),
        "provider_rank_bucket": ("provider_local_rank_bucket",),
        "family_rank_bucket": ("provider_family", "provider_local_rank_bucket"),
        "family_rank_score_bucket": (
            "provider_family",
            "provider_local_rank_bucket",
            "normalized_score_bucket",
        ),
        "family_maturity_rank_target_kind": (
            "provider_family",
            "provider_maturity",
            "provider_local_rank_bucket",
            "target_kind",
        ),
    }
    balanced_results = {
        name: _evaluate_loo(balanced_rows, keys)
        for name, keys in baseline_specs.items()
    }
    provenance_results = {
        name: _evaluate_loo(provenance_labeled, keys)
        for name, keys in baseline_specs.items()
    }

    best_balanced = max(
        balanced_results.items(),
        key=lambda item: item[1]["accuracy"] if item[1]["accuracy"] is not None else -1,
    )
    best_provenance = max(
        provenance_results.items(),
        key=lambda item: item[1]["accuracy"] if item[1]["accuracy"] is not None else -1,
    )
    missing_fields = {
        "balanced": _missing_required_fields(balanced_rows),
        "provenance_labeled": _missing_required_fields(provenance_labeled),
    }
    normalized_fields_available = all(
        count == 0 for count in missing_fields["provenance_labeled"].values()
    )
    underpowered = len(balanced_rows) < 30 or len(provenance_labeled) < 80

    status = (
        "normalized_objective_probe_fields_available_but_underpowered"
        if normalized_fields_available
        else "normalized_objective_probe_blocked_missing_rank_fields"
    )
    if underpowered:
        status = (
            "normalized_objective_probe_underpowered_fields_available"
            if normalized_fields_available
            else "normalized_objective_probe_underpowered_missing_rank_fields"
        )

    probe = {
        "schema_version": "krk_normalized_strategy_selector_objective_probe.v1",
        "causal_status": "non_causal_offline_probe",
        "runtime_behavior_changed": False,
        "runtime_defaults_changed": False,
        "runtime_dtm_or_tablebase_lookup": False,
        "gameplay_topology_mutation": False,
        "stage7_promotion_allowed": False,
        "stage8_training_allowed": False,
        "source_artifacts": [str(OBJECTIVE_PLAN), str(BALANCED_DATASET), str(PROVENANCE_DATASET)],
        "dataset_summary": {
            "balanced": _summarize_rows(balanced_rows),
            "provenance_labeled": _summarize_rows(provenance_labeled),
            "heldout_stage7": _summarize_rows(heldout_stage7),
        },
        "required_field_gaps": missing_fields,
        "normalized_fields_available": normalized_fields_available,
        "benchmark_underpowered": underpowered,
        "results": {
            "balanced_leave_one_out": {
                name: {key: value for key, value in metrics.items() if key != "predictions"}
                for name, metrics in balanced_results.items()
            },
            "provenance_leave_one_out": {
                name: {key: value for key, value in metrics.items() if key != "predictions"}
                for name, metrics in provenance_results.items()
            },
        },
        "best_results": {
            "balanced": {"objective": best_balanced[0], "accuracy": best_balanced[1]["accuracy"]},
            "provenance": {"objective": best_provenance[0], "accuracy": best_provenance[1]["accuracy"]},
        },
        "interpretation": {
            "probe_can_test_full_normalized_objective": normalized_fields_available,
            "stage7_training_leakage": False,
            "finding": (
                "Existing provenance labels can test normalized rank/score proxies via "
                "target_provider_best_rank and target_provider_best_raw_score, but the dataset "
                "is still too small and Stage7 remains held out."
                if normalized_fields_available
                else "Existing labels can replay provenance baselines but cannot test the full "
                "normalized objective because provider_local_rank and normalized_score are absent."
            ),
        },
        "decision": {
            "status": status,
            "recommended_next_step": (
                "review_normalized_probe_before_runtime_tests"
                if normalized_fields_available
                else "export_strategy_proposal_frames_with_provider_local_rank"
            ),
            "runtime_test_allowed_next": False,
            "stage7_promotion_allowed": False,
            "stage8_training_allowed": False,
        },
    }
    validate_probe(probe)
    return probe


def validate_probe(probe: dict[str, Any]) -> None:
    for key in (
        "runtime_behavior_changed",
        "runtime_defaults_changed",
        "runtime_dtm_or_tablebase_lookup",
        "gameplay_topology_mutation",
        "stage7_promotion_allowed",
        "stage8_training_allowed",
    ):
        if probe.get(key) is not False:
            raise ValueError(f"{key} must be false")
    if probe.get("decision", {}).get("runtime_test_allowed_next") is not False:
        raise ValueError("runtime tests must remain blocked by this probe")


def render_markdown(probe: dict[str, Any]) -> str:
    lines = [
        "# KRK Normalized Strategy Selector Objective Probe v1",
        "",
        "This offline probe uses existing labels only. It does not train or enable a runtime selector.",
        "",
        "## Dataset Summary",
        "",
    ]
    for name, summary in probe["dataset_summary"].items():
        lines.append(f"### `{name}`")
        lines.append("")
        for key, value in summary.items():
            lines.append(f"- `{key}`: `{value}`")
        lines.append("")
    lines.extend(["## Required Field Gaps", ""])
    for key, value in probe["required_field_gaps"].items():
        lines.append(f"- `{key}` missing rows: `{value}`")
    lines.extend(["", "## Best Results", ""])
    for key, value in probe["best_results"].items():
        lines.append(f"- `{key}`: `{value}`")
    lines.extend(["", "## Result Tables", ""])
    for table_name, table in probe["results"].items():
        lines.append(f"### `{table_name}`")
        lines.append("")
        for objective, metrics in table.items():
            lines.append(
                f"- `{objective}` accuracy=`{metrics['accuracy']}` "
                f"precision=`{metrics['positive_precision']}` "
                f"recall=`{metrics['positive_recall']}` "
                f"negative_suppression=`{metrics['negative_suppression']}`"
            )
        lines.append("")
    lines.extend(
        [
            "## Interpretation",
            "",
            f"- Full normalized objective testable: `{probe['interpretation']['probe_can_test_full_normalized_objective']}`",
            f"- Stage 7 training leakage: `{probe['interpretation']['stage7_training_leakage']}`",
            f"- Finding: {probe['interpretation']['finding']}",
            "",
            "## Decision",
            "",
            f"- Status: `{probe['decision']['status']}`",
            f"- Recommended next step: `{probe['decision']['recommended_next_step']}`",
            f"- Runtime test allowed next: `{probe['decision']['runtime_test_allowed_next']}`",
            f"- Stage 7 promotion allowed: `{probe['decision']['stage7_promotion_allowed']}`",
            f"- Stage 8 training allowed: `{probe['decision']['stage8_training_allowed']}`",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> None:
    probe = build_probe()
    (ROOT / OUT_JSON).write_text(json.dumps(probe, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (ROOT / OUT_MD).write_text(render_markdown(probe), encoding="utf-8")
    print(json.dumps(probe["decision"], indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
